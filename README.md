# Stories Coffee: <headline finding>

**Team:** Rakan Bou Hatoum Hamadeh · Muche Abere Workie
EECE 490 (Introduction to Machine Learning), American University of Beirut · Hackathon, October 17, 2026

## Conclusion
<One paragraph for the CEO: the problem, the recommended action, the estimated value in USD and the main assumption it depends on. Written last.>

## The business problem
<Which decision this helps Stories make, and why it matters.>

## Measured findings
Facts computed directly from the data (after removing 132 duplicate rows). Each one points to the script and the table that produce it.

1. **Garden earns far less gross profit per dollar of sales than the other branches.** Gross margin, January to June 2026:

   | Branch | Revenue (USD) | Gross profit (USD) | Gross margin |
   |---|---|---|---|
   | Harbour | 150,099 | 97,503 | 65.0% |
   | Uptown | 55,554 | 34,795 | 62.6% |
   | Garden | 99,531 | 46,696 | 46.9% |

   The gap is the same every month (Garden 46.7–47.2%), so it is structural, not a one-off.

2. **The gap comes from unit cost, not price.** For every one of the 45 products, Garden's recorded unit cost is 1.43× Harbour's (range 1.426–1.439). Garden's prices are about 5% *lower* than Harbour's (Uptown's about 9% lower). A uniform 43% markup on every product points to a branch-level cause, such as supplier terms, delivery costs or how costs are allocated to Garden, rather than recipes or waste on specific items.

3. **Each branch has one fixed price list, set as a flat percentage of Harbour's prices, whatever the branch's costs.** All 135 product-branch pairs have exactly one price and one unit cost over the six months. Every Uptown price is 91.2–91.6% of Harbour's and every Garden price is 95.1–95.3% of Harbour's. So Garden, the branch whose costs are 43% higher, charges *less* than Harbour. At list prices, before any discount, the share of revenue kept as gross profit is:

   | Branch | Price vs Harbour | Unit cost vs Harbour | Margin at list price |
   |---|---|---|---|
   | Harbour | 1.000 | 1.000 | 65.3% |
   | Uptown | 0.914 | 0.960 | 62.9% |
   | Garden | 0.952 | 1.430 | 47.2% |

   Source: `src/pricing_analysis.py`, `results/pricing_ratios_summary.csv`, `results/pricing_list_margin_by_branch.csv`.

4. **Tuesday has about 1.5 times the transactions of other weekdays, every week, at every branch, and it does not look like a recording error.** Mean transactions per calendar day:

   | | Mon | Tue | Wed | Thu | Fri | Sat | Sun |
   |---|---|---|---|---|---|---|---|
   | All branches | 178.0 | 284.5 | 186.2 | 180.0 | 197.5 | 128.7 | 155.7 |

   Tuesday divided by the Monday, Wednesday, Thursday and Friday average is 1.56 at Garden, 1.53 at Harbour and 1.52 at Uptown. It is the busiest day in all 25 full weeks, with a weekly ratio between 1.32 and 1.69. We tested five ways it could be an artifact:
   - *Another day's sales posted on Tuesday:* Monday and Wednesday are not lower than Thursday and Friday, and transaction IDs follow the date exactly with no Tuesday out of sequence.
   - *Copied records:* transactions repeating the same branch, second of the day and products appear at the same rate as on other days.
   - *A few event days:* no week falls below 1.32.
   - *One event slot, e.g. a Tuesday-evening offer:* the hour-by-hour profile matches other days, with the largest gap 0.62 points; a permutation test gives p = 0.75.
   - *Different buyers:* items per transaction and spend per transaction differ from other days by under 1%, and category shares, dine-in share and known-customer share by about one percentage point or less, and 99.2% of known Tuesday customers also buy on other days.

   Tuesday is the same customers buying the same things at the same hours, just about 1.5 times as often. Nothing in the data explains why: there is no Tuesday discount and no change in mix. Saturday is the quietest day. Source: `src/tuesday_check.py`, `results/tuesday_*.csv`, `figures/tuesday_check.png`.

5. <Promo and 10% discount findings: to write up from `results/promo_*.csv` and `results/discount_*.csv`>

## Estimated business value
Estimates, kept separate from the measured facts above.

- If Garden's costs matched Harbour's cost ratio, gross profit over the same six months would be about **$18,000 higher** (Garden revenue × 18.1 margin points), or about **$15,600** if matched to Uptown. That is roughly $31,000–36,000 per year at the current sales level.
- **Aligning Garden's and Uptown's prices with Harbour's.** The data cannot measure price sensitivity, because no price ever changes. So we assume a constant price elasticity for every product and show a range. Gross-profit change over the same six months, from `results/pricing_scenarios.csv`:

  | Elasticity (assumed) | Garden to Harbour prices (+5.0%) | Garden half-way | Uptown to Harbour prices (+9.4%) | Uptown half-way |
  |---|---|---|---|---|
  | 0 (no customers lost) | +$4,975 | +$2,488 | +$5,216 | +$2,608 |
  | −0.5 | +$3,731 | +$1,884 | +$3,461 | +$1,760 |
  | −1.0 | +$2,516 | +$1,289 | +$1,782 | +$931 |
  | −1.5 | +$1,331 | +$700 | +$177 | +$121 |
  | −2.0 | +$174 | +$119 | −$1,357 | −$671 |
  | Break-even elasticity | −2.08 | −2.10 | −1.56 | −1.58 |

  For Garden, the price rise loses money only if customers are very price-sensitive: a 5% rise would have to cut units by about 10%. Annualised, the Garden scenario is worth about $5,000 a year at an elasticity of −1 and about $10,000 a year if no customers leave. This is smaller than fixing Garden's costs, but it needs no supplier change and can start at once.
- **Cross-branch effect, not in the numbers above.** 94% of known customers already buy at more than one branch. If a Garden price rise moves some customers to Harbour, the chain still keeps 65% gross margin on those sales instead of 47%. Treating lost Garden units as lost to the chain therefore understates the Garden gain. For Uptown, the two margins are close, so moved customers change little.

## Assumptions and what would change the recommendation
| Assumption | Why it matters | If it is wrong |
|---|---|---|
| The `Unit Cost` column reflects real costs Stories pays per item | The Garden finding depends on it | If Garden's cost includes allocated overheads (e.g. higher rent) that other branches book elsewhere, the gap may be an accounting difference with little savings available |
| Garden's higher cost is not buying better quality that supports its sales | Cutting cost could otherwise hurt demand | Savings would be offset by lost sales |
| Price elasticity is between 0 and −2, and the same for every product | Sets the size of the pricing gain | Above about 2.1 in absolute value, raising Garden's prices loses gross profit; for Uptown the limit is about 1.6 |
| Lower prices at Garden and Uptown are not a deliberate response to local competitors | A competitor next door could make customers more price-sensitive than the range we assume | The price rise could lose more customers than estimated; the pilot below would show this |
| The Tuesday surge reflects real customer visits | Staffing and stock plans would follow it | If it comes from how the data was produced or exported, Tuesday staffing should not change until Stories checks its till and footfall records |
| <more> | | |

## A practical test Stories could run
- **Garden costs.** Audit how Garden's costs are recorded. Then run a one-month pilot buying Garden's top 10 products through Harbour's supplier, comparing cost per unit and sales against the previous month and against the other branches.
- **Garden prices.** For four weeks, move a random half of Garden's products to Harbour's price and keep the other half unchanged. Compare units sold between the two halves, with Harbour as a second control. This measures Garden's real price sensitivity before changing the whole list. Garden sold between 2,410 and 3,556 units a month from January to June.
- **Tuesday.** Compare the Tuesday surge with till-session counts, door counters or staff rosters for a few weeks. If it is confirmed, plan Tuesday staffing and stock at about 1.5 times a normal weekday.

## Weak areas and uncertainty
- Only six months of data (January–June), so there is no yearly seasonality.
- 36.5% of lines have no Customer ID, and 94% of known customers appear at several branches, so customer-level conclusions are uncertain.
- Prices never change in the data, so price sensitivity is an assumption, not a measurement. The pricing estimates are only as good as the elasticity range.
- We could not find the cause of the Tuesday surge in the data. We can only rule out the recording errors we tested.
- <more>

## Approaches we considered and rejected
- **Estimating price sensitivity from differences between branches.** Uptown is the cheapest branch but sells the least, so comparing branches would suggest higher prices bring more customers. Location and size drive those differences, not price, so we rejected this.
- **Estimating price sensitivity from the 10% discount.** Discounted lines have the same quantity as full-price lines. But the discount seems to be applied at the till, so customers do not see it when choosing, and it says little about how they react to a posted price.
- <more>

## Data quality
See [`data/README.md`](data/README.md): row counts, duplicates removed, missing values and formula checks.

## How to reproduce
```bash
pip install -r requirements.txt
# place stories_transactions.csv in data/ (see data/README.md)
cd src
python margin_analysis.py     # Garden margin and unit costs
python pricing_analysis.py    # branch price lists and pricing scenarios
python tuesday_check.py       # Tuesday surge artifact tests
python promo_analysis.py      # Harbour 15% promo, about 40 seconds
python discount_analysis.py   # 10% discount
```
Summary tables are saved in `results/`, figures in `figures/`.
