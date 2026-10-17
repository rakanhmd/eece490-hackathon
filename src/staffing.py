"""Hourly demand forecast per branch x weekday x hour, and a staffing SCENARIO built on it.

Target:  transactions per branch per calendar hour (07:00-23:59), zero-filled.
Evaluation: ROLLING ORIGINS at a fixed horizon. Every Sunday night from 1 March (8 full weeks of history) a model is refitted on
         everything before the coming Monday and forecasts that Monday-Sunday (1 to 7 days ahead), which is how a weekly roster
         would be built. 17 weekly origins cover forecast weeks from Mon 2 Mar to Sun 28 Jun. Test months are April, May and June:
         for each, the model is chosen among the candidates on the forecast weeks completed before that month's first origin
         (so April uses March only, June uses March-May), then scored on that month's weeks. Nothing is chosen on test weeks.
Baselines: same branch, same hour, same weekday last week (the count 7 days earlier) and the mean of the same hour over the four
         previous same weekdays. Both use only data available at the origin, so every method has the same information and the
         same lead time. The dummy is the branch mean.
Uncertainty: contiguous-week block bootstrap on weekly paired differences, all branches and hours of a week kept together.
Staffing: a SCENARIO under three assumptions that are not in the data (service rate, minimum crew, how breaks and hourly changes
         are handled). It is not measured against Stories' actual rosters.
Note on the 18:00 step: dine-in/takeaway shares jump at 18:00 (FINDING_weekend.md), possibly a till default. This script
forecasts transaction counts, which do not depend on order type; if table service needs more labour than counter service,
the order-type record must be checked before it is used for staffing.
"""
import os

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import PoissonRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import RESULTS_CSV, SEED, log_result, save_fig
from load import load_clean, save_table

rng = np.random.default_rng(SEED)
d = load_clean()
BRANCHES = ["Garden", "Harbour", "Uptown"]
HOURS = list(range(7, 24))
tx = d.groupby("Transaction ID").agg(date=("date", "first"), hour=("hour", "first"), branch=("Branch", "first")).reset_index()
dates = pd.date_range(tx.date.min(), tx.date.max())
grid = pd.MultiIndex.from_product([BRANCHES, dates, HOURS], names=["branch", "date", "hour"]).to_frame(index=False)
cnt = tx.groupby(["branch", "date", "hour"]).size().rename("n").reset_index()
grid = grid.merge(cnt, how="left", on=["branch", "date", "hour"]).fillna({"n": 0})
grid["weekday"] = grid.date.dt.dayofweek
grid["t"] = (grid.date - grid.date.min()).dt.days / 30.0
grid["lag7"] = grid.groupby(["branch", "hour"]).n.shift(7)
print(f"hours {HOURS[0]}-{HOURS[-1]}: {len(grid):,} branch-date-hour cells; mean {grid.n.mean():.2f} transactions per cell, "
      f"max {grid.n.max():.0f}; share of cells with zero: {(grid.n == 0).mean():.1%}")
# four-week same-weekday mean (context baseline)
grid["mean4w"] = np.nan
for k in (7, 14, 21, 28):
    grid["mean4w"] = grid["mean4w"].add(grid.groupby(["branch", "hour"]).n.shift(k), fill_value=0)
grid.loc[grid.date < grid.date.min() + pd.Timedelta(days=28), "mean4w"] = np.nan
grid["mean4w"] = grid["mean4w"] / 4

TRAIN_END, VAL = pd.Timestamp("2026-04-30"), (pd.Timestamp("2026-05-01"), pd.Timestamp("2026-05-31"))
TEST = (pd.Timestamp("2026-06-01"), pd.Timestamp("2026-06-30"))


def split(a, b):
    return grid[(grid.date >= a) & (grid.date <= b)].copy()


# ---------------- models ----------------
def fit_predict(kind, train, test):
    """Predicted transactions for the rows of `test`, fitted on `train` only."""
    if kind == "dummy":
        return test.branch.map(train.groupby("branch").n.mean()).values
    if kind == "same_hour_last_week":
        return test.lag7.values
    if kind == "mean_last_4_same_weekdays":
        return test.mean4w.values
    if kind == "profile_trend":
        # branch x weekday x hour mean of detrended counts, multiplied by the branch's growth trend (log-linear on daily totals)
        out = np.zeros(len(test))
        for b in BRANCHES:
            tr = train[train.branch == b]
            daily = tr.groupby("date").n.sum()
            slope = np.polyfit((daily.index - daily.index[0]).days.values, np.log(daily.values.clip(1)), 1)[0]
            f = lambda dt: np.exp(slope * (pd.Series(np.asarray(dt)) - tr.date.min()).dt.days.values)
            prof = (tr.n.values / f(tr.date)).copy()
            prof = pd.Series(prof, index=tr.index).groupby([tr.weekday, tr.hour]).mean()
            m = (test.branch == b).values
            key = pd.MultiIndex.from_arrays([test.weekday[m], test.hour[m]])
            out[m] = prof.reindex(key).values * f(test.date[m])
        return out
    cols = ["branch", "weekday", "hour"]
    if kind.startswith("poisson_glm"):
        alpha = float(kind.split("_a")[1])
        X = lambda df: df.assign(bh=df.branch + "_" + df.hour.astype(str), wh=df.weekday.astype(str) + "_" + df.hour.astype(str),
                                 bw=df.branch + "_" + df.weekday.astype(str))
        feats = ["branch", "weekday", "hour", "bh", "wh", "bw"]
        pre = ColumnTransformer([("c", OneHotEncoder(handle_unknown="ignore"), feats)], remainder="passthrough")
        m = Pipeline([("p", pre), ("m", PoissonRegressor(alpha=alpha, max_iter=2000))])
        Xtr, Xte = X(train)[feats + ["t"]], X(test)[feats + ["t"]]
        m.fit(Xtr, train.n)
        return m.predict(Xte)
    if kind.startswith("gboost_poisson"):
        depth, lr_, it = [float(x) for x in kind.split("_")[2:]]
        Xtr, Xte = train[cols + ["t"]].copy(), test[cols + ["t"]].copy()
        for c in cols:
            Xtr[c] = Xtr[c].astype("category")
            Xte[c] = pd.Categorical(Xte[c], categories=Xtr[c].cat.categories)
        m = HistGradientBoostingRegressor(loss="poisson", max_depth=int(depth), learning_rate=lr_, max_iter=int(it),
                                          min_samples_leaf=50, categorical_features="from_dtype", random_state=SEED)
        return m.fit(Xtr, train.n).predict(Xte)
    raise ValueError(kind)


KINDS = ["dummy", "same_hour_last_week", "mean_last_4_same_weekdays", "profile_trend",
         "poisson_glm_a0.001", "poisson_glm_a0.01", "poisson_glm_a0.1",
         "gboost_poisson_3_0.05_200", "gboost_poisson_4_0.05_300"]
FITTED = [k for k in KINDS if k.startswith(("profile", "poisson", "gboost"))]


def mae(df, p):
    ok = ~np.isnan(p)
    return float(np.abs(df.n.values[ok] - p[ok]).mean()), int(ok.sum())


def score_row(df, p):
    row = {"mae_all": mae(df, p)[0]}
    for b in BRANCHES:
        m = (df.branch == b).values
        row[f"mae_{b}"] = mae(df[m], p[m])[0]
    tot = np.abs(df.n.values - p).sum() if not np.isnan(p).any() else np.nan
    row["wape_pct"] = 100 * tot / df.n.sum() if not np.isnan(tot) else np.nan
    return {k: round(float(v), 4) for k, v in row.items()}


# the script replaces its own rows in the shared log on a re-run
OLD_SPLITS = ["val_may_hourly", "test_june_hourly", "test_apr_jun_rolling"]
if os.path.exists(RESULTS_CSV):
    _r = pd.read_csv(RESULTS_CSV)
    _r[~_r.split.isin(OLD_SPLITS)].to_csv(RESULTS_CSV, index=False)

# ---------------- rolling-origin forecasts ----------------
FIRST = pd.Timestamp("2026-03-02")
mondays = [FIRST + pd.Timedelta(days=7 * i) for i in range(30) if FIRST + pd.Timedelta(days=7 * i + 6) <= grid.date.max()]
pieces = []
for m in mondays:
    train = grid[grid.date < m]
    test = grid[(grid.date >= m) & (grid.date <= m + pd.Timedelta(days=6))].copy()
    for k in KINDS:
        test[k] = fit_predict(k, train, test)
    test["origin"] = m
    pieces.append(test)
R = pd.concat(pieces, ignore_index=True)
R["month"] = R.origin.dt.month
R["lead_days"] = (R.date - R.origin).dt.days + 1
print(f"{len(mondays)} weekly origins; forecast weeks {mondays[0].date()} .. {(mondays[-1] + pd.Timedelta(days=6)).date()}; lead 1 to 7 days; "
      f"{len(R):,} branch-date-hour forecasts per method")
TEST_MONTHS = {4: "April", 5: "May", 6: "June"}
BASELINES = ["dummy", "same_hour_last_week", "mean_last_4_same_weekdays"]


def mae_of(df, col):
    return float(np.abs(df.n - df[col]).mean())


sel_rows, chosen = [], {}
for tm in TEST_MONTHS:
    first_origin = R.loc[R.month == tm, "origin"].min()
    sel = R[R.origin <= first_origin - pd.Timedelta(days=7)]            # weeks fully completed before this month's first origin
    scores = {k: mae_of(sel, k) for k in KINDS}
    chosen[tm] = min(FITTED, key=lambda k: scores[k])
    sel_rows.append({"test_month": TEST_MONTHS[tm], "selection_weeks": sel.origin.nunique(), "chosen_model": chosen[tm],
                     **{f"mae_{k}": v for k, v in scores.items()}})
selt = pd.DataFrame(sel_rows).round(4)
save_table(selt, "staffing_rolling_selection.csv", index=False)
print("\nMODEL CHOSEN BEFORE EACH TEST MONTH (MAE on the forecast weeks completed earlier; transactions per branch-hour)")
print(selt.T.to_string(header=False))
R["chosen"] = np.nan
for tm in TEST_MONTHS:
    mk = R.month == tm
    R.loc[mk, "chosen"] = R.loc[mk, chosen[tm]]
T = R[R.month.isin(TEST_MONTHS)].copy()
METHODS = {"dummy": "dummy (branch mean)", "same_hour_last_week": "same hour last week", "mean_last_4_same_weekdays": "mean of the last 4 same weekdays",
           "chosen": "chosen model (picked before each month)"}
res_rows = []
for col, label in METHODS.items():
    row = {"method": label}
    for tm, name in TEST_MONTHS.items():
        row[f"mae_{name}"] = mae_of(T[T.month == tm], col)
    row["mae_pooled"] = mae_of(T, col)
    row["wape_pct_pooled"] = 100 * np.abs(T.n - T[col]).sum() / T.n.sum()
    for b in BRANCHES:
        row[f"mae_{b}"] = mae_of(T[T.branch == b], col)
    res_rows.append(row)
res = pd.DataFrame(res_rows).round(4)
save_table(res, "staffing_rolling_results.csv", index=False)
print(f"\nROLLING-ORIGIN TEST, {T.origin.nunique()} forecast weeks (MAE in transactions per branch-hour)\n", res.to_string(index=False))
for col, label in METHODS.items():
    sc = {"mae_all": mae_of(T, col), "wape_pct": 100 * np.abs(T.n - T[col]).sum() / T.n.sum(),
          **{f"mae_{b}": mae_of(T[T.branch == b], col) for b in BRANCHES}}
    log_result("hourly_rolling_" + col, "test_apr_jun_rolling", {k_: round(v, 4) for k_, v in sc.items()},
               "weekly rolling origins, 1-7 days ahead; test weeks Apr-Jun; model chosen before each month on earlier weeks")
print("models chosen:", {TEST_MONTHS[k]: v for k, v in chosen.items()})
# context: every candidate over all 17 origins (March included, which is selection data for April, so descriptive only)
allm = pd.DataFrame({"mae_all_17_weeks": {k: mae_of(R, k) for k in KINDS}}).round(4)
save_table(allm, "staffing_rolling_all_candidates.csv")
print("\nall candidates, all 17 forecast weeks (descriptive; includes selection weeks):\n", allm.T.to_string())

# ---- contiguous-week block bootstrap, all branches and hours of a week together ----
wk = T.assign(e_c=(T.n - T.chosen).abs(), e_l=(T.n - T.same_hour_last_week).abs(), e_4=(T.n - T.mean_last_4_same_weekdays).abs(),
              e_d=(T.n - T.dummy).abs()).groupby("origin")[["e_c", "e_l", "e_4", "e_d"]].mean().sort_index()
NW = len(wk)


def block_boot(x, L, n_boot=5000):
    x = np.asarray(x, float)
    n = len(x)
    L = min(L, n)
    out = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.integers(0, n - L + 1, int(np.ceil(n / L)))
        out[b] = np.concatenate([x[s:s + L] for s in starts])[:n].mean()
    return np.percentile(out, [2.5, 97.5])


pairs = {"chosen minus same hour last week": wk.e_c - wk.e_l, "chosen minus mean of last 4 same weekdays": wk.e_c - wk.e_4,
         "mean of last 4 minus same hour last week": wk.e_4 - wk.e_l, "chosen minus dummy": wk.e_c - wk.e_d}
brows = []
for name, x in pairs.items():
    for L in (1, 2, 3):
        lo, hi = block_boot(x.values, L)
        brows.append({"comparison": name, "block_weeks": L, "mean_difference_mae": x.mean(), "ci_low": lo, "ci_high": hi,
                      "weeks_where_first_is_better": int((x < 0).sum()), "weeks": NW})
bt = pd.DataFrame(brows).round(4)
save_table(bt, "staffing_rolling_bootstrap.csv", index=False)
print(f"\nPAIRED DIFFERENCES IN MAE over {NW} test weeks (negative = first is better); 95% block-bootstrap interval, blocks of 1, 2 or 3 contiguous weeks\n")
print(bt.to_string(index=False))
bm = {TEST_MONTHS[m]: (T[T.month == m].assign(e=lambda z: (z.n - z.chosen).abs() - (z.n - z.same_hour_last_week).abs()).groupby("origin").e.mean() < 0).mean()
      for m in TEST_MONTHS}
print("share of weeks in which the chosen model beats last week's same hour, by month:", {k: round(v, 2) for k, v in bm.items()})
# model-based reference (not a bound on any real forecast): expected MAE if the forecast were the true mean and counts were Poisson
lam = np.clip(T.chosen.values, 1e-6, None)
kk = np.arange(0, 80)
ref = np.array([np.abs(kk - l) @ stats.poisson.pmf(kk, l) for l in lam]).mean()
print(f"model-based reference: if the chosen forecast were the true mean and counts were Poisson, the expected MAE would be {ref:.3f}; "
      f"the chosen model's MAE is {mae_of(T, 'chosen'):.3f}. This depends on the model being right, so it is a reference, not a limit.")

# ---- error by hour and branch (pooled test weeks) ----
by_hour = T.assign(chosen_=(T.n - T.chosen).abs(), last_week=(T.n - T.same_hour_last_week).abs(), last4=(T.n - T.mean_last_4_same_weekdays).abs(),
                   dummy_=(T.n - T.dummy).abs()).groupby("hour")[["n", "chosen_", "last_week", "last4", "dummy_"]].mean()
by_hour = by_hour.rename(columns={"n": "mean_transactions", "chosen_": "mae_chosen", "last_week": "mae_same_hour_last_week",
                                  "last4": "mae_mean_last_4_weeks", "dummy_": "mae_dummy"}).round(3)
by_hour_branch = T.assign(m=(T.n - T.chosen).abs(), lw=(T.n - T.same_hour_last_week).abs(), l4=(T.n - T.mean_last_4_same_weekdays).abs()
                          ).groupby(["branch", "hour"])[["n", "m", "lw", "l4"]].mean().round(3)
save_table(by_hour, "staffing_mae_by_hour.csv")
save_table(by_hour_branch.rename(columns={"n": "mean_transactions", "m": "mae_chosen", "lw": "mae_same_hour_last_week", "l4": "mae_mean_last_4_weeks"}),
           "staffing_mae_by_branch_hour.csv")
print("\nMAE PER HOUR (all branches, pooled test weeks)\n", by_hour.to_string())
print("hours in which the chosen model has lower MAE than same hour last week:", int((by_hour.mae_chosen < by_hour.mae_same_hour_last_week).sum()),
      "of", len(by_hour), "; than the 4-week mean:", int((by_hour.mae_chosen < by_hour.mae_mean_last_4_weeks).sum()), "of", len(by_hour))
shape = T.groupby(["branch", "weekday", "hour"]).chosen.mean().round(2)
save_table(shape.rename("forecast_transactions").to_frame(), "staffing_forecast_shape.csv")


# ---------------- staffing SCENARIO ----------------
def staff(arr, cap, minimum, how="mean"):
    a = np.asarray(arr, float)
    if how == "p80":
        a = stats.poisson.ppf(0.8, np.clip(a, 1e-6, None))
    return np.maximum(minimum, np.ceil(a / cap))


def block_cover(plan, k):
    """Staff scheduled in blocks of k consecutive open hours (aligned to 07:00): a block must cover its busiest hour."""
    if k == 1:
        return plan
    key = [T.branch.values, T.date.values, (T.hour.values - HOURS[0]) // k]
    return pd.Series(plan).groupby(key).transform("max").values


def plans_for(cap, minimum, k=1):
    return {"forecast (chosen model)": block_cover(staff(T.chosen.values, cap, minimum), k),
            "forecast, 80% cover (assumes Poisson counts)": block_cover(staff(T.chosen.values, cap, minimum, "p80"), k),
            "same hour last week": block_cover(staff(T.same_hour_last_week.values, cap, minimum), k),
            "mean of last 4 same weekdays": block_cover(staff(T.mean_last_4_same_weekdays.values, cap, minimum), k),
            "flat: always the minimum": np.full(len(T), float(minimum)), "flat: 2 staff every open hour": np.full(len(T), 2.0)}


def plan_table(cap, minimum, k=1, break_share=0.0):
    cap_eff = cap * (1 - break_share)
    need = staff(T.n.values, cap_eff, minimum)
    out = []
    for name, plan in plans_for(cap_eff, minimum, k).items():
        short = np.maximum(need - plan, 0)
        out.append({"cap_tx_per_staff_hour": cap, "break_share": round(break_share, 4), "min_staff": minimum, "block_hours": k, "plan": name,
                    "staff_hours_needed": need.sum(), "staff_hours_planned": plan.sum(), "short_staff_hours": short.sum(),
                    "share_of_branch_hours_understaffed": float((short > 0).mean()), "surplus_staff_hours": np.maximum(plan - need, 0).sum()})
    return pd.DataFrame(out)


main = plan_table(8, 1).round(3)
save_table(main, "staffing_staff_hours_rolling.csv", index=False)
print("\nSCENARIO (assumptions: 8 transactions per staff-hour, at least 1 staff in every open hour, no break loss, staff can change every hour);"
      f"\nforecast weeks Apr-Jun ({NW} weeks), all branches:")
print(main.drop(columns=["cap_tx_per_staff_hour", "break_share", "min_staff", "block_hours"]).to_string(index=False))

# week-block bootstrap of the difference in understaffed share (main scenario)
need1 = staff(T.n.values, 8, 1)
pl = plans_for(8, 1)
shr = pd.DataFrame({name: pd.Series((np.maximum(need1 - p, 0) > 0)).groupby(T.origin.values).mean() for name, p in pl.items()}).sort_index()
srows = []
for a_, b_ in [("forecast (chosen model)", "same hour last week"), ("forecast (chosen model)", "mean of last 4 same weekdays"),
               ("forecast (chosen model)", "flat: always the minimum")]:
    x = (shr[a_] - shr[b_]).values
    lo, hi = block_boot(x, 2)
    srows.append({"comparison": f"{a_} minus {b_}", "mean_difference_in_understaffed_share": x.mean(), "ci_low_blocks_of_2_weeks": lo, "ci_high_blocks_of_2_weeks": hi})
sdf = pd.DataFrame(srows).round(4)
save_table(sdf, "staffing_scenario_bootstrap.csv", index=False)
print("\nScenario: difference in the share of branch-hours understaffed (negative = first plan better), 95% block-bootstrap interval:\n", sdf.to_string(index=False))

# sensitivities
sens_rows = []
for cap in (6, 8, 10):
    for minimum in (1, 2):
        t_ = plan_table(cap, minimum)
        for _, r in t_.iterrows():
            sens_rows.append(r)
sens = pd.DataFrame(sens_rows)
save_table(sens.round(3), "staffing_service_rate_sensitivity.csv", index=False)
print("\nSENSITIVITY to service rate and minimum crew: share of branch-hours understaffed (hourly changes allowed)")
print(sens[sens.plan.isin(["forecast (chosen model)", "same hour last week", "mean of last 4 same weekdays", "flat: always the minimum"])].pivot_table(
    index=["cap_tx_per_staff_hour", "min_staff"], columns="plan", values="share_of_branch_hours_understaffed").round(3).to_string())
brk = pd.concat([plan_table(8, 1, 1, b) for b in (0.0, 1 / 16, 1 / 8)]).round(3)
save_table(brk, "staffing_break_sensitivity.csv", index=False)
print("\nSENSITIVITY to breaks (a share of each paid hour is lost; 1/16 = 30 minutes per 8-hour shift, 1/8 = 30 minutes per 4 hours):")
print(brk[brk.plan.isin(["forecast (chosen model)", "same hour last week", "mean of last 4 same weekdays", "flat: always the minimum"])].pivot_table(
    index=["break_share", "staff_hours_needed"], columns="plan", values="share_of_branch_hours_understaffed").round(3).to_string())
flex = pd.concat([plan_table(8, 1, k) for k in (1, 2, 4)]).round(3)
save_table(flex, "staffing_flexibility_sensitivity.csv", index=False)
print("\nSENSITIVITY to hourly flexibility (staff scheduled in blocks of k hours, each block covering its busiest hour):")
print(flex[flex.plan.isin(["forecast (chosen model)", "same hour last week", "mean of last 4 same weekdays"])][
    ["block_hours", "plan", "staff_hours_needed", "staff_hours_planned", "short_staff_hours", "share_of_branch_hours_understaffed", "surplus_staff_hours"]].to_string(index=False))

need8 = staff(T.n.values, 8, 1)
print(f"\nmain scenario: share of branch-hours needing 2 or more staff: {(need8 >= 2).mean():.1%}; 3 or more: {(need8 >= 3).mean():.2%}")
days_in = T.groupby(["branch", "weekday"]).date.nunique()
wkn = T.assign(need=need8).groupby(["branch", "weekday"]).need.sum() / days_in
wk_tab = wkn.round(1).unstack().rename(columns=dict(enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])))
save_table(wk_tab, "staffing_needed_staff_hours_per_day.csv")
print("needed staff-hours per day by weekday (scenario, Apr-Jun actual demand):\n", wk_tab.to_string())
hh = T.assign(need=need8).groupby("hour")[["need"]].sum()
print(f"share of all needed staff-hours that fall from 18:00: {hh.loc[18:, 'need'].sum() / hh.need.sum():.1%} (share of the open hours from 18:00: {6 / 17:.1%})")
hb = T.assign(need=need8).groupby(["branch", "hour"]).need.mean().unstack(0).round(2)
save_table(hb, "staffing_needed_staff_by_hour.csv")
print("mean staff needed per hour (scenario):\n", hb.T.to_string())

# ---------------- figures ----------------
fig, ax = plt.subplots(figsize=(9, 4.5))
x = np.arange(len(by_hour))
ax.bar(x - 0.27, by_hour.mae_chosen, width=0.27, label="chosen model", color="#c0392b")
ax.bar(x, by_hour.mae_mean_last_4_weeks, width=0.27, label="mean of last 4 same weekdays", color="#e59866")
ax.bar(x + 0.27, by_hour.mae_same_hour_last_week, width=0.27, label="same hour last week", color="#7f8c8d")
ax.plot(x, by_hour.mean_transactions, "k.-", label="mean transactions per branch-hour")
ax.set_xticks(x, by_hour.index)
ax.set_title("Rolling 1-7 day-ahead forecasts, April-June: error per hour, mean over the three branches")
ax.set_xlabel("Hour of day")
ax.set_ylabel("Transactions (MAE, or mean count)")
ax.legend(fontsize=8)
save_fig(fig, "staffing_mae_by_hour.png")
fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=True)
for ax, b in zip(axes, BRANCHES):
    M = shape.loc[b].unstack(0)       # hour x weekday
    im = ax.imshow(M.values, aspect="auto", cmap="YlOrRd", origin="lower", extent=[-0.5, 6.5, HOURS[0] - 0.5, HOURS[-1] + 0.5])
    ax.set_xticks(range(7), ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    ax.set_title(f"{b}: forecast transactions per hour, Apr-Jun")
    ax.set_xlabel("Weekday")
    fig.colorbar(im, ax=ax)
axes[0].set_ylabel("Hour of day")
save_fig(fig, "staffing_forecast_heatmap.png")
fig, ax = plt.subplots(figsize=(9, 4))
for col, c in [("e_c", "#c0392b"), ("e_4", "#e59866"), ("e_l", "#7f8c8d")]:
    ax.plot(wk.index, wk[col], marker="o", color=c, label={"e_c": "chosen model", "e_4": "mean of last 4 same weekdays", "e_l": "same hour last week"}[col])
ax.set_title("Weekly MAE over the 12 test weeks (all branches and hours)")
ax.set_xlabel("Forecast week starting")
ax.set_ylabel("MAE (transactions per branch-hour)")
ax.legend(fontsize=8)
save_fig(fig, "staffing_weekly_mae.png")
print("\nsaved figures/staffing_mae_by_hour.png, staffing_forecast_heatmap.png, staffing_weekly_mae.png")
