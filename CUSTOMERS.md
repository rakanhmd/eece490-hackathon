# Customers: churn model, segments and a win-back plan

Code: [`src/customer_model.py`](src/customer_model.py) (about 30 seconds, seeded; a second run from scratch printed identical output and tables). Tables: `results/customer_*.csv`; model rows are logged in `results/results.csv` (names start with `churn_`). Figures: `figures/customer_churn_pr_curve.png`, `customer_segments_pca.png`, `customer_segment_churn.png`.

## Short answer
**We could not predict who will stop buying.** On the held-out test customers no model beats the no-skill baseline, so we do not recommend a model-targeted win-back campaign. The customers split into two groups (regulars and occasional), but their lapse rates are the same. With realistic assumptions a win-back offer loses money, because only 8.7% of customers lapse and an offer costs about as much per customer as a lapsed customer is worth.

Only customers with an ID are used (3,494 IDs, 63% of lines). Finding 1 already warned that IDs are unreliable: 94% of known customers appear at several branches. "Churn" below means "this ID stopped appearing", which may not be one real person.

## Setup
- **Features from Jan–Apr only** (before 2026-05-01), 31 per customer: visits, active days, recency, tenure, days since first visit, total spend, average basket, units per visit, gross profit, visits in April and April's share, mean gap between visits, share of discounted visits, dine-in, weekend, evening and morning shares, number of branches and branch shares, number of categories and category spend shares.
- **Label:** no purchase in May–Jun. 3,414 customers were active in Jan–Apr; 296 lapsed (**8.7%**). The 80 customers first seen in May–Jun are excluded.
- **Split before fitting:** customers 70/15/15, stratified on the label: 2,389 / 512 / 513 (churn 8.7% / 8.6% / 8.8%). Imputer and scaler are inside the pipelines (fitted on train only).
- **Leakage check:** (1) the feature function stops with an error if any May–Jun row reaches it; (2) rebuilding the features from a file that never contained May–Jun gives an identical table.
- **Choosing:** model chosen on validation PR-AUC, threshold chosen on validation (maximum F1 with `choose_threshold`). The test set was scored once, for the chosen model and the dummy only. Before looking at it we set the rule: the model "clearly beats" the baseline only if the lower end of the 95% bootstrap interval is above the prevalence (PR-AUC) and above 0.5 (ROC-AUC).

## 1. Churn model results
Validation (prevalence 8.59%; a no-skill PR-AUC equals the prevalence). From `customer_churn_validation.csv`:

| Model | Val PR-AUC | Val ROC-AUC | 5-fold ROC-AUC on train |
|---|---|---|---|
| Dummy (always the base rate) | 0.086 | 0.500 | 0.500 |
| Logistic regression C = 0.01 / 0.1 / 1 / 10 | 0.121 / **0.138** / 0.133 / 0.131 | 0.496 / 0.489 / 0.479 / 0.478 | 0.465 / 0.469 / 0.479 / 0.481 |
| Gradient boosting, best of 8 settings (depth 3, rate 0.03, 200 iterations) | 0.122 | 0.569 | 0.444 |
| Steady-rate rule (no fitting; see below) | 0.116 | 0.561 | n/a |

- Chosen on validation PR-AUC: **logistic regression, C = 0.1**. Its validation ROC-AUC is 0.489, so it ranks customers no better than a coin.
- **Random scores reach the same level.** On a validation set this size, random scores give PR-AUC of 0.096 on average and 0.126 at the 95th percentile; their ROC-AUC spans 0.41 to 0.59. Every model above is inside that noise (the best, 0.138, is only just above the 95th percentile, and it is the maximum of 12 fitted models). Cross-validated ROC-AUC on the training folds is *below* 0.5 for every fitted model.
- No single feature separates the groups either: the strongest has a ROC-AUC of 0.47 (`customer_churn_univariate_auc.csv`; measured on train + validation only).
- Threshold chosen on validation: 0.1013 (flags about a quarter of customers).

**Test set (scored once, 513 customers, 45 lapsers; `customer_churn_test.csv`):**

| | Model | Baseline |
|---|---|---|
| PR-AUC | 0.0995 (95% bootstrap CI 0.069–0.150) | 0.0877 (the prevalence) |
| ROC-AUC | 0.541 (0.447–0.627) | 0.5 |
| Precision at the threshold | 0.090 (0.043–0.144) | 0.088 |
| Recall at the threshold | 0.244 (0.122–0.370) | n/a (random flagging of the same 23.8% would give about 0.24) |
| Share of customers flagged | 23.8% | |

Confusion matrix at the threshold (rows = truth, columns = prediction):

| | Predicted stays | Predicted lapses |
|---|---|---|
| Actually stays | 357 | 111 |
| Actually lapses | 34 | 11 |

**Verdict: no.** The lower ends of both intervals (PR-AUC 0.069 vs 0.088 prevalence; ROC-AUC 0.447 vs 0.5) do not clear our rule. On validation the threshold gave precision 0.16 at recall 0.41 (`results/results.csv`), which looked better; that is the threshold being tuned to validation noise, and it did not carry over to the test set.

**Why there is nothing to find (measured):** if every customer kept buying at their own Jan–Apr rate, with volume growth (×1.28 transactions per day) taken into account, we would expect about **14.8%** of them to have a gap of two months. We see **8.7%** (`customer_churn_vs_steady_rate.csv`). So lapses are not more common than ordinary gaps between purchases would produce. This is a chance-gap reference, not proof that nobody leaves. A customer who stops buying looks very much like one who has a long gap.

## 2. Segments
RFM = recency, frequency, monetary value from Jan–Apr, with frequency and spend log-transformed and all three scaled. KMeans for k = 2 to 8; silhouette: 0.44 (k = 2), 0.36, 0.32, 0.34, 0.30, 0.31, 0.29 (k = 8). So **k = 2** (`customer_segments_silhouette.csv`). The PCA plot shows no gap between the two groups: it is one cloud cut along "how often and how recently", not two kinds of customer. The segments were built without the churn label.

| | Regulars | Occasional |
|---|---|---|
| Customers | 2,266 (66%) | 1,148 (34%) |
| Share of Jan–Apr spend | 84% | 16% |
| Visits in Jan–Apr (mean) | 4.76 | 1.98 |
| Days since last visit (mean, on Apr 30) | 16.5 | 44.2 |
| Spend per customer | $43.68 | $16.23 |
| Average basket | $9.29 | $8.42 |
| Gross margin | 58.5% | 59.5% |
| Gross profit per customer | $25.54 | $9.65 |
| Main branch (share of visits) | Harbour (48%) | Harbour (48%) |
| Top category (share of spend) | Matcha & Tea (16.6%) | Bakery (18.7%) |
| **Lapse rate (May–Jun), 95% CI** | **8.4%** (7.4–9.6%) | **9.2%** (7.6–11.0%) |

- **Regulars:** about two thirds of customers, who come about once a month or more and bring most of the margin. **Occasional:** one or two visits, last seen on average six weeks before the cut-off.
- Both groups use Harbour most (Harbour is 48% of all customers' visits), so there is no branch difference, and both have about the same margin. They differ in frequency, spend per head and favourite category.
- **Lapse rates are not different** (chi-square p = 0.52). Segment membership does not tell us who will lapse. Occasional customers are not more at risk in this data, which again fits the "ordinary gaps" reading.

## 3. Business use: win-back offer (estimates, not measured)
**Who to target.** The model's flagged group (23.8% of customers, about 812 of 3,414) has a lapse rate of about 9% (95% CI 4–14%), the same as customers in general (8.7%). The flagged customers contain about 72 of the 296 who will lapse; flagging a random 23.8% would catch about 70. Targeting by this model therefore adds nothing over mailing a random group. Targeting by segment adds nothing either.

**Cost and benefit.** Measured: a customer's gross profit is about $5.05 a month (Jan–Apr; $5.02 for those who later lapsed), and the average basket is $9.00. Everything else is an assumption (`customer_winback_scenarios.csv`):

| Assumption | Pessimistic | Middle | Optimistic |
|---|---|---|---|
| Share of would-be lapsers the offer brings back | 5% | 10% | 20% |
| Months a saved customer keeps buying at the old rate | 2 | 3 | 6 |
| Share of contacted customers who use the offer (including those who would have come anyway) | 40% | 25% | 15% |
| Discount | 15% of the basket | 15% | 15% |
| Cost of contacting one customer | $0.10 | $0.05 | $0.02 |

Result for the 812 model-flagged customers: customers saved about **3.7 / 7.3 / 14.6**; net gross profit **−$483 / −$204 / +$260**. For all 3,414 active customers: about 15 / 30 / 59 saved; net **−$2,036 / −$877 / +$1,023**. A random group of 812 gives almost the same as the flagged group (−$484 / −$209 / +$243), which is the point: the model adds nothing.

An offer costs about $0.39 per contacted customer in the middle case. It breaks even only if 26% of contacted customers would otherwise lapse. The real lapse rate is 8.7%. The cost is dominated by discounts given to customers who would have come back anyway. Even in the best segment (regulars, $6.39 a month, lapse 8.4%) the expected net per offer is −$0.23 in the middle case; occasional customers are −$0.32 (`customer_winback_by_segment.csv`). Only the optimistic scenario is positive, and we have no evidence for it.

**Recommendation.** Do not launch a model-targeted, discount-based win-back. If Stories wants to try one anyway, use a cheap, no-discount reminder (a message with no coupon) aimed at regulars, who earn the most per person, and measure it with the test below before spending more.

## A test to confirm
- **Design:** randomise customer IDs (not visits) to "reminder" or "hold-out", stratified by segment, with the hold-out receiving nothing. Include model-flagged and unflagged customers in both arms so we can also check whether the model's flag matters (it should not, if our result holds).
- **Outcome:** purchase within 8 weeks; secondary: gross profit per customer after offer cost.
- **Size** (`customer_ab_test_size.csv`; 80% power, 5% test level, baseline lapse 8.7%): to detect a fall in the lapse rate of 3 points, 1,158 customers per arm (2,315 total); 2 points, 2,776 per arm (5,551 total); 1 point, 11,774 per arm (23,548 total). We have 3,414 active customers, so only a 3-point effect can be tested with today's base. Smaller effects need a longer enrolment period.
- **Decision rule set beforehand:** continue only if the gross profit per customer, after offer cost, is higher in the offer arm and the lower end of its 95% interval is positive.
- **Risk to watch:** IDs may be shared or reused, so one person can fall into both arms. Randomise on ID, and check whether the same person appears under several IDs at the till.

## Weak areas
- Everything depends on customer IDs that may not map to one person each; the whole analysis could be about ID noise.
- Only six months, four of them for features; no yearly cycle. Sales grew 28% per day between the two windows.
- 45 lapsers in the test set is few: the intervals are wide, so a modest real signal could be missed. The model-selection results (validation, cross-validation, the test) all point the same way, which is why we call it "no signal found" and not "no signal exists".
- The cost and benefit figures use our assumptions, not measured offer responses. The segments' differences in value (per head) are real; their churn difference is not.
- We tried only logistic regression and gradient boosting on 31 features. Features we do not have (visit reason, price sensitivity, store events, demographics) could carry the signal.

## Reproduce
```bash
python src/customer_model.py   # needs data/stories_transactions.csv (see data/README.md)
```
