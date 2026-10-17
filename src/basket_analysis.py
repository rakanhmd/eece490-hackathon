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
