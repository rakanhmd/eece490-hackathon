"""Tuesday mechanism: who carries the Tuesday lift? (descriptive; no causal claim)

Lift = transactions on Tuesday / mean transactions on Mon, Wed, Thu, Fri, over the 25 full Mon-Sun weeks, all
branches pooled. 95% intervals: bootstrap that resamples whole weeks (all branches together), 2,000 resamples.

1. Identified (Customer ID present) vs anonymous transactions, and their difference. A members-only trigger
   (loyalty or app offer) predicts a larger lift for identified transactions than for anonymous ones.
2. Lift by customer frequency. Frequency = non-Tuesday visits. To avoid a mechanical link (the baseline days are
   part of the frequency count), frequency is measured in the other half of the weeks: customers are grouped by
   their non-Tuesday transactions in odd weeks, and their lift is measured in even weeks, and vice versa
   ("customers" then counts a customer once per half).
3. Lift by the month a customer was first seen, excluding each customer's first transaction (a first visit is
   more likely to fall on a busy Tuesday).
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import SEED, save_fig
from load import load_clean, save_table

rng = np.random.default_rng(SEED)
N_BOOT = 2000
BASE_DAYS = [0, 2, 3, 4]

d = load_clean()
tx = d.groupby("Transaction ID").agg(date=("date", "first"), cust=("Customer ID", "first"),
                                     branch=("Branch", "first")).reset_index()
tx["wd"] = tx.date.dt.dayofweek
tx["week"] = tx.date - pd.to_timedelta(tx.wd, unit="D")
first_monday = tx.date.min() + pd.Timedelta(days=(7 - tx.date.min().dayofweek) % 7)
last_sunday = tx.date.max() - pd.Timedelta(days=(tx.date.max().dayofweek + 1) % 7)
tx = tx[(tx.date >= first_monday) & (tx.date <= last_sunday)].copy()
weeks = np.array(sorted(tx.week.unique()))
wk_no = {w: i for i, w in enumerate(weeks)}
tx["wk"] = tx.week.map(wk_no)
tx["identified"] = tx.cust.notna()
print(f"{len(tx):,} transactions in {len(weeks)} full weeks; identified {tx.identified.mean():.1%}")


def week_counts(sub):
    """weeks x 2 array: Tuesday count, sum over Mon/Wed/Thu/Fri."""
    t = sub[sub.wd == 1].groupby("wk").size().reindex(range(len(weeks)), fill_value=0).values
    b = sub[sub.wd.isin(BASE_DAYS)].groupby("wk").size().reindex(range(len(weeks)), fill_value=0).values
    return np.c_[t, b]


def lift(c):
    return c[..., 0].sum(-1) / (c[..., 1].sum(-1) / 4)


DRAWS = rng.integers(0, len(weeks), size=(N_BOOT, len(weeks)))


def boot_lift(c):
    return lift(c[DRAWS])


rows = []
# ---- 1. identified vs anonymous
c_id, c_an = week_counts(tx[tx.identified]), week_counts(tx[~tx.identified])
b_id, b_an = boot_lift(c_id), boot_lift(c_an)
for name, c, b in [("identified", c_id, b_id), ("anonymous", c_an, b_an)]:
    rows.append({"analysis": "ID status", "group": name, "tuesday_tx": int(c[:, 0].sum()),
                 "baseline_tx_per_day": c[:, 1].sum() / 4, "lift": lift(c),
                 "ci_low": np.percentile(b, 2.5), "ci_high": np.percentile(b, 97.5)})
diff = lift(c_id) - lift(c_an)
rows.append({"analysis": "ID status", "group": "identified minus anonymous", "lift": diff,
             "ci_low": np.percentile(b_id - b_an, 2.5), "ci_high": np.percentile(b_id - b_an, 97.5)})
for br in sorted(tx.branch.unique()):
    s = tx[tx.branch == br]
    ci_, ca_ = week_counts(s[s.identified]), week_counts(s[~s.identified])
    bd = boot_lift(ci_) - boot_lift(ca_)
    rows.append({"analysis": "ID status by branch", "group": f"{br}: identified minus anonymous",
                 "lift": lift(ci_) - lift(ca_), "ci_low": np.percentile(bd, 2.5), "ci_high": np.percentile(bd, 97.5)})

# ---- 2. frequency segments, measured out of sample (odd vs even weeks)
idt = tx[tx.identified].copy()
idt["half"] = idt.wk % 2
SEG_BINS, SEG_LAB = [0, 1, 3, 6, np.inf], ["0", "1-2", "3-5", "6+"]
seg_counts = {lab: np.zeros((len(weeks), 2)) for lab in SEG_LAB}
seg_cust = {lab: 0 for lab in SEG_LAB}
for h in (0, 1):
    other = idt[(idt.half != h) & (idt.wd != 1)].groupby("cust").size()
    here = idt[idt.half == h].copy()
    here["freq_other_half"] = here.cust.map(other).fillna(0)
    here["seg"] = pd.cut(here.freq_other_half, SEG_BINS, right=False, labels=SEG_LAB)
    for lab in SEG_LAB:
        s = here[here.seg == lab]
        seg_counts[lab] += week_counts(s)
        seg_cust[lab] += s.cust.nunique()
for lab in SEG_LAB:
    c = seg_counts[lab]
    b = boot_lift(c)
    rows.append({"analysis": "frequency (non-Tuesday transactions in the other half of the weeks)", "group": lab,
                 "customers": seg_cust[lab], "tuesday_tx": int(c[:, 0].sum()),
                 "baseline_tx_per_day": c[:, 1].sum() / 4, "lift": lift(c),
                 "ci_low": np.percentile(b, 2.5), "ci_high": np.percentile(b, 97.5)})

# ---- 3. first-seen month (first transaction of each customer excluded)
first = idt.sort_values("date").groupby("cust").head(1)
idt["first_month"] = idt.cust.map(first.set_index("cust").date.dt.month)
rest = idt.drop(first.index)
for m in sorted(rest.first_month.unique()):
    s = rest[rest.first_month == m]
    c = week_counts(s)
    if c[:, 1].sum() < 200:
        continue
    b = boot_lift(c)
    rows.append({"analysis": "first-seen month (first transaction excluded)", "group": int(m),
                 "customers": s.cust.nunique(), "tuesday_tx": int(c[:, 0].sum()),
                 "baseline_tx_per_day": c[:, 1].sum() / 4, "lift": lift(c),
                 "ci_low": np.percentile(b, 2.5), "ci_high": np.percentile(b, 97.5)})

res = pd.DataFrame(rows)
print(res.round(3).to_string(index=False))
save_table(res.round(4), "tuesday_mechanism.csv", index=False)

fig, ax = plt.subplots(figsize=(8, 4))
plot = res[res.analysis.str.startswith(("ID status", "frequency")) & ~res.group.astype(str).str.contains("minus")]
labels = [("ID: " if a.startswith("ID") else "freq ") + str(g) for a, g in zip(plot.analysis, plot.group)]
ax.errorbar(range(len(plot)), plot.lift, yerr=[plot.lift - plot.ci_low, plot.ci_high - plot.lift], fmt="o", capsize=4)
ax.axhline(1, color="grey", ls="--", lw=0.8)
ax.set_xticks(range(len(plot)), labels, rotation=20)
ax.set_ylabel("Tuesday / mean(Mon, Wed, Thu, Fri)")
ax.set_title("Tuesday lift by ID status and customer frequency (95% week-bootstrap CI)")
fig.tight_layout()
save_fig(fig, "tuesday_mechanism.png")
print("saved figures/tuesday_mechanism.png")
