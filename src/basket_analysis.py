"""Finding 8: basket and cross-sell analysis.

Questions:
  1. How often does a transaction that has a drink also carry a food item (the "attach rate"), and does it
     differ by branch, hour or drink category? Drink-only transactions are the cross-sell opportunity.
  2. Which drink + food pairs are sold less often than the popularity of each item predicts?
  3. How much gross profit do the food items involved earn?
  4. What is a realistic gross-profit gain from a higher attach rate? (ESTIMATE, with stated assumptions.)
Everything printed or saved under "MEASURED" comes straight from the data. "ESTIMATE" rows rest on assumptions.
This is observational data: differences in attach rate are associations, not proof that a prompt would change them.
"""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression

from common import SEED
from load import GP, REV, load_clean, save_table

rng = np.random.default_rng(SEED)
DRINK_CATS = ["Hot Coffee", "Cold Coffee", "Cold Drinks", "Matcha & Tea"]
FOOD_CATS = ["Bakery", "Breakfast", "Desserts", "Meals", "Sandwiches"]

d = load_clean()
assert set(d.Category) == set(DRINK_CATS + FOOD_CATS)
d["is_drink"] = d.Category.isin(DRINK_CATS)

# ---------- one row per transaction ----------
# primary drink = the drink line with the highest list price, so each drink transaction has exactly one drink category
drinks = d[d.is_drink].sort_values(["Transaction ID", "Unit Price (USD)"], ascending=[True, False])
primary = drinks.drop_duplicates("Transaction ID").set_index("Transaction ID")["Category"].rename("drink_cat")
t = d.groupby("Transaction ID").agg(
    branch=("Branch", "first"), hour=("hour", "first"), weekday=("weekday", "first"), month=("month", "first"),
    order_type=("Order Type", "first"), n_drink=("is_drink", "sum"),
    n_food=("is_drink", lambda s: (~s).sum()))
t = t.join(primary)
dt = t[t.n_drink > 0].copy()                      # transactions that contain at least one drink
dt["attached"] = dt.n_food > 0
dt["hour_block"] = pd.cut(dt.hour, [6, 10, 14, 18, 24], labels=["07-10", "11-14", "15-18", "19-23"])
print(f"transactions {len(t):,}: drink+food {(dt.attached).sum():,}, drink-only {(~dt.attached).sum():,}, "
      f"food-only {(t.n_drink == 0).sum():,}")
print(f"MEASURED: attach rate = share of drink transactions that also contain a food item = {dt.attached.mean():.1%}")


def wilson(k, n, z=1.96):
    p = k / n
    centre = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return centre - half, centre + half


# ---------- 1. attach rate by segment ----------
rows, homog = [], []
for dim in ["branch", "hour", "hour_block", "weekday", "month", "order_type", "drink_cat"]:
    g = dt.groupby(dim, observed=True)["attached"].agg(["sum", "size"])
    for lvl, r in g.iterrows():
        lo, hi = wilson(r["sum"], r["size"])
        rows.append({"dimension": dim, "level": lvl, "drink_transactions": int(r["size"]),
                     "attached": int(r["sum"]), "drink_only": int(r["size"] - r["sum"]),
                     "attach_rate": r["sum"] / r["size"], "ci_low": lo, "ci_high": hi})
    chi2, p, dof, _ = stats.chi2_contingency(pd.crosstab(dt[dim], dt.attached))
    homog.append({"dimension": dim, "chi2": chi2, "dof": dof, "p_value": p,
                  "min_rate": g["sum"].div(g["size"]).min(), "max_rate": g["sum"].div(g["size"]).max()})
att = pd.DataFrame(rows).round(4)
hom = pd.DataFrame(homog).round(4)
save_table(att, "basket_attach_rates.csv", index=False)
save_table(hom, "basket_attach_homogeneity.csv", index=False)
print("\nMEASURED: attach rate by segment (95% Wilson CI) -- results/basket_attach_rates.csv")
print(att[att.dimension.isin(["branch", "hour_block", "order_type", "drink_cat"])].to_string(index=False))
print("\nMEASURED: chi-square test that the attach rate is the same across levels (small p = it differs):")
print(hom.to_string(index=False))

# branch x drink category, so a category gap is not just a branch gap
bc = dt.pivot_table(index="drink_cat", columns="branch", values="attached", aggfunc="mean").round(4)
bn = dt.pivot_table(index="drink_cat", columns="branch", values="attached", aggfunc="size")
save_table(bc, "basket_attach_branch_category.csv")
print("\nMEASURED: attach rate, drink category x branch (n per cell >= %d)\n" % bn.min().min(), bc)

# adjusted check: likelihood-ratio test for each factor, controlling for the others (logistic regression, no penalty)
factors = ["branch", "hour_block", "weekday", "month", "order_type", "drink_cat"]


def logloss_fit(cols):
    X = pd.get_dummies(dt[cols].astype(str), drop_first=True, dtype=float)
    m = LogisticRegression(penalty=None, max_iter=2000).fit(X, dt.attached)
    return -len(dt) * np.mean(np.where(dt.attached, np.log(m.predict_proba(X)[:, 1]),
                                       np.log(m.predict_proba(X)[:, 0]))), X.shape[1]


ll_full, k_full = logloss_fit(factors)
lr = []
for f in factors:
    ll_red, k_red = logloss_fit([x for x in factors if x != f])
    stat = 2 * (ll_red - ll_full)
    lr.append({"factor": f, "lr_stat": stat, "dof": k_full - k_red, "p_value": stats.chi2.sf(stat, k_full - k_red)})
lr = pd.DataFrame(lr).round(4)
save_table(lr, "basket_attach_adjusted_tests.csv", index=False)
print("\nMEASURED: does each factor still matter after controlling for the others? (likelihood-ratio test)\n", lr.to_string(index=False))

# ---------- 2. under-sold drink + food pairs ----------
# Null model: "each item is chosen according to its popularity, independently of the other items in the basket".
# We keep every basket's shape (how many drink lines and food lines it has) and its branch, then shuffle which
# drink product fills each drink slot and which food product fills each food slot, within the branch. A pair that is
# bought together less often than in these shuffles is under-sold relative to the popularity of its two items.
# Total drink+food baskets is fixed by the null, so over-sold pairs are balanced by under-sold ones: this finds
# WHICH food goes with which drink, it does not show that total food sales could rise (that is section 4).
N_PERM = 2000
drink_items = sorted(d.loc[d.is_drink, "Product"].unique())
food_items = sorted(d.loc[~d.is_drink, "Product"].unique())
di = {p: i for i, p in enumerate(drink_items)}
fi = {p: i for i, p in enumerate(food_items)}
nD, nF = len(drink_items), len(food_items)
item_cat = d.drop_duplicates("Product").set_index("Product")["Category"]
lines = d.reset_index(drop=True)


def pair_counts(tx_mask_months):
    """Observed and permuted pair-count arrays for the transactions whose month is in tx_mask_months."""
    L = lines[lines.month.isin(tx_mask_months)]
    L = L[L["Transaction ID"].map(t.n_drink).gt(0) & L["Transaction ID"].map(t.n_food).gt(0)]  # mixed baskets only
    dl = L[L.is_drink].reset_index(drop=True)
    fl = L[~L.is_drink].reset_index(drop=True)
    d_item = dl.Product.map(di).values
    f_item = fl.Product.map(fi).values
    # all (drink line, food line) pairs inside each basket
    pr = dl.reset_index().merge(fl.reset_index(), on="Transaction ID", suffixes=("_d", "_f"))
    a, b = pr["index_d"].values, pr["index_f"].values
    # popularity is taken from ALL drink / food lines of the branch (not only mixed baskets), as the brief asks
    allL = lines[lines.month.isin(tx_mask_months)]
    pool_d = {br: allL[allL.is_drink & (allL.Branch == br)].Product.map(di).values for br in allL.Branch.unique()}
    pool_f = {br: allL[~allL.is_drink & (allL.Branch == br)].Product.map(fi).values for br in allL.Branch.unique()}
    d_br, f_br = dl.Branch.values, fl.Branch.values

    def count(di_vec, fi_vec):
        return np.bincount(di_vec[a] * nF + fi_vec[b], minlength=nD * nF).reshape(nD, nF)

    obs = count(d_item, f_item)
    perms = np.empty((N_PERM, nD, nF))
    for k in range(N_PERM):
        dv, fv = d_item.copy(), f_item.copy()
        for br in pool_d:      # redraw each slot from the branch's overall popularity
            m = d_br == br
            dv[m] = rng.choice(pool_d[br], m.sum())
            m = f_br == br
            fv[m] = rng.choice(pool_f[br], m.sum())
        perms[k] = count(dv, fv)
    return obs, perms, L["Transaction ID"].nunique()


def bh(p):
    """Benjamini-Hochberg q-values."""
    p = np.asarray(p)
    o = np.argsort(p)
    q = np.empty_like(p)
    q[o] = np.minimum.accumulate((p[o] * len(p) / (np.arange(len(p)) + 1))[::-1])[::-1]
    return np.minimum(q, 1)


obs, perms, n_mixed = pair_counts(range(1, 7))
exp, sd = perms.mean(0), perms.std(0)
z = (obs - exp) / np.where(sd > 0, sd, np.nan)
p_two = 2 * stats.norm.sf(np.abs(z))
pairs = pd.DataFrame([{"drink": drink_items[i], "food": food_items[j], "drink_cat": item_cat[drink_items[i]],
                       "food_cat": item_cat[food_items[j]], "observed": int(obs[i, j]), "expected": exp[i, j],
                       "obs_over_exp": obs[i, j] / exp[i, j], "z": z[i, j], "p_value": p_two[i, j]}
                      for i in range(nD) for j in range(nF)])
pairs["q_value"] = bh(pairs.p_value.fillna(1).values)
# does the same direction hold in each half of the data? (replication, not a second test)
for name, months in [("jan_mar", [1, 2, 3]), ("apr_jun", [4, 5, 6])]:
    o2, p2, _ = pair_counts(months)
    pairs[f"obs_over_exp_{name}"] = (o2 / p2.mean(0)).reshape(-1)
pairs["undersold"] = (pairs.q_value < 0.05) & (pairs.obs_over_exp < 1)
pairs["oversold"] = (pairs.q_value < 0.05) & (pairs.obs_over_exp > 1)
pairs["stable_both_halves"] = (np.sign(pairs.obs_over_exp_jan_mar - 1) == np.sign(pairs.obs_over_exp - 1)) & \
                              (np.sign(pairs.obs_over_exp_apr_jun - 1) == np.sign(pairs.obs_over_exp - 1))
pairs = pairs.sort_values("z").round(4)
save_table(pairs, "basket_pairs.csv", index=False)
print(f"\nMEASURED: {n_mixed:,} drink+food baskets; {len(pairs)} item pairs tested, shuffle null with {N_PERM} draws")
print(f"pairs significantly under-sold (BH q<0.05): {pairs.undersold.sum()}; over-sold: {pairs.oversold.sum()}; "
      f"under-sold and same direction in both halves: {(pairs.undersold & pairs.stable_both_halves).sum()}")
cols = ["drink", "food", "observed", "expected", "obs_over_exp", "z", "q_value", "obs_over_exp_jan_mar", "obs_over_exp_apr_jun"]
print("most under-sold pairs:\n", pairs.head(12)[cols].to_string(index=False))
print("most over-sold pairs:\n", pairs.tail(8)[cols].to_string(index=False))

# same test one level up (drink category x food category): fewer, bigger cells, so far less noise
cat_d = np.array([DRINK_CATS.index(item_cat[p]) for p in drink_items])
cat_f = np.array([FOOD_CATS.index(item_cat[p]) for p in food_items])


def to_cat(a):
    out = np.zeros(a.shape[:-2] + (len(DRINK_CATS), len(FOOD_CATS)))
    for i in range(nD):
        for j in range(nF):
            out[..., cat_d[i], cat_f[j]] += a[..., i, j]
    return out


oc, pc = to_cat(obs), to_cat(perms)
ec, sc = pc.mean(0), pc.std(0)
catpairs = pd.DataFrame([{"drink_cat": DRINK_CATS[i], "food_cat": FOOD_CATS[j], "observed": int(oc[i, j]),
                          "expected": ec[i, j], "obs_over_exp": oc[i, j] / ec[i, j],
                          "z": (oc[i, j] - ec[i, j]) / sc[i, j]}
                         for i in range(len(DRINK_CATS)) for j in range(len(FOOD_CATS))])
catpairs["p_value"] = 2 * stats.norm.sf(catpairs.z.abs())
catpairs["q_value"] = bh(catpairs.p_value.values)
catpairs = catpairs.round(4)
save_table(catpairs, "basket_pairs_category.csv", index=False)
print("\nMEASURED: drink category x food category, observed / expected (<1 = under-sold)")
print(catpairs.pivot(index="drink_cat", columns="food_cat", values="obs_over_exp").round(2).to_string())
print(catpairs.sort_values("z").head(6)[["drink_cat", "food_cat", "observed", "expected", "obs_over_exp", "q_value"]].to_string(index=False))

# food mix: is a food item under-represented in drink baskets compared with food-only baskets?
f_lines = lines[~lines.is_drink].copy()
f_lines["in_drink_basket"] = f_lines["Transaction ID"].map(t.n_drink).gt(0)
fm = f_lines.groupby(["Product", "in_drink_basket"])["Quantity"].sum().unstack()
fm = (fm / fm.sum()).rename(columns={True: "share_of_food_in_drink_baskets", False: "share_of_food_in_food_only_baskets"})
fm["ratio_drink_vs_food_only"] = fm.iloc[:, 1] / fm.iloc[:, 0]
fm["category"] = item_cat.reindex(fm.index)
fm = fm.sort_values("ratio_drink_vs_food_only").round(4)
save_table(fm, "basket_food_mix.csv")
print("\nMEASURED: share of each food item in drink baskets vs in food-only baskets (ratio < 1 = bought alone more often)")
print(fm.head(6).to_string()); print(fm.tail(4).to_string())
