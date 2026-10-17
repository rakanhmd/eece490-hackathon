"""Hourly demand forecast per branch x weekday x hour, and what it implies for staff-hours.

Target:  transactions per branch per calendar hour (07:00-23:59), zero-filled.
Split:   train Jan-Apr, choose among models on May (validation), refit the chosen model on Jan-May and score June ONCE.
Baseline (the brief's): same branch, same hour, same weekday last week = the count 7 days earlier. It uses the actual
         previous week, so it is a 1-week-ahead forecast; the fitted models use nothing from the forecast month (1 to 5 weeks ahead).
         A second reference, the mean of the same hour over the last four same weekdays, is shown for context.
Staffing conversion (a SCENARIO under assumptions, not measured): one staff member serves CAP transactions per hour,
         at least MIN_STAFF people are on duty in every open hour, and breaks are covered inside the hour or by an
         overlapping shift (break share 0). None of these is in the data; sensitivity to all three is shown.
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
if os.path.exists(RESULTS_CSV):
    _r = pd.read_csv(RESULTS_CSV)
    _r[~_r.split.isin(["val_may_hourly", "test_june_hourly"])].to_csv(RESULTS_CSV, index=False)

# ---------------- validation: train Jan-Apr, score May ----------------
tr, va = split(grid.date.min(), TRAIN_END), split(*VAL)
vrows = []
for k in KINDS:
    s = score_row(va, fit_predict(k, tr, va))
    vrows.append({"model": k, **s})
    log_result("hourly_" + k, "val_may_hourly", {x: s[x] for x in ["mae_all", "mae_Garden", "mae_Harbour", "mae_Uptown", "wape_pct"]},
               "transactions per branch-hour; train Jan-Apr")
val = pd.DataFrame(vrows)
save_table(val, "staffing_validation_may.csv", index=False)
print("\nVALIDATION (May; mean absolute error in transactions per branch-hour)\n", val.to_string(index=False))
best = val[val.model.isin(FITTED)].sort_values("mae_all").iloc[0].model
print(f"model chosen on May: {best}")

# ---------------- test: refit on Jan-May, score June once ----------------
trf, te = split(grid.date.min(), VAL[1]), split(*TEST)
P = {k: fit_predict(k, trf, te) for k in ["dummy", "same_hour_last_week", "mean_last_4_same_weekdays", best]}
trows = []
for k, p in P.items():
    s = score_row(te, p)
    trows.append({"model": k, **s})
    log_result("hourly_" + k, "test_june_hourly", {x: s[x] for x in ["mae_all", "mae_Garden", "mae_Harbour", "mae_Uptown", "wape_pct"]},
               "transactions per branch-hour; train Jan-May; model chosen on May; test scored once")
test = pd.DataFrame(trows)
save_table(test, "staffing_test_june.csv", index=False)
print("\nTEST (June, scored once)\n", test.to_string(index=False))
te = te.assign(pred=P[best], base=P["same_hour_last_week"], base4=P["mean_last_4_same_weekdays"], dummy=P["dummy"])

# paired bootstrap over days: is the model's MAE different from the baseline's?
day_err = te.assign(e_m=(te.n - te.pred).abs(), e_b=(te.n - te.base).abs()).groupby("date")[["e_m", "e_b"]].mean()
diff = (day_err.e_m - day_err.e_b).values
bs = [rng.choice(diff, len(diff)).mean() for _ in range(5000)]
print(f"\nMAE(model) - MAE(same hour last week) = {diff.mean():+.4f} transactions per branch-hour, 95% bootstrap CI over days "
      f"[{np.percentile(bs, 2.5):+.4f}, {np.percentile(bs, 97.5):+.4f}] (negative = model better)")
# the part of the error nobody can remove: if counts were Poisson around the forecast
lam = np.clip(te.pred.values, 1e-6, None)
k_ = np.arange(0, 80)
floor = np.array([np.abs(k_ - l) @ stats.poisson.pmf(k_, l) for l in lam]).mean()
print(f"noise floor: if June counts were Poisson with mean equal to the model's forecast, the MAE could not go below {floor:.3f}; "
      f"the model's MAE is {mae(te, te.pred.values)[0]:.3f}")

# MAE per hour
by_hour = te.assign(model=(te.n - te.pred).abs(), last_week=(te.n - te.base).abs(), last4=(te.n - te.base4).abs(),
                    dummy_=(te.n - te.dummy).abs()).groupby("hour")[["n", "model", "last_week", "last4", "dummy_"]].mean()
by_hour = by_hour.rename(columns={"n": "mean_transactions", "model": f"mae_{best}", "last_week": "mae_same_hour_last_week",
                                  "last4": "mae_mean_last_4_weeks", "dummy_": "mae_dummy"}).round(3)
by_hour_branch = te.assign(model=(te.n - te.pred).abs(), last_week=(te.n - te.base).abs()).groupby(["branch", "hour"])[["n", "model", "last_week"]].mean().round(3)
save_table(by_hour, "staffing_mae_by_hour.csv")
save_table(by_hour_branch.rename(columns={"n": "mean_transactions", "model": "mae_model", "last_week": "mae_same_hour_last_week"}), "staffing_mae_by_branch_hour.csv")
print("\nJUNE MAE PER HOUR (all branches; mean transactions per branch-hour)\n", by_hour.to_string())
print("hours where the model beats last week's same hour:", int((by_hour.iloc[:, 1] < by_hour.mae_same_hour_last_week).sum()), "of", len(by_hour))
# forecast of the weekday x hour shape, for the figure and as a plain-language schedule input
shape = te.groupby(["branch", "weekday", "hour"]).pred.mean().round(2)
save_table(shape.rename("forecast_transactions").to_frame(), "staffing_forecast_shape_june.csv")

# ---------------- staff-hours (ASSUMPTIONS) ----------------
def staff(arr, cap, minimum, how="mean"):
    a = np.asarray(arr, float)
    if how == "p80":
        a = stats.poisson.ppf(0.8, np.clip(a, 1e-6, None))
    return np.maximum(minimum, np.ceil(a / cap))


rows = []
for cap in (6, 8, 10):
    for minimum in (1, 2):
        need = staff(te.n.values, cap, minimum)
        plans = {"forecast (model)": staff(te.pred.values, cap, minimum), "forecast, 80% cover": staff(te.pred.values, cap, minimum, "p80"),
                 "same hour last week": staff(np.nan_to_num(te.base.values, nan=te.n.mean()), cap, minimum),
                 "flat: always the minimum": np.full(len(te), float(minimum)), "flat: 2 staff every open hour": np.full(len(te), 2.0)}
        for name, plan in plans.items():
            short = np.maximum(need - plan, 0)
            rows.append({"cap_tx_per_staff_hour": cap, "min_staff": minimum, "plan": name, "staff_hours_needed": need.sum(),
                         "staff_hours_planned": plan.sum(), "short_staff_hours": short.sum(),
                         "share_of_branch_hours_understaffed": float((short > 0).mean()),
                         "surplus_staff_hours": np.maximum(plan - need, 0).sum()})
st = pd.DataFrame(rows).round(3)
save_table(st, "staffing_staff_hours_june.csv", index=False)
main = st[(st.cap_tx_per_staff_hour == 8) & (st.min_staff == 1)]
print("\nESTIMATE (main assumptions: 8 transactions per staff-hour, at least 1 staff in every open hour), June, all branches:")
print(main.to_string(index=False))
print("\nESTIMATE sensitivity: understaffed share of branch-hours, plan = forecast (model) vs same hour last week")
sens = st[st.plan.isin(["forecast (model)", "same hour last week", "forecast, 80% cover"])].pivot_table(
    index=["cap_tx_per_staff_hour", "min_staff"], columns="plan", values="share_of_branch_hours_understaffed")
print(sens.round(3).to_string())
# Breaks (ASSUMPTION): the main case assumes breaks are covered inside the hour or by an overlapping shift (break share 0).
# Sensitivity: a share of each paid staff-hour is lost to breaks, so effective capacity = 8 x (1 - break share).
# 1/16 = a 30-minute break per 8-hour shift; 1/8 = 30 minutes per 4 hours.
brk = []
for b_share in (0.0, 1 / 16, 1 / 8):
    cap_eff = 8 * (1 - b_share)
    need_b = staff(te.n.values, cap_eff, 1)
    for name, plan in {"forecast (model)": staff(te.pred.values, cap_eff, 1),
                       "same hour last week": staff(np.nan_to_num(te.base.values, nan=te.n.mean()), cap_eff, 1),
                       "flat: always the minimum": np.full(len(te), 1.0)}.items():
        short = np.maximum(need_b - plan, 0)
        brk.append({"break_share": b_share, "effective_tx_per_paid_staff_hour": cap_eff, "min_staff": 1, "plan": name,
                    "staff_hours_needed": need_b.sum(), "staff_hours_planned": plan.sum(),
                    "share_of_branch_hours_understaffed": float((short > 0).mean())})
brk = pd.DataFrame(brk).round(3)
save_table(brk, "staffing_break_sensitivity.csv", index=False)
print("\nESTIMATE sensitivity to breaks (8 transactions per staff-hour before breaks, at least 1 staff):\n", brk.to_string(index=False))
need8 = staff(te.n.values, 8, 1)
print(f"main case: share of June branch-hours that need 2 or more staff: {(need8 >= 2).mean():.1%}; 3 or more: {(need8 >= 3).mean():.2%}")
byb = te.assign(need=need8, plan=staff(te.pred.values, 8, 1)).groupby("branch")[["need", "plan"]].sum()
print("staff-hours needed vs planned by branch (June):\n", byb.to_string())
days_in = te.groupby(["branch", "weekday"]).date.nunique()
wk = te.assign(need=need8).groupby(["branch", "weekday"]).need.sum() / days_in
wk_tab = wk.round(1).unstack().rename(columns=dict(enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])))
save_table(wk_tab, "staffing_needed_staff_hours_per_day.csv")
print("needed staff-hours per day by weekday (main case, June actual demand):\n", wk_tab.to_string())
hh = te.assign(need=need8, plan=staff(te.pred.values, 8, 1)).groupby("hour")[["need"]].sum()
eve = hh.loc[18:, "need"].sum() / hh.need.sum()
print(f"share of all needed staff-hours that fall from 18:00: {eve:.1%} (share of the open hours from 18:00: {6 / 17:.1%})")
hb = te.assign(need=need8).groupby(["branch", "hour"]).need.mean().unstack(0).round(2)
save_table(hb, "staffing_needed_staff_by_hour.csv")
print("mean staff needed per hour (main case):\n", hb.T.to_string())

# ---------------- figures ----------------
fig, ax = plt.subplots(figsize=(8.5, 4.5))
x = np.arange(len(by_hour))
ax.bar(x - 0.2, by_hour[f"mae_{best}"], width=0.4, label=f"model: {best}", color="#c0392b")
ax.bar(x + 0.2, by_hour.mae_same_hour_last_week, width=0.4, label="same hour last week", color="#7f8c8d")
ax.plot(x, by_hour.mean_transactions, "k.-", label="mean transactions per branch-hour")
ax.set_xticks(x, by_hour.index)
ax.set_title("June test: error per hour, mean over the three branches")
ax.set_xlabel("Hour of day")
ax.set_ylabel("Transactions (MAE, or mean count)")
ax.legend(fontsize=8)
save_fig(fig, "staffing_mae_by_hour.png")
fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=True)
for ax, b in zip(axes, BRANCHES):
    M = shape.loc[b].unstack(0)       # hour x weekday
    im = ax.imshow(M.values, aspect="auto", cmap="YlOrRd", origin="lower", extent=[-0.5, 6.5, HOURS[0] - 0.5, HOURS[-1] + 0.5])
    ax.set_xticks(range(7), ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    ax.set_title(f"{b}: forecast transactions per hour, June")
    ax.set_xlabel("Weekday")
    fig.colorbar(im, ax=ax)
axes[0].set_ylabel("Hour of day")
save_fig(fig, "staffing_forecast_heatmap.png")
print("\nsaved figures/staffing_mae_by_hour.png, staffing_forecast_heatmap.png")
