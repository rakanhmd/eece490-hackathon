# Pilot specifications and what each can detect

Code: [`src/experiment_power.py`](src/experiment_power.py) (about 45 seconds, seeded). Tables: `results/experiment_*.csv`. Figure: `figures/experiment_power.png`. Every detection rate below comes from that simulation: **500 simulated pilots per cell** (1,000 null pilots for each calibrated threshold), built from the Jan–Jun 2026 transaction file with an effect injected, **including an effect of zero** to measure false positives. None of the effects is a finding; they are sizes we want to be able to detect. With 500 pilots a rate has a Monte Carlo standard error of at most ±2.2 points.

**Thresholds.** Every chain-wide pilot (price, discount, Saturday, menu price) is judged with a **calibrated critical value**: the 95th percentile of |t| in 1,000 simulated pilots with no effect, built from Stories' history, and never below the nominal t. This brings their false-positive rate to about 5%. In the same null pilots the nominal t gave 8–12% at 16–26 weeks (`experiment_calibrated_critical.csv`). Every chain-wide power figure, interval and rule below uses it. The branch-week prompt pilots' power tables use the nominal t (false positives 6–7%), and their rollout rules and duration search use calibrated values.

## What the simulations say, in one table
| Pilot | Central effect | Detection at the central effect, 12 / 20 / 26 weeks | Length for 80% power at the central effect | At a practical length (26 weeks) |
|---|---|---|---|---|
| 1 Food prompt (branch-week) | +2.5 points | 67% at 12 weeks, 79% at 16 | **20 weeks** (86%) | Rule "lower bound > 0" rolls out a true +2.5 points 84% of the time at 20 weeks |
| 2 Evening dessert prompt (branch-week) | +2.5 points | 67% at 12 weeks, 81% at 16 | **20 weeks** (89%) | Same rule: 90% at 20 weeks |
| 3 Price Option A (+6.9%), gross profit | +4.5% of weekly gross profit | 31% / 46% / 55% | Not within 52 weeks (71% at 52) | 6.8% detectable |
| 3 Price Option A, visits | a 6.4% fall in transactions | 52% / 79% / 91% | **26 weeks** (91%) | a 5.8% fall detectable |
| 3b Price Option B (Garden +5%, Uptown +9.4%) | +2.40% of weekly chain gross profit | 13% / 19% / 20% | Not reachable (at most 31%, at 39 weeks) | 6.9% detectable |
| 4 Discount removal | +0.99% (the whole prize) | 5% / 6% / 7% | Not reachable (5–8% at every length to 52 weeks) | Non-inferiority margin of 5.6% (below) |
| 5 Saturday offer | 19% Saturday lift (+1.4% of the week) | 8% / 10% / 8% | Not reachable (at most 14%) | even a 50% Saturday lift is detected 47% of the time |
| 6 Menu price (4 items, +5%) | +0.49% of chain gross profit | 5% / 4% / 7% | Not reachable (at most 6%) | 6.9% detectable |

We treat **26 weeks** as the longest practical pilot. Lengths of 39 and 52 weeks were simulated by reusing the 25 historical weeks, which makes them less reliable. Beyond 52 weeks the simulated growth compounds far past the data, so we did not use longer lengths.

**What this means for the recommendations.**
- **(a) Testable at a practical length:**
  - **Food and evening dessert prompts:** 20 weeks each, rolled out if the lower 95% bound is above 0.
  - **Price Option A's visit measure:** 26 weeks, which measures the elasticity.
- **(b) Not measurable at a practical length:**
  - **Discount removal:** only a 5.6% loss margin can be guaranteed, against a saving of about 1%.
  - **Menu price:** detected 7% of the time.
  - **Price Option B:** at most 31% power.
  - **Saturday offer:** at most 14% power.
  - **Price Option A's gross-profit gain:** 55% power at 26 weeks.
- **What we recommend for (b):** we do not recommend a pilot as the decision tool for these. The README states their dollar stakes, says the data cannot settle them, and gives a cautious default:
  - keep the discount as it is;
  - do not raise the four menu prices or change branch price lists on this analysis;
  - no Saturday offer until the Tuesday driver is found;
  - decide price levels from the elasticity measured in (a).

## Who is eligible, and the denominator (pilots 1 and 2)
| | Pilot 1: food prompt | Pilot 2: evening dessert prompt |
|---|---|---|
| Hours | All opening hours | From 18:00 onward (the same definition as the README's dessert estimate) |
| Eligible transactions (denominator) | Every transaction with at least one drink line (about 906 a week) | Every transaction from 18:00, with or without a drink (about 660 a week) |
| Success (numerator) | The transaction also has at least one food line (any food category, desserts included) | The transaction has at least one dessert line |
| Baseline rate | 40.8% | 15.9% |
| Not eligible | Food-only transactions | Transactions before 18:00 |

The two outcomes overlap: an evening drink + dessert counts as a success in both. That is why the two pilots run one after the other, not at the same time.

## Rules that apply to every pilot
- **Randomise on a schedule written in advance** (below), with a random start week and random branch labels. Balanced: each branch is treated half the time and every week has treated and control branches (branch-week designs); each ABBA block has two treated and two control weeks (chain-wide designs).
- **Measure with a counterfactual, not before/after.** The estimate is the difference between treated and control branch-weeks (or weeks) after removing branch, week, weekday and trend effects. A before/after comparison would mix the effect with growth (chain transactions grow about 1.9% per week in the data), Tuesday and the calendar.
- **Washout.** The Monday after any switch is dropped (branch-week designs: for the branch that switched; chain-wide designs: Monday of every week is dropped, so every week is analysed on Tuesday–Sunday). Staff are briefed the Friday before a switch. We also check carryover by adding "the previous week was treated" to the model; if it is clearly non-zero, the first week after each treated week is dropped and the pilot is extended by the weeks lost.
- **Multi-branch customers (93.8% of identified customers use more than one branch).** Pilots 1 and 2 act at the till on one transaction, and the outcome is measured per transaction; the sensitivity section shows what spillover between branches would do. Pilots 3 to 6 change what a customer sees at every branch, so they are chain-wide week-level switchbacks.
- **Do not overlap pilots 3 to 6** (they all change the chain for whole weeks), and run 1 and 2 one after the other.
- **One decision rule per pilot**, set before the pilot, on the lower or upper end of the 95% interval of the estimated effect (calibrated threshold for chain-wide pilots). We simulated how often each rule fires for a given true effect (`results/experiment_rollout_rules.csv`).

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
  - Gross profit or transactions (pilots 3, 3b, 4, 6): the treated week's total × (1 + e). The visit metric is injected as a fall.
  - Saturday offer: treated Saturdays × (1 + lift), with 25% of the extra taken back from that week's Monday–Friday.
  - Effect 0 is always included.
- **The exact planned analysis.** Each simulated pilot is analysed with the model in its section, including the washout days it drops, and judged at its threshold. A "detection" is a significant result in the direction of the true effect.

**Calibrated critical values** (`results/experiment_calibrated_critical.csv`; the value used is the larger of the calibrated and nominal t):

| Pilot | 8 weeks | 12 | 16 | 20 | 26 |
|---|---|---|---|---|---|
| Nominal t (weeks − 3 df) | 2.57 | 2.26 | 2.16 | 2.11 | 2.07 |
| 3 Price A, gross profit | 2.57 | 2.50 | 2.35 | 2.46 | 2.33 |
| 3 Price A, visits | 2.89 | 2.79 | 2.79 | 2.71 | 2.62 |
| 3b Price B, gross profit | 2.94 | 2.34 | 2.48 | 2.39 | 2.36 |
| 4 Discount removal | 2.57 | 2.47 | 2.33 | 2.41 | 2.45 |
| 5 Saturday offer | 2.62 | 2.52 | 2.44 | 2.46 | 2.49 |
| 6 Menu price | 2.57 | 2.36 | 2.42 | 2.50 | 2.28 |

**False-positive rate by pilot length** (effect 0; chain-wide pilots at the calibrated threshold):

| Pilot | 4 wk | 6 | 8 | 12 | 16 | 20 | 26 |
|---|---|---|---|---|---|---|---|
| 1 Food prompt (nominal t) | 9.6% | 6.0% | 6.4% | 7.0% | 6.2% | | |
| 2 Evening dessert (nominal t) | 7.2% | 6.2% | 5.8% | 6.8% | 5.8% | | |
| 3 Price A, gross profit | | | 4.0% | 4.6% | 6.0% | 5.0% | 5.4% |
| 3 Price A, visits | | | 6.8% | 5.0% | 4.6% | 4.4% | 3.8% |
| 3b Price B, gross profit | | | 2.8% | 6.0% | 3.6% | 6.6% | 6.0% |
| 4 Discount, gross profit | | | 4.8% | 4.8% | 6.2% | 4.6% | 5.6% |
| 5 Saturday, weekly gross profit | | | 3.6% | 5.8% | 5.8% | 7.2% | 3.4% |
| 6 Menu price, chain gross profit | | | 4.4% | 7.6% | 3.4% | 6.0% | 6.0% |

Newey–West standard errors (lag 3) did not fix the nominal test's excess false positives with so few weeks (9–12%; `results/experiment_sensitivity.csv`); calibration does.

**Sensitivity to carryover and spillover** (`results/experiment_sensitivity.csv`; the planned analysis is unchanged):
- Carryover = the share of the effect that persists in the control week after a treated week.
- Spillover = the share of the effect that control branches receive in a week when another branch is treated.

| Pilot, length, true effect | No carryover or spillover | Carryover 50% | Spillover 25% | Spillover 50% | Carryover 50% + spillover 25% |
|---|---|---|---|---|---|
| 1 Food prompt, 12 wk, +2.5 pts: detected / mean estimate | 67% / 2.46 | 34% / 1.70 | 39% / 1.79 | 21% / 1.18 | 28% / 1.44 |
| 1 Food prompt, 12 wk, +5 pts | 99% / 4.96 | 86% / 3.33 | 93% / 3.68 | 63% / 2.48 | 75% / 2.92 |
| 2 Evening dessert, 12 wk, +2.5 pts | 69% / 2.50 | 38% / 1.68 | 47% / 1.94 | 24% / 1.27 | 30% / 1.50 |
| 2 Evening dessert, 12 wk, +5 pts | 100% / 5.04 | 85% / 3.30 | 95% / 3.72 | 65% / 2.55 | 76% / 2.92 |
| False positives (effect 0), pilot 1 / 2 | 4.2% / 5.0% | 6.0% / 5.0% | 6.4% / 7.0% | 5.8% / 6.0% | 7.0% / 5.8% |

- **Under the carryover and spillover structures simulated here**, both shrink the estimate toward zero (50% carryover removes about a third of a true effect, 50% spillover about half) and do not create false positives. A positive result therefore stays trustworthy under those structures, while a null result is weaker evidence than its power suggests. Other structures (for example spillover that grows over time) were not simulated.
- **Price test, 20 weeks, +4.5%, calibrated threshold.** Detection is 42% with no carryover. With 50% carryover it falls to 27% (mean estimate 3.3%). With a negative carryover (customers delaying purchases after a rise) it is 58% (mean estimate 5.5%), so that case biases the price result upward. The previous-week check guards against both.

**Limits.**
- Only shocks from these 25 weeks are available.
- Effects are assumed to start at once and stay constant apart from the carryover cases.
- Lengths over 26 weeks reuse the history.

Value anchors measured from the file (`results/experiment_anchors.csv`):
- **Food prompt.** The chain sells about 906 drink transactions a week, and a drink + food basket earns $3.70 of food gross profit, so **+1 point of attach rate is worth about $33 a week**.
- **Evening dessert.** About 660 transactions a week are from 18:00, and a dessert basket earns $3.15, so **+1 point of evening dessert rate is worth about $21 a week**.
- **Chain.** Mean weekly chain gross profit is $6,922, and the 10% discount costs $66 a week.

---

## Pilot 1: food prompt (suggest a food item with a drink)
- **Question.** Does a till prompt raise the share of drink transactions that include food? (Under-sold pairs: Cold Drinks + Bakery, Matcha & Tea + savoury items; see `FINDING_8.md`.)
- **Eligible population:** every transaction with at least one drink, any hour.
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

  Before starting, permute the three branch columns at random and start the cycle at a random week.
- **Duration: 20 weeks**, which gives 86% power at +2.5 points with a calibrated threshold (79% at 16 weeks).
- **Primary metric:** attach rate = share of eligible transactions that contain a food item, in points. Weekly chain gross profit, drinks per transaction and average ticket are guardrails.
- **Analysis model:** rate for branch *b* on day *d* of week *w* = β · prompt(b, w) + branch effect + week effect + weekday effect, weighted by the number of eligible transactions, with standard errors clustered by week.
- **Power** (500 simulated pilots, detection rate, nominal t):

  | True gain | 4 weeks | 6 | 8 | 12 | 16 |
  |---|---|---|---|---|---|
  | 0 (false positives) | 9.6% | 6.0% | 6.4% | 7.0% | 6.2% |
  | +1 point | 10% | 9% | 10% | 13% | 19% |
  | +2.5 points | 25% | 35% | 43% | 67% | 79% |
  | +5 points | 59% | 89% | 94% | 100% | 100% |

  Median 95% interval half-width: ±2.0 points at 12 weeks, ±1.8 at 16.
- **Rollout rule: roll out chain-wide if the lower 95% bound of β is above 0** (calibrated threshold).
  - **Simulated at 20 weeks:** the rule rolls out 2.6% of the time with no effect, 24% at +1 point, 84% at +2.5 points and 100% at +5 points.
  - **Why not a stricter rule:** "lower bound ≥ 1 point" was simulated and rejected. At 20 weeks it rolls out a true +2.5 points only 40% of the time.
  - **Cost check:** +1 point is worth about $33 a week, so the prompt must cost less than its measured gain. Stories should compare the cost with the lower bound, not with zero.

## Pilot 2: evening dessert upsell
- **Question.** Does suggesting a dessert (or a drink-and-dessert bundle) from 18:00 raise the share of evening transactions that include a dessert?
- **Eligible population:** every transaction from 18:00 onward, with or without a drink.
- **Unit of randomisation, schedule, analysis, carryover:** the same as pilot 1; the prompt is switched on only from 18:00 on treated branch-weeks.
- **Duration: 20 weeks** (89% power at +2.5 points with a calibrated threshold; 79% at 16 weeks).
- **Primary metric:** dessert rate = share of eligible transactions that contain a dessert (baseline 15.9%), in points. Guardrails: evening gross profit per transaction, average ticket, queue time.
- **Run it after pilot 1, not at the same time** (the outcomes overlap).
- **Power** (nominal t):

  | True gain | 4 weeks | 6 | 8 | 12 | 16 |
  |---|---|---|---|---|---|
  | 0 (false positives) | 7.2% | 6.2% | 5.8% | 6.8% | 5.8% |
  | +1 point | 15% | 12% | 12% | 18% | 20% |
  | +2.5 points | 26% | 40% | 47% | 67% | 81% |
  | +5 points | 61% | 86% | 95% | 100% | 100% |

- **Rollout rule:** the same as pilot 1 (lower bound > 0). Simulated at 20 weeks: it rolls out 2.6% of the time with no effect, 26% at +1 point, 90% at +2.5 points and 100% at +5 points. A rule of "lower bound ≥ 1 point" would roll out a true +2.5 points 52% of the time.
- **Caveat on the 18:00 step:** the evening takeaway and dine-in shares change abruptly at 18:00 (`FINDING_weekend.md`), which may be a till default.

## Pilot 3: price test (Option A, and Option B)
- **Question.** What happens to units and gross profit if every menu price rises about 6.9% (Option A: the inflation-matched rise in `results/opportunity_inflation_meta.csv`, 6.856%)?
- **Unit of randomisation:** chain-week. All branches, all menu items, app and menu boards change together on Monday of a treated week and change back on Monday of a control week.
- **Schedule (ABBA, 0 = current prices, 1 = new prices; random choice of ABBA or BAAB at the start):**

  | Weeks | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | … |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|---|
  | Price | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 0 | repeat |

- **Duration:** 26 weeks.
- **Primary metric:** chain gross profit, Tuesday–Sunday of each week. **Co-primary:** chain transactions (visits).
  - **Assumption:** the visit fall equals the fall in units, i.e. basket size and mix are unchanged. Under elasticity −1, units fall 6.4%, so transactions are assumed to fall 6.4%.
- **Analysis model:** weekly outcome = α + β · treated week + γ · week number, ordinary least squares. β is a percent of the mean weekly outcome with a 95% interval at the calibrated critical value (gross profit: 2.46 at 20 weeks, 2.33 at 26; visits: 2.71 and 2.62).
- **Power for chain gross profit** (calibrated threshold):

  | True effect on weekly GP | 8 weeks | 12 | 16 | 20 | 26 |
  |---|---|---|---|---|---|
  | 0 (false positives) | 4.0% | 4.6% | 6.0% | 5.0% | 5.4% |
  | +1% | 3% | 3% | 8% | 6% | 9% |
  | +2.5% | 8% | 11% | 19% | 17% | 22% |
  | **+4.5% (Option A central case, elasticity −1)** | 23% | 31% | 44% | 46% | 55% |
  | +5% | 29% | 37% | 46% | 47% | 60% |
  | +7.5% | 48% | 54% | 73% | 72% | 88% |

  Median 95% half-width: ±5.1% at 20 weeks, ±4.3% at 26. The central +4.5% reaches 71% at 52 weeks, so 80% is not reached within 52 weeks.
- **Power for the visit effect** (a simulated FALL in chain transactions, calibrated threshold):

  | True change in transactions | 8 weeks | 12 | 16 | 20 | 26 |
  |---|---|---|---|---|---|
  | 0 (false positives) | 6.8% | 5.0% | 4.6% | 4.4% | 3.8% |
  | −2.5% | 11% | 12% | 11% | 20% | 18% |
  | −5% | 27% | 39% | 43% | 51% | 66% |
  | **−6.4% (central case)** | 42% | 52% | 67% | 79% | 91% |
  | −7.5% | 51% | 66% | 78% | 89% | 96% |

  The smallest fall detectable with 80% power is 6.5% at 20 weeks and 5.8% at 26.
- **Rollout rule (the one rule; calibrated threshold; break-even = a 10.5% fall in units):** roll out the price rise if the lower 95% bound of the gross-profit effect is above 0; otherwise keep current prices.

  | True units change (gross-profit effect) | Roll out, 20 weeks | 26 weeks |
  |---|---|---|
  | −3.3% (+8.0%) | 81% | 92% |
  | −6.4% (+4.5%) | 46% | 55% |
  | −9.0% (+1.6%) | 8% | 13% |
  | −10.5% (0) | 2.4% | 4.6% |
  | −12.4% (−2.2%) | 0.2% | 0.2% |

  The visit estimate is reported alongside it, to measure the elasticity, but it is not a second rollout rule.
- **Option B (Garden +5.0%, Uptown +9.4% to Harbour's prices; Harbour unchanged).**
  - **What was simulated:** the same chain-week design, with the central effect of +2.40% of chain gross profit (its $4,298 estimate).
  - **Simplification:** the effect is applied to the chain total; we did not model it falling only on Garden's and Uptown's transactions.
  - **Result:** detection is 19% at 20 weeks and 20% at 26 (at most 31%, at 39 weeks). The smallest effect detectable at 26 weeks is 6.9% of chain gross profit, and false positives are 6.0% at 26 weeks.
  - **Reading (group b):** Option B cannot be confirmed by a pilot, so we do not recommend a pilot as the decision tool. The default is to leave the branch price lists unchanged until Option A's visit measure gives the elasticity.

## Pilot 4: discount removal (stop the blanket 10% discount), a non-inferiority test
- **Question.** If the 10% discount is switched off, is the chain no worse off, allowing for lost visits?
- **Unit of randomisation:** chain-week, ABBA as pilot 3, with 1 = discount off.
- **Duration:** 26 weeks.
- **Primary metric:** chain gross profit (Tuesday–Sunday); same weekly model as pilot 3, calibrated critical value 2.45 at 26 weeks.
- **Why non-inferiority:** the saving if no visits are lost is $66 a week, 0.99% of weekly gross profit. A gain that small is detected only 5–8% of the time at any length up to 52 weeks. The question a pilot can answer is whether removal loses more than an acceptable margin.
- **Margin.** We set the margin to the smallest loss that a 26-week pilot passes with 80% probability when the true effect is the whole prize (+0.99%): **5.6% of weekly chain gross profit** (6.5% at 20 weeks, 8.9% at 12; `results/experiment_discount_noninferiority.csv`). A smaller acceptable loss cannot be guaranteed within 26 weeks.
- **Rule (the one rule):** remove the discount only if the lower 95% bound of the gross-profit effect is above −5.6%. Otherwise the result is inconclusive and the discount is kept.

  | True gross-profit effect | Discount removed, 26 weeks | 20 weeks (margin 6.5%) |
  |---|---|---|
  | +0.99% (no visits lost) | 80% | 80% |
  | 0 | 68% | 69% |
  | −2.5% | **30% (wrongly passes)** | 37% |
  | −5% | **3.4% (wrongly passes)** | 8.7% |

- **Reading (group b):** the margin is more than five times the saving. A true 2.5% loss would wrongly pass about three times in ten, and a 5% loss about once in thirty. So we do not recommend this pilot as the decision tool. The stakes are $1,706 per six months if no visits are lost, the data cannot settle them, and the cautious default is to keep the discount as it is. A smaller change (for example 5% instead of 10%) halves both the saving and the risk, but it would still be a judgement, not a test result.

## Pilot 5: Saturday transfer (copy the Tuesday driver onto Saturday)
- **Prerequisite:** the Tuesday driver is unknown (`TUESDAY_DECOMP.md`, `docs/tuesday_mechanism.md`). This pilot can only start after Stories identifies it.
- **Unit of randomisation:** chain-week, ABBA as in pilot 3.
- **Primary metric:** chain gross profit for the whole week, Monday–Sunday, so displaced visits count against the offer. Calibrated critical value 2.46 at 20 weeks, 2.49 at 26.
- **Power: not sufficient at any practical length.** A 19% Saturday lift is +1.4% of the week after 25% displacement.

  | Saturday lift | 8 weeks | 12 | 16 | 20 | 26 |
  |---|---|---|---|---|---|
  | 0 (false positives) | 3.6% | 5.8% | 5.8% | 7.2% | 3.4% |
  | 19% (central case) | 5% | 8% | 10% | 10% | 8% |
  | 25% | 7% | 12% | 16% | 15% | 17% |
  | 50% | 19% | 31% | 40% | 39% | 47% |

- **Alternatives simulated:**
  1. *Saturday-only metric, chain-wide* (calibrated threshold). A 19% lift is detected 69% of the time at 16 weeks and 92% at 26, but this metric ignores displacement.
  2. *Branch-week Saturday offer* (nominal t; not chain-wide). It detects the central case 23% of the time at 26 weeks and a 50% lift 90% of the time. It cannot see customers moving between branches.
- **Reading (group b):** no practical pilot can confirm the weekly gain, and the Tuesday driver is unknown, so we do not recommend a Saturday offer now (stakes: $2,601 per six months in the central case). If the driver is found, the only rule a pilot could support is a Saturday-only stage 1: 12 weeks, continuing only if the lower 95% bound of the Saturday lift is above 0. The README's displacement scenarios would then give an estimate, not a confirmation.

## Pilot 6: menu price test (4 items)
- **Question.** Does a 5% rise on the four frequent, below-median-margin items (Iced Matcha, Strawberry Matcha, Cinnamon Roll, Chocolate Croissant; `MENU.md`) raise the chain's gross profit, once customers who swap to other items or skip the item are counted?
- **Unit of randomisation:** chain-week, ABBA as in pilot 3. All branches change the four prices together.
- **Primary metric:** **total chain weekly gross profit** (Tuesday–Sunday), so substitution to any other item is captured.
- **Secondary metrics (not simulated):** units of the four items, units of their closest substitutes, and gross profit of transactions containing the four items (20.8% of chain gross profit).
- **Analysis model:** as pilot 3, at its calibrated critical value (2.50 at 20 weeks, 2.28 at 26).
- **Central effect:** the +$880.80 six-month estimate at elasticity −1 (`results/menu_price_scenarios.csv`) is **+0.49% of six-month chain gross profit**.
- **Power: not reachable.**

  | True effect on chain GP | 8 weeks | 12 | 16 | 20 | 26 |
  |---|---|---|---|---|---|
  | 0 (false positives) | 4.4% | 7.6% | 3.4% | 6.0% | 6.0% |
  | **+0.49% (central case)** | 4% | 5% | 4% | 4% | 7% |
  | +1% | 3% | 5% | 5% | 3% | 9% |
  | +2.5% | 9% | 15% | 18% | 19% | 21% |
  | +5% | 32% | 38% | 45% | 45% | 59% |
  | +7.5% | 56% | 66% | 71% | 76% | 87% |

  The central effect is detected no more often than no effect at all, up to 52 weeks. The smallest effect detectable at 26 weeks is 6.9% of chain gross profit, 14 times the central estimate.
- **Rule (the one rule, the same in `MENU.md` and the README):** keep the rise only if the lower 95% bound of the chain gross-profit effect is above 0; otherwise revert.
  - **Simulated at 26 weeks:** the rise is kept 4.0% of the time with no effect, 6.8% at the central +0.49%, 27% at +2.5% and 62% at +5%. A true loss of 1% is kept 0.8% of the time.
- **Reading (group b):** a pilot cannot show the expected gain. It would almost always revert, so it would also undo a small real gain. We do not recommend the rise on the strength of this analysis. The stakes are $881 per six months at elasticity −1, and the default is to keep the four prices as they are.

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
**(a) Run as pilots:**

| Order | Pilot | Weeks | What it settles |
|---|---|---|---|
| 1 | Food prompt | 20 | A +2.5-point gain (rolled out 84% of the time; 2.6% with no effect) |
| 2 | Evening dessert upsell | 20 | A +2.5-point gain (rolled out 90% of the time) |
| 3 | Price Option A, visit measure | 26 | The elasticity (91% power at a 6.4% fall); price levels are then decided from it |

**(b) Not pilots; cautious defaults:**

| Change | Six-month stakes | Default |
|---|---|---|
| Remove the 10% discount | $1,706 if no visits are lost | Keep it as it is |
| Raise the four menu prices 5% | $881 at elasticity −1 | Keep them as they are |
| Price Option B | $4,298 at elasticity −1 | No change until the elasticity is measured |
| Saturday offer | $2,601 (central case) | None until the Tuesday driver is found |

## Limits of this document
- Effect sizes are injected, not measured.
- The simulated noise is that of 25 weeks in one half-year, resampled in 4-week blocks; lengths over 26 weeks reuse that history.
- The chain-wide pilots are limited by how much weekly gross profit moves, not by the number of transactions, and they need the calibrated threshold.
- Carryover and spillover bias the branch-week estimates toward zero under the structures simulated; their sizes (25–50%) are assumptions.
- Option B is simulated as a chain-wide effect, not branch by branch.
- A weekly switchback for prices is unusual and may affect customers' trust.

## Reproduce
```bash
python src/experiment_power.py   # needs data/stories_transactions.csv and results from opportunity_estimates.py and menu_profit.py
```
