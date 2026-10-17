"""Finding 2: did Harbour's 15% promo on Cold Coffee + Desserts (2026-03-12 .. 2026-05-19) pay for itself?

Method: difference-in-differences on daily units sold.
  log(units + 1) ~ branch FE + date FE + b1 * Harbour x promo + b2 * Harbour x post
Garden and Uptown are the controls: they share the season and the chain-wide growth but had no 15% promo.
The date fixed effects absorb weather, seasonality and growth common to all branches.
Uncertainty: block bootstrap that resamples whole weeks (days in a week are not independent).
Placebos: (a) same model on NON-target categories (should show ~0),
          (b) a fake promo window inside the pre-period (should show ~0).
"""
import os
# One BLAS thread: the bootstrap runs thousands of small least-squares fits, where multithreaded BLAS
# mostly adds overhead. Tested on a Mac (system BLAS): 33.6 s vs 33.9 s, identical results.
# Not tested on an OpenBLAS machine, where the default used ~52 CPU-minutes for a 2-minute run.
for _v in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]:
    os.environ.setdefault(_v, "1")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import SEED, save_fig
from load import GP, REV, load_clean, save_table

PROMO_START, PROMO_END = pd.Timestamp("2026-03-12"), pd.Timestamp("2026-05-19")
TARGET = ["Cold Coffee", "Desserts"]
N_BOOT = 1000
rng = np.random.default_rng(SEED)

d = load_clean()
promo_lines = d[d["Discount Rate"] == 0.15]
print(f"15% lines: {len(promo_lines)}, branches {promo_lines.Branch.unique().tolist()}, "
      f"{promo_lines.date.min().date()} .. {promo_lines.date.max().date()}, "
      f"categories {promo_lines.Category.unique().tolist()}")

d["target"] = d["Category"].isin(TARGET)


def daily_panel(df):
    """Units per branch per day; zero-filled."""
    dates = pd.date_range(d.date.min(), d.date.max())
    idx = pd.MultiIndex.from_product([["Garden", "Harbour", "Uptown"], dates], names=["Branch", "date"])
    return df.groupby(["Branch", "date"])["Quantity"].sum().reindex(idx, fill_value=0).reset_index()


def did_flags(sample):
    p = sample.copy()
    p["y"] = np.log1p(p["Quantity"])
    X = pd.concat([p[["hp", "hpost"]],
                   pd.get_dummies(p.Branch, drop_first=True, dtype=float),
                   pd.get_dummies(p.date.astype(str), dtype=float)], axis=1).values
    return np.linalg.lstsq(X, p["y"].values, rcond=None)[0][:2]


def add_flags(panel, start, end, post_end=None):
    p = panel.copy()
    h = (p.Branch == "Harbour").astype(float)
    p["hp"] = h * ((p.date >= start) & (p.date <= end))
    post = (p.date > end) if post_end is None else ((p.date > end) & (p.date <= post_end))
    p["hpost"] = h * post
    return p


def run(name, panel, start, end, post_end=None, keep=None):
    p = add_flags(panel, start, end, post_end)
    if keep is not None:
        p = p[keep(p)]
    est = did_flags(p)
    bs = boot_flags(p)
    lo, hi = np.percentile(bs, [2.5, 97.5], axis=0)
    row = {"test": name,
           "promo_effect_pct": 100 * (np.exp(est[0]) - 1),
           "promo_ci_low_pct": 100 * (np.exp(lo[0]) - 1), "promo_ci_high_pct": 100 * (np.exp(hi[0]) - 1),
           "post_effect_pct": 100 * (np.exp(est[1]) - 1),
           "post_ci_low_pct": 100 * (np.exp(lo[1]) - 1), "post_ci_high_pct": 100 * (np.exp(hi[1]) - 1)}
    print(f"{name:45s} promo {row['promo_effect_pct']:+6.1f}% [{row['promo_ci_low_pct']:+.1f}, {row['promo_ci_high_pct']:+.1f}]"
          f"   after {row['post_effect_pct']:+6.1f}% [{row['post_ci_low_pct']:+.1f}, {row['post_ci_high_pct']:+.1f}]")
    return row


def boot_flags(p):
    p = p.assign(wk=p.date.dt.to_period("W"))
    weeks = p.wk.unique()
    groups = {w: g for w, g in p.groupby("wk")}
    out = []
    for _ in range(N_BOOT):
        pick = rng.choice(weeks, size=len(weeks), replace=True)
        parts = []
        for i, w in enumerate(pick):
            g = groups[w].copy()
            g["date"] = g["date"] + pd.Timedelta(days=7 * len(weeks) * (i + 1))
            parts.append(g)
        out.append(did_flags(pd.concat(parts)))
    return np.array(out)


tgt = daily_panel(d[d.target])
non = daily_panel(d[~d.target])
rows = [
    run("MAIN: target categories, Harbour vs Garden+Uptown", tgt, PROMO_START, PROMO_END),
    run("Control = Garden only", tgt, PROMO_START, PROMO_END, keep=lambda p: p.Branch != "Uptown"),
    run("Control = Uptown only", tgt, PROMO_START, PROMO_END, keep=lambda p: p.Branch != "Garden"),
    run("PLACEBO: non-target categories", non, PROMO_START, PROMO_END),
    run("PLACEBO: Cold Drinks (weather-sensitive, never discounted)", daily_panel(d[d.Category == "Cold Drinks"]),
        PROMO_START, PROMO_END),
    run("PLACEBO: fake window Feb 1-Mar 11 (pre only)", tgt, pd.Timestamp("2026-02-01"), PROMO_START - pd.Timedelta(days=1),
        keep=lambda p: p.date < PROMO_START),
]
res = pd.DataFrame(rows).round(2)

# pre-trend check: was Harbour's target share already rising relative to controls before the promo?
wk_share = (d[d.date < PROMO_START].groupby(["week_start", "Branch"])
            .apply(lambda g: g.loc[g.target, "Quantity"].sum() / g["Quantity"].sum(), include_groups=False)
            .unstack().iloc[1:])  # drop partial first week
gap = wk_share["Harbour"] - wk_share[["Garden", "Uptown"]].mean(axis=1)
x = np.arange(len(gap))
slope = np.polyfit(x, gap.values, 1)[0]
bs = []
for _ in range(N_BOOT):
    i = rng.choice(len(gap), len(gap), replace=True)
    bs.append(np.polyfit(x[i], gap.values[i], 1)[0])
lo_s, hi_s = np.percentile(bs, [2.5, 97.5])
print(f"PRE-TREND: Harbour minus control target share, slope per week = {100*slope:+.3f} pts "
      f"[{100*lo_s:+.3f}, {100*hi_s:+.3f}] over {len(gap)} pre-promo weeks")
save_table(pd.DataFrame({"pre_weeks": [len(gap)], "slope_pts_per_week": [round(100 * slope, 3)],
                         "ci_low": [round(100 * lo_s, 3)], "ci_high": [round(100 * hi_s, 3)]}),
           "promo_pretrend.csv", index=False)
save_table(res, "promo_did.csv", index=False)

# ---------- money: what the promo cost vs what it could have earned ----------
hp = d[(d.Branch == "Harbour") & d.target & (d.date >= PROMO_START) & (d.date <= PROMO_END)]
disc_cost = promo_lines["discount_usd"].sum()
units_promo = hp["Quantity"].sum()
# Net effect = actual GP - counterfactual GP without the promo.
# Counterfactual: (units - incremental) sold at FULL-price gross profit per unit.
# Actual GP is already net of the discount, so: net = incremental x full-price GP/unit - total discount.
# (Using the after-discount GP/unit here would subtract part of the discount twice.)
gp_per_unit = (hp[GP].sum() + disc_cost) / units_promo   # full-price gross profit per unit
eff = rows[0]["promo_effect_pct"] / 100
lo_eff, hi_eff = rows[0]["promo_ci_low_pct"] / 100, rows[0]["promo_ci_high_pct"] / 100


def incr_units(e):  # units that would not have been sold without the promo
    return units_promo - units_promo / (1 + e)


money = pd.DataFrame({
    "scenario": ["point estimate", "CI low", "CI high"],
    "uplift_pct": [100 * eff, 100 * lo_eff, 100 * hi_eff],
})
money["incremental_units"] = [incr_units(e) for e in [eff, lo_eff, hi_eff]]
money["incremental_gross_profit_usd"] = money.incremental_units * gp_per_unit
money["discount_cost_usd"] = disc_cost
money["net_usd"] = money.incremental_gross_profit_usd - disc_cost
break_even_units = disc_cost / gp_per_unit
break_even_pct = 100 * (units_promo / (units_promo - break_even_units) - 1)
money = money.round(1)
save_table(money, "promo_value.csv", index=False)
print(f"\nMEASURED: discount given on 15% lines = ${disc_cost:,.0f}; Harbour target units in window = {units_promo:,}; "
      f"full-price gross profit per unit = ${gp_per_unit:.2f}")
print(f"ESTIMATE: break-even uplift = {break_even_pct:.1f}% more target units")
print(money.to_string(index=False))

# who received it: share of eligible lines, by hour, known customer?
elig = hp.copy()
elig["got15"] = elig["Discount Rate"] == 0.15
w = pd.DataFrame({
    "share_of_eligible_lines_discounted": [elig.got15.mean()],
    "known_customer_share_discounted": [elig[elig.got15]["Customer ID"].notna().mean()],
    "known_customer_share_not_discounted": [elig[~elig.got15]["Customer ID"].notna().mean()],
    "dinein_share_discounted": [(elig[elig.got15]["Order Type"] == "Dine-in").mean()],
    "dinein_share_not_discounted": [(elig[~elig.got15]["Order Type"] == "Dine-in").mean()],
}).round(3)
save_table(w, "promo_who_got_it.csv", index=False)
print("\n", w.T)

# ---------- figure: weekly target units, Harbour vs controls, indexed to pre-period mean ----------
wk = d[d.target].groupby(["week_start", "Branch"])["Quantity"].sum().unstack()
wk = wk.iloc[1:-1]  # drop partial first/last weeks
pre = wk[wk.index < PROMO_START]
idx = 100 * wk / pre.mean()
fig, ax = plt.subplots(figsize=(9, 4.5))
for b, c in [("Harbour", "#c0392b"), ("Garden", "#7f8c8d"), ("Uptown", "#2c3e50")]:
    ax.plot(idx.index, idx[b], label=b, color=c, lw=2 if b == "Harbour" else 1.3)
ax.axvspan(PROMO_START, PROMO_END, color="#f5b7b1", alpha=0.35, label="Harbour 15% promo")
ax.set_title("Cold Coffee + Desserts weekly units (index, pre-promo mean = 100)")
ax.set_xlabel("Week")
ax.set_ylabel("Units, index")
ax.legend()
save_fig(fig, "promo_weekly.png")
print("saved figures/promo_weekly.png")
