"""Why is Garden's recorded unit cost about 1.43x Harbour's?  Three tests of candidate explanations.

 1. Shape of the gap: is the ratio the same for every product, category and month, and for cheap vs expensive items?
    A fixed fee per unit/order would raise cheap items' ratio MORE; a percentage overhead or supplier markup is uniform.
 2. Fuel/transport: does Garden's cost relative to the other branches move with weekly Brent crude?
 3. Location: does Garden look like a different neighbourhood (basket, hours, categories, customers)?
Needs data/external/DCOILBRENTEU.csv (committed; downloaded 2026-10-17 with
  curl -o data/external/DCOILBRENTEU.csv "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU").
All tests are on observed data; none can identify the cause, only say which stories the data rules out.
"""
import os

import numpy as np
import pandas as pd
from scipy import stats

from common import ROOT, SEED
from load import GP, REV, load_clean, save_table

rng = np.random.default_rng(SEED)
d = load_clean()
UC, UP = "Unit Cost (USD)", "Unit Price (USD)"
BRENT = os.path.join(ROOT, "data", "external", "DCOILBRENTEU.csv")

# ================= 1. shape of the gap =================
# unit cost is one constant per product x branch for the whole period (checked: max 1 distinct value)
assert d.groupby(["Product", "Branch"])[UC].nunique().max() == 1
cost = d.groupby(["Product", "Branch"])[UC].first().unstack()
cat = d.drop_duplicates("Product").set_index("Product")["Category"]
prod = pd.DataFrame({"category": cat, "cost_harbour": cost["Harbour"], "cost_garden": cost["Garden"],
                     "cost_uptown": cost["Uptown"]})
prod["ratio_garden"] = prod.cost_garden / prod.cost_harbour
prod["ratio_uptown"] = prod.cost_uptown / prod.cost_harbour
prod["diff_garden_usd"] = prod.cost_garden - prod.cost_harbour
print("\n[1] MEASURED: cost ratio vs Harbour across the 45 products")
spread = pd.DataFrame({c: prod[c].agg(["min", "median", "max", "std"]) for c in ["ratio_garden", "ratio_uptown"]}).T
print(spread.round(4).to_string())
save_table(prod.round(4), "garden_cause_product_ratios.csv")
save_table(spread.round(4), "garden_cause_ratio_spread.csv")
by_cat = prod.groupby("category")[["ratio_garden", "ratio_uptown"]].agg(["min", "median", "max"]).round(4)
print("\nby category:\n", by_cat.to_string())
save_table(by_cat, "garden_cause_ratio_by_category.csv")

# rounding: costs are in cents, so a cheap item's ratio can move by up to 0.005/cost just from rounding
prod["rounding_halfwidth"] = prod.ratio_garden * (0.005 / prod.cost_harbour + 0.005 / prod.cost_garden)
inside = ((prod.ratio_garden - prod.ratio_garden.median()).abs() <= prod.rounding_halfwidth).sum()
print(f"cost rounding alone can move a ratio by up to +/-{prod.rounding_halfwidth.max():.3f} (cheapest item, ${prod.cost_harbour.min():.2f}); "
      f"{inside} of {len(prod)} products lie within their own rounding band of the median ratio {prod.ratio_garden.median():.4f}")

# by month: costs never change, so the ratio is exactly constant; the *realised* ratio only moves with product mix
m = d.groupby(["month", "Branch"]).apply(lambda g: g.cost.sum() / g.Quantity.sum(), include_groups=False).unstack()
m["garden_over_harbour_avg_cost_per_unit"] = m.Garden / m.Harbour
print("\nby month: same-product ratio is constant (cost never changes); average cost per unit sold (mix-affected):\n",
      m.round(3).to_string())

# fixed fee vs proportional: regress Garden cost on Harbour cost across products.
#   fixed fee per unit  -> intercept > 0, slope near 1
#   proportional markup -> intercept near 0, slope near 1.43
def fit(x, y):
    b, a = np.polyfit(x, y, 1)
    return a, b


x, y = prod.cost_harbour.values, prod.cost_garden.values
a, b = fit(x, y)
boot = np.array([fit(x[i], y[i]) for i in (rng.integers(0, len(x), len(x)) for _ in range(2000))])
ci_a, ci_b = np.percentile(boot[:, 0], [2.5, 97.5]), np.percentile(boot[:, 1], [2.5, 97.5])
rho, p_rho = stats.spearmanr(prod.cost_harbour, prod.ratio_garden)
cheap = prod.cost_harbour <= prod.cost_harbour.median()
res1 = pd.DataFrame([{
    "intercept_usd": a, "intercept_ci_low": ci_a[0], "intercept_ci_high": ci_a[1],
    "slope": b, "slope_ci_low": ci_b[0], "slope_ci_high": ci_b[1],
    "spearman_ratio_vs_harbour_cost": rho, "spearman_p": p_rho,
    "median_ratio_cheap_half": prod.ratio_garden[cheap].median(), "median_ratio_expensive_half": prod.ratio_garden[~cheap].median(),
    "cheapest_ratio": prod.ratio_garden.loc[prod.cost_harbour.idxmin()], "cheapest_item": prod.cost_harbour.idxmin(),
    "most_expensive_ratio": prod.ratio_garden.loc[prod.cost_harbour.idxmax()], "most_expensive_item": prod.cost_harbour.idxmax(),
    "median_abs_diff_usd": prod.diff_garden_usd.median(), "cheap_half_median_diff_usd": prod.diff_garden_usd[cheap].median(),
    "expensive_half_median_diff_usd": prod.diff_garden_usd[~cheap].median()}]).round(4)
save_table(res1, "garden_cause_shape_tests.csv", index=False)
print("\n[1] MEASURED: Garden cost = intercept + slope x Harbour cost (45 products, bootstrap 95% CI)")
print(res1.T.to_string(header=False))
# other ways to see if cost tracks price (a margin-based rule)
prod["price_ratio_garden"] = d.groupby(["Product", "Branch"])[UP].first().unstack()["Garden"] / d.groupby(["Product", "Branch"])[UP].first().unstack()["Harbour"]
prod["cost_to_price_garden"] = d.groupby(["Product", "Branch"]).apply(lambda g: g[UC].iloc[0] / g[UP].iloc[0], include_groups=False).unstack()["Garden"]
prod["cost_to_price_harbour"] = d.groupby(["Product", "Branch"]).apply(lambda g: g[UC].iloc[0] / g[UP].iloc[0], include_groups=False).unstack()["Harbour"]
print(f"cost/price: Harbour median {prod.cost_to_price_harbour.median():.3f}, Garden median {prod.cost_to_price_garden.median():.3f}, "
      f"ratio of the two spans {(prod.cost_to_price_garden / prod.cost_to_price_harbour).min():.3f}-{(prod.cost_to_price_garden / prod.cost_to_price_harbour).max():.3f}")
# does the 1.43 depend on how many units were sold in the line (per-order fee?) -> unit cost is identical in 1- and 2-unit lines
print("distinct Garden unit costs per product (any quantity, any month):",
      int(d[d.Branch == "Garden"].groupby("Product")[UC].nunique().max()))

# ================= 2. fuel prices =================
brent = pd.read_csv(BRENT, parse_dates=["observation_date"]).rename(columns={"observation_date": "date", "DCOILBRENTEU": "brent"})
brent["brent"] = pd.to_numeric(brent.brent, errors="coerce")
brent = brent[(brent.date >= "2026-01-01") & (brent.date <= "2026-06-30")]
brent["week_start"] = brent.date - pd.to_timedelta(brent.date.dt.dayofweek, unit="D")
bw = brent.groupby("week_start").brent.mean()
print(f"\n[2] Brent Jan-Jun 2026: {brent.brent.notna().sum()} daily prices, ${brent.brent.min():.2f}-${brent.brent.max():.2f}, "
      f"{len(bw)} weeks")
save_table(bw.round(3).rename("brent_weekly_mean_usd").to_frame(), "garden_cause_brent_weekly.csv")  # small copy: data/ is gitignored

g = d.assign(HarbourCost=d.Product.map(cost["Harbour"]) * d.Quantity)
wk = g.groupby(["week_start", "Branch"]).agg(units=("Quantity", "sum"), cost=("cost", "sum"), rev=(REV, "sum"),
                                              harbour_cost_same_lines=("HarbourCost", "sum")).unstack()
series = pd.DataFrame({
    # (a) same products, same quantities, priced at Harbour's cost: removes product mix entirely
    "mix_neutral_ratio": wk[("cost", "Garden")] / wk[("harbour_cost_same_lines", "Garden")],
    # (b) naive: Garden's average cost per unit over the other two branches' average (moves with product mix)
    "naive_cost_per_unit_ratio": (wk[("cost", "Garden")] / wk[("units", "Garden")]) /
                                 ((wk[("cost", "Harbour")] + wk[("cost", "Uptown")]) / (wk[("units", "Harbour")] + wk[("units", "Uptown")])),
    # (c) cost of sales as a share of revenue, Garden over others
    "cost_to_revenue_ratio": (wk[("cost", "Garden")] / wk[("rev", "Garden")]) /
                             ((wk[("cost", "Harbour")] + wk[("cost", "Uptown")]) / (wk[("rev", "Harbour")] + wk[("rev", "Uptown")])),
}).join(bw).dropna()
series = series[(series.index >= d.week_start.min() + pd.Timedelta(days=7)) & (series.index < d.date.max() - pd.Timedelta(days=6))]
print(f"weeks used (full weeks only): {len(series)}")


def corr_ci(x, y):
    r, p = stats.pearsonr(x, y)
    zr, se = np.arctanh(r), 1 / np.sqrt(len(x) - 3)
    return r, np.tanh(zr - 1.96 * se), np.tanh(zr + 1.96 * se), p


rows = []
for name in ["mix_neutral_ratio", "naive_cost_per_unit_ratio", "cost_to_revenue_ratio"]:
    s = series[name]
    row = {"weekly_series": name, "mean": s.mean(), "std": s.std(), "min": s.min(), "max": s.max(), "n_weeks": len(s)}
    if s.std() < 1e-9:
        row.update(r_levels=np.nan, r_ci_low=np.nan, r_ci_high=np.nan, p_levels=np.nan, r_diff=np.nan, p_diff=np.nan,
                   ratio_change_over_brent_range=np.nan)
    else:
        r, lo, hi, p = corr_ci(s.values, series.brent.values)
        rd, _, _, pd_ = corr_ci(s.diff().dropna().values, series.brent.diff().dropna().values)
        slope = np.polyfit(series.brent.values, s.values, 1)[0]
        row.update(r_levels=r, r_ci_low=lo, r_ci_high=hi, p_levels=p, r_diff=rd, p_diff=pd_,
                   ratio_change_over_brent_range=slope * (series.brent.max() - series.brent.min()))
    rows.append(row)
fuel = pd.DataFrame(rows).round(4)
save_table(fuel, "garden_cause_fuel_correlation.csv", index=False)
print("[2] MEASURED: weekly Garden/other cost ratio vs weekly Brent (levels, and week-to-week changes to avoid trend artefacts)")
print(fuel.to_string(index=False))
# what size of fuel effect could we even see? Brent range as a share of its mean
print(f"weekly Brent mean ranged ${series.brent.min():.2f}-${series.brent.max():.2f} over the weeks used")
print(f"Brent moved {100 * (bw.max() / bw.min() - 1):.0f}% from weekly low to high over the period; "
      f"Garden's gap is {100 * (cost['Garden'] / cost['Harbour']).median() - 100:.0f}% and does not change at all")

# ================= 3. does Garden look like a different place? =================
d["is_cold"] = d.Category.isin(["Cold Coffee", "Cold Drinks"])
tx = d.groupby("Transaction ID").agg(branch=("Branch", "first"), hour=("hour", "first"), lines=("Product", "size"),
                                     units=("Quantity", "sum"), list_rev=("list_revenue", "sum"),
                                     dinein=("Order Type", lambda s: (s == "Dine-in").any()),
                                     known=("Customer ID", lambda s: s.notna().any()))
prof = pd.DataFrame({
    "transactions": tx.groupby("branch").size(),
    "lines_per_tx": tx.groupby("branch").lines.mean(),
    "units_per_tx": tx.groupby("branch").units.mean(),
    "list_revenue_per_tx": tx.groupby("branch").list_rev.mean(),
    "dine_in_share": tx.groupby("branch").dinein.mean(),
    "known_customer_share": tx.groupby("branch").known.mean(),
    "cold_drink_share_of_units": d.groupby("Branch").apply(lambda g: g.loc[g.is_cold, "Quantity"].sum() / g.Quantity.sum(), include_groups=False),
    "food_share_of_units": d.groupby("Branch").apply(lambda g: g.loc[~g.Category.isin(["Hot Coffee", "Cold Coffee", "Cold Drinks", "Matcha & Tea"]), "Quantity"].sum() / g.Quantity.sum(), include_groups=False),
    "median_hour": tx.groupby("branch").hour.median(),
})
cust = d.dropna(subset=["Customer ID"])
cb = cust.groupby("Customer ID").Branch.agg(lambda s: set(s))
for br in ["Garden", "Harbour", "Uptown"]:
    mine = cb[cb.apply(lambda s: br in s)]
    prof.loc[br, "known_customers"] = len(mine)
    prof.loc[br, "share_also_buying_elsewhere"] = (mine.apply(len) > 1).mean()
prof = prof.round(4)
save_table(prof, "garden_cause_branch_profile.csv")
print("\n[3] MEASURED: branch profiles\n", prof.T.to_string())

# pairwise customer overlap (Jaccard) -- if Garden served its own neighbourhood, its overlap would be lower than the others'
ov = {}
sets = {br: set(cust[cust.Branch == br]["Customer ID"]) for br in ["Garden", "Harbour", "Uptown"]}
for a_, b_ in [("Garden", "Harbour"), ("Garden", "Uptown"), ("Harbour", "Uptown")]:
    ov[f"{a_}-{b_}"] = len(sets[a_] & sets[b_]) / len(sets[a_] | sets[b_])
print("customer overlap (Jaccard):", {k: round(v, 3) for k, v in ov.items()})
save_table(pd.Series(ov, name="jaccard").round(4).to_frame(), "garden_cause_customer_overlap.csv")


def jsd(p, q):
    p, q = p / p.sum(), q / q.sum()
    m_ = (p + q) / 2
    with np.errstate(divide="ignore", invalid="ignore"):
        f = lambda a_, b_: np.sum(np.where(a_ > 0, a_ * np.log2(a_ / b_), 0))
        return np.sqrt((f(p, m_) + f(q, m_)) / 2)


def dist_test(labels, values, n_perm=500):
    """Jensen-Shannon distance between a branch's distribution of `values` and all other branches pooled.
    p-value: shuffle branch labels across transactions (keeps branch sizes), n_perm times."""
    out = {}
    levels = sorted(set(values))
    codes = pd.Categorical(values, categories=levels).codes
    for br in ["Garden", "Harbour", "Uptown"]:
        def stat(lab):
            a_ = np.bincount(codes[lab == br], minlength=len(levels)).astype(float)
            b_ = np.bincount(codes[lab != br], minlength=len(levels)).astype(float)
            return jsd(a_, b_)
        obs = stat(labels)
        null = np.array([stat(rng.permutation(labels)) for _ in range(n_perm)])
        out[br] = (obs, (1 + (null >= obs).sum()) / (n_perm + 1))
    return out


# hour profile: transactions by hour; category mix: units by category
hour_t = dist_test(tx.branch.values, tx.hour.values)
catlines = d.loc[d.index.repeat(d.Quantity)]
cat_t = dist_test(catlines.Branch.values, catlines.Category.values)
# basket size (units per transaction) as a distribution
bk_t = dist_test(tx.branch.values, tx.units.clip(upper=5).values)
dt_rows = []
for name, r in [("hour of day (transactions)", hour_t), ("category mix (units)", cat_t), ("units per transaction", bk_t)]:
    for br, (obs, p) in r.items():
        dt_rows.append({"profile": name, "branch_vs_others": br, "js_distance": obs, "permutation_p": p})
dtest = pd.DataFrame(dt_rows).round(4)
save_table(dtest, "garden_cause_profile_tests.csv", index=False)
print("\n[3] MEASURED: how different is each branch from the other two pooled? (Jensen-Shannon distance; p from 500 label shuffles)")
print(dtest.to_string(index=False))

# is Garden different from Harbour AND Uptown in the same way they differ from each other? (3 pairwise distances)
hr = tx.groupby(["branch", "hour"]).size().unstack(0)
print("pairwise hour-profile distances:",
      {f"{a_}-{b_}": round(jsd(hr[a_].values.astype(float), hr[b_].values.astype(float)), 4)
       for a_, b_ in [("Garden", "Harbour"), ("Garden", "Uptown"), ("Harbour", "Uptown")]})
