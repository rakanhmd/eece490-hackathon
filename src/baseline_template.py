"""Baseline vs models on a tabular CSV.

Usage:
    python src/baseline_template.py --csv data/train.csv --target label
    python src/baseline_template.py --demo        # dry run on a built-in dataset
Add --task regression for regression targets.
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (SEED, choose_threshold, eval_classifier, eval_regressor,  # noqa: E402
                    log_result, split_train_val_test)


def make_pre(X):
    num = X.select_dtypes(include="number").columns.tolist()
    cat = X.select_dtypes(exclude="number").columns.tolist()
    return ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num),
        ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                          ("oh", OneHotEncoder(handle_unknown="ignore"))]), cat),
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv"); ap.add_argument("--target")
    ap.add_argument("--task", choices=["classification", "regression"], default="classification")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()

    if a.demo:
        from sklearn.datasets import load_breast_cancer
        d = load_breast_cancer(as_frame=True)
        X, y = d.data, d.target
    else:
        df = pd.read_csv(a.csv)
        X, y = df.drop(columns=[a.target]), df[a.target]

    clf = a.task == "classification"
    X_tr, X_va, X_te, y_tr, y_va, y_te = split_train_val_test(X, y, stratify=clf)
    print(f"train {len(X_tr)} | val {len(X_va)} | test {len(X_te)}")

    if clf:
        models = {"dummy": DummyClassifier(strategy="most_frequent"),
                  "logreg": LogisticRegression(max_iter=2000, class_weight="balanced"),
                  "hgb": HistGradientBoostingClassifier(random_state=SEED)}
    else:
        models = {"dummy": DummyRegressor(), "ridge": Ridge(alpha=1.0),
                  "hgb": HistGradientBoostingRegressor(random_state=SEED)}

    best_name, best_score, best_pipe = None, -np.inf, None
    for name, m in models.items():
        pipe = Pipeline([("pre", make_pre(X_tr)), ("model", m)]).fit(X_tr, y_tr)
        pred = pipe.predict(X_va)
        if clf:
            binary = y.nunique() == 2
            score = pipe.predict_proba(X_va)[:, 1] if binary else None
            s = eval_classifier(y_va, pred, score)
            key = s.get("f1", s["f1_macro"])
        else:
            s = eval_regressor(y_va, pred)
            key = -s["rmse"]
        log_result(name, "val", s)
        print(name, s)
        if key > best_score:
            best_name, best_score, best_pipe = name, key, pipe

    # Final: threshold on validation (binary only), then test exactly once.
    if clf and y.nunique() == 2:
        t = choose_threshold(y_va, best_pipe.predict_proba(X_va)[:, 1])
        p_te = best_pipe.predict_proba(X_te)[:, 1]
        s = eval_classifier(y_te, (p_te >= t).astype(int), p_te)
        log_result(best_name, "test", s, notes=f"threshold={t:.3f} chosen on val")
    elif clf:
        s = eval_classifier(y_te, best_pipe.predict(X_te))
        log_result(best_name, "test", s)
    else:
        s = eval_regressor(y_te, best_pipe.predict(X_te))
        log_result(best_name, "test", s)
    print("TEST", best_name, s)


if __name__ == "__main__":
    main()
