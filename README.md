# Stories Coffee: Garden pays 43% more for every product and still charges less

**Team:** Rakan Bou Hatoum Hamadeh · Muche Abere Workie
EECE 490 (Introduction to Machine Learning), American University of Beirut · Hackathon, October 17, 2026

## Conclusion
Garden is Stories' biggest profit leak. On every one of its 45 products, Garden's recorded unit cost is 1.43 times Harbour's. Yet its price list is a flat 95% of Harbour's, so it keeps 47% of sales as gross profit against Harbour's 65%. We recommend two steps. First, audit where Garden's extra cost comes from: suppliers, delivery, or how costs are booked. Second, move a random half of Garden's products to Harbour's prices for four weeks and compare them with the other half. If the costs are real and Garden can buy at Harbour's prices, our estimate is about $17,600 more gross profit per six months, roughly $35,600 a year. This assumes customers cut purchases 1% for every 1% price rise, and the range is $14,600–$20,900. About 90% of that gain comes from the cost fix. The main assumption is that the unit-cost column records money Stories really pays. If Garden's cost includes overheads that other branches book elsewhere, most of the saving disappears, which is why the audit comes first. Separately, Tuesday brings about 1.5 times a normal weekday's transactions at every branch, every week. A simple forecast cuts the Tuesday planning error from 15.2 to 9.0 transactions a day compared with "same weekday last week". Neither discount we examined shows evidence of paying for itself.

| Rank | Finding and action | Value over 6 months (Jan–Jun) | Measured or estimated |
|---|---|---|---|
| 1 | Garden: bring unit costs to Harbour's level and prices to Harbour's list | +$17,647 at elasticity −1 (range $14,585 to $20,863); about $35,600 a year | Estimated. The cost and price gaps themselves are measured |
| 1a | Of which, cost fix alone | +$15,888 | Estimated. Part of row 1, do not add |
| 1b | Of which, price fix alone | +$2,516 at elasticity −1 (range $174 to $4,975) | Estimated. Part of row 1, do not add |
| 2 | Uptown: move prices to Harbour's list | +$1,782 at elasticity −1 (range −$1,357 to +$5,216) | Estimated. Can lose money if customers are price-sensitive |
| 3 | Stop or restrict the 10% discount | $1,696 given away; saving up to that if no sales are lost | Cost measured, saving estimated |
| 4 | Harbour 15% promo: do not extend it without a proper test | $470 of discounts given; net +$543 only if the promo caused the rise (range −$308 to +$1,349) | Cost measured, net estimated; causation not shown |
| 5 | Plan Tuesday staffing and stock with the weekday forecast | No dollar figure, because labour costs are not in the data. Tuesday error 9.0 vs 15.2 transactions a day | Measured on June, held-out data |

Rows 1 and 2 concern different branches, so they do not overlap. Removing the 10% discount at Garden or Uptown would slightly raise the price-row gains, which already include discounts as observed.

## The business problem
Stories already knows what each branch sells. We looked instead at decisions where the data points to money left on the table:
- what each branch pays for its products, and how each branch sets its prices;
- whether its two discounts, the 10% discount and Harbour's 15% promo, earn back what they give away;
- how many customers to plan for on each day of the week.

Gross profit is the measure throughout, because it is what is left to pay staff and rent. Revenue would hide Garden's problem.

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

5. **A simple weekday-and-growth model forecasts daily transactions better than "same weekday last week", most of all on Tuesdays.** Target: transactions per branch per day. We chose between two models on May, after training on January to April. Then we refit the chosen model on January to May and tested it once on June. The model is a per-branch regression of log(transactions) on weekday plus a time trend. It uses no June data. The baseline uses the actual count from seven days earlier, so it has more recent information than the model. June mean absolute error, in transactions per day:

   | Model | Garden | Harbour | Uptown | All | Tuesdays | Other days |
   |---|---|---|---|---|---|---|
   | Dummy (training mean) | 18.15 | 31.30 | 11.35 | 20.27 | 55.04 | 13.31 |
   | Same weekday last week (baseline) | 10.23 | 11.23 | 7.33 | 9.60 | 15.20 | 8.48 |
   | Weekday + log trend | **6.96** | **8.17** | **5.74** | **6.95** | **9.02** | **6.54** |

   On May validation the order was the same, with all-branch errors of 6.12 for the model and 8.94 for the baseline. **Business use:** this sets Tuesday staffing and stock. In June, Harbour averaged 168.8 transactions on Tuesdays against 111.5 on other weekdays. Planning Tuesdays like a normal weekday would be off by 57.3 transactions a day at Harbour. The model's Tuesday error there was 12.2, and the baseline's was 18.6. The forecast assumes the Tuesday pattern is real, as discussed in finding 4. Source: `src/forecast.py`, `results/forecast_mae.csv`, `results/forecast_tuesday.csv`, `results/results.csv`, `figures/forecast_june.png`.

6. **Harbour's 15% promo on Cold Coffee and Desserts shows no clear evidence that it caused extra sales.** All 502 lines with a 15% discount are at Harbour, from 12 March to 19 May, on those two categories only. 23.2% of eligible lines in the window got the discount. We used a difference-in-differences on daily units, with Garden and Uptown as controls. Day fixed effects absorb season and chain-wide growth. The 95% intervals come from a bootstrap over whole weeks:

   | Test | Effect during promo | Effect after promo ended |
   |---|---|---|
   | Harbour vs Garden + Uptown | +13.7% [+2.0, +27.7] | +18.6% [+8.1, +29.2] |
   | Garden as only control | +6.9% [−4.3, +21.0] | +10.1% [−1.5, +22.8] |
   | Uptown as only control | +21.1% [+6.0, +41.1] | +27.8% [+10.5, +46.4] |
   | Placebo: categories not on promo | −1.5% [−5.7, +2.9] | +3.4% [−1.3, +8.2] |
   | Placebo: Cold Drinks, weather-sensitive, never discounted | −1.3% [−16.1, +15.8] | −5.1% [−24.3, +13.4] |
   | Placebo: fake promo window, Feb 1 to Mar 11 | −1.6% [−15.2, +13.0] | n/a |

   The placebos are flat, and there was no clear pre-promo trend: −0.28 to +0.62 points per week over 10 weeks. But the gain is *larger after the discount stopped*, Harbour only pulls away about five weeks into the promo, and the size depends on which branch is the control. A discount effect would end when the discount ends. So we do not credit the promo with the rise. Source: `src/promo_analysis.py`, `results/promo_*.csv`, `figures/promo_weekly.png`.

7. **The 10% discount buys nothing measurable.** It appears on 5.5–5.8% of lines at every branch, 5.4–5.9% in every month and 5.3–6.2% on every weekday. Known customers get it at the same rate as everyone else, 63.2% vs 63.6% of transactions. Discounted transactions look bigger, with 0.23 more items. But shuffling the discount at random across lines produces the same gap, 0.23, because the discount is applied per line and bigger baskets have more lines to land on. For the same product at the same branch, a discounted line has the same quantity as a full-price one, a difference of +0.0004 units. Discounts given, January to June: **$1,696**. Source: `src/discount_analysis.py`, `results/discount_*.csv`.

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
- **Garden cost and Garden price together, without double counting.** The $18,000 above assumes Garden reaches Harbour's margin at Garden's own prices, which means costs slightly *below* Harbour's. Here instead Garden pays exactly Harbour's unit cost per product. Both changes are computed together from one baseline, not added, because after the cost fix every customer lost to a price rise costs more. Six months, from `results/garden_cost_price_combined.csv`:

  | Elasticity (assumed) | Cost fix only | Price fix only | Both together | Sum of the two (overstated) |
  |---|---|---|---|---|
  | 0 | $15,888 | $4,975 | $20,863 | $20,863 |
  | −1.0 | $15,888 | $2,516 | $17,647 | $18,404 |
  | −2.0 | $15,888 | $174 | $14,585 | $16,062 |
- **Harbour 15% promo.** If all of the measured rise were caused by the promo, the extra gross profit would be about $1,013 against $470 of discounts, a net +$543. The 95% range is −$308 to +$1,349, over the ten-week window. The promo breaks even at a 5.9% uplift. Because we do not credit the promo with the rise, the true net is probably lower. Source: `results/promo_value.csv`.
- **Stopping the 10% discount.** This would save up to $1,696 per six months, about $3,420 a year, if no sales are lost. We found no sign that it brings extra items, but we cannot see whether it keeps customers coming back.
- **Cross-branch effect, not in the numbers above.** 94% of known customers already buy at more than one branch. If a Garden price rise moves some customers to Harbour, the chain still keeps 65% gross margin on those sales instead of 47%. Treating lost Garden units as lost to the chain therefore understates the Garden gain. For Uptown, the two margins are close, so moved customers change little.

## Assumptions and what would change the recommendation
| Assumption | Why it matters | If it is wrong |
|---|---|---|
| The `Unit Cost` column reflects real costs Stories pays per item | The Garden finding depends on it | If Garden's cost includes allocated overheads (e.g. higher rent) that other branches book elsewhere, the gap may be an accounting difference with little savings available |
| Garden's higher cost is not buying better quality that supports its sales | Cutting cost could otherwise hurt demand | Savings would be offset by lost sales |
| Price elasticity is between 0 and −2, and the same for every product | Sets the size of the pricing gain | Above about 2.1 in absolute value, raising Garden's prices loses gross profit; for Uptown the limit is about 1.6 |
| Lower prices at Garden and Uptown are not a deliberate response to local competitors | A competitor next door could make customers more price-sensitive than the range we assume | The price rise could lose more customers than estimated; the pilot below would show this |
| The Tuesday surge reflects real customer visits | Staffing and stock plans would follow it | If it comes from how the data was produced or exported, Tuesday staffing should not change until Stories checks its till and footfall records |
| Garden could buy at Harbour's unit costs | Sets the size of the cost fix, the largest row | If part of the gap is unavoidable, such as a remote location, the gain scales down roughly in proportion |

## A practical test Stories could run
- **Garden costs.** Audit how Garden's costs are recorded. Then run a one-month pilot buying Garden's top 10 products through Harbour's supplier, comparing cost per unit and sales against the previous month and against the other branches.
- **Garden prices.** For four weeks, move a random half of Garden's products to Harbour's price and keep the other half unchanged. Compare units sold between the two halves, with Harbour as a second control. This measures Garden's real price sensitivity before changing the whole list. Garden sold between 2,410 and 3,556 units a month from January to June.
- **Tuesday.** Compare the Tuesday surge with till-session counts, door counters or staff rosters for a few weeks. If it is confirmed, plan Tuesday staffing and stock at about 1.5 times a normal weekday.

## Weak areas and uncertainty
- Only six months of data (January–June), so there is no yearly seasonality.
- 36.5% of lines have no Customer ID, and 94% of known customers appear at several branches, so customer-level conclusions are uncertain.
- Prices never change in the data, so price sensitivity is an assumption, not a measurement. The pricing estimates are only as good as the elasticity range.
- We could not find the cause of the Tuesday surge in the data. We can only rule out the recording errors we tested.
- The promo analysis compares Harbour with only two control branches, and the result changes with the choice of control.
- The forecast was tested on one month. June continued the January-to-June growth, so a log trend fit well. A change in trend, for example in summer, would hurt it.

## Approaches we considered and rejected
- **Estimating price sensitivity from differences between branches.** Uptown is the cheapest branch but sells the least, so comparing branches would suggest higher prices bring more customers. Location and size drive those differences, not price, so we rejected this.
- **Estimating price sensitivity from the 10% discount.** Discounted lines have the same quantity as full-price lines. But the discount seems to be applied at the till, so customers do not see it when choosing, and it says little about how they react to a posted price.
- **Customer retention or churn models.** 94% of known customer IDs buy at more than one branch, so we do not trust the IDs to track individuals.
- **More complex forecast models.** There are only 151 training days per branch, and a weekday-plus-trend regression already beats the baseline at every branch. We kept the model we can explain.
- **Adding the Garden cost and price gains.** They interact, so we computed them together.

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
python forecast.py            # June forecast vs same-weekday-last-week baseline
python promo_analysis.py      # Harbour 15% promo, about 40 seconds
python discount_analysis.py   # 10% discount
```
Summary tables are saved in `results/`, figures in `figures/`.
