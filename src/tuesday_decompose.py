"""Where do the extra Tuesday transactions come from?  A decomposition with the Customer IDs we have.

For each branch and full Mon-Sun week, Tuesday is compared with the mean of Mon/Wed/Thu/Fri. For a day:
    transactions = A  (no Customer ID)  +  C x t  (C = distinct identified customers at that branch that day,
                                                   t = transactions per identified customer that day)
and C = C_old (first appearance anywhere in the data is BEFORE this week) + C_first (first appearance is in this week).
"first seen in the data" is NOT "new customer": the file starts on 2026-01-01, so early weeks label everyone "first seen".
The Tuesday excess E = Tuesday - baseline is split EXACTLY into four parts (midpoint split of the C x t product):
    (d) no Customer ID:                         dA
    (b) more transactions per identified cust.: dt x mean(C_T, C_B)
    (c1) more customers seen before this week:  dC_old x mean(t_T, t_B)
    (c2) more customers first seen this week:   dC_first x mean(t_T, t_B)
    (a) more distinct identified customers = c1 + c2.
Shares are pooled over weeks (sum of a component / sum of E). 95% CIs: bootstrap that resamples whole weeks (all branches
together). IDs are unreliable (Finding 1: 94% of known customers appear at several branches), so this is a description of IDs,
not necessarily of people. Nothing here shows WHY customers came on Tuesday.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import SEED, save_fig
from load import load_clean, save_table

rng = np.random.default_rng(SEED)
N_BOOT = 2000
BURN_IN_WEEKS = 8
d = load_clean()
tx = d.groupby("Transaction ID").agg(date=("date", "first"), branch=("Branch", "first"),
                                     cust=("Customer ID", "first")).reset_index()
assert d.groupby("Transaction ID")["Customer ID"].nunique().max() <= 1      # one customer per transaction
tx["weekday"] = tx.date.dt.dayofweek
tx["week"] = tx.date - pd.to_timedelta(tx.weekday, unit="D")
first_seen_week = tx.dropna(subset=["cust"]).groupby("cust").date.min()
first_seen_week = first_seen_week - pd.to_timedelta(first_seen_week.dt.dayofweek, unit="D")
tx["first_this_week"] = tx.cust.map(first_seen_week) == tx.week          # False for anonymous rows (not used)
first_monday = tx.date.min() + pd.Timedelta(days=(7 - tx.date.min().dayofweek) % 7)
last_sunday = tx.date.max() - pd.Timedelta(days=(tx.date.max().dayofweek + 1) % 7)
full = tx[(tx.date >= first_monday) & (tx.date <= last_sunday)].copy()
weeks = sorted(full.week.unique())
print(f"transactions {len(tx):,}; {len(weeks)} full weeks {weeks[0].date()} .. {weeks[-1].date()}; "
      f"identified {tx.cust.notna().mean():.1%} of transactions")

# ---- per branch x day counts ----
ident = full[full.cust.notna()]
day = pd.DataFrame({
    "n_tx": full.groupby(["branch", "week", "weekday"]).size(),
    "A": full[full.cust.isna()].groupby(["branch", "week", "weekday"]).size(),
    "tx_id": ident.groupby(["branch", "week", "weekday"]).size(),
    "C": ident.groupby(["branch", "week", "weekday"]).cust.nunique(),
    "C_first": ident[ident.first_this_week].groupby(["branch", "week", "weekday"]).cust.nunique(),
}).fillna(0)
day["C_old"] = day.C - day.C_first
assert (day.n_tx == day.A + day.tx_id).all()

rows = []
for (b, w), g in day.reset_index().groupby(["branch", "week"]):
    g = g.set_index("weekday")[["n_tx", "A", "tx_id", "C", "C_first", "C_old"]]
    T = g.loc[1]
    B = g.loc[[0, 2, 3, 4]].mean()
    tT, tB = T.tx_id / T.C, B.tx_id / B.C
    tbar, cbar = (tT + tB) / 2, (T.C + B.C) / 2
    r = {"branch": b, "week": w, "tuesday_tx": T.n_tx, "baseline_tx": B.n_tx, "excess": T.n_tx - B.n_tx,
         "tuesday_customers": T.C, "baseline_customers": B.C, "t_tuesday": tT, "t_baseline": tB,
         "d_no_id": T.A - B.A, "b_more_tx_per_customer": (tT - tB) * cbar,
         "c1_more_customers_seen_before": (T.C_old - B.C_old) * tbar,
         "c2_more_customers_first_seen_this_week": (T.C_first - B.C_first) * tbar}
    assert abs(r["excess"] - (r["d_no_id"] + r["b_more_tx_per_customer"] + r["c1_more_customers_seen_before"]
                              + r["c2_more_customers_first_seen_this_week"])) < 1e-9     # exact decomposition
    rows.append(r)
wk = pd.DataFrame(rows)
save_table(wk.round(3), "tuesday_decomp_weekly.csv", index=False)
COMP = ["d_no_id", "b_more_tx_per_customer", "c1_more_customers_seen_before", "c2_more_customers_first_seen_this_week"]
print("exact decomposition verified for every branch-week (components sum to the excess)")

# ---- shares with week-block bootstrap ----
wk_idx = {w: i for i, w in enumerate(weeks)}
wk["wi"] = wk.week.map(wk_idx)


def shares(frame, sel_weeks):
    f = frame[frame.wi.isin(sel_weeks)]
    tot = f.excess.sum()
    out = {c: f[c].sum() / tot for c in COMP}
    out["a_more_identified_customers"] = out["c1_more_customers_seen_before"] + out["c2_more_customers_first_seen_this_week"]
    out["excess_per_week"] = tot / len(sel_weeks)
    return out


def table(scope_name, frame, sel_weeks):
    est = shares(frame, list(sel_weeks))
    boots = []
    for _ in range(N_BOOT):
        boots.append(_boot_share(frame, rng.choice(list(sel_weeks), len(sel_weeks))))
    boots = pd.DataFrame(boots)
    out = []
    for k_ in ["d_no_id", "b_more_tx_per_customer", "a_more_identified_customers",
               "c1_more_customers_seen_before", "c2_more_customers_first_seen_this_week"]:
        lo, hi = np.percentile(boots[k_], [2.5, 97.5])
        out.append({"scope": scope_name, "component": k_, "share_of_tuesday_excess": est[k_], "ci_low": lo, "ci_high": hi,
                    "transactions_per_week": est[k_] * est["excess_per_week"]})
    out.append({"scope": scope_name, "component": "TOTAL excess (transactions per week)", "share_of_tuesday_excess": 1.0,
                "ci_low": np.nan, "ci_high": np.nan, "transactions_per_week": est["excess_per_week"]})
    return out


def _boot_share(frame, picks):
    """Shares for a bootstrap sample of weeks (with repeats) without rebuilding the frame each time."""
    f = frame.set_index("wi")
    idx = np.asarray(picks)
    sums = {c: f[c].groupby(level=0).sum().reindex(range(len(weeks)), fill_value=0).values[idx].sum() for c in COMP}
    e = f.excess.groupby(level=0).sum().reindex(range(len(weeks)), fill_value=0).values[idx].sum()
    out = {c: sums[c] / e for c in COMP}
    out["a_more_identified_customers"] = out["c1_more_customers_seen_before"] + out["c2_more_customers_first_seen_this_week"]
    return out


allw = list(range(len(weeks)))
res = []
overall = wk.groupby(["week", "wi"], as_index=False)[["excess"] + COMP].sum()      # sum of the three branches' components
res += table("all branches (sum of branch-level components)", overall, allw)
for b in ["Garden", "Harbour", "Uptown"]:
    res += table(b, wk[wk.branch == b], allw)
post = list(range(BURN_IN_WEEKS, len(weeks)))
res += table(f"all branches, weeks {BURN_IN_WEEKS + 1}-{len(weeks)} only (after burn-in)", overall, post)
sh = pd.DataFrame(res).round(4)
save_table(sh, "tuesday_decomp_shares.csv", index=False)
print(f"\nMEASURED: share of the Tuesday excess by component (95% CI = bootstrap over weeks, {N_BOOT} resamples)")
print(sh.to_string(index=False))

# average customers and trips per customer on Tuesday vs baseline
cmp_ = wk.groupby("branch")[["tuesday_tx", "baseline_tx", "tuesday_customers", "baseline_customers", "t_tuesday", "t_baseline"]].mean().round(3)
print("\nweekly means by branch (Tuesday vs mean of Mon/Wed/Thu/Fri):\n", cmp_.to_string())
save_table(cmp_, "tuesday_decomp_means.csv")

# ---- first-seen share trend (the label is left-censored: the file starts on 2026-01-01) ----
fs = full[full.cust.notna()].groupby("week").first_this_week.mean()
print(f"\nshare of identified transactions by a customer 'first seen this week': week 1 {fs.iloc[0]:.1%}, week 8 {fs.iloc[7]:.1%}, "
      f"week 9 {fs.iloc[8]:.1%}, last week {fs.iloc[-1]:.1%}  (falls because the file starts in January)")
save_table(fs.round(4).rename("share_first_seen_this_week").to_frame(), "tuesday_decomp_first_seen_trend.csv")

# ---- who comes on Tuesday: distinct customers, not transactions ----
idt = tx[tx.cust.notna()].copy()
days_by_cust = idt.groupby("cust").weekday.agg(lambda s: set(s))
visits = idt.groupby("cust").size()
rows = []
for wd, name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
    custs = days_by_cust[days_by_cust.apply(lambda s: wd in s)].index
    other = days_by_cust.loc[custs].apply(lambda s: len(s - {wd}) > 0)
    v = idt[idt.cust.isin(custs)].groupby("cust").weekday.agg(lambda s: (s == wd).mean())
    rows.append({"weekday": name, "distinct_customers": len(custs), "share_who_also_buy_other_days": other.mean(),
                 "mean_share_of_their_visits_on_this_day": v.mean(),
                 "share_with_all_visits_on_this_day": (v == 1.0).mean(),
                 "share_with_all_visits_on_this_day_among_2plus_visits": (v[visits.loc[custs] >= 2] == 1.0).mean()})
wdt = pd.DataFrame(rows).round(4)
save_table(wdt, "tuesday_decomp_customers_by_weekday.csv", index=False)
print("\nMEASURED: distinct identified customers by weekday (customers who bought on that weekday at least once)\n", wdt.to_string(index=False))

# Tuesday-only regulars: among customers with >=4 visits, how many have >=50% of visits on Tuesday?  vs random weekday labels
reg = visits[visits >= 4].index
sub = idt[idt.cust.isin(reg)].reset_index(drop=True)
obs_share = (sub.weekday == 1).groupby(sub.cust).mean()
stat = lambda s: (s >= 0.5).sum()
obs_n = stat(obs_share)
null = []
wd_arr = sub.weekday.values.copy()
cust_codes = pd.factorize(sub.cust)[0]
for _ in range(2000):
    sh_ = rng.permutation(wd_arr)      # shuffle weekday labels across all identified transactions of these customers
    s = pd.Series(sh_ == 1).groupby(cust_codes).mean()
    null.append(stat(s))
null = np.array(null)
p_null = ((sub.weekday == 1).mean())
print(f"\nTuesday-heavy regulars: customers with >=4 visits: {len(reg):,}. Tuesday is {p_null:.1%} of their visits. "
      f"Customers with >=50% of visits on Tuesday: observed {obs_n}, if weekdays were random {null.mean():.1f} "
      f"(95% range {np.percentile(null, 2.5):.0f}-{np.percentile(null, 97.5):.0f})")
vv = visits[visits >= 4]
tue_only = ((obs_share == 1.0)).sum()
print(f"customers with >=4 visits and ALL visits on Tuesday: {tue_only}")
print(f"Spread of Tuesday share of visits among >=4-visit customers: mean {obs_share.mean():.3f}, std {obs_share.std():.3f}; "
      f"std if weekdays were random {np.mean([pd.Series(rng.permutation(wd_arr) == 1).groupby(cust_codes).mean().std() for _ in range(300)]):.3f}")
save_table(pd.DataFrame({"customers_4plus_visits": [len(reg)], "tuesday_share_of_their_visits": [round(p_null, 4)],
                         "observed_customers_ge50pct_tuesday": [obs_n], "null_mean": [round(null.mean(), 2)],
                         "null_ci_low": [np.percentile(null, 2.5)], "null_ci_high": [np.percentile(null, 97.5)],
                         "customers_all_visits_on_tuesday": [int(tue_only)]}),
           "tuesday_decomp_tuesday_regulars.csv", index=False)

# ---- do Tuesday visits replace visits on other days, or add to them? (same customers, weeks with vs without that weekday) ----
fw = idt[(idt.date >= first_monday) & (idt.date <= last_sunday)]
cc, wi_ = pd.factorize(fw.cust)[0], fw.week.map(wk_idx).values
cnt = np.zeros((cc.max() + 1, len(weeks), 7))
np.add.at(cnt, (cc, wi_, fw.weekday.values), 1)
total_c = cnt.sum(2)


def displacement(wd):
    has = cnt[:, :, wd] > 0
    other = total_c - cnt[:, :, wd]
    n_has, n_not = has.sum(1), (~has).sum(1)
    ok = (n_has >= 2) & (n_not >= 2)
    m_has = (other * has).sum(1) / np.maximum(n_has, 1)
    m_not = (other * ~has).sum(1) / np.maximum(n_not, 1)
    return (m_has - m_not)[ok]


disp_rows = []
for wd, name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
    dd_ = displacement(wd)
    bs_ = [rng.choice(dd_, len(dd_)).mean() for _ in range(1000)]
    disp_rows.append({"weekday": name, "customers_compared": len(dd_), "other_day_visits_in_weeks_with_minus_without": dd_.mean(),
                      "ci_low": np.percentile(bs_, 2.5), "ci_high": np.percentile(bs_, 97.5)})
disp = pd.DataFrame(disp_rows).round(4)
save_table(disp, "tuesday_decomp_displacement.csv", index=False)
print("\nMEASURED: for the same customer, visits on OTHER days in weeks with a visit on this weekday minus weeks without "
      "(negative = visits replace each other; ~0 = independent)\n", disp.to_string(index=False))

# ---- figures ----
fig, ax = plt.subplots(figsize=(9, 4.8))
scopes = ["all branches (sum of branch-level components)", "Garden", "Harbour", "Uptown"]
labels = ["All", "Garden", "Harbour", "Uptown"]
cols = {"d_no_id": "#95a5a6", "b_more_tx_per_customer": "#e67e22", "c1_more_customers_seen_before": "#2980b9",
        "c2_more_customers_first_seen_this_week": "#85c1e9"}
names = {"d_no_id": "(d) no Customer ID", "b_more_tx_per_customer": "(b) more trips per identified customer",
         "c1_more_customers_seen_before": "(c1) more customers, seen before this week",
         "c2_more_customers_first_seen_this_week": "(c2) more customers, first seen in the data this week"}
bottom = np.zeros(len(scopes))
for c in cols:
    vals = np.array([sh[(sh.scope == s) & (sh.component == c)].share_of_tuesday_excess.iloc[0] for s in scopes]) * 100
    ax.bar(labels, vals, bottom=bottom, color=cols[c], label=names[c])
    bottom += vals
ax.axhline(100, color="black", lw=0.6)
ax.set_title("What the extra Tuesday transactions are made of (share of the Tuesday excess)")
ax.set_xlabel("Branch")
ax.set_ylabel("% of Tuesday excess")
ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2)
save_fig(fig, "tuesday_decomp_components.png")

fig, ax = plt.subplots(figsize=(7, 4.2))
ax.hist(null, bins=np.arange(null.min() - 0.5, max(null.max(), obs_n) + 1.5, 1), color="#bdc3c7", label="random weekdays (2,000 shuffles)")
ax.axvline(obs_n, color="#c0392b", lw=2, label=f"observed ({obs_n})")
ax.set_title("Customers with 4+ visits and at least half of them on Tuesday")
ax.set_xlabel("Number of such customers")
ax.set_ylabel("Shuffles")
ax.legend()
save_fig(fig, "tuesday_decomp_regulars.png")
print("\nsaved figures/tuesday_decomp_components.png, tuesday_decomp_regulars.png")
