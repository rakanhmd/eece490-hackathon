# Why is Garden's unit cost 1.43× Harbour's? Three tests

Code: [`src/garden_cost_cause.py`](src/garden_cost_cause.py) (13 s, seeded, reruns give identical tables). Tables: `results/garden_cause_*.csv`. Data: Jan–Jun 2026 transactions after removing 132 duplicates, plus daily Brent crude (FRED `DCOILBRENTEU`, downloaded to `data/external/`, which is gitignored; the weekly means we used are saved in `results/garden_cause_brent_weekly.csv`).

## Short answer
The data says the gap is a **flat multiplier of about 1.430 applied to every product, all six months**, not a delivery fee, not fuel, and not a different kind of customer. It looks like a rule in how costs are recorded (an allocation or a standard-cost factor), not like invoices. The data cannot tell an accounting rule from a real supplier surcharge. Finance's invoices can.

## Test 1: is the ratio the same everywhere?
**One fact first (measured):** each product has exactly **one** recorded unit cost per branch for the whole period. Garden's cost for a Butter Croissant is the same in January and June, in a one-unit line and a two-unit line. So the cost field is a price list, not a series of real purchases.

Ratio of Garden's unit cost to Harbour's, over the 45 products (`garden_cause_ratio_spread.csv`):

| | min | median | max | std |
|---|---|---|---|---|
| Garden / Harbour | 1.4261 | 1.4302 | 1.4386 | 0.0019 |
| Uptown / Harbour (for comparison) | 0.9524 | 0.9596 | 0.9651 | 0.0027 |

- **Every category** is the same: the nine category medians run 1.4292 to 1.4313 (`garden_cause_ratio_by_category.csv`).
- **Every month** is the same by construction, because costs never change. The only thing that moves from month to month is the mix of products sold: Garden's average cost per unit sold is 1.45–1.49 × Harbour's (`garden_cause_product_ratios.csv` and script output).
- **Rounding explains the spread.** Costs are stored in cents, so a $0.57 item's ratio can move by ±0.021 from rounding alone. All 45 products lie within their own rounding band of 1.4302. The largest outlier (English Breakfast Tea, 1.4386, the cheapest item) is inside its band.

**Fixed fee or percentage?** If Garden paid a fixed delivery fee per unit, Garden cost = Harbour cost + a constant, so cheap items would show a *higher* ratio. We fit Garden cost = intercept + slope × Harbour cost across products (bootstrap 95% intervals, `garden_cause_shape_tests.csv`):

| | Estimate | 95% interval |
|---|---|---|
| Intercept (a fixed $ per unit) | −$0.0003 | −$0.0019 to +$0.0011 |
| Slope | 1.4302 | 1.4297 to 1.4309 |

- The fixed amount per unit is zero within ±$0.002. Cheap-half items have a median ratio of 1.4298, expensive-half 1.4303. Rank correlation of the ratio with item cost is 0.11 (p = 0.47). The dollar difference grows with the item: median $0.50 for the cheaper half, $1.28 for the dearer half.
- **Verdict: the pattern matches a uniform percentage** (overhead or rent allocation, a flat supplier markup, or a branch cost factor). It does **not** match a fixed delivery fee per unit or per order. A per-order fee cannot be seen at all in this field, because the cost does not vary by order.
- Uptown is also uniform (0.960), and Garden's and Uptown's *prices* are uniform too (Garden 0.951–0.953 of Harbour's). The data looks like each branch has its own multiplier for cost and for price.

## Test 2: does it move with fuel prices?
Brent crude for Jan–Jun 2026: 124 daily prices from $61.08 to $138.21. Weekly means over the 25 full weeks we used run from $62.93 to $124.61, so fuel roughly doubled, a big signal to look for. We correlated three weekly series with weekly Brent (`garden_cause_fuel_correlation.csv`; 95% interval by Fisher's z; "changes" = week-to-week differences, to avoid two trending series looking related):

| Weekly Garden-vs-others series | Mean (std) | r with Brent | 95% CI | p | r of weekly changes (p) |
|---|---|---|---|---|---|
| Mix-neutral cost ratio (same products and quantities, priced at Harbour's cost) | 1.4300 (0.0001) | +0.48 | +0.11 to +0.74 | 0.014 | −0.04 (0.86) |
| Average cost per unit sold, Garden ÷ others | 1.464 (0.036) | −0.03 | −0.42 to +0.37 | 0.89 | −0.01 (0.97) |
| Cost of sales as a share of revenue, Garden ÷ others | 1.488 (0.020) | −0.25 | −0.59 to +0.16 | 0.22 | −0.18 (0.41) |

- The one "significant" row is not a fuel effect. The mix-neutral ratio varies by only ±0.0001 across the half year (from which products were sold that week); across the whole Brent range the fitted change is +0.0001 on a ratio of 1.43. Its week-to-week changes do not follow Brent at all (r = −0.04). With a 101% rise in Brent, a transport-cost pass-through would have moved the ratio by far more than 0.0001.
- The other two series are mix-driven and show no relation (r near zero or negative; intervals include zero). With 25 weeks we cannot rule out a moderate correlation in these two, so we rely more on the structural fact in Test 1: **the recorded cost never changes, so no fuel price could have flowed into it.** Brent doubling should have shown up in real delivery costs; it did not show up in this field.
- **Verdict: fuel or transport does not explain the gap**, and this field cannot tell us about transport cost either way, because it is not updated over time.

## Test 3: does Garden look like a different place?
Branch profiles (`garden_cause_branch_profile.csv`):

| | Garden | Harbour | Uptown |
|---|---|---|---|
| Lines per transaction | 1.511 | 1.505 | 1.501 |
| Units per transaction | 1.594 | 1.593 | 1.586 |
| List revenue per transaction | $8.97 | $9.27 | $8.74 |
| Dine-in share | 58.7% | 59.0% | 60.3% |
| Known-customer share | 63.2% | 63.7% | 63.6% |
| Cold-drink share of units | 24.0% | 24.9% | 24.1% |
| Food share of units | 45.9% | 43.9% | 45.5% |
| Median hour of purchase | 18 | 18 | 18 |
| Known customers who also bought at another branch | 98.6% | 95.5% | 98.9% |

Distance between each branch and the other two pooled (Jensen–Shannon distance; p-values from 500 shuffles of the branch labels; `garden_cause_profile_tests.csv`):

| Profile | Garden | Harbour | Uptown |
|---|---|---|---|
| Hour of day | 0.017 (p = 0.81) | 0.014 (p = 0.90) | 0.020 (p = 0.79) |
| Units per transaction | 0.007 (p = 0.71) | 0.011 (p = 0.18) | 0.011 (p = 0.49) |
| Category mix | 0.053 (p = 0.002) | 0.039 (p = 0.002) | 0.063 (p = 0.002) |

- **Hours, basket size, dine-in and known-customer shares match the other branches** (Garden's hour-profile distance to Harbour is 0.017, to Uptown 0.024, versus 0.020 between Harbour and Uptown).
- **Category mix differs a little in all three branches**, which with 50,000 lines is detectable; Garden (0.053) sits between Harbour (0.039) and Uptown (0.063) and is not the odd one out. Its cold-drink share (24.0%) is within 1 point of the others.
- **Customers overlap heavily:** 98.6% of Garden's known customers also bought at another branch, and 83% of the customer IDs that appear at Garden or Harbour appear at both (Jaccard 0.83; Garden–Uptown 0.62, Harbour–Uptown 0.65). The overlap depends on branch size, so compare with care, and Finding 1 already says customer IDs are unreliable.
- **Verdict:** nothing in this data suggests Garden serves a different neighbourhood. A "different neighbourhood, so higher costs" story is weak. This test does not show where the cost comes from, only that the sales side gives no hint of a different place.

## Most likely explanation (a hypothesis, not a finding)
**Hypothesis:** Garden's unit cost is Harbour's cost × a flat factor of about 1.43 set at branch level. It is a standard-cost or allocation rule (for example an overhead or rent loading booked into product cost) or a flat percentage surcharge on a supplier price list. It is not Garden's actual invoiced prices.

Evidence for it: (1) one fixed cost per product per branch for six months; (2) slope 1.4302 with a 95% interval of ±0.0006 and no fixed-fee component; (3) the same ratio for cheap and expensive items and every category; (4) no connection to Brent even though Brent doubled; (5) Garden's sales look like Harbour's and Uptown's. Real purchase prices would normally differ by product and change over the months.

**Alternatives we cannot exclude with this data:** (a) a real supplier agreement with a flat 43% surcharge; (b) an artefact of how the data set was built (the transaction IDs are replacement IDs, `SYN-…`, and Uptown and the prices also follow flat branch multipliers).

**How to confirm (ask finance):**
1. Garden's and Harbour's supplier invoices for 5 to 10 products across two or three months. If the invoice price is about the same and only the booked cost differs, the gap is accounting. If Garden's invoice is about 43% higher, it is a real purchase-price gap.
2. How overhead (rent, delivery, labour) is allocated to unit cost, and whether Garden is loaded with a different percentage. Whether Harbour and Uptown carry similar loadings.
3. Whether the cost field is updated monthly. If it is a fixed standard cost, say so, because then Finding 1 measures the standard, not what was paid.

**What it changes:** if the gap is allocation, the estimated gain of about $15,888 per six months is a bookkeeping difference and no cash would be saved by renegotiating suppliers. If it is a real supplier surcharge, the estimate stands and the action is to renegotiate or source Garden's top items through Harbour's supplier.

## Weak spots
- Test 2 has 25 weekly points, so only large correlations can be excluded; the argument rests on the cost not changing over time.
- Rounding to cents limits how exactly we can call the ratio "flat": the spread (std 0.0019) is within what rounding explains, but a very small product-specific effect would be invisible.
- Test 3 describes sales; it cannot see rent, wages, delivery routes or supplier terms, which are the likely real causes.
- The permutation p-values use 500 shuffles, so the smallest p reported is 0.002.

## Reproduce
```bash
mkdir -p data/external
curl -o data/external/DCOILBRENTEU.csv "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU"
python src/garden_cost_cause.py   # needs data/stories_transactions.csv
```
