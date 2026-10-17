"""Menu profit table: every product's units, revenue, gross profit, margin, share of profit and role in the basket.

MEASURED (from the transaction file, after removing exact duplicates): per-product units, revenue, gross profit, margin %,
profit share, and its basket role (food: bought with a drink more or less than the average food item; drink: pulls a food
item along more or less than the average drink). Garden is shown separately because its unit costs are 1.43x Harbour's
(Finding 1), so its margins are not comparable with the other branches'.
FLAGS (rules written below, applied to the chain table and again to Garden's own table):
  low-profit low-volume : bottom quartile of units AND bottom quartile of gross profit (both within the branch's own menu)
  low-margin basket driver: top quartile of share of transactions containing the item, AND margin below the menu's median
ESTIMATES (labelled; every assumption is stated in the table or in MENU.md): a price rise on the flagged basket drivers, and what
dropping the flagged items could cost. Prices never change in the data, so price sensitivity is assumed, not measured.
Associations only: nothing here shows what happens if a product is repriced or removed.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import SEED, save_fig
from load import GP, REV, load_clean, save_table

d = load_clean()
BRANCHES = ["Garden", "Harbour", "Uptown"]
DRINKS = ["Hot Coffee", "Cold Coffee", "Cold Drinks", "Matcha & Tea"]
d["is_drink"] = d.Category.isin(DRINKS)
N_TX = d["Transaction ID"].nunique()
TOTAL_GP, TOTAL_REV = d[GP].sum(), d[REV].sum()


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return c - h, c + h


# ---------- basket presence ----------
P = pd.crosstab(d["Transaction ID"], d.Product).clip(upper=1).astype(bool)
cat_of = d.drop_duplicates("Product").set_index("Product").Category
drink_items = [p for p in P.columns if cat_of[p] in DRINKS]
food_items = [p for p in P.columns if cat_of[p] not in DRINKS]
has_drink, has_food = P[drink_items].any(axis=1), P[food_items].any(axis=1)
attach_avg = has_food[has_drink].mean()                       # average share of drink transactions that carry food
with_drink_avg = has_drink[has_food].mean()                   # average share of food transactions that carry a drink
print(f"transactions {N_TX:,}; drink transactions that carry food: {attach_avg:.1%}; food transactions that carry a drink: {with_drink_avg:.1%}")


def build(frame, label):
    g = frame.groupby(["Category", "Product"]).agg(units=("Quantity", "sum"), revenue=(REV, "sum"), gross_profit=(GP, "sum"),
                                                   list_revenue=("list_revenue", "sum"), cost=("cost", "sum")).reset_index()
    g["margin_pct"] = 100 * g.gross_profit / g.revenue
    g["gp_per_unit"] = g.gross_profit / g.units
    g["avg_net_price"] = g.revenue / g.units
    g["avg_unit_cost"] = g.cost / g.units
    g["units_share_pct"] = 100 * g.units / g.units.sum()
    g["revenue_share_pct"] = 100 * g.revenue / g.revenue.sum()
    g["profit_share_pct"] = 100 * g.gross_profit / g.gross_profit.sum()
    tx_ids = frame["Transaction ID"].unique()
    sub = P.loc[P.index.isin(tx_ids)]
    g["basket_share_pct"] = g.Product.map(100 * sub.mean())
    g["branch"] = label
    return g


chain = build(d, "All")
# ---------- basket role (chain-wide) ----------
role_rows = []
for p in P.columns:
    inb = P[p]
    n = int(inb.sum())
    if p in drink_items:
        k = int(has_food[inb].sum())
        lo, hi = wilson(k, n)
        role = "pulls food (attach above the drink average)" if lo > attach_avg else \
               "tends to be bought alone (attach below the drink average)" if hi < attach_avg else "neutral"
        role_rows.append({"Product": p, "transactions": n, "role_rate": k / n, "role_ci_low": lo, "role_ci_high": hi,
                          "role_basis": "share of its transactions that also carry food", "average_for_group": attach_avg, "attach_role": role})
    else:
        k = int(has_drink[inb].sum())
        lo, hi = wilson(k, n)
        role = "add-on (usually with a drink)" if lo > with_drink_avg else \
               "stand-alone (usually without a drink)" if hi < with_drink_avg else "neutral"
        role_rows.append({"Product": p, "transactions": n, "role_rate": k / n, "role_ci_low": lo, "role_ci_high": hi,
                          "role_basis": "share of its transactions that also carry a drink", "average_for_group": with_drink_avg, "attach_role": role})
roles = pd.DataFrame(role_rows)
chain = chain.merge(roles, on="Product")


# ---------- flags ----------
def flag(tab):
    tab = tab.copy()
    q_u, q_g = tab.units.quantile(0.25), tab.gross_profit.quantile(0.25)
    q_b, med_m = tab.basket_share_pct.quantile(0.75), tab.margin_pct.median()
    tab["low_profit_low_volume"] = (tab.units <= q_u) & (tab.gross_profit <= q_g)
    tab["low_margin_basket_driver"] = (tab.basket_share_pct >= q_b) & (tab.margin_pct < med_m)
    tab.attrs.update(q_units=q_u, q_gp=q_g, q_basket=q_b, median_margin=med_m)
    return tab


chain = flag(chain).sort_values("gross_profit", ascending=False).reset_index(drop=True)
chain["cum_profit_share_pct"] = chain.profit_share_pct.cumsum()
cols = ["Category", "Product", "units", "revenue", "gross_profit", "margin_pct", "gp_per_unit", "units_share_pct", "profit_share_pct",
        "cum_profit_share_pct", "basket_share_pct", "attach_role", "role_rate", "low_profit_low_volume", "low_margin_basket_driver"]
save_table(chain[cols].round(3), "menu_products.csv", index=False)
print(f"\nMEASURED: {len(chain)} products; total revenue ${TOTAL_REV:,.0f}, gross profit ${TOTAL_GP:,.0f}, margin {100 * TOTAL_GP / TOTAL_REV:.1f}%")
print(chain[["Product", "Category", "units", "revenue", "gross_profit", "margin_pct", "profit_share_pct", "basket_share_pct", "attach_role"]]
      .round(1).to_string(index=False))
top = lambda n: chain.profit_share_pct.head(n).sum()
print(f"\nprofit concentration: top 5 products {top(5):.1f}% of gross profit, top 10 {top(10):.1f}%, top 20 {top(20):.1f}%; "
      f"bottom 10 products {chain.profit_share_pct.tail(10).sum():.1f}%")
cat = chain.groupby("Category").agg(products=("Product", "size"), units=("units", "sum"), revenue=("revenue", "sum"),
                                    gross_profit=("gross_profit", "sum"))
cat["margin_pct"] = 100 * cat.gross_profit / cat.revenue
cat["profit_share_pct"] = 100 * cat.gross_profit / cat.gross_profit.sum()
cat["gp_per_unit"] = cat.gross_profit / cat.units
save_table(cat.round(3).sort_values("gross_profit", ascending=False), "menu_category_summary.csv")
print("\nMEASURED: by category\n", cat.round(2).sort_values("gross_profit", ascending=False).to_string())

fl = chain[chain.low_profit_low_volume | chain.low_margin_basket_driver]
print(f"\nFLAG RULES (chain): low-profit low-volume = units <= {chain.attrs['q_units']:.0f} and gross profit <= ${chain.attrs['q_gp']:,.0f} (bottom quartiles); "
      f"low-margin basket driver = in >= {chain.attrs['q_basket']:.1f}% of transactions and margin < {chain.attrs['median_margin']:.1f}% (menu median)")
print("low-profit low-volume items:\n", chain[chain.low_profit_low_volume][["Product", "Category", "units", "gross_profit", "margin_pct", "profit_share_pct"]].round(1).to_string(index=False))
print("low-margin basket drivers:\n", chain[chain.low_margin_basket_driver][["Product", "Category", "basket_share_pct", "margin_pct", "gross_profit", "attach_role"]].round(1).to_string(index=False))
save_table(fl[["Product", "Category", "low_profit_low_volume", "low_margin_basket_driver", "units", "gross_profit", "margin_pct", "basket_share_pct"]].round(3),
           "menu_flags_chain.csv", index=False)

# ---------- branches; Garden separately ----------
by_b = {b: flag(build(d[d.Branch == b], b)) for b in BRANCHES}
allb = pd.concat(by_b.values(), ignore_index=True)
allb = allb.merge(roles[["Product", "attach_role"]], on="Product")
save_table(allb[["branch", "Category", "Product", "units", "revenue", "gross_profit", "margin_pct", "gp_per_unit", "profit_share_pct", "basket_share_pct",
                 "low_profit_low_volume", "low_margin_basket_driver"]].round(3), "menu_products_by_branch.csv", index=False)
g_ = by_b["Garden"].sort_values("margin_pct")
h_ = by_b["Harbour"].set_index("Product")
u_ = by_b["Uptown"].set_index("Product")
gt = g_.set_index("Product")
cmp_ = pd.DataFrame({"Category": gt.Category, "garden_margin_pct": gt.margin_pct, "harbour_margin_pct": h_.margin_pct, "uptown_margin_pct": u_.margin_pct,
                     "garden_gp_per_unit": gt.gp_per_unit, "harbour_gp_per_unit": h_.gp_per_unit, "garden_units": gt.units,
                     "garden_profit_share_pct": gt.profit_share_pct})
cmp_["margin_gap_vs_harbour_pts"] = cmp_.garden_margin_pct - cmp_.harbour_margin_pct
save_table(cmp_.round(3).sort_values("garden_margin_pct"), "menu_garden_vs_others.csv")
print("\nGARDEN: gross margin by branch")
for b in BRANCHES:
    t_ = by_b[b]
    print(f"  {b}: margin {100 * t_.gross_profit.sum() / t_.revenue.sum():.1f}%; products with margin below 40%: {(t_.margin_pct < 40).sum()}, below 50%: {(t_.margin_pct < 50).sum()}; "
          f"lowest margin {t_.margin_pct.min():.1f}% ({t_.loc[t_.margin_pct.idxmin(), 'Product']}), highest {t_.margin_pct.max():.1f}% ({t_.loc[t_.margin_pct.idxmax(), 'Product']})")
print("Garden lowest-margin items:\n", cmp_.sort_values("garden_margin_pct").head(8)[["Category", "garden_margin_pct", "harbour_margin_pct", "garden_units", "garden_profit_share_pct"]].round(1).to_string())
gc = by_b["Garden"]
print("Garden flags (own quartiles: units <= %.0f and GP <= $%.0f; basket >= %.1f%% and margin < %.1f%%):" %
      (gc.attrs["q_units"], gc.attrs["q_gp"], gc.attrs["q_basket"], gc.attrs["median_margin"]))
print(" low-profit low-volume:", gc[gc.low_profit_low_volume].Product.tolist())
print(" low-margin basket drivers:", gc[gc.low_margin_basket_driver].Product.tolist())
print("chain flags that are also flagged at Garden (low-profit low-volume):", sorted(set(chain[chain.low_profit_low_volume].Product) & set(gc[gc.low_profit_low_volume].Product)))
print("rank correlation of product margin, Garden vs Harbour:", round(cmp_[["garden_margin_pct", "harbour_margin_pct"]].corr(method="spearman").iloc[0, 1], 3))

# Garden's gross profit if each item had Harbour's unit cost (ESTIMATE: assumes Garden could buy at Harbour's costs; README assumption)
hc = d[d.Branch == "Harbour"].groupby("Product")["Unit Cost (USD)"].first()
gd = d[d.Branch == "Garden"].copy()
gd["gain_if_harbour_cost"] = gd.Quantity * (gd["Unit Cost (USD)"] - gd.Product.map(hc))
gain = gd.groupby(["Category", "Product"]).gain_if_harbour_cost.sum().reset_index().sort_values("gain_if_harbour_cost", ascending=False)
gain["share_of_total_gain_pct"] = 100 * gain.gain_if_harbour_cost / gain.gain_if_harbour_cost.sum()
save_table(gain.round(2), "menu_garden_cost_gap_by_product.csv", index=False)
print(f"\nESTIMATE (assumes Garden could buy at Harbour's unit costs): gross profit gain ${gain.gain_if_harbour_cost.sum():,.0f} over six months; "
      f"top 5 products give {gain.share_of_total_gain_pct.head(5).sum():.1f}% of it:\n", gain.head(5).round(0).to_string(index=False))

# ---------- ESTIMATES: price rise on flagged basket drivers ----------
drivers = chain[chain.low_margin_basket_driver].Product.tolist()
RISE = 0.05                                                  # assumption: +5% on the flagged items only
rows = []
sub = d[d.Product.isin(drivers)]
unit_net = sub.groupby("Product").apply(lambda g: pd.Series({"units": g.Quantity.sum(), "revenue": g[REV].sum(), "cost": g.cost.sum()}), include_groups=False)
for e in [0.0, -1.0, -2.0]:
    new_units = unit_net.units * (1 + RISE) ** e
    new_gp = new_units * ((unit_net.revenue / unit_net.units) * (1 + RISE) - unit_net.cost / unit_net.units)
    old_gp = unit_net.revenue - unit_net.cost
    rows.append({"items": ", ".join(drivers), "price_rise_pct": 100 * RISE, "elasticity_assumed": e, "units_change_pct": 100 * ((1 + RISE) ** e - 1),
                 "gp_change_6mo_usd": (new_gp - old_gp).sum(), "gp_change_per_year_usd_x2": 2 * (new_gp - old_gp).sum(),
                 "ignores": "customers who skip the basket or the drink-and-food pairing; no price variation exists in the data to measure elasticity"})
ps = pd.DataFrame(rows).round(1)
save_table(ps, "menu_price_scenarios.csv", index=False)
print(f"\nESTIMATE: +{100 * RISE:.0f}% on the {len(drivers)} low-margin basket drivers ({', '.join(drivers)}), gross profit change over six months:")
print(ps[["elasticity_assumed", "units_change_pct", "gp_change_6mo_usd", "gp_change_per_year_usd_x2"]].to_string(index=False))

# ---------- ESTIMATES: dropping the low-profit low-volume items ----------
lp = chain[chain.low_profit_low_volume]
rows = []
for s in [0.0, 0.5, 0.8]:
    rows.append({"substitution_share": s, "items": len(lp), "gross_profit_of_items_6mo_usd": lp.gross_profit.sum(),
                 "share_of_total_gross_profit_pct": lp.profit_share_pct.sum(),
                 "gp_lost_6mo_usd": lp.gross_profit.sum() * (1 - s),
                 "assumption": f"{int(100 * s)}% of the buyers choose another item that earns the same gross profit per unit"})
ds = pd.DataFrame(rows).round(1)
save_table(ds, "menu_drop_scenarios.csv", index=False)
print(f"\nESTIMATE: removing the {len(lp)} low-profit low-volume items puts ${lp.gross_profit.sum():,.0f} of gross profit ({lp.profit_share_pct.sum():.1f}% of the total) at stake over six months")
print(ds.to_string(index=False))

# ---------- figures ----------
colors = dict(zip(sorted(chain.Category.unique()), plt.cm.tab10.colors))
fig, ax = plt.subplots(figsize=(9.5, 6))
for c, g in chain.groupby("Category"):
    ax.scatter(g.units, g.margin_pct, s=g.gross_profit / 25, color=colors[c], alpha=0.75, label=c, edgecolor="white")
for _, r in chain[chain.low_profit_low_volume | chain.low_margin_basket_driver].iterrows():
    ax.annotate(r.Product, (r.units, r.margin_pct), fontsize=7, xytext=(4, 3), textcoords="offset points")
ax.axhline(chain.attrs["median_margin"], color="grey", ls=":", lw=1)
ax.set_xscale("log")
ax.set_title("Menu: units sold vs gross margin (bubble = gross profit; labelled = flagged)")
ax.set_xlabel("Units sold, Jan-Jun (log scale)")
ax.set_ylabel("Gross margin (%)")
ax.legend(fontsize=7, ncol=2)
save_fig(fig, "menu_units_vs_margin.png")
fig, ax = plt.subplots(figsize=(8, 9))
c2 = cmp_.sort_values("garden_margin_pct")
y = np.arange(len(c2))
ax.hlines(y, c2.garden_margin_pct, c2.harbour_margin_pct, color="#bdc3c7")
ax.scatter(c2.garden_margin_pct, y, color="#c0392b", label="Garden", zorder=3)
ax.scatter(c2.harbour_margin_pct, y, color="#2c3e50", label="Harbour", zorder=3)
ax.scatter(c2.uptown_margin_pct, y, color="#7f8c8d", marker="x", label="Uptown", zorder=3)
ax.set_yticks(y, c2.index, fontsize=7)
ax.set_title("Gross margin by product: Garden vs Harbour and Uptown")
ax.set_xlabel("Gross margin (%)")
ax.set_ylabel("Product")
ax.legend()
save_fig(fig, "menu_garden_margins.png")
print("\nsaved figures/menu_units_vs_margin.png, menu_garden_margins.png")
