"""Forecast of daily transactions per branch (staffing use, Tuesday surge).

Target: transactions per branch per day.

MAIN EVALUATION: rolling origin, fixed 7-day horizon.
  For each origin date t from 1 Mar to 23 Jun, every candidate is fit on data up to and including t and predicts
  t + 7. All features are computed relative to the origin (never the target date). The candidate list below is
  fixed before evaluation and every candidate is reported. The one model that "selects" (selected_trailing) picks,
  at each origin, the candidate with the lowest MAE over the last 28 target dates already observed at t
  (targets <= t), so selection uses only data before the origin. Interval for the MAE difference vs the seasonal
  naive baseline: paired block bootstrap over contiguous weeks of target dates, all branches kept together, with
  block lengths of 1, 2 and 3 weeks.

Candidates (frozen)
  dummy           : mean of all data up to t, per branch
  seasonal_naive  : the count at t (same weekday, one week before the target): the brief's baseline
  weekday_trend   : per branch, least squares on weekday dummies + linear time trend, fit on data up to t
  weekday_logtrend: same on log(transactions)
  hgb_lags        : HistGradientBoostingRegressor, pooled over branches, fixed settings (no tuning). Target
                    log(y[t+7] / mean28[t]); features, all known at t: target weekday, branch, y[t]/mean28,
                    y[t-7]/mean28, mean7/mean28 (mean7, mean28 = means of the 7 and 28 days ending at t).
                    Trained on pairs (s, s+7) with s + 7 <= t.
  selected_trailing: see above.

SECONDARY CHECK (kept from the first version): train Jan-Apr, compare on May, refit Jan-May, score June once.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import os

from common import RESULTS_CSV, log_result, save_fig
from load import load_clean, save_table

d = load_clean()
tx = d.groupby(["date", "Branch"])["Transaction ID"].nunique().unstack(fill_value=0)
tx = tx.asfreq("D", fill_value=0)
BRANCHES = list(tx.columns)
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def design(idx, t0):
    X = pd.get_dummies(idx.dayofweek, dtype=float).reindex(columns=range(7), fill_value=0.0).values
    t = ((idx - t0).days.values / 30.0)[:, None]
    return np.hstack([X, t])


def fit_predict(kind, train, test_idx):
    """Return predictions (DataFrame, index=test_idx, columns=branches)."""
    out = pd.DataFrame(index=test_idx, columns=BRANCHES, dtype=float)
    for b in BRANCHES:
        y = train[b]
        if kind == "dummy":
            out[b] = y.mean()
        elif kind == "seasonal_naive":
            full = tx[b]
            out[b] = full.shift(7).loc[test_idx].values
        else:
            t0 = train.index[0]
            Xtr, Xte = design(train.index, t0), design(test_idx, t0)
            target = np.log(y.values) if kind == "weekday_logtrend" else y.values
            beta = np.linalg.lstsq(Xtr, target, rcond=None)[0]
            p = Xte @ beta
            out[b] = np.exp(p) if kind == "weekday_logtrend" else p
    return out


def score(actual, pred):
    err = (pred - actual).abs()
    row = {f"mae_{b}": err[b].mean() for b in BRANCHES}
    row["mae_all"] = err.values.mean()
    tue = actual.index.dayofweek == 1
    row["mae_tuesdays"] = err[tue].values.mean()
    row["mae_other_days"] = err[~tue].values.mean()
    row["mape_all_pct"] = 100 * (err / actual).values.mean()
    return {k: round(float(v), 2) for k, v in row.items()}


KINDS = ["dummy", "seasonal_naive", "weekday_trend", "weekday_logtrend"]

# rerunning replaces this script's own rows in results.csv instead of appending duplicates
if os.path.exists(RESULTS_CSV):
    _r = pd.read_csv(RESULTS_CSV)
    _r[~_r.split.isin(["val_may", "test_june", "rolling_h7"])].to_csv(RESULTS_CSV, index=False)

# ---------- validation: train Jan-Apr, score May ----------
tr, va = tx.loc[:"2026-04-30"], tx.loc["2026-05-01":"2026-05-31"]
val_rows = []
for k in KINDS:
    s = score(va, fit_predict(k, tr, va.index))
    log_result(k, "val_may", s, "daily transactions per branch; train Jan-Apr" + ("; seasonal_naive = same weekday last week (uses last week's actuals)" if k == "seasonal_naive" else ""))
    val_rows.append({"model": k, **s})
val = pd.DataFrame(val_rows)
print("VALIDATION (May):\n", val.to_string(index=False))
model_kinds = ["weekday_trend", "weekday_logtrend"]
best = val[val.model.isin(model_kinds)].sort_values("mae_all").iloc[0].model
print(f"chosen on May: {best}")

# ---------- test: refit on Jan-May, score June once ----------
trf, te = tx.loc[:"2026-05-31"], tx.loc["2026-06-01":"2026-06-30"]
preds, test_rows = {}, []
for k in ["dummy", "seasonal_naive", best]:
    p = fit_predict(k, trf, te.index)
    preds[k] = p
    s = score(te, p)
    log_result(k, "test_june", s, "daily transactions per branch; train Jan-May; model chosen on May" + ("; seasonal_naive = same weekday last week (uses last week's actuals)" if k == "seasonal_naive" else ""))
    test_rows.append({"model": k, **s})
test = pd.DataFrame(test_rows)
print("\nTEST (June):\n", test.to_string(index=False))
save_table(pd.concat([val.assign(split="val_may"), test.assign(split="test_june")]), "forecast_mae.csv", index=False)

# ---------- business view: Tuesday staffing ----------
tue = te.index.dayofweek == 1
biz = pd.DataFrame({
    "branch": BRANCHES,
    "june_tuesday_actual_mean": te[tue].mean().values,
    "june_other_weekday_actual_mean": te[(~tue) & (te.index.dayofweek < 5)].mean().values,
    "model_tuesday_forecast_mean": preds[best][tue].mean().values,
    "model_tuesday_mae": (preds[best][tue] - te[tue]).abs().mean().values,
    "naive_tuesday_mae": (preds["seasonal_naive"][tue] - te[tue]).abs().mean().values,
    # descriptive reference, not a forecast: error if Tuesdays were staffed like June's average Mon/Wed-Fri
    "flat_weekday_tuesday_mae": (te[tue] - te[(~tue) & (te.index.dayofweek < 5)].mean()).abs().mean().values,
}).round(1)
print("\nTuesday view (June):\n", biz.to_string(index=False))
save_table(biz, "forecast_tuesday.csv", index=False)

# ---------- figure ----------
fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
for ax, b in zip(axes, BRANCHES):
    ax.plot(te.index, te[b], "k-o", ms=3, label="actual")
    ax.plot(te.index, preds["seasonal_naive"][b], color="#7f8c8d", ls="--", label="same weekday last week")
    ax.plot(te.index, preds[best][b], color="#c0392b", label=best.replace("_", " "))
    ax.set_title(f"{b}: daily transactions, June 2026 (test)")
    ax.set_ylabel("Transactions")
axes[0].legend(ncol=3, fontsize=8)
axes[-1].set_xlabel("Date")
fig.tight_layout()
save_fig(fig, "forecast_june.png")
print("saved figures/forecast_june.png")


# ======================= MAIN: rolling origin, 7-day horizon =======================
from sklearn.ensemble import HistGradientBoostingRegressor

from common import SEED

H = 7
CANDS = ["dummy", "seasonal_naive", "weekday_trend", "weekday_logtrend", "hgb_lags"]
REPORT_FROM, REPORT_TO = pd.Timestamp("2026-03-01"), pd.Timestamp("2026-06-23")
WARMUP_FROM = pd.Timestamp("2026-02-15")       # extra origins only so selected_trailing has a history on 1 Mar
origins = pd.date_range(WARMUP_FROM, REPORT_TO, freq="D")
m7, m28 = tx.rolling(7).mean(), tx.rolling(28).mean()


def lag_rows(s_idx):
    """Origin-relative features for origins s_idx (all branches stacked)."""
    rows = []
    for bi, b in enumerate(BRANCHES):
        base = m28[b].loc[s_idx].values
        rows.append(pd.DataFrame({
            "origin": s_idx, "branch": b, "branch_code": bi,
            "target_dow": (s_idx + pd.Timedelta(days=H)).dayofweek,
            "lag0_rel": tx[b].loc[s_idx].values / base,
            "lag7_rel": tx[b].shift(7).loc[s_idx].values / base,
            "mean7_rel": m7[b].loc[s_idx].values / base,
            "base": base}))
    return pd.concat(rows, ignore_index=True)


FEATS = ["branch_code", "target_dow", "lag0_rel", "lag7_rel", "mean7_rel"]
all_feat = lag_rows(tx.index[27:])                        # need 28 days of history for mean28
all_feat["target"] = [tx[b].get(o + pd.Timedelta(days=H), np.nan) for o, b in zip(all_feat.origin, all_feat.branch)]

pred_rows = []
for t in origins:
    tgt = t + pd.Timedelta(days=H)
    hist = tx.loc[:t]
    for b in BRANCHES:
        y = hist[b]
        actual = tx[b].loc[tgt]
        row = {"origin": t, "target_date": tgt, "branch": b, "actual": actual}
        row["dummy"] = y.mean()
        row["seasonal_naive"] = y.loc[t]                    # same weekday, one week before the target
        t0 = hist.index[0]
        Xtr, Xte = design(hist.index, t0), design(pd.DatetimeIndex([tgt]), t0)
        row["weekday_trend"] = float((Xte @ np.linalg.lstsq(Xtr, y.values, rcond=None)[0])[0])
        row["weekday_logtrend"] = float(np.exp(Xte @ np.linalg.lstsq(Xtr, np.log(y.values), rcond=None)[0])[0])
        pred_rows.append(row)
    # pooled gradient boosting: train only on pairs whose target is already observed at t
    trn = all_feat[(all_feat.origin + pd.Timedelta(days=H) <= t)].dropna(subset=["target"])
    cur = all_feat[all_feat.origin == t]
    hgb = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_depth=3, min_samples_leaf=20,
                                        categorical_features=[0, 1], random_state=SEED)
    hgb.fit(trn[FEATS], np.log(trn.target / trn.base))
    p = np.exp(hgb.predict(cur[FEATS])) * cur.base.values
    for b, v in zip(cur.branch, p):
        pred_rows[-len(BRANCHES) + BRANCHES.index(b)]["hgb_lags"] = float(v)

roll = pd.DataFrame(pred_rows)
for k in CANDS:
    roll[f"ae_{k}"] = (roll[k] - roll.actual).abs()

# selected_trailing: at origin t, pick the candidate with the lowest MAE over the last 28 target dates <= t
sel_pred = []
for t in roll.origin.unique():
    past = roll[(roll.target_date <= t) & (roll.target_date > t - pd.Timedelta(days=28))]
    pick = "seasonal_naive" if past.target_date.nunique() < 7 else min(CANDS, key=lambda k: past[f"ae_{k}"].mean())
    cur = roll.origin == t
    sel_pred.append((t, pick))
    roll.loc[cur, "selected_trailing"] = roll.loc[cur, pick]
    roll.loc[cur, "selected_pick"] = pick
roll["ae_selected_trailing"] = (roll.selected_trailing - roll.actual).abs()
ALL = CANDS + ["selected_trailing"]
rep = roll[(roll.origin >= REPORT_FROM) & (roll.origin <= REPORT_TO)].copy()
rep["month"] = rep.target_date.dt.month
rep["is_tue"] = rep.target_date.dt.dayofweek == 1
print(f"\nROLLING ORIGIN (h = {H} days): origins {REPORT_FROM.date()} to {REPORT_TO.date()}, "
      f"targets {rep.target_date.min().date()} to {rep.target_date.max().date()}, {rep.origin.nunique()} origins x {len(BRANCHES)} branches")

mae_rows = []
for k in ALL:
    r = {"model": k, "mae_all": rep[f"ae_{k}"].mean(), "mae_tuesdays": rep.loc[rep.is_tue, f"ae_{k}"].mean(),
         "mae_other_days": rep.loc[~rep.is_tue, f"ae_{k}"].mean()}
    for m in sorted(rep.month.unique()):
        r[f"mae_month_{m}"] = rep.loc[rep.month == m, f"ae_{k}"].mean()
    for b in BRANCHES:
        r[f"mae_{b}"] = rep.loc[rep.branch == b, f"ae_{k}"].mean()
    mae_rows.append(r)
rmae = pd.DataFrame(mae_rows).round(2)
print(rmae.to_string(index=False))
print("selected_trailing picks (share of reported origins):",
      rep.drop_duplicates("origin").selected_pick.value_counts(normalize=True).round(3).to_dict())
save_table(rmae, "forecast_rolling_mae.csv", index=False)
for r in rmae.itertuples():
    log_result(r.model, "rolling_h7", {f"mae_{b}": getattr(r, f"mae_{b}") for b in BRANCHES} |
               {"mae_all": r.mae_all, "mae_tuesdays": r.mae_tuesdays, "mae_other_days": r.mae_other_days},
               "rolling origin 1 Mar-23 Jun, horizon 7 days, fit on data up to the origin")

# paired block bootstrap of daily error differences vs seasonal naive (all branches kept together)
rng = np.random.default_rng(SEED)
N_BOOT = 2000
day0 = rep.target_date.min()
boot_rows = []
for weeks in [1, 2, 3]:
    blk = ((rep.target_date - day0).dt.days // (7 * weeks)).values
    ublk = np.unique(blk)
    draws = rng.integers(0, len(ublk), size=(N_BOOT, len(ublk)))
    for k in ALL:
        if k == "seasonal_naive":
            continue
        diff = (rep[f"ae_{k}"] - rep["ae_seasonal_naive"]).values       # negative = better than the baseline
        bs = np.array([diff[blk == u].sum() for u in ublk]); bn = np.array([(blk == u).sum() for u in ublk])
        means = bs[draws].sum(1) / bn[draws].sum(1)
        boot_rows.append({"model": k, "block_weeks": weeks, "n_blocks": len(ublk), "mae_diff_vs_naive": diff.mean(),
                          "ci_low": np.percentile(means, 2.5), "ci_high": np.percentile(means, 97.5)})
boot = pd.DataFrame(boot_rows).round(3)
print("\nMAE difference vs seasonal naive (negative = better), paired block bootstrap over weeks:\n", boot.to_string(index=False))
save_table(boot, "forecast_rolling_bootstrap.csv", index=False)

fig, ax = plt.subplots(figsize=(8, 4))
months = [c for c in rmae.columns if c.startswith("mae_month_")]
for r in rmae.itertuples():
    ax.plot([int(c.split("_")[-1]) for c in months], [getattr(r, c) for c in months], "o-", label=r.model.replace("_", " "))
ax.set_xticks([3, 4, 5, 6], ["Mar", "Apr", "May", "Jun"])
ax.set_title("Rolling-origin forecast, 7 days ahead: MAE by target month")
ax.set_xlabel("Target month"); ax.set_ylabel("MAE (transactions per branch per day)")
ax.legend(fontsize=7, ncol=2)
fig.tight_layout()
save_fig(fig, "forecast_rolling.png")
print("saved figures/forecast_rolling.png")
