# Does Tuesday's surge offset the weekend? And the takeaway drop at 18:00

Code: [`src/weekend_check.py`](src/weekend_check.py) (a few seconds, seeded, a rerun gives identical output and tables). Tables: `results/weekend_*.csv`. Figures: `figures/weekend_weekly_series.png`, `weekend_offset_scatter.png`, `weekend_takeaway_by_hour.png`. Data: Jan–Jun 2026, 33,887 transactions after removing 132 duplicate rows.

**Everything below is a hypothesis about the data, not a proven cause.** The file shows what happens, not why. The check that could decide between the explanations needs data we do not have (till and bank totals).

## Short answer
1. **The totals are close, but the weeks do not move together.** Over 25 full weeks the extra Tuesday transactions (2,385) and the missing weekend transactions (2,132) are of similar size (ratio 1.12). From week to week, though, a weaker weekend does not reliably go with a bigger following Tuesday (r = +0.32, p = 0.12), and the one raw correlation that looks significant disappears once we allow for the growth in sales. So we **cannot confirm** that Tuesday makes up for the weekend.
2. **Takeaway share drops in one step at 18:00**, from 54.0% to 28.0%, in every branch, weekday and month. A step this sharp and this uniform looks more like a rule or a till setting than customers changing their minds. This too is a hypothesis.

## 1. Tuesday excess vs weekend deficit
**Definitions.** Full Monday-to-Sunday weeks only: 25 weeks, Mon 5 Jan to Sun 28 Jun. *Baseline* = mean daily transactions on Mon, Wed, Thu and Fri of that week. *Tuesday excess* = Tuesday − baseline. *Weekend deficit* = 2 × baseline − (Saturday + Sunday); positive means the weekend was weaker than two normal weekdays. "Previous weekend" for a Tuesday is the Sat + Sun of the week before (24 pairs, as the first week has no earlier full weekend); "same-week weekend" is the Sat + Sun right after that Tuesday (25 pairs).

**Measured size** (all branches, per week on average; `weekend_weekly.csv`, `weekend_size_comparison.csv`):

| | Transactions per day | vs baseline |
|---|---|---|
| Mon/Wed/Thu/Fri (baseline) | 186 | |
| Tuesday | 281 | +52% (95 extra per week) |
| Saturday | 130 | |
| Sunday | 157 | Sat + Sun together 23% below two baseline days (85 missing per week) |

Tuesday was above the baseline in all 25 weeks (excess 32% to 69%, median 51%), and the weekend was below it in all 25 weeks (deficit 9% to 32%, median 24%). Whole-period totals: 2,385 extra Tuesday transactions vs 2,132 missing weekend ones. Two steady gaps of similar size will give totals like this by coincidence, so the ratio of 1.12 is **not** evidence of an offset.

**Do the weeks move together?** The offset story predicts a positive correlation: the weaker the weekend, the stronger the next Tuesday. Pearson r with a 95% Fisher interval; permutation p = 10,000 shuffles of the weeks; "circular shift" keeps each series' trend and autocorrelation; "partial" removes the linear effect of the baseline volume of both weeks (`weekend_offset_tests.csv`, all branches):

| Tuesday excess vs | n | r (95% CI) | Permutation p (two-sided) | Circular-shift p | Partial r given volume |
|---|---|---|---|---|---|
| Previous weekend deficit, relative to baseline | 24 | +0.32 (−0.09 to +0.64) | 0.12 (one-sided 0.06) | 0.13 | −0.16 |
| Same-week weekend deficit, relative | 25 | −0.17 (−0.53 to +0.24) | 0.42 | 0.56 | −0.09 |
| Previous weekend deficit, raw counts | 24 | +0.50 (+0.12 to +0.75) | 0.013 | 0.042 | −0.09 |
| Same-week weekend deficit, raw counts | 25 | +0.18 (−0.23 to +0.54) | 0.37 | 0.52 | −0.13 |
| (control) Tuesday excess vs baseline volume | 25 | +0.43 (+0.04 to +0.70) | 0.035 | 0.12 | n/a |

- **The only "significant" result is the raw-count one for the previous weekend** (r = 0.50, p = 0.013). It is a growth effect: sales rose through the half year, so busier weeks have both bigger Tuesday excesses and bigger weekend deficits in raw counts. Tuesday excess correlates 0.43 with baseline volume alone (control row). Once we control for volume, the partial correlation is −0.09; with relative (percentage) measures it is not significant (p = 0.12).
- The same-week weekend shows no positive relation (r = −0.17).
- By branch (relative, previous weekend): Garden +0.09 (p = 0.69), Harbour +0.22 (p = 0.29), Uptown +0.30 (p = 0.15). Same-week weekend: Garden −0.46 (p = 0.019), Harbour −0.39 (p = 0.057), Uptown −0.20 (p = 0.32). We ran 6 branch tests without correction, so the Garden result is not strong evidence (its circular-shift p is 0.08).
- With 24–25 weeks, only a fairly strong link could be detected; a moderate one (r about 0.3) could be present and missed.

**Verdict: not supported by this data.** There is no reliable week-to-week offset. The totals of the two gaps are similar in size, which fits an offset but would also arise by chance. If Tuesday's surge were simply the previous weekend's sales posted late, we would expect the two to track each other closely week by week; they do not (r about 0.3 with a wide interval). That is also a hypothesis.

## 2. Takeaway share by hour
(`weekend_takeaway_by_hour.csv`, `weekend_takeaway_15min.csv`, `weekend_takeaway_drop_by_segment.csv`)

| Hours | Takeaway share of transactions | Transactions |
|---|---|---|
| 07:00–17:59 | 54.0% (each hour 51.1% to 56.0%) | 16,822 |
| 17:00 hour | 54.0% | 1,814 |
| 18:00 hour | 30.1% (95% CI 28.2–32.1%) | 2,084 |
| 19:00–23:59 | 27.3% to 28.3% in each hour | 14,981 |
| 18:00–23:59 | 28.0% | 17,065 |

- **The drop is abrupt:** in 15-minute bins the share is 55.6% at 17:45 and 29.3% at 18:00, with no slope before or after.
- **It is the same everywhere:** the fall is 25.8 points at Harbour, 26.0 at Garden and 26.4 at Uptown; 23.7 to 27.2 points on each weekday and 25.1 to 27.2 in each month.
- **It matters for volume:** 50.4% of all transactions happen at 18:00 or later, so the whole evening peak is on the low-takeaway side.
- Tuesday's overall takeaway share (41.7%) matches Mon/Wed/Thu/Fri (40.8%) and Sat/Sun (40.2%), so Tuesday's extra transactions do not differ by order type.

**Hypotheses (none proven):**
1. *A till or process rule at 18:00:* the order-type default or the available options change in the evening (for example a takeaway counter or delivery partner stops, or the POS records "dine-in" by default after 18:00). A rule would give exactly this: abrupt, same in every branch, weekday and month.
2. *A real change in what customers do:* evening customers sit down. This would normally be gradual and differ by branch or weekday, which is not what we see, so we consider it less likely.

## A test for Stories
Compare independent daily records with this data. For each branch and day, Stories already has these from the till or the bank:
1. **Daily till (Z-report) or card-settlement totals vs this file's daily transactions and revenue.** Include Mon–Sun for a few weeks.
   - If the till also shows Tuesday about 50% above the other weekdays and weekends about a quarter lower, the pattern is real demand, and staffing and promotions can use it.
   - If till totals are flat across the weekdays but this file shows a Tuesday peak, the Tuesday surge is a data or posting artefact (for example the file posts weekend sales on Tuesday). Then no business action should rest on it.
   - Ask for the posting timestamp and the sale timestamp of each transaction; they should match.
2. **Check the offset directly:** do the till totals of Saturday and Sunday equal the file's weekend totals, with no weekend sales appearing on Tuesday?
3. **Check whether something recurring happens on Tuesdays** (a standing promotion, a delivery-app deal, a local market or class).
4. **For the 18:00 drop:** ask how the POS sets the order type in the evening, and whether takeaway or delivery stops at 18:00. Pull 30 receipts from 17:30–18:00 and 30 from 18:00–18:30 and compare what customers actually did with what the till recorded.

## Weak areas
- 25 weeks (about 6 months): no yearly cycle, and a growth trend that confounds raw counts.
- A "deficit" depends on the baseline we picked (Mon/Wed/Thu/Fri average). A different baseline would shift the size but, as both gaps are present in every week, probably not the conclusion.
- The data is real Stories data with anonymized IDs; 36.5% of lines have no Customer ID, so customer results cover identified customers only. 94% of identified customers use more than one branch. This analysis uses daily totals, so it does not follow customers from a weekend to a Tuesday; TUESDAY_DECOMP.md does that for identified customers.
- The dataset has no sale-versus-posting times and no till totals, so we cannot tell a real demand shift from an artefact. That is why we propose the test above.

## Reproduce
```bash
python src/weekend_check.py   # needs data/stories_transactions.csv (see data/README.md)
```
