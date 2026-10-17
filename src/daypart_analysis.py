"""Finding 9: who buys when? Weekday vs weekend, commuters, students, and daypart x order type.

MEASURED
  1. Transactions per day by weekday and branch; weekend dip (Sat+Sun vs Mon, Wed, Thu, Fri) with a
     bootstrap CI over weeks.
  2. Commute test: share of transactions between 07:00 and 09:59 on weekdays vs weekends.
  3. Student test: weekday volume during AUB online / reading / exam / no-class periods vs term, controlling
     for branch x weekday and a branch trend (calendar: data/external/lebanon_calendar_2026H1.csv).
  4. Daypart x order type: dine-in share, basket value and share of traffic by time slot, per branch, plus how
     similar the branches' hourly and weekday shapes are.
ESTIMATED (labelled)
  5. Evening dessert attach test: extra gross profit if more evening transactions included a dessert.
Associations only; nothing here proves who the customers are.
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import ROOT, SEED, save_fig
from load import GP, REV, load_clean, save_table

rng = np.random.default_rng(SEED)
N_BOOT = 2000
BR = ["Garden", "Harbour", "Uptown"]
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
d = load_clean()
tx = d.groupby("Transaction ID").agg(date=("date", "first"), hour=("hour", "first"), branch=("Branch", "first"),
                                     weekday=("weekday", "first"), order=("Order Type", "first"),
                                     rev=(REV, "sum"), gp=(GP, "sum"),
                                     dessert=("Category", lambda s: (s == "Desserts").any()))
daily = tx.groupby(["date", "branch"]).size().unstack().reindex(columns=BR)
wd = daily.index.dayofweek

# ---------------- 1. weekday vs weekend ----------------
per_wd = daily.groupby(wd).mean()
per_wd.index = DAYS
per_wd["All"] = per_wd[BR].sum(axis=1)
print("1. Mean transactions per day:\n", per_wd.round(1))
save_table(per_wd.round(2), "daypart_tx_per_weekday.csv")

weeks = daily.index.to_period("W")
groups = {w: g for w, g in daily.assign(wd=wd).groupby(weeks)}
wk_list = list(groups)


def weekend_ratio(sample):
    g = pd.concat([groups[w] for w in sample])
    g = g.assign(All=g[BR].sum(axis=1))
    wkend = g[g.wd >= 5][BR + ["All"]].mean()
    wkday = g[g.wd.isin([0, 2, 3, 4])][BR + ["All"]].mean()
    return wkend / wkday


obs = weekend_ratio(wk_list)
bs = np.array([weekend_ratio(rng.choice(wk_list, len(wk_list))).values for _ in range(N_BOOT)])
dip = pd.DataFrame({"weekend_vs_mon_wed_thu_fri": obs.values,
                    "ci_low": np.percentile(bs, 2.5, axis=0), "ci_high": np.percentile(bs, 97.5, axis=0)},
                   index=BR + ["All"])
print("\n   Weekend (Sat+Sun) / mean(Mon, Wed, Thu, Fri), bootstrap over weeks:\n", dip.round(3))
save_table(dip.round(4), "daypart_weekend_dip.csv")

# ---------------- 2. commute test ----------------
tx["morning"] = tx.hour.between(7, 9)
tx["weekend"] = tx.weekday >= 5
day_share = tx.groupby("date").agg(m=("morning", "mean"), wkend=("weekend", "first"))
a, b = day_share[~day_share.wkend].m.values, day_share[day_share.wkend].m.values
diffs = [rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(N_BOOT)]
commute = pd.DataFrame({"weekday_morning_share": [tx[~tx.weekend].morning.mean()],
                        "weekend_morning_share": [tx[tx.weekend].morning.mean()],
                        "diff_pts": [100 * (tx[~tx.weekend].morning.mean() - tx[tx.weekend].morning.mean())],
                        "ci_low_pts": [100 * np.percentile(diffs, 2.5)], "ci_high_pts": [100 * np.percentile(diffs, 97.5)]})
print("\n2. Share of transactions 07:00-09:59, weekdays vs weekends:\n", commute.round(4).T)
save_table(commute.round(5), "daypart_commute_test.csv", index=False)

# ---------------- 3. student test ----------------
cal = pd.read_csv(os.path.join(ROOT, "data", "external", "lebanon_calendar_2026H1.csv"), parse_dates=["start", "end"])
days = daily.index


def in_type(t):
    m = pd.Series(False, index=days)
    for _, r in cal[cal.type == t].iterrows():
        m |= (days >= r.start) & (days <= r.end)
    return m


holiday = in_type("public_holiday")
period = pd.Series("term (in person)", index=days)
period[(days >= "2026-03-02") & (days <= "2026-03-09")] = "schools closed (escalation)"
period[in_type("university_online").values] = "AUB online/hybrid"
period[(days >= "2026-05-05") & (days <= "2026-05-07")] = "AUB reading period"
period[in_type("university_exams").values] = "AUB exams"
period[(days >= "2026-05-18")] = "AUB no classes"
P = daily.stack().rename("tx").reset_index().rename(columns={"level_1": "branch"})
P["wd"] = P.date.dt.dayofweek
P["period"] = P.date.map(period)
P["hol"] = P.date.map(holiday)
P = P[(P.wd < 5) & ~P.hol].reset_index(drop=True)      # weekdays, holidays excluded
P["y"] = np.log(P.tx)
P["t"] = (P.date - days[0]).dt.days / 30.0
LEVELS = ["schools closed (escalation)", "AUB online/hybrid", "AUB reading period", "AUB exams", "AUB no classes"]


def fit(p):
    X = pd.concat([pd.get_dummies(p.branch + "_" + p.wd.astype(str), dtype=float),
                   pd.get_dummies(p.branch, dtype=float).mul(p.t, axis=0),
                   pd.DataFrame({lv: (p.period == lv).astype(float) for lv in LEVELS})], axis=1)
    beta, *_ = np.linalg.lstsq(X.values, p.y.values, rcond=None)
    out = beta[-len(LEVELS):].copy()
    present = np.array([(p.period == lv).any() for lv in LEVELS])
    out[~present] = np.nan          # a resample without that period says nothing about it
    return out


est = fit(P)
P["week"] = P.date.dt.to_period("W")
pw = {w: g for w, g in P.groupby("week")}
wl = list(pw)
boot = np.array([fit(pd.concat([pw[w] for w in rng.choice(wl, len(wl))], ignore_index=True)) for _ in range(1000)])
stud = pd.DataFrame({"period_vs_term": LEVELS, "bootstrap_draws_with_period": (~np.isnan(boot)).sum(axis=0), "weekdays": [int((P.period == lv).sum() / 3) for lv in LEVELS],
                     "effect_pct": 100 * (np.exp(est) - 1),
                     "ci_low_pct": 100 * (np.exp(np.nanpercentile(boot, 2.5, axis=0)) - 1),
                     "ci_high_pct": 100 * (np.exp(np.nanpercentile(boot, 97.5, axis=0)) - 1)})
print("\n3. Weekday volume vs in-person term (branch x weekday + branch trend; week-block bootstrap):\n", stud.round(2))
save_table(stud.round(3), "daypart_student_test.csv", index=False)

# ---------------- 4. daypart x order type ----------------
SLOTS = [("07-10", 7, 9), ("10-14", 10, 13), ("14-19", 14, 18), ("19-24", 19, 23)]
tx["slot"] = pd.cut(tx.hour, [6, 9, 13, 18, 23], labels=[s[0] for s in SLOTS])
tx["daytime"] = np.where(tx.hour < 19, "07-19 (daytime)", "19-24 (evening)")
tx["dinein"] = tx.order == "Dine-in"
rows = []
for b in BR + ["All"]:
    sub = tx if b == "All" else tx[tx.branch == b]
    for col in ["slot", "daytime"]:
        for s, g in sub.groupby(col, observed=True):
            rows.append({"branch": b, "slot": s, "share_of_transactions": len(g) / len(sub),
                         "dine_in_share": g.dinein.mean(), "basket_value_usd": g.rev.mean(),
                         "dessert_attach_rate": g.dessert.mean(), "gross_profit_per_tx_usd": g.gp.mean()})
dp = pd.DataFrame(rows)
print("\n4. Daypart x order type:\n", dp.round(3).to_string(index=False))
hourly_dinein = tx.groupby(["hour", "branch"]).dinein.mean().unstack().reindex(columns=BR)
hourly_dinein["All"] = tx.groupby("hour").dinein.mean()
print("\n   Dine-in share by hour:\n", hourly_dinein.round(3))
save_table(hourly_dinein.round(4), "daypart_dinein_by_hour.csv")
save_table(dp.round(4), "daypart_slots.csv", index=False)

hour_share = tx.groupby(["branch", "hour"]).size().unstack(0)
hour_share = hour_share / hour_share.sum()
wd_share = daily.groupby(wd).mean()
wd_share = wd_share / wd_share.sum()
sim = pd.DataFrame([{"pair": f"{BR[i]}-{BR[j]}", "hourly_profile_corr": hour_share[BR[i]].corr(hour_share[BR[j]]),
                     "weekday_profile_corr": wd_share[BR[i]].corr(wd_share[BR[j]])}
                    for i in range(3) for j in range(i + 1, 3)])
print("\n   Branch shape similarity:\n", sim.round(4).to_string(index=False))
save_table(sim.round(4), "daypart_branch_similarity.csv", index=False)

# ---------------- 5. ESTIMATE: evening dessert attach test ----------------
des = d[d.Category == "Desserts"]
des_gp_unit = des.groupby("Branch")[GP].sum() / des.groupby("Branch").Quantity.sum()
eve = tx[tx.hour >= 19]
est_rows = []
for b in BR:
    n_eve = int((eve.branch == b).sum())
    base = eve[eve.branch == b].dessert.mean()
    for pts in [1.0, 2.5, 5.0]:
        extra = n_eve * pts / 100
        est_rows.append({"branch": b, "evening_tx_6mo": n_eve, "evening_dessert_attach_now": base,
                         "attach_rise_pts": pts, "extra_dessert_baskets": extra,
                         "dessert_gp_per_unit_usd": des_gp_unit[b], "extra_gp_6mo_usd": extra * des_gp_unit[b]})
ev = pd.DataFrame(est_rows)
ev_tot = ev.groupby("attach_rise_pts")[["extra_dessert_baskets", "extra_gp_6mo_usd"]].sum()
print("\n5. ESTIMATE, evening (19:00+) dessert attach rise; one dessert per extra basket at the branch's dessert GP/unit:")
print(ev.round(3).to_string(index=False))
print(ev_tot.round(1))
save_table(ev.round(4), "daypart_evening_dessert_estimate.csv", index=False)
save_table(ev_tot.round(2), "daypart_evening_dessert_total.csv")

# ---------------- figure ----------------
fig, axes = plt.subplots(1, 4, figsize=(20, 4.3))
cols = {"Garden": "#7f8c8d", "Harbour": "#c0392b", "Uptown": "#2c3e50"}
for b in BR:
    axes[0].plot(DAYS, per_wd[b] / per_wd.loc[["Mon", "Wed", "Thu", "Fri"], b].mean(), "o-", color=cols[b], label=b)
    axes[1].plot(hour_share.index, 100 * hour_share[b], color=cols[b], label=b)
    hd = tx[tx.branch == b].groupby("hour").dinein.mean()
    axes[2].plot(hd.index, 100 * hd.values, color=cols[b], label=b)
axes[0].axhline(1, color="grey", ls="--", lw=0.8)
axes[0].set_title("Transactions per day vs Mon/Wed/Thu/Fri average")
axes[0].set_xlabel("Weekday"); axes[0].set_ylabel("Ratio"); axes[0].legend(fontsize=8)
axes[1].set_title("Share of transactions by hour")
axes[1].set_xlabel("Hour of day"); axes[1].set_ylabel("% of branch transactions")
axes[2].set_title("Dine-in share by hour")
axes[2].set_xlabel("Hour of day"); axes[2].set_ylabel("Dine-in, % of transactions")
slot_tab = dp[(dp.branch.isin(BR)) & (dp.slot.isin([s[0] for s in SLOTS]))].pivot(index="slot", columns="branch", values="basket_value_usd")
slot_tab.loc[[s[0] for s in SLOTS], BR].plot.bar(ax=axes[3], color=[cols[b] for b in BR], rot=0)
axes[3].set_title("Basket value by time slot")
axes[3].set_xlabel("Time slot (hours)"); axes[3].set_ylabel("Revenue per transaction (USD)")
axes[3].set_ylim(0, slot_tab.values.max() * 1.4)
axes[3].legend(fontsize=8, ncol=3, loc="upper center")
fig.tight_layout()
save_fig(fig, "daypart_ordertype.png")
print("saved figures/daypart_ordertype.png")
