"""Customer churn model, RFM segments and a win-back plan (known-ID customers only).

Setup: features come ONLY from transactions before 2026-05-01 (Jan-Apr). Label = the customer made no purchase in
May-Jun. Customers are split 70/15/15 (stratified on the label, SEED) before any fitting; imputers/scalers live inside
Pipelines; models and the threshold are chosen on validation; the test set is scored once, for the chosen model
and the dummy baseline only.
The data is real Stories data with anonymized IDs; 36.5% of lines have no Customer ID, so customer results cover
identified customers only. 94% of identified customers use more than one branch. "Churn" here is "this ID stopped appearing".
"""
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, confusion_matrix, precision_recall_curve,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from common import RESULTS_CSV, SEED, choose_threshold, log_result, save_fig, split_train_val_test
from load import GP, REV, load_clean, save_table

warnings.filterwarnings("ignore", category=FutureWarning)
rng = np.random.default_rng(SEED)
CUT = pd.Timestamp("2026-05-01")
DRINKS = ["Hot Coffee", "Cold Coffee", "Cold Drinks", "Matcha & Tea"]

d = load_clean()
k = d.dropna(subset=["Customer ID"]).copy()
hist, fut = k[k.date < CUT], k[k.date >= CUT]
print(f"known-ID lines: {len(k):,} ({k['Customer ID'].nunique():,} customers); Jan-Apr {len(hist):,} lines, May-Jun {len(fut):,}")


# ---------------- features (Jan-Apr only) ----------------
def build_features(h: pd.DataFrame, cut: pd.Timestamp = CUT) -> pd.DataFrame:
    assert h.date.max() < cut, "leakage: feature input contains rows on or after the cut-off"
    last_day = cut - pd.Timedelta(days=1)
    tx = h.groupby(["Customer ID", "Transaction ID"]).agg(
        date=("date", "first"), hour=("hour", "first"), weekday=("weekday", "first"), branch=("Branch", "first"),
        dinein=("Order Type", lambda s: (s == "Dine-in").any()), spend=(REV, "sum"), units=("Quantity", "sum"),
        gp=(GP, "sum"), disc=("Discount Rate", lambda s: (s > 0).any())).reset_index()
    g = tx.groupby("Customer ID")
    f = pd.DataFrame({
        "visits": g.size(),
        "active_days": g.date.nunique(),
        "recency_days": (last_day - g.date.max()).dt.days,
        "tenure_days": (g.date.max() - g.date.min()).dt.days,
        "days_since_first": (last_day - g.date.min()).dt.days,
        "spend_total": g.spend.sum(),
        "avg_basket_usd": g.spend.mean(),
        "avg_units_per_visit": g.units.mean(),
        "gp_total": g.gp.sum(),
        "visits_last_30d": tx[tx.date >= cut - pd.Timedelta(days=30)].groupby("Customer ID").size().reindex(g.size().index, fill_value=0),   # April for the Jan-Apr period
        "share_discounted_visits": g.disc.mean(),
        "share_dine_in": g.dinein.mean(),
        "share_weekend": tx.assign(w=tx.weekday >= 5).groupby("Customer ID").w.mean(),
        "share_evening": tx.assign(e=tx.hour >= 18).groupby("Customer ID").e.mean(),
        "share_morning": tx.assign(e=tx.hour < 11).groupby("Customer ID").e.mean(),
        "n_branches": g.branch.nunique(),
    })
    f["mean_gap_days"] = f.tenure_days / (f.visits - 1).replace(0, np.nan)   # NaN for one-visit customers (imputed in the pipeline)
    f["last30d_share_of_visits"] = f.visits_last_30d / f.visits
    f["n_categories"] = h.groupby("Customer ID").Category.nunique()
    cs = h.pivot_table(index="Customer ID", columns="Category", values=REV, aggfunc="sum", fill_value=0)
    cs = cs.div(cs.sum(1), axis=0).add_prefix("cat_share_")
    bs = tx.pivot_table(index="Customer ID", columns="branch", values="spend", aggfunc="count", fill_value=0)
    bs = bs.div(bs.sum(1), axis=0).add_prefix("branch_share_")
    return f.join(cs).join(bs)


X = build_features(hist)
y = (~X.index.isin(fut["Customer ID"].unique())).astype(int)
y = pd.Series(y, index=X.index, name="churned")
print(f"customers active Jan-Apr: {len(X):,}; churned (no purchase May-Jun): {y.sum():,} = {y.mean():.1%}; "
      f"{fut['Customer ID'].nunique() - (~y.astype(bool)).sum()} May-Jun customers were new and are excluded")
print(f"features: {X.shape[1]}, all computed from rows before {CUT.date()}")
# leakage check 2: rebuilding features from a file that never contained May-Jun gives identical numbers
assert build_features(d[d.date < CUT].dropna(subset=["Customer ID"])).equals(X)
print("leakage check: features rebuilt from data with May-Jun removed are identical")

X_tr, X_va, X_te, y_tr, y_va, y_te = split_train_val_test(X, y)
print(f"split customers train/val/test = {len(X_tr)}/{len(X_va)}/{len(X_te)}; churn rate "
      f"{y_tr.mean():.3f}/{y_va.mean():.3f}/{y_te.mean():.3f}")


# ---------------- models ----------------
def lr(C):
    return Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler()),
                     ("m", LogisticRegression(C=C, max_iter=2000))])


def gb(depth, lrate, iters):
    return Pipeline([("m", HistGradientBoostingClassifier(max_depth=depth, learning_rate=lrate, max_iter=iters,
                                                          min_samples_leaf=40, l2_regularization=1.0, random_state=SEED))])


def poisson_gap_score(Xf):
    """Rule, not a fitted model: if purchases arrive at a steady rate, P(no purchase in 61 days) = exp(-rate*61*growth).
    rate = Jan-Apr visits per day; growth = ratio of May-Jun to Jan-Apr daily transactions (all branches).
    It uses May-Jun growth, so it is a retrospective reference, not a forecast available at the April cutoff."""
    return np.exp(-(Xf.visits / 120.0) * 61 * GROWTH)


tx_day = d.groupby("date")["Transaction ID"].nunique()
GROWTH = (tx_day[tx_day.index >= CUT].mean() / tx_day[tx_day.index < CUT].mean())

cands = {"dummy_prior": DummyClassifier(strategy="prior")}
for C in [0.01, 0.1, 1, 10]:
    cands[f"logreg_C{C}"] = lr(C)
for depth in [2, 3]:
    for lrate in [0.03, 0.1]:
        for iters in [100, 200]:
            cands[f"gboost_d{depth}_lr{lrate}_it{iters}"] = gb(depth, lrate, iters)
rows, fitted = [], {}
for name, m in cands.items():
    m.fit(X_tr, y_tr)
    p = m.predict_proba(X_va)[:, 1]
    fitted[name] = m
    rows.append({"model": name, "val_pr_auc": average_precision_score(y_va, p), "val_roc_auc": roc_auc_score(y_va, p)})
p_rule = poisson_gap_score(X_va)
rows.append({"model": "poisson_gap_rule", "val_pr_auc": average_precision_score(y_va, p_rule), "val_roc_auc": roc_auc_score(y_va, p_rule)})
val = pd.DataFrame(rows).round(4).set_index("model")
# context for stability only (train folds, no val/test): 5-fold CV ROC-AUC on the training set
skf = StratifiedKFold(5, shuffle=True, random_state=SEED)
val["cv_train_roc_auc"] = [round(cross_val_score(cands[n], X_tr, y_tr, cv=skf, scoring="roc_auc").mean(), 4) if n in cands else np.nan
                           for n in val.index]
save_table(val, "customer_churn_validation.csv")
print(f"\nVALIDATION (prevalence = {y_va.mean():.4f}; a no-skill PR-AUC equals the prevalence)\n", val.to_string())

# pick the best per family on validation PR-AUC, then the overall best
fam = {"logistic": val.loc[[i for i in val.index if i.startswith("logreg")]].val_pr_auc.idxmax(),
       "gboost": val.loc[[i for i in val.index if i.startswith("gboost")]].val_pr_auc.idxmax()}
best = max(fam.values(), key=lambda n: val.loc[n, "val_pr_auc"])
print(f"best per family on validation: {fam}; overall: {best}")

# how much PR-AUC can pure noise reach on a validation set this small? (random scores, 2000 draws)
noise = np.array([average_precision_score(y_va, rng.random(len(y_va))) for _ in range(2000)])
print(f"noise reference on validation: random scores give PR-AUC mean {noise.mean():.4f}, 95th percentile {np.percentile(noise, 95):.4f}")
noise_roc = np.array([roc_auc_score(y_va, rng.random(len(y_va))) for _ in range(2000)])
print(f"                               ROC-AUC 2.5-97.5 percentile {np.percentile(noise_roc, 2.5):.3f}-{np.percentile(noise_roc, 97.5):.3f}")

# does the steady-purchase-rate rule explain the churn we see?  (all customers; a measurement, not a model)
exp_churn = poisson_gap_score(X)
print(f"\nIf every customer kept buying at their Jan-Apr rate (growth x{GROWTH:.2f}), expected churn = {exp_churn.mean():.1%}; "
      f"observed = {y.mean():.1%}")
save_table(pd.DataFrame({"observed_churn": [y.mean()], "expected_if_steady_rate": [exp_churn.mean()], "growth_factor": [GROWTH]}).round(4),
           "customer_churn_vs_steady_rate.csv", index=False)
# does Jan-Apr behaviour relate to churn at all? simple univariate view (train+val only; test untouched)
tv = pd.concat([X_tr, X_va]); ytv = pd.concat([y_tr, y_va])
uni = pd.DataFrame({c: {"auc": roc_auc_score(ytv, tv[c].fillna(tv[c].median()))} for c in tv.columns}).T
uni["abs_dev_from_0.5"] = (uni.auc - 0.5).abs()
uni = uni.sort_values("abs_dev_from_0.5", ascending=False).round(4)
save_table(uni, "customer_churn_univariate_auc.csv")
print("single-feature ROC-AUC on train+val (0.5 = no signal), strongest 5:\n", uni.head(5)["auc"].to_string())

# ---------------- threshold on validation, test once ----------------
model = fitted[best]
p_va = model.predict_proba(X_va)[:, 1]
thr = choose_threshold(y_va, p_va, goal="f1")
print(f"\nchosen model: {best}; threshold chosen on validation (max F1) = {thr:.4f}")


def scores_at(y_true, p, t):
    pred = (p >= t).astype(int)
    return {"pr_auc": average_precision_score(y_true, p), "roc_auc": roc_auc_score(y_true, p),
            "precision": precision_score(y_true, pred, zero_division=0), "recall": recall_score(y_true, pred, zero_division=0),
            "flag_rate": pred.mean()}


# a clean tidy-up so a re-run does not duplicate our rows in the shared results log
if pd.io.common.file_exists(RESULTS_CSV):
    log = pd.read_csv(RESULTS_CSV)
    log[~log.model.astype(str).str.startswith("churn_")].to_csv(RESULTS_CSV, index=False)

sv = scores_at(y_va, p_va, thr)
dummy = fitted["dummy_prior"]
sd = scores_at(y_va, dummy.predict_proba(X_va)[:, 1], 1.0)
log_result("churn_dummy_prior", "val", {k_: round(v, 4) for k_, v in sd.items()}, "no skill; PR-AUC = prevalence")
log_result(f"churn_{best}", "val", {k_: round(v, 4) for k_, v in sv.items()}, f"threshold {thr:.4f} chosen on val (max F1)")
best_gb = fam["gboost"]
pg = fitted[best_gb].predict_proba(X_va)[:, 1]
log_result(f"churn_{best_gb}", "val", {k_: round(v, 4) for k_, v in scores_at(y_va, pg, choose_threshold(y_va, pg)).items()}, "best gradient boosting on val")

p_te = model.predict_proba(X_te)[:, 1]
st = scores_at(y_te, p_te, thr)
st_dummy = scores_at(y_te, dummy.predict_proba(X_te)[:, 1], 1.0)
cm = confusion_matrix(y_te, (p_te >= thr).astype(int))
boots = []
for _ in range(2000):
    i = rng.integers(0, len(y_te), len(y_te))
    if y_te.values[i].sum() == 0:
        continue
    boots.append([average_precision_score(y_te.values[i], p_te[i]), roc_auc_score(y_te.values[i], p_te[i])])
ci = np.percentile(boots, [2.5, 97.5], axis=0)
log_result(f"churn_{best}", "test", {k_: round(v, 4) for k_, v in st.items()}, f"threshold {thr:.4f}; test scored once")
log_result("churn_dummy_prior", "test", {k_: round(v, 4) for k_, v in st_dummy.items()}, "no skill")
print(f"\nTEST (scored once; {len(y_te)} customers, {y_te.sum()} churners = prevalence {y_te.mean():.4f})")
print(f"  PR-AUC  {st['pr_auc']:.4f} (95% bootstrap CI {ci[0,0]:.3f}-{ci[1,0]:.3f})   dummy {st_dummy['pr_auc']:.4f}")
print(f"  ROC-AUC {st['roc_auc']:.4f} (95% bootstrap CI {ci[0,1]:.3f}-{ci[1,1]:.3f})   dummy 0.5")
print(f"  at threshold {thr:.4f}: precision {st['precision']:.3f}, recall {st['recall']:.3f}, share flagged {st['flag_rate']:.3f}")
print(f"  confusion matrix [[TN FP],[FN TP]]:\n{cm}")
res = pd.DataFrame([{"model": best, "threshold": thr, **{k_: round(v, 4) for k_, v in st.items()},
                     "pr_auc_ci_low": ci[0, 0], "pr_auc_ci_high": ci[1, 0], "roc_auc_ci_low": ci[0, 1], "roc_auc_ci_high": ci[1, 1],
                     "tn": cm[0, 0], "fp": cm[0, 1], "fn": cm[1, 0], "tp": cm[1, 1], "prevalence_test": y_te.mean()}]).round(4)
save_table(res, "customer_churn_test.csv", index=False)
beats = ci[0, 0] > y_te.mean() and ci[0, 1] > 0.5
print(f"\nVERDICT: model clearly beats baseline? {'yes' if beats else 'NO'} "
      f"(rule set before looking at test: lower end of both bootstrap intervals must exceed prevalence / 0.5)")

# ---------------- figure ----------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(6.5, 4.5))
for lab, yy, pp, c in [("validation", y_va, p_va, "#2c3e50"), ("test", y_te, p_te, "#c0392b")]:
    pr, rc, _ = precision_recall_curve(yy, pp)
    ax.plot(rc, pr, label=f"{lab} (PR-AUC {average_precision_score(yy, pp):.3f})", color=c)
    ax.axhline(yy.mean(), color=c, ls=":", lw=1)
ax.set_title(f"Churn model ({best}): precision-recall vs no-skill (dotted)")
ax.set_xlabel("Recall")
ax.set_ylabel("Precision")
ax.set_ylim(0, 0.5)
ax.legend()
save_fig(fig, "customer_churn_pr_curve.png")

# =====================================================================
# 2. RFM segments (unsupervised: the churn label is NOT used to build them)
# =====================================================================
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

R = X[["recency_days", "visits", "spend_total"]].copy()
R["visits"] = np.log1p(R.visits)            # frequency and spend are right-skewed
R["spend_total"] = np.log1p(R.spend_total)
Z = StandardScaler().fit_transform(R)
sil = {}
for kk in range(2, 9):
    km = KMeans(n_clusters=kk, n_init=10, random_state=SEED).fit(Z)
    sil[kk] = silhouette_score(Z, km.labels_)
sil_s = pd.Series(sil).round(4)
K = int(sil_s.idxmax())
save_table(sil_s.rename("silhouette").to_frame(), "customer_segments_silhouette.csv")
print("\nSEGMENTS: silhouette by k:", sil_s.to_dict(), f"-> k = {K}")
print("note: silhouette values below ~0.25 mean the groups are not well separated (a slicing of a continuum)")
km = KMeans(n_clusters=K, n_init=10, random_state=SEED).fit(Z)
seg = pd.Series(km.labels_, index=X.index, name="segment")


def wilson(kk, n, z=1.96):
    p = kk / n
    c = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return c - h, c + h


cat_cols = [c for c in X.columns if c.startswith("cat_share_")]
br_cols = [c for c in X.columns if c.startswith("branch_share_")]
rows = []
for s_, idx in seg.groupby(seg).groups.items():
    xs = X.loc[idx]
    n = len(xs)
    lo, hi = wilson(y.loc[idx].sum(), n)
    rows.append({"segment": s_, "customers": n, "share_of_customers": n / len(X),
                 "recency_days_mean": xs.recency_days.mean(), "visits_mean": xs.visits.mean(),
                 "spend_mean_usd": xs.spend_total.mean(), "avg_basket_usd": xs.avg_basket_usd.mean(),
                 "gross_margin": xs.gp_total.sum() / xs.spend_total.sum(), "gp_per_customer_usd": xs.gp_total.mean(),
                 "share_of_total_spend": xs.spend_total.sum() / X.spend_total.sum(),
                 "main_branch": xs[br_cols].mean().idxmax().replace("branch_share_", ""),
                 "main_branch_share": xs[br_cols].mean().max(),
                 "top_category": xs[cat_cols].mean().idxmax().replace("cat_share_", ""),
                 "top_category_share": xs[cat_cols].mean().max(),
                 "churn_rate": y.loc[idx].mean(), "churn_ci_low": lo, "churn_ci_high": hi})
sg = pd.DataFrame(rows).sort_values("spend_mean_usd", ascending=False).round(4)
save_table(sg, "customer_segments.csv", index=False)
chi2, p_chi, _, _ = stats.chi2_contingency(pd.crosstab(seg, y))
print("\nSEGMENT PROFILES (Jan-Apr behaviour; churn = no purchase May-Jun)\n", sg.T.to_string(header=False))
print(f"chi-square test that churn differs between segments: p = {p_chi:.3f}")
overall_branch = X[br_cols].mean().round(3).to_dict()
print("all customers' average branch shares:", overall_branch)

pca = PCA(n_components=2, random_state=SEED).fit(Z)
P2 = pca.transform(Z)
fig, ax = plt.subplots(figsize=(7, 5))
for s_ in sorted(seg.unique()):
    m_ = (seg == s_).values
    ax.scatter(P2[m_, 0], P2[m_, 1], s=8, alpha=0.5, label=f"segment {s_} (n={m_.sum()})")
ax.set_title(f"RFM segments (k={K}, KMeans) in PCA 2D; PCA explains {100 * pca.explained_variance_ratio_.sum():.0f}% of variance")
ax.set_xlabel("PC1")
ax.set_ylabel("PC2")
ax.legend(markerscale=2)
save_fig(fig, "customer_segments_pca.png")
fig, ax = plt.subplots(figsize=(6.5, 4))
sgp = sg.sort_values("segment")
ax.bar(sgp.segment.astype(str), 100 * sgp.churn_rate, color="#4c78a8",
       yerr=100 * np.vstack([sgp.churn_rate - sgp.churn_ci_low, sgp.churn_ci_high - sgp.churn_rate]), capsize=4)
ax.axhline(100 * y.mean(), color="#c0392b", ls="--", label=f"all customers ({y.mean():.1%})")
ax.set_title("Churn rate by RFM segment (95% CI)")
ax.set_xlabel("Segment")
ax.set_ylabel("No purchase in May-Jun (%)")
ax.legend()
save_fig(fig, "customer_segment_churn.png")

# =====================================================================
# 3. business use: win-back offer (ESTIMATE; every parameter below is an assumption)
# =====================================================================
N_BASE = len(X)
gp_month = X.gp_total / 4.0                         # Jan-Apr gross profit per customer-month (measured)
avg_basket = X.avg_basket_usd.mean()
print(f"\nMEASURED: customers {N_BASE:,}; gross profit per customer-month (Jan-Apr) mean ${gp_month.mean():.2f}, "
      f"average basket ${avg_basket:.2f}")
# precision/recall at the chosen threshold with a bootstrap interval (test set, so out of sample)
pr_b = []
pred_te = (p_te >= thr).astype(int)
for _ in range(2000):
    i = rng.integers(0, len(y_te), len(y_te))
    yy, pp = y_te.values[i], pred_te[i]
    if pp.sum() == 0 or yy.sum() == 0:
        continue
    pr_b.append([precision_score(yy, pp), recall_score(yy, pp)])
prec_ci, rec_ci = np.percentile(np.array(pr_b)[:, 0], [2.5, 97.5]), np.percentile(np.array(pr_b)[:, 1], [2.5, 97.5])
print(f"MEASURED (test): precision {st['precision']:.3f} (95% CI {prec_ci[0]:.3f}-{prec_ci[1]:.3f}), "
      f"recall {st['recall']:.3f} ({rec_ci[0]:.3f}-{rec_ci[1]:.3f}), flagged {st['flag_rate']:.1%}; no-skill precision = {y_te.mean():.3f}")
flagged = st["flag_rate"] * N_BASE
caught = st["recall"] * y.mean() * N_BASE
print(f"scaled to the {N_BASE:,}-customer base: flag {flagged:,.0f} customers, containing about {caught:,.0f} of the "
      f"{y.mean() * N_BASE:,.0f} who will lapse; flagging a random {st['flag_rate']:.1%} would catch about {st['flag_rate'] * y.mean() * N_BASE:,.0f}")

# assumptions (low / mid / high), all UNMEASURED
S = pd.DataFrame({
    "uplift_win_back": [0.05, 0.10, 0.20],      # share of would-be lapsers the offer brings back
    "months_retained": [2, 3, 6],                # how long a saved customer keeps buying at the old rate
    "redemption_rate_flagged": [0.40, 0.25, 0.15],   # share of ALL contacted customers who use the offer
    "discount_pct_of_basket": [0.15, 0.15, 0.15],
    "contact_cost_per_customer": [0.10, 0.05, 0.02],
}, index=["pessimistic", "middle", "optimistic"])
V = gp_month[y == 1].mean()          # value of one lapser-month (measured on churners' own Jan-Apr history)
rows = []
for target, prec, n_t in [("model-flagged (test precision)", st["precision"], flagged),
                          ("random customers, same number", y.mean(), flagged),
                          ("all active customers", y.mean(), N_BASE)]:
    for sc, a in S.iterrows():
        saved = n_t * prec * a.uplift_win_back
        gain = saved * V * a.months_retained
        cost = n_t * (a.contact_cost_per_customer + a.redemption_rate_flagged * a.discount_pct_of_basket * avg_basket)
        rows.append({"target": target, "scenario": sc, "customers_contacted": n_t, "precision_assumed": prec,
                     "customers_saved": saved, "gross_profit_gained_usd": gain, "offer_cost_usd": cost, "net_usd": gain - cost})
bu = pd.DataFrame(rows).round(2)
save_table(bu, "customer_winback_scenarios.csv", index=False)
print(f"\nESTIMATE (assumptions in results/customer_winback_scenarios.csv; value of a lapser-month = ${V:.2f}, measured on lapsers' own history)")
print(bu.to_string(index=False))
mid = S.loc["middle"]
cost_per = mid.contact_cost_per_customer + mid.redemption_rate_flagged * mid.discount_pct_of_basket * avg_basket
be_prec = cost_per / (mid.uplift_win_back * V * mid.months_retained)
print(f"ESTIMATE: with middle assumptions an offer costs ${cost_per:.2f} per contacted customer; it breaks even only if "
      f"{be_prec:.0%} of contacted customers would otherwise lapse (observed lapse rate {y.mean():.1%}, model-flagged {st['precision']:.1%})")

# value-based targeting: same lapse rate, but a bigger prize per customer in high-value segments
vs = []
for s_, idx in seg.groupby(seg).groups.items():
    xs = X.loc[idx]
    Vs = (xs.gp_total / 4.0).mean()
    ev = y.loc[idx].mean() * mid.uplift_win_back * Vs * mid.months_retained - cost_per
    vs.append({"segment": s_, "customers": len(idx), "lapse_rate": y.loc[idx].mean(), "gp_per_customer_month_usd": Vs,
               "expected_net_per_offer_usd_middle": ev})
vs = pd.DataFrame(vs).round(3).sort_values("expected_net_per_offer_usd_middle", ascending=False)
save_table(vs, "customer_winback_by_segment.csv", index=False)
print("\nESTIMATE: expected net per offer by segment (middle assumptions; lapse rates are noisy)\n", vs.to_string(index=False))

# A/B test sizing: two-arm test on 'no purchase in the next 8 weeks'
za, zb = stats.norm.ppf(0.975), stats.norm.ppf(0.8)
ab = []
for cut in [0.01, 0.02, 0.03]:
    p0, p1 = y.mean(), y.mean() - cut
    n = (za + zb) ** 2 * (p0 * (1 - p0) + p1 * (1 - p1)) / cut**2
    ab.append({"lapse_rate_cut_pp": cut * 100, "customers_per_arm": int(np.ceil(n)), "total": int(np.ceil(2 * n)),
               "base_available": N_BASE})
ab = pd.DataFrame(ab)
save_table(ab, "customer_ab_test_size.csv", index=False)
print("\nESTIMATE: A/B sample size (80%% power, 5%% level, baseline lapse rate %.1f%%)\n" % (100 * y.mean()), ab.to_string(index=False))

# =====================================================================
# 4. Second-period validation: features Jan-Mar, label = no purchase in Apr-May (June not used)
# Same recipe as above (same features, split seed, model grid, validation choices, one test scoring), so the two periods can be
# compared. The two label windows are both 61 days long. Period 1 above is features Jan-Apr / label May-Jun.
# =====================================================================
CUT2, LABEL_END2 = pd.Timestamp("2026-04-01"), pd.Timestamp("2026-05-31")
rng2 = np.random.default_rng(SEED + 1)          # own generator, so nothing above changes
hist2 = k[k.date < CUT2]
lab_win2 = k[(k.date >= CUT2) & (k.date <= LABEL_END2)]
X2 = build_features(hist2, CUT2)
y2 = pd.Series((~X2.index.isin(lab_win2["Customer ID"].unique())).astype(int), index=X2.index, name="churned")
assert build_features(d[d.date < CUT2].dropna(subset=["Customer ID"]), CUT2).equals(X2)
print(f"\nPERIOD 2: features before {CUT2.date()} ({X2.shape[1]} features, {len(X2):,} customers); label = no purchase "
      f"{CUT2.date()} to {LABEL_END2.date()}; churned {y2.sum()} = {y2.mean():.1%}")
print("leakage check: features rebuilt from data with everything on/after the cut-off removed are identical")
a_tr, a_va, a_te, b_tr, b_va, b_te = split_train_val_test(X2, y2)
print(f"split train/val/test = {len(a_tr)}/{len(a_va)}/{len(a_te)}; churn {b_tr.mean():.3f}/{b_va.mean():.3f}/{b_te.mean():.3f}")
fitted2, vrows = {}, []
for name, m in cands.items():
    from sklearn.base import clone
    m2 = clone(m).fit(a_tr, b_tr)
    fitted2[name] = m2
    p = m2.predict_proba(a_va)[:, 1]
    vrows.append({"model": name, "val_pr_auc": average_precision_score(b_va, p), "val_roc_auc": roc_auc_score(b_va, p)})
val2 = pd.DataFrame(vrows).round(4).set_index("model")
save_table(val2, "customer_churn_validation_period2.csv")
best2 = max([n for n in val2.index if not n.startswith("dummy")], key=lambda n: val2.loc[n, "val_pr_auc"])
print(f"\nPERIOD 2 VALIDATION (prevalence {b_va.mean():.4f}); best model on validation PR-AUC: {best2}")
print(val2.to_string())
mod2 = fitted2[best2]
pv2 = mod2.predict_proba(a_va)[:, 1]
thr2 = choose_threshold(b_va, pv2, goal="f1")
pt2 = mod2.predict_proba(a_te)[:, 1]
st2 = scores_at(b_te, pt2, thr2)
cm2 = confusion_matrix(b_te, (pt2 >= thr2).astype(int))
boots2 = []
for _ in range(2000):
    i = rng2.integers(0, len(b_te), len(b_te))
    if b_te.values[i].sum() == 0:
        continue
    boots2.append([average_precision_score(b_te.values[i], pt2[i]), roc_auc_score(b_te.values[i], pt2[i])])
ci2 = np.percentile(boots2, [2.5, 97.5], axis=0)
sv2 = scores_at(b_va, pv2, thr2)
log_result("churn_p2_dummy_prior", "val", {"pr_auc": round(b_va.mean(), 4), "roc_auc": 0.5}, "period 2 (Jan-Mar features, Apr-May label); no skill")
log_result(f"churn_p2_{best2}", "val", {k_: round(v, 4) for k_, v in sv2.items()}, f"period 2; threshold {thr2:.4f} chosen on val (max F1)")
log_result(f"churn_p2_{best2}", "test", {k_: round(v, 4) for k_, v in st2.items()}, f"period 2; threshold {thr2:.4f}; test scored once")
log_result("churn_p2_dummy_prior", "test", {"pr_auc": round(b_te.mean(), 4), "roc_auc": 0.5}, "period 2; no skill")
print(f"\nPERIOD 2 TEST (scored once; {len(b_te)} customers, {b_te.sum()} churners, prevalence {b_te.mean():.4f}) model {best2}, threshold {thr2:.4f}")
print(f"  PR-AUC {st2['pr_auc']:.4f} (95% bootstrap CI {ci2[0, 0]:.3f}-{ci2[1, 0]:.3f}) vs no-skill {b_te.mean():.4f}")
print(f"  ROC-AUC {st2['roc_auc']:.4f} (95% bootstrap CI {ci2[0, 1]:.3f}-{ci2[1, 1]:.3f}) vs 0.5")
print(f"  precision {st2['precision']:.3f}, recall {st2['recall']:.3f}, flagged {st2['flag_rate']:.3f}; confusion [[TN FP],[FN TP]]:\n{cm2}")
beats2 = ci2[0, 0] > b_te.mean() and ci2[0, 1] > 0.5
print(f"  clearly beats baseline (same rule as period 1)? {'yes' if beats2 else 'NO'}")
# noise reference on this validation set, as for period 1
noise2 = np.array([average_precision_score(b_va, rng2.random(len(b_va))) for _ in range(2000)])
print(f"  noise reference on validation: random scores give PR-AUC mean {noise2.mean():.4f}, 95th percentile {np.percentile(noise2, 95):.4f}")
# steady-rate reference for period 2. RETROSPECTIVE: it uses the growth of daily transactions inside the label window, which is
# not known at the cut-off, so it explains the label after the fact and is not a usable forecast.
g2 = tx_day[(tx_day.index >= CUT2) & (tx_day.index <= LABEL_END2)].mean() / tx_day[tx_day.index < CUT2].mean()
exp2 = np.exp(-(X2.visits / ((CUT2 - d.date.min()).days)) * 61 * g2)
print(f"  steady-rate reference (RETROSPECTIVE: uses growth x{g2:.2f} measured inside the label window): expected churn {exp2.mean():.1%}, observed {y2.mean():.1%}")

per = pd.DataFrame([
    {"period": "1: features Jan-Apr, label May-Jun", "customers": len(X), "churn_rate": y.mean(), "test_customers": len(y_te), "test_churners": int(y_te.sum()),
     "model": best, "val_pr_auc": val.loc[best, "val_pr_auc"], "test_pr_auc": st["pr_auc"], "test_pr_auc_ci_low": ci[0, 0], "test_pr_auc_ci_high": ci[1, 0],
     "no_skill_pr_auc": y_te.mean(), "test_roc_auc": st["roc_auc"], "test_roc_ci_low": ci[0, 1], "test_roc_ci_high": ci[1, 1],
     "precision": st["precision"], "recall": st["recall"], "flag_rate": st["flag_rate"], "clearly_beats_baseline": bool(beats),
     "steady_rate_expected_churn_retrospective": exp_churn.mean()},
    {"period": "2: features Jan-Mar, label Apr-May", "customers": len(X2), "churn_rate": y2.mean(), "test_customers": len(b_te), "test_churners": int(b_te.sum()),
     "model": best2, "val_pr_auc": val2.loc[best2, "val_pr_auc"], "test_pr_auc": st2["pr_auc"], "test_pr_auc_ci_low": ci2[0, 0], "test_pr_auc_ci_high": ci2[1, 0],
     "no_skill_pr_auc": b_te.mean(), "test_roc_auc": st2["roc_auc"], "test_roc_ci_low": ci2[0, 1], "test_roc_ci_high": ci2[1, 1],
     "precision": st2["precision"], "recall": st2["recall"], "flag_rate": st2["flag_rate"], "clearly_beats_baseline": bool(beats2),
     "steady_rate_expected_churn_retrospective": exp2.mean()}]).round(4)
save_table(per, "customer_churn_periods.csv", index=False)
print("\nPERIOD COMPARISON\n", per.T.to_string(header=False))
