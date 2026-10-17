# What are the extra Tuesday transactions made of?

Code: [`src/tuesday_decompose.py`](src/tuesday_decompose.py) (a few seconds, seeded; a second run from scratch gave identical output and tables). Tables: `results/tuesday_decomp_*.csv`. Figures: `figures/tuesday_decomp_components.png`, `tuesday_decomp_regulars.png`. Data: 25 full Mon–Sun weeks (Mon 5 Jan to Sun 28 Jun 2026), 33,887 transactions after removing 132 duplicates; 63.5% of transactions carry a Customer ID.

## Short answer
**Mostly more distinct customer IDs on Tuesday, plus a third that has no ID. Almost none of it is more trips per ID. The ID data cannot say why, and it cannot show that these are different people.** About two thirds of the extra Tuesday transactions are IDs that did not buy on a normal weekday that week. But those IDs are mostly not new faces (from week 9 on, only 2.6% of the excess is from IDs first seen that week) and not a Tuesday-only crowd: 99% of them also buy on other days, and no customer is a "Tuesday-only regular". The mix of the surge (66% identified, 34% not) is the same as the mix of all transactions (63.5% identified). Visits on one weekday look independent of visits on another for the same ID. Whatever causes the surge, the IDs behave like one pool of customers who buy a little more often on Tuesday, not like a distinct group.

## Method
For each branch and week, Tuesday is compared with the mean of Mon/Wed/Thu/Fri at that branch. A day's transactions = A (no Customer ID) + C × t, where C is the number of distinct identified customers that day at that branch and t is transactions per identified customer that day. The Tuesday excess E = Tuesday − baseline is split exactly (checked for every branch-week) into:
- **(d) no Customer ID:** the change in A.
- **(b) more transactions per identified customer:** the change in t × the average C.
- **(a) more distinct identified customers**, split into **(c1)** customers whose first appearance in the data is before this week and **(c2)** customers whose first appearance is in this week. We call (c2) "first seen in the data", not "new customer": the file starts on 2026-01-01, so in January almost everyone is "first seen".

Shares are pooled over weeks (sum of a component ÷ sum of the excess). The 95% intervals come from a bootstrap that resamples whole weeks (2,000 resamples; the same weeks for all branches). "All branches" adds up the three branch-level components; a customer who visits two branches counts once in each.

## Results (`tuesday_decomp_shares.csv`)
Average Tuesday excess: **95.4 transactions per week** across the three branches (Harbour 44.8, Garden 33.2, Uptown 17.4). Tuesday has about 50% more distinct identified customers than a normal weekday (for example Garden 59.4 vs 38.1, Harbour 85.0 vs 56.5, Uptown 34.0 vs 22.0), while transactions per customer per day are about 1.01 on every day type (`tuesday_decomp_means.csv`).

| Component (share of the Tuesday excess, 95% CI) | All branches | Garden | Harbour | Uptown |
|---|---|---|---|---|
| (a) more distinct identified customers | **65.3%** (62.0–68.8) | 64.5% (58.9–70.5) | 64.2% (59.1–69.0) | 69.4% (61.4–76.0) |
| of which (c1) seen before this week | 52.6% (45.4–58.9) | 51.8% (43.9–59.3) | 52.0% (43.7–59.5) | 55.8% (44.3–65.2) |
| of which (c2) first seen in the data this week | 12.6% (6.0–21.6) | 12.7% (5.7–21.4) | 12.2% (4.7–21.8) | 13.6% (6.9–22.2) |
| (b) more transactions per identified customer | **0.6%** (−0.1 to 1.2) | 0.9% (0.05–1.8) | 0.5% (−0.5 to 1.5) | 0.1% (−0.5 to 0.7) |
| (d) no Customer ID | **34.2%** (30.7–37.3) | 34.6% (28.8–39.9) | 35.3% (30.5–40.2) | 30.5% (23.9–38.4) |

- **No component is a surprise by branch:** the three branches give the same picture and their intervals overlap.
- **(c2) is inflated by the start of the file.** The share of identified transactions made by a customer first seen that week falls from 92.7% in week 1 to 23.1% in week 8, 19.2% in week 9 and 0.3% in the last week (`tuesday_decomp_first_seen_trend.csv`). Using only weeks 9–25, (c2) is **2.6%** (0.8–4.7), (c1) is **60.7%** (57.4–64.3), (a) is 63.2% (59.5–67.8), (b) 0.5% and (d) 36.3% (31.9–39.9). So the surge is not driven by customers appearing for the first time: the ID pool (about 3,500 IDs) is used up gradually, and by the last weeks almost every ID has been seen before.
- **The surge is identified and anonymous in the same proportion as everything else:** 65.8% of the excess carries an ID (a + b) against 63.5% of all transactions. The anonymous third is not unusual.

## Who comes on Tuesday (distinct customers, not transactions)
(`tuesday_decomp_customers_by_weekday.csv`, `tuesday_decomp_tuesday_regulars.csv`)

| Weekday | Distinct customers who bought that day | Of them, also buy on other days | Customers whose visits are all on that day |
|---|---|---|---|
| Mon | 1,970 | 99.4% | 0.6% |
| **Tue** | **2,560** | **99.1%** | **0.9%** |
| Wed / Thu / Fri | 1,985 / 1,978 / 2,122 | 99.3–99.5% | 0.6–0.8% |
| Sat / Sun | 1,590 / 1,826 | 99.9% / 99.6% | 0.1% / 0.4% |

- **99.1% of distinct Tuesday customers also buy on other days.** Tuesday is not a separate set of people. Of the 3,494 IDs, 2,560 (73%) bought on at least one Tuesday.
- **No "Tuesday-only regulars":** among 3,030 customers with at least 4 visits, Tuesday makes up 22.0% of their visits. Only **1** of them has every visit on a Tuesday. The number with at least half of their visits on Tuesday is **292**; if the weekday labels were shuffled at random we would expect 277 (95% range 253–303), so 292 is within chance. The spread of customers' Tuesday share (standard deviation 0.172) is about what random weekdays give (0.168).
- **Do Tuesday visits replace visits on other days?** For the same customer, we compared visits on other days in weeks with a Tuesday visit and weeks without one. The difference is +0.006 visits per week (95% CI −0.011 to +0.021, 1,266 customers), and between +0.002 and +0.013 for every other weekday, all with intervals around zero (`tuesday_decomp_displacement.csv`). Tuesday visits neither replace nor add to other visits for the same ID. This is a separate observation from the weekend finding (`FINDING_weekend.md`), which found no clear week-to-week offset in the totals.

(The mean share of a customer's visits that falls on the day, 30% for Tuesday vs 22–25% for other days, is higher for Tuesday simply because Tuesday has more customers and more visits; do not read it as loyalty to Tuesday.)

## In plain words
Is the surge more people, more trips from the same people, or not attributable?
- **More distinct IDs on the day** explains about two thirds of it, and **more trips per ID within the day** explains almost none (0.6%). In ID terms it is "more people", not "the same people coming twice".
- **But "more people" is a statement about IDs, and IDs are weak evidence about people.** The extra IDs are the same ones that shop on other days, few are first-time IDs after the first two months, and they do not form a Tuesday-only group. Within one ID, Tuesday visits and other-day visits are independent. This looks like one pool of customers who each come a bit more often on Tuesday, not like extra customers who arrive only then. We cannot tell whether that pool is real people (a recurring habit) or an artefact of how IDs were assigned (Finding 1 already found that 94% of known customers appear at several branches).
- **A third is not attributable** because it has no Customer ID.
- So our overall verdict is: **mostly extra identified customers, but not attributable to a distinct kind of customer with the IDs available.** We have no evidence of a group, a promotion or a routine behind it.

## What the data cannot show
- **Promotions, app pushes, e-mails or social posts:** there is no campaign calendar, send log or redemption field except the discount rate on the line.
- **Staffing, opening hours, local events, weather, school or work schedules, competitor closures:** none of these are in the file.
- **Whether an ID is one person:** IDs repeat across branches at a rate that does not look like real customers.
- **Why Tuesday:** the decomposition says what the surge is made of, not what caused it. All reasons below are hypotheses until checked.

## The Stories records that would settle it
1. **A promotion and campaign calendar for Tuesdays** (offers, loyalty-app pushes, e-mails with send time and number of recipients, delivery-app deals) for Jan–Jun. If a campaign hits every Tuesday, the surge is its response; the per-week excess should line up with campaign size.
2. **Till or card-settlement data with a payment token or loyalty tap for every sale** (including the anonymous third), so distinct people can be counted without the unreliable IDs.
3. **Daily till (Z-report) or bank totals by branch** to confirm the Tuesday peak is real in money received (the check proposed in `FINDING_weekend.md`).
4. **Staff rosters by day**, to see whether Tuesday is staffed up because it is busy or is busy for another reason.

## Weak areas
- 25 weeks. The week-block bootstrap treats weeks as exchangeable; a trend in the surge would widen the true uncertainty.
- The (c1)/(c2) split depends on the file starting in January; the weeks 9–25 table is the better reading.
- A customer who visits more than one branch on the same Tuesday is counted at each branch in the branch-level components.
- With about 3,500 IDs and nearly all of them already seen by the last weeks, any week-level change is a change in how often the same IDs appear, which is why the "more trips" and "more people" labels are close together in practice.

## Reproduce
```bash
python src/tuesday_decompose.py   # needs data/stories_transactions.csv (see data/README.md)
```
