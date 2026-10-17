"""Tuesday check: is the Tuesday surge a real demand pattern or a recording error?

Recording-error hypotheses and the test for each:
  A. Batch posting: another day's sales booked on Tuesday. -> Monday or Wednesday would be low; Tuesday
     timestamps would bunch (e.g. at one hour) or replacement IDs would be out of time order.
  B. Duplicated records: Tuesday transactions copied from elsewhere. -> near-duplicate rate (same branch,
     time to the second, same products) higher on Tuesday than on other days.
  C. A few event days (holidays, launches). -> excess would come from a handful of Tuesdays.
  D. A specific event slot (e.g. a Tuesday evening offer). -> extra traffic concentrated in some hours.
  E. Different buyers (a group, a corporate order). -> basket size, mix, order type, known-customer
     share or customer identities differ on Tuesday.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import SEED, save_fig
from load import REV, load_clean, save_table

rng = np.random.default_rng(SEED)
d = load_clean()
d["is_tue"] = d.weekday == 1
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

tx = d.groupby("Transaction ID").agg(
    date=("date", "first"), weekday=("weekday", "first"), hour=("hour", "first"), time=("Time", "first"),
    branch=("Branch", "first"), lines=("Product", "size"), qty=("Quantity", "sum"), rev=(REV, "sum"),
    known=("Customer ID", lambda s: s.notna().any()), cust=("Customer ID", "first"),
    dinein=("Order Type", lambda s: (s == "Dine-in").all()),
    products=("Product", lambda s: "|".join(sorted(s))))
tx["is_tue"] = tx.weekday == 1
out = {}

# ---- 0. size of the effect, per branch and month: transactions per calendar day ----
daily = tx.groupby(["date", "branch"]).size().unstack(fill_value=0)
daily["weekday"] = daily.index.dayofweek
per_day = daily.groupby("weekday")[["Garden", "Harbour", "Uptown"]].mean()
per_day.index = DAYS
per_day["all"] = per_day.sum(axis=1)
print("Mean transactions per calendar day:\n", per_day.round(1))
save_table(per_day.round(2), "tuesday_tx_per_day.csv")
tue_ratio = per_day.loc["Tue"] / per_day.drop(["Tue"]).loc[["Mon", "Wed", "Thu", "Fri"]].mean()
print("Tuesday / mean(Mon, Wed, Thu, Fri):\n", tue_ratio.round(3))

# ---- C. every week? ratio of each Tuesday to the other weekdays of the same week ----
dt = tx.groupby("date").size().to_frame("n")
dt["weekday"] = dt.index.dayofweek
dt["week"] = dt.index.to_period("W")
wk = dt.pivot_table(index="week", columns="weekday", values="n")
wk = wk.dropna()  # full weeks only
wk_ratio = wk[1] / wk[[0, 2, 3, 4]].mean(axis=1)
print(f"\nC. Full weeks: {len(wk_ratio)}; Tuesday/(Mon,Wed,Thu,Fri) per week: "
      f"min {wk_ratio.min():.2f}, median {wk_ratio.median():.2f}, max {wk_ratio.max():.2f}; "
      f"weeks with ratio < 1.2: {(wk_ratio < 1.2).sum()}")
# is Tuesday the busiest weekday in every week? compare with how often each other day 'wins'
wins = wk.idxmax(axis=1).map(dict(enumerate(DAYS))).value_counts()
print("Busiest day of the week, count of weeks:", wins.to_dict())
out["C_weeks"] = len(wk_ratio); out["C_ratio_min"] = wk_ratio.min(); out["C_ratio_median"] = wk_ratio.median()
out["C_weeks_ratio_below_1.2"] = int((wk_ratio < 1.2).sum())
save_table(wk_ratio.rename("tuesday_ratio").to_frame(), "tuesday_ratio_by_week.csv")

# ---- A. neighbours depleted? IDs in time order? ----
mon_wed = per_day.loc[["Mon", "Wed"], "all"].mean(); thu_fri = per_day.loc[["Thu", "Fri"], "all"].mean()
print(f"\nA. Mon/Wed mean {mon_wed:.1f} vs Thu/Fri mean {thu_fri:.1f} transactions/day "
      f"(if Tuesday absorbed a neighbour's sales, Mon or Wed would be lower)")
tx["id_num"] = tx.index.str.replace("SYN-", "").astype(int)
tx["ts"] = pd.to_datetime(tx.date.dt.strftime("%Y-%m-%d") + " " + tx.time)
srt = tx.sort_values("id_num")
date_inv = int((srt.date.diff() < pd.Timedelta(0)).sum())
time_inv = int((srt.ts.diff() < pd.Timedelta(0)).sum())
print(f"   IDs sorted: date goes backwards {date_inv} times; timestamp goes backwards {time_inv} of {len(srt)} "
      f"(IDs follow the date exactly but are in random order within a day)")
out["A_id_date_inversions"] = date_inv; out["A_id_time_inversions"] = time_inv
# do Tuesday transactions bunch at particular seconds/minutes? (batch imports often share timestamps)
same_ts = tx.groupby(["branch", "date", "time"]).size()
share_shared = lambda m: (same_ts[same_ts.index.get_level_values("date").dayofweek.isin(m)] > 1).mean()
print(f"   share of (branch, date, second) slots with >1 transaction: Tue {share_shared([1]):.4f}, "
      f"other days {share_shared([0,2,3,4,5,6]):.4f}")

# ---- B. near-duplicates: same branch + time-of-day to the second + same products, on a different date ----
key = tx.branch + "_" + tx.time + "_" + tx.products
dup = key.map(key.value_counts()) > 1
print(f"\nB. Transactions whose (branch, time-of-day, products) also occurs on another date: "
      f"Tue {dup[tx.is_tue].mean():.4f}, other days {dup[~tx.is_tue].mean():.4f}")
# expected rate grows with volume, so compare with a random sample of other-day transactions of equal size
n_tue = tx.is_tue.sum()
other = tx[~tx.is_tue]
null = []
for _ in range(50):
    samp = other.sample(n_tue, random_state=int(rng.integers(1e9)))
    k2 = pd.concat([samp, other.drop(samp.index).sample(n_tue, random_state=int(rng.integers(1e9)))])
    kk = k2.branch + "_" + k2.time + "_" + k2.products
    null.append((kk.map(kk.value_counts()) > 1).mean())
kt = pd.concat([tx[tx.is_tue], other.sample(n_tue, random_state=SEED)])
kk = kt.branch + "_" + kt.time + "_" + kt.products
obs = (kk.map(kk.value_counts()) > 1).mean()
print(f"   equal-size check: Tue+random other {obs:.4f} vs two random other-day sets "
      f"{np.mean(null):.4f} (95th pct {np.percentile(null, 95):.4f})")
out["B_dup_rate_tue"] = dup[tx.is_tue].mean(); out["B_dup_rate_other"] = dup[~tx.is_tue].mean()

# ---- D. hour profile: share of each day's transactions by hour ----
prof = pd.crosstab(tx.hour, tx.is_tue, normalize="columns")
prof.columns = ["other_days", "tuesday"]
prof["diff_pts"] = 100 * (prof.tuesday - prof.other_days)
print(f"\nD. Hour shares: largest absolute difference Tuesday vs other days = "
      f"{prof.diff_pts.abs().max():.2f} pts (hour {prof.diff_pts.abs().idxmax()})")
# permutation null for the max difference: shuffle the Tuesday label across days, not transactions
days_list = tx.date.unique()
n_tue_days = tx[tx.is_tue].date.nunique()
by_day_hour = pd.crosstab(tx.date, tx.hour)
mx = []
for _ in range(500):
    pick = rng.choice(days_list, n_tue_days, replace=False)
    a = by_day_hour.loc[pick].sum(); b = by_day_hour.drop(pick).sum()
    mx.append(100 * (a / a.sum() - b / b.sum()).abs().max())
p_hour = (np.array(mx) >= prof.diff_pts.abs().max()).mean()
print(f"   permutation p-value (random sets of {n_tue_days} days): {p_hour:.3f}")
out["D_max_hour_diff_pts"] = prof.diff_pts.abs().max(); out["D_perm_p"] = p_hour
save_table(prof.round(4), "tuesday_hour_profile.csv")

# ---- E. who buys: basket, mix, order type, customer identity ----
comp = pd.DataFrame({
    "tuesday": [tx[tx.is_tue][c].mean() for c in ["lines", "qty", "rev", "known", "dinein"]],
    "other_days": [tx[~tx.is_tue][c].mean() for c in ["lines", "qty", "rev", "known", "dinein"]],
}, index=["lines_per_tx", "qty_per_tx", "revenue_per_tx", "known_customer_share", "dinein_share"])
mix = pd.crosstab(d.Category, d.is_tue, normalize="columns")
comp.loc["max_category_share_diff_pts"] = [100 * (mix[True] - mix[False]).abs().max(), 0]
k = tx[tx.known]
cust_tue_share = k.groupby("cust").is_tue.mean()
comp.loc["known_customers_buying_on_tuesday_share"] = [(cust_tue_share > 0).mean(), np.nan]
comp.loc["customers_with_over_half_visits_on_tue"] = [(cust_tue_share > 0.5).mean(), np.nan]
print("\nE. Tuesday vs other days:\n", comp.round(4))
save_table(comp.round(4), "tuesday_who_buys.csv")
# is Tuesday extra driven by new IDs? share of known Tuesday transactions from customers seen on other days
seen_other = set(k[~k.is_tue].cust)
print(f"   known Tuesday transactions by customers who also buy on other days: "
      f"{k[k.is_tue].cust.isin(seen_other).mean():.3f}")

save_table(pd.Series(out).to_frame("value"), "tuesday_tests_summary.csv")

# ---- F. is Tuesday a discount day, or new customers? ----
tx_f = d.groupby("Transaction ID").agg(is_tue=("is_tue", "first"),
                                       discounted=("Discount Rate", lambda s: (s > 0).any()),
                                       identified=("Customer ID", lambda s: s.notna().any()),
                                       order_type=("Order Type", "first"))
f = pd.DataFrame({
    "tuesday": [tx_f[tx_f.is_tue].discounted.mean(), tx_f[tx_f.is_tue].identified.mean(),
                (tx_f[tx_f.is_tue].order_type == "Dine-in").mean(), (tx_f[tx_f.is_tue].order_type == "Takeaway").mean()],
    "other_days": [tx_f[~tx_f.is_tue].discounted.mean(), tx_f[~tx_f.is_tue].identified.mean(),
                   (tx_f[~tx_f.is_tue].order_type == "Dine-in").mean(), (tx_f[~tx_f.is_tue].order_type == "Takeaway").mean()],
}, index=["share_of_transactions_with_a_discount", "identified_customer_share", "dine_in_share", "takeaway_share"])
print("\nF. Discount, identified customers and order type, Tuesday vs other days:\n", f.round(4))
save_table(f.round(4), "tuesday_discount_customer_mix.csv")

# regulars: how often identified customers come back and use several branches
kc = d.dropna(subset=["Customer ID"])
ct = kc.groupby("Transaction ID").agg(c=("Customer ID", "first"), date=("date", "first"), b=("Branch", "first"))
g = ct.groupby("c")
reg = pd.DataFrame({
    "identified_customers": [g.ngroups],
    "share_with_more_than_one_purchase": [(g.size() > 1).mean()],
    "share_returning_within_30_days_of_first_visit": [g.date.apply(lambda s: (s.sort_values().diff().dt.days.dropna() <= 30).any()).mean()],
    "share_using_more_than_one_branch": [(g.b.nunique() > 1).mean()],
    "median_purchases_per_customer": [g.size().median()]})
print("\nRegular customers:\n", reg.round(4).T)
save_table(reg.round(4), "customer_regulars.csv", index=False)

# ---- figure ----
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
per_day[["Garden", "Harbour", "Uptown"]].plot.bar(ax=axes[0], color=["#7f8c8d", "#c0392b", "#2c3e50"])
axes[0].set_title("Mean transactions per day, by weekday")
axes[0].set_xlabel("Weekday"); axes[0].set_ylabel("Transactions per day")
axes[1].plot(wk_ratio.index.to_timestamp(), wk_ratio.values, marker="o", color="#c0392b")
axes[1].axhline(1, color="grey", ls="--", lw=1)
axes[1].set_title("Each week: Tuesday / mean(Mon, Wed, Thu, Fri)")
axes[1].set_xlabel("Week"); axes[1].set_ylabel("Ratio"); axes[1].set_ylim(0, None)
save_fig(fig, "tuesday_check.png")
print("saved figures/tuesday_check.png")
