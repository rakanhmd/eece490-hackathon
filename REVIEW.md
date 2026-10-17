# Independent review (Task 1)

Reviewer: Claude (Muche's session). Scope: README.md, data/README.md, plan.md, REQUIREMENTS.md and the three scripts in `src/`. Nothing in those files was edited.

## What was rerun
`margin_analysis.py`, `promo_analysis.py`, `discount_analysis.py` were run with system `python3` (pandas 2.3.3) on `data/stories_transactions.csv` (copied from `muche/`, gitignored, not committed). The README's "How to reproduce" does not list scripts, so I took the three scripts in `src/` (the `.venv/` in the repo is empty, so `.venv/bin/python` from plan.md fails).

| Script | Wall time | Result vs committed `results/` |
|---|---|---|
| margin_analysis.py | 1 s | identical |
| promo_analysis.py | 2 min 16 s (52 min CPU) | identical except one sign: `-0.0` vs `0.0` in `promo_did.csv` (fake-window row, post columns). Bootstrap is seeded, so it is deterministic. The figure PNG differs only in bytes. |
| discount_analysis.py | 19 s | identical |

## README numbers vs recomputed
All figures in the Garden section match: revenue, gross profit and margin per branch, monthly Garden range 46.66–47.23%, 45 products, cost ratio 1.426–1.439, price ratio 0.951–0.953 (Garden) and 0.912–0.916 (Uptown), `$17,955` and `$15,636`. data/README.md matches too: 51,177 rows, 132 duplicates, 51,045 lines, 33,887 transactions, 36.5% missing IDs, 93.8% multi-branch customers, quantity 1 or 2, 181 days, 9 categories.

## Problems, most severe first

### 1. (High) Findings 2 and 3 are not in the README, and the README still has placeholders
- Lines 1, 7, 10, 27, 33, 40, 43, 48, 51 are `<...>` placeholders; line 60 is `python src/<script>.py`.
- The promo and discount results exist only in `results/` and the script output. Graders read the README.
- **Fix:** list the three real commands under "How to reproduce" (`python src/margin_analysis.py`, `promo_analysis.py`, `discount_analysis.py`, note that promo takes ~2 min), then write findings 2 and 3 from the tables below (with the caveats in problems 3–5).

### 2. (High) The $18,000 / $15,600 estimate does not match the sentence that describes it
- README line 32: "If Garden's costs matched Harbour's cost ratio, gross profit … would be about **$18,000 higher** (Garden revenue × 18.1 margin points)".
- Garden's prices are 4.7% lower than Harbour's (README line 25). Applying Harbour's *margin* to Garden's revenue silently also gives Garden Harbour's prices. If Garden pays Harbour's **unit costs** at its own lower prices and quantities, I recompute gross profit of 62,584 vs 46,696 = **+$15,888**, about $2,000 lower than $17,955 (computed from the data, same median-cost method as `margin_analysis.py`; not in any `results/` file yet).
- **Fix:** say "matched Harbour's gross margin (65.0%)" for the $18,000 figure, and add the unit-cost version ($15.9k) as the lower end. Add the calculation to `margin_analysis.py` (Rakan's file) so the number has a source.

### 3. (High) "$31,000–36,000 per year" has no source and is probably biased
- README line 32 ("roughly $31,000–36,000 per year at the current sales level"). It is 6-month value × 365/181 (I get 31,532 and 36,208). That calculation is in neither the script nor `results/`, which breaks the "every number from code we ran" rule.
- Garden revenue rose 49% from January (13,473) to June (20,088). Doubling the six-month total understates the June run rate (June × 12 × 18.1 pts = $43,500) and assumes the growth is not seasonal. With only six months we cannot tell. Either direction is a guess.
- **Fix:** print the annualised figure in `margin_analysis.py`, label it an estimate, and give a range that includes both the H1×2 and the June×12 versions, with the unit-cost correction from problem 2. State that growth may be seasonal.

### 4. (High) Promo effect: the "post" effect is larger than the "during" effect, so the causal reading is weak
- `results/promo_did.csv`, main row: during +13.7% [+2.0, +27.7], **after +18.6% [+8.1, +29.2]**. Harbour's target units kept rising relative to the controls *after the discount ended*. A discount cannot cause a gap that grows once it is removed. That points to a Harbour-specific trend or a lasting habit, and either way the +13.7% is not cleanly "the promo".
- The pre-trend check does not rule this out: slope +0.144 pts/week with CI [−0.28, +0.62] over only 10 weeks is a wide interval, not evidence of "no trend". Reporting it as passing would be correlation-as-cause by omission.
- The result depends on which control is used: Garden only +6.9% [−4.3, +21.0] (includes zero), Uptown only +21.1% [+6.0, +41.1]. The "main" CI [2.0, 27.7] excludes zero only because of the pooled controls.
- The placebo checks help but have wide CIs (Cold Drinks −1.3% [−16.1, +15.8], fake window −1.6% [−15.2, +13.0]), so they cannot detect an effect of +14%.
- **Fix:** when writing finding 2, report the during/after pair and the two single-control rows together. Wording such as "Harbour's target categories sold 2–28% more than the controls' trend predicts during the promo, and the gap did not close afterwards, so we cannot attribute it to the discount." Present the money result as a range whose low end is negative, not as "the promo paid".

### 5. (Medium) Promo value table: the discount is partly subtracted twice, and the incremental units are priced at the wrong margin
- `src/promo_analysis.py`, `money` block: `gp_per_unit` is average gross profit **after** discount (`hp[GP].sum()/units`), multiplied by incremental units, then the whole $470 discount is subtracted. Discounted lines are already net of their discount in `GP`, so part of the $470 is counted twice. Conversely, extra buyers receive the 15%, so their margin is lower than average. The two errors push in opposite directions.
- My recompute with net = actual GP − counterfactual GP at full-price margin gives about +$597 (point), −$296 (CI low), vs the table's +$543 and −$308. The difference is small, and the sign flips at the same place, so the conclusion survives. Say so rather than hide it.
- Break-even 5.9% is the same calculation and has the same small bias.
- **Fix:** note in `promo_value.csv` or the README that the figures are approximate (± about $60), or switch to the counterfactual formula. Do not claim a precise net.

### 6. (Medium) Scale: both discount findings are tiny in dollars, and the README should say so
- 15% promo discount cost $470; best-case net +$1,349 over ten weeks. 10% discount: $1,696 over six months (0.56% of $305,184 revenue), $3,420 annualised. Garden's gap is ~$16–18k per half-year. Ranking by value, finding 1 dominates; findings 2 and 3 are secondary and should not be sold as the headline.
- `plan.md` row 3 says "USD of margin per year that could be recovered"; the answer is ≤ $3.4k and relies on the assumption "removing it loses few customers", which this data cannot test (the null model shows no basket effect; it says nothing about visit frequency).

### 7. (Medium) Discount result wording: "no sign it buys bigger baskets" is absence of evidence
- Raw matched gap is +0.226 lines per discounted transaction, +$1.32 list revenue; the null model (random flag per line) gives +0.232 and +$1.417, so the excess is −0.006 lines and −$0.095. That supports "the bigger basket is a counting artifact". Good, but it only rules out *basket size*.
- `excess_over_null` for `gp` (−0.661) is just the discount itself (1,696 / 2,789 txs = $0.61 each) plus noise; do not describe it as "discounted baskets are less profitable".
- **Fix:** state that the test cannot see whether the discount changes who visits or how often.

### 8. (Medium) Duplicate removal is an unverified assumption
- data/README.md and plan.md treat the 132 duplicates as "system errors". The duplicates are adjacent rows with the same Transaction ID, product and timestamp, so they could be a double scan or a real second item. Quantity is only ever 1 or 2, and 68 lines remain that share transaction and product with a *different* time or value.
- They are 132 rows, $741 of revenue (0.24%), so no headline changes. The statement belongs in the assumptions table (README has none for it).
- **Fix:** add the row "Exact duplicate rows are errors, not real repeat purchases; impact if wrong: +$741 revenue, no change to margins".

### 9. (Low) Garden's cause is stated more firmly than the data allows
- README line 25: "points to a branch-level cause, such as supplier terms, delivery costs or how costs are allocated … rather than recipes or waste on specific items". A uniform ×1.43 on all 45 products fits an allocation rule or a synthetic-data multiplier equally well; the data cannot distinguish "pays more" from "books more". Lines 38–39 already hedge; the wording at line 25 should say "consistent with", not "points to".
- A cost field being exactly proportional also means the "structural" label (line 23) says only that it is stable over time.

### 10. (Low) Small factual and wording issues
- data/README.md "Revenue formula … holds on every row": the maximum deviation is $0.005 (rounding to cents). Write "holds to within rounding (≤ $0.005)".
- discount_analysis.py excludes the 458 transactions that contain a 15% line, so the 10% cost (`$1,696`) omits 16 ten-percent lines worth $9.94 (total 10% cost $1,705.91). The sample is 33,429 transactions, not 33,887. Mention it if either number is quoted.
- plan.md says "Tuesday spike", "Evening peak", "Growth 50%", "94% of known customers" as "measured". The Tuesday/hour numbers have no script or table yet (`demand_patterns.py`, `forecast.py` do not exist). The growth figure is confirmed for Garden only (+49%). Do not quote them in the README until a script produces them.
- REQUIREMENTS.md points at `src/forecast.py` and `results/results.csv` (requirement 4); neither exists. If no model is built, say "no model; requirement 4 not applicable" instead.
- `promo_analysis.py` takes 2m16s wall but 52 min CPU (multithreaded `lstsq` inside 6 × 1000 bootstraps); on a 4-core laptop it may exceed the 3-minute guideline. Setting `OMP_NUM_THREADS=1` would probably help; not tested.
- `promo_who_got_it.csv` shows only 23.2% of eligible lines got the 15% and nothing in the data says why. Any DiD effect is the effect of an offer that reached under a quarter of the lines.
