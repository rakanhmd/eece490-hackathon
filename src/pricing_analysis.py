"""Finding 4: branch price lists vs branch costs.

MEASURED: is there one fixed list price per product per branch (over all six months)?
          How do Garden's and Uptown's price lists compare with Harbour's, and with their own costs?
ESTIMATED: gross-profit change if Garden and/or Uptown moved to Harbour's price list, under a range of
           price elasticities. Elasticity cannot be measured from this data (prices never change),
           so it is an assumption, shown as a range, with the break-even elasticity for each scenario.
Demand model (assumption): constant elasticity, Q1 = Q0 * (P1 / P0) ** e, applied per product.
Discount rates and unit costs are kept as observed.
"""
import numpy as np
import pandas as pd
from scipy.optimize import brentq

from load import GP, REV, load_clean, save_table

d = load_clean()

# ---------------- MEASURED ----------------
n_prices = d.groupby(["Product", "Branch"])["Unit Price (USD)"].nunique()
n_costs = d.groupby(["Product", "Branch"])["Unit Cost (USD)"].nunique()
print(f"product-branch pairs: {len(n_prices)}; with exactly one price: {(n_prices == 1).sum()}; "
      f"with exactly one unit cost: {(n_costs == 1).sum()}")

pb = d.groupby(["Product", "Branch"]).agg(
    price=("Unit Price (USD)", "first"), cost=("Unit Cost (USD)", "first"),
    units=("Quantity", "sum"), revenue=(REV, "sum"), gp=(GP, "sum"),
    list_rev=("list_revenue", "sum"))
pb["net_factor"] = pb.revenue / pb.list_rev          # 1 - average discount actually given
pb = pb.reset_index()
wide = pb.pivot(index="Product", columns="Branch", values=["price", "cost"])
ratios = pd.DataFrame({
    "price_garden_vs_harbour": wide["price"]["Garden"] / wide["price"]["Harbour"],
    "price_uptown_vs_harbour": wide["price"]["Uptown"] / wide["price"]["Harbour"],
    "cost_garden_vs_harbour": wide["cost"]["Garden"] / wide["cost"]["Harbour"],
    "cost_uptown_vs_harbour": wide["cost"]["Uptown"] / wide["cost"]["Harbour"],
})
summary = ratios.agg(["min", "median", "max"]).T.round(4)
# revenue-weighted average (weights = Harbour units, so it reflects the same basket)
w = pb[pb.Branch == "Harbour"].set_index("Product").units
summary["harbour_unit_weighted_mean"] = [np.average(ratios[c], weights=w.loc[ratios.index]) for c in ratios]
summary = summary.round(4)
print("\nPrice and cost ratios vs Harbour (45 products):\n", summary)
save_table(summary, "pricing_ratios_summary.csv")

# per-branch margin at list price (before discounts), unit-weighted
lm = pb.assign(list_gp=lambda x: x.units * (x.price - x.cost)).groupby("Branch")[["list_rev", "list_gp"]].sum()
lm["list_margin"] = (lm.list_gp / lm.list_rev).round(4)
print("\nMargin at list price (no discounts):\n", lm.round({"list_rev": 0, "list_gp": 0, "list_margin": 4}))
save_table(lm.round(4), "pricing_list_margin_by_branch.csv")

# ---------------- ESTIMATED ----------------
harbour_price = wide["price"]["Harbour"]
ELASTICITIES = [0.0, -0.5, -1.0, -1.5, -2.0]


def scenario_gain(branch, e, move=1.0):
    """Gross-profit change over Jan-Jun if `branch` moves `move` of the way to Harbour's price."""
    x = pb[pb.Branch == branch].set_index("Product")
    p0 = x.price
    p1 = p0 + move * (harbour_price.loc[x.index] - p0)
    q1 = x.units * (p1 / p0) ** e
    gp1 = q1 * (p1 * x.net_factor - x.cost)
    gp0 = x.units * (p0 * x.net_factor - x.cost)  # equals observed gp up to rounding
    return float((gp1 - gp0).sum()), float(x.units.sum()), float(q1.sum())


rows = []
for branch in ["Garden", "Uptown"]:
    for move, label in [(1.0, "full: match Harbour"), (0.5, "half-way")]:
        for e in ELASTICITIES:
            g, q0, q1 = scenario_gain(branch, e, move)
            rows.append({"branch": branch, "scenario": label, "elasticity": e,
                         "units_change_pct": round(100 * (q1 / q0 - 1), 1),
                         "gp_change_6mo_usd": round(g), "gp_change_per_year_usd": round(g * 365 / 181)})
        be = brentq(lambda e: scenario_gain(branch, e, move)[0], -30, -0.01)
        rows.append({"branch": branch, "scenario": label, "elasticity": round(be, 2),
                     "units_change_pct": np.nan, "gp_change_6mo_usd": 0, "gp_change_per_year_usd": 0,
                     "note": "break-even elasticity"})
est = pd.DataFrame(rows)
print("\nESTIMATES (assumed constant elasticity, per product):\n", est.to_string(index=False))
save_table(est, "pricing_scenarios.csv", index=False)

# ---------------- ESTIMATED: Garden cost fix and price fix together (no double counting) ----------------
# Cost fix = Garden pays Harbour's unit cost for each product. Price fix = Garden charges Harbour's price.
# Both are computed from the same per-product baseline, and "both" is one combined calculation,
# not the sum of the two: with lost customers (e < 0), each lost unit is worth more after the cost fix.
g = pb[pb.Branch == "Garden"].set_index("Product")
h_cost = wide["cost"]["Harbour"].loc[g.index]
gp0 = g.units * (g.price * g.net_factor - g.cost)
comb = []
for e in ELASTICITIES:
    q1 = g.units * (harbour_price.loc[g.index] / g.price) ** e
    cost_only = (g.units * (g.price * g.net_factor - h_cost) - gp0).sum()
    price_only = (q1 * (harbour_price.loc[g.index] * g.net_factor - g.cost) - gp0).sum()
    both = (q1 * (harbour_price.loc[g.index] * g.net_factor - h_cost) - gp0).sum()
    comb.append({"elasticity": e, "cost_only_6mo_usd": round(cost_only), "price_only_6mo_usd": round(price_only),
                 "both_6mo_usd": round(both), "sum_of_separate_6mo_usd": round(cost_only + price_only),
                 "overlap_usd": round(cost_only + price_only - both),
                 "both_per_year_usd": round(both * 365 / 181)})
comb = pd.DataFrame(comb)
print("\nESTIMATES, Garden cost + price combined:\n", comb.to_string(index=False))
save_table(comb, "garden_cost_price_combined.csv", index=False)
