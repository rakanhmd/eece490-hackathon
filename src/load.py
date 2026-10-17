"""Load the Stories transactions file, drop exact duplicates, add date/time helper columns."""
from __future__ import annotations

import os

import pandas as pd

from common import ROOT

DATA = os.path.join(ROOT, "data", "stories_transactions.csv")
RESULTS_DIR = os.path.join(ROOT, "results")

REV = "Line Revenue (USD)"
GP = "Line Gross Profit (USD)"


def load_clean(verbose: bool = True) -> pd.DataFrame:
    raw = pd.read_csv(DATA)
    d = raw.drop_duplicates().reset_index(drop=True)
    if verbose:
        print(f"loaded {len(raw):,} lines, removed {len(raw) - len(d):,} exact duplicates -> {len(d):,}")
    d["date"] = pd.to_datetime(d["Date"])
    d["hour"] = pd.to_datetime(d["Time"], format="%H:%M:%S").dt.hour
    d["weekday"] = d["date"].dt.dayofweek          # 0 = Monday
    d["month"] = d["date"].dt.month
    d["week_start"] = d["date"] - pd.to_timedelta(d["weekday"], unit="D")
    d["list_revenue"] = d["Quantity"] * d["Unit Price (USD)"]
    d["discount_usd"] = d["list_revenue"] - d[REV]
    d["cost"] = d["Quantity"] * d["Unit Cost (USD)"]
    return d


def save_table(df: pd.DataFrame, name: str, index: bool = True) -> str:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, name)
    df.to_csv(path, index=index)
    return path
