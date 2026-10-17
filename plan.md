# Stories Coffee hackathon plan

## Context
The brief ranks teams on original, evidence-backed findings with clear business value. The grading agents have already mined this dataset. Basic sales summaries do not count. Finding #1 (Garden unit cost is 1.43x Harbour's) is drafted in README.md and data/README.md and needs only a reproducing script. This plan picks the other findings, favouring ones that need a causal check or a "challenge the first explanation" step, because those are the ones generic agents usually skip.

## What the read-only scan already showed (measured, after removing 132 duplicates)
- **Harbour-only 15% promo.** All 502 lines with a 15% discount are at Harbour, between 2026-03-12 and 2026-05-19. They cover only Cold Coffee and Desserts, about 23% of those lines in the window.
- **First look at the promo.** Harbour's Cold Coffee + Desserts unit share went 21.7% before, 22.8% during, 23.3% after. Garden rose slightly too, Uptown fell. The share staying high after the promo ended hints that warming weather, not the discount, drives much of the rise.
- **10% discount.** It appears on about 6% of lines at every branch, every month, every hour. Mean quantity is 1.057 with or without it, so there is no sign it buys bigger baskets.
- **Tuesday spike.** Tuesday has about 7,400 transactions against about 4,600–5,100 on other weekdays, at all branches, every month. Category mix and discount share are the same as other days. Saturday is the weakest day.
- **Evening peak.** Lines peak at 21:00 at every branch. 07:00–08:00 is the quietest period.
- **Growth.** Monthly revenue rises about 50% from January to June at all three branches.
- **Customer IDs are unreliable.** 94% of known customers buy at several branches, so customer-level retention work is risky.

## Candidate findings, ranked by value x originality
| # | Problem / decision | Why agents likely missed it | Evidence needed | Value (to estimate) |
|---|---|---|---|---|
| 2 | **Did Harbour's 15% promo pay for itself?** Stop, keep, or redesign | Needs a difference-in-differences with control branches and a seasonality check, not a total | Weekly units and gross profit of target categories, Harbour vs Garden+Uptown, pre/promo/post. Diff-in-diff estimate with a bootstrap CI by week. Placebo: same test on non-target categories and on a fake promo window. Cost = discount dollars given | Incremental gross profit minus discount cost, in USD. Likely negative or near zero |
| 3 | **Is the 10% discount giving margin away?** | Agents report discount share, not its effect | Compare basket size, items per transaction and category of discounted vs full-price transactions, same branch/hour/day. Total USD discounted | USD of margin per year that could be recovered. Assumption: removing it loses few customers |
| 4 | **Staff to the real demand curve: Tuesday surge, Saturday trough, 21:00 peak** | Agents note "busiest day" but rarely test if Tuesday is real or an artifact | Branch x weekday x hour heatmap. Check Tuesday by hour, order type, basket size, known vs anonymous IDs, and every week (is any Tuesday missing, are there holidays). Alternative explanations: batch posting of another day's sales, a recurring Tuesday event, data generation. Simple forecast of daily transactions per branch: seasonal-naive baseline (same weekday last week) vs linear model with weekday + trend, trained Jan–May, tested on June | Staff-hours shifted from quiet slots to peaks, using a stated cost per staff-hour and transactions per staff-hour. Clearly marked as estimate |
| 5 | Bundle the most common pairs (Bakery + Matcha/Tea, Bakery + Hot Coffee) | Lower originality | Attach rates per drink by branch | Small; do only if time remains |

Rejected: customer retention or churn (IDs unreliable), a "chat with your data" tool (brief excludes it), deep learning (no need).

## Shared assumptions (stated in README, separate from facts)
- Unit Cost and prices are real. The 132 duplicates are system errors.
- No outside events data is available, so seasonality is estimated from control branches.
- Labour cost and staff productivity figures are assumptions with a sensitivity range, never measured.

## Files
- `REQUIREMENTS.md`: numbered checklist quoting the brief.
- `src/load.py`: `load_clean()` reads the CSV, drops duplicates, parses date/time, adds weekday/hour/week. All scripts use it.
- `src/margin_analysis.py`: reproduces finding #1 tables into `results/margin_by_branch.csv`, `results/unit_cost_ratio_by_product.csv`, `results/margin_by_month.csv`.
- `src/promo_analysis.py`: finding #2; `results/promo_did.csv`, `figures/promo_weekly.png`.
- `src/discount_analysis.py`: finding #3; `results/discount_effect.csv`.
- `src/demand_patterns.py` and `src/forecast.py`: finding #4; heatmap figure, Tuesday checks table, forecast results logged with `log_result` from `src/common.py`.
- README.md and data/README.md: extend only (fill "Next finding", estimates, assumptions, test, rejected approaches). Do not rewrite the Garden section.

## Timed plan (from now; adjust to the real clock)
| Time | Work | Owner |
|---|---|---|
| 0:00–0:20 | REQUIREMENTS.md, `load.py`, `margin_analysis.py`; commit "finding 1 reproducible" | Claude + Rakan |
| 0:20–1:20 | Promo diff-in-diff with placebos and CI; commit | Rakan |
| 0:20–1:20 | Tuesday checks and demand heatmap | Muche |
| 1:20–2:00 | Discount effect; commit | Rakan |
| 1:20–2:20 | Forecast vs seasonal-naive baseline on June; commit | Muche |
| 2:20–3:00 | Value estimates with sensitivity tables; one-line action per finding | both |
| 3:00–3:40 | README write-up from results files only; one-paragraph conclusion | both |
| 3:40 | Final audit: rerun every script from scratch, check README numbers against results/, remind to push and check repo is public | Claude |

Rule: if a finding shows nothing after ~20 minutes, report the null result honestly in README (a null promo effect is itself a finding) and move on.

## Verification
- Run each script with `.venv/bin/python src/<script>.py` and read its printed output.
- Garden numbers must match the README table (Harbour 65.0%, Uptown 62.6%, Garden 46.9%; ratio 1.426–1.439).
- Every number added to README must appear in a file in `results/` or in script output.
- Forecast: test month (June) used once, after choosing the model on May.

##test