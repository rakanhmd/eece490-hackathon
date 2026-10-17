# Stories Coffee: Garden's recorded unit costs are about 43% higher on every product

**Team:** Rakan Bou Hatoum Hamadeh · Muche Abere Workie
EECE 490 (Introduction to Machine Learning), American University of Beirut · Hackathon, October 17, 2026

## Bottom line: three actions
1. **Audit Garden's costs.** Garden's recorded unit cost is about 1.43× Harbour's on every product (1.426–1.439 across 45 products), unchanged for six months; Garden keeps 46.9% of sales as gross profit, Harbour 65.0%. Comparing supplier invoices and overhead allocations for 5–10 products will show which explanation fits the sampled products. It is worth $0 if the gap is accounting only, and up to +$15,888 of gross profit per six months if the whole gap is real, avoidable cash.
2. **Verify Tuesday against till records and campaign logs.** Tuesday brings about 1.5× the transactions of the Monday, Wednesday, Thursday and Friday average at every branch (1.52–1.56), and Saturday 0.69×. The mechanism is not identified. Daily till (Z-report) or bank totals and Stories' campaign and app logs for Tuesdays should come before copying it to Saturday; staffing from the forecast needs only the pattern to persist.
3. **Run the food and evening dessert prompt pilots.** Two 20-week branch-week switchbacks, no discount. They are rolled out if the lower 95% bound of the gain is above 0. At +2.5 points they are worth about $2,171 and $1,295 per six months; the two overlap.

None of the pilot designs we simulated can settle removing the discount, raising the four menu prices, price Option B or a Saturday offer; the default is to leave them unchanged (Decisions, b).

Also measured: no price changed from January to June while Lebanese consumer prices rose 17.25% a year. The decision tables follow the measured findings.

## The business problem
Gross profit is the measure throughout, because revenue would hide Garden's problem.

## Measured findings
All figures are computed from the data after removing 132 exact duplicate rows. Each finding names its script and tables.

1. **Garden keeps far less of each sale as gross profit.** The gap is the same every month (Garden 46.7–47.2%).

   | Branch | Revenue (USD) | Gross profit (USD) | Gross margin |
   |---|---|---|---|
   | Harbour | 150,099 | 97,503 | 65.0% |
   | Uptown | 55,554 | 34,795 | 62.6% |
   | Garden | 99,531 | 46,696 | 46.9% |

2. **The gap is mostly in recorded unit cost; Garden's lower prices also contribute.** Its prices are about 5% lower than Harbour's.
   - [`GARDEN_CAUSE.md`](GARDEN_CAUSE.md) finds a best-fit factor of 1.4302 (95% interval 1.4297 to 1.4309), every product within cent rounding of it, and no fixed fee per unit. Garden's customers, hours and baskets look like the other branches'.
   - This is consistent with a branch-level standard-cost or allocation rule.
   - Source: `src/margin_analysis.py`, `results/margin_by_branch.csv`, `results/unit_cost_ratio_by_product.csv`.

3. **Each branch has one fixed price list, set as a flat share of Harbour's prices.** All 135 product-branch pairs have exactly one price and one unit cost for all six months. Every Uptown price is 91.2–91.6% of Harbour's and every Garden price is 95.1–95.3%. One multiplier plus cent rounding reproduces all 45 Garden prices (0.9522–0.9526), as it does Garden's costs (1.4299–1.4302); that fits a branch-level rule better than product-by-product setting, but is evidence, not proof ([`docs/price_structure.md`](docs/price_structure.md)). Source: `src/pricing_analysis.py`, `results/pricing_*.csv`.

4. **Tuesday brings about 1.5× the transactions of the Monday, Wednesday, Thursday and Friday average at every branch (1.52–1.56), and weekends are the quietest.** Mean transactions per day, all branches:

   | Mon | Tue | Wed | Thu | Fri | Sat | Sun |
   |---|---|---|---|---|---|---|
   | 178.0 | 284.5 | 186.2 | 180.0 | 197.5 | 128.7 | 155.7 |

   - **Every week.** Tuesday is the busiest day in all 25 full weeks, with weekly ratios of 1.32–1.69. On the same base the weekend is 0.767 [0.745, 0.790] (`results/tuesday_weekday_ratios.csv`).
   - **No sign of a recording error in our tests.** No other day is depleted, there are no copied records, it is not a few event days, and the hours and baskets are unchanged (permutation p = 0.75).
   - **Not a discount day.** 10.1% of Tuesday transactions carry a discount, against 9.4% on other days. The identified-customer share is 64.2% against 63.4%.
   - **What the excess is made of** ([`TUESDAY_DECOMP.md`](TUESDAY_DECOMP.md)). About 95.4 extra transactions a week: 65.3% more distinct customer IDs [62.0%, 68.8%], 0.6% more trips per ID [−0.1%, 1.2%], 34.2% with no Customer ID. 99.1% of Tuesday customers also buy on other days.
   - **Who carries the lift** ([`docs/tuesday_mechanism.md`](docs/tuesday_mechanism.md)). Identified transactions rise 1.535× and anonymous ones 1.477×; the difference, +0.058 [−0.018, +0.140], is not clear. Assuming Customer IDs approximate members, a members-only app or loyalty offer would predict a much larger identified lift, so that trigger is weakened. The lift is also similar across customer-frequency groups and first-seen months. This fits a trigger that reaches every buyer, or a recording pattern; it does not identify one.
   - **When customers come.** Dine-in is about 46% of transactions every hour until 17:00, then jumps to 69.9% at 18:00 at all three branches; 44.2% of traffic comes after 19:00. The step is so sharp and uniform that it may be a till default rather than customer behaviour ([`FINDING_weekend.md`](FINDING_weekend.md)), so check it against receipts from 17:30–18:30 before changing seating or staffing.
   - Source: `src/tuesday_check.py`, `src/tuesday_decompose.py`, `src/daypart_analysis.py`, `results/tuesday_*.csv`, `results/daypart_*.csv`.

5. **A weekday + log-trend forecast beats the seasonal naive baseline 7 days ahead, most of all on Tuesdays.** Rolling origin: for each day from 1 March to 23 June, every candidate is fit on data up to that day and predicts 7 days later, with all features computed at the origin. This is a retrospective backtest with controlled information access; every candidate is reported ([`docs/forecast.md`](docs/forecast.md)).

   | MAE, transactions per branch per day | All | Tuesdays | Other days |
   |---|---|---|---|
   | Dummy (mean to date) | 15.04 | 44.82 | 9.88 |
   | Seasonal naive (same weekday, one week before) | 8.79 | 11.80 | 8.26 |
   | Weekday + trend | 6.65 | 9.26 | 6.20 |
   | **Weekday + log trend** | **6.39** | **8.27** | **6.07** |
   | Gradient boosting with lags | 6.71 | 8.61 | 6.38 |
   | Selected each day on the trailing 28 days | 6.55 | 8.36 | 6.23 |

   Weekday + log trend has 2.39 lower MAE than the baseline, 95% interval [−2.90, −1.79] from a paired bootstrap over 2-week blocks (all branches together); 1- and 3-week blocks give [−2.97, −1.72] and [−2.68, −2.00]. It is better in every target month. Gradient boosting did not beat the simple regression, so we rejected it. The first version (choose on May, score June once: 6.95 against 9.60) agrees. Source: `src/forecast.py`, `results/forecast_rolling_*.csv`, `results/results.csv`.

6. **Harbour's 15% promo on Cold Coffee and Desserts shows no clear evidence of causing extra sales.** A difference-in-differences on daily units, with Garden and Uptown as controls and a bootstrap over weeks, gives +13.7% [+2.0, +27.7] during the promo (March 12 to May 19) and +18.6% [+8.1, +29.2] after it ended. With Garden as the only control the effect is +6.9% [−4.3, +21.0]; with Uptown it is +21.1% [+6.0, +41.1]. Placebos are near zero. Because the rise grew after the promo ended (habits can persist, but a price effect would be expected to fade) and depends on the control branch, we do not credit the promo with it. Source: `src/promo_analysis.py`, `results/promo_*.csv`.

7. **The 10% discount costs $1,706, and we found no evidence it raises basket size beyond what random assignment would produce.** It is on 5.50–5.84% of lines by branch, 5.36–5.92% by month and 5.29–6.16% by weekday (`results/discount_spread.csv`). Discounted transactions look 0.23 items bigger, but shuffling the discount at random across lines produces the same gap. Its effect on visits is untested. Source: `src/discount_analysis.py`, `results/discount_*.csv`.

8. **59% of drink orders carry no food; of the variables we measured, only drink category was linked to the food-with-drink rate.** The attach rate is 40.8% overall, with no detectable difference across branches, hours, weekdays and months. It runs from 38.1% for Cold Coffee to 43.0% for Matcha & Tea (p < 0.0001) under the main rule (most expensive drink); under four other rules Matcha & Tea stays highest and the gap is 4.8–11.8 points. Detail in [`FINDING_8.md`](FINDING_8.md). Source: `src/basket_analysis.py`, `results/basket_*.csv`.

## Decisions
Recommendations follow the simulations in [`EXPERIMENTS.md`](EXPERIMENTS.md). "At stake" is the six-month estimate under the stated assumptions, and also the most the action can cost to implement before it stops paying. Thresholds hold the other assumptions fixed (`results/decision_thresholds.csv`).

**(a) A pilot of practical length can settle it.**

| Action | Evidence | Pilot and rule | At stake | What would change the order |
|---|---|---|---|---|
| Food and evening dessert prompts | 59% of drink orders carry no food; attach rate 38.1%–43.0% by drink | Two 20-week branch-week switchbacks; roll out if the lower 95% bound is above 0 (a true +2.5 points rolls out 84% / 90% of the time; 2.6% with no effect) | $2,171 (food) and $1,295 (dessert) at +2.5 points; they overlap | Worth less than stopping the 10% discount if the attach rate rises less than 1.96 points |
| Price elasticity (Option A, +6.86%) | 0 price changes on 135 price lists; Lebanon CPI +17.25% a year | 26-week chain-wide switchback; it measures the visit fall (91% power at −6.4%), not the profit gain (55% power), so prices are decided from the measured elasticity | $8,096 at elasticity −1 | Option A loses gross profit beyond elasticity −1.67 (a 10.5% fall in units) |

**(b) None of the pilot designs we simulated can settle it: stakes and a cautious default.**

| Action | At stake | Why a pilot cannot settle it | Default |
|---|---|---|---|
| Remove the 10% discount | $1,706 if no visits are lost | Under our simulations a 26-week pilot reaches only a 5.6% loss margin against a 0.99% saving; a true 2.5% loss passes 30% of the time | Keep the discount as it is. A smaller change (for example 5% instead of 10%) halves the saving, and is still a judgement, not a test result |
| Raise the four menu prices 5% | $881 at elasticity −1 (+0.49% of chain gross profit) | Detected 7% of the time at 26 weeks | Do not raise them on the strength of this analysis |
| Price Option B (Garden and Uptown to Harbour's prices) | $4,298 at elasticity −1 | At most 31% power up to 52 weeks | No branch price changes until the elasticity is measured in (a) |
| Saturday offer | $2,601 (central case); ranks below the food prompt above 37.4% shifting | At most 14% power; the Tuesday driver is unknown | None until the Tuesday driver is found |

**Other decisions.**
- **Garden costs:** the invoice audit decides (action 1). The cost fix beats price Option A only if more than 51.0% of the $15,888 gap is real, avoidable cash, and Option B only above 27.1%.
- **Tuesday:** verify (action 2); staff Tuesdays from the forecast.
- **Harbour's 15% promo:** do not extend it without a proper test.
- **Win-back:** no model-targeted campaign (churn model PR-AUC 0.0995 on held-out customers vs 0.0877 baseline).

**Price options (alternatives; do not add them).**
- **Option A, all branches +6.86%** (inflation-matched): +$8,096 at an assumed elasticity of −1, meaning customers cut purchases 1% for every 1% price rise. The range is −$3,907 at elasticity −2 to +$20,922 at 0. It breaks even at −1.67.
- **Option B, Garden and Uptown matched to Harbour's prices** (Garden about +5.0%, Uptown about +9.4%; Harbour unchanged): +$4,298 at elasticity −1 (Garden $2,516, Uptown $1,782). Uptown breaks even at −1.56.
- **Overlap with the Garden cost fix.** With either option Garden sells fewer units, so the cost fix saves less. At elasticity −1 the overlap is $1,019 for Option A (`results/opportunity_cost_price_overlap.csv`) and $757 for Garden's part of Option B (`results/garden_cost_price_combined.csv`).

## Did outside factors cause this?
All branches are treated as being in Greater Beirut, because branch addresses are not in the data. Real-shop values are references, not causes. Brackets are 95% intervals. Weather terms use standard errors clustered by date and a week-block bootstrap. We ran about 14 tests without a multiple-testing correction. Detail: [`docs/outside_factors.md`](docs/outside_factors.md); sources: [`data/README.md`](data/README.md).

![Real shops vs Stories](figures/outside_factors_summary.png)

| Pattern | What we tested (our result; reference) | Verdict | Still possible | Next test |
|---|---|---|---|---|
| Tuesday surge | Local cause: Tuesday ratio 1.52–1.56 at every branch. School and AUB calendar: −0.026 [−0.096, +0.050] with AUB out. Tue/Thu timetable: Thursday 0.971 [0.940, 1.003] of Mon/Wed/Fri. Reference: only the vending machine peaks on Tuesday, at 1.08; the bakery is 0.97; chains peak on Saturday | Not supported by our tests; Stories' peak is unusual | A trigger reaching every buyer (public or delivery-app offer, operations); a data or posting artefact. A members-only offer is weakened | App/loyalty campaign logs for Tuesdays; daily till (Z-report) or bank totals by weekday |
| Daily demand | Holidays −0.5% [−3.9, +3.0] (French bakery +36% [+19, +54]). Temperature within month −0.09% per °C, week-block bootstrap [−0.64, +0.48] (bakery +0.82% [+0.37, +1.27]; intervals overlap). Rain −0.9%, week-block bootstrap [−4.2, +2.7] (bakery −2.6% [−6.9, +2.0]). Cold-drink share +0.08 points per °C [−0.06, +0.22] (one London café +2.2). Ramadan evening share +0.4 points [−1.4, +2.2]. March escalation +2.4% [−2.6, +6.8] vs trend | Not supported by our tests. Bakery-sized effects injected into our series are detected in 94.6% (temperature) and 100% (holiday) of 500 simulations | Effects smaller than the bakery's | — |
| Steady daily counts | Dispersion 0.98, inside the pure-chance range 0.88–1.14 (bakery 8.45, vending machine 1.84, Maven, fictitious, 4.76) | Much steadier than every reference shop | Habitual demand from regulars (98.5% of identified customers bought more than once), a hypothesis; smoothing from how the data was recorded | Daily till totals for a few weeks |
| Growth | +52.6% transactions, January to June, with no price change; the weather change implies a −0.75% change in transactions (−1.78% of the log growth) | Not nominal price rises; no detectable weather effect | More customers or visits; seasonality we cannot see in six months | A second year of data |
| Garden's 1.43× | Brent weekly mean $62.93 to $124.61, ratio moved 0.0001. Arabica −15.4%, all 135 unit costs unchanged. Cost of goods: Garden 53.1%, Harbour 35.0%, Starbucks 31.4% | Fuel and world coffee prices not supported | A branch-level standard-cost or overhead allocation; a real flat supplier surcharge; rent or location costs | Supplier invoices and overhead allocations for 5–10 products |

## Estimated business value
Estimates, kept separate from the measured facts. Six-month figures; per year = six months × 2. The price options and the Garden cost fix are under Decisions; tables by elasticity and the decision thresholds are in [`docs/estimates_detail.md`](docs/estimates_detail.md).
- **Price review basis.** With Lebanon's CPI up 17.25% a year on an even monthly path, Stories' real prices were 6.42% lower by June (modelled), if dollar menu prices track the lira-based CPI. (`results/opportunity_inflation_price.csv`).
- **Saturday, if the Tuesday driver can be copied.** Each branch's actual Saturday basket and margin are used. Some extra visits may be shifted from other days (`results/opportunity_saturday_range.csv`):

  | Scenario | No shifting | Quarter shifted | Half shifted |
  |---|---|---|---|
  | Saturday gains 25% of Tuesday's lift | +$3,468 | **+$2,601** (central case) | +$1,734 (illustrative downside; shifting could be higher) |
  | Saturday gains 50% of Tuesday's lift | +$6,937 | +$5,202 | +$3,468 |
  | Saturday reaches the Mon/Wed/Thu/Fri average | +$7,993 | +$5,994 | +$3,996 |
- **Food with drinks.** A 1 to 5 point rise in the attach rate is worth +$644 to +$4,341 (`results/basket_value_scenarios.csv`). A 10% pairing discount would need a 9.4-point rise to break even. An evening dessert upsell (18:00 onward) of 1 to 5 points, worth +$518 to +$2,589 (`results/daypart_evening_dessert_total.csv`), overlaps with it.
- **10% discount.** Stopping it saves up to $1,706, or $3,412 a year, if no visits are lost.
- **Harbour promo.** If the promo caused all of the rise, its net was +$599, with a range of −$299 to +$1,451 (`results/promo_value.csv`).

## Assumptions and what would change the recommendation
| Assumption | If it is wrong |
|---|---|
| The `Unit Cost` column records money Stories really pays per item | If Garden's cost includes overheads booked differently, no cash is saved; if it is a real supplier surcharge, it may still not be avoidable |
| Price elasticity is between 0 and −2, the same for every product | Beyond −1.67, Option A loses gross profit |
| Lebanon's lira-based CPI is a fair guide to pressure on dollar menu prices | The 6.42% real-price loss is then overstated or understated |
| Tuesday's extra transactions are extra visits | Items per transaction are unchanged on Tuesdays, so there is no sign of split orders; till-session counts would confirm it |
| Extra Saturday visits need no extra labour | Labour cost reduces every Saturday figure |
| The 132 exact duplicates are recording errors | If they are real, revenue rises by $741 (0.24%); nothing else changes |
| Anonymization changed only branch names and IDs | Some patterns could partly reflect that process; Stories can check against its own records |

## Pilots, staffing, menu and customers
- **Pilots** ([`EXPERIMENTS.md`](EXPERIMENTS.md)). Simulated on Stories' own weeks in 4-week blocks, with zero effects, the planned analysis and, for chain-wide pilots, a critical value calibrated on Stories' history (the nominal t gave 8–12% false positives).
- **Staffing** ([`STAFFING.md`](STAFFING.md)). Measured: at a weekly roster horizon (1–7 days ahead, 12 test weeks, April–June) the hourly forecast's error is 1.55 transactions per branch-hour, against 2.15 for the same hour last week and 1.71 for the four-week average; it wins in all 12 weeks. Scenario (assumed service rate, minimum crew and breaks), with staff scheduled hour by hour: a forecast roster leaves 4.1% of branch-hours short, against 5.4% (last week's roster) and 9.6% (flat one person). With 4-hour blocks the forecast roster leaves 2.9% short against 2.6% for last week's, with 315 fewer staff-hours.
- **Menu** ([`MENU.md`](MENU.md)). Profit is spread out (the top 10 products earn 35.9%), and low margin or volume is no reason to drop an item, since its buyers also buy other items. A 5% rise on four frequent, below-median-margin items cannot be confirmed by a practical pilot, so we do not recommend it on this analysis.
- **Customers** ([`CUSTOMERS.md`](CUSTOMERS.md)). Lapses could not be predicted at either of two prediction origins with equal three-month feature windows (a sensitivity check; May overlaps), so we recommend no model-targeted win-back.

## Weak areas and uncertainty
- Only six months of data, with no yearly seasonality. Sales grew through the period, so yearly figures (six months × 2) may be too low if growth continues.
- Prices never change in the data, so price sensitivity is assumed, not measured. The forecast is tested over March to June only.
- The Tuesday driver is unknown; the Saturday transfer depends on finding it.
- 36.5% of lines have no Customer ID, so customer figures describe identified customers only.

## Approaches we considered and rejected
- **Estimating price sensitivity from differences between branches.** Branch prices are confounded with location and size, so those differences cannot isolate price.
- **Estimating price sensitivity from the 10% discount.** It is applied at the till to 5.3–6.2% of lines by branch, month and weekday, so it gives no menu-price variation to estimate from.
- **Plain basket "lift", or a model of whether a basket takes food.** Basket size distorts lift, and of the variables measured only drink type was linked to taking food.

## Data and reproduction
Data, column schema, quality checks, external sources and licenses are in [`data/README.md`](data/README.md).

```bash
pip install -r requirements-lock.txt   # exact versions (Python 3.14.8); on another Python use requirements.txt
# place stories_transactions.csv in data/ (see data/README.md)
python run_all.py                # runs all in this order, stops on the first failure
cd src
python margin_analysis.py        # Garden margin and unit costs
python pricing_analysis.py       # prices, structure, Option B
python tuesday_check.py          # Tuesday checks and ratios
python tuesday_decompose.py      # Tuesday excess (TUESDAY_DECOMP.md)
python tuesday_mechanism.py      # who carries the Tuesday lift
python weekend_check.py          # weekend offset, 18:00 step (FINDING_weekend.md)
python forecast.py               # rolling-origin forecast
python promo_analysis.py         # Harbour 15% promo
python discount_analysis.py      # 10% discount
python basket_analysis.py        # food with drinks
python external_factors.py       # weather, calendar, school, cost checks
python benchmarks.py             # published coffee-chain benchmarks
python garden_cost_cause.py      # Garden cost-cause tests (GARDEN_CAUSE.md)
python reference_compare.py      # public shop datasets (Kaggle, see below)
python weather_power.py          # weather power simulation
python outside_summary.py        # outside-factors figure
python opportunity_estimates.py  # Saturday, Option A, decision thresholds
python daypart_analysis.py       # weekday vs weekend, dayparts
python customer_model.py         # churn, two origins, segments (CUSTOMERS.md)
python staffing.py               # hourly forecast, staffing scenario (STAFFING.md)
python menu_profit.py            # menu profit and contribution (MENU.md)
python experiment_power.py       # pilot simulations (EXPERIMENTS.md)
```

`reference_compare.py` needs the Kaggle downloads in `data/README.md`; without them `run_all.py` skips it and uses the committed `results/reference_*.csv`.
