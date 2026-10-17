"""June forecast of daily transactions per branch (staffing use, Tuesday surge).

Target: transactions per branch per day.
Test:   June 2026, touched once at the end.
Model choice: candidates are compared on May (validation) after training on Jan-Apr. The chosen model is
then refit on Jan-May and scored on June.

Models
  dummy           : mean of the training period per branch (CLAUDE.md dummy baseline)
  seasonal_naive  : same weekday last week (the brief's baseline). This uses actual counts from 7 days
                    earlier, so it is a 1-week-ahead forecast.
  weekday_trend   : per branch, least squares on weekday dummies + linear time trend. Uses no data from the
                    forecast month at all, so it is a 1-to-5-weeks-ahead forecast (a harder setting).
  weekday_logtrend: same, but on log(transactions), so growth is a percentage per day and weekday effects
                    are multiplicative.
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
    _r[~_r.split.isin(["val_may", "test_june"])].to_csv(RESULTS_CSV, index=False)

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
