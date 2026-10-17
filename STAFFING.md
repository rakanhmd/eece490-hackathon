# Hourly staffing: forecast and staffing scenario

Code: [`src/staffing.py`](src/staffing.py) (about 40 seconds, seeded; two runs from scratch gave identical output and tables). Tables: `results/staffing_*.csv`; model rows are logged in `results/results.csv` (names start with `hourly_rolling_`, split `test_apr_jun_rolling`). Figures: `figures/staffing_mae_by_hour.png`, `figures/staffing_weekly_mae.png`, `figures/staffing_forecast_heatmap.png`.

## Short answer
**Measured (forecast accuracy against baselines):** at a weekly roster horizon (forecasts made on Sunday night for the following Monday to Sunday, 1 to 7 days ahead), a model that knows the branch, weekday and hour (plus the growth trend) has an error of **1.55 transactions per branch-hour over 12 test weeks (April to June), against 2.15 for the same hour last week and 1.71 for the average of the last four same weekdays**. It beats both baselines in all 12 weeks, in each of the three test months, in all 17 hours and at all three branches. **Scenario (not measured):** the staffing figures depend on three assumptions that are not in the data (how many transactions one person serves an hour, the minimum crew, and how hourly changes and breaks are handled), and they are not checked against Stories' actual rosters. Under the central scenario, a roster built from the forecast leaves 4.1% of branch-hours short-staffed, against 5.4% for a roster built from last week's same hour and 9.6% for a flat one-person roster; the advantage over last week's roster shrinks or disappears when staff can only be scheduled in blocks of several hours.

## Setup
- **Target:** transactions per branch per hour, 07:00 to 23:59 (the file has no sales outside these hours), zero where nobody bought. 3 branches × 181 days × 17 hours = 9,231 cells. Mean 3.7 transactions per cell, maximum 27, and 9.3% of cells are empty.
- **Rolling origins at a fixed horizon.** Every Sunday night from 1 March (eight full weeks of history) the models are refitted on everything before the coming Monday and forecast that Monday to Sunday, which is how a weekly roster would be built. That gives 17 weekly origins, with forecast weeks from Monday 2 March to Sunday 28 June, and 6,069 branch-hour forecasts per method. Lead time is 1 to 7 days (4 days on average).
- **Three test months, with the model chosen before each.** April, May and June are the test months (12 forecast weeks: those starting 6, 13, 20, 27 April, 4, 11, 18, 25 May, and 1, 8, 15, 22 June). Before each test month, the model is chosen among the candidates on the forecast weeks completed before that month's first origin (April uses March only; May uses March and April; June uses March to May). No model is chosen on a test week. The same Poisson regression was chosen each time (regularisation 0.01; `staffing_rolling_selection.csv`).
- **Baselines with the same information and lead time:** (1) same branch, same hour, same weekday last week (the count 7 days earlier); (2) the mean of the same hour over the four previous same weekdays. Both use only data available at the origin. The dummy is each branch's mean.
- **Candidates:** dummy; the two baselines; *profile × trend* (branch × weekday × hour mean of detrended counts, times the branch's growth trend); *Poisson regression* (branch, weekday, hour, branch × hour, weekday × hour, branch × weekday, and a linear trend; regularisation 0.001, 0.01 or 0.1); *gradient boosting with Poisson loss* (2 settings).
- **Uncertainty.** Differences between methods are summarised by week (all branches and all hours of a week together) and given 95% intervals from a **contiguous-week block bootstrap** (blocks of 1, 2 or 3 weeks; the results hardly change).

## Results (measured: forecast accuracy against the baselines)
Mean absolute error (MAE) in transactions per branch-hour; WAPE = total absolute error ÷ total transactions (`staffing_rolling_results.csv`).

| Method | April | May | June | All 12 weeks | WAPE |
|---|---|---|---|---|---|
| Dummy (branch mean) | 2.00 | 2.14 | 2.20 | 2.11 | 51.5% |
| Same hour last week | 1.99 | 2.25 | 2.20 | 2.15 | 52.3% |
| Mean of the last 4 same weekdays | 1.63 | 1.73 | 1.75 | 1.71 | 41.6% |
| **Chosen model (picked before each month)** | **1.48** | **1.56** | **1.61** | **1.55** | **37.7%** |

By branch over the 12 weeks (chosen model / same hour last week / 4-week mean): Garden 1.57 / 2.15 / 1.74, Harbour 1.89 / 2.67 / 2.07, Uptown 1.19 / 1.61 / 1.30.

**Paired differences in weekly MAE** (negative = first method better; 95% interval from the contiguous-week block bootstrap, blocks of 2 weeks; `staffing_rolling_bootstrap.csv`):

| Comparison | Mean difference | 95% interval | Weeks the first is better |
|---|---|---|---|
| Chosen model − same hour last week | −0.60 | −0.65 to −0.55 | 12 of 12 |
| Chosen model − mean of last 4 same weekdays | −0.16 | −0.17 to −0.15 | 12 of 12 |
| Mean of last 4 − same hour last week | −0.44 | −0.49 to −0.39 | 12 of 12 |
| Chosen model − dummy | −0.56 | −0.60 to −0.52 | 12 of 12 |

- **The four-week average is a much better baseline than last week's same hour**, because with 3 to 10 transactions in an hour a single earlier count carries nearly as much noise as the quantity being forecast. **Same hour last week scores 2.15, close to the branch mean (2.11).** The model improves on the four-week average by 0.16 (about 9%), on last week's same hour by 0.60 (28%).
- These intervals describe 12 test weeks in one half-year, with overlapping training windows and a growth trend. They capture week-to-week variation in the error, not a new season or a changed business; treat them as the precision of this test, not as a guarantee for next year.
- **A model-based reference.** If the chosen forecast were the true mean and counts were Poisson, the expected MAE would be 1.556; the model's is 1.549. This depends on the model being right (it is computed from the model's own forecasts), so it is a reference point and not a limit on what any forecast could achieve.

Error by hour of the day, pooled over the 12 test weeks, mean of the three branches (`staffing_mae_by_hour.csv`):

| Hour | Mean transactions | Chosen model | 4-week mean | Same hour last week |
|---|---|---|---|---|
| 07:00 | 1.6 | 1.00 | 1.05 | 1.24 |
| 12:00 | 3.2 | 1.46 | 1.60 | 2.08 |
| 18:00 | 4.4 | 1.66 | 1.83 | 2.36 |
| 20:00 | 6.5 | 2.03 | 2.25 | 2.89 |
| 21:00 | 8.7 | 2.30 | 2.59 | 3.11 |
| 22:00 | 6.7 | 2.05 | 2.21 | 2.96 |
| 23:00 | 3.6 | 1.50 | 1.65 | 2.19 |

The model has the lowest error in all 17 hours against both baselines. Errors are largest in the busy evening hours in absolute terms but not relatively (at 21:00 about 26% of the mean, at 07:00 about 63%).

**The shape of demand in the forecasts** (`staffing_forecast_heatmap.png`, `staffing_forecast_shape.csv`): at every branch demand is lowest at 07:00 and peaks at 21:00; Tuesday is the busiest day at every branch.

## Staffing scenario (not measured: every figure below rests on assumptions)
This is a scenario conditional on three things we do not know: the **service rate** (transactions one person serves an hour), the **minimum crew**, and how much **hourly flexibility** and break cover Stories' rosters allow. It does not compare against Stories' actual rosters, which are not in the data, and it counts transactions, not workload minutes.

**Central scenario:** one staff member serves **8 transactions per hour**; **at least 1 person** is on duty in every open hour; breaks are covered inside the hour or by an overlapping shift (no capacity lost); staffing can change every hour. Staff needed in an hour = the larger of the minimum and ⌈transactions ÷ 8⌉. A "plan" is made from each method's 7-day-ahead forecast and checked against the actual transactions of the 12 test weeks.

All branches, 12 test weeks (`staffing_staff_hours_rolling.csv`):

| Plan | Staff-hours planned (needed: 4,724) | Short staff-hours | Branch-hours understaffed | Surplus staff-hours |
|---|---|---|---|---|
| Forecast (chosen model) | 4,684 | 178 | 4.1% | 138 |
| Forecast, covering 80% of cases (assumes Poisson counts) | 4,954 | 106 | 2.5% | 336 |
| Same hour last week | 4,711 | 236 | 5.4% | 223 |
| Mean of the last 4 same weekdays | 4,614 | 228 | 5.3% | 118 |
| Flat: 1 person every hour | 4,284 | 440 | 9.6% | 0 |
| Flat: 2 people every hour | 8,568 | 28 | 0.6% | 3,872 |

- **In this scenario, planning from the forecast sits between the two flat options.** Against last week's same-hour roster it leaves 1.3 points fewer branch-hours short (95% block-bootstrap interval −1.6 to −1.1; 12 weeks), against the four-week-average roster 1.2 points fewer (−1.5 to −0.9), and against a flat one-person roster 5.5 points fewer (−6.4 to −4.7), at 400 more staff-hours over 12 weeks than the flat one-person roster. A flat two-person roster uses 3,884 more staff-hours than the forecast roster over the same weeks. We have no wage figure, so no dollar value; multiply staff-hours by Stories' cost per hour.
- **Most hours need only one person.** At 8 transactions per staff-hour, 9.6% of branch-hours need two or more people and 0.6% need three or more. Staff needed rises with the evening peak: 39.6% of all needed staff-hours fall from 18:00, against 35.3% of the open hours. Harbour at 21:00 needs 2.0 people on average (other Harbour hours 1.0 to 1.6), Garden 1.5, Uptown 1.1.
- **Tuesday needs more hours at Harbour and Garden.** Needed staff-hours per day (actual April to June demand), Harbour: Tuesday 26.0 against 19.9 to 21.7 on Mon/Wed/Thu/Fri and 18.1 to 18.8 on Saturday and Sunday. Garden: Tuesday 20.8 against 17.9 to 18.5 (Mon–Fri) and 17.3 to 17.5 (weekend). Uptown is about 17 on every day, because its volumes are low enough that one person covers every hour.

**Sensitivity to the service rate and the minimum crew** (share of branch-hours understaffed; plan from the forecast / last week's same hour / four-week mean; `staffing_service_rate_sensitivity.csv`):

| | 6 tx per staff-hour | 8 | 10 |
|---|---|---|---|
| At least 1 person | 8.7% / 10.4% / 10.0% | 4.1% / 5.4% / 5.3% | 2.9% / 3.0% / 3.1% |
| At least 2 people | 1.6% / 1.8% / 1.8% | 0.4% / 0.5% / 0.5% | 0.1% / 0.1% / 0.1% |

With a minimum crew of two, or a service rate of 10 or more, the minimum covers nearly every hour and the choice of forecast makes little difference. The forecast matters when the minimum is one person and one person serves fewer than about 10 transactions an hour.

**Sensitivity to breaks** (`staffing_break_sensitivity.csv`; 8 transactions per staff-hour before breaks, at least 1 person). The break share is the part of each paid staff-hour lost to breaks: 1/16 is a 30-minute break per 8-hour shift, and 1/8 is 30 minutes per 4 hours.

| Break share | Staff-hours needed | Understaffed: forecast / last week / 4-week mean / flat 1 person |
|---|---|---|
| 0 (central scenario) | 4,724 | 4.1% / 5.4% / 5.3% / 9.6% |
| 1/16 | 4,886 | 6.3% / 7.1% / 7.4% / 13.0% |
| 1/8 | 4,901 | 5.7% / 7.2% / 7.0% / 13.0% |

Allowing for breaks adds about 160 to 180 staff-hours over the 12 weeks and raises the understaffed share under every plan; the forecast plan stays the best of the three non-flat plans.

**Sensitivity to hourly flexibility** (`staffing_flexibility_sensitivity.csv`). If staff can only be scheduled in blocks of k consecutive open hours, each block must cover its busiest hour:

| Block length | Plan | Staff-hours planned (needed: 4,724) | Short staff-hours | Understaffed | Surplus staff-hours |
|---|---|---|---|---|---|
| 1 hour | Forecast | 4,684 | 178 | 4.1% | 138 |
| | Last week | 4,711 | 236 | 5.4% | 223 |
| | 4-week mean | 4,614 | 228 | 5.3% | 118 |
| 2 hours | Forecast | 4,808 | 142 | 3.3% | 226 |
| | Last week | 4,957 | 160 | 3.7% | 393 |
| | 4-week mean | 4,762 | 172 | 4.0% | 210 |
| 4 hours | Forecast | 4,964 | 124 | 2.9% | 364 |
| | Last week | 5,279 | 114 | 2.6% | 669 |
| | 4-week mean | 4,910 | 143 | 3.3% | 329 |

The more the roster is made in blocks, the smaller the forecast's advantage. With 4-hour blocks, the forecast plan has about the same number of short hours as last week's same-hour plan (2.9% against 2.6%) and schedules 315 fewer staff-hours (4,964 against 5,279). The forecast helps most when Stories can change staffing hour by hour.

## What could make this wrong
- **Everything in the scenario depends on the service rate, minimum crew, breaks and hourly flexibility.** The best source is Stories' roster and till data (people on shift by hour, queue times); the numbers above are not measured against them.
- **A transaction is not a workload.** Drinks that need long preparation, or dine-in service, take more labour than a counter sale. The order-type split changes in one step at 18:00 (takeaway 54% of transactions before, 28% after), which may be a till default (`FINDING_weekend.md`); it does not change the counts forecast here, but if table service needs extra staff, the order-type record must be checked before it is used.
- **Persistence.** The model needs the Tuesday peak and the evening peak to continue, and it extends a growth trend of about 1.9% per week; the test covers three months in one half-year.
- **Hour cells are small** (a mean of 3.7 per cell), so every hour's forecast has an error of one to two transactions. An hour's staffing cannot be exact; the 80%-cover plan schedules 270 more staff-hours than the plain forecast plan for fewer short hours (2.5% against 4.1%) and relies on a Poisson assumption.
- The forecast cannot know about events or closures; it uses only calendar and trend.
- Opening hours are taken from when sales appear (07:00 to 23:59), not from a known timetable.

## A test for Stories
Collect two things for four weeks: staff on shift by hour (the roster) and a measure of service pressure (queue length or the time from order to hand-over, or the number of customers who leave). Then for random branch-weeks use a demand-led roster built from this forecast and compare short-staffed hours with the usual roster. We have not simulated the power of this test, so we make no claim about its length; the power calculations in `EXPERIMENTS.md` cover the six pilots there only.

## Reproduce
```bash
python src/staffing.py   # needs data/stories_transactions.csv (see data/README.md)
```
