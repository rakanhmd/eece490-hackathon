"""Shared helpers: seed, splits, evaluation, threshold choice, results log."""
from __future__ import annotations

import os
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn import metrics as M

SEED = 42
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_CSV = os.path.join(ROOT, "results", "results.csv")
FIG_DIR = os.path.join(ROOT, "figures")


# ---------- splits ----------
def split_train_val_test(X, y, val=0.15, test=0.15, stratify=True, seed=SEED):
    """Random 70/15/15 split (stratified for classification)."""
    strat = y if stratify else None
    X_tr, X_tmp, y_tr, y_tmp = train_test_split(
        X, y, test_size=val + test, stratify=strat, random_state=seed)
    strat2 = y_tmp if stratify else None
    X_va, X_te, y_va, y_te = train_test_split(
        X_tmp, y_tmp, test_size=test / (val + test), stratify=strat2, random_state=seed)
    return X_tr, X_va, X_te, y_tr, y_va, y_te


def split_by_time(df: pd.DataFrame, time_col: str, val=0.15, test=0.15):
    """Chronological split: oldest -> train, then val, newest -> test. No shuffling."""
    d = df.sort_values(time_col).reset_index(drop=True)
    n = len(d)
    i1, i2 = int(n * (1 - val - test)), int(n * (1 - test))
    return d.iloc[:i1], d.iloc[i1:i2], d.iloc[i2:]


# ---------- evaluation ----------
def eval_classifier(y_true, y_pred, y_score=None) -> dict:
    """Metrics for binary or multiclass. y_score = P(positive) for binary."""
    out = {"accuracy": M.accuracy_score(y_true, y_pred),
           "f1_macro": M.f1_score(y_true, y_pred, average="macro")}
    if len(np.unique(y_true)) == 2:
        out["precision"] = M.precision_score(y_true, y_pred, zero_division=0)
        out["recall"] = M.recall_score(y_true, y_pred, zero_division=0)
        out["f1"] = M.f1_score(y_true, y_pred, zero_division=0)
        if y_score is not None:
            out["roc_auc"] = M.roc_auc_score(y_true, y_score)
            out["pr_auc"] = M.average_precision_score(y_true, y_score)
    return {k: round(float(v), 4) for k, v in out.items()}


def eval_regressor(y_true, y_pred) -> dict:
    out = {"mae": M.mean_absolute_error(y_true, y_pred),
           "rmse": float(np.sqrt(M.mean_squared_error(y_true, y_pred))),
           "r2": M.r2_score(y_true, y_pred)}
    return {k: round(float(v), 4) for k, v in out.items()}


def choose_threshold(y_val, p_val, goal="f1", min_recall=None):
    """Pick a decision threshold on VALIDATION data.
    goal="f1": maximize F1.  min_recall=0.9: highest threshold keeping recall >= 0.9."""
    prec, rec, thr = M.precision_recall_curve(y_val, p_val)
    prec, rec = prec[:-1], rec[:-1]
    if min_recall is not None:
        ok = np.where(rec >= min_recall)[0]
        return float(thr[ok[-1]]) if len(ok) else 0.5
    f1 = 2 * prec * rec / (prec + rec + 1e-12)
    return float(thr[int(np.argmax(f1))])


# ---------- results log ----------
def log_result(model: str, split: str, scores: dict, notes: str = "") -> pd.DataFrame:
    """Append one row to results/results.csv and return the full table."""
    os.makedirs(os.path.dirname(RESULTS_CSV), exist_ok=True)
    row = {"time": datetime.now().strftime("%H:%M"), "model": model, "split": split,
           **scores, "notes": notes}
    df = pd.read_csv(RESULTS_CSV) if os.path.exists(RESULTS_CSV) else pd.DataFrame()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(RESULTS_CSV, index=False)
    return df


def save_fig(fig, name: str):
    os.makedirs(FIG_DIR, exist_ok=True)
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    return path
