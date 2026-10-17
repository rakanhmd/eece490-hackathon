# Forecast: rolling-origin evaluation

Code: `src/forecast.py`. Tables: `results/forecast_rolling_mae.csv`, `results/forecast_rolling_bootstrap.csv`, `results/forecast_mae.csv` (secondary check), rows `rolling_h7`, `val_may` and `test_june` in `results/results.csv`. Figures: `figures/forecast_rolling.png`, `figures/forecast_june.png`.

## Design
- **Target:** transactions per branch per day.
- **Rolling origin, fixed 7-day horizon.** For each origin date t from 1 March to 23 June (115 origins × 3 branches), every candidate is fit on data up to and including t and predicts t + 7. Targets run from 8 March to 30 June.
- **No look-ahead.** Every feature is computed relative to the origin, never the target date. The seasonal naive baseline is the count observed at t (same weekday, one week before the target).
- **Candidates frozen before evaluation, all reported:**
  - dummy (mean of all data up to t);
  - seasonal naive;
  - weekday + trend and weekday + log trend (least squares per branch on all data up to t);
  - gradient boosting (`HistGradientBoostingRegressor`, fixed settings, no tuning), pooled over branches. It predicts log(count at t+7 ÷ mean of the 28 days ending at t) from the target weekday, the branch, and the count at t, the count at t−7 and the 7-day mean, each divided by the 28-day mean. It is trained only on pairs whose target was already observed at t;
  - selected (trailing): at each origin, the candidate with the lowest MAE over the last 28 target dates already observed at t. This is the only step that selects, and it uses only data before the origin. Origins from 15 February are computed only to give it a history on 1 March.
- **Uncertainty.** Paired block bootstrap of the daily error differences (candidate minus seasonal naive) over contiguous weeks of target dates, all branches kept together, 2,000 resamples, block lengths of 1, 2 and 3 weeks.

## Results
Mean absolute error, transactions per branch per day (`results/forecast_rolling_mae.csv`):

| Model | All | Tuesdays | Other days | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|---|
| Dummy | 15.04 | 44.82 | 9.88 | 12.03 | 12.85 | 15.03 | 19.67 |
| Seasonal naive | 8.79 | 11.80 | 8.26 | 8.75 | 7.84 | 8.94 | 9.60 |
| Weekday + trend | 6.65 | 9.26 | 6.20 | 6.38 | 6.25 | 6.50 | 7.44 |
| **Weekday + log trend** | **6.39** | **8.27** | **6.07** | 6.35 | 6.05 | 6.21 | 6.96 |
| Gradient boosting with lags | 6.71 | 8.61 | 6.38 | 6.63 | 6.25 | 6.76 | 7.19 |
| Selected (trailing) | 6.55 | 8.36 | 6.23 | 6.44 | 6.28 | 6.47 | 6.97 |

The trailing selection picked weekday + log trend at 72.2% of origins, weekday + trend at 24.3% and gradient boosting at 3.5%.

MAE difference against the seasonal naive baseline (negative = better), with 95% block-bootstrap intervals (`results/forecast_rolling_bootstrap.csv`):

| Model | Difference | 1-week blocks | 2-week blocks | 3-week blocks |
|---|---|---|---|---|
| Weekday + log trend | −2.392 | [−2.968, −1.721] | [−2.903, −1.791] | [−2.679, −1.998] |
| Weekday + trend | −2.131 | [−2.721, −1.448] | [−2.645, −1.502] | [−2.528, −1.667] |
| Gradient boosting with lags | −2.075 | [−2.732, −1.382] | [−2.443, −1.627] | [−2.524, −1.719] |
| Selected (trailing) | −2.238 | [−2.772, −1.563] | [−2.712, −1.658] | [−2.552, −1.831] |
| Dummy | +6.258 | [+4.994, +7.582] | [+4.797, +7.949] | [+4.526, +8.356] |

- Every non-dummy model beats the baseline at every block length, and in every target month.
- Gradient boosting with lags does not beat the simple weekday + log trend regression, so we keep the simpler model.
- With 3-week blocks there are only 6 blocks, so those intervals are the least reliable.

## Secondary check (first version)
Train January to April and compare on May; refit January to May and score June once. Weekday + log trend: May 6.12, June 6.95 (June Tuesdays 9.02). Seasonal naive: May 8.94, June 9.60 (June Tuesdays 15.20). This agrees with the rolling evaluation.

## Limits
- One half-year of data; no yearly cycle, and every model extrapolates the growth trend.
- The horizon is fixed at 7 days; staffing rosters made further ahead would see larger errors.
