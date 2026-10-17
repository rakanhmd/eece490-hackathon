"""Power simulations for the five proposed pilots, run on resampled historical data.

Designs (all on the Jan-Jun 2026 transaction file; effects are INJECTED, nothing here measures a real effect):
  D1 food prompt       branch-week switchback, outcome = share of drink transactions that include a food item
  D2 evening upsell    branch-week switchback, outcome = share of 18:00+ transactions that include a dessert
  D3 price test        chain-wide week switchback (ABBA), outcome = chain gross profit per week (Tue-Sun)
  D4 discount removal  chain-wide week switchback (ABBA), outcome = chain gross profit per week (Tue-Sun)
  D5 Saturday offer    chain-wide week switchback (ABBA), outcome = chain gross profit per WEEK (Mon-Sun, so shifted
                       visits from other days count against the offer)
How one simulated experiment is built
  * Historical week-by-branch-by-weekday cells (25 full weeks) are detrended by the chain's fitted weekly growth, whole weeks
    are resampled with replacement (the same historical week for all three branches, which keeps week shocks shared),
    and the growth trend is put back over the pilot's weeks. So noise = week-to-week and day-to-day variation, and the
    pilot sees growth like the real data.
  * Treatment is assigned by the balanced schedule written to results/experiment_schedules.csv (random start / branch labels).
  * Washout: D1/D2 drop the Monday of any branch-week whose treatment differs from the previous week; D3/D4 analyse
    Tuesday-Sunday totals of every week (Monday is the washout day after a switch).
  * An effect is injected into the treated cells: D1/D2 +x percentage points (each non-event transaction becomes an event
    with probability x/(1-base rate), a binomial draw); D3/D4 treated-week Tue-Sun gross profit x (1+e); D5 Saturday gross
    profit x (1+lift) with 25% of the extra taken back from Mon-Fri of the same week (assumed displacement).
  * The pilot is analysed with the model in EXPERIMENTS.md and counts as a detection if the two-sided p < 0.05 with the right sign.
    D1/D2: weighted regression of branch-day rates with branch, week and weekday fixed effects, SEs clustered by week, t(weeks-1)
    critical values. D3-D5: one observation per week (the unit of randomisation), OLS with a linear trend, t(weeks-3). 500 simulated pilots per cell;
    the effect-0 rows give the false-positive rate, which should be near 5%.
"""
import textwrap

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import SEED, save_fig
from load import GP, load_clean, save_table

import sys
N_SIM = int(sys.argv[1]) if len(sys.argv) > 1 else 500
rng = np.random.default_rng(SEED)
d = load_clean()
BRANCHES = ["Garden", "Harbour", "Uptown"]

# ---------------- historical cells ----------------
tx = d.groupby("Transaction ID").agg(date=("date", "first"), branch=("Branch", "first"), hour=("hour", "first"),
                                     gp=(GP, "sum"),
                                     n_drink=("Category", lambda s: s.isin(["Hot Coffee", "Cold Coffee", "Cold Drinks", "Matcha & Tea"]).sum()),
                                     n_food=("Category", lambda s: (~s.isin(["Hot Coffee", "Cold Coffee", "Cold Drinks", "Matcha & Tea"])).sum()),
                                     dessert=("Category", lambda s: (s == "Desserts").any())).reset_index()
tx["weekday"] = tx.date.dt.dayofweek
first_monday = tx.date.min() + pd.Timedelta(days=(7 - tx.date.min().dayofweek) % 7)
last_sunday = tx.date.max() - pd.Timedelta(days=(tx.date.max().dayofweek + 1) % 7)
tx = tx[(tx.date >= first_monday) & (tx.date <= last_sunday)].copy()
tx["h"] = ((tx.date - first_monday).dt.days // 7).astype(int)
H = tx.h.max() + 1
bi = tx.branch.map({b: i for i, b in enumerate(BRANCHES)}).values


def cell(mask, value=None):
    a = np.zeros((H, 3, 7))
    v = np.ones(len(tx)) if value is None else value
    np.add.at(a, (tx.h.values[mask], bi[mask], tx.weekday.values[mask]), v[mask])
    return a


allm = np.ones(len(tx), bool)
drink_m, eve_m = (tx.n_drink > 0).values, (tx.hour >= 18).values
GPc = cell(allm, tx.gp.values)
Dn, Att = cell(drink_m), cell(drink_m & (tx.n_food > 0).values)
En, Edes = cell(eve_m), cell(eve_m & tx.dessert.values)
a0_food, a0_des = Att.sum() / Dn.sum(), Edes.sum() / En.sum()
weekly_tx = cell(allm).sum(axis=(1, 2))
slope = np.polyfit(np.arange(H), np.log(weekly_tx), 1)[0]
print(f"historical full weeks: {H}; chain transactions grow {100 * (np.exp(slope) - 1):.1f}% per week; "
      f"food attach rate {a0_food:.3f}; evening dessert rate {a0_des:.3f}; mean weekly chain gross profit ${GPc.sum() / H:,.0f}")
detr = np.exp(-slope * (np.arange(H) - (H - 1) / 2))[:, None, None]       # divide out the growth


def synth_weeks(W):
    """Resampled historical weeks (same week for all branches), detrended, with growth re-applied over W weeks."""
    pick = rng.integers(0, H, W)
    level = np.exp(slope * (np.arange(W) - (W - 1) / 2))[:, None, None]
    return pick, (detr[pick] * level)[:, :, :, None].squeeze(-1), level


# ---------------- schedules ----------------
# branch-week: 6-week cycle in which every branch is treated in 3 of 6 weeks and every week has treated and control branches
CYCLE_BW = np.array([[1, 0, 0], [0, 1, 1], [0, 1, 0], [1, 0, 1], [0, 0, 1], [1, 1, 0]])      # rows = weeks, cols = Garden, Harbour, Uptown
ABBA = np.array([0, 1, 1, 0])      # chain-wide: 0 = control week, 1 = treated week, pattern repeats; start/flip randomised


def schedule_bw(W):
    perm = rng.permutation(3)
    start = rng.integers(0, 6)
    return np.array([CYCLE_BW[(start + w) % 6][perm] for w in range(W)])


def schedule_chain(W):
    flip = rng.integers(0, 2)
    return np.array([ABBA[w % 4] ^ flip for w in range(W)])


def keep_mask_bw(treat):
    """Rows (w, b, d) kept after the washout day: Monday of a week where the branch's treatment changed."""
    W = treat.shape[0]
    keep = np.ones((W, 3, 7), bool)
    for w in range(1, W):
        for b in range(3):
            if treat[w, b] != treat[w - 1, b]:
                keep[w, b, 0] = False
    return keep


def keep_mask_chain(treat):
    W = len(treat)
    keep = np.ones((W, 7), bool)
    for w in range(1, W):
        if treat[w] != treat[w - 1]:
            keep[w, 0] = False
    return keep


# ---------------- regression with week-clustered SEs ----------------
def wls_cluster(X, y, wts, cl):
    """Coefficient on column 0 and its cluster-robust (CR1) SE; df = number of clusters - 1."""
    XtW = X.T * wts
    A = np.linalg.pinv(XtW @ X)
    beta = A @ (XtW @ y)
    r = y - X @ beta
    uc, inv = np.unique(cl, return_inverse=True)
    S = np.zeros((len(uc), X.shape[1]))
    np.add.at(S, inv, X * (wts * r)[:, None])
    G, n, k = len(uc), len(y), np.linalg.matrix_rank(X)
    V = A @ (S.T @ S) @ A * (G / (G - 1)) * ((n - 1) / (n - k))
    return beta[0], np.sqrt(V[0, 0]), G - 1


def ols_t(X, y):
    """Classical OLS: coefficient on column 0, its SE and residual df (used when there is one observation per week)."""
    A = np.linalg.pinv(X.T @ X)
    beta = A @ (X.T @ y)
    df = len(y) - np.linalg.matrix_rank(X)
    s2 = ((y - X @ beta) ** 2).sum() / df
    return beta[0], np.sqrt(s2 * A[0, 0]), df


def design_bw(treat, keep):
    """Design matrix for branch-day rows: treat, branch FE, week FE, weekday FE."""
    W = treat.shape[0]
    w_i, b_i, d_i = np.meshgrid(np.arange(W), np.arange(3), np.arange(7), indexing="ij")
    w_i, b_i, d_i, kp = w_i.ravel(), b_i.ravel(), d_i.ravel(), keep.ravel()
    cols = [treat[w_i, b_i].astype(float)]
    cols += [(b_i == b).astype(float) for b in range(1, 3)]
    cols += [(w_i == w).astype(float) for w in range(W)]            # week FE (includes the intercept)
    cols += [(d_i == dd).astype(float) for dd in range(1, 7)]
    return np.column_stack(cols)[kp], w_i[kp], (w_i, b_i, d_i, kp)


def sim_rate_design(W, delta_pts, tot, succ, base):
    """One simulated pilot for D1/D2; returns (estimate in points, se, df)."""
    treat = schedule_bw(W)
    keep = keep_mask_bw(treat)
    X, cl, (w_i, b_i, d_i, kp) = design_bw(treat, keep)
    pick, scale, _ = synth_weeks(W)
    t_ = np.rint(tot[pick] * scale).astype(int)
    s_ = np.minimum(np.rint(succ[pick] * scale).astype(int), t_)
    if delta_pts > 0:
        p = min(1.0, delta_pts / 100 / (1 - base))
        extra = rng.binomial(t_ - s_, p)
        s_ = s_ + extra * treat[:, :, None]
    n = t_[w_i, b_i, d_i][kp].astype(float)
    y = (s_[w_i, b_i, d_i][kp] / np.maximum(n, 1))
    ok = n > 0
    return wls_cluster(X[ok], y[ok], n[ok], cl[ok])


def sim_chain_weekly(W, e_pct):
    """D3/D4: chain-wide ABBA. Outcome = chain gross profit Tuesday-Sunday of each week (the Monday after a switch is the
    washout day; dropping every Monday keeps weeks comparable). Model: weekly GP ~ treat + linear trend (OLS, t with W-3 df)."""
    treat = schedule_chain(W)
    pick, scale, _ = synth_weeks(W)
    gp = (GPc[pick] * scale).sum(axis=1)[:, 1:]                   # W x 6 (Tue..Sun)
    y = gp.sum(axis=1) * (1 + e_pct / 100 * treat)
    X = np.column_stack([treat.astype(float), np.ones(W), np.arange(W, dtype=float)])
    est, se, df = ols_t(X, y)
    return 100 * est / y.mean(), 100 * se / y.mean(), df          # percent of mean weekly gross profit


def sim_saturday(W, lift_pct, displacement=0.25, saturday_only=False):
    """D5: chain-wide ABBA; treated Saturdays gain lift_pct; displacement share of the extra is taken from Mon-Fri."""
    treat = schedule_chain(W)
    pick, scale, _ = synth_weeks(W)
    gp = (GPc[pick] * scale).sum(axis=1)                          # W x 7
    extra = gp[:, 5] * lift_pct / 100 * treat
    gp[:, 5] += extra
    gp[:, :5] -= (displacement * extra)[:, None] * gp[:, :5] / gp[:, :5].sum(axis=1, keepdims=True)
    y = gp[:, 5] if saturday_only else gp.sum(axis=1)
    X = np.column_stack([treat.astype(float), np.ones(W), np.arange(W, dtype=float)])
    est, se, df = ols_t(X, y)
    return 100 * est / y.mean(), 100 * se / y.mean(), df          # percent of the outcome (weekly GP; Saturday GP if saturday_only)


def detect(fn, true_effect_positive=True):
    est, se, df = fn()
    t = est / se if se > 0 else 0.0
    return (abs(t) > stats.t.ppf(0.975, df)) and (est > 0 if true_effect_positive else True)


# ---------------- run ----------------
DUR_BW = [4, 6, 8, 12, 16]
DUR_CH = [8, 12, 16, 20, 26]
EFF_RATE = [0, 1, 2.5, 5]
EFF_PCT = [0, 0.5, 1, 2.5, 4.5, 5, 7.5]                 # 4.5% = central price-review effect; 1% ~ whole discount-removal prize (0.99%)
EFF_SAT = [0, 5, 10, 19, 25, 50]                        # 19% Saturday lift ~ the central case ($3,468 extra on $18,080 Saturday gross profit)
TXc = cell(allm)
rows, halfw = [], []


def one(fn, W, e, positive=True):
    est, se, df = fn(W, e)
    return abs(est / se) > stats.t.ppf(0.975, df) and (e == 0 or est > 0), stats.t.ppf(0.975, df) * se


def sim_chain_weekly_tx(W, e):          # same design as D3/D4 but the outcome is chain transactions (units of customers)
    treat = schedule_chain(W)
    pick, scale, _ = synth_weeks(W)
    y = (TXc[pick] * scale).sum(axis=1)[:, 1:].sum(axis=1) * (1 + e / 100 * treat)
    est, se, df = ols_t(np.column_stack([treat.astype(float), np.ones(W), np.arange(W, dtype=float)]), y)
    return 100 * est / y.mean(), 100 * se / y.mean(), df


def sim_saturday_bw(W, lift):
    """D5 alternative: branch-week switchback of the Saturday offer; outcome = log weekly gross profit of the branch (Mon-Sun),
    branch and week fixed effects. It cannot see customers who move BETWEEN branches (assumed none)."""
    treat = schedule_bw(W)
    pick, scale, _ = synth_weeks(W)
    gp = GPc[pick] * scale                                         # W x 3 x 7
    extra = gp[:, :, 5] * lift / 100 * treat
    gp[:, :, 5] += extra
    gp[:, :, :5] -= 0.25 * extra[:, :, None] * gp[:, :, :5] / gp[:, :, :5].sum(axis=2, keepdims=True)
    y = np.log(gp.sum(axis=2)).ravel()
    w_i, b_i = np.meshgrid(np.arange(W), np.arange(3), indexing="ij")
    X = np.column_stack([treat.ravel().astype(float)] + [(b_i.ravel() == b).astype(float) for b in range(1, 3)] +
                        [(w_i.ravel() == w).astype(float) for w in range(W)])
    est, se, df = ols_t(X, y)
    return 100 * est, 100 * se, df           # percent


RATES = {"D1 food prompt (attach, points)": (Dn, Att, a0_food), "D2 evening dessert upsell (points)": (En, Edes, a0_des)}
for name, (tot, succ, base) in RATES.items():
    for W in DUR_BW:
        for e in EFF_RATE:
            out = [(lambda r: (abs(r[0] / r[1]) > stats.t.ppf(0.975, r[2]) and (e == 0 or r[0] > 0), 100 * stats.t.ppf(0.975, r[2]) * r[1]))
                   (sim_rate_design(W, e, tot, succ, base)) for _ in range(N_SIM)]
            rows.append({"design": name, "weeks": W, "effect": e, "detection_rate": np.mean([o[0] for o in out])})
            if e == 0:
                halfw.append({"design": name, "weeks": W, "median_ci_halfwidth": np.median([o[1] for o in out])})
    print(f"done {name}")
CHAIN = [("D3 price test (chain GP, %)", sim_chain_weekly, EFF_PCT),
         ("D3 price test, customer-visit metric (chain transactions, %)", sim_chain_weekly_tx, [0, 1, 2.5, 5, 6.4, 7.5]),
         ("D4 discount removal (chain GP, %)", sim_chain_weekly, EFF_PCT)]
for name, fn, effs in CHAIN:
    for W in DUR_CH:
        for e in effs:
            out = [one(fn, W, e) for _ in range(N_SIM)]
            rows.append({"design": name, "weeks": W, "effect": e, "detection_rate": np.mean([o[0] for o in out])})
            if e == 0:
                halfw.append({"design": name, "weeks": W, "median_ci_halfwidth": np.median([o[1] for o in out])})
    print(f"done {name}")
SAT = [("D5 Saturday offer, chain-wide (weekly chain GP; Saturday lift %)", lambda W, l: sim_saturday(W, l)),
       ("D5 alternative: branch-week Saturday offer (log branch weekly GP; ignores cross-branch shifting)", sim_saturday_bw),
       ("D5 Saturday-only metric, chain-wide (ignores displacement; NOT recommended)", lambda W, l: sim_saturday(W, l, saturday_only=True))]
for name, fn in SAT:
    for W in DUR_CH:
        for lift in EFF_SAT:
            out = [one(fn, W, lift) for _ in range(N_SIM)]
            rows.append({"design": name, "weeks": W, "effect": lift, "detection_rate": np.mean([o[0] for o in out])})
            if lift == 0:
                halfw.append({"design": name, "weeks": W, "median_ci_halfwidth": np.median([o[1] for o in out])})
    print(f"done {name}")
res = pd.DataFrame(rows)
res["mc_se"] = np.sqrt(res.detection_rate * (1 - res.detection_rate) / N_SIM)
res = res.round(4)
save_table(res, "experiment_power_results.csv", index=False)
hw = pd.DataFrame(halfw).round(2)
save_table(hw, "experiment_ci_halfwidth.csv", index=False)
print("\nMEDIAN 95% CI HALF-WIDTH of the estimated effect (the precision a pilot of this length gives; points for D1/D2, % otherwise;\n"
      "for the D5 Saturday designs the effect is on the weekly total, not on Saturday)")
print(hw.pivot_table(index="design", columns="weeks", values="median_ci_halfwidth").to_string())

sat_share = GPc[:, :, 5].sum() / GPc.sum()
print(f"\nSaturday is {100 * sat_share:.1f}% of weekly chain gross profit; a 25% Saturday lift = +{25 * sat_share:.2f}% of weekly GP before "
      f"displacement, +{25 * sat_share * 0.75:.2f}% after 25% displacement; a 19% lift (central case) = +{19 * sat_share * 0.75:.2f}%")
print(f"Reference sizes (measured/estimated elsewhere): price review central +4.5% of six-month GP; discount removal whole prize "
      f"{100 * 1705.91 / GPc.sum():.2f}% of GP; Saturday central case +{100 * 2601.23 / GPc.sum():.2f}% of GP")
print("\nFALSE-POSITIVE RATE (effect 0; target about 5%, 500 simulated pilots, standard error +/- 1 point):")
print(res[res.effect == 0].pivot_table(index="design", columns="weeks", values="detection_rate").to_string())
for name, g in res.groupby("design"):
    print(f"\n{name}: detection rate by effect (rows) and weeks (columns)")
    print(g.pivot_table(index="effect", columns="weeks", values="detection_rate").to_string())

mde = []
for (name, W), g in res[res.effect > 0].groupby(["design", "weeks"]):
    g = g.sort_values("effect")
    eff, pw = g.effect.values, g.detection_rate.values
    val = np.nan
    if pw.max() >= 0.8:
        j = np.argmax(pw >= 0.8)
        val = eff[j] if j == 0 else eff[j - 1] + (0.8 - pw[j - 1]) * (eff[j] - eff[j - 1]) / (pw[j] - pw[j - 1])
    mde.append({"design": name, "weeks": W, "effect_for_80pct_power": val})
mde = pd.DataFrame(mde).round(2)
save_table(mde, "experiment_mde.csv", index=False)
print("\nSMALLEST EFFECT DETECTED WITH 80% POWER (blank = not reached within the simulated effects)\n",
      mde.pivot_table(index="design", columns="weeks", values="effect_for_80pct_power", dropna=False).to_string())

# ---------------- value anchors: what the effects are worth, to set rollout thresholds ----------------
WEEKS_ALL = ((d.date.max() - d.date.min()).days + 1) / 7
DRINKS = ["Hot Coffee", "Cold Coffee", "Cold Drinks", "Matcha & Tea"]
dl = d.assign(is_drink=d.Category.isin(DRINKS))
tx_all = dl.groupby("Transaction ID").agg(has_drink=("is_drink", "any"), has_food=("is_drink", lambda s: (~s).any()), hour=("hour", "first"))
food_gp = dl[~dl.is_drink].groupby("Transaction ID")[GP].sum()
mixed = tx_all[tx_all.has_drink & tx_all.has_food].index
gp_per_attached = food_gp.loc[mixed].mean()
wk_drink = tx_all.has_drink.sum() / WEEKS_ALL
des = dl[(dl.Category == "Desserts") & (dl.hour >= 18)].groupby("Transaction ID")[GP].sum()
wk_eve = (tx_all.hour >= 18).sum() / WEEKS_ALL
d10 = d[d["Discount Rate"] == 0.10]
tx10 = d[d["Transaction ID"].isin(d10["Transaction ID"])]
disc_total = d10.discount_usd.sum()
gp10 = tx10[GP].sum()
sstar = disc_total / (gp10 + disc_total)
n_tx = d["Transaction ID"].nunique()
sat_gp = d[d.weekday == 5][GP].sum()
anch = pd.DataFrame([
    {"anchor": "chain drink transactions per week", "value": wk_drink},
    {"anchor": "food gross profit per drink+food basket (USD)", "value": gp_per_attached},
    {"anchor": "value of +1 point attach rate per week (USD)", "value": wk_drink * 0.01 * gp_per_attached},
    {"anchor": "chain transactions from 18:00 per week", "value": wk_eve},
    {"anchor": "dessert gross profit per evening dessert basket (USD)", "value": des.mean()},
    {"anchor": "value of +1 point evening dessert rate per week (USD)", "value": wk_eve * 0.01 * des.mean()},
    {"anchor": "mean weekly chain gross profit (USD)", "value": d[GP].sum() / WEEKS_ALL},
    {"anchor": "10% discount given per week (USD)", "value": disc_total / WEEKS_ALL},
    {"anchor": "break-even share of discounted transactions lost if the discount is removed", "value": sstar},
    {"anchor": "share of chain transactions that carry a 10% line", "value": tx10["Transaction ID"].nunique() / n_tx},
    {"anchor": "break-even chain transaction loss (%) = both of the above multiplied", "value": 100 * sstar * tx10["Transaction ID"].nunique() / n_tx},
    {"anchor": "Saturday lift (%) implied by the 'no shifting' central case ($3,468 on Saturday gross profit)", "value": 100 * 3468.31 / sat_gp},
]).round(4)
save_table(anch, "experiment_anchors.csv", index=False)
print("\nVALUE ANCHORS (measured from the file; used to set rollout thresholds)\n", anch.to_string(index=False))

# ---------------- the written-out schedules ----------------
sched = []
rs = np.random.default_rng(0)       # fixed example draw for the document
for w in range(12):
    sched.append({"week": w + 1, "D1_D2_Garden": CYCLE_BW[w % 6][0], "D1_D2_Harbour": CYCLE_BW[w % 6][1], "D1_D2_Uptown": CYCLE_BW[w % 6][2],
                  "D3_D4_D5_all_branches": ABBA[w % 4]})
sched = pd.DataFrame(sched)
save_table(sched, "experiment_schedules.csv", index=False)
print("\nSCHEDULE (1 = treated, 0 = control); example draw before randomising the start week and branch labels:\n", sched.to_string(index=False))

# ---------------- figure ----------------
designs = list(res.design.unique())
fig, axes = plt.subplots(3, 3, figsize=(15, 13), sharey=True)
fig.subplots_adjust(hspace=0.5, top=0.93)
for ax, name in zip(axes.ravel(), designs):
    g = res[res.design == name]
    for e, gg in g.groupby("effect"):
        ax.plot(gg.weeks, 100 * gg.detection_rate, marker="o", label=f"effect {e:g}" + (" (false positives)" if e == 0 else ""),
                ls="--" if e == 0 else "-")
    ax.axhline(80, color="grey", lw=0.8, ls=":")
    ax.set_title(textwrap.fill(name, 48), fontsize=8)
    ax.set_xlabel("Pilot length (weeks)")
    ax.set_ylabel("Detection rate (%)")
    ax.legend(fontsize=7)
for ax in axes.ravel()[len(designs):]:
    ax.axis("off")
fig.suptitle("Simulated detection rate vs pilot length (500 simulated pilots per point; dotted line = 80%)")
save_fig(fig, "experiment_power.png")
print("saved figures/experiment_power.png")
