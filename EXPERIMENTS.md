# Pilot specifications and what each can detect

Code: [`src/experiment_power.py`](src/experiment_power.py) (about 40 seconds, seeded; two runs from scratch gave identical output and tables). Tables: `results/experiment_*.csv`. Figure: `figures/experiment_power.png`. Every detection rate below comes from that simulation: **500 simulated pilots per cell**, built from the Jan–Jun 2026 transaction file with an effect injected. None of the effects is a finding; they are sizes we want to be able to detect.

## What the simulations say, in one table
| Pilot | Unit randomised | Length simulated | Smallest effect detected with 80% power | Realistic size (from our estimates) | Chance of detecting it |
|---|---|---|---|---|---|
| 1 Food prompt | branch-week | 12 / 16 weeks | 3.6 / 2.8 points | +1 to +5 points | 1 pt: 16% / 19%; 2.5 pts: 65% / 78%; 5 pts: 99% / 100% |
| 2 Evening dessert upsell | branch-week | 12 / 16 weeks | 3.6 / 2.6 points | +1 to +5 points | 1 pt: 14% / 21%; 2.5 pts: 66% / 79%; 5 pts: 100% / 100% |
| 3 Price test (+6.9%) | chain-week | 20 / 26 weeks | 6.8% / 5.8% of weekly gross profit | +4.5% (if demand elasticity is −1) | 59% / 65% |
| 4 Discount removal | chain-week | 20 / 26 weeks | 6.8% / 6.0% | +0.99% (the whole prize) | 7% / 9% |
| 5 Saturday offer | chain-week | 26 weeks | not reached (even at a 50% Saturday lift: 57%) | Saturday lift of about 19% | 15% |

**The pilots for the food prompt and the evening upsell are well powered. The three chain-wide pilots (price, discount, Saturday) are not, for gross profit.** Weekly chain gross profit moves by several percent from week to week (the 95% interval of an effect estimate is about ±3.8% after 26 weeks, ±4.8% after 16), so a pilot cannot confirm a 1–4% gain. We say this plainly instead of promising a confirmation. For each of those three the spec below says what the pilot can still learn and what rule it supports.

## Rules that apply to every pilot
- **Randomise on a schedule written in advance** (below), with a random start week and random branch labels. Balanced: each branch is treated half the time and every week has treated and control branches (branch-week designs); each ABBA block has two treated and two control weeks (chain-wide designs).
- **Measure with a counterfactual, not before/after.** The estimate is the difference between treated and control branch-weeks (or weeks) after removing branch, week, weekday and trend effects. A before/after comparison would mix the effect with growth (chain transactions grow about 1.9% per week in the data), Tuesday and the calendar.
- **Washout.** The Monday after any switch is dropped (branch-week designs: for the branch that switched; chain-wide designs: Monday of every week is dropped, so every week is analysed on Tuesday–Sunday). Staff are briefed the Friday before a switch. We also check carry-over by adding "the previous week was treated" to the model; if it is clearly non-zero, the first week after each treated week is dropped and the pilot is extended by the weeks lost.
- **Multi-branch customers (93.8% of identified customers use more than one branch).** Pilots 1 and 2 act at the till on one transaction, so a customer who visits two branches is treated or not per transaction, and the outcome is measured per transaction; contamination between branches is small. Pilots 3, 4 and 5 change what a customer sees at every branch, so they are **chain-wide week-level switchbacks**: all three branches change together, which removes switching of customers between treated and untreated branches. The primary metric for those is chain-wide gross profit.
- **Do not overlap pilots 3, 4 and 5** (they all change the chain for whole weeks), and run 1 and 2 one after the other (see the plan at the end). An overlap with another change would be confounded, and we have not simulated it.
- **Decision rule.** Each rule is a threshold on the lower or upper end of the 95% interval of the estimated effect, set before the pilot. We simulated how often each rule says "roll out" or "revert" for a given true effect (`results/experiment_rollout_rules.csv`).

## How the simulation works (and what it leaves out)
- The 25 full Mon–Sun weeks (5 Jan to 28 Jun) are cut into week × branch × weekday cells. The chain's growth trend is divided out, whole weeks are resampled with replacement (the same week for all three branches, so shocks shared by the branches stay shared), and the trend is put back over the pilot's length. So the noise is the real week-to-week and day-to-day variation, and the pilot sees growth.
- An effect is injected into the treated cells. Rates (pilots 1, 2): each non-event transaction becomes an event with probability x ÷ (1 − base rate), a binomial draw. Gross profit (pilots 3, 4): the treated week's gross profit × (1 + e). Saturday offer: treated Saturdays × (1 + lift), with 25% of the extra taken back from that week's Monday–Friday (assumed displacement).
- Each simulated pilot is analysed with the model given in its section. A "detection" is a two-sided p < 0.05 with the right sign. With no effect injected the models flag 2% to 7% of simulated pilots (mean 5.1%, 40 cells), so they are calibrated.
- **Limits.** Weeks are resampled independently, so autocorrelation, holidays, Ramadan and school terms are only present as ordinary noise; if anything the true noise is larger and the power lower. Only whole-week shocks that happened in these 25 weeks are available. Effects are assumed to start at once and stay constant.

Value anchors measured from the file (`results/experiment_anchors.csv`): the chain sells about 906 drink transactions a week, and a drink + food basket earns $3.70 of food gross profit, so **+1 point of attach rate is worth about $33 a week**. About 660 transactions a week are from 18:00, and a dessert basket earns $3.15, so **+1 point of evening dessert rate is worth about $21 a week**. Mean weekly chain gross profit is $6,922, and the 10% discount costs $66 a week.

---

## Pilot 1: food prompt (suggest a food item with a drink)
- **Question.** Does a till prompt raise the share of drink transactions that include food? (Under-sold pairs: Cold Drinks + Bakery, Matcha & Tea + savoury items; see `FINDING_8.md`.)
- **Unit of randomisation:** branch × week. Treatment = every drink order at that branch that week gets the prompt.
- **Schedule (6-week cycle, repeated; 1 = prompt on):**

  | Week | Garden | Harbour | Uptown |
  |---|---|---|---|
  | 1 | 1 | 0 | 0 |
  | 2 | 0 | 1 | 1 |
  | 3 | 0 | 1 | 0 |
  | 4 | 1 | 0 | 1 |
  | 5 | 0 | 0 | 1 |
  | 6 | 1 | 1 | 0 |
  | 7–12 | repeat weeks 1–6 | | |

  Before starting, permute the three branch columns at random and start the cycle at a random week; the table above is the pattern. Each branch is treated in 3 of every 6 weeks, and no week is all treated or all control.
- **Duration:** 12 weeks (two full cycles, exactly balanced). 16 weeks gives more power but ends in a part cycle; both were simulated.
- **Primary metric:** attach rate = share of drink transactions that contain a food item, in points. **Chain-wide gross profit is not the primary metric here**: the prompt works inside one visit at one till and we see no sign of customers moving between branches for it. Weekly chain gross profit, drinks per transaction and average ticket are watched as guardrails (a fall in drinks per transaction would mean customers swap a drink for food).
- **Analysis model:** rate for branch *b* on day *d* of week *w* = β · prompt(b, w) + branch effect + week effect + weekday effect, weighted by the number of drink transactions, with standard errors clustered by week and t critical values with (weeks − 1) degrees of freedom. The week effect gives each treated branch its counterfactual from the control branches in the same week.
- **Carry-over:** Monday of a switched branch-week is dropped; checked with a "previous week treated" term.
- **Power** (500 simulated pilots, detection rate):

  | True gain | 4 weeks | 6 | 8 | 12 | 16 |
  |---|---|---|---|---|---|
  | +1 point | 9% | 11% | 13% | 16% | 19% |
  | +2.5 points | 26% | 36% | 45% | 65% | 78% |
  | +5 points | 61% | 83% | 92% | 99% | 100% |

  Median 95% interval half-width: ±2.0 points at 12 weeks, ±1.8 at 16. Smallest gain detected with 80% power: 3.6 points at 12 weeks, 2.8 at 16.
- **Rollout rule (set M, the minimum worthwhile gain, from Stories' own cost of the prompt; we use M = 1 point = about $33 a week as a placeholder):** roll out chain-wide if the lower 95% bound of β is at least M. Simulated: with no effect the rule fires 0.2% of the time; with a true +2.5 points it fires 32% of the time at 12 weeks (33% at 16); with +5 points 95% (99% at 16). A true gain of 1 point is almost never confirmed (4%). So the pilot rolls out a prompt only when it works well (about 4 points or more); smaller gains stay "not shown".
- **If the interval includes M but not 0:** do not roll out yet; continue 4 more weeks or keep the prompt only at the branches where it ran.

## Pilot 2: evening dessert upsell
- **Question.** Does suggesting a dessert (or a drink-and-dessert bundle) from 18:00 raise the share of evening transactions that include a dessert? (Half of all transactions are from 18:00.)
- **Unit of randomisation, schedule, duration, analysis, carry-over:** the same as pilot 1; the prompt is switched on only from 18:00 on treated branch-weeks.
- **Primary metric:** dessert rate = share of transactions from 18:00 that contain a dessert (baseline 15.9%), in points. Guardrails: evening gross profit per transaction, average ticket, and queue time if Stories records it.
- **Run it after pilot 1, not at the same time.** A prompt for food (pilot 1) already includes dessert, so the two outcomes overlap. Running both at once was not simulated; splitting by hour (pilot 1 before 18:00, pilot 2 from 18:00) would halve pilot 1's transactions and raise its smallest detectable gain by roughly 40%, which we have not simulated either.
- **Power:**

  | True gain | 4 weeks | 6 | 8 | 12 | 16 |
  |---|---|---|---|---|---|
  | +1 point | 9% | 9% | 13% | 14% | 21% |
  | +2.5 points | 23% | 33% | 44% | 66% | 79% |
  | +5 points | 59% | 85% | 97% | 100% | 100% |

  Smallest gain with 80% power: 3.6 points at 12 weeks, 2.6 at 16.
- **Rollout rule:** same form as pilot 1, with M = 1 point (about $21 a week). Simulated: fires 0–0.2% with no effect, 28% (12 weeks) and 38% (16 weeks) for a true +2.5 points, 98–100% for +5 points.
- **Caveat on the 18:00 step:** the evening takeaway and dine-in shares change abruptly at 18:00 (`FINDING_weekend.md`), which may be a till default. If order type is recorded by a default, check the counts of evening transactions are not affected by the switch.

## Pilot 3: price test
- **Question.** What happens to units and gross profit if every menu price rises about 6.9% (the inflation-matched rise in `results/opportunity_inflation_meta.csv`: 6.856%)?
- **Unit of randomisation:** chain-week. All branches, all menu items, app and menu boards change together on Monday of a treated week and change back on Monday of a control week. Chain-wide because most customers use several branches; a branch-level price test would let a customer buy in the cheaper branch.
- **Schedule (ABBA, 0 = current prices, 1 = +6.9%; random choice of ABBA or BAAB at the start):**

  | Weeks | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | … |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|---|
  | Price | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 0 | repeat |

  The pattern balances any steady trend: treated and control weeks have the same average week number.
- **Duration:** 20 weeks (five ABBA blocks). 26 weeks if affordable.
- **Primary metric:** chain gross profit, Tuesday–Sunday of each week. **Co-primary:** chain transactions (visits), because the visit effect is what tells us the demand elasticity.
- **Analysis model:** weekly chain gross profit = α + β · treated week + γ · week number, ordinary least squares, t with (weeks − 3) degrees of freedom; β is shown as a percent of mean weekly gross profit with a 95% interval. The same model on weekly transactions gives the visit effect. (There is one observation per week, so "clustered by week" and ordinary standard errors coincide; the week is the unit.)
- **Carry-over:** Monday dropped; the previous week's state is added to the model as a check; customers may buy ahead of a known price rise or delay purchases after it, which a weekly switch makes more likely than a one-off change. If the previous-week term is clearly non-zero, the estimate is biased and the pilot's result is reported with that caveat.
- **Power for chain gross profit** (detection rate): 

  | True effect on weekly GP | 8 weeks | 12 | 16 | 20 | 26 |
  |---|---|---|---|---|---|
  | +1% | 4% | 6% | 7% | 7% | 6% |
  | +2.5% | 11% | 15% | 18% | 22% | 23% |
  | **+4.5% (central case, elasticity −1)** | 25% | 34% | 45% | 59% | 65% |
  | +5% | 26% | 40% | 53% | 58% | 72% |
  | +7.5% | 49% | 71% | 84% | 89% | 97% |

  Median 95% half-width: ±4.3% at 20 weeks, ±3.8% at 26.
- **Power for the visit effect** (detection of a fall in chain transactions): a 5% fall is detected 63% of the time at 16 weeks, 72% at 20 and 84% at 26. A 6.4% fall (what elasticity −1 would give) is detected 84% at 16, 90% at 20 and 95% at 26 weeks. So a 20-week pilot **can measure whether demand falls about as much as elasticity −1 predicts**, but it cannot confirm the resulting gain in gross profit.
- **Rollout rule (simulated; the break-even is a 10.5% fall in units, from `opportunity_inflation_meta.csv`):**
  - **Roll out the price rise if the lower 95% bound of the estimated gross-profit effect is above 0.** **Revert if the upper bound is below 0.** Otherwise keep current prices.
  - Simulated rates of "roll out": if the true effect is +4.5% (units −6.4%): 54% at 20 weeks, 63% at 26. If +8.0% (units −3.3%): 91% at 20 weeks, 97% at 26. If +1.6% (units −9%): 12–13%. If 0 (units −10.5%): 2%. If −2.2% (units −12.4%): 0–1%. So the rule almost never rolls out a price rise that loses money, and rolls out a clearly good one, but misses a moderate gain (+4.5%) about 4 times in 10.
  - A second rule using only the visit effect (roll out if the lower bound of the visit effect is above −10.5%) behaves almost the same (56% at 20 weeks for a true −6.4%), so it adds nothing.
- **Practical note:** the largest uncertainty after the pilot is the effect on customers' goodwill and loyalty, which weekly sales cannot show.

## Pilot 4: discount removal (stop the blanket 10% discount)
- **Question.** If the 10% discount is switched off, do visits fall enough to wipe out the saving?
- **Unit of randomisation:** chain-week (the discount is applied at the till to about 8.3% of transactions at every branch, and customers use several branches), ABBA schedule exactly as pilot 3, with 1 = discount off.
- **Duration:** 20 weeks.
- **Primary metric:** chain gross profit (Tuesday–Sunday). Secondary: chain transactions, share of discounted transactions (should fall to zero in treated weeks), average ticket.
- **Analysis model:** the same weekly model as pilot 3.
- **The prize is too small to confirm.** The saving if no visits are lost is $66 a week, 0.99% of weekly gross profit. At 20 weeks the 95% interval is about ±4.3%, so the pilot detects a gain of 1% in 7% of simulated pilots. It cannot confirm the saving or rule out a small loss.
- **What it can do:** act as a **safety check against a large loss**. The break-even is a loss of 10.0% of the discounted transactions, which is **0.83% of all chain transactions**; that is far below what a pilot can see (visit effects of 5% are detected 72% of the time at 20 weeks, 84% at 26; 2.5% only 28–33%).
- **Rollout rule:** the saving is mechanical (it is the discount no longer given), so **remove the discount unless the pilot shows a loss: revert if the upper 95% bound of the gross-profit effect is below 0.** Simulated "revert" rates: true effect +0.99%: 0.8% at 20 weeks; 0: 2.6%; −2.5%: 22%; −5%: 64%; −7.5%: 92% (at 26 weeks: 0.4%, 2%, 25%, 78%, 97%). A loss of 5% of weekly gross profit would be caught about two times in three at 20 weeks. Losses smaller than about 2.5% would not be caught, so the pilot is a guard against a disaster, not a proof of benefit.

## Pilot 5: Saturday transfer (copy the Tuesday driver onto Saturday)
- **Question.** If Stories finds what drives Tuesday (campaign, app push, routine; not in our data) and runs the same thing on Saturday, does weekly gross profit rise, once visits shifted from other days are counted?
- **Prerequisite:** the Tuesday driver is unknown (`TUESDAY_DECOMP.md`). This pilot can only start after Stories identifies it from campaign logs.
- **Unit of randomisation:** chain-week (offer on Saturday of treated weeks at every branch), ABBA as in pilot 3. Chain-wide so that customers moving between branches or between days stay inside the measured total.
- **Duration:** 26 weeks maximum (what we simulated).
- **Primary metric:** **chain gross profit for the whole week, Monday–Sunday**, not Saturday alone, so displaced visits count against the offer. Analysis: weekly gross profit = α + β · treated week + γ · week number, OLS, t with (weeks − 3) degrees of freedom.
- **Power: not sufficient.** Saturday is 10.1% of weekly gross profit. A 25% Saturday lift is +2.5% of the week before displacement, +1.9% after the assumed 25% displacement.

  | Saturday lift (net effect on weekly GP) | 8 weeks | 12 | 16 | 20 | 26 |
  |---|---|---|---|---|---|
  | 19% (central case, +1.4% of the week) | 5% | 7% | 10% | 12% | 15% |
  | 25% (+1.9%) | 8% | 13% | 13% | 17% | 19% |
  | 50% (+3.8%) | 23% | 33% | 43% | 49% | 57% |

  The central case is detected 15% of the time even after 26 weeks, and even a 50% Saturday lift only 57%. Median 95% half-width of the weekly effect: ±3.4% after 26 weeks.
- **Two alternatives we simulated:**
  1. *Saturday-only metric, chain-wide.* Strong power (a 19% lift is detected 90% at 16 weeks, 99% at 26), but it **ignores displacement**, so it can only show that Saturday sales rise, not that gross profit rises overall. Use it as stage 1, never as the profit result.
  2. *Branch-week Saturday offer with the branch's weekly gross profit* (the schedule of pilot 1; branch and week effects; log gross profit): power is better but still low at the central case (24% at 26 weeks; 50% lift: 87%). It cannot see customers who move between branches (93.8% use several), so it is biased upward if they do. Not recommended as the decision metric.
- **Recommended path:** stage 1 (12 weeks, chain-wide ABBA, Saturday metric): does the offer lift Saturday at all? If yes, stage 2: apply the README's displacement scenarios (25% to 50%) to the stage-1 lift and treat the result as an estimate; a direct profit confirmation of the central case is not possible with weekly data.
- **Rollout rule:** roll out if the lower 95% bound of the Saturday lift (stage 1), reduced by 50% for displacement, still covers the offer's cost; state the cost beforehand. A before/after comparison is not accepted.

---

## Weeks written out (example before randomising the start)
`results/experiment_schedules.csv`; 1 = treated:

| Week | Pilots 1 & 2: Garden | Harbour | Uptown | Pilots 3, 4, 5: all branches |
|---|---|---|---|---|
| 1 | 1 | 0 | 0 | 0 |
| 2 | 0 | 1 | 1 | 1 |
| 3 | 0 | 1 | 0 | 1 |
| 4 | 1 | 0 | 1 | 0 |
| 5 | 0 | 0 | 1 | 0 |
| 6 | 1 | 1 | 0 | 1 |
| 7 | 1 | 0 | 0 | 1 |
| 8 | 0 | 1 | 1 | 0 |
| 9 | 0 | 1 | 0 | 0 |
| 10 | 1 | 0 | 1 | 1 |
| 11 | 0 | 0 | 1 | 1 |
| 12 | 1 | 1 | 0 | 0 |

For 20 weeks the last column continues 0 1 1 0 0 1 1 0 (weeks 13–20).

## A plan that fits the evidence
| Order | Pilot | Weeks | Why |
|---|---|---|---|
| 1 | Food prompt | 12 (16 if affordable) | Well powered; effect worth about $33 a week per point |
| 2 | Evening dessert upsell | 12 | Well powered; about $21 a week per point |
| 3 | Price test | 20 | Cannot confirm the gross profit gain (59% power at the central size) but can measure the visit loss and so the elasticity |
| 4 | Discount removal | 20 | Safety check only; the saving itself is mechanical |
| 5 | Saturday offer | 12 + more | Only after the Tuesday driver is known; stage 1 only |

Steps 1–4 would take about 64 weeks end to end if run one after another. Because only pilots 1 and 2 are well powered, we would start with them, and treat the price and discount changes as decisions made from the estimates in the README with a safety check, not as tests that will confirm a gain.

## Limits of this document
- Effect sizes are injected, not measured; real effects could be smaller or larger, and may change over time.
- The simulated noise is the noise of 25 weeks in one half-year; a year with holidays, Ramadan or school terms may be noisier.
- Pilots 3 to 5 are limited by how much chain gross profit moves from week to week, not by the number of transactions; more weeks help slowly (the interval shrinks about as the square root of the weeks).
- A weekly switchback for prices is unusual and may affect customers' trust; Stories should judge that before running it.
- Thresholds (M = 1 point, 25% displacement) are assumptions we chose; Stories' own cost of running each pilot should replace them.

## Reproduce
```bash
python src/experiment_power.py   # needs data/stories_transactions.csv and results/opportunity_inflation_meta.csv
```
