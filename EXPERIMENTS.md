# Pilot specifications and what each can detect

Code: [`src/experiment_power.py`](src/experiment_power.py) (about 40 seconds, seeded). Tables: `results/experiment_*.csv`. Figure: `figures/experiment_power.png`. Every detection rate below comes from that simulation: **500 simulated pilots per cell** (1,000 for the calibrated critical values), built from the Jan–Jun 2026 transaction file with an effect injected, **including an effect of zero** to measure false positives. None of the effects is a finding; they are sizes we want to be able to detect. With 500 pilots a rate has a Monte Carlo standard error of at most ±2.2 points.

## What the simulations say, in one table
| Pilot | Unit randomised | Length simulated | False positives (no effect) | Smallest effect detected with 80% power | Realistic size (from our estimates) | Chance of detecting it |
|---|---|---|---|---|---|---|
| 1 Food prompt | branch-week | 12 / 16 weeks | 7.0% / 6.2% | 3.5 / 2.6 points | +1 to +5 points | 1 pt: 13% / 19%; 2.5 pts: 67% / 79%; 5 pts: 100% / 100% |
| 2 Evening dessert upsell | branch-week | 12 / 16 weeks | 6.8% / 5.8% | 3.5 / 2.5 points | +1 to +5 points | 1 pt: 18% / 20%; 2.5 pts: 67% / 81%; 5 pts: 100% / 100% |
| 3 Price test (+6.9%) | chain-week | 20 / 26 weeks | 11.4% / 10.0% | 7.2% / 6.1% of weekly gross profit | +4.5% (if demand elasticity is −1) | 54% / 60% (42% / 56% at the calibrated threshold) |
| 4 Discount removal | chain-week | 20 / 26 weeks | 7.8% / 7.8% | 7.3% / 6.3% | +0.99% (the whole prize) | 10% / 14% |
| 5 Saturday offer | chain-week | 26 weeks | 9.8% | not reached (even at a 50% Saturday lift: 57%) | Saturday lift of about 19% | 20% |

**The pilots for the food prompt and the evening upsell are well powered and close to their nominal 5% false-positive rate. The three chain-wide pilots (price, discount, Saturday) are not well powered for gross profit, and their planned test gives too many false positives (8–12% at 16–26 weeks) once week-to-week dependence is kept.** Weekly chain gross profit moves by several percent from week to week (the 95% interval of an effect estimate is about ±3.8% after 26 weeks, ±5.1% after 16), so a pilot cannot confirm a 1–4% gain. For each of those three the spec below says what the pilot can still learn, the corrected threshold to use, and what rule it supports.

## Who is eligible, and the denominator (pilots 1 and 2)
| | Pilot 1: food prompt | Pilot 2: evening dessert prompt |
|---|---|---|
| Hours | All opening hours | From 18:00 only |
| Eligible transactions (denominator) | Every transaction with at least one drink line (about 906 a week) | Every transaction from 18:00, with or without a drink (about 660 a week) |
| Success (numerator) | The transaction also has at least one food line (any food category, desserts included) | The transaction has at least one dessert line |
| Baseline rate | 40.8% | 15.9% |
| Not eligible | Food-only transactions | Transactions before 18:00 |

The two outcomes overlap: an evening drink + dessert counts as a success in both. That is why the two pilots run one after the other, not at the same time.

## Rules that apply to every pilot
- **Randomise on a schedule written in advance** (below), with a random start week and random branch labels. Balanced: each branch is treated half the time and every week has treated and control branches (branch-week designs); each ABBA block has two treated and two control weeks (chain-wide designs).
- **Measure with a counterfactual, not before/after.** The estimate is the difference between treated and control branch-weeks (or weeks) after removing branch, week, weekday and trend effects. A before/after comparison would mix the effect with growth (chain transactions grow about 1.9% per week in the data), Tuesday and the calendar.
- **Washout.** The Monday after any switch is dropped (branch-week designs: for the branch that switched; chain-wide designs: Monday of every week is dropped, so every week is analysed on Tuesday–Sunday). Staff are briefed the Friday before a switch. We also check carryover by adding "the previous week was treated" to the model; if it is clearly non-zero, the first week after each treated week is dropped and the pilot is extended by the weeks lost.
- **Multi-branch customers (93.8% of identified customers use more than one branch).** Pilots 1 and 2 act at the till on one transaction, and the outcome is measured per transaction. A customer who sees the prompt at one branch could still change what they buy at another (spillover); the sensitivity section shows what that would do to the estimate. Pilots 3, 4 and 5 change what a customer sees at every branch, so they are **chain-wide week-level switchbacks**: all three branches change together, which removes switching between treated and untreated branches. The primary metric for those is chain-wide gross profit.
- **Do not overlap pilots 3, 4 and 5** (they all change the chain for whole weeks), and run 1 and 2 one after the other (see the plan at the end).
- **Decision rule.** Each rule is a threshold on the lower or upper end of the 95% interval of the estimated effect, set before the pilot. We simulated how often each rule says "roll out" or "revert" for a given true effect (`results/experiment_rollout_rules.csv`).

## How the simulation works (and what it leaves out)
- **Stories' own history, with its dependence kept.** The 25 full Mon–Sun weeks (5 Jan to 28 Jun) are cut into week × branch × weekday cells. The chain's growth trend is divided out, and the weeks are resampled **in blocks of 4 contiguous weeks** (circular block bootstrap), the same historical weeks for all three branches. This keeps:
  - shocks shared by the branches;
  - each branch's own level and weekday pattern;
  - the calendar, since holidays, Ramadan and school terms stay in their weeks;
  - week-to-week dependence within a block.

  The trend is put back over the pilot's length, so the pilot sees growth.
- **The exact schedule.** Treatment follows the balanced schedule written to `results/experiment_schedules.csv`, with a random start and random branch labels.
- **An effect is injected into the treated cells.**
  - Rates (pilots 1, 2): each non-event transaction becomes an event with probability x ÷ (1 − base rate), a binomial draw.
  - Gross profit (pilots 3, 4): the treated week's gross profit × (1 + e).
  - Saturday offer: treated Saturdays × (1 + lift), with 25% of the extra taken back from that week's Monday–Friday (assumed displacement).
  - Effect 0 is always included.
- **The exact planned analysis.** Each simulated pilot is analysed with the model in its section, including the washout days it drops. A "detection" is a two-sided p < 0.05 with the right sign.

**False-positive rate by pilot length** (effect 0 injected; `results/experiment_power_results.csv`):

| Pilot | 4 wk | 6 | 8 | 12 | 16 | 20 | 26 |
|---|---|---|---|---|---|---|---|
| 1 Food prompt | 9.6% | 6.0% | 6.4% | 7.0% | 6.2% | | |
| 2 Evening dessert | 7.2% | 6.2% | 5.8% | 6.8% | 5.8% | | |
| 3 Price, chain GP | | | 3.8% | 6.0% | 5.8% | 11.4% | 10.0% |
| 3 Price, chain transactions | | | 7.2% | 9.0% | 12.4% | 11.4% | 11.4% |
| 4 Discount, chain GP | | | 2.4% | 7.2% | 7.6% | 7.8% | 7.8% |
| 5 Saturday, chain GP | | | 5.8% | 5.4% | 10.2% | 10.8% | 9.8% |

- **Branch-week pilots (1, 2)** are close to 5% from 6 weeks on (4 weeks is too short: 9.6%).
- **Chain-wide pilots (3–5)** have one observation per week, and weekly chain gross profit is correlated from one week to the next, so the planned OLS test rejects too often at 16–26 weeks. Newey–West standard errors (lag 3) do not fix it with so few weeks: they also give 9–12% (`results/experiment_sensitivity.csv`).
- **The fix.** Use a critical value calibrated on null pilots built from Stories' history (`results/experiment_calibrated_critical.csv`): |t| > 2.44 at 20 weeks and 2.37 at 26 weeks, instead of the nominal 2.11 and 2.07. This brings the false-positive rate back to 5%, at a cost in power: the central +4.5% price effect is detected 42% of the time at 20 weeks and 56% at 26 weeks (the same simulated pilots give 52% and 66% at the nominal threshold).

**Sensitivity to carryover and spillover** (`results/experiment_sensitivity.csv`; the planned analysis is unchanged):
- Carryover = the share of the effect that persists in the control week after a treated week.
- Spillover = the share of the effect that control branches receive in a week when another branch is treated.

| Pilot, length, true effect | No carryover or spillover | Carryover 50% | Spillover 25% | Spillover 50% | Carryover 50% + spillover 25% |
|---|---|---|---|---|---|
| 1 Food prompt, 12 wk, +2.5 pts: detected / mean estimate | 62% / 2.47 | 36% / 1.66 | 42% / 1.83 | 20% / 1.23 | 31% / 1.54 |
| 1 Food prompt, 12 wk, +5 pts | 100% / 5.00 | 84% / 3.33 | 93% / 3.71 | 62% / 2.52 | 76% / 2.99 |
| 2 Evening dessert, 12 wk, +2.5 pts | 68% / 2.46 | 34% / 1.66 | 44% / 1.88 | 21% / 1.21 | 29% / 1.43 |
| 2 Evening dessert, 12 wk, +5 pts | 100% / 4.96 | 83% / 3.28 | 95% / 3.80 | 65% / 2.58 | 69% / 2.84 |
| False positives (effect 0), pilot 1 / 2 | 6.8% / 6.0% | 7.8% / 6.2% | 6.0% / 8.4% | 5.2% / 6.4% | 5.8% / 7.2% |

- Both carryover and spillover **shrink the estimate toward zero**: 50% carryover removes about a third of a true effect, and 50% spillover about half. They do not create false positives, so a positive result stays trustworthy; a null result is weaker evidence than its power suggests.
- For the price test (20 weeks, +4.5%), 50% carryover lowers detection from 52% to 39%. A negative carryover (customers delaying purchases after a rise) raises the estimate to 5.5% and detection to 64%, so it biases the price result upward. The previous-week check in the analysis guards against both.

**Limits.**
- Only shocks that happened in these 25 weeks are available, and blocks of 4 weeks keep dependence only up to that length.
- Effects are assumed to start at once and stay constant apart from the carryover cases.

Value anchors measured from the file (`results/experiment_anchors.csv`):
- **Food prompt.** The chain sells about 906 drink transactions a week, and a drink + food basket earns $3.70 of food gross profit, so **+1 point of attach rate is worth about $33 a week**.
- **Evening dessert.** About 660 transactions a week are from 18:00, and a dessert basket earns $3.15, so **+1 point of evening dessert rate is worth about $21 a week**.
- **Chain.** Mean weekly chain gross profit is $6,922, and the 10% discount costs $66 a week.

---

## Pilot 1: food prompt (suggest a food item with a drink)
- **Question.** Does a till prompt raise the share of drink transactions that include food? (Under-sold pairs: Cold Drinks + Bakery, Matcha & Tea + savoury items; see `FINDING_8.md`.)
- **Eligible population:** every transaction with at least one drink, any hour (table above).
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
- **Primary metric:** attach rate = share of eligible transactions that contain a food item, in points. Weekly chain gross profit, drinks per transaction and average ticket are guardrails (a fall in drinks per transaction would mean customers swap a drink for food).
- **Analysis model:** rate for branch *b* on day *d* of week *w* = β · prompt(b, w) + branch effect + week effect + weekday effect, weighted by the number of eligible transactions, with standard errors clustered by week and t critical values with (weeks − 1) degrees of freedom.
- **Power** (500 simulated pilots, detection rate):

  | True gain | 4 weeks | 6 | 8 | 12 | 16 |
  |---|---|---|---|---|---|
  | 0 (false positives) | 9.6% | 6.0% | 6.4% | 7.0% | 6.2% |
  | +1 point | 10% | 9% | 10% | 13% | 19% |
  | +2.5 points | 25% | 35% | 43% | 67% | 79% |
  | +5 points | 59% | 89% | 94% | 100% | 100% |

  Median 95% interval half-width: ±2.0 points at 12 weeks, ±1.8 at 16. Smallest gain detected with 80% power: 3.5 points at 12 weeks, 2.6 at 16.
- **Rollout rule** (M = the minimum worthwhile gain, set from Stories' own cost of the prompt; we use M = 1 point, about $33 a week, as a placeholder): roll out chain-wide if the lower 95% bound of β is at least M.
  - **Simulated:** with no effect the rule fires 0.8% of the time at 12 weeks (0.2% at 16). With a true +2.5 points it fires 29% (40%), and with +5 points 96% (98%).
  - **Reading:** the pilot rolls out a prompt only when it works well (about 4 points or more), and smaller gains stay "not shown".

## Pilot 2: evening dessert upsell
- **Question.** Does suggesting a dessert (or a drink-and-dessert bundle) from 18:00 raise the share of evening transactions that include a dessert?
- **Eligible population:** every transaction from 18:00, with or without a drink (table above).
- **Unit of randomisation, schedule, duration, analysis, carryover:** the same as pilot 1; the prompt is switched on only from 18:00 on treated branch-weeks.
- **Primary metric:** dessert rate = share of eligible transactions that contain a dessert (baseline 15.9%), in points. Guardrails: evening gross profit per transaction, average ticket, and queue time if Stories records it.
- **Run it after pilot 1, not at the same time** (the outcomes overlap; see the eligibility table).
- **Power:**

  | True gain | 4 weeks | 6 | 8 | 12 | 16 |
  |---|---|---|---|---|---|
  | 0 (false positives) | 7.2% | 6.2% | 5.8% | 6.8% | 5.8% |
  | +1 point | 15% | 12% | 12% | 18% | 20% |
  | +2.5 points | 26% | 40% | 47% | 67% | 81% |
  | +5 points | 61% | 86% | 95% | 100% | 100% |

  Smallest gain with 80% power: 3.5 points at 12 weeks, 2.5 at 16.
- **Rollout rule:** same form as pilot 1, with M = 1 point (about $21 a week). Simulated: it fires 0–0.2% with no effect, 30% (12 weeks) and 41% (16 weeks) for a true +2.5 points, and 96–100% for +5 points.
- **Caveat on the 18:00 step:** the evening takeaway and dine-in shares change abruptly at 18:00 (`FINDING_weekend.md`), which may be a till default. Check that the counts of evening transactions are not affected by the switch.

## Pilot 3: price test
- **Question.** What happens to units and gross profit if every menu price rises about 6.9% (the inflation-matched rise in `results/opportunity_inflation_meta.csv`: 6.856%)?
- **Unit of randomisation:** chain-week. All branches, all menu items, app and menu boards change together on Monday of a treated week and change back on Monday of a control week. Chain-wide because most customers use several branches.
- **Schedule (ABBA, 0 = current prices, 1 = +6.9%; random choice of ABBA or BAAB at the start):**

  | Weeks | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | … |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|---|
  | Price | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 0 | repeat |

- **Duration:** 20 weeks (five ABBA blocks). 26 weeks if affordable.
- **Primary metric:** chain gross profit, Tuesday–Sunday of each week. **Co-primary:** chain transactions (visits), because the visit effect is what tells us the demand elasticity.
- **Analysis model:** weekly chain gross profit = α + β · treated week + γ · week number, ordinary least squares. β is shown as a percent of mean weekly gross profit with a 95% interval. **Use the calibrated critical value** (|t| > 2.44 at 20 weeks, 2.37 at 26), not the nominal t, because the nominal test gives 10–11% false positives here.
- **Carryover:** Monday dropped; the previous week's state is added to the model as a check. Customers may buy ahead of a known price rise or delay purchases after it.
- **Power for chain gross profit** (detection rate, nominal threshold):

  | True effect on weekly GP | 8 weeks | 12 | 16 | 20 | 26 |
  |---|---|---|---|---|---|
  | 0 (false positives) | 3.8% | 6.0% | 5.8% | 11.4% | 10.0% |
  | +1% | 3% | 8% | 8% | 12% | 11% |
  | +2.5% | 7% | 17% | 24% | 27% | 28% |
  | **+4.5% (central case, elasticity −1)** | 19% | 36% | 49% | 54% | 60% |
  | +5% | 28% | 47% | 51% | 61% | 71% |
  | +7.5% | 53% | 67% | 77% | 82% | 91% |

  At the calibrated threshold the central +4.5% is detected 42% of the time at 20 weeks and 56% at 26. Median 95% half-width: ±4.4% at 20 weeks, ±3.8% at 26.
- **Power for the visit effect** (detection of a fall in chain transactions):
  - **What it detects:** a 5% fall 59% of the time at 16 weeks, 68% at 20 and 76% at 26. A 6.4% fall (what elasticity −1 would give) is detected 77%, 84% and 93% of the time.
  - **Calibration:** this metric's false-positive rate is 11–12% at 16–26 weeks, so it also needs a calibrated threshold, which we have not computed for it.
  - **Reading:** a 20-week pilot can show whether demand falls by roughly as much as elasticity −1 predicts. It cannot confirm the resulting gain in gross profit.
- **Rollout rule (simulated at the nominal threshold; the break-even is a 10.5% fall in units, from `opportunity_inflation_meta.csv`):** roll out the price rise if the lower 95% bound of the gross-profit effect is above 0, and revert if the upper bound is below 0. Otherwise keep current prices.

  | True units change (gross-profit effect) | Roll out, 20 weeks | 26 weeks |
  |---|---|---|
  | −3.3% (+8.0%) | 87% | 94% |
  | −6.4% (+4.5%) | 53% | 65% |
  | −9.0% (+1.6%) | 17% | 19% |
  | −10.5% (0) | 5% | 4% |
  | −12.4% (−2.2%) | 0.6% | 0% |

## Pilot 4: discount removal (stop the blanket 10% discount)
- **Question.** If the 10% discount is switched off, do visits fall enough to wipe out the saving?
- **Unit of randomisation:** chain-week (the discount is applied at the till to about 8.3% of transactions at every branch, and customers use several branches). The schedule is ABBA, exactly as in pilot 3, with 1 = discount off.
- **Duration:** 20 weeks.
- **Primary metric:** chain gross profit (Tuesday–Sunday). Secondary: chain transactions, share of discounted transactions (should fall to zero in treated weeks), average ticket.
- **Analysis model:** the same weekly model as pilot 3, with the calibrated threshold.
- **The prize is too small to confirm.** The saving if no visits are lost is $66 a week, 0.99% of weekly gross profit. At 20 weeks the 95% interval is about ±4.3%, and a +1% gain is "detected" about as often as no effect at all (10% vs 7.8%).
- **What it can do: act as a safety check against a large loss.** The break-even is a loss of 10.0% of the discounted transactions, which is 0.83% of all chain transactions.
- **Rollout rule:** the saving is mechanical, so **remove the discount unless the pilot shows a loss: revert if the upper 95% bound of the gross-profit effect is below 0.**

  | True gross-profit effect | Revert, 20 weeks | 26 weeks |
  |---|---|---|
  | +0.99% | 1.4% | 2.4% |
  | 0 | 5.2% | 6.0% |
  | −2.5% | 27% | 31% |
  | −5% | 61% | 71% |
  | −7.5% | 88% | 93% |

  A 5% loss would be caught about three times in five at 20 weeks; losses smaller than about 2.5% would not be caught.

## Pilot 5: Saturday transfer (copy the Tuesday driver onto Saturday)
- **Question.** If Stories finds what drives Tuesday (not in our data) and runs the same thing on Saturday, does weekly gross profit rise once visits shifted from other days are counted?
- **Prerequisite:** the Tuesday driver is unknown (`TUESDAY_DECOMP.md`, `docs/tuesday_mechanism.md`). This pilot can only start after Stories identifies it.
- **Unit of randomisation:** chain-week, ABBA as in pilot 3.
- **Primary metric:** **chain gross profit for the whole week, Monday–Sunday**, so displaced visits count against the offer. Analysis as pilot 3, with a calibrated threshold.
- **Power: not sufficient.** Saturday is 10.1% of weekly gross profit; a 19% Saturday lift is +1.4% of the week after 25% displacement.

  | Saturday lift | 8 weeks | 12 | 16 | 20 | 26 |
  |---|---|---|---|---|---|
  | 0 (false positives) | 5.8% | 5.4% | 10.2% | 10.8% | 9.8% |
  | 19% (central case) | 5% | 8% | 15% | 17% | 20% |
  | 25% | 11% | 16% | 20% | 20% | 28% |
  | 50% | 21% | 40% | 48% | 51% | 57% |

- **Two alternatives we simulated:**
  1. *Saturday-only metric, chain-wide.* A 19% lift is detected 82% of the time at 16 weeks and 97% at 26, but this metric **ignores displacement**. It can only show that Saturday sales rise, not that gross profit rises overall.
  2. *Branch-week Saturday offer with the branch's weekly gross profit.* Power is low at the central case (20% at 26 weeks; a 50% lift is detected 90% of the time). It cannot see customers who move between branches, so it is biased upward if they do.
- **Recommended path:** stage 1 (12 weeks, chain-wide ABBA, Saturday metric): does the offer lift Saturday at all? If yes, apply the README's displacement scenarios to the stage-1 lift and treat the result as an estimate.

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
| 1 | Food prompt | 12 (16 if affordable) | Well powered, false positives near 5%; about $33 a week per point |
| 2 | Evening dessert upsell | 12 | Well powered; about $21 a week per point |
| 3 | Price test | 20 | Cannot confirm the gross-profit gain (42% power at the central size with the calibrated threshold) but can measure the visit loss |
| 4 | Discount removal | 20 | Safety check only; the saving itself is mechanical |
| 5 | Saturday offer | 12 + more | Only after the Tuesday driver is known; stage 1 only |

## Limits of this document
- Effect sizes are injected, not measured.
- The simulated noise is that of 25 weeks in one half-year, resampled in 4-week blocks; a full year may be noisier.
- The chain-wide pilots are limited by how much weekly chain gross profit moves, not by the number of transactions. Their nominal test is anti-conservative, so the calibrated threshold must be used.
- Carryover and spillover bias the branch-week estimates toward zero. The sizes we simulated (25–50%) are assumptions.
- A weekly switchback for prices is unusual and may affect customers' trust.
- Thresholds (M = 1 point, 25% displacement) are assumptions; Stories' own cost of running each pilot should replace them.

## Reproduce
```bash
python src/experiment_power.py   # needs data/stories_transactions.csv and results/opportunity_inflation_meta.csv (from opportunity_estimates.py)
```
