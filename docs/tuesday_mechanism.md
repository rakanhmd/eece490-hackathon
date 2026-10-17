# Tuesday mechanism: who carries the lift?

Code: `src/tuesday_mechanism.py`. Table: `results/tuesday_mechanism.csv`. Figure: `figures/tuesday_mechanism.png`. Descriptive only; no causal claim.

## Design
- **Lift** = Tuesday transactions ÷ mean transactions on Monday, Wednesday, Thursday and Friday, over the 25 full Mon–Sun weeks (32,761 transactions), all branches pooled.
- **95% intervals:** bootstrap resampling whole weeks (all branches together), 2,000 resamples.
- **Prediction tested.** A members-only trigger (an app push or loyalty offer that only reaches identified customers) predicts a larger lift for identified transactions than for anonymous ones, and an anonymous lift near 1.
- **Frequency without a mechanical link.** A customer's frequency (non-Tuesday transactions) is measured in the other half of the weeks: grouped on odd weeks and measured on even weeks, and the other way round.
- **First-seen month** excludes each customer's first transaction, because a first visit is more likely to fall on a busy Tuesday.

## Results
| Group | Lift | 95% interval |
|---|---|---|
| Identified transactions | 1.535 | [1.490, 1.586] |
| Anonymous transactions | 1.477 | [1.412, 1.539] |
| Identified minus anonymous | +0.058 | [−0.018, +0.140] |

By branch, identified minus anonymous is +0.059 at Garden [−0.071, +0.195], +0.023 at Harbour [−0.082, +0.144] and +0.144 at Uptown [−0.017, +0.307].

| Non-Tuesday transactions in the other half of the weeks | Lift | 95% interval |
|---|---|---|
| 0 | 1.523 | [1.356, 1.710] |
| 1–2 | 1.485 | [1.415, 1.566] |
| 3–5 | 1.615 | [1.534, 1.701] |
| 6+ | 1.428 | [1.186, 1.704] |

| First seen (month) | Lift | 95% interval |
|---|---|---|
| January | 1.526 | [1.462, 1.596] |
| February | 1.471 | [1.405, 1.539] |
| March | 1.501 | [1.337, 1.660] |
| April | 1.294 | [0.987, 1.632] |

## What it is consistent with, and what it weakens
- **Weakened: a trigger that reaches only identified members.** Anonymous transactions rise almost as much (1.477) as identified ones (1.535); the difference is small and its interval includes zero. A members-only offer would leave the anonymous lift close to 1, unless many members buy without giving their ID.
- **Weakened: a lift driven by the most frequent regulars.** The lift is similar across frequency groups, with no steady rise from occasional to frequent customers, and similar for customers first seen in January, February and March.
- **Consistent with:** a trigger that reaches everyone who buys, identified or not, such as a public in-store or social-media offer, a delivery-app deal, a chain-wide operational pattern (opening hours, staffing, stock), or a data or posting artefact. The data cannot separate these.
- **Next test:** Stories' campaign and social-post calendar for Tuesdays, delivery-app deal dates, and daily till (Z-report) or bank totals by weekday.
