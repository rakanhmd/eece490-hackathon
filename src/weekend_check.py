"""Does Tuesday's extra volume offset the previous weekend's shortfall?  And where does the takeaway share drop?

Hypotheses only: this script measures associations in the transaction file. It cannot say WHY Tuesday is busy or
why takeaway falls at 18:00. A comparison with till or bank totals (see FINDING_weekend.md) is the check that could.

Definitions (transactions after removing exact duplicates, full Mon-Sun weeks only):
  baseline_w    = mean daily transactions on Mon, Wed, Thu, Fri of week w
  tuesday_excess_w = Tuesday_w - baseline_w
  weekend_deficit_w = 2 * baseline_w - (Sat_w + Sun_w)      (positive = weekend weaker than a normal weekday)
"Previous weekend" for week w is the Sat+Sun of week w-1 (measured against week w-1's own baseline);
"same-week weekend" is the Sat+Sun that follows the Tuesday of week w.
"""
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import SEED, save_fig
from load import load_clean, save_table

rng = np.random.default_rng(SEED)
N_PERM = 10000
d = load_clean()
tx = d.groupby("Transaction ID").agg(date=("date", "first"), time=("Time", "first"), hour=("hour", "first"),
                                     branch=("Branch", "first"), order=("Order Type", "first")).reset_index()
tx["weekday"] = tx.date.dt.dayofweek
tx["week_start"] = tx.date - pd.to_timedelta(tx.weekday, unit="D")
first_full = tx.date.min() + pd.Timedelta(days=(7 - tx.date.min().dayofweek) % 7)      # first Monday
last_full = tx.date.max() - pd.Timedelta(days=(tx.date.max().dayofweek + 1) % 7)       # last Sunday before the final partial week
print(f"transactions {len(tx):,}; full weeks from Monday {first_full.date()} to Sunday {last_full.date()}")


def weekly_table(t):
    daily = t.groupby("date").size().reindex(pd.date_range(first_full, last_full), fill_value=0).rename("tx").to_frame()
    daily["week_start"] = daily.index - pd.to_timedelta(daily.index.dayofweek, unit="D")
    daily["wd"] = daily.index.dayofweek
    w = daily.pivot(index="week_start", columns="wd", values="tx")
    out = pd.DataFrame({"baseline": w[[0, 2, 3, 4]].mean(axis=1), "tuesday": w[1], "saturday": w[5], "sunday": w[6]})
    out["tuesday_excess"] = out.tuesday - out.baseline
    out["weekend_deficit"] = 2 * out.baseline - (out.saturday + out.sunday)
    out["tuesday_excess_rel"] = out.tuesday_excess / out.baseline            # relative: removes the growth in volume
    out["weekend_deficit_rel"] = out.weekend_deficit / (2 * out.baseline)
    out["prev_weekend_deficit"] = out.weekend_deficit.shift(1)
    out["prev_weekend_deficit_rel"] = out.weekend_deficit_rel.shift(1)
    out["prev_baseline"] = out.baseline.shift(1)
    return out


wk = weekly_table(tx)
save_table(wk.round(4), "weekend_weekly.csv")
print(f"\nMEASURED: {len(wk)} full weeks. Per week, averages: baseline weekday {wk.baseline.mean():.0f} tx/day, "
      f"Tuesday {wk.tuesday.mean():.0f}, Saturday {wk.saturday.mean():.0f}, Sunday {wk.sunday.mean():.0f}")
print(f"Tuesday excess averages {wk.tuesday_excess.mean():.0f} tx/week ({100 * wk.tuesday_excess_rel.mean():.0f}% above baseline); "
      f"weekend deficit averages {wk.weekend_deficit.mean():.0f} tx/week ({100 * wk.weekend_deficit_rel.mean():.0f}% below two baseline days)")


# ---------- correlations and permutation tests ----------
def perm_corr(x, y, n=N_PERM):
    """Pearson r; two-sided and one-sided (r > 0, the 'offset' direction) permutation p-values; circular-shift p-value too."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    r = np.corrcoef(x, y)[0, 1]
    null = np.array([np.corrcoef(x, rng.permutation(y))[0, 1] for _ in range(n)])
    shifts = np.array([np.corrcoef(x, np.roll(y, s))[0, 1] for s in range(1, len(y))])      # keeps trend/autocorrelation
    return {"r": r, "p_perm_two_sided": (1 + (np.abs(null) >= abs(r)).sum()) / (n + 1),
            "p_perm_one_sided_pos": (1 + (null >= r).sum()) / (n + 1),
            "p_circular_shift_two_sided": (1 + (np.abs(shifts) >= abs(r)).sum()) / (len(shifts) + 1)}


def partial_r(x, y, Z):
    """Correlation of x and y after removing a linear effect of the control columns Z (baseline volumes) from both."""
    A = np.column_stack([np.ones(len(x)), Z])
    rx = x - A @ np.linalg.lstsq(A, x, rcond=None)[0]
    ry = y - A @ np.linalg.lstsq(A, y, rcond=None)[0]
    return np.corrcoef(rx, ry)[0, 1]


def fisher_ci(r, n):
    zr, se = np.arctanh(r), 1 / np.sqrt(n - 3)
    return np.tanh(zr - 1.96 * se), np.tanh(zr + 1.96 * se)


rows = []


def add_test(label, scope, df, xcol, ycol, ctrl):
    ctrls = [ctrl] if isinstance(ctrl, str) else ctrl
    s = df[list(dict.fromkeys([xcol, ycol] + ctrls))].dropna()
    res = perm_corr(s[xcol], s[ycol])
    lo, hi = fisher_ci(res["r"], len(s))
    rho, p_sp = stats.spearmanr(s[xcol], s[ycol])
    rows.append({"scope": scope, "tuesday_excess_vs": label, "x_y": f"{xcol} ~ {ycol}", "n_weeks": len(s), "pearson_r": res["r"],
                 "r_ci_low": lo, "r_ci_high": hi, "spearman_rho": rho, "spearman_p": p_sp,
                 "p_perm_two_sided": res["p_perm_two_sided"], "p_perm_one_sided_pos": res["p_perm_one_sided_pos"],
                 "p_circular_shift": res["p_circular_shift_two_sided"],
                 "partial_r_given_baseline": partial_r(s[xcol].values, s[ycol].values, s[ctrls].values) if ycol not in ctrls else np.nan})


for scope, t in [("all branches", tx)] + [(b, tx[tx.branch == b]) for b in ["Garden", "Harbour", "Uptown"]]:
    w = weekly_table(t) if scope != "all branches" else wk
    add_test("previous weekend deficit (relative)", scope, w, "tuesday_excess_rel", "prev_weekend_deficit_rel", ["baseline", "prev_baseline"])
    add_test("same-week weekend deficit (relative)", scope, w, "tuesday_excess_rel", "weekend_deficit_rel", "baseline")
    if scope == "all branches":
        add_test("previous weekend deficit (counts)", scope, w, "tuesday_excess", "prev_weekend_deficit", ["baseline", "prev_baseline"])
        add_test("same-week weekend deficit (counts)", scope, w, "tuesday_excess", "weekend_deficit", "baseline")
        add_test("(control) baseline volume", scope, w, "tuesday_excess", "baseline", "baseline")
tests = pd.DataFrame(rows).round(4)
save_table(tests, "weekend_offset_tests.csv", index=False)
print("\nMEASURED: weekly Tuesday excess vs weekend deficit (permutation = 10,000 shuffles of the weeks; the 'offset' story predicts r > 0)")
print(tests[["scope", "tuesday_excess_vs", "n_weeks", "pearson_r", "r_ci_low", "r_ci_high", "p_perm_two_sided",
             "p_perm_one_sided_pos", "p_circular_shift", "partial_r_given_baseline"]].to_string(index=False))

# does the deficit even exist week to week? and size comparison
print(f"\nSize comparison, whole period: Tuesday excess {wk.tuesday_excess.sum():,.0f} transactions, "
      f"weekend deficit {wk.weekend_deficit.sum():,.0f} transactions (ratio {wk.tuesday_excess.sum() / wk.weekend_deficit.sum():.2f})")
share_tue_weeks = (wk.tuesday_excess > 0).mean()
print(f"Tuesday above baseline in {100 * share_tue_weeks:.0f}% of weeks; weekend below baseline in {100 * (wk.weekend_deficit > 0).mean():.0f}% of weeks")
print(f"Tuesday excess relative to baseline: min {wk.tuesday_excess_rel.min():.2f}, median {wk.tuesday_excess_rel.median():.2f}, max {wk.tuesday_excess_rel.max():.2f}; "
      f"weekend deficit relative: min {wk.weekend_deficit_rel.min():.2f}, median {wk.weekend_deficit_rel.median():.2f}, max {wk.weekend_deficit_rel.max():.2f}")
save_table(pd.DataFrame({"tuesday_excess_total": [wk.tuesday_excess.sum()], "weekend_deficit_total": [wk.weekend_deficit.sum()],
                         "ratio": [wk.tuesday_excess.sum() / wk.weekend_deficit.sum()], "weeks": [len(wk)]}).round(3),
           "weekend_size_comparison.csv", index=False)

# ---------- takeaway share by hour ----------
tx["takeaway"] = tx.order == "Takeaway"
hr = tx.groupby("hour").takeaway.agg(["sum", "size"])
hr["takeaway_share"] = hr["sum"] / hr["size"]
z = 1.96
hr["ci_low"] = (hr.takeaway_share + z**2 / (2 * hr["size"]) - z * np.sqrt(hr.takeaway_share * (1 - hr.takeaway_share) / hr["size"] + z**2 / (4 * hr["size"]**2))) / (1 + z**2 / hr["size"])
hr["ci_high"] = (hr.takeaway_share + z**2 / (2 * hr["size"]) + z * np.sqrt(hr.takeaway_share * (1 - hr.takeaway_share) / hr["size"] + z**2 / (4 * hr["size"]**2))) / (1 + z**2 / hr["size"])
hr = hr.rename(columns={"sum": "takeaway_tx", "size": "transactions"}).round(4)
save_table(hr, "weekend_takeaway_by_hour.csv")
print("\nMEASURED: takeaway share of transactions by hour\n", hr[["transactions", "takeaway_share", "ci_low", "ci_high"]].to_string())
bef, aft = tx[(tx.hour >= 7) & (tx.hour < 18)], tx[tx.hour >= 18]
p1, p2 = bef.takeaway.mean(), aft.takeaway.mean()
print(f"07:00-17:59 takeaway {p1:.1%} ({len(bef):,} tx); 18:00-23:59 {p2:.1%} ({len(aft):,} tx); share of all transactions at 18:00 or later {len(aft) / len(tx):.1%}")
# is the drop at 18:00 in every branch, weekday and month? (a behavioural change would be gradual / vary; a rule is abrupt and uniform)
seg_rows = []
for dim in ["branch", "weekday", "month"]:
    col = tx[dim] if dim in tx else tx.date.dt.month
    for lvl, g in tx.assign(seg=col).groupby("seg"):
        b_, a_ = g[(g.hour >= 7) & (g.hour < 18)].takeaway.mean(), g[g.hour >= 18].takeaway.mean()
        seg_rows.append({"dimension": dim, "level": lvl, "takeaway_before_18": b_, "takeaway_from_18": a_, "drop_points": 100 * (b_ - a_)})
seg_t = pd.DataFrame(seg_rows).round(4)
save_table(seg_t, "weekend_takeaway_drop_by_segment.csv", index=False)
print("drop (points) by segment: min %.1f, max %.1f" % (seg_t.drop_points.min(), seg_t.drop_points.max()))
# minute-level look around 18:00 (15-minute bins from 16:00 to 20:00): abrupt step or slope?
tx["minute_of_day"] = pd.to_datetime(tx.time, format="%H:%M:%S").dt.hour * 60 + pd.to_datetime(tx.time, format="%H:%M:%S").dt.minute
zoom = tx[(tx.minute_of_day >= 16 * 60) & (tx.minute_of_day < 20 * 60)].copy()
zoom["bin"] = (zoom.minute_of_day // 15) * 15
zb = zoom.groupby("bin").takeaway.agg(["mean", "size"]).rename(columns={"mean": "takeaway_share", "size": "transactions"}).round(4)
zb.index = [f"{i // 60:02d}:{i % 60:02d}" for i in zb.index]
save_table(zb, "weekend_takeaway_15min.csv")
print("\nMEASURED: takeaway share in 15-minute bins around 18:00\n", zb.T.to_string())
# Tuesday vs other days: do the extra Tuesday transactions look different?
tue = tx[tx.weekday == 1]
oth = tx[tx.weekday.isin([0, 2, 3, 4])]
print(f"takeaway share: Tuesday {tue.takeaway.mean():.1%}, Mon/Wed/Thu/Fri {oth.takeaway.mean():.1%}, Sat/Sun {tx[tx.weekday >= 5].takeaway.mean():.1%}")

# ---------- figures ----------
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(wk.index, wk.tuesday_excess, marker="o", ms=3, label="Tuesday excess (tx above Mon/Wed/Thu/Fri average)", color="#c0392b")
ax.plot(wk.index, wk.weekend_deficit, marker="s", ms=3, label="Sat+Sun deficit (2 x baseline - Sat - Sun)", color="#2c3e50")
ax.axhline(0, color="grey", lw=0.8)
ax.set_title("Weekly Tuesday excess and weekend deficit, all branches (transactions)")
ax.set_xlabel("Week starting")
ax.set_ylabel("Transactions per week")
ax.legend(fontsize=8)
save_fig(fig, "weekend_weekly_series.png")

fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
for ax, col, lab, test_label in [(axes[0], "prev_weekend_deficit_rel", "previous weekend deficit (share of 2 baseline days)", "previous weekend deficit (relative)"),
                                 (axes[1], "weekend_deficit_rel", "same-week weekend deficit (share of 2 baseline days)", "same-week weekend deficit (relative)")]:
    s = wk[[col, "tuesday_excess_rel"]].dropna()
    ax.scatter(100 * s[col], 100 * s.tuesday_excess_rel, color="#4c78a8")
    tr = tests[(tests.scope == "all branches") & (tests.tuesday_excess_vs == test_label)].iloc[0]
    ax.set_title(f"r = {tr.pearson_r:+.2f} (permutation p = {tr.p_perm_two_sided:.2f}, n = {int(tr.n_weeks)})", fontsize=10)
    ax.set_xlabel(lab + ", %")
axes[0].set_ylabel("Tuesday excess over baseline, %")
fig.suptitle("Does a weaker weekend go with a bigger Tuesday? (each dot = one week)")
save_fig(fig, "weekend_offset_scatter.png")

fig, axes = plt.subplots(1, 2, figsize=(11, 4.3), gridspec_kw={"width_ratios": [1.4, 1]})
ax = axes[0]
ax.errorbar(hr.index, 100 * hr.takeaway_share, yerr=100 * np.vstack([hr.takeaway_share - hr.ci_low, hr.ci_high - hr.takeaway_share]),
            marker="o", color="#2c3e50", capsize=3)
ax.axvline(17.5, color="#c0392b", ls="--", lw=1)
ax.set_title("Takeaway share of transactions by hour (95% CI)")
ax.set_xlabel("Hour of day (hour starting)")
ax.set_ylabel("Takeaway share (%)")
ax.set_ylim(0, 70)
ax = axes[1]
ax.plot(zb.index, 100 * zb.takeaway_share, marker="o", color="#2c3e50")
ax.axvline("18:00", color="#c0392b", ls="--", lw=1)
ax.set_title("Zoom: 15-minute bins, 16:00-20:00")
ax.set_xlabel("Start of 15-minute bin")
ax.set_ylabel("Takeaway share (%)")
ax.set_ylim(0, 70)
plt.setp(ax.get_xticklabels(), rotation=60, fontsize=8)
save_fig(fig, "weekend_takeaway_by_hour.png")
print("\nsaved figures/weekend_weekly_series.png, weekend_offset_scatter.png, weekend_takeaway_by_hour.png")
