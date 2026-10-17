# Pilot specifications and what each can detect

Code: [`src/experiment_power.py`](src/experiment_power.py) (about 40 seconds, seeded). Tables: `results/experiment_*.csv`. Figure: `figures/experiment_power.png`. Every detection rate below comes from that simulation: **500 simulated pilots per cell** (1,000 null pilots for each calibrated threshold), built from the Jan–Jun 2026 transaction file with an effect injected, **including an effect of zero** to measure false positives. None of the effects is a finding; they are sizes we want to be able to detect. With 500 pilots a rate has a Monte Carlo standard error of at most ±2.2 points.

**Thresholds.** Every chain-wide pilot (price, discount, Saturday, menu price) is judged with a **calibrated critical value**: the 95th percentile of |t| in 1,000 simulated pilots with no effect, built from Stories' history, and never below the nominal t. This brings their false-positive rate to about 5%. In the same null pilots the nominal t gave 8–12% at 16–26 weeks for the price, discount and Saturday pilots and 5–9% for the menu pilot (`experiment_calibrated_critical.csv`). Every chain-wide power figure, interval and rollout rule below uses it. The branch-week prompt pilots use the nominal t (their false-positive rate is 6–7%); their duration search uses calibrated values too.

## What the simulations say, in one table
| Pilot | Unit randomised | Central effect | Detection at the central effect, 12 / 20 / 26 weeks | Length for 80% power at the central effect | Smallest effect with 80% power at a practical length |
|---|---|---|---|---|---|
| 1 Food prompt | branch-week | +2.5 points | 67% at 12 weeks, 79% at 16 | **20 weeks** (86%) | 3.5 points at 12 weeks, 2.6 at 16 |
| 2 Evening dessert upsell | branch-week | +2.5 points | 67% at 12 weeks, 81% at 16 | **20 weeks** (85%) | 3.5 points at 12 weeks, 2.5 at 16 |
| 3 Price test (+6.9%), gross profit | chain-week | +4.5% of weekly gross profit (elasticity −1) | 31% / 46% / 55% | **Not reached within 52 weeks** (74% at 52) | 6.8% of weekly gross profit at 26 weeks |
| 3 Price test, visits | chain-week | −6.4% transactions (elasticity −1) | 48% / 68% / 82% | **26 weeks** (82%; 89% in the separate duration search) | a 6.3% fall at 26 weeks |
| 4 Discount removal | chain-week | +0.99% (the whole prize) | 6% / 6% / 5% | **Not reachable** (3–8% at every length to 52 weeks) | 7.1% of weekly gross profit at 26 weeks |
| 5 Saturday offer | chain-week | 19% Saturday lift (+1.4% of the week) | 9% / 11% / 13% | **Not reachable** (13% at 52 weeks) | not reached even at a 50% Saturday lift (50% at 26 weeks) |
| 6 Menu price (4 items, +5%) | chain-week | +2.35% of their transactions' gross profit (+$881 per six months) | 6% / 13% / 10% | **Not reachable** (19% at 52 weeks) | 9.5% of their gross profit at 26 weeks |

We treat **26 weeks** as the longest practical pilot. Lengths of 39 and 52 weeks were simulated by reusing the 25 historical weeks, which makes them less reliable. Beyond 52 weeks the simulated growth compounds far past the data and the planned linear trend no longer fits, so we did not use longer lengths.

**Reading.** The two prompt pilots are well powered and reach 80% at their central size in about 20 weeks. The price pilot can measure the visit loss (and so the elasticity) in 26 weeks, but it cannot confirm the gross-profit gain at a practical length. The discount, Saturday and menu-price pilots cannot confirm their central effects at any practical length; at 26 weeks they can only detect effects of about 7% (discount), 9.5% (menu) or a much larger Saturday lift. For those, the pilot works as a safety check against large losses, not as proof of a gain.

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
- **Multi-branch customers (93.8% of identified customers use more than one branch).**
  - **Pilots 1 and 2** act at the till on one transaction, and the outcome is measured per transaction. A customer who sees the prompt at one branch could still change what they buy at another (spillover); the sensitivity section shows what that would do.
  - **Pilots 3 to 6** change what a customer sees at every branch, so they are chain-wide week-level switchbacks. All three branches change together, which removes switching between treated and untreated branches.
- **Do not overlap pilots 3 to 6** (they all change the chain for whole weeks), and run 1 and 2 one after the other.
- **Decision rule.** Each rule is a threshold on the lower or upper end of the 95% interval of the estimated effect, set before the pilot. For chain-wide pilots the interval uses the calibrated critical value. We simulated how often each rule fires for a given true effect (`results/experiment_rollout_rules.csv`).

## How the simulation works (and what it leaves out)
- **Stories' own history, with its dependence kept.** The 25 full Mon–Sun weeks (5 Jan to 28 Jun) are cut into week × branch × weekday cells. The chain's growth trend is divided out, and the weeks are resampled in blocks of 4 contiguous weeks (circular block bootstrap), the same historical weeks for all three branches. This keeps:
  - shocks shared by the branches;
  - each branch's level and weekday pattern;
  - the calendar;
  - week-to-week dependence within a block.

  The trend is put back over the pilot's length.
- **The exact schedule.** Treatment follows the balanced schedule written to `results/experiment_schedules.csv`, with a random start and random branch labels.
- **An effect is injected into the treated cells.**
  - Rates (pilots 1, 2): each non-event transaction becomes an event with probability x ÷ (1 − base rate), a binomial draw.
  - Gross profit (pilots 3, 4, 6): the treated week's gross profit × (1 + e).
  - Saturday offer: treated Saturdays × (1 + lift), with 25% of the extra taken back from that week's Monday–Friday (assumed displacement).
  - Effect 0 is always included.
- **The exact planned analysis.** Each simulated pilot is analysed with the model in its section, including the washout days it drops, and judged at its threshold (calibrated for chain-wide pilots). A "detection" is a significant result with the right sign.

**Calibrated critical values** (`results/experiment_calibrated_critical.csv`; the value used is the larger of the calibrated and nominal t):

| Pilot | 8 weeks | 12 | 16 | 20 | 26 |
|---|---|---|---|---|---|
| Nominal t (weeks − 3 df) | 2.57 | 2.26 | 2.16 | 2.11 | 2.07 |
| 3 Price, gross profit | 2.57 | 2.50 | 2.35 | 2.46 | 2.33 |
| 3 Price, visits | 2.89 | 2.79 | 2.79 | 2.71 | 2.62 |
| 4 Discount removal | 2.94 | 2.30 | 2.40 | 2.45 | 2.45 |
| 5 Saturday offer | 2.57 | 2.43 | 2.44 | 2.38 | 2.37 |
| 6 Menu price | 3.31 | 2.45 | 2.50 | 2.14 | 2.19 |

**False-positive rate by pilot length** (effect 0; chain-wide pilots at the calibrated threshold):

| Pilot | 4 wk | 6 | 8 | 12 | 16 | 20 | 26 |
|---|---|---|---|---|---|---|---|
| 1 Food prompt (nominal t) | 9.6% | 6.0% | 6.4% | 7.0% | 6.2% | | |
| 2 Evening dessert (nominal t) | 7.2% | 6.2% | 5.8% | 6.8% | 5.8% | | |
| 3 Price, gross profit | | | 4.0% | 4.6% | 6.0% | 5.0% | 5.4% |
| 3 Price, visits | | | 6.8% | 5.0% | 4.6% | 4.4% | 3.8% |
| 4 Discount, gross profit | | | 2.8% | 5.8% | 4.4% | 6.2% | 4.4% |
| 5 Saturday, weekly gross profit | | | 5.8% | 5.8% | 4.8% | 5.2% | 6.2% |
| 6 Menu price | | | 4.8% | 7.2% | 5.0% | 6.2% | 6.2% |

With the nominal t the price, discount and Saturday pilots gave 8–12% false positives at 16–26 weeks (the menu pilot 5–9%), because weekly gross profit is correlated from week to week. Newey–West standard errors (lag 3) did not fix it with so few weeks (9–12%; `results/experiment_sensitivity.csv`); calibration does.

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

- **Direction of the bias.** Both carryover and spillover shrink the estimate toward zero: 50% carryover removes about a third of a true effect, and 50% spillover about half. They do not create false positives, so a positive result stays trustworthy; a null result is weaker evidence than its power suggests.
- **Price test (20 weeks, +4.5%, calibrated threshold).** Detection is 43% with no carryover. 50% carryover lowers it to 28% (mean estimate 3.3%). A negative carryover, where customers delay purchases after a rise, raises it to 57% (mean estimate 5.5%), so it would bias the price result upward. The previous-week check in the analysis guards against both.

**Limits.**
- Only shocks that happened in these 25 weeks are available.
- Effects are assumed to start at once and stay constant apart from the carryover cases.
- Lengths over 26 weeks reuse the history.

Value anchors measured from the file (`results/experiment_anchors.csv`):
- **Food prompt.** The chain sells about 906 drink transactions a week, and a drink + food basket earns $3.70 of food gross profit, so **+1 point of attach rate is worth about $33 a week**.
- **Evening dessert.** About 660 transactions a week are from 18:00, and a dessert basket earns $3.15, so **+1 point of evening dessert rate is worth about $21 a week**.
- **Chain.** Mean weekly chain gross profit is $6,922, and the 10% discount costs $66 a week.
- **Menu items.** The four menu items' transactions earn 20.8% of chain gross profit.

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

  Before starting, permute the three branch columns at random and start the cycle at a random week. Each branch is treated in 3 of every 6 weeks, and no week is all treated or all control.
- **Duration:** 12 weeks gives 67% power at the central +2.5 points. **For 80% at +2.5 points, run 20 weeks** (86% with a calibrated threshold); at 16 weeks it is 77%.
- **Primary metric:** attach rate = share of eligible transactions that contain a food item, in points. Weekly chain gross profit, drinks per transaction and average ticket are guardrails.
- **Analysis model:** rate for branch *b* on day *d* of week *w* = β · prompt(b, w) + branch effect + week effect + weekday effect, weighted by the number of eligible transactions, with standard errors clustered by week and t critical values with (weeks − 1) degrees of freedom.
- **Power** (500 simulated pilots, detection rate, nominal t):

  | True gain | 4 weeks | 6 | 8 | 12 | 16 |
  |---|---|---|---|---|---|
  | 0 (false positives) | 9.6% | 6.0% | 6.4% | 7.0% | 6.2% |
  | +1 point | 10% | 9% | 10% | 13% | 19% |
  | +2.5 points | 25% | 35% | 43% | 67% | 79% |
  | +5 points | 59% | 89% | 94% | 100% | 100% |

  Median 95% interval half-width: ±2.0 points at 12 weeks, ±1.8 at 16. Smallest gain detected with 80% power: 3.5 points at 12 weeks, 2.6 at 16.
- **Rollout rule** (M = the minimum worthwhile gain, set from Stories' own cost of the prompt; we use M = 1 point, about $33 a week, as a placeholder): roll out chain-wide if the lower 95% bound of β is at least M.
  - **Simulated:** with no effect the rule fires 0.2% of the time. With a true +2.5 points it fires 28% at 12 weeks (39% at 16), and with +5 points 95% (99%).

## Pilot 2: evening dessert upsell
- **Question.** Does suggesting a dessert (or a drink-and-dessert bundle) from 18:00 raise the share of evening transactions that include a dessert?
- **Eligible population:** every transaction from 18:00, with or without a drink (table above).
- **Unit of randomisation, schedule, analysis, carryover:** the same as pilot 1; the prompt is switched on only from 18:00 on treated branch-weeks.
- **Duration:** **20 weeks for 80% power at +2.5 points** (85% with a calibrated threshold); 12 weeks gives 67%, 16 weeks 78%.
- **Primary metric:** dessert rate = share of eligible transactions that contain a dessert (baseline 15.9%), in points. Guardrails: evening gross profit per transaction, average ticket, and queue time if Stories records it.
- **Run it after pilot 1, not at the same time** (the outcomes overlap).
- **Power** (nominal t):

  | True gain | 4 weeks | 6 | 8 | 12 | 16 |
  |---|---|---|---|---|---|
  | 0 (false positives) | 7.2% | 6.2% | 5.8% | 6.8% | 5.8% |
  | +1 point | 15% | 12% | 12% | 18% | 20% |
  | +2.5 points | 26% | 40% | 47% | 67% | 81% |
  | +5 points | 61% | 86% | 95% | 100% | 100% |

  Smallest gain with 80% power: 3.5 points at 12 weeks, 2.5 at 16.
- **Rollout rule:** same form as pilot 1, with M = 1 point (about $21 a week). Simulated: it fires 0% with no effect, 30% (12 weeks) and 42% (16 weeks) for a true +2.5 points, and 95–99% for +5 points.
- **Caveat on the 18:00 step:** the evening takeaway and dine-in shares change abruptly at 18:00 (`FINDING_weekend.md`), which may be a till default. Check that the counts of evening transactions are not affected by the switch.

## Pilot 3: price test
- **Question.** What happens to units and gross profit if every menu price rises about 6.9% (the inflation-matched rise in `results/opportunity_inflation_meta.csv`: 6.856%)?
- **Unit of randomisation:** chain-week. All branches, all menu items, app and menu boards change together on Monday of a treated week and change back on Monday of a control week.
- **Schedule (ABBA, 0 = current prices, 1 = +6.9%; random choice of ABBA or BAAB at the start):**

  | Weeks | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | … |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|---|
  | Price | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 0 | repeat |

- **Duration:** 26 weeks.
  - **Visit metric:** reaches 80% power at the central visit loss (−6.4%) in 26 weeks (82% in the power table below, 89% in the duration search).
  - **Gross profit:** does not reach 80% at its central +4.5% within 52 weeks (55% at 26 weeks, 74% at 52). The smallest gross-profit effect detectable with 80% power in 26 weeks is 6.8%.
- **Primary metric:** chain gross profit, Tuesday–Sunday of each week. **Co-primary:** chain transactions (visits), because the visit effect is what tells us the demand elasticity.
- **Analysis model:** weekly chain gross profit = α + β · treated week + γ · week number, ordinary least squares. β is shown as a percent of mean weekly gross profit with a 95% interval **at the calibrated critical value**: 2.46 at 20 weeks and 2.33 at 26 for gross profit; 2.71 and 2.62 for visits.
- **Carryover:** Monday dropped; the previous week's state is added to the model as a check.
- **Power for chain gross profit** (detection rate, calibrated threshold):

  | True effect on weekly GP | 8 weeks | 12 | 16 | 20 | 26 |
  |---|---|---|---|---|---|
  | 0 (false positives) | 4.0% | 4.6% | 6.0% | 5.0% | 5.4% |
  | +1% | 3% | 3% | 8% | 6% | 9% |
  | +2.5% | 8% | 11% | 19% | 17% | 22% |
  | **+4.5% (central case, elasticity −1)** | 23% | 31% | 44% | 46% | 55% |
  | +5% | 29% | 37% | 46% | 47% | 60% |
  | +7.5% | 48% | 54% | 73% | 72% | 88% |

  Median 95% half-width: ±5.1% at 20 weeks, ±4.3% at 26.
- **Power for the visit effect** (calibrated threshold): a 5% fall is detected 43% of the time at 16 weeks, 52% at 20 and 65% at 26. A 6.4% fall is detected 59%, 68% and 82% of the time.
- **Rollout rule (calibrated threshold; the break-even is a 10.5% fall in units):** roll out the price rise if the lower 95% bound of the gross-profit effect is above 0, and revert if the upper bound is below 0. Otherwise keep current prices.

  | True units change (gross-profit effect) | Roll out, 20 weeks | 26 weeks |
  |---|---|---|
  | −3.3% (+8.0%) | 84% | 92% |
  | −6.4% (+4.5%) | 47% | 51% |
  | −9.0% (+1.6%) | 12% | 12% |
  | −10.5% (0) | 2.4% | 2.8% |
  | −12.4% (−2.2%) | 0.4% | 0% |

## Pilot 4: discount removal (stop the blanket 10% discount)
- **Question.** If the 10% discount is switched off, do visits fall enough to wipe out the saving?
- **Unit of randomisation:** chain-week (the discount is applied at the till to about 8.3% of transactions at every branch, and customers use several branches), ABBA schedule exactly as pilot 3, with 1 = discount off.
- **Duration:** 20–26 weeks, as a safety check only.
- **Primary metric:** chain gross profit (Tuesday–Sunday). Secondary: chain transactions, share of discounted transactions (should fall to zero in treated weeks), average ticket.
- **Analysis model:** the same weekly model as pilot 3, at its calibrated critical value (2.45 at 20 and 26 weeks).
- **The prize cannot be confirmed at any practical length.**
  - **Size of the prize:** the saving if no visits are lost is $66 a week, 0.99% of weekly gross profit.
  - **Detection:** at that size it is detected 3–6% of the time at every length up to 26 weeks, no better than no effect, and 7% at 52 weeks.
  - **What 26 weeks can detect:** the smallest effect with 80% power is 7.1% of weekly gross profit.
- **What it can do: act as a safety check against a large loss.** The break-even is a loss of 10.0% of the discounted transactions, which is 0.83% of all chain transactions.
- **Rollout rule:** the saving is mechanical, so **remove the discount unless the pilot shows a loss: revert if the upper 95% bound of the gross-profit effect is below 0** (calibrated threshold).

  | True gross-profit effect | Revert, 20 weeks | 26 weeks |
  |---|---|---|
  | +0.99% | 0.6% | 0.6% |
  | 0 | 1.6% | 2.0% |
  | −2.5% | 18% | 20% |
  | −5% | 54% | 63% |
  | −7.5% | 80% | 89% |

  A 5% loss would be caught a little over half the time at 20 weeks; losses smaller than about 2.5% would usually not be caught.

## Pilot 5: Saturday transfer (copy the Tuesday driver onto Saturday)
- **Question.** If Stories finds what drives Tuesday (not in our data) and runs the same thing on Saturday, does weekly gross profit rise once visits shifted from other days are counted?
- **Prerequisite:** the Tuesday driver is unknown (`TUESDAY_DECOMP.md`, `docs/tuesday_mechanism.md`). This pilot can only start after Stories identifies it.
- **Unit of randomisation:** chain-week, ABBA as in pilot 3.
- **Primary metric:** **chain gross profit for the whole week, Monday–Sunday**, so displaced visits count against the offer. Analysis as pilot 3, at its calibrated critical value (2.38 at 20 weeks, 2.37 at 26).
- **Power: not sufficient at any practical length.** Saturday is 10.1% of weekly gross profit; a 19% Saturday lift is +1.4% of the week after 25% displacement. It is detected 13% of the time at 26 weeks and 13% at 52.

  | Saturday lift | 8 weeks | 12 | 16 | 20 | 26 |
  |---|---|---|---|---|---|
  | 0 (false positives) | 5.8% | 5.8% | 4.8% | 5.2% | 6.2% |
  | 19% (central case) | 7% | 9% | 10% | 11% | 13% |
  | 25% | 8% | 11% | 15% | 14% | 17% |
  | 50% | 25% | 31% | 38% | 45% | 50% |

- **Two alternatives we simulated:**
  1. *Saturday-only metric, chain-wide* (calibrated threshold). A 19% lift is detected 67% of the time at 16 weeks and 89% at 26, but this metric **ignores displacement**. It can only show that Saturday sales rise.
  2. *Branch-week Saturday offer with the branch's weekly gross profit* (nominal t; not chain-wide). It detects the central case 18% of the time at 26 weeks and a 50% lift 86% of the time. It cannot see customers who move between branches, so it is biased upward if they do.
- **Recommended path:** stage 1 (12 weeks, chain-wide ABBA, Saturday metric): does the offer lift Saturday at all? If yes, apply the README's displacement scenarios to the stage-1 lift and treat the result as an estimate.

## Pilot 6: menu price test (4 items)
- **Question.** Does a 5% rise on the four frequent, below-median-margin items (Iced Matcha, Strawberry Matcha, Cinnamon Roll, Chocolate Croissant; `MENU.md`) raise gross profit, once buyers who drop or swap the item are counted?
- **Unit of randomisation:** chain-week, ABBA as in pilot 3. All branches change the four prices together.
- **Primary metric:** weekly gross profit (Tuesday–Sunday) of every transaction that contains any of the four items, own plus accompanying items. These transactions earn 20.8% of chain gross profit.
- **Analysis model:** as pilot 3 on this outcome, at its calibrated critical value (2.14 at 20 weeks, 2.19 at 26).
- **Central effect:** +2.35% of those transactions' gross profit. This is the +$881 six-month estimate at elasticity −1 from `MENU.md`, which counts only the four items' own profit.
- **Power: not sufficient at any practical length.**

  | True effect on their gross profit | 8 weeks | 12 | 16 | 20 | 26 |
  |---|---|---|---|---|---|
  | 0 (false positives) | 4.8% | 7.2% | 5.0% | 6.2% | 6.2% |
  | +1% | 2% | 4% | 4% | 8% | 6% |
  | **+2.35% (central case)** | 7% | 6% | 8% | 13% | 10% |
  | +5% | 12% | 19% | 20% | 33% | 38% |
  | +10% | 22% | 47% | 59% | 79% | 85% |
  | +15% | 51% | 79% | 86% | 98% | 99% |

  The central effect reaches only 19% power at 52 weeks. The smallest effect detectable with 80% power is 10.4% at 20 weeks and 9.5% at 26, about four times the central estimate. Median 95% half-width: ±6.2% at 26 weeks.
- **Rollout rule:** keep the rise if the lower 95% bound of the effect is above 0 (calibrated threshold). Simulated "keep" rates at 26 weeks: 2.4% with no effect, 15% at the central +2.35%, 34% at +5% and 87% at +10%. A true loss of 2.5% is kept 0.4% of the time.
- **Reading:** the pilot would almost never keep a rise that loses money, but it would also miss the gain the estimate expects. Treat it as a safety check, and decide the rise on cost and price-positioning grounds.

---

## Weeks written out (example before randomising the start)
`results/experiment_schedules.csv`; 1 = treated:

| Week | Pilots 1 & 2: Garden | Harbour | Uptown | Pilots 3–6: all branches |
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

For 20 or 26 weeks the last column continues 0 1 1 0 0 1 1 0 … .

## A plan that fits the evidence
| Order | Pilot | Weeks | Why |
|---|---|---|---|
| 1 | Food prompt | 20 | 80% power at +2.5 points; about $33 a week per point |
| 2 | Evening dessert upsell | 20 | 80% power at +2.5 points; about $21 a week per point |
| 3 | Price test | 26 | Measures the visit loss (82% power at −6.4%), not the gross-profit gain |
| 4 | Discount removal | 20–26 | Safety check only; the saving itself is mechanical |
| 5 | Menu price (4 items) | 20–26 | Safety check only; cannot confirm the central gain |
| 6 | Saturday offer | 12 + more | Only after the Tuesday driver is known; stage 1 only |

## Limits of this document
- Effect sizes are injected, not measured.
- The simulated noise is that of 25 weeks in one half-year, resampled in 4-week blocks; lengths over 26 weeks reuse that history, and a full year may be noisier.
- The chain-wide pilots are limited by how much weekly gross profit moves, not by the number of transactions, and they need the calibrated threshold.
- Carryover and spillover bias the branch-week estimates toward zero; the sizes we simulated (25–50%) are assumptions.
- A weekly switchback for prices is unusual and may affect customers' trust.
- Thresholds (M = 1 point, 25% displacement) are assumptions; Stories' own cost of running each pilot should replace them.

## Reproduce
```bash
python src/experiment_power.py   # needs data/stories_transactions.csv and results from opportunity_estimates.py and menu_profit.py
```
