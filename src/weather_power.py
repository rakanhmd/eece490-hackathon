"""Power simulation: would effects the size of the French bakery's be detectable in Stories' data?

Run after reference_compare.py (it reads the bakery's estimates from results/reference_effect_transfer.csv).

Model (same as external_factors.py, 1c): log(transactions per branch-day) ~ branch x weekday + month fixed effects
+ daily max temperature + rain day + public holiday. Stories' series is kept: we fit this model, keep its fitted
values with the temperature and holiday terms removed, and add Stories' own residuals resampled in blocks of
contiguous weeks (all branches together, so the cross-branch correlation on a date is kept). We then inject the
bakery's effect (temperature per degC, or holiday) on the real dates, refit, and count how often the injected term
is significant at 5% with standard errors clustered by date. 500 simulations per scenario.
ASSUMPTIONS: Beirut weather and the hand-compiled Lebanese holiday calendar (data/README.md); the bakery's effect
sizes transfer as a percentage change. This is a statement about detectability, not about Beirut's real effects.
"""
import os

import numpy as np
import pandas as pd
from scipy import stats

from common import ROOT, SEED
from load import load_clean, save_table

rng = np.random.default_rng(SEED)
N_SIM = 500
EXT, RES = os.path.join(ROOT, "data", "external"), os.path.join(ROOT, "results")

d = load_clean()
BR = ["Garden", "Harbour", "Uptown"]
txb = d.groupby(["date", "Branch"])["Transaction ID"].nunique().unstack().reindex(columns=BR)
days = txb.index
weather = pd.read_csv(os.path.join(EXT, "weather_beirut_2026H1.csv"), skiprows=3)
weather.columns = ["date", "tmax", "precip"]
weather["date"] = pd.to_datetime(weather["date"])
weather = weather.set_index("date").reindex(days)
weather["rain_day"] = (weather.precip >= 1.0).astype(float)
cal = pd.read_csv(os.path.join(EXT, "lebanon_calendar_2026H1.csv"), parse_dates=["start", "end"])
hol = pd.Series(False, index=days)
for _, r in cal[cal.type == "public_holiday"].iterrows():
    hol |= (days >= r.start) & (days <= r.end)
weather["holiday"] = hol.astype(float).values

P = txb.stack().rename("tx").reset_index().rename(columns={"level_1": "Branch"})
P = P.merge(weather, left_on="date", right_index=True)
P["y"] = np.log(P.tx)
X = pd.concat([pd.get_dummies(P.Branch + "_" + P.date.dt.dayofweek.astype(str), dtype=float),
               pd.get_dummies(P.date.dt.month, prefix="m", drop_first=True, dtype=float),
               P[["tmax", "rain_day", "holiday"]]], axis=1)
Xv, yv, cols = X.values, P.y.values, list(X.columns)
it, ih = cols.index("tmax"), cols.index("holiday")


def fit_cluster(y):
    beta, *_ = np.linalg.lstsq(Xv, y, rcond=None)
    u = y - Xv @ beta
    bread = np.linalg.pinv(Xv.T @ Xv)
    n, k = Xv.shape[0], np.linalg.matrix_rank(Xv)
    ug = pd.DataFrame(Xv * u[:, None]).groupby(P.date.values).sum().values
    G = ug.shape[0]
    V = (G / (G - 1)) * ((n - 1) / (n - k)) * bread @ (ug.T @ ug) @ bread
    return beta, np.sqrt(np.diag(V)), u


beta, se, u = fit_cluster(yv)
base = Xv @ beta - Xv[:, it] * beta[it] - Xv[:, ih] * beta[ih]      # Stories' fit without temperature and holiday terms
print(f"Stories, observed: tmax {100*(np.exp(beta[it])-1):+.2f}%/degC (cluster p {2*stats.norm.sf(abs(beta[it]/se[it])):.2f}), "
      f"holiday {100*(np.exp(beta[ih])-1):+.1f}% (cluster p {2*stats.norm.sf(abs(beta[ih]/se[ih])):.2f}), holiday days {int(hol.sum())}")

# residuals resampled in blocks of contiguous weeks of dates (all branches of a date move together)
day_idx = (P.date - days.min()).dt.days.values
n_days = len(days)
rows_by_day = [np.where(day_idx == k)[0] for k in range(n_days)]
U = np.vstack([u[r] for r in rows_by_day])             # days x branches (same branch order for every day)
assert U.shape == (n_days, len(BR))


def resampled_resid():
    starts = rng.integers(0, n_days - 7 + 1, size=int(np.ceil(n_days / 7)))
    Ub = np.vstack([U[s:s + 7] for s in starts])[:n_days]
    out = np.empty_like(u)
    for k, r in enumerate(rows_by_day):
        out[r] = Ub[k]
    return out


tr = pd.read_csv(os.path.join(RES, "reference_effect_transfer.csv"))
fe = tr[tr.spec == "same + month fixed effects"].set_index("effect")
tr0 = tr[tr.spec == "weekday + trend + weather + holiday"].set_index("effect")
scen = [("temperature, bakery within-month effect", "tmax", fe.loc["per 1 degC of daily max temperature", "bakery_pct"]),
        ("public holiday, bakery effect (month fixed effects)", "holiday", fe.loc["public holiday", "bakery_pct"]),
        ("public holiday, bakery effect (trend model)", "holiday", tr0.loc["public holiday", "bakery_pct"]),
        ("no effect injected (false-positive check), temperature", "tmax", 0.0),
        ("no effect injected (false-positive check), holiday", "holiday", 0.0)]
rows = []
for name, term, eff_pct in scen:
    j = it if term == "tmax" else ih
    inj = np.log(1 + eff_pct / 100) * Xv[:, j]
    hits, ests = 0, []
    for _ in range(N_SIM):
        b, s, _ = fit_cluster(base + resampled_resid() + inj)
        hits += abs(b[j] / s[j]) > 1.96
        ests.append(100 * (np.exp(b[j]) - 1))
    rows.append({"scenario": name, "term": term, "injected_effect_pct": eff_pct, "simulations": N_SIM,
                 "detection_rate_cluster_5pct": hits / N_SIM, "mean_estimate_pct": float(np.mean(ests))})
power = pd.DataFrame(rows)
print("\nPower (share of simulations where the injected term is significant at 5%, date-clustered SEs):")
print(power.round(3).to_string(index=False))
save_table(power.round(4), "external_weather_power.csv", index=False)
