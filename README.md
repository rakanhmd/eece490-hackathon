# Stories Coffee: Garden's recorded unit costs are about 43% higher on every product

**Team:** Rakan Bou Hatoum Hamadeh · Muche Abere Workie
EECE 490 (Introduction to Machine Learning), American University of Beirut · Hackathon, October 17, 2026

## Bottom line
**Start with an audit of Garden's invoices and cost allocations.** Garden's recorded unit cost is about 1.43× Harbour's on every product (1.426–1.439 across the 45 products), unchanged for six months. Garden keeps 46.9% of sales as gross profit, against 65.0% at Harbour. Comparing Garden's and Harbour's supplier invoices and overhead allocations for 5–10 products will show which case holds. If the gap is accounting only, the saving is $0. If the whole gap is real, avoidable cash, it is worth up to +$15,888 of gross profit per six months.

**Tuesday's mechanism is not identified.** Tuesday is about 1.5× the Monday, Wednesday, Thursday and Friday average at every branch (1.52–1.56), and Saturday is 0.69×. The extra Tuesday transactions come mostly from more distinct existing customers, not more trips per customer, but nothing in the data says why.

Other measured facts: no price changed from January to June while Lebanese consumer prices rose 17.25% a year, and the 10% discount cost $1,706 with no evidence that it raises basket size beyond what random assignment would produce.

**Decision table.** Each threshold holds the other assumptions fixed and excludes implementation costs (`results/decision_thresholds.csv`). Six-month figures; per year = six months × 2.

| Area | Observed evidence | Decision now | What would change the order |
|---|---|---|---|
| Garden costs | About 1.43× Harbour's recorded cost on every product, unchanged for six months | Audit invoices and cost allocations for 5–10 products before any other cost action | The cost fix is worth more than price Option A only if more than 51.0% of the $15,888 gap is real, avoidable cash, and more than Option B only above 27.1% |
| Prices | 0 price changes on 135 price lists; Lebanon CPI +17.25% a year | Choose Option A or Option B (below) and test it by branch-week before a chain-wide change | Option A loses gross profit at elasticities beyond −1.67 (a 10.5% fall in units) |
| Tuesday and Saturday | Tuesday 1.52–1.56× at every branch, in all 25 full weeks; not a discount day | Check Stories' app/loyalty campaign logs for Tuesdays; staff Tuesdays from the weekday forecast; copy the driver to Saturday only once it is found | A Saturday gain of 25% of Tuesday's lift ($3,468 before shifting) falls below the food prompt if more than 37.4% of the extra visits are shifted from other days |
| Food with drinks | 59% of drink orders carry no food; the attach rate runs from 38.1% to 43.0% by drink | Test a till prompt, without a discount, switched on and off by branch-week at random | The prompt is worth less than stopping the 10% discount if it raises the attach rate by less than 1.96 points |
| 10% discount | Costs $1,706; no evidence it raises basket size | Pilot stopping it at one branch for four weeks | Any lost visits reduce the saving; their effect is untested |
| Harbour's 15% promo | $470 of discounts; the rise in promoted categories grew after it ended | Do not extend it without a proper test | — |
| Win-back campaigns | Selected churn model PR-AUC 0.0995 on held-out customers vs 0.0877 for the baseline | Do not target win-back offers with a model | A model that clearly beats the baseline on new data |

**Price options (alternatives; do not add them).**
- **Option A, all branches +6.86%** (inflation-matched): +$8,096 at an assumed elasticity of −1, meaning customers cut purchases 1% for every 1% price rise. The range is −$3,907 at elasticity −2 to +$20,922 at 0. It breaks even at −1.67.
- **Option B, Garden and Uptown matched to Harbour's prices** (Garden about +5.0%, Uptown about +9.4%; Harbour unchanged): +$4,298 at elasticity −1 (Garden $2,516, Uptown $1,782). Uptown breaks even at −1.56.
- **Overlap with the Garden cost fix.** With either option Garden sells fewer units, so the cost fix saves less. At elasticity −1 the overlap is $1,019 for Option A (`results/opportunity_cost_price_overlap.csv`) and $757 for Garden's part of Option B (`results/garden_cost_price_combined.csv`).

## The business problem
Stories already knows what each branch sells. We looked for decisions where money is left on the table: what each branch's products are recorded to cost, how prices are set, whether discounts earn back what they give away, and when customers come. Gross profit is the measure throughout, because revenue would hide Garden's problem.

## Measured findings
All figures are computed from the data after removing 132 exact duplicate rows. Each finding names its script and tables.

1. **Garden keeps far less of each sale as gross profit.** The gap is the same every month (Garden 46.7–47.2%).

   | Branch | Revenue (USD) | Gross profit (USD) | Gross margin |
   |---|---|---|---|
   | Harbour | 150,099 | 97,503 | 65.0% |
   | Uptown | 55,554 | 34,795 | 62.6% |
   | Garden | 99,531 | 46,696 | 46.9% |

2. **The gap is mostly in recorded unit cost; Garden's lower prices also contribute.** Garden's recorded unit cost is about 1.43× Harbour's on every product (1.426–1.439), while its prices are about 5% lower.
   - [`GARDEN_CAUSE.md`](GARDEN_CAUSE.md) finds a best-fit factor of 1.4302 (95% interval 1.4297 to 1.4309), every product within cent rounding of it, and no fixed fee per unit. The factor does not move with Brent crude, which roughly doubled. Garden's customers, hours and baskets look like the other branches'.
   - This is consistent with a branch-level standard-cost or allocation rule. The data cannot tell whether Garden's costs are higher in cash or only recorded higher.
   - Source: `src/margin_analysis.py`, `results/margin_by_branch.csv`, `results/unit_cost_ratio_by_product.csv`.

3. **Each branch has one fixed price list, set as a flat share of Harbour's prices.** All 135 product-branch pairs have exactly one price and one unit cost for all six months. Every Uptown price is 91.2–91.6% of Harbour's and every Garden price is 95.1–95.3%. Source: `src/pricing_analysis.py`, `results/pricing_*.csv`.

4. **Tuesday brings about 1.5× the transactions of the Monday, Wednesday, Thursday and Friday average at every branch (1.52–1.56), and weekends are the quietest.** Mean transactions per day, all branches:

   | Mon | Tue | Wed | Thu | Fri | Sat | Sun |
   |---|---|---|---|---|---|---|
   | 178.0 | 284.5 | 186.2 | 180.0 | 197.5 | 128.7 | 155.7 |

   - **Every week.** Tuesday is the busiest day in all 25 full weeks, with weekly ratios of 1.32–1.69. On the same base Saturday is 0.69× and the weekend 0.767 [0.745, 0.790] (`results/tuesday_weekday_ratios.csv`).
   - **No sign of a recording error in our tests.** No other day is depleted, there are no copied records, it is not a few event days, and the hours and baskets are unchanged (permutation p = 0.75).
   - **Not a discount day.** 10.1% of Tuesday transactions carry a discount, against 9.4% on other days. The identified-customer share is 64.2% against 63.4%.
   - **What the excess is made of** ([`TUESDAY_DECOMP.md`](TUESDAY_DECOMP.md)). About 95.4 extra transactions a week: 65.3% more distinct customer IDs [62.0%, 68.8%], 0.6% more trips per ID [−0.1%, 1.2%], and 34.2% with no Customer ID [30.7%, 37.3%]. From week 9 on only 2.6% comes from IDs first seen that week, and 99.1% of Tuesday customers also buy on other days. Whatever drives it reaches a broad share of existing customers at once, which is consistent with a chain-wide trigger such as an app notification or loyalty-member offer (hypothesis, not shown).
   - **Commuters and students.** Weekday mornings are not over-represented (9.78% of weekday transactions between 07:00 and 09:59, against 9.55% at weekends), and weekday sales show no clear dip while AUB students were away.
   - **When customers come.** Dine-in is about 46% of transactions every hour until 17:00, then jumps to 69.9% at 18:00 at all three branches; 44.2% of traffic comes after 19:00. The step is so sharp and uniform that it may be a till default rather than customer behaviour ([`FINDING_weekend.md`](FINDING_weekend.md)), so check it against receipts from 17:30–18:30 before changing seating or staffing.
   - Source: `src/tuesday_check.py`, `src/tuesday_decompose.py`, `src/daypart_analysis.py`, `results/tuesday_*.csv`, `results/daypart_*.csv`.

5. **A weekday-and-trend forecast beats the baseline on June, most of all on Tuesdays.** Four models were trained on January to April and compared on May. Only the one chosen on May, weekday + log trend, was refit on January to May and scored once on June, next to the dummy and the baseline. The comparison favours the baseline, which uses last week's actual counts, while our model forecasts up to a month ahead. Staffing from this forecast needs only the Tuesday pattern to persist, not its cause.

   Mean absolute error, transactions per branch per day:

   | Model | May (validation) | June (test) | June, Tuesdays |
   |---|---|---|---|
   | Dummy (training mean) | 15.45 | 20.27 | 55.04 |
   | Seasonal naive (same weekday last week) | 8.94 | 9.60 | 15.20 |
   | Weekday + trend | 6.54 | not scored | not scored |
   | Weekday + log trend | **6.12** | **6.95** | **9.02** |

   Source: `src/forecast.py`, `results/forecast_mae.csv`, `results/results.csv`.

6. **Harbour's 15% promo on Cold Coffee and Desserts shows no clear evidence of causing extra sales.** A difference-in-differences on daily units, with Garden and Uptown as controls and a bootstrap over weeks, gives +13.7% [+2.0, +27.7] during the promo (March 12 to May 19) and +18.6% [+8.1, +29.2] after it ended. With Garden as the only control the effect is +6.9% [−4.3, +21.0]; with Uptown it is +21.1% [+6.0, +41.1]. Placebos are near zero. A pure price effect would be expected to fade after the discount ends, although habits can persist; because the rise grew after the end and depends on the control branch, we do not credit the promo with it. Source: `src/promo_analysis.py`, `results/promo_*.csv`.

7. **The 10% discount costs $1,706, and we found no evidence it raises basket size beyond what random assignment would produce.** It is on 5.50–5.84% of lines by branch, 5.36–5.92% by month and 5.29–6.16% by weekday (`results/discount_spread.csv`). Discounted transactions look 0.23 items bigger, but shuffling the discount at random across lines produces the same gap, because bigger baskets have more lines for it to land on. Its effect on visits is untested. Source: `src/discount_analysis.py`, `results/discount_*.csv`.

8. **59% of drink orders carry no food; of the variables we measured, only drink category was linked to the food-with-drink rate.** The attach rate is 40.8% overall, with no detectable difference across branches, hours, weekdays and months. It runs from 38.1% for Cold Coffee to 43.0% for Matcha & Tea (p < 0.0001). Detail in [`FINDING_8.md`](FINDING_8.md). Source: `src/basket_analysis.py`, `results/basket_*.csv`.

## Did outside factors cause this?
We tested public data against the Tuesday surge, daily demand, growth and Garden's 1.43×, and compared our data with real shops. All branches are treated as being in Greater Beirut, because branch addresses are not in the data. Real-shop values are references, not causes. Brackets are 95% intervals. We ran about 14 tests without a multiple-testing correction. Full detail is in [`docs/outside_factors.md`](docs/outside_factors.md); sources are in [`data/README.md`](data/README.md).

![Real shops vs Stories](figures/outside_factors_summary.png)

| Pattern | What we tested (our result; reference) | Verdict | Still possible | Next test |
|---|---|---|---|---|
| Tuesday surge | Local cause: Tuesday ratio 1.52–1.56 at every branch. School and AUB calendar: −0.026 [−0.096, +0.050] with AUB out. Tue/Thu timetable: Thursday 0.971 [0.940, 1.003] of Mon/Wed/Fri. Reference: only the vending machine peaks on Tuesday, at 1.08; the bakery is 0.97; chains peak on Saturday | Not supported by our tests; Stories' peak is unusual | A chain-wide internal driver (app notification, loyalty offer, standing promotion); a data or posting artefact | App/loyalty campaign logs for Tuesdays; daily till (Z-report) or bank totals by weekday |
| Daily demand | Holidays −0.5% [−3.9, +3.0] (French bakery +36% [+19, +54]). Temperature within month −0.09% per °C [−0.54, +0.37] (bakery +0.82% [+0.37, +1.27]; intervals touch). Rain −0.9% [−3.6, +1.9] (bakery −2.6% [−6.9, +2.0]). Cold-drink share +0.08 points per °C [−0.06, +0.22] (one London café +2.2). Ramadan evening share +0.4 points [−1.4, +2.2]. March escalation +2.4% [−2.6, +6.8] vs trend | Not supported by our tests | Effects too small for our data to detect | — |
| Steady daily counts | Dispersion 0.98, inside the pure-chance range 0.88–1.14 (bakery 8.45, vending machine 1.84, Maven, fictitious, 4.76) | Much steadier than every reference shop | Habitual demand from regulars (98.5% of identified customers bought more than once), a hypothesis; smoothing from how the data was recorded | Daily till totals for a few weeks |
| Growth | +52.6% transactions, January to June, with no price change; the weather change implies a −0.75% change in transactions (−1.78% of the log growth) | Not price, not weather | More customers or visits; seasonality we cannot see in six months | A second year of data |
| Garden's 1.43× | Brent weekly mean $62.93 to $124.61, ratio moved 0.0001. Arabica −15.4%, all 135 unit costs unchanged. Cost of goods: Garden 53.1%, Harbour 35.0%, Starbucks 31.4% | Fuel and world coffee prices not supported | A branch-level standard-cost or overhead allocation; a real flat supplier surcharge; rent or location costs | Supplier invoices and overhead allocations for 5–10 products |

Our data shares only its framing with the public Maven dataset and shows no sign of being derived from it.

## Estimated business value
Estimates, kept separate from the measured facts. Six-month figures; per year = six months × 2. The price options and the Garden cost fix are in the bottom line; tables by elasticity and the decision thresholds are in [`docs/estimates_detail.md`](docs/estimates_detail.md).
- **Price review basis.** Lebanon's consumer prices rose 17.25% in the year to June 2026. Assuming an even monthly path (1.335% a month), Stories' real prices were 6.42% lower by June (modelled), if dollar menu prices track the lira-based CPI. Option A tests one rise of 6.86% on the same six months of volume, with costs and discounts unchanged (`results/opportunity_inflation_price.csv`).
- **Saturday, if the Tuesday driver can be copied.** Each branch's actual Saturday basket and margin are used. Because most customers are regulars who use several branches, some extra Saturday visits may be shifted from other days (`results/opportunity_saturday_range.csv`):

  | Scenario | No shifting | Quarter shifted | Half shifted |
  |---|---|---|---|
  | Saturday gains 25% of Tuesday's lift | +$3,468 | **+$2,601** (central case) | +$1,734 (illustrative downside; shifting could be higher) |
  | Saturday gains 50% of Tuesday's lift | +$6,937 | +$5,202 | +$3,468 |
  | Saturday reaches the Mon/Wed/Thu/Fri average | +$7,993 | +$5,994 | +$3,996 |
- **Food with drinks.** A 1 to 5 point rise in the attach rate is worth +$644 to +$4,341, with +$2,171 for 2.5 points at the average food margin (`results/basket_value_scenarios.csv`). A 10% pairing discount would need a 9.4-point rise to break even. An evening dessert upsell of 1 to 5 points, worth +$455 to +$2,273, is part of this.
- **10% discount.** Stopping it saves up to $1,706, or $3,412 a year, if no visits are lost.
- **Harbour promo.** If the promo caused all of the rise, its net was +$599, with a range of −$299 to +$1,451 (`results/promo_value.csv`).

## Assumptions and what would change the recommendation
| Assumption | If it is wrong |
|---|---|
| The `Unit Cost` column records money Stories really pays per item | If Garden's cost includes overheads booked differently, no cash is saved; if it is a real supplier surcharge, it may still not be avoidable |
| Price elasticity is between 0 and −2, the same for every product | Beyond about −1.67, Option A loses gross profit |
| Lebanon's lira-based CPI is a fair guide to pressure on dollar menu prices | The 6.42% real-price loss is then overstated or understated |
| Tuesday's extra transactions are extra visits | Items per transaction are unchanged on Tuesdays, so there is no sign of split orders; till-session counts would confirm it |
| Extra Saturday visits need no extra labour | Labour cost reduces every Saturday figure; above 37.4% shifting the food prompt ranks higher |
| All branches are in Greater Beirut | We cannot test a cause that affects only one branch |
| The 132 exact duplicates are recording errors | If they are real, revenue rises by $741 (0.24%); nothing else changes |
| Anonymization changed only branch names and IDs | Some patterns could partly reflect that process; Stories can check against its own records |

## Practical tests Stories could run
- **Garden costs.** Supplier invoices and overhead allocations for 5–10 products, Garden against Harbour.
- **Prices.** Raise prices in randomly chosen branch-weeks for about eight weeks, randomizing by branch-week rather than by product so customers cannot switch between raised and unraised products. Roll out if units fall by less than 10.5%.
- **Food prompt and evening upsell.** Switch each on and off by branch-week at random (switchback) for 6–8 weeks, so no single branch carries the whole treatment. We have not computed the detectable effect for this design.
- **Tuesday.** Stories' app/loyalty campaign logs and daily till totals by weekday.

## Weak areas and uncertainty
- Only six months of data, with no yearly seasonality. Sales grew through the period, so yearly figures (six months × 2) may be too low if growth continues.
- Prices never change in the data, so price sensitivity is assumed, not measured.
- The Tuesday driver is unknown. Tuesday staffing needs only the pattern to persist; the Saturday transfer depends on finding the cause.
- The promo test has only two control branches, and its result depends on the choice of control.
- The forecast was tested on one month.
- 36.5% of lines have no Customer ID, so customer figures describe identified customers only.

## Approaches we considered and rejected
- **Estimating price sensitivity from differences between branches.** Branch prices are confounded with location and size, so those differences cannot isolate price.
- **Estimating price sensitivity from the 10% discount.** It is applied at the till to 5.3–6.2% of lines by branch, month and weekday, so it gives no menu-price variation to estimate from.
- **Adding the Garden cost and price gains.** They interact, so we computed them together.
- **Plain basket "lift", or a model of whether a basket takes food.** Basket size distorts lift, and of the variables measured only drink type was linked to taking food.
- **More complex forecast models.** There are only 151 training days per branch, and a simple regression already beats the baseline.

## Data and reproduction
Data, column schema, quality checks, external sources and licenses are in [`data/README.md`](data/README.md). Working notes are in [`docs/internal/`](docs/internal/).

```bash
pip install -r requirements.txt
# place stories_transactions.csv in data/ (see data/README.md)
cd src
python margin_analysis.py        # Garden margin and unit costs
python pricing_analysis.py       # price lists, Garden/Uptown price scenarios (Option B)
python tuesday_check.py          # Tuesday checks, weekday ratios, discount and customer mix
python tuesday_decompose.py      # what the Tuesday excess is made of (TUESDAY_DECOMP.md)
python weekend_check.py          # Tuesday vs weekend offset, takeaway step at 18:00 (FINDING_weekend.md)
python forecast.py               # June forecast vs seasonal naive; replaces its own rows in results/results.csv
python promo_analysis.py         # Harbour 15% promo, 30 seconds to about 2 minutes
python discount_analysis.py      # 10% discount
python basket_analysis.py        # food with drinks
python external_factors.py       # weather, calendar, conflict, school/campus, cost checks
python benchmarks.py             # published coffee-chain benchmarks (after external_factors.py)
python garden_cost_cause.py      # Garden cost-cause tests (GARDEN_CAUSE.md)
python reference_compare.py      # public shop datasets: needs the Kaggle API, see below
python outside_summary.py        # outside-factors figure (after the two scripts above)
python opportunity_estimates.py  # Saturday, Option A, overlap and decision thresholds (after the scripts above)
python daypart_analysis.py       # weekday vs weekend, commuter and student tests, dayparts
python customer_model.py         # churn model and segments (CUSTOMERS.md); appends rows to results/results.csv
```

The reference comparison needs the Kaggle API with a `kaggle.json` token; the download commands are in `data/README.md`. Its outputs (`results/reference_*.csv`, `figures/reference_signatures.png`) feed the real-shop values above and `figures/outside_factors_summary.png`. Every other script needs only the transaction file and the committed files in `data/external/`.
