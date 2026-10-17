# Stories Coffee hackathon plan (final status)

## Context
The brief ranks teams on original, evidence-backed findings with clear business value. The grading agents have already mined this dataset, and basic sales summaries do not count. So we picked findings that need a causal check or a "challenge the first explanation" step. README.md is the deliverable. This file records what we planned and what was done. Every number quoted here comes from a file in `results/`.

## Early observations and where each ended up
- **Harbour-only 15% promo.** 502 lines, Harbour only, 12 March to 19 May, Cold Coffee and Desserts only. Became finding 6.
- **10% discount.** On 5.5–5.8% of lines at every branch. Became finding 7.
- **Tuesday surge.** Tuesday has about 1.53 times the transactions of an average Monday-to-Friday weekday, at every branch, every week. Saturday is the quietest day. Became finding 4, with the forecast in finding 5.
- **Evening peak.** Transactions peak at 21:00 and are lowest at 07:00 (`results/tuesday_hour_profile.csv`). Not developed further.
- **Growth.** June revenue was 1.46 to 1.57 times January's at each branch (`results/revenue_by_month.csv`). Used as a caveat on yearly figures.
- **Customer IDs are unreliable.** 93.8% of known customers buy at several branches (data/README.md). Customer-level work was rejected.

## Findings: planned vs done
| Planned | Status | Where |
|---|---|---|
| Garden margin gap, reproducing script | Done | Findings 1–2; `src/margin_analysis.py` |
| Branch price lists vs costs, elasticity scenarios | Done (added during the session) | Finding 3; `src/pricing_analysis.py` |
| Tuesday surge: real or artifact | Done | Finding 4; `src/tuesday_check.py` |
| June forecast vs same-weekday-last-week baseline | Done | Finding 5; `src/forecast.py` |
| Harbour 15% promo: did it pay? | Done. Causation not shown, net value range includes a loss | Finding 6; `src/promo_analysis.py` |
| 10% discount: does it buy anything? | Done. No basket effect, small cost | Finding 7; `src/discount_analysis.py` |
| Drink + food cross-sell | Done | Finding 8; `src/basket_analysis.py`, `FINDING_8.md` |
| Staff-hour savings in USD | Dropped. Labour cost is not in the data, so the README gives no dollar figure for staffing | README ranked table, row 6 |
| Branch × weekday × hour heatmap (`demand_patterns.py`) | Dropped. The Tuesday checks covered the decision | n/a |

Rejected: customer retention or churn (IDs unreliable), a "chat with your data" tool (brief excludes it), deep learning (no need).

## Shared assumptions (all stated in the README assumptions table)
- Unit Cost and prices are real costs and prices.
- The 132 duplicates are recording errors. They carry $741 of revenue (0.24%).
- No outside events data is available, so seasonality in the promo test comes from the control branches.
- Price elasticity, food margin per extra basket and yearly growth are assumptions shown as ranges, never measured.

## Files
- `REQUIREMENTS.md`: checklist quoting the brief, with where each requirement is met.
- `src/load.py`: `load_clean()` reads the CSV, drops duplicates and adds date and time columns. All scripts use it.
- One script per finding, as listed in the table above. Tables go to `results/`, figures to `figures/`. Forecast scores are logged to `results/results.csv` with `log_result` from `src/common.py`.

## Timeline
| Step | Status |
|---|---|
| Requirements, loader, Garden script | Done |
| Promo and discount analyses | Done |
| Pricing scenarios and Tuesday checks | Done |
| Forecast | Done |
| README conclusion and ranked table | Done |
| Independent review (REVIEW.md) and fixes | Done |
| Cross-sell, finding 8 | Done |
| Final audit: rerun every script from scratch, check README numbers against `results/`, push, confirm the repo is public | To do before the cutoff |

## Verification
- Run each script from `src/` (see README "How to reproduce") and read its printed output.
- Garden numbers must match the README table: Harbour 65.0%, Uptown 62.6%, Garden 46.9%; cost ratio 1.426–1.439.
- Every number in the README must appear in a file in `results/` or in script output.
- Forecast: the June test month was used once, after choosing the model on May.
