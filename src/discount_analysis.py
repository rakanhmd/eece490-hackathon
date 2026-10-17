"""Finding 3: does the 10% discount buy anything, or does it only give margin away?

Questions:
  1. How is the 10% discount applied: whole transactions or single lines? Which branches, hours, products?
  2. Do discounted transactions buy more (items, quantity, spend before discount) than full-price
     transactions in the same branch, weekday and hour? (matched comparison, not a raw average)
  3. Is it tied to known customers (a loyalty scheme) or anonymous buyers?
  4. What did it cost in USD?
Caveat: this is observational. Bigger baskets with a discount would not prove the discount caused them,
and equal baskets do not prove that removing it loses no customers.
"""
import numpy as np
import pandas as pd

from common import SEED
from load import GP, REV, load_clean, save_table

rng = np.random.default_rng(SEED)
d = load_clean()
d10 = d[d["Discount Rate"] != 0.15]          # the 15% promo is analysed separately
d10 = d10[~d10["Transaction ID"].isin(d.loc[d["Discount Rate"] == 0.15, "Transaction ID"])]
print(f"transactions left out because they contain a 15% line: "
      f"{d.loc[d['Discount Rate'] == 0.15, 'Transaction ID'].nunique():,}")

# 1. line-level or transaction-level?
t = d10.groupby("Transaction ID").agg(
    branch=("Branch", "first"), weekday=("weekday", "first"), hour=("hour", "first"),
    lines=("Product", "size"), qty=("Quantity", "sum"),
    list_rev=("list_revenue", "sum"), rev=(REV, "sum"), gp=(GP, "sum"),
    n_disc=("Discount Rate", lambda s: (s == 0.10).sum()),
    known=("Customer ID", lambda s: s.notna().any()),
    dinein=("Order Type", lambda s: (s == "Dine-in").any()))
t["any_disc"] = t.n_disc > 0
mixed = ((t.n_disc > 0) & (t.n_disc < t.lines)).sum()
print(f"transactions: {len(t):,}; with a 10% line: {t.any_disc.sum():,} ({t.any_disc.mean():.1%}); "
      f"multi-line transactions where only some lines are discounted: {mixed:,} "
      f"of {(t.any_disc & (t.lines > 1)).sum():,}")

# 2. matched comparison within branch x weekday x hour cells
t["cell"] = t.branch + "_" + t.weekday.astype(str) + "_" + t.hour.astype(str)
metrics = ["lines", "qty", "list_rev", "gp"]


def matched_diff(tt):
    """Mean over discounted transactions of (own value - mean of full-price txs in same cell)."""
    full = tt[~tt.any_disc].groupby("cell")[metrics].mean()
    disc = tt[tt.any_disc]
    disc = disc[disc.cell.isin(full.index)]
    return (disc[metrics].values - full.loc[disc.cell].values).mean(axis=0), len(disc)


diff, n = matched_diff(t)
boots = []
cells = t.cell.unique()
by_cell = {c: g for c, g in t.groupby("cell")}
for _ in range(300):  # resample transactions within cells (stratified bootstrap)
    s = t.groupby("cell", group_keys=False).sample(frac=1, replace=True, random_state=int(rng.integers(1e9)))
    boots.append(matched_diff(s)[0])
lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
base = t[~t.any_disc][metrics].mean()
res = pd.DataFrame({"metric": metrics, "full_price_mean": base.values,
                    "matched_diff_discounted_minus_full": diff, "ci_low": lo, "ci_high": hi}).round(3)
print(f"\nMatched comparison ({n:,} discounted transactions):\n", res.to_string(index=False))
save_table(res, "discount_effect.csv", index=False)

# 2b. NULL MODEL. The discount is applied per line, so a transaction with more lines has more chances to
# contain a discounted line. Shuffle the 10% flag randomly across lines within each branch x weekday x hour
# cell and redo the comparison. If the observed gap matches this null, the "bigger basket" is a counting effect.
d10 = d10.assign(cell=d10.Branch + "_" + d10.weekday.astype(str) + "_" + d10.hour.astype(str),
                 is10=(d10["Discount Rate"] == 0.10))
tid = d10["Transaction ID"].values
null = []
for _ in range(200):
    flag = d10.groupby("cell")["is10"].transform(lambda s: rng.permutation(s.values))
    any_d = pd.Series(flag.values, index=tid).groupby(level=0).any()
    tt = t.assign(any_disc=any_d.reindex(t.index).values)
    null.append(matched_diff(tt)[0])
null = np.array(null)
res["null_mean_if_random"] = null.mean(axis=0).round(3)
res["null_p95"] = np.percentile(null, 95, axis=0).round(3)
res["excess_over_null"] = (res.matched_diff_discounted_minus_full - res.null_mean_if_random).round(3)
print("\nObserved vs random-assignment null:\n", res.to_string(index=False))
save_table(res, "discount_effect.csv", index=False)

# 2c. line-level: same product, same branch -> does a discounted line have a bigger quantity?
g = d10.groupby(["Product", "Branch", "is10"])["Quantity"].mean().unstack()
w = d10[d10.is10].groupby(["Product", "Branch"]).size()
line_gap = ((g[True] - g[False]) * w).sum() / w.sum()
print(f"Line-level: discounted minus full-price quantity, same product and branch (weighted) = {line_gap:+.4f} units")
save_table(pd.DataFrame({"line_qty_gap_same_product_branch": [round(line_gap, 4)]}), "discount_line_level.csv", index=False)

# 3. who gets it, and where/when
who = pd.DataFrame({
    "share_discounted": [t.any_disc.mean()],
    "known_customer_rate_discounted": [t[t.any_disc].known.mean()],
    "known_customer_rate_full": [t[~t.any_disc].known.mean()],
    "dinein_rate_discounted": [t[t.any_disc].dinein.mean()],
    "dinein_rate_full": [t[~t.any_disc].dinein.mean()],
}).round(3)
print("\n", who.T)
save_table(who, "discount_who.csv", index=False)
spread = pd.concat({
    "by_branch": d10.groupby("Branch")["Discount Rate"].apply(lambda s: (s == 0.10).mean()),
    "by_month": d10.groupby("month")["Discount Rate"].apply(lambda s: (s == 0.10).mean()),
    "by_weekday": d10.groupby("weekday")["Discount Rate"].apply(lambda s: (s == 0.10).mean()),
    "by_category": d10.groupby("Category")["Discount Rate"].apply(lambda s: (s == 0.10).mean()),
}).round(4).rename("share_lines_10pct")
save_table(spread.to_frame(), "discount_spread.csv")
print("\nShare of lines with 10% discount:\n", spread.groupby(level=0).agg(["min", "max"]))

# repeat use by known customers: is it concentrated on a few IDs (loyalty / staff) or spread out?
k = d10[d10["Customer ID"].notna()]
per_c = k.groupby("Customer ID")["Discount Rate"].apply(lambda s: (s == 0.10).mean())
print(f"\nKnown customers: {len(per_c):,}; share with any 10% line: {(per_c > 0).mean():.1%}; "
      f"top 5% of customers' share of discounted lines: "
      f"{k[k['Discount Rate']==0.10]['Customer ID'].value_counts().pipe(lambda v: v.head(int(len(per_c)*0.05)).sum()/v.sum()):.1%}")

# 4. cost
# cost over ALL 10% lines, including the few inside transactions that also had a 15% line
cost = d.loc[d["Discount Rate"] == 0.10, "discount_usd"].sum()
days = (d.date.max() - d.date.min()).days + 1
print(f"\nMEASURED: 10% discounts given Jan-Jun = ${cost:,.0f} over {days} days")
print(f"ESTIMATE: per year (six months x 2) = ${cost * 2:,.0f}")
save_table(pd.DataFrame({"discount_usd_jan_jun": [round(cost, 2)], "days": [days],
                         "per_year_estimate_usd_x2": [round(cost * 2, 0)]}),
           "discount_cost.csv", index=False)
