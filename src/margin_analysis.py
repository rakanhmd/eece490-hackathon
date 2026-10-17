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

# 4. estimated value: Garden at Harbour's / Uptown's margin, same revenue (an ESTIMATE)
g_rev = b.loc["Garden", REV]
for ref in ["Harbour", "Uptown"]:
    gain = g_rev * (b.loc[ref, "gross_margin"] - b.loc["Garden", "gross_margin"])
    print(f"ESTIMATE: Garden at {ref} margin -> +${gain:,.0f} gross profit over 6 months")
