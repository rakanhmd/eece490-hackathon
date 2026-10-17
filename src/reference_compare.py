"""How our data compares with public coffee/bakery transaction datasets (reference only, never a cause).

Reference datasets (downloaded with the Kaggle API into data/external/reference/, gitignored; only summary
tables are committed). Source, license and real/fictional claim are recorded in data/README.md.
  maven    ahmedabbas757/coffee-sales            Maven Roasters, 3 NYC stores, Jan-Jun 2023 (self-described FICTITIOUS)
  bakery   matthieugimbert/french-bakery-daily-sales  one French bakery, 2021-01-02 to 2022-09-30 (claims real)
  vending  ihelon/coffee-sales                    one coffee vending machine, Mar 2024 to Mar 2025 (claims real)

1. Signatures for every dataset: Tuesday ratio, busiest weekday, peak hour, overdispersion, basket size,
   top-category share.
2. Template check: does our data look derived from the Maven dataset?
3. Effect-size transfer: weather and holiday effects in the (real) bakery, compared with the 95% CIs we
   measured in our own data (src/external_factors.py). ASSUMPTION: the bakery is in Paris (the dataset names no
   city); weather from Open-Meteo for Paris, holidays from the French government API.
Run after external_factors.py (it reads that script's result tables).
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import ROOT, SEED, save_fig
from load import REV, load_clean, save_table

rng = np.random.default_rng(SEED)
REF = os.path.join(ROOT, "data", "external", "reference")
EXT = os.path.join(ROOT, "data", "external")
RES = os.path.join(ROOT, "results")
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# ---------------------------------------------------------------- load into one line-level format
# columns: date (Timestamp, day), hour (int), basket (id), store, category, qty, revenue
def load_ours():
    d = load_clean(verbose=False)
    return pd.DataFrame({"date": d.date, "hour": d.hour, "basket": d["Transaction ID"], "store": d.Branch,
                         "category": d.Category, "qty": d.Quantity, "revenue": d[REV], "product": d.Product,
                         "price": d["Unit Price (USD)"]})


def load_maven():
    p = os.path.join(REF, "ahmedabbas757_coffee-sales", "Coffee Shop Sales.xlsx")
    m = pd.read_excel(p)
    t = pd.to_datetime(m.transaction_time.astype(str), format="%H:%M:%S")
    return pd.DataFrame({"date": pd.to_datetime(m.transaction_date).dt.normalize(), "hour": t.dt.hour,
                         "basket": m.transaction_id, "store": m.store_location, "category": m.product_category,
                         "qty": m.transaction_qty, "revenue": m.transaction_qty * m.unit_price,
                         "product": m.product_detail, "price": m.unit_price})


def load_bakery():
    p = os.path.join(REF, "matthieugimbert_french-bakery-daily-sales", "Bakery sales.csv")
    b = pd.read_csv(p)
    b = b[b.Quantity > 0]                                   # drop returns / corrections
    price = b.unit_price.str.replace("€", "", regex=False).str.replace(",", ".").str.strip().astype(float)
    return pd.DataFrame({"date": pd.to_datetime(b.date), "hour": pd.to_datetime(b.time, format="%H:%M").dt.hour,
                         "basket": b.date + "_" + b.ticket_number.astype(int).astype(str), "store": "bakery",
                         "category": b.article, "qty": b.Quantity, "revenue": b.Quantity * price,
                         "product": b.article, "price": price})


def load_vending():
    p = os.path.join(REF, "ihelon_coffee-sales", "index_1.csv")
    v = pd.read_csv(p)
    dt = pd.to_datetime(v.datetime, format="mixed")
    return pd.DataFrame({"date": dt.dt.normalize(), "hour": dt.dt.hour, "basket": np.arange(len(v)),
                         "store": "machine", "category": v.coffee_name, "qty": 1.0, "revenue": v.money,
                         "product": v.coffee_name, "price": v.money})


loaders = {"Stories (ours)": load_ours, "Maven (fictitious, NYC)": load_maven,
           "French bakery (real)": load_bakery, "Vending machine (real)": load_vending}
data, skipped = {}, []
for name, f in loaders.items():
    try:
        data[name] = f()
        x = data[name]
        print(f"{name}: {len(x):,} lines, {x.basket.nunique():,} baskets, {x.date.min().date()} to {x.date.max().date()}, "
              f"{x.store.nunique()} store(s)")
    except Exception as e:  # a missing or malformed download is skipped, not fatal
        skipped.append(f"{name}: {type(e).__name__}: {e}")
        print("SKIPPED", skipped[-1])


# ---------------------------------------------------------------- 1. signatures
def daily_tx(x):
    """Transactions per store per observed day (days with no sales at a store are treated as closed)."""
    return x.groupby(["store", "date"]).basket.nunique().rename("tx").reset_index()


def dispersion(x, n_sim=500):
    """Pearson variance/mean of daily transactions after store x weekday x year-month cell means,
    plus the 2.5-97.5% range of the same statistic on Poisson counts with those means."""
    t = daily_tx(x)
    t["cell"] = t.store + "_" + t.date.dt.dayofweek.astype(str) + "_" + t.date.dt.to_period("M").astype(str)
    mu = t.groupby("cell").tx.transform("mean")
    dof = len(t) - t.cell.nunique()
    obs = ((t.tx - mu) ** 2 / mu).sum() / dof
    sims = []
    for _ in range(n_sim):
        ys = rng.poisson(mu.values)
        ms = pd.Series(ys).groupby(t.cell.values).transform("mean").values
        sims.append(((ys - ms) ** 2 / np.where(ms > 0, ms, 1)).sum() / dof)
    return obs, np.percentile(sims, 2.5), np.percentile(sims, 97.5)


sig_rows, wd_profiles, hour_profiles = [], {}, {}
for name, x in data.items():
    t = daily_tx(x)
    per_wd = t.groupby(t.date.dt.dayofweek).tx.mean().reindex(range(7))      # mean per open store-day
    open_days = per_wd.dropna().index.tolist()
    comp = per_wd.reindex([0, 2, 3, 4]).dropna()
    mon_fri = per_wd.reindex(range(5)).dropna()
    hours = x.drop_duplicates("basket").hour.value_counts(normalize=True).sort_index()
    basket = x.groupby("basket").agg(items=("qty", "sum"), lines=("category", "size"))
    cat = x.groupby("category").qty.sum().sort_values(ascending=False) / x.qty.sum()
    disp, plo, phi = dispersion(x)
    first, last = x.date.dt.to_period("M").min(), x.date.dt.to_period("M").max()
    sig_rows.append({
        "dataset": name, "stores": x.store.nunique(), "days": x.date.nunique(),
        "closed_weekdays": ",".join(DAYS[i] for i in range(7) if i not in open_days) or "none",
        "tx_per_store_day": t.tx.mean(),
        "tue_ratio_vs_mon_wed_thu_fri": per_wd[1] / comp.mean() if not np.isnan(per_wd[1]) else np.nan,
        "busiest_weekday": DAYS[int(per_wd.idxmax())], "busiest_vs_mon_fri_avg": per_wd.max() / mon_fri.mean(),
        "peak_hour": int(hours.idxmax()), "peak_hour_share": hours.max(),
        "dispersion_ratio": disp, "poisson_range_low": plo, "poisson_range_high": phi,
        "items_per_basket": basket["items"].mean(), "lines_per_basket": basket["lines"].mean(),
        "top_category": cat.index[0], "top_category_share": cat.iloc[0], "top3_category_share": cat.iloc[:3].sum(),
        "n_categories": x.category.nunique()})
    wd_profiles[name] = per_wd / mon_fri.mean()
    hour_profiles[name] = hours
sig = pd.DataFrame(sig_rows)
pd.set_option("display.width", 250)
print("\n1. Signatures:\n", sig.round(3).T)
save_table(sig.round(4), "reference_signatures.csv", index=False)

# ---------------------------------------------------------------- 2. template check vs Maven
tmpl = None
if "Maven (fictitious, NYC)" in data:
    o, m = data["Stories (ours)"], data["Maven (fictitious, NYC)"]

    def month_growth(x):
        mt = x.groupby(x.date.dt.month).basket.nunique()
        return mt.iloc[-1] / mt.iloc[0]

    ho, hm = hour_profiles["Stories (ours)"], hour_profiles["Maven (fictitious, NYC)"]
    hh = pd.concat([ho, hm], axis=1).fillna(0)
    prod_overlap = len(set(o["product"].str.lower()) & set(m["product"].astype(str).str.lower()))
    cat_overlap = sorted(set(o.category) & set(m.category))
    so, sm = sig.set_index("dataset").loc["Stories (ours)"], sig.set_index("dataset").loc["Maven (fictitious, NYC)"]
    tmpl = pd.DataFrame([
        ["Date span", f"{o.date.min().date()} to {o.date.max().date()}", f"{m.date.min().date()} to {m.date.max().date()}"],
        ["Stores", str(o.store.nunique()), str(m.store.nunique())],
        ["Categories", str(o.category.nunique()), str(m.category.nunique())],
        ["Category names in common", str(len(cat_overlap)) + (f" ({', '.join(cat_overlap)})" if cat_overlap else ""), ""],
        ["Products", str(o["product"].nunique()), str(m["product"].nunique())],
        ["Product names in common (exact, case-insensitive)", str(prod_overlap), ""],
        ["Median unit price (USD)", f"{o.price.median():.2f}", f"{m.price.median():.2f}"],
        ["Unit price range (USD)", f"{o.price.min():.2f}-{o.price.max():.2f}", f"{m.price.min():.2f}-{m.price.max():.2f}"],
        ["Quantity values", ",".join(map(str, sorted(o.qty.unique().astype(int)))), ",".join(map(str, sorted(m.qty.unique().astype(int))))],
        ["Lines per transaction", f"{so.lines_per_basket:.2f}", f"{sm.lines_per_basket:.2f}"],
        ["Transactions per store per day", f"{so.tx_per_store_day:.1f}", f"{sm.tx_per_store_day:.1f}"],
        ["Transactions, last month / first month", f"{month_growth(o):.2f}", f"{month_growth(m):.2f}"],
        ["Peak hour", f"{int(so.peak_hour)}:00", f"{int(sm.peak_hour)}:00"],
        ["Correlation of hourly profiles", f"{np.corrcoef(hh.iloc[:, 0], hh.iloc[:, 1])[0, 1]:.2f}", ""],
        ["Busiest weekday (ratio to Mon-Fri average)", f"{so.busiest_weekday} ({so.busiest_vs_mon_fri_avg:.2f})",
         f"{sm.busiest_weekday} ({sm.busiest_vs_mon_fri_avg:.2f})"],
        ["Tuesday / Mon, Wed, Thu, Fri", f"{so.tue_ratio_vs_mon_wed_thu_fri:.2f}", f"{sm.tue_ratio_vs_mon_wed_thu_fri:.2f}"],
        ["Dispersion ratio (Poisson about 1)", f"{so.dispersion_ratio:.2f}", f"{sm.dispersion_ratio:.2f}"],
        ["Customer IDs", "yes (63% of transactions)", "no"],
    ], columns=["feature", "stories", "maven"])
    print("\n2. Template check vs Maven:\n", tmpl.to_string(index=False))
    save_table(tmpl, "reference_template_maven.csv", index=False)

# ---------------------------------------------------------------- 3. effect-size transfer (bakery)
transfer = None
if "French bakery (real)" in data:
    b = data["French bakery (real)"]
    bt = b.groupby("date").basket.nunique().rename("tx").to_frame()
    w = pd.read_csv(os.path.join(EXT, "weather_paris_2021_2022.csv"), skiprows=3)
    w.columns = ["date", "tmax", "precip"]
    w["date"] = pd.to_datetime(w.date)
    hol = pd.read_csv(os.path.join(EXT, "france_holidays_2021_2022.csv"), parse_dates=["date"])
    bt = bt.join(w.set_index("date"), how="left")
    bt["rain_day"] = (bt.precip >= 1.0).astype(float)
    bt["holiday"] = bt.index.isin(hol.date).astype(float)
    bt = bt.dropna()
    bt["y"] = np.log(bt.tx)
    bt["t"] = (bt.index - bt.index[0]).days / 30.0

    def fit(df, month_fe):
        parts = [pd.get_dummies(df.index.dayofweek, prefix="wd", dtype=float).set_index(df.index), df[["t"]]]
        if month_fe:
            parts.append(pd.get_dummies(df.index.to_period("M").astype(str), prefix="m", drop_first=True,
                                        dtype=float).set_index(df.index))
        X = pd.concat(parts + [df[["tmax", "rain_day", "holiday"]]], axis=1)
        beta, *_ = np.linalg.lstsq(X.values, df.y.values, rcond=None)
        resid = df.y.values - X.values @ beta
        s2 = resid @ resid / (len(df) - np.linalg.matrix_rank(X.values))
        se = np.sqrt(np.diag(s2 * np.linalg.pinv(X.values.T @ X.values)))
        return {k: (beta[-3 + i], se[-3 + i]) for i, k in enumerate(["tmax", "rain_day", "holiday"])}

    ours_w = pd.read_csv(os.path.join(RES, "external_weather_coefficients.csv")).set_index("term")
    ours_g = pd.read_csv(os.path.join(RES, "external_weather_growth.csv")).iloc[0]
    ours_h = pd.read_csv(os.path.join(RES, "external_holidays_summary.csv")).iloc[0]
    ours = {  # (estimate %, CI low %, CI high %)
        ("tmax", False): (ours_w.loc["tmax", "effect_pct"], ours_w.loc["tmax", "effect_ci_low_pct"], ours_w.loc["tmax", "effect_ci_high_pct"]),
        ("rain_day", False): (ours_w.loc["rain_day", "effect_pct"], ours_w.loc["rain_day", "effect_ci_low_pct"], ours_w.loc["rain_day", "effect_ci_high_pct"]),
        ("tmax", True): (ours_g.within_month_tmax_coef_pct_per_degC, ours_g.within_month_tmax_ci_low, ours_g.within_month_tmax_ci_high),
        ("holiday", False): (100 * (ours_h.mean_ratio - 1), 100 * (ours_h.ci_low - 1), 100 * (ours_h.ci_high - 1)),
    }
    rows = []
    for month_fe, spec in [(False, "weekday + trend + weather + holiday"), (True, "same + month fixed effects")]:
        r = fit(bt, month_fe)
        for term, label in [("tmax", "per 1 degC of daily max temperature"), ("rain_day", "rain day (1 mm or more)"),
                            ("holiday", "public holiday")]:
            est, se = r[term]
            ref = 100 * (np.exp(est) - 1)
            lo, hi = 100 * (np.exp(est - 1.96 * se) - 1), 100 * (np.exp(est + 1.96 * se) - 1)
            o = ours.get((term, month_fe))
            rows.append({"spec": spec, "effect": label, "bakery_pct": ref, "bakery_ci_low": lo, "bakery_ci_high": hi,
                         "ours_pct": o[0] if o else np.nan, "ours_ci_low": o[1] if o else np.nan,
                         "ours_ci_high": o[2] if o else np.nan,
                         "bakery_effect_outside_our_ci": (bool(ref < o[1] or ref > o[2]) if o else None)})
    transfer = pd.DataFrame(rows)
    print(f"\n3. Effect-size transfer: bakery {len(bt)} open days, Paris weather assumed")
    print(transfer.round(3).to_string(index=False))
    save_table(transfer.round(4), "reference_effect_transfer.csv", index=False)

if skipped:
    save_table(pd.DataFrame({"skipped": skipped}), "reference_skipped.csv", index=False)

# ---------------------------------------------------------------- figure
fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
colors = {"Stories (ours)": "#c0392b", "Maven (fictitious, NYC)": "#7f8c8d",
          "French bakery (real)": "#2c3e50", "Vending machine (real)": "#27ae60"}
for name, prof in wd_profiles.items():
    axes[0].plot(range(7), prof.values, "o-", color=colors[name], label=name, lw=2.2 if "ours" in name else 1.3)
axes[0].axhline(1, color="grey", ls="--", lw=0.8)
axes[0].set_xticks(range(7), DAYS)
axes[0].set_title("Transactions per day, relative to Mon-Fri average")
axes[0].set_xlabel("Weekday")
axes[0].set_ylabel("Ratio (gaps = closed)")
axes[0].legend(fontsize=8)
for name, prof in hour_profiles.items():
    axes[1].plot(prof.index, 100 * prof.values, color=colors[name], label=name, lw=2.2 if "ours" in name else 1.3)
axes[1].set_title("Share of transactions by hour")
axes[1].set_xlabel("Hour of day")
axes[1].set_ylabel("% of transactions")
ys = np.arange(len(sig))
axes[2].barh(ys, sig.dispersion_ratio, color=[colors[n] for n in sig.dataset])
axes[2].errorbar((sig.poisson_range_low + sig.poisson_range_high) / 2, ys,
                 xerr=(sig.poisson_range_high - sig.poisson_range_low) / 2, fmt="none", ecolor="k", capsize=5,
                 label="pure-chance (Poisson) range")
axes[2].set_yticks(ys, sig.dataset, fontsize=8)
axes[2].axvline(1, color="grey", ls="--", lw=0.8)
axes[2].set_title("Day-to-day variation (variance / mean)")
axes[2].set_xlabel("Dispersion ratio after weekday x month")
axes[2].legend(fontsize=8)
fig.tight_layout()
save_fig(fig, "reference_signatures.png")
print("saved figures/reference_signatures.png")
