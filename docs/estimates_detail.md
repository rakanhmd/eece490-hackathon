# Estimates and findings: extra detail

Detail moved out of the README to keep it short. All figures come from the results tables named next to them. Six-month figures; per year = six months × 2.

## Garden cost fix and price fix together
Computed together, not added, because with lost customers (elasticity below 0) each lost unit is worth more after the cost fix (`results/garden_cost_price_combined.csv`):

| Elasticity (assumed) | Cost fix only | Price fix only (Garden to Harbour's prices, +5.0%) | Both together |
|---|---|---|---|
| 0 | $15,888 | $4,975 | $20,863 |
| −1.0 | $15,888 | $2,516 | $17,647 |
| −2.0 | $15,888 | $174 | $14,585 |

The $15,888 is an upper bound: it assumes the whole recorded gap is real, avoidable cash.

## Price Option A by elasticity
All branches +6.86% on the same six months of volume, costs and discounts unchanged (`results/opportunity_inflation_price.csv`):

| Elasticity (assumed) | Units | All branches | Garden + Uptown part |
|---|---|---|---|
| 0 | 0% | +$20,922 | +$10,632 |
| −1.0 | −6.4% | +$8,096 | +$4,722 |
| −2.0 | −12.4% | −$3,907 | −$810 |

Option A breaks even at elasticity −1.67, a 10.5% fall in units.

## Price Option B by elasticity
Garden and Uptown matched to Harbour's prices, each branch separately (`results/pricing_scenarios.csv`, "full: match Harbour"):

| Elasticity (assumed) | Garden (+5.0%) | Uptown (+9.4%) |
|---|---|---|
| 0 | +$4,975 | +$5,216 |
| −1.0 | +$2,516 | +$1,782 |
| −2.0 | +$174 | −$1,357 |

Break-even elasticities: Garden −2.08, Uptown −1.56.

## Decision thresholds
From `src/opportunity_estimates.py`, `results/decision_thresholds.csv`. Each holds the other assumptions fixed and excludes implementation costs.

| Comparison | Threshold |
|---|---|
| Garden cost fix vs Option A ($8,096 at elasticity −1) | cost fix ranks higher if more than 51.0% of the $15,888 gap is real, avoidable cash |
| Garden cost fix vs Option B ($4,298 at elasticity −1) | above 27.1% |
| Saturday at 25% of Tuesday's lift ($3,468) vs food prompt at +2.5 points ($2,171) | Saturday ranks lower if more than 37.4% of the extra visits are shifted from other days |
| Food prompt vs stopping the 10% discount ($1,706) | the prompt ranks lower if it raises the attach rate by less than 1.96 points |
| Option A break-even | elasticity −1.67 |

## Prices and dayparts
- At list prices (before discounts) the margin is Harbour 65.3%, Uptown 62.9% and Garden 47.2% (`results/pricing_list_margin_by_branch.csv`).
- Evenings bring the largest share of dessert baskets (16.6%). All branches share the same hourly and weekday shape (correlations 0.99 and above), so the data cannot tell what kind of location each branch is (`src/daypart_analysis.py`, `results/daypart_*.csv`).
- For the same product at the same branch, a discounted line has the same quantity as a full-price one (`results/discount_line_level.csv`).
