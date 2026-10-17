"""How Stories compares with other coffee chains: published benchmarks as context, not causes.

Reads data/external/benchmarks.csv (each value with its source URL; see data/README.md) and computes the
matching Stories numbers from the transaction data and earlier results. No correlations with quarterly or
annual outside figures: each benchmark is set next to one Stories number, nothing more.
"""
import os

import numpy as np
import pandas as pd

from common import ROOT
from load import REV, load_clean, save_table

d = load_clean()
bm = pd.read_csv(os.path.join(ROOT, "data", "external", "benchmarks.csv")).set_index("metric")
res = os.path.join(ROOT, "results")


def bval(m):
    return float(bm.loc[m, "value"])


rows = []

# ---------- 1. day of week ----------
tx = d.groupby(["date"])["Transaction ID"].nunique()
per_wd = tx.groupby(tx.index.dayofweek).mean()
others = per_wd.loc[[0, 2, 3, 4]].mean()
rows += [
    ["Day of week", "Busiest day", "Saturday (Starbucks, Placer.ai; UK coffee, Square)",
     ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][int(per_wd.idxmax())], "transactions per day"],
    ["Day of week", "Tuesday vs Mon, Wed, Thu, Fri", "no published Tuesday peak found",
     f"{per_wd[1] / others:.2f}x", "transactions per day"],
    ["Day of week", "Saturday vs Mon, Wed, Thu, Fri (UK: vs the average weekday, the source's definition)",
     f"{bval('saturday_vs_average_weekday_uk_coffee'):.2f}x (UK, busiest day)",
     f"{per_wd[5] / others:.2f}x (quietest day)", "transactions per day"],
]

# ---------- 2. cost share ----------
DRINK_COFFEE = ["Hot Coffee", "Cold Coffee"]
FOOD = ["Bakery", "Breakfast", "Desserts", "Meals", "Sandwiches"]


def cost_share(x):
    return 100 * x["cost"].sum() / x[REV].sum()


cs = {"All branches": cost_share(d)}
for b in ["Harbour", "Uptown", "Garden"]:
    cs[b] = cost_share(d[d.Branch == b])
rows.append(["Cost share", "Cost of goods as % of net sales", f"Starbucks {bval('starbucks_product_distribution_cost_pct_revenue'):.1f}% (FY2025)",
             "; ".join(f"{k} {v:.1f}%" for k, v in cs.items()), "unit cost x quantity / revenue after discounts"])
for label, cats, lo, hi in [("Coffee drinks", DRINK_COFFEE, "cafe_coffee_cogs_target_low", "cafe_coffee_cogs_target_high"),
                            ("Food", FOOD, "cafe_food_cogs_target_low", "cafe_food_cogs_target_high")]:
    sub = d[d.Category.isin(cats)]
    vals = {b: cost_share(sub[sub.Branch == b]) for b in ["Harbour", "Uptown", "Garden"]}
    rows.append(["Cost share", f"{label}: cost as % of {label.lower()} sales",
                 f"{bval(lo):.0f}-{bval(hi):.0f}% (café target, Zest)",
                 "; ".join(f"{k} {v:.1f}%" for k, v in vals.items()), "unit cost x quantity / revenue after discounts"])

# ---------- 3. growth vs inflation ----------
g = pd.read_csv(os.path.join(res, "external_weather_growth.csv")).iloc[0]
n_price_changes = int((d.groupby(["Product", "Branch"])["Unit Price (USD)"].nunique() - 1).sum())
rows += [
    ["Growth vs inflation", "June vs January transactions, weekday-adjusted",
     f"Lebanon CPI +{bval('lebanon_cpi_yoy_jun2026'):.2f}% year on year in June 2026 (CAS)",
     f"+{g['jun_vs_jan_growth_pct_weekday_adjusted']:.1f}% in five months with no price changes, so volume, not price",
     "transaction counts, not dollars"],
    ["Growth vs inflation", "Price changes Jan-Jun", "consumer prices rose about 17% over the year to June",
     f"{n_price_changes} price changes across 135 product-branch price lists", "Unit Price per product and branch"],
]

# ---------- 4. weather ----------
cold = pd.read_csv(os.path.join(res, "external_cold_share.csv")).iloc[0]
wc = pd.read_csv(os.path.join(res, "external_weather_coefficients.csv")).set_index("term")
rows += [
    ["Weather", "Cold-coffee/cold-drink share per 1 degC of daily max temperature",
     f"+{bval('cold_coffee_share_pts_per_degC_london'):.1f} pts (one London café, cold coffee)",
     f"{cold.pts_per_degC_within_month:+.2f} pts [{cold.ci_low:+.2f}, {cold.ci_high:+.2f}] (cold coffee + cold drinks, within month)",
     "share of items"],
    ["Weather", "Rain", "less coffee-shop traffic when it rains (Foursquare/AccuWeather, US)",
     f"{wc.loc['rain_day', 'effect_pct']:+.1f}% on rain days [{wc.loc['rain_day', 'effect_ci_low_pct']:+.1f}, {wc.loc['rain_day', 'effect_ci_high_pct']:+.1f}]",
     "transactions"],
]

out = pd.DataFrame(rows, columns=["topic", "measure", "benchmark", "stories", "stories_basis"])
pd.set_option("display.max_colwidth", 120)
print(out.to_string(index=False))
save_table(out, "benchmarks_comparison.csv", index=False)
