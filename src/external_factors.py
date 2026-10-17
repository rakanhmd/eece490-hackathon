"""Outside factors: can public data explain (a) the Tuesday surge and (b) Garden's 43% higher unit costs?

ASSUMPTION used throughout: Stories is a Lebanese chain, so all three branches are treated as being in
Greater Beirut (lat 33.89, lon 35.50). Branch addresses are not in the data, so weather and calendar are the
same for every branch, and nothing here can separate one branch's location from another's.

External data (saved in data/external/, sources and download date in data/README.md):
  weather_beirut_2026H1.csv      Open-Meteo archive, daily max temperature and precipitation
  lebanon_calendar_2026H1.csv    public holidays, Ramadan, school closures, AUB calendar, security escalation
  coffee_price_arabica_fred.csv  IMF arabica price (FRED series PCOFFOTMUSDM), monthly

Tests
  1. Weather: log(tx/day) ~ branch x weekday + branch x trend (as in forecast.py), then + temperature + rain day.
     Coefficients with 95% CI, R2 change, permutation p-value (weather shuffled across days within month).
     Cold-drink share vs temperature beyond the month effect. Does weather explain the Jan->Jun growth?
  2. Calendar: holidays vs the same weekday +-1..3 weeks; Ramadan evening share; security escalation vs the
     Jan-Feb trend; KEY school/campus test: is the Tuesday ratio lower when schools or AUB are out?
     Thursday check (university Tue/Thu timetables).
  3. Tuesday ratio per branch with bootstrap CIs.
  4. Data diagnostic: day-to-day variation vs a Poisson model.
  5. Garden costs vs a public coffee price series.
Nothing here proves cause. Results are associations, tested against shuffled versions of the same data.
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

from common import ROOT, SEED, save_fig
from load import load_clean, save_table

rng = np.random.default_rng(SEED)
EXT = os.path.join(ROOT, "data", "external")
N_PERM = 2000
N_BOOT = 2000

# ---------------------------------------------------------------- data
d = load_clean()
BR = ["Garden", "Harbour", "Uptown"]
txb = d.groupby(["date", "Branch"])["Transaction ID"].nunique().unstack().reindex(columns=BR)
days = txb.index
weather = pd.read_csv(os.path.join(EXT, "weather_beirut_2026H1.csv"), skiprows=3)
weather.columns = ["date", "tmax", "precip"]
weather["date"] = pd.to_datetime(weather["date"])
weather = weather.set_index("date").reindex(days)
assert weather.notna().all().all(), "weather has missing days"
weather["rain_day"] = (weather.precip >= 1.0).astype(float)
cal = pd.read_csv(os.path.join(EXT, "lebanon_calendar_2026H1.csv"), parse_dates=["start", "end"])


def in_type(t):
    """Boolean Series over days: day falls inside any calendar row of type t."""
    m = pd.Series(False, index=days)
    for _, r in cal[cal.type == t].iterrows():
        m |= (days >= r.start) & (days <= r.end)
    return m


holiday = in_type("public_holiday")
print(f"days {len(days)}, weather days {len(weather)}, rain days (>=1 mm) {int(weather.rain_day.sum())}, "
      f"tmax {weather.tmax.min():.1f}-{weather.tmax.max():.1f} C, holiday days in range {int(holiday.sum())}")

# long panel: one row per branch-day
P = txb.stack().rename("tx").reset_index().rename(columns={"level_1": "Branch"})
P = P.merge(weather, left_on="date", right_index=True)
P["y"] = np.log(P.tx)
P["t"] = (P.date - days[0]).dt.days / 30.0
P["wd"] = P.date.dt.dayofweek
P["month"] = P.date.dt.month


def ols(X, y):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n, k = X.shape
    s2 = resid @ resid / (n - np.linalg.matrix_rank(X))
    cov = s2 * np.linalg.pinv(X.T @ X)
    r2 = 1 - resid @ resid / ((y - y.mean()) @ (y - y.mean()))
    return beta, np.sqrt(np.diag(cov)), r2, resid


def base_X(p, trend=True, month_fe=False):
    cols = [pd.get_dummies(p.Branch + "_" + p.wd.astype(str), dtype=float)]
    if trend:
        cols.append(pd.get_dummies(p.Branch, dtype=float).mul(p.t, axis=0).add_prefix("trend_"))
    if month_fe:
        cols.append(pd.get_dummies(p.month, prefix="m", drop_first=True, dtype=float))
    return pd.concat(cols, axis=1)


def perm_within_month(series_by_day):
    """Shuffle a day-level DataFrame's rows across days within the same month."""
    out = series_by_day.copy()
    for m, idx in series_by_day.groupby(series_by_day.index.month).groups.items():
        out.loc[idx] = series_by_day.loc[idx].values[rng.permutation(len(idx))]
    return out


# ---------------------------------------------------------------- 1. WEATHER
WCOLS = ["tmax", "rain_day"]
Xb = base_X(P)
_, _, r2_base, _ = ols(Xb.values, P.y.values)
Xf = pd.concat([Xb, P[WCOLS].reset_index(drop=True)], axis=1)
beta, se, r2_full, _ = ols(Xf.values, P.y.values)
k = len(Xb.columns)
coef = pd.DataFrame({"term": WCOLS, "coef_log": beta[k:], "se": se[k:]})
coef["ci_low"] = coef.coef_log - 1.96 * coef.se
coef["ci_high"] = coef.coef_log + 1.96 * coef.se
coef["effect_pct"] = 100 * (np.exp(coef.coef_log) - 1)
coef["effect_ci_low_pct"] = 100 * (np.exp(coef.ci_low) - 1)
coef["effect_ci_high_pct"] = 100 * (np.exp(coef.ci_high) - 1)
# permutation: shuffle weather across days within month; statistic = R2 gain and |t| per term
wday = weather[WCOLS]
gain_obs = r2_full - r2_base
t_obs = np.abs(coef.coef_log / coef.se).values
gains, tstats = [], []
for _ in range(N_PERM):
    ws = perm_within_month(wday)
    Pw = P[["date"]].merge(ws, left_on="date", right_index=True)[WCOLS].reset_index(drop=True)
    b, s, r2p, _ = ols(pd.concat([Xb, Pw], axis=1).values, P.y.values)
    gains.append(r2p - r2_base)
    tstats.append(np.abs(b[k:] / s[k:]))
gains, tstats = np.array(gains), np.array(tstats)
coef["perm_p"] = [(tstats[:, i] >= t_obs[i]).mean() for i in range(len(WCOLS))]
r2 = pd.DataFrame({"r2_weekday_trend": [r2_base], "r2_plus_weather": [r2_full], "r2_gain": [gain_obs],
                   "perm_p_r2_gain": [(gains >= gain_obs).mean()]})
print("\n1a. Weather added to weekday + log-trend model (per branch-day, log transactions):")
print(coef.round(4).to_string(index=False))
print(r2.round(5).to_string(index=False))
save_table(coef.round(5), "external_weather_coefficients.csv", index=False)
save_table(r2.round(6), "external_weather_r2.csv", index=False)

# 1b. cold-drink share of items vs temperature, beyond month and weekday
COLD = ["Cold Coffee", "Cold Drinks"]
items = d.groupby("date").Quantity.sum()
cold = d[d.Category.isin(COLD)].groupby("date").Quantity.sum().reindex(days, fill_value=0)
cs = pd.DataFrame({"cold_share": cold / items, "tmax": weather.tmax, "rain_day": weather.rain_day})
Xc = pd.concat([pd.get_dummies(days.month, prefix="m", dtype=float).set_index(days),
                pd.get_dummies(days.dayofweek, prefix="wd", drop_first=True, dtype=float).set_index(days),
                cs[["tmax"]]], axis=1)
bc, sc, _, _ = ols(Xc.values, cs.cold_share.values)
t_c = abs(bc[-1] / sc[-1])
perm_c = []
for _ in range(N_PERM):
    Xp = Xc.copy()
    Xp["tmax"] = perm_within_month(cs[["tmax"]]).tmax.values
    b, s, _, _ = ols(Xp.values, cs.cold_share.values)
    perm_c.append(abs(b[-1] / s[-1]))
cold_res = pd.DataFrame({
    "cold_share_mean": [cs.cold_share.mean()],
    "cold_share_jan": [cs.cold_share[days.month == 1].mean()], "cold_share_jun": [cs.cold_share[days.month == 6].mean()],
    "pts_per_degC_within_month": [100 * bc[-1]], "ci_low": [100 * (bc[-1] - 1.96 * sc[-1])],
    "ci_high": [100 * (bc[-1] + 1.96 * sc[-1])], "perm_p": [(np.array(perm_c) >= t_c).mean()]})
print("\n1b. Cold-drink share of items vs max temperature (month and weekday fixed effects):")
print(cold_res.round(4).to_string(index=False))
save_table(cold_res.round(5), "external_cold_share.csv", index=False)

# 1c. does weather explain the Jan->Jun growth? Estimate weather effects WITHIN month (month fixed effects,
# no trend), then ask how much of the Jan->Jun rise the change in weather would predict.
Xm = base_X(P, trend=False, month_fe=True)
bm0, _, _, _ = ols(Xm.values, P.y.values)
growth_obs = bm0[list(Xm.columns).index("m_6")]          # June vs January, log points, weekday-adjusted
Xmw = pd.concat([Xm, P[WCOLS].reset_index(drop=True)], axis=1)
bmw, smw, _, _ = ols(Xmw.values, P.y.values)
bt, bra = bmw[-2], bmw[-1]
dT = weather.tmax[days.month == 6].mean() - weather.tmax[days.month == 1].mean()
dR = weather.rain_day[days.month == 6].mean() - weather.rain_day[days.month == 1].mean()
implied = bt * dT + bra * dR
growth = pd.DataFrame({
    "jun_vs_jan_growth_pct_weekday_adjusted": [100 * (np.exp(growth_obs) - 1)],
    "tmax_jan_mean": [weather.tmax[days.month == 1].mean()], "tmax_jun_mean": [weather.tmax[days.month == 6].mean()],
    "rain_days_jan": [int(weather.rain_day[days.month == 1].sum())], "rain_days_jun": [int(weather.rain_day[days.month == 6].sum())],
    "within_month_tmax_coef_pct_per_degC": [100 * (np.exp(bt) - 1)],
    "within_month_tmax_ci_low": [100 * (np.exp(bt - 1.96 * smw[-2]) - 1)],
    "within_month_tmax_ci_high": [100 * (np.exp(bt + 1.96 * smw[-2]) - 1)],
    "within_month_rain_coef_pct": [100 * (np.exp(bra) - 1)],
    "growth_implied_by_weather_pct": [100 * (np.exp(implied) - 1)],
    "share_of_growth_implied_by_weather": [implied / growth_obs]})
print("\n1c. Jan->Jun growth vs weather (weather effects estimated within month):")
print(growth.T.round(4))
save_table(growth.round(5), "external_weather_growth.csv", index=False)

# ---------------------------------------------------------------- 2. CALENDAR
chain = txb.sum(axis=1)

# 2a. each holiday day vs the same weekday 1, 2 and 3 weeks before and after (non-holiday days only)
rows = []
for day in days[holiday.values]:
    refs = [day + pd.Timedelta(weeks=w) for w in (-3, -2, -1, 1, 2, 3)]
    refs = [r for r in refs if r in chain.index and not holiday[r]]
    if len(refs) < 3:
        continue
    rows.append({"date": day.date(), "weekday": day.day_name()[:3], "tx": chain[day],
                 "ref_mean": chain[refs].mean(), "ratio": chain[day] / chain[refs].mean(), "n_refs": len(refs)})
hol = pd.DataFrame(rows)
bs = [hol.ratio.sample(len(hol), replace=True, random_state=int(rng.integers(1e9))).mean() for _ in range(N_BOOT)]
print(f"\n2a. Holidays: {len(hol)} holiday days; mean ratio to same weekday +-1..3 weeks = {hol.ratio.mean():.3f} "
      f"[{np.percentile(bs, 2.5):.3f}, {np.percentile(bs, 97.5):.3f}]")
print(hol.round(3).to_string(index=False))
hol_summary = pd.DataFrame({"holiday_days": [len(hol)], "mean_ratio": [hol.ratio.mean()],
                            "ci_low": [np.percentile(bs, 2.5)], "ci_high": [np.percentile(bs, 97.5)]})
save_table(hol.round(4), "external_holidays.csv", index=False)
save_table(hol_summary.round(4), "external_holidays_summary.csv", index=False)

# 2b. Ramadan: evening share of transactions (18:00 or later) vs the three weeks before and after
txh = d.groupby("Transaction ID").agg(date=("date", "first"), hour=("hour", "first"))
ev = txh.assign(evening=txh.hour >= 18).groupby("date").evening.mean().reindex(days)
ram = in_type("ramadan")
before = (days >= "2026-01-28") & (days <= "2026-02-17")
after = (days >= "2026-03-24") & (days <= "2026-04-13")


def boot_diff(a, b):
    return np.percentile([rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(N_BOOT)], [2.5, 97.5])


ram_rows = []
for name, mask in [("3 weeks before (Jan 28-Feb 17)", before), ("3 weeks after (Mar 24-Apr 13)", after)]:
    lo, hi = boot_diff(ev[ram.values].values, ev[mask].values)
    ram_rows.append({"comparison": f"Ramadan vs {name}", "ramadan_evening_share": ev[ram.values].mean(),
                     "other_evening_share": ev[mask].mean(), "diff_pts": 100 * (ev[ram.values].mean() - ev[mask].mean()),
                     "ci_low_pts": 100 * lo, "ci_high_pts": 100 * hi})
ram_res = pd.DataFrame(ram_rows)
print("\n2b. Ramadan evening share (transactions at 18:00 or later):")
print(ram_res.round(4).to_string(index=False))
save_table(ram_res.round(5), "external_ramadan.csv", index=False)

# 2c. security escalation from Mar 2: actual vs the weekday + log-trend model fitted on Jan 1 - Mar 1.
# Placebo: the same model fitted on Jan 1 - Feb 1 and scored on Feb 2 - Mar 1 (no escalation).
def trend_gap(fit_end, score_start, score_end):
    tr = P[P.date <= fit_end]
    sc_ = P[(P.date >= score_start) & (P.date <= score_end)]
    Xall = base_X(P)
    b, _, _, _ = ols(Xall.loc[tr.index].values, tr.y.values)
    resid = (sc_.y - Xall.loc[sc_.index].values @ b).groupby(sc_.date).mean()   # mean over branches, per day
    wk = resid.groupby(resid.index.to_period("W"))
    means = wk.mean().values
    bs_ = [rng.choice(means, len(means)).mean() for _ in range(N_BOOT)]
    return 100 * (np.exp(resid.mean()) - 1), 100 * (np.exp(np.percentile(bs_, 2.5)) - 1), 100 * (np.exp(np.percentile(bs_, 97.5)) - 1)


esc_rows = []
for label, fe, s0, s1 in [("PLACEBO: fit Jan 1-Feb 1, score Feb 2-Mar 1", "2026-02-01", "2026-02-02", "2026-03-01"),
                          ("Escalation month: fit Jan 1-Mar 1, score Mar 2-Mar 31", "2026-03-01", "2026-03-02", "2026-03-31"),
                          ("Following month: fit Jan 1-Mar 1, score Apr 1-Apr 30", "2026-03-01", "2026-04-01", "2026-04-30")]:
    g, lo, hi = trend_gap(pd.Timestamp(fe), pd.Timestamp(s0), pd.Timestamp(s1))
    esc_rows.append({"test": label, "actual_vs_trend_pct": g, "ci_low_pct": lo, "ci_high_pct": hi})
esc = pd.DataFrame(esc_rows)
print("\n2c. Security escalation: actual transactions vs the Jan-Feb weekday + trend model:")
print(esc.round(2).to_string(index=False))
save_table(esc.round(3), "external_escalation.csv", index=False)

# 2d. KEY school/campus test: Tuesday / mean(Mon, Wed, Thu, Fri) per week, by period.
# Comparison days that are public holidays are dropped; weeks where the Tuesday itself is a holiday are flagged.
wk = pd.DataFrame({"tx": chain, "wd": days.dayofweek, "hol": holiday.values}, index=days)
wk["week"] = days.to_period("W")
recs = []
for w, g in wk.groupby("week"):
    tue = g[g.wd == 1]
    comp = g[g.wd.isin([0, 2, 3, 4]) & ~g.hol]
    mwf = g[g.wd.isin([0, 2, 4]) & ~g.hol]
    thu = g[(g.wd == 3) & ~g.hol]
    if len(tue) == 0 or len(comp) < 2:
        continue
    td = tue.index[0]
    recs.append({"week": str(w), "tuesday": td.date(), "tue_ratio": tue.tx.iloc[0] / comp.tx.mean(),
                 "thu_ratio": thu.tx.iloc[0] / mwf.tx.mean() if len(thu) and len(mwf) >= 2 else np.nan,
                 "tuesday_is_holiday": bool(tue.hol.iloc[0]), "n_comp_days": len(comp)})
W = pd.DataFrame(recs)
W["tuesday"] = pd.to_datetime(W.tuesday)


def period(t):
    if t <= pd.Timestamp("2026-03-01"):
        return "1 Jan-Feb: schools and AUB in session, before escalation"
    if t <= pd.Timestamp("2026-03-09"):
        return "2 Mar 2-9: public schools closed (escalation)"
    if t <= pd.Timestamp("2026-03-29"):
        return "3 Mar 10-29: schools reopen, AUB in person"
    if t <= pd.Timestamp("2026-05-04"):
        return "4 Mar 30-May 4: AUB online or hybrid"
    if t <= pd.Timestamp("2026-06-14"):
        return "5 May 5-Jun 14: AUB exams then no classes"
    return "6 Jun 15-30: AUB out, schools out (assumed)"


W["period"] = W.tuesday.map(period)
per = W.groupby("period").agg(weeks=("tue_ratio", "size"), tue_ratio_mean=("tue_ratio", "mean"),
                              tue_ratio_min=("tue_ratio", "min"), tue_ratio_max=("tue_ratio", "max"),
                              tuesday_holidays=("tuesday_is_holiday", "sum")).reset_index()
print("\n2d. Tuesday ratio by school/campus period (chain):")
print(per.round(3).to_string(index=False))
save_table(per.round(4), "external_tuesday_periods.csv", index=False)
save_table(W.round({"tue_ratio": 4, "thu_ratio": 4}), "external_tuesday_weekly.csv", index=False)

# campus in person (periods 1 and 3) vs campus online/out (periods 4-6): difference + permutation over weeks
inp = W.period.str[0].isin(["1", "3"])
out = W.period.str[0].isin(["4", "5", "6"])
diff_obs = W.tue_ratio[out].mean() - W.tue_ratio[inp].mean()
pool = W.tue_ratio[inp | out].values
n_out = out.sum()
perm = []
for _ in range(N_PERM):
    s = rng.permutation(pool)
    perm.append(s[:n_out].mean() - s[n_out:].mean())
lo, hi = boot_diff(W.tue_ratio[out].values, W.tue_ratio[inp].values)
late = W.period.str[0] == "6"
# sensitivity: keep only weeks with at least 3 non-holiday comparison days (the first version of this test)
W3 = W[W.n_comp_days >= 3]
inp3, out3 = W3.period.str[0].isin(["1", "3"]), W3.period.str[0].isin(["4", "5", "6"])
d3 = W3.tue_ratio[out3].mean() - W3.tue_ratio[inp3].mean()
lo3, hi3 = boot_diff(W3.tue_ratio[out3].values, W3.tue_ratio[inp3].values)
pool3, n3 = W3.tue_ratio[inp3 | out3].values, out3.sum()
perm3 = []
for _ in range(N_PERM):
    s3 = rng.permutation(pool3)
    perm3.append(s3[:n3].mean() - s3[n3:].mean())
campus = pd.DataFrame({
    "test": ["Campus online/out (Mar 30-Jun 30) minus campus in person (Jan-Feb, Mar 10-29)"],
    "weeks_a": [int(n_out)], "weeks_b": [int(inp.sum())],
    "mean_a": [W.tue_ratio[out].mean()], "mean_b": [W.tue_ratio[inp].mean()],
    "diff": [diff_obs], "ci_low": [lo], "ci_high": [hi],
    "perm_p_two_sided": [(np.abs(perm) >= abs(diff_obs)).mean()]})
campus.loc[1] = ["SENSITIVITY: same test, only weeks with >= 3 comparison days", int(n3), int(inp3.sum()),
                 W3.tue_ratio[out3].mean(), W3.tue_ratio[inp3].mean(), d3, lo3, hi3,
                 (np.abs(perm3) >= abs(d3)).mean()]
print("   Late-June weeks (school out assumed), too few for an interval:")
print(W[late][["tuesday", "tue_ratio", "tuesday_is_holiday"]].round(3).to_string(index=False))
print(f"   range of the Tuesday ratio in all other weeks: {W.tue_ratio[~late].min():.3f}-{W.tue_ratio[~late].max():.3f}")
print("\n   Campus / school-out tests on the Tuesday ratio:")
print(campus.round(3).to_string(index=False))
save_table(campus.round(4), "external_tuesday_school_tests.csv", index=False)

# 2e. Thursday check
th = W.thu_ratio.dropna()
bs = [rng.choice(th.values, len(th)).mean() for _ in range(N_BOOT)]
thu_res = pd.DataFrame({"weeks": [len(th)], "thu_over_mon_wed_fri_mean": [th.mean()],
                        "ci_low": [np.percentile(bs, 2.5)], "ci_high": [np.percentile(bs, 97.5)],
                        "tue_ratio_mean_same_weeks": [W.tue_ratio.mean()]})
print("\n2e. Thursday / mean(Mon, Wed, Fri):")
print(thu_res.round(3).to_string(index=False))
save_table(thu_res.round(4), "external_thursday.csv", index=False)

# ---------------------------------------------------------------- 3. TUESDAY BY BRANCH
bw = txb.copy()
bw["wd"] = days.dayofweek
bw["week"] = days.to_period("W")
bw = bw[~holiday.values]
weeks = bw.week.unique()
wk_groups = {w: g for w, g in bw.groupby("week")}


def branch_ratios(sample_weeks):
    g = pd.concat([wk_groups[w] for w in sample_weeks])
    tue = g[g.wd == 1][BR].mean()
    comp = g[g.wd.isin([0, 2, 3, 4])][BR].mean()
    return tue / comp


obs = branch_ratios(weeks)
boots = np.array([branch_ratios(rng.choice(weeks, len(weeks))).values for _ in range(N_BOOT)])
tb = pd.DataFrame({"branch": BR, "tue_ratio": obs.values,
                   "ci_low": np.percentile(boots, 2.5, axis=0), "ci_high": np.percentile(boots, 97.5, axis=0)})
for i, j in [(0, 1), (0, 2), (1, 2)]:
    dif = boots[:, i] - boots[:, j]
    tb.loc[len(tb)] = [f"{BR[i]} minus {BR[j]}", obs.iloc[i] - obs.iloc[j],
                       np.percentile(dif, 2.5), np.percentile(dif, 97.5)]
print("\n3. Tuesday / mean(Mon, Wed, Thu, Fri) by branch, holidays excluded, bootstrap over weeks:")
print(tb.round(3).to_string(index=False))
save_table(tb.round(4), "external_tuesday_by_branch.csv", index=False)

# ---------------------------------------------------------------- 4. POISSON DIAGNOSTIC
disp_rows = []
for b in BR:
    s = pd.DataFrame({"y": txb[b], "wd": days.dayofweek, "m": days.month})
    mu = s.groupby(["wd", "m"]).y.transform("mean")
    n_cells = s.groupby(["wd", "m"]).ngroups
    pearson = ((s.y - mu) ** 2 / mu).sum() / (len(s) - n_cells)
    # same statistic on simulated Poisson data with the same cell means
    sims = []
    for _ in range(1000):
        ys = rng.poisson(mu.values)
        mus = pd.Series(ys).groupby([s.wd.values, s.m.values]).transform("mean").values
        sims.append(((ys - mus) ** 2 / np.where(mus > 0, mus, 1)).sum() / (len(s) - n_cells))
    disp_rows.append({"branch": b, "days": len(s), "mean_tx_per_day": s.y.mean(), "dispersion_ratio": pearson,
                      "poisson_sim_p2.5": np.percentile(sims, 2.5), "poisson_sim_p97.5": np.percentile(sims, 97.5)})
disp = pd.DataFrame(disp_rows)
print("\n4. Day-to-day variation vs Poisson (variance / mean of residual counts after weekday x month):")
print(disp.round(3).to_string(index=False))
save_table(disp.round(4), "external_dispersion.csv", index=False)

# ---------------------------------------------------------------- 5. GARDEN COSTS vs COFFEE PRICE
cof = pd.read_csv(os.path.join(EXT, "coffee_price_arabica_fred.csv"), parse_dates=["observation_date"])
cof = cof.set_index("observation_date").PCOFFOTMUSDM
c_jan, c_jun = cof["2026-01-01"], cof["2026-06-01"]
n_cost = d.groupby(["Product", "Branch"])["Unit Cost (USD)"].nunique()
mc = d.groupby(["month", "Branch"])["Unit Cost (USD)"].median().unstack()
coffee_cats = d[d.Category.isin(["Hot Coffee", "Cold Coffee"])]
cc = coffee_cats.groupby(["month", "Branch"])["Unit Cost (USD)"].mean().unstack()
cost_res = pd.DataFrame({
    "arabica_usd_cents_per_lb_jan": [c_jan], "arabica_jun": [c_jun], "arabica_change_pct": [100 * (c_jun / c_jan - 1)],
    "product_branch_pairs": [len(n_cost)], "pairs_with_one_unit_cost_all_6_months": [int((n_cost == 1).sum())],
    "coffee_drink_mean_unit_cost_change_jan_jun_pct_harbour": [100 * (cc.loc[6, "Harbour"] / cc.loc[1, "Harbour"] - 1)],
    "coffee_drink_mean_unit_cost_change_jan_jun_pct_garden": [100 * (cc.loc[6, "Garden"] / cc.loc[1, "Garden"] - 1)]})
print("\n5. Garden costs vs world arabica price:")
print(cost_res.T.round(3))
save_table(cost_res.round(4), "external_coffee_cost.csv", index=False)

# ---------------------------------------------------------------- figures
fig, axes = plt.subplots(1, 3, figsize=(15, 4.3))
_, _, _, res_b = ols(Xb.values, P.y.values)
day_res = pd.Series(res_b, index=P.date.values).groupby(level=0).mean()
sc0 = axes[0].scatter(weather.tmax, 100 * day_res.values, s=10, c=days.month, cmap="viridis")
fig.colorbar(sc0, ax=axes[0], label="Month")
axes[0].axhline(0, color="grey", lw=0.8)
axes[0].set_title("Sales vs temperature, after weekday + trend")
axes[0].set_xlabel("Daily max temperature (°C), Beirut")
axes[0].set_ylabel("Transactions vs model (%, approx.)")
for r, lab in [(0, "no rain"), (1, "rain ≥ 1 mm")]:
    axes[1].hist(100 * day_res[weather.rain_day.values == r], bins=20, alpha=0.6, label=lab, density=True)
axes[1].set_title("Residual sales on rain vs dry days")
axes[1].set_xlabel("Transactions vs model (%, approx.)")
axes[1].set_ylabel("Density")
axes[1].legend()
cs_res = cs.cold_share - cs.cold_share.groupby(days.month).transform("mean")
t_res = cs.tmax - cs.tmax.groupby(days.month).transform("mean")
axes[2].scatter(t_res, 100 * cs_res, s=10, color="#c0392b")
axes[2].axhline(0, color="grey", lw=0.8)
axes[2].set_title("Cold-drink share vs temperature, within month")
axes[2].set_xlabel("Temperature minus month mean (°C)")
axes[2].set_ylabel("Cold share minus month mean (pts)")
fig.tight_layout()
save_fig(fig, "weather_vs_sales.png")

fig, axes = plt.subplots(1, 2, figsize=(14, 4.5), gridspec_kw={"width_ratios": [1, 2.2]})
tbb = tb[tb.branch.isin(BR)]
axes[0].errorbar(tbb.branch, tbb.tue_ratio, yerr=[tbb.tue_ratio - tbb.ci_low, tbb.ci_high - tbb.tue_ratio],
                 fmt="o", capsize=6, color="#c0392b")
axes[0].axhline(1, color="grey", ls="--", lw=1)
axes[0].set_ylim(0.9, 1.8)
axes[0].set_title("Tuesday / Mon-Wed-Thu-Fri, by branch (95% CI)")
axes[0].set_xlabel("Branch")
axes[0].set_ylabel("Ratio")
spans = [("2026-02-18", "2026-03-19", "#f9e79f", "Ramadan"),
         ("2026-03-02", "2026-03-09", "#f5b7b1", "Public schools closed"),
         ("2026-03-30", "2026-05-04", "#aed6f1", "AUB online/hybrid"),
         ("2026-05-05", "2026-06-30", "#d6eaf8", "AUB exams / no classes"),
         ("2026-06-15", "2026-06-30", "#d5f5e3", "School out (assumed)")]
for s0, s1, c, lab in spans:
    axes[1].axvspan(pd.Timestamp(s0), pd.Timestamp(s1), color=c, alpha=0.6, label=lab)
axes[1].plot(W.tuesday, W.tue_ratio, "o-", color="#c0392b", label="Tuesday ratio (chain)")
axes[1].plot(W.tuesday, W.thu_ratio, "s--", color="#2c3e50", ms=4, label="Thursday / Mon-Wed-Fri")
hw = W[W.tuesday_is_holiday]
axes[1].scatter(hw.tuesday, hw.tue_ratio, s=120, facecolors="none", edgecolors="k", label="Tuesday is a holiday")
axes[1].axhline(1, color="grey", ls="--", lw=1)
axes[1].set_ylim(0.6, 1.9)
axes[1].set_title("Weekly Tuesday ratio vs school and campus calendar")
axes[1].set_xlabel("Week (Tuesday date)")
axes[1].set_ylabel("Ratio")
axes[1].legend(fontsize=7, ncol=2, loc="lower left")
fig.tight_layout()
save_fig(fig, "tuesday_by_branch_school.png")
print("\nsaved figures/weather_vs_sales.png, figures/tuesday_by_branch_school.png")

# ---------------------------------------------------------------- summary table
c = coef.set_index("term")
g = growth.iloc[0]
summary = pd.DataFrame([
    ["Temperature", "Open-Meteo daily max temperature, Beirut",
     "Add to weekday + log-trend model; permutation within month",
     f"{c.loc['tmax', 'effect_pct']:+.2f}% transactions per degC [{c.loc['tmax', 'effect_ci_low_pct']:+.2f}, {c.loc['tmax', 'effect_ci_high_pct']:+.2f}], p = {c.loc['tmax', 'perm_p']:.2f}",
     "does not explain"],
    ["Rain", "Open-Meteo daily precipitation (rain day = 1 mm or more)",
     "Same model",
     f"{c.loc['rain_day', 'effect_pct']:+.1f}% on rain days [{c.loc['rain_day', 'effect_ci_low_pct']:+.1f}, {c.loc['rain_day', 'effect_ci_high_pct']:+.1f}], p = {c.loc['rain_day', 'perm_p']:.2f}; R2 gain from both {r2.r2_gain[0]:.5f}, p = {r2.perm_p_r2_gain[0]:.2f}",
     "does not explain"],
    ["Hot days and cold drinks", "Open-Meteo max temperature",
     "Cold-drink share of items vs temperature, month and weekday fixed effects",
     f"{cold_res.pts_per_degC_within_month[0]:+.2f} pts per degC [{cold_res.ci_low[0]:+.2f}, {cold_res.ci_high[0]:+.2f}], p = {cold_res.perm_p[0]:.2f}; share {100*cold_res.cold_share_jan[0]:.1f}% in Jan vs {100*cold_res.cold_share_jun[0]:.1f}% in Jun",
     "does not explain"],
    ["Jan to Jun growth", "Open-Meteo",
     "Weather effect estimated within month, applied to the Jan-Jun change in weather",
     f"weather predicts {g.growth_implied_by_weather_pct:+.1f}% of the observed {g['jun_vs_jan_growth_pct_weekday_adjusted']:+.1f}%",
     "does not explain"],
    ["Public holidays", "holidaydb.com, calendarlabs.com",
     "Holiday day vs same weekday 1-3 weeks before and after",
     f"mean ratio {hol_summary.mean_ratio[0]:.3f} [{hol_summary.ci_low[0]:.3f}, {hol_summary.ci_high[0]:.3f}] over {hol_summary.holiday_days[0]} days",
     "does not explain"],
    ["Ramadan", "L'Orient Today (dates)",
     "Share of transactions at 18:00 or later, Ramadan vs 3 weeks before and after",
     f"{ram_res.diff_pts[0]:+.1f} pts [{ram_res.ci_low_pts[0]:+.1f}, {ram_res.ci_high_pts[0]:+.1f}] vs before; {ram_res.diff_pts[1]:+.1f} pts [{ram_res.ci_low_pts[1]:+.1f}, {ram_res.ci_high_pts[1]:+.1f}] vs after",
     "does not explain"],
    ["Security escalation from Mar 2", "Al-Monitor, LBC (dates)",
     "Actual vs Jan-Feb weekday + trend model; placebo on Feb",
     f"Mar {esc.actual_vs_trend_pct[1]:+.1f}% [{esc.ci_low_pct[1]:+.1f}, {esc.ci_high_pct[1]:+.1f}], Apr {esc.actual_vs_trend_pct[2]:+.1f}% [{esc.ci_low_pct[2]:+.1f}, {esc.ci_high_pct[2]:+.1f}]; placebo Feb {esc.actual_vs_trend_pct[0]:+.1f}%",
     "does not explain"],
    ["School or campus drives Tuesday", "AUB Provost calendar, LBC school closures",
     "Tuesday ratio, campus online/out vs in person (permutation over weeks)",
     f"{campus['diff'][0]:+.3f} [{campus.ci_low[0]:+.3f}, {campus.ci_high[0]:+.3f}], p = {campus.perm_p_two_sided[0]:.2f}; Tuesday still {campus.mean_a[0]:.2f}x with campus out",
     "does not explain"],
    ["University Tue/Thu timetable", "Transactions only",
     "Thursday / mean(Mon, Wed, Fri)",
     f"{thu_res.thu_over_mon_wed_fri_mean[0]:.3f} [{thu_res.ci_low[0]:.3f}, {thu_res.ci_high[0]:.3f}]",
     "does not explain"],
    ["Local cause (school, market day near one branch)", "Transactions by branch",
     "Tuesday ratio per branch, bootstrap over weeks",
     "; ".join(f"{r.branch} {r.tue_ratio:.2f} [{r.ci_low:.2f}, {r.ci_high:.2f}]" for r in tb[tb.branch.isin(BR)].itertuples()),
     "does not explain"],
    ["Real-world day-to-day noise", "Transactions only",
     "Variance / mean of daily counts after weekday x month, vs simulated Poisson",
     "; ".join(f"{r.branch} {r.dispersion_ratio:.2f} (Poisson range {r._5:.2f}-{r._6:.2f})" for r in disp.itertuples()),
     "cannot tell (data diagnostic)"],
    ["World coffee price and Garden's costs", "FRED PCOFFOTMUSDM (IMF arabica price)",
     "Do recorded unit costs move with the world price?",
     f"arabica {cost_res.arabica_change_pct[0]:+.1f}% Jan-Jun; {cost_res.pairs_with_one_unit_cost_all_6_months[0]} of {cost_res.product_branch_pairs[0]} product-branch pairs keep one unit cost all six months",
     "cannot tell"],
], columns=["factor", "dataset", "test", "result", "verdict"])
save_table(summary, "external_factors_summary.csv", index=False)
print("\nOutside factors we checked:")
print(summary.to_string(index=False))
