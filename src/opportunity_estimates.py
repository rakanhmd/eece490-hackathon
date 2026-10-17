"""Opportunity estimates (ESTIMATES, not measurements; every assumption is printed and saved).

a) Saturday. Saturday is Stories' quietest day. How much would six months of Saturdays add if Saturday
   (1) reached the average of Mon, Wed, Thu and Fri, or (2) gained 25% or 50% of Tuesday's lift
   (Tuesday minus that same average)? Uses each branch's actual Saturday basket value and gross margin.
   Assumptions: extra Saturday transactions look like today's Saturday transactions; no customers move from
   other days; no extra staff or waste cost (we have no labour data).
b) Inflation. Prices never changed from January to June while Lebanon's consumer prices rose 17.25% in the
   year to June 2026 (CAS; data/external/benchmarks.csv). Monthly rate = 1.1725 ** (1/12) - 1. Real price lost by
   June = 1 - 1 / (1 + monthly) ** 5 (five monthly steps from January to June). Profit effect of one
   inflation-matched rise of (1 + monthly) ** 5 - 1 on every price, applied to the same six months of volume,
   under constant elasticity 0 to -2 per product, unit costs and discount rates as observed.
   Assumptions: CPI (measured in Lebanese pounds) is a fair guide to price pressure on USD menu prices;
   costs do not move; competitors do not change prices.
"""
import os

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from common import ROOT
from load import GP, REV, load_clean, save_table

d = load_clean()
BR = ["Garden", "Harbour", "Uptown"]
bm = pd.read_csv(os.path.join(ROOT, "data", "external", "benchmarks.csv")).set_index("metric")

# ---------------- a) Saturday ----------------
tx = d.groupby(["date", "Branch"])["Transaction ID"].nunique().unstack()
wd = tx.index.dayofweek
n_sat = int((wd == 5).sum())
sat = d[d.weekday == 5]
sat_tx = sat.groupby("Branch")["Transaction ID"].nunique()
basket = sat.groupby("Branch")[REV].sum() / sat_tx
margin = sat.groupby("Branch")[GP].sum() / sat.groupby("Branch")[REV].sum()
rows = []
for b in BR:
    s_mean = tx.loc[wd == 5, b].mean()
    avg_wd = tx.loc[np.isin(wd, [0, 2, 3, 4]), b].mean()
    tue = tx.loc[wd == 1, b].mean()
    lift = tue - avg_wd
    for scen, gain in [("Saturday reaches the Mon/Wed/Thu/Fri average", avg_wd - s_mean),
                       ("Saturday gains 25% of Tuesday's lift", 0.25 * lift),
                       ("Saturday gains 50% of Tuesday's lift", 0.50 * lift)]:
        extra_tx = gain * n_sat
        rows.append({"branch": b, "scenario": scen, "saturdays": n_sat, "saturday_tx_per_day": s_mean,
                     "mon_wed_thu_fri_tx_per_day": avg_wd, "tuesday_tx_per_day": tue,
                     "extra_tx_per_saturday": gain, "extra_tx_6mo": extra_tx,
                     "saturday_basket_usd": basket[b], "saturday_gross_margin": margin[b],
                     "extra_revenue_6mo_usd": extra_tx * basket[b],
                     "extra_gross_profit_6mo_usd": extra_tx * basket[b] * margin[b]})
satdf = pd.DataFrame(rows)
tot = satdf.groupby("scenario")[["extra_tx_6mo", "extra_revenue_6mo_usd", "extra_gross_profit_6mo_usd"]].sum()
tot["extra_gross_profit_per_year_usd"] = tot.extra_gross_profit_6mo_usd * 2   # per year = six months x 2
# Shifting: regulars (98.5% of identified customers buy more than once; 93.8% use several branches) may move
# visits from other days or branches instead of adding new ones. Net gain = gross gain x (1 - shifted share).
rng_rows = []
for scen in tot.index:
    for shift in [0.0, 0.5]:
        rng_rows.append({"scenario": scen, "shifted_share": shift,
                         "net_extra_gross_profit_6mo_usd": tot.loc[scen, "extra_gross_profit_6mo_usd"] * (1 - shift)})
sat_range = pd.DataFrame(rng_rows)
print("\nSaturday with half of the extra visits shifted from other days or branches (ESTIMATE):\n", sat_range.round(0))
save_table(sat_range.round(2), "opportunity_saturday_range.csv", index=False)
print(f"a) Saturday ({n_sat} Saturdays). Per branch:")
print(satdf[["branch", "scenario", "saturday_tx_per_day", "mon_wed_thu_fri_tx_per_day", "tuesday_tx_per_day",
             "extra_tx_per_saturday", "saturday_basket_usd", "saturday_gross_margin",
             "extra_gross_profit_6mo_usd"]].round(2).to_string(index=False))
print("\nAll branches (ESTIMATE):\n", tot.round(0))
save_table(satdf.round(4), "opportunity_saturday_by_branch.csv", index=False)
save_table(tot.round(2), "opportunity_saturday_total.csv")

# ---------------- b) inflation ----------------
cpi = float(bm.loc["lebanon_cpi_yoy_jun2026", "value"]) / 100
monthly = (1 + cpi) ** (1 / 12) - 1
lost_by_june = 1 - 1 / (1 + monthly) ** 5
avg_lost = 1 - np.mean([1 / (1 + monthly) ** m for m in range(6)])
rise = (1 + monthly) ** 5 - 1
n_price_changes = int((d.groupby(["Product", "Branch"])["Unit Price (USD)"].nunique() - 1).sum())
print(f"\nb) CPI {100*cpi:.2f}%/yr -> {100*monthly:.3f}%/month; price changes Jan-Jun: {n_price_changes}")
print(f"   real price lost by June vs January: {100*lost_by_june:.2f}%; average over Jan-Jun: {100*avg_lost:.2f}%")
print(f"   inflation-matched price rise tested: +{100*rise:.2f}%")

pb = d.groupby(["Product", "Branch"]).agg(price=("Unit Price (USD)", "first"), cost=("Unit Cost (USD)", "first"),
                                          units=("Quantity", "sum"), rev=(REV, "sum"), lst=("list_revenue", "sum"))
pb["f"] = pb.rev / pb.lst


def gain(e, sub=pb):
    q1 = sub.units * (1 + rise) ** e
    return float((q1 * (sub.price * (1 + rise) * sub.f - sub.cost) - sub.units * (sub.price * sub.f - sub.cost)).sum())


inf_rows = []
for e in [0.0, -0.5, -1.0, -1.5, -2.0]:
    r = {"elasticity": e, "units_change_pct": 100 * ((1 + rise) ** e - 1), "gp_change_6mo_usd_all": gain(e)}
    for b in BR:
        r[f"gp_change_6mo_usd_{b}"] = gain(e, pb.xs(b, level="Branch"))
    r["gp_change_6mo_usd_Garden_Uptown"] = r["gp_change_6mo_usd_Garden"] + r["gp_change_6mo_usd_Uptown"]
    r["gp_change_per_year_usd_all"] = r["gp_change_6mo_usd_all"] * 2   # per year = six months x 2
    inf_rows.append(r)
be = brentq(lambda e: gain(e), -30, -0.01)
infl = pd.DataFrame(inf_rows)
print("\nInflation-matched price rise, gross-profit change over six months (ESTIMATE):")
print(infl.round(1).to_string(index=False))
print(f"break-even elasticity (all branches): {be:.2f}; units change at break-even: {100*((1+rise)**be-1):.1f}%")
meta = pd.DataFrame({"cpi_yoy_jun2026": [cpi], "monthly_rate": [monthly], "real_price_lost_by_june": [lost_by_june],
                     "real_price_lost_avg_jan_jun": [avg_lost], "price_rise_tested": [rise],
                     "price_changes_jan_jun": [n_price_changes], "break_even_elasticity": [be],
                     "units_change_at_break_even": [(1 + rise) ** be - 1]})
save_table(infl.round(2), "opportunity_inflation_price.csv", index=False)
save_table(meta.round(5), "opportunity_inflation_meta.csv", index=False)
