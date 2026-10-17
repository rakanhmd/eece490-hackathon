"""Customer churn model, RFM segments and a win-back plan (known-ID customers only).

Setup: features come ONLY from transactions before 2026-05-01 (Jan-Apr). Label = the customer made no purchase in
May-Jun. Customers are split 70/15/15 (stratified on the label, SEED) before any fitting; imputers/scalers live inside
Pipelines; models and the threshold are chosen on validation; the test set is scored once, for the chosen model
and the dummy baseline only.
Caveat from Finding 1: customer IDs are unreliable (94% of known customers appear at several branches), so "churn" here is
"this ID stopped appearing", which may not be one real person.
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
def build_features(h: pd.DataFrame) -> pd.DataFrame:
    assert h.date.max() < CUT, "leakage: feature input contains May-Jun rows"
    last_day = CUT - pd.Timedelta(days=1)
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
        "visits_in_april": tx[tx.date >= "2026-04-01"].groupby("Customer ID").size().reindex(g.size().index, fill_value=0),
        "share_discounted_visits": g.disc.mean(),
        "share_dine_in": g.dinein.mean(),
        "share_weekend": tx.assign(w=tx.weekday >= 5).groupby("Customer ID").w.mean(),
        "share_evening": tx.assign(e=tx.hour >= 18).groupby("Customer ID").e.mean(),
        "share_morning": tx.assign(e=tx.hour < 11).groupby("Customer ID").e.mean(),
        "n_branches": g.branch.nunique(),
    })
    f["mean_gap_days"] = f.tenure_days / (f.visits - 1).replace(0, np.nan)   # NaN for one-visit customers (imputed in the pipeline)
    f["april_share_of_visits"] = f.visits_in_april / f.visits
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
    rate = Jan-Apr visits per day; growth = ratio of May-Jun to Jan-Apr daily transactions (all branches)."""
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
