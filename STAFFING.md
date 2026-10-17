# Hourly staffing: forecast and staff-hours

Code: [`src/staffing.py`](src/staffing.py) (about 4 seconds, seeded; two runs from scratch gave identical output and tables). Tables: `results/staffing_*.csv`; model rows are logged in `results/results.csv` (names start with `hourly_`, splits `val_may_hourly` and `test_june_hourly`). Figures: `figures/staffing_mae_by_hour.png`, `figures/staffing_forecast_heatmap.png`.

## Short answer
A model that knows the branch, weekday and hour (plus the growth trend) forecasts June's hourly transactions with an error of **1.62 transactions per branch-hour, against 2.24 for the usual baseline (same hour last week)**. It is better in all 17 hours and at all three branches. The error is already at the level that random variation in such small counts would leave (about 1.63 even for a perfect forecast), so a better model would not help. The staffing conversion depends on two assumptions that are not in the data (how many transactions one person serves an hour, and the minimum crew), and with Stories' volumes most hours need only one or two people, so the gain from demand-led rosters is real but modest: fewer short-staffed hours than a flat roster (5.4% vs 12.6% of branch-hours at one person minimum), without paying for two people all day (1,717 vs 3,060 staff-hours in June).

## Setup
- **Target:** transactions per branch per hour, 07:00 to 23:59 (the file has no sales outside these hours), zero where nobody bought. 3 branches × 181 days × 17 hours = 9,231 cells. Mean 3.7 transactions per cell, maximum 27, and 9.3% of cells are empty.
- **Split by time, no shuffling:** train Jan–Apr, choose the model on May, refit on Jan–May and score June once. The June test touched only the chosen model, the dummy and the two baselines.
- **Baseline (the brief's):** same branch, same hour, same weekday last week. It uses last week's actual counts, so it is a one-week-ahead forecast. The fitted models use nothing from the forecast month and forecast 1 to 5 weeks ahead, which is the harder setting. A second reference, the mean of the same hour over the four previous same weekdays, is also shown.
- **Candidates:** dummy (each branch's mean); same hour last week; mean of last four same weekdays; *profile × trend* (branch × weekday × hour mean of detrended counts, times the branch's growth trend); *Poisson regression* (branch, weekday, hour, branch × hour, weekday × hour, branch × weekday, and a linear trend; regularisation 0.001, 0.01 or 0.1); *gradient boosting with Poisson loss* (2 settings).

## Results
Mean absolute error (MAE) in transactions per branch-hour, with the weighted absolute percentage error (WAPE = total absolute error ÷ total transactions).

| Model | May validation MAE | June test MAE | June WAPE |
|---|---|---|---|
| Dummy (branch mean) | 2.13 | 2.28 | 50.6% |
| Same hour last week (baseline) | 2.21 | 2.24 | 49.6% |
| Mean of the last 4 same weekdays | 1.70 | 1.79 | 39.6% |
| Profile × trend | 1.58 | not scored | |
| Poisson regression, regularisation 0.001 / **0.01** / 0.1 | 1.54 / **1.535** / 1.58 | **1.62** (chosen on May) | **36.0%** |
| Gradient boosting (depth 3, rate 0.05, 200 iterations / depth 4, 300 iterations) | 1.55 / 1.56 | not scored | |

- **Chosen on May:** Poisson regression with regularisation 0.01. The May differences among the three best (1.535, 1.541, 1.547) are tiny, so the choice is not important.
- **June by branch (model vs same hour last week):** Garden 1.71 vs 2.31, Harbour 1.99 vs 2.83, Uptown 1.18 vs 1.58.
- **The model beats the baseline by 0.62 transactions per branch-hour** (95% bootstrap interval over the 30 days: −0.71 to −0.53, negative meaning better). It wins in all 17 hours (`results/staffing_mae_by_hour.csv`).
- **The baseline is no better than a constant.** Same hour last week scores 2.24, and the branch mean scores 2.28. With 3 to 10 transactions in an hour, one earlier count carries nearly as much noise as the quantity being forecast.
- **A floor on the error.** If June counts were Poisson with a mean equal to the model's forecast, no forecast could have an MAE below 1.625; the model's is 1.624. This assumes the forecast is the true rate, so treat it as a guide: the remaining error looks like chance variation in small counts, not a missing pattern.

Error by hour of the day, June, mean of the three branches (`staffing_mae_by_hour.csv`):

| Hour | Mean transactions | Model MAE | Last-week MAE |
|---|---|---|---|
| 07:00 | 1.8 | 1.05 | 1.36 |
| 12:00 | 3.4 | 1.45 | 1.99 |
| 18:00 | 4.9 | 1.69 | 2.46 |
| 20:00 | 6.7 | 2.18 | 2.86 |
| 21:00 | 9.4 | 2.48 | 3.38 |
| 22:00 | 7.5 | 2.25 | 3.29 |
| 23:00 | 4.1 | 1.69 | 2.32 |

Errors are largest in the busy evening hours in absolute terms but not relatively (at 21:00 the model is off by about 26% of the mean, at 07:00 by about 59%).

**What the forecast says about the shape of demand** (`staffing_forecast_heatmap.png`, `staffing_forecast_shape_june.csv`): at every branch demand is lowest at 07:00 and peaks at 21:00; Tuesday is the busiest day at every branch.

## Converting to staff-hours (ESTIMATES: the two assumptions are not in the data)
**Assumptions:** one staff member serves **8 transactions per hour** (CAP), and **at least 1 person** is on duty in every open hour (MIN). Staff needed in an hour = the larger of MIN and ⌈transactions ÷ CAP⌉. A "plan" is made from the forecast and checked against June's actual transactions. We chose 8 and 1 as a central case; the sensitivity below shows what changes.

June, all branches, main case (`staffing_staff_hours_june.csv`):

| Plan | Staff-hours planned (needed: 1,739) | Short staff-hours | Branch-hours understaffed | Surplus staff-hours |
|---|---|---|---|---|
| Forecast (model) | 1,717 | 85 | 5.4% | 63 |
| Forecast, covering 80% of cases | 1,828 | 60 | 3.9% | 149 |
| Same hour last week | 1,740 | 109 | 6.9% | 110 |
| Flat: 1 person every hour | 1,530 | 209 | 12.6% | 0 |
| Flat: 2 people every hour | 3,060 | 16 | 0.9% | 1,337 |

- **Demand-led rosters sit between the two flat options.** Compared with a flat 2 people all day, planning from the forecast uses 1,343 fewer staff-hours in June (44% fewer) and leaves 5.4% of branch-hours short against 0.9%. Compared with a flat 1 person, it adds 187 staff-hours and cuts short-staffed hours from 12.6% to 5.4%. The forecast roster also beats the same-hour-last-week roster (5.4% vs 6.9% short) for about the same total hours. We have no wage figure, so there is no dollar value; multiply staff-hours by Stories' cost per hour.
- **Most hours need only one person.** At 8 transactions per staff-hour, 12.6% of branch-hours need two or more people and 0.9% need three or more. Staff needed rises with the evening peak: 40.2% of all needed staff-hours fall from 18:00, against 35.3% of the open hours. Harbour at 21:00 needs 2.3 people on average (other Harbour hours 1.0 to 1.8). Garden at 21:00 needs 1.6, Uptown 1.1.
- **Tuesday needs more hours at Harbour and Garden.** Needed staff-hours per day (June actual demand), Harbour: Tuesday 27.8 against 20.2 to 23.0 on Mon/Wed/Thu/Fri and 18.5 to 19.0 on Saturday and Sunday. Garden: Tuesday 21.8 against 18.2 to 18.8 (Mon–Fri) and 17.5 to 18.0 (weekend). Uptown is about 17 on every day, because its volumes are low enough that one person covers every hour.
- **Sensitivity** (share of June branch-hours understaffed, plan from the forecast / plan from last week's same hour):

  | | 6 tx per staff-hour | 8 | 10 |
  |---|---|---|---|
  | At least 1 person | 10.5% / 12.4% | 5.4% / 6.9% | 3.3% / 3.7% |
  | At least 2 people | 2.2% / 2.7% | 0.7% / 0.7% | 0.1% / 0.2% |

  With a minimum crew of two and a capacity of 8 or more, the minimum covers nearly every hour and the forecast has almost nothing to add. The forecast matters when the minimum is one person or when one person serves fewer than about 8 transactions an hour.

## What could make this wrong
- **Capacity and minimum crew are assumptions.** Staff-hours scale with them; the best source is Stories' roster and till data (people on shift by hour, queue times).
- **A transaction is not a workload.** Drinks that need long preparation, or dine-in service, take more labour than a counter sale. The model counts transactions, not minutes. The order-type split changes in one step at 18:00 (takeaway 54% of transactions before, 28% after), which may be a till default (`FINDING_weekend.md`); it does not change the counts forecast here, but if table service needs extra staff, the order-type record must be checked before it is used.
- **Persistence.** The model needs the Tuesday peak and the evening peak to continue, and it extends a 1.9% per week growth trend; one month (June) is the only out-of-time test.
- **Hour cells are small** (a mean of 3.7 per cell), so every hour's forecast has an error of one to two transactions. An hour's staffing cannot be exact; the 80%-cover plan trades 111 more staff-hours for fewer short hours (3.9% against 5.4%).
- The forecast cannot know about events or closures; it uses only calendar and trend.
- Opening hours are taken from when sales appear (07:00 to 23:59), not from a known timetable.

## A test for Stories
Collect two things for four weeks: staff on shift by hour (the roster) and a measure of service pressure (queue length or the time from order to hand-over, or the number of customers who leave). Then for random branch-weeks use a demand-led roster built from this forecast and compare short-staffed hours with the usual roster. We have not simulated the power of this test, so we make no claim about its length; the power calculations in `EXPERIMENTS.md` cover the five pilots there only.

## Reproduce
```bash
python src/staffing.py   # needs data/stories_transactions.csv (see data/README.md)
```
