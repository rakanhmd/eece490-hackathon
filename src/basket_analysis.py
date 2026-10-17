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


def pair_counts(tx_mask_months, pool="all"):
    """Observed and permuted pair-count arrays for the transactions whose month is in tx_mask_months.
    pool="all": slots are redrawn from the popularity of ALL drink / food lines in the branch (the brief's definition).
    pool="mixed": redrawn only from lines in drink+food baskets, which isolates the pairing from the fact that some
    drinks are simply less often bought with food at all."""
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
    if pool == "mixed":
        allL = L
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

# conditional version: pool restricted to drink+food baskets (pure pairing affinity)
obs_c, perms_c, _ = pair_counts(range(1, 7), pool="mixed")
exp_c, sd_c = perms_c.mean(0), perms_c.std(0)
z_c = (obs_c - exp_c) / np.where(sd_c > 0, sd_c, np.nan)
cond = pd.DataFrame([{"drink": drink_items[i], "food": food_items[j], "obs_over_exp_given_basket": obs_c[i, j] / exp_c[i, j],
                      "z_given_basket": z_c[i, j]} for i in range(nD) for j in range(nF)])
cond["q_given_basket"] = bh(np.nan_to_num(2 * stats.norm.sf(np.abs(cond.z_given_basket.values)), nan=1.0))
pairs = pairs.merge(cond.round(4), on=["drink", "food"])
save_table(pairs, "basket_pairs.csv", index=False)
print(f"under-sold pairs when only drink+food baskets define popularity (q<0.05): "
      f"{((pairs.q_given_basket < 0.05) & (pairs.obs_over_exp_given_basket < 1)).sum()}; "
      f"over-sold: {((pairs.q_given_basket < 0.05) & (pairs.obs_over_exp_given_basket > 1)).sum()}")

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
oc2, pc2 = to_cat(obs_c), to_cat(perms_c)
ec2, sc2 = pc2.mean(0), pc2.std(0)
catpairs["obs_over_exp_given_basket"] = (oc2 / ec2).reshape(-1).round(4)
catpairs["q_given_basket"] = bh(2 * stats.norm.sf(np.abs(((oc2 - ec2) / sc2).reshape(-1)))).round(4)
save_table(catpairs, "basket_pairs_category.csv", index=False)
print("\nMEASURED: drink category x food category, observed / expected (<1 = under-sold)")
print(catpairs.pivot(index="drink_cat", columns="food_cat", values="obs_over_exp").round(2).to_string())
print("same, but expected counts built only from drink+food baskets (pure pairing, ignores that some drinks attach less often):")
print(catpairs.pivot(index="drink_cat", columns="food_cat", values="obs_over_exp_given_basket").round(2).to_string())
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

# ---------- 3. margin of the food items ----------
fl_all = lines[~lines.is_drink]
fmar = fl_all.groupby(["Category", "Product"]).agg(units=("Quantity", "sum"), revenue=(REV, "sum"), gross_profit=(GP, "sum"))
fmar["gp_per_unit"] = fmar.gross_profit / fmar.units
fmar["gross_margin"] = fmar.gross_profit / fmar.revenue
fmar = fmar.round(4).sort_values("gp_per_unit", ascending=False)
save_table(fmar, "basket_food_margin.csv")
fcat = fl_all.groupby(["Category", "Branch"]).agg(units=("Quantity", "sum"), revenue=(REV, "sum"), gp=(GP, "sum"))
fcat["gp_per_unit"] = fcat.gp / fcat.units
fcat["gross_margin"] = fcat.gp / fcat.revenue
fcat = fcat.round(4)
save_table(fcat, "basket_food_margin_category.csv")
print("\nMEASURED: food gross profit per unit and margin, by category and branch (after discounts)")
print(fcat[["gp_per_unit", "gross_margin"]].unstack("Branch").round(3).to_string())
drink_m = lines[lines.is_drink].groupby("Category").apply(lambda g: pd.Series({"gp_per_unit": g[GP].sum() / g.Quantity.sum(),
                                                                                "gross_margin": g[GP].sum() / g[REV].sum()}), include_groups=False)
print("for comparison, drinks:\n", drink_m.round(3).to_string())

# ---------- value of under-sold category pairs (reallocation, NOT new sales) ----------
mixed_ids = t.index[(t.n_drink > 0) & (t.n_food > 0)]
fm_lines = lines[~lines.is_drink & lines["Transaction ID"].isin(mixed_ids)]
gp_unit_cat = fm_lines.groupby("Category").apply(lambda g: g[GP].sum() / g.Quantity.sum(), include_groups=False)
under = catpairs[(catpairs.q_value < 0.05) & (catpairs.obs_over_exp < 1)].copy()
under["missing_baskets_vs_expected"] = (under.expected - under.observed).round(1)
under["food_gp_per_unit_in_drink_baskets"] = under.food_cat.map(gp_unit_cat).round(3)
under["gp_if_closed_usd_upper_bound"] = (under.missing_baskets_vs_expected * under.food_gp_per_unit_in_drink_baskets).round(0)
save_table(under, "basket_undersold_category_pairs.csv", index=False)
print("\nMEASURED: category pairs sold less often than popularity predicts (q<0.05), with the food's margin")
print(under[["drink_cat", "food_cat", "observed", "expected", "obs_over_exp", "missing_baskets_vs_expected",
             "food_gp_per_unit_in_drink_baskets", "gp_if_closed_usd_upper_bound"]].to_string(index=False))
print("ESTIMATE note: closing these gaps only moves food between drinks unless total attach rises, so the dollars above\n"
      "are an upper bound on what pair-steering alone could add, not a forecast.")

# ---------- 4. ESTIMATE: gross profit from a higher attach rate ----------
DAYS = (d.date.max() - d.date.min()).days + 1
ANNUAL = 365 / DAYS
mx = t.loc[mixed_ids]
per_branch = []
for br in sorted(t.branch.unique()):
    ids = mx.index[mx.branch == br]
    fb = fm_lines[fm_lines["Transaction ID"].isin(ids)]
    per_branch.append({"branch": br, "drink_tx": int((dt.branch == br).sum()), "attach": dt[dt.branch == br].attached.mean(),
                       "food_gp_per_attached_basket": fb[GP].sum() / len(ids),
                       "food_list_rev_per_attached_basket": fb["list_revenue"].sum() / len(ids),
                       "attached_baskets": len(ids), "food_list_rev_in_attached": fb["list_revenue"].sum()})
pb = pd.DataFrame(per_branch).set_index("branch")
tot_gp_basket = (pb.food_gp_per_attached_basket * pb.attached_baskets).sum() / pb.attached_baskets.sum()
# bootstrap CI for the measured GP per attached basket (resample baskets)
bk = fm_lines.groupby("Transaction ID")[GP].sum().values
bs = [rng.choice(bk, len(bk)).mean() for _ in range(1000)]
print(f"\nMEASURED: food gross profit per drink+food basket = ${bk.mean():.2f} (95% bootstrap CI {np.percentile(bs, 2.5):.2f}-{np.percentile(bs, 97.5):.2f})")
print(pb.round(3).to_string())
low_factor = gp_unit_cat["Bakery"] / (fm_lines[GP].sum() / fm_lines.Quantity.sum())   # cheapest food category, as the low case
print(f"low-case food margin factor = Bakery GP/unit / average food GP/unit = {low_factor:.2f}")

scen = []


def add_scenario(name, assumption, gain_by_branch, factor):
    """gain_by_branch: extra attached baskets per branch (Series). Incremental basket earns factor x branch average."""
    extra = gain_by_branch
    gp = (extra * pb.food_gp_per_attached_basket * factor).sum()
    # if the offer were a 10% discount on food sold with a drink, it also applies to baskets that would attach anyway
    disc = 0.10 * (pb.food_list_rev_in_attached.sum() + (extra * pb.food_list_rev_per_attached_basket).sum())
    scen.append({"scenario": name, "assumption": assumption, "extra_attached_baskets_H1": extra.sum(),
                 "gp_per_extra_basket_factor": factor, "extra_gp_H1_usd": gp,
                 "extra_gp_annualised_usd": gp * ANNUAL,
                 "cost_if_10pct_combo_discount_H1_usd": disc,
                 "net_with_combo_discount_H1_usd": gp - disc})


for pp in [0.01, 0.025, 0.05]:
    for f_, lab in [(low_factor, "cheap add-on (Bakery margin)"), (1.0, "average food margin")]:
        add_scenario(f"+{pp*100:g} pp attach, {lab}", f"attach rate rises by {pp*100:g} pp in every branch; extra basket earns {f_:.2f}x avg",
                     pb.drink_tx * pp, f_)
# data-anchored benchmark: every drink category reaches the best existing category's attach rate
best = att[(att.dimension == "drink_cat")].set_index("level").attach_rate.max()
dcat = dt.groupby(["branch", "drink_cat"]).attached.agg(["mean", "size"])
gap = ((best - dcat["mean"]).clip(lower=0) * dcat["size"]).groupby("branch").sum()
add_scenario("benchmark: all drink categories reach the best category's rate",
             f"every drink category rises to {best:.1%} (Matcha & Tea today); assumes drinks differ only by habit, which may be false",
             gap, 1.0)
sc = pd.DataFrame(scen).round(1)
save_table(sc, "basket_value_scenarios.csv", index=False)
print("\nESTIMATE (assumption-driven, NOT measured): extra gross profit from a higher attach rate, Jan-Jun 2026 volume")
print(sc.drop(columns="assumption").to_string(index=False))

# break-even for a 10% combo discount applied to every food item sold with a drink
F0 = pb.food_list_rev_in_attached.sum()
Ntx = pb.drink_tx.sum()
net_per_basket = tot_gp_basket - 0.10 * (pb.food_list_rev_in_attached.sum() / pb.attached_baskets.sum())
be = 0.10 * F0 / (Ntx * net_per_basket)
print(f"ESTIMATE: a 10% discount on all food sold with a drink only pays if attach rises by >= {be*100:.1f} pp "
      f"(today's {dt.attached.mean():.1%} -> {(dt.attached.mean()+be):.1%}); a prompt or placement with no discount has no such hurdle")
save_table(pd.DataFrame({"breakeven_attach_gain_pp_for_10pct_combo_discount": [round(be * 100, 2)]}), "basket_discount_breakeven.csv", index=False)

# ---------- 5. design of a practical test ----------
daily = dt.join(lines.drop_duplicates("Transaction ID").set_index("Transaction ID")["date"])
dd = daily.groupby(["branch", "date"]).attached.agg(["sum", "size"])
dd["rate"] = dd["sum"] / dd["size"]
p0 = dt.attached.mean()
deff = {}
for br in ["Garden", "Harbour", "Uptown"]:
    x = dd.loc[br]
    deff[br] = max(1.0, x.rate.var() / (p0 * (1 - p0) / x["size"].mean()))
print("\nMEASURED: day-to-day variance of attach rate vs pure binomial noise (design effect): "
      + ", ".join(f"{k} {float(v):.2f}" for k, v in deff.items()))
june = dd.reset_index()
june = june[june.date >= "2026-06-01"].groupby("branch")["size"].mean()
z_a, z_b = stats.norm.ppf(0.975), stats.norm.ppf(0.8)
options = {"Garden treated vs Uptown control": (min(june["Garden"], june["Uptown"]), max(deff["Garden"], deff["Uptown"])),
           "Harbour treated vs Garden+Uptown control": (min(june["Harbour"], june["Garden"] + june["Uptown"]),
                                                       max(deff.values()))}
pw = []
for pp in [0.02, 0.03, 0.05]:
    p1 = p0 + pp
    n_arm = (z_a + z_b) ** 2 * (p0 * (1 - p0) + p1 * (1 - p1)) / pp**2
    for name, (per_day, de) in options.items():
        pw.append({"detectable_gain_pp": pp * 100, "design": name, "drink_tx_needed_per_arm": round(n_arm),
                   "drink_tx_per_day_in_smaller_arm_june": round(per_day, 1),
                   "days_needed": round(n_arm * max(1.0, de) / per_day),
                   "note": "two-proportion test, 80% power, 5% level, inflated by the day-to-day design effect"})
pw = pd.DataFrame(pw)
save_table(pw, "basket_pilot_power.csv", index=False)
print("ESTIMATE: how long a two-branch pilot must run to see a gain of this size\n", pw.drop(columns="note").to_string(index=False))

# ---------- figures ----------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import save_fig

fig, ax = plt.subplots(figsize=(8, 4.5))
cat_att = att[att.dimension == "drink_cat"].set_index("level").loc[DRINK_CATS]
ax.bar(cat_att.index, 100 * cat_att.attach_rate, color="#4c78a8",
       yerr=100 * np.vstack([cat_att.attach_rate - cat_att.ci_low, cat_att.ci_high - cat_att.attach_rate]), capsize=4)
ax.axhline(100 * dt.attached.mean(), color="#c0392b", ls="--", label=f"all drink transactions ({dt.attached.mean():.1%})")
ax.set_ylim(30, 48)
ax.set_title("Share of drink transactions that also contain food, by primary drink (95% CI)")
ax.set_xlabel("Primary drink category")
ax.set_ylabel("Attach rate (%)")
ax.legend()
save_fig(fig, "basket_attach_by_category.png")

fig, ax = plt.subplots(figsize=(7, 4))
M = catpairs.pivot(index="drink_cat", columns="food_cat", values="obs_over_exp").loc[DRINK_CATS, FOOD_CATS]
im = ax.imshow(M.values, cmap="RdBu", vmin=0.4, vmax=1.6)
ax.set_xticks(range(len(FOOD_CATS)), FOOD_CATS)
ax.set_yticks(range(len(DRINK_CATS)), DRINK_CATS)
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        ax.text(j, i, f"{M.values[i, j]:.2f}", ha="center", va="center", fontsize=9,
                color="white" if M.values[i, j] > 1.35 or M.values[i, j] < 0.65 else "black")
ax.set_title("Drink + food baskets: observed / expected from item popularity\n(<1 = under-sold, >1 = over-sold)")
ax.set_xlabel("Food category")
ax.set_ylabel("Primary drink category")
fig.colorbar(im, ax=ax)
save_fig(fig, "basket_pair_ratio.png")
print("saved figures/basket_attach_by_category.png, figures/basket_pair_ratio.png")
