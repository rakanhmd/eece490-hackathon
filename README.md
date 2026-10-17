# Stories Coffee: Garden pays 43% more for every product and still charges less

**Team:** Rakan Bou Hatoum Hamadeh · Muche Abere Workie
EECE 490 (Introduction to Machine Learning), American University of Beirut · Hackathon, October 17, 2026

## Conclusion
Garden is Stories' biggest profit leak. On every one of its 45 products, Garden's recorded unit cost is 1.43 times Harbour's. Yet its price list is a flat 95% of Harbour's, so it keeps 47% of sales as gross profit against Harbour's 65%. We recommend two steps. First, audit where Garden's extra cost comes from: suppliers, delivery, or how costs are booked. Second, move a random half of Garden's products to Harbour's prices for four weeks and compare them with the other half. If the costs are real and Garden can buy at Harbour's prices, our estimate is about $17,600 more gross profit per six months, roughly $35,600 a year. This assumes customers cut purchases 1% for every 1% price rise, and the range is $14,600–$20,900. About 90% of that gain comes from the cost fix. The main assumption is that the unit-cost column records money Stories really pays. If Garden's cost includes overheads that other branches book elsewhere, most of the saving disappears, which is why the audit comes first. Separately, Tuesday brings about 1.5 times a normal weekday's transactions at every branch, every week. A simple forecast cuts the Tuesday planning error from 15.2 to 9.0 transactions a day compared with "same weekday last week". Public weather, holiday, Ramadan, school and campus data explain none of the surge. The daily counts also show none of the real-world effects we tested, so Stories should confirm the Tuesday pattern against raw till records before changing staffing. 59% of drink orders carry no food. A counter prompt, not a discount, could add an estimated $640 to $4,340 per six months if it lifts the food-with-drink rate by 1 to 5 points. Neither discount we examined shows evidence of paying for itself.

| Rank | Finding and action | Value over 6 months (Jan–Jun) | Measured or estimated |
|---|---|---|---|
| 1 | Garden: bring unit costs to Harbour's level and prices to Harbour's list | +$17,647 at elasticity −1 (range $14,585 to $20,863); about $35,600 a year | Estimated. The cost and price gaps themselves are measured |
| 1a | Of which, cost fix alone | +$15,888 | Estimated. Part of row 1, do not add |
| 1b | Of which, price fix alone | +$2,516 at elasticity −1 (range $174 to $4,975) | Estimated. Part of row 1, do not add |
| 2 | Prompt food with drinks, especially Cold Drinks and Matcha & Tea, with no discount | +$644 to +$4,341; +$2,037 if every drink type reached the best attach rate | Estimated. The 40.8% attach rate and the drink-type gap are measured; the effect of a prompt is not |
| 3 | Uptown: move prices to Harbour's list | +$1,782 at elasticity −1 (range −$1,357 to +$5,216) | Estimated. Can lose money if customers are price-sensitive |
| 4 | Stop or restrict the 10% discount | $1,706 given away; saving up to that if no sales are lost | Cost measured, saving estimated |
| 5 | Harbour 15% promo: do not extend it without a proper test | $470 of discounts given; net +$599 only if the promo caused the rise (range −$299 to +$1,451) | Cost measured, net estimated; causation not shown |
| 6 | Plan Tuesday staffing and stock with the weekday forecast | No dollar figure, because labour costs are not in the data. Tuesday error 9.0 vs 15.2 transactions a day | Measured on June, held-out data |

Rows are ranked by their central estimate. Rows 1 and 3 concern different branches, so they do not overlap. Row 2 is priced at today's food margins, so it does not overlap with row 1. If Garden's costs fall, each extra Garden food basket earns more, which makes adding rows 1 and 2 slightly *understate* the total. A Garden price rise that loses customers would trim row 2 slightly. Removing the 10% discount at Garden or Uptown would slightly raise the price-row gains, which already include discounts as observed.

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

   The gap is the same every month (Garden 46.7–47.2%), so it is stable over time, not a one-off.

2. **The gap comes from unit cost, not price.** For every one of the 45 products, Garden's recorded unit cost is 1.43× Harbour's (range 1.426–1.439). Garden's prices are about 5% *lower* than Harbour's (Uptown's about 9% lower). A uniform 43% markup on every product is consistent with a branch-level cause, such as supplier terms, delivery costs or how costs are allocated to Garden, rather than recipes or waste on specific items. The data cannot tell whether Garden *pays* more or only *books* more.

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

   The placebo on categories not on promo is flat with a tight interval. The Cold Drinks and fake-window placebos are also near zero, but their intervals are too wide to rule out an effect of this size. The pre-promo trend test is inconclusive: −0.28 to +0.62 points per week over only 10 weeks cannot rule out a Harbour-specific trend. Moreover, the gain is *larger after the discount stopped*, Harbour only pulls away about five weeks into the promo, and the size depends on which branch is the control. A discount effect would end when the discount ends. So we do not credit the promo with the rise. Any effect would also come from an offer that reached under a quarter of eligible purchases, and nothing in the data says who got it or why. Source: `src/promo_analysis.py`, `results/promo_*.csv`, `figures/promo_weekly.png`.

7. **The 10% discount does not lead to bigger baskets.** It appears on 5.5–5.8% of lines at every branch, 5.4–5.9% in every month and 5.3–6.2% on every weekday. Known customers get it at the same rate as everyone else, 63.2% vs 63.6% of transactions. Discounted transactions look bigger, with 0.23 more items. But shuffling the discount at random across lines produces the same gap, 0.23, because the discount is applied per line and bigger baskets have more lines to land on. For the same product at the same branch, a discounted line has the same quantity as a full-price one, a difference of +0.0004 units. The basket comparison leaves out the 458 transactions that also contain a 15% promo line. This test covers basket size only. It cannot show whether the discount changes who visits or how often. Discounts given on all 10% lines, January to June: **$1,706**. Source: `src/discount_analysis.py`, `results/discount_*.csv`.

8. **59% of drink orders carry no food, and how often food is added depends only on the drink type.** Drinks are Hot Coffee, Cold Coffee, Cold Drinks and Matcha & Tea. Everything else is food. The "attach rate" is the share of transactions with a drink that also have food, and it is 40.8% overall. 13,865 drink transactions have no food, against 9,563 that do. The attach rate is the same across branches, hours, weekdays and months. It varies only with the most expensive drink in the basket:

   | Segment | Attach rate | Real difference? |
   |---|---|---|
   | Branch: Garden / Harbour / Uptown | 41.8% / 40.2% / 40.9% | No, p = 0.10 |
   | Hour, 17 hours | 39.4% to 43.1% | No, p = 0.89 |
   | Weekday / month | 39.8% to 41.9% / 40.2% to 41.5% | No, p = 0.39 / 0.82 |
   | Drink: Cold Coffee / Cold Drinks / Hot Coffee / Matcha & Tea | **38.1%** / 40.7% / 41.1% / **43.0%** | Yes, p < 0.0001, also after adjusting for branch, hour, day and month |

   The drink-type gap appears inside every branch. Some drink and food pairs sell less often together than item popularity predicts. To test this, we reshuffled items 2,000 times, keeping each basket's size and branch fixed. Cold Drinks + Bakery comes out at 0.63 of the expected count, 605 baskets against 958 expected. It stays at 0.62 when the comparison is limited to baskets that already hold both a drink and food. Matcha & Tea + Meals and + Sandwiches also stay under-sold, at 0.64 and 0.70, under that stricter test. Item-level pairs rest on small counts, so we treat them as pointers only. Food gross profit per drink-and-food basket averages $3.70: $4.22 at Harbour, $4.00 at Uptown and $2.77 at Garden. Garden's figure is lower because of its higher costs. Full write-up: [`FINDING_8.md`](FINDING_8.md). Source: `src/basket_analysis.py`, `results/basket_*.csv`, `figures/basket_attach_by_category.png`, `figures/basket_pair_ratio.png`.

## Did outside factors cause this?
We tested public data against the two biggest patterns: the Tuesday surge and Garden's 43% higher unit costs. **Assumption:** Stories is a Lebanese chain, and branch addresses are not in the data, so we treat all three branches as being in Greater Beirut (lat 33.89, lon 35.50). Weather and calendar are therefore the same for every branch. Datasets, URLs and download dates are in [`data/README.md`](data/README.md). Every result below is an association tested against shuffled versions of the same data, not proof of cause.

**Outside factors we checked.** Brackets are 95% intervals. The p-values come from shuffling weather across days within each month, or calendar labels across weeks.

| Factor | Dataset | Test | Result | Verdict |
|---|---|---|---|---|
| Temperature | Open-Meteo daily max, Beirut | Added to the weekday + log-trend model from finding 5 | −0.21% transactions per °C [−0.64, +0.21], p = 0.29 | does not explain |
| Rain | Open-Meteo precipitation; rain day = 1 mm or more | Same model | −0.9% on rain days [−3.6, +1.9], p = 0.54. Adding both weather terms raises R² by 0.00018, p = 0.56 | does not explain |
| Hot days and cold drinks | Open-Meteo | Cold-drink share of items vs temperature, beyond month and weekday | +0.08 points per °C [−0.06, +0.22], p = 0.31. Share 24.4% in January and 25.0% in June, although June averaged 28.1 °C against 17.4 °C | does not explain |
| January to June growth | Open-Meteo | Weather effect measured within months, applied to the January-to-June change in weather | Weather predicts −0.7% of the observed +52.6% | does not explain |
| Public holidays | holidaydb.com, calendarlabs.com | 26 holiday days vs the same weekday 1–3 weeks before and after | Mean ratio 0.995 [0.961, 1.030] | does not explain |
| Ramadan, Feb 18 to Mar 19 | L'Orient Today | Share of transactions at 18:00 or later vs three weeks before and after | +0.4 points [−1.4, +2.2] vs before; −1.6 points [−3.6, +0.4] vs after | does not explain |
| Security escalation from Mar 2 | Al-Monitor, LBC | Actual sales vs a weekday + trend model fitted on January–February | March +2.4% [−2.6, +6.8]; April +0.8% [−2.2, +5.3]. The same model scored on February gives +5.7%, so errors of about ±6% are normal | does not explain |
| School or campus drives Tuesday | AUB Provost calendar, LBC school closures | Tuesday ratio while AUB was online or out (Mar 30 to Jun 30) vs in person | −0.026 [−0.096, +0.050], p = 0.51. Tuesday is still 1.50× with campus out | does not explain |
| University Tue/Thu timetable | Transactions | Thursday / mean of Mon, Wed, Fri | 0.971 [0.940, 1.003], so Thursday is not raised | does not explain |
| A local cause near one branch | Transactions | Tuesday ratio per branch, holidays excluded | Garden 1.56 [1.49, 1.66], Harbour 1.56 [1.47, 1.65], Uptown 1.53 [1.42, 1.67]. All pairwise gaps include zero | does not explain |
| Normal real-world day-to-day noise | Transactions | Variance ÷ mean of daily counts after weekday × month, vs simulated Poisson counts | Garden 0.86, Harbour 1.10, Uptown 0.99. Pure-chance (Poisson) ranges are about 0.76 to 1.25 | cannot tell (data diagnostic) |
| World coffee price and Garden's costs | IMF arabica price via FRED | Do recorded unit costs move with the world price? | Arabica fell 15.4% from January to June. All 135 product-branch pairs keep one unit cost for all six months | cannot tell |

Source: `src/external_factors.py`, `results/external_*.csv` (summary in `results/external_factors_summary.csv`), `figures/weather_vs_sales.png`, `figures/tuesday_by_branch_school.png`.

**(a) Tuesday.** None of the outside factors we could test explains the surge.
- **Branches.** It is the same size at all three branches, which argues against a local cause such as a school, a market day or an office next to one shop.
- **School and campus.** It did not fade while AUB taught online or after its exams ended. It did not fade in late June either: the June 23 week has the highest ratio of the half-year at 1.74.
- **Thursday.** Thursday is not raised, so a university Tuesday/Thursday timetable cannot explain it.
- **One test was sensitive to how we chose weeks.** Our first version kept only weeks with three or more non-holiday comparison days. It found a small dip when the campus was out, −0.068 [−0.135, −0.001], p = 0.08. Keeping weeks with two comparison days, the version above, the dip shrinks to −0.026, p = 0.51. Either way, Tuesday stays about 1.5 times a normal weekday with the campus out.
- **Calendar caveats.** The school Easter and Eid closures contained no Tuesday. Late June rests on two weeks, one of them a holiday. The end-of-school date of June 15 is our assumption.

**(b) Garden's costs.** Public data cannot explain the 43% gap.
- **Fixed costs.** The recorded unit costs never change in six months, even though the world arabica price fell 15.4%. So the cost column looks like a fixed standard cost, not what Stories paid each month.
- **Location.** With no branch addresses, we cannot test location causes such as rent or delivery distance.
- **Action unchanged.** The cost audit in the conclusion is still the way to find the cause.

**What the null results suggest.** A real café in Beirut would normally show some of these effects. Typical examples are fewer customers on rainy days, more cold drinks in June, different evening traffic in Ramadan, and some change during a war that displaced over a million people. This data shows none of them. Its day-to-day variation is also no larger than pure chance: real shop counts usually vary more than a Poisson model predicts, because of weather, events and promotions. Ratios at or below 1 suggest the daily counts may have been generated or smoothed rather than recorded as they happened. We cannot tell which from the data. Stories' data team can check this against raw till records. This matters most for the Tuesday staffing recommendation and the forecast, which rely on the daily pattern being real.

### How Stories compares with other coffee chains
These published figures are context, not causes. Each is set beside one Stories number, with no correlation computed. Values and URLs are in `data/external/benchmarks.csv`, and the comparison is in `results/benchmarks_comparison.csv`.

| Topic | Published benchmark | Stories, Jan–Jun 2026 |
|---|---|---|
| Busiest day | Saturday, for Starbucks (Placer.ai foot traffic) and for UK coffee purchases (Square) | Tuesday. Saturday is the quietest day |
| Busiest day vs the average weekday, Mon–Fri | UK Saturday: 1.49× (cups sold, Square) | Tuesday: 1.39×; Saturday: 0.63× |
| Cost of goods, % of net sales | Starbucks 31.4%, fiscal 2025 (product and distribution costs, 10-K) | All 41.3%; Harbour 35.0%; Uptown 37.4%; Garden 53.1% |
| Coffee-drink costs, % of coffee sales | Café target 20–25% (Zest, a coffee supplier's rule of thumb) | Harbour 28.8%; Uptown 30.2%; Garden 43.2% |
| Food costs, % of food sales | Café target 25–35% (Zest) | Harbour 39.6%; Uptown 42.1%; Garden 59.9% |
| Growth vs inflation | Lebanon consumer prices +17.25% year on year, June 2026 (Central Administration of Statistics) | Transactions +52.6% from January to June, weekday-adjusted; no price changes on any of the 135 price lists |
| Weather | One London café: cold-coffee share +2.2 points per °C. US coffee shops: less traffic when it rains (Foursquare and AccuWeather, 13 million users) | Cold-drink share +0.08 points per °C [−0.06, +0.22]; −0.9% on rain days [−3.6, +1.9] |

- **Day of week.** We found no published source showing a Tuesday peak, let alone one of 1.5 times the other weekdays. The sources we found put the peak on Saturday, which is Stories' quietest day. This is outside evidence that the Tuesday pattern is unusual.
- **Costs.** Harbour and Uptown are somewhat above Starbucks and above the café targets, which may reflect import costs in Lebanon. Garden is far outside every benchmark: 53.1% overall, 43.2% on coffee and 59.9% on food. The benchmarks support finding 1: Garden is the abnormal branch, not the others.
- **Growth.** The 52.6% rise is in transaction counts, and prices never changed, so inflation cannot produce it. It is three times a full year of consumer-price inflation, reached in five months. Keeping every price fixed for six months while consumer prices rose about 17% in a year is also unusual. One caveat: Stories prices in US dollars, while the inflation rate is measured on Lebanese pounds.
- **Weather.** Industry and trade analyses report that weather moves coffee-shop traffic and the share of cold drinks; we found no peer-reviewed café study. Stories shows neither effect, which is consistent with the daily data being generated rather than recorded.

### How our data compares with real shops
We compared our data with three public transaction datasets from Kaggle, used only as a reference for what shop data looks like. No other shop's pattern is a cause of ours. Licenses and claims are recorded in [`data/README.md`](data/README.md).
- **French bakery.** It claims to be real: one bakery, January 2021 to September 2022.
- **Coffee vending machine.** It claims to be real: one machine, March 2024 to March 2025.
- **Maven Roasters.** Its own description calls it a *fictitious* coffee shop: three New York stores, January to June 2023.

Source: `src/reference_compare.py`, `results/reference_*.csv`, `figures/reference_signatures.png`.

| Signature | Stories | French bakery (real) | Vending machine (real) | Maven (fictitious) | Verdict |
|---|---|---|---|---|---|
| Tuesday / Mon, Wed, Thu, Fri | 1.53 | 0.97 | 1.08 | 0.98 | Ours is unusual |
| Busiest day (ratio to Mon–Fri average) | Tue (1.39) | Sun (1.35) | Tue (1.06) | Fri (1.01) | Ours is unusual |
| Peak hour | 21:00 | 11:00 | 10:00 | 10:00 | Ours is unusual. A late peak may be local habit, so on its own this proves nothing |
| Day-to-day variation, variance ÷ mean after weekday × month | **0.98**; pure-chance range 0.88–1.14 | 8.45 | 1.84 | 4.76 | Ours lacks normal variation |
| Items per transaction | 1.59 | 2.67 | 1.00 | 1.44 | Normal |
| Top-3 category share of items | 52% | 48% | 60% | 85% | Normal |

**Weather and holiday effects in the real bakery.** The test asks whether effects of the bakery's size would show up in our data. We assume the bakery is in Paris, because the dataset names no city, and join Open-Meteo weather and official French holidays. The model is the same as for Stories: log(daily transactions) on weekday, trend, temperature, rain day and holiday. Results are from `results/reference_effect_transfer.csv`:

| Effect | French bakery, 95% interval | Stories, 95% interval | Bakery effect outside our interval? |
|---|---|---|---|
| Temperature, within month (month fixed effects) | +0.82% per °C [+0.37, +1.27] | −0.09% per °C [−0.54, +0.37] | Yes, just. The intervals touch at +0.37 |
| Temperature, no month effects | +3.2% per °C [+2.9, +3.6] | −0.21% per °C [−0.64, +0.21] | Yes, but the bakery figure mixes in its summer season |
| Rain day | −2.6% [−6.9, +2.0] | −0.9% [−3.6, +1.9] | No. Neither is clearly different from zero, so we cannot tell |
| Public holiday | +36% [+19, +54] | −0.5% [−3.9, +3.0] | Yes, by a wide margin |

**Does our data come from the Maven dataset?** Probably not. It shares Maven's framing: January 1 to June 30, three stores and nine categories. But almost everything at row level differs (`results/reference_template_maven.csv`):
- **Products.** Only 3 of our 45 product names appear in Maven: Almond Croissant, Cappuccino and Chocolate Croissant. Only one category name is shared.
- **Prices.** The median price is $5.41 against $3.00.
- **Baskets.** Ours average 1.51 lines per transaction, while Maven always has one.
- **Traffic.** We have 62 transactions per store per day against 275.
- **Hours.** Our hourly profile runs opposite to Maven's, with a correlation of −0.58.
- **Weekdays and noise.** Maven has no Tuesday peak, at 0.98, and its day-to-day variation is 4.76 against our 0.98.

This is evidence, not certainty: the shared framing could be a loose template or a coincidence.

**Verdict.** All three reference datasets vary from day to day far more than chance alone, and so does a fictitious one. None of them has a Tuesday peak near 1.5. Our data sits inside the pure-chance range and has a Tuesday surge no reference shows. The real bakery also has temperature and holiday effects that our data would have detected, and our intervals exclude them. Together these add to the earlier signs that Stories' daily counts lack the normal variation of real shops. The French holiday effect need not apply in Beirut, though: the test shows that effects of this size would be visible in our data, not that Stories should have them.

This day-to-day ratio of 0.98 pools the three branches and uses year-month cells, so the same method fits every dataset. The per-branch figures earlier in this section, 0.86 to 1.10, use the same idea.

## Estimated business value
Estimates, kept separate from the measured facts above.

- If Garden paid Harbour's unit cost for each product, with its current prices and sales, gross profit over the same six months would be **$15,888 higher**. That is about $32,000 a year at the current sales level. Source: `results/garden_cost_price_combined.csv`.
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
- **Garden cost and Garden price together, without double counting.** Garden pays exactly Harbour's unit cost per product, as above. Both changes are computed together from one baseline, not added, because after the cost fix every customer lost to a price rise costs more. Six months, from `results/garden_cost_price_combined.csv`:

  | Elasticity (assumed) | Cost fix only | Price fix only | Both together | Sum of the two (overstated) |
  |---|---|---|---|---|
  | 0 | $15,888 | $4,975 | $20,863 | $20,863 |
  | −1.0 | $15,888 | $2,516 | $17,647 | $18,404 |
  | −2.0 | $15,888 | $174 | $14,585 | $16,062 |
- **Harbour 15% promo.** If all of the measured rise were caused by the promo, the extra units at full-price gross profit would be worth about $1,070 against $470 of discounts, a net +$599. The 95% range is −$299 to +$1,451, over the ten-week window. The promo breaks even at a 5.6% uplift. Because we do not credit the promo with the rise, the true net is probably lower. Source: `results/promo_value.csv`.
- **Stopping the 10% discount.** This would save up to $1,706 per six months, about $3,440 a year, if no sales are lost. Both discounts are small in dollars. The 10% discount is 0.56% of six-month revenue, which was $305,184. We found no sign that it brings extra items, but we cannot see whether it keeps customers coming back.
- **Selling food with more drink orders, finding 8.** The data does not show how much a counter prompt would move the attach rate, so we use scenarios. Each extra basket is priced at the branch's average food gross profit, or at 0.74 of it, which is Bakery's margin. From `results/basket_value_scenarios.csv`, six months:

  | Attach rate rise (assumed) | Bakery-margin add-on | Average food margin |
  |---|---|---|
  | +1 point | +$644 | +$868 |
  | +2.5 points | +$1,611 | +$2,171 |
  | +5 points | +$3,222 | +$4,341 |
  | Every drink type reaches Matcha & Tea's 43.0% | | +$2,037 |

  That is about $1,300 to $8,800 a year. **A pairing discount would lose money.** Ten percent off food bought with a drink would also go to the 9,563 baskets that already carry food. The attach rate would need to rise by 9.4 points just to break even (`results/basket_discount_breakeven.csv`). The recommendation is a prompt or menu placement, not a discount.
- **Cross-branch effect, not in the numbers above.** 94% of known customers already buy at more than one branch. If a Garden price rise moves some customers to Harbour, the chain still keeps 65% gross margin on those sales instead of 47%. Treating lost Garden units as lost to the chain therefore understates the Garden gain. For Uptown, the two margins are close, so moved customers change little.

## Assumptions and what would change the recommendation
| Assumption | Why it matters | If it is wrong |
|---|---|---|
| The `Unit Cost` column reflects real costs Stories pays per item | The Garden finding depends on it | If Garden's cost includes allocated overheads (e.g. higher rent) that other branches book elsewhere, the gap may be an accounting difference with little savings available |
| Garden's higher cost is not buying better quality that supports its sales | Cutting cost could otherwise hurt demand | Savings would be offset by lost sales |
| Price elasticity is between 0 and −2, and the same for every product | Sets the size of the pricing gain | Above about 2.1 in absolute value, raising Garden's prices loses gross profit; for Uptown the limit is about 1.6 |
| Lower prices at Garden and Uptown are not a deliberate response to local competitors | A competitor next door could make customers more price-sensitive than the range we assume | The price rise could lose more customers than estimated; the pilot below would show this |
| The Tuesday surge reflects real customer visits | Staffing and stock plans would follow it | If it comes from how the data was produced or exported, Tuesday staffing should not change until Stories checks its till and footfall records |
| An extra food basket earns the branch's average food gross profit, or 0.74 of it, and does not replace a second drink | Sets the size of the cross-sell gain | If customers swap a drink for a pastry, or prep and waste costs rise, the gain falls; we have no data on either |
| All branches are in Greater Beirut (lat 33.89, lon 35.50); branch addresses are not in the data | Weather and calendar tests use one location for all branches | If branches are far apart, local weather or local events could differ by branch; our tests could not detect a cause that affects only one branch |
| The 132 exact duplicate rows are recording errors, not real repeat purchases | We removed them before all analysis | If they were real, revenue rises by $741, which is 0.24%; no margin or finding changes. Source: `results/duplicates_summary.csv` |
| Garden could buy at Harbour's unit costs | Sets the size of the cost fix, the largest row | If part of the gap is unavoidable, such as a remote location, the gain scales down roughly in proportion |

## A practical test Stories could run
- **Garden costs.** Audit how Garden's costs are recorded. Then run a one-month pilot buying Garden's top 10 products through Harbour's supplier, comparing cost per unit and sales against the previous month and against the other branches.
- **Garden prices.** For four weeks, move a random half of Garden's products to Harbour's price and keep the other half unchanged. Compare units sold between the two halves, with Harbour as a second control. This measures Garden's real price sensitivity before changing the whole list. Garden sold between 2,410 and 3,556 units a month from January to June.
- **Food with drinks.** Add a till prompt suggesting a bakery item with Cold Drinks and a savoury item with Matcha & Tea. Use Harbour as the test branch, with Garden and Uptown as controls. Compare the change in attach rate before and after, and track drinks per transaction to catch swapping. At June volumes, a 5-point rise needs about 22 days to detect and a 3-point rise about 62 days (`results/basket_pilot_power.csv`). Agree the roll-out threshold before starting.
- **Tuesday.** Compare the Tuesday surge with till-session counts, door counters or staff rosters for a few weeks. If it is confirmed, plan Tuesday staffing and stock at about 1.5 times a normal weekday.

## Weak areas and uncertainty
- Only six months of data (January–June), so there is no yearly seasonality.
- Yearly figures multiply the six-month value by 365/181. June revenue was 1.49 times January's at Garden, 1.57 at Harbour and 1.46 at Uptown (`results/revenue_by_month.csv`). If that growth continues, the yearly figures are too low. If it is seasonal, they may be too high. We cannot tell which with six months.
- 36.5% of lines have no Customer ID, and 94% of known customers appear at several branches, so customer-level conclusions are uncertain.
- Prices never change in the data, so price sensitivity is an assumption, not a measurement. The pricing estimates are only as good as the elasticity range.
- We could not find the cause of the Tuesday surge in the data. We can only rule out the recording errors we tested.
- The cross-sell data shows how baskets look today, not how a prompt would change them. We do not know what cashiers say now, where the bakery case sits, or which items were out of stock. Any of these could explain the Cold Drinks + Bakery gap.
- Some calendar dates come from news pages we could only read through search summaries, and the end of the school year is an assumption. Holiday sources disagree by a day on two Islamic dates, so both days are counted.
- The promo analysis compares Harbour with only two control branches, and the result changes with the choice of control.
- The forecast was tested on one month. June continued the January-to-June growth, so a log trend fit well. A change in trend, for example in summer, would hurt it.

## Approaches we considered and rejected
- **Estimating price sensitivity from differences between branches.** Uptown is the cheapest branch but sells the least, so comparing branches would suggest higher prices bring more customers. Location and size drive those differences, not price, so we rejected this.
- **Estimating price sensitivity from the 10% discount.** Discounted lines have the same quantity as full-price lines. But the discount seems to be applied at the till, so customers do not see it when choosing, and it says little about how they react to a posted price.
- **Customer retention or churn models.** 94% of known customer IDs buy at more than one branch, so we do not trust the IDs to track individuals.
- **More complex forecast models.** There are only 151 training days per branch, and a weekday-plus-trend regression already beats the baseline at every branch. We kept the model we can explain.
- **Plain market-basket "lift" for cross-sell.** Most baskets have one or two lines, which distorts lift. A reshuffle that keeps each basket's size fixed avoids this.
- **A model predicting whether a basket takes food.** Branch, hour, day and month carry no signal, and drink type alone explains the 5-point range. A model would add complexity without supporting a decision.
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
python promo_analysis.py      # Harbour 15% promo, 30 seconds to about 2 minutes depending on the machine
python discount_analysis.py   # 10% discount
python basket_analysis.py     # drink + food cross-sell, about 15 seconds
python external_factors.py    # weather, calendar, Tuesday and cost checks against public data in data/external/, about 10 seconds
python benchmarks.py          # Stories next to published coffee-chain benchmarks (run after external_factors.py)
python garden_cost_cause.py   # Garden cost-cause checks (Brent crude, branch profile), written up in GARDEN_CAUSE.md
python reference_compare.py   # comparison with public shop datasets; first download them with the Kaggle API (see data/README.md)
```
Summary tables are saved in `results/`, figures in `figures/`.
