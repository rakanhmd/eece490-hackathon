"""Finding 1: Garden's gross margin gap and where it comes from (unit cost vs price)."""
import pandas as pd

from load import GP, REV, load_clean, save_table

d = load_clean()

# 1. margin by branch
b = d.groupby("Branch")[[REV, GP]].sum()
b["gross_margin"] = b[GP] / b[REV]
b = b.sort_values("gross_margin", ascending=False).round(4)
print("\nGross margin by branch:\n", b)
save_table(b, "margin_by_branch.csv")

# 2. margin by branch and month (is the gap stable?)
m = d.groupby(["month", "Branch"])[[REV, GP]].sum()
m = (m[GP] / m[REV]).unstack().round(4)
print("\nGross margin by month:\n", m)
save_table(m, "margin_by_month.csv")
rm = d.groupby(["month", "Branch"])[REV].sum().unstack().round(2)
print("\nRevenue by month:\n", rm)
print("June / January revenue:\n", (rm.loc[6] / rm.loc[1]).round(3))
save_table(rm, "revenue_by_month.csv")
um = d.groupby(["month", "Branch"])["Quantity"].sum().unstack()
print("\nUnits by month:\n", um)
save_table(um, "units_by_month.csv")
print(f"\nTotal revenue Jan-Jun: ${b[REV].sum():,.2f}")

# 3. unit cost and price per product per branch (median, robust to rounding)
p = d.groupby(["Product", "Branch"])[["Unit Cost (USD)", "Unit Price (USD)"]].median().unstack()
out = pd.DataFrame({
    "cost_garden": p[("Unit Cost (USD)", "Garden")],
    "cost_harbour": p[("Unit Cost (USD)", "Harbour")],
    "cost_uptown": p[("Unit Cost (USD)", "Uptown")],
    "price_garden": p[("Unit Price (USD)", "Garden")],
    "price_harbour": p[("Unit Price (USD)", "Harbour")],
    "price_uptown": p[("Unit Price (USD)", "Uptown")],
})
out["cost_ratio_garden_vs_harbour"] = out.cost_garden / out.cost_harbour
out["cost_ratio_uptown_vs_harbour"] = out.cost_uptown / out.cost_harbour
out["price_ratio_garden_vs_harbour"] = out.price_garden / out.price_harbour
out["price_ratio_uptown_vs_harbour"] = out.price_uptown / out.price_harbour
out = out.round(4)
save_table(out, "unit_cost_ratio_by_product.csv")
print(f"\nProducts compared: {len(out)}")
for c in [c for c in out.columns if "ratio" in c]:
    print(f"{c}: min {out[c].min():.3f}  median {out[c].median():.3f}  max {out[c].max():.3f}")

# 4. estimated value (an ESTIMATE): Garden pays Harbour's unit cost per product, same prices and quantities
gd = d[d.Branch == "Garden"]
saving = (gd["Quantity"] * (gd["Unit Cost (USD)"] - gd["Product"].map(out.cost_harbour))).sum()
print(f"ESTIMATE: Garden at Harbour unit costs -> +${saving:,.0f} gross profit over 6 months")

# 5. the removed duplicates: how much revenue they carry (for the assumptions table)
import pandas as pd
from load import DATA
raw = pd.read_csv(DATA)
dups = raw[raw.duplicated()]
dq = pd.DataFrame({"duplicate_rows": [len(dups)], "duplicate_revenue_usd": [round(dups[REV].sum(), 2)],
                   "share_of_revenue": [round(dups[REV].sum() / raw[REV].sum(), 4)]})
print("\nRemoved duplicates:\n", dq.to_string(index=False))
save_table(dq, "duplicates_summary.csv", index=False)
