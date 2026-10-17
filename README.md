# Stories Coffee: <headline finding>

**Team:** Rakan Bou Hatoum Hamadeh · Muche Abere Workie
EECE 490 (Introduction to Machine Learning), American University of Beirut · Hackathon, October 17, 2026

## Conclusion
<One paragraph for the CEO: the problem, the recommended action, the estimated value in USD and the main assumption it depends on. Written last.>

## The business problem
<Which decision this helps Stories make, and why it matters.>

## Measured findings
Facts computed directly from the data (after removing 132 duplicate rows). Each one points to the script and the table that produce it.

1. **Garden earns far less gross profit per dollar of sales than the other branches.** Gross margin, January to June 2026:

   | Branch | Revenue (USD) | Gross profit (USD) | Gross margin |
   |---|---|---|---|
   | Harbour | 150,099 | 97,503 | 65.0% |
   | Uptown | 55,554 | 34,795 | 62.6% |
   | Garden | 99,531 | 46,696 | 46.9% |

   The gap is the same every month (Garden 46.7–47.2%), so it is structural, not a one-off.

2. **The gap comes from unit cost, not price.** For every one of the 45 products, Garden's recorded unit cost is 1.43× Harbour's (range 1.426–1.439). Garden's prices are about 5% *lower* than Harbour's (Uptown's about 9% lower). A uniform 43% markup on every product points to a branch-level cause, such as supplier terms, delivery costs or how costs are allocated to Garden, rather than recipes or waste on specific items.

3. <Next finding: in progress>

## Estimated business value
Estimates, kept separate from the measured facts above.

- If Garden's costs matched Harbour's cost ratio, gross profit over the same six months would be about **$18,000 higher** (Garden revenue × 18.1 margin points), or about **$15,600** if matched to Uptown. That is roughly $31,000–36,000 per year at the current sales level.
- <Further estimates: in progress>

## Assumptions and what would change the recommendation
| Assumption | Why it matters | If it is wrong |
|---|---|---|
| The `Unit Cost` column reflects real costs Stories pays per item | The Garden finding depends on it | If Garden's cost includes allocated overheads (e.g. higher rent) that other branches book elsewhere, the gap may be an accounting difference with little savings available |
| Garden's higher cost is not buying better quality that supports its sales | Cutting cost could otherwise hurt demand | Savings would be offset by lost sales |
| <more> | | |

## A practical test Stories could run
<e.g. audit how Garden's costs are recorded, then a one-month pilot buying Garden's top 10 products through Harbour's supplier, comparing cost per unit and sales against the previous month and against the other branches.>

## Weak areas and uncertainty
- Only six months of data (January–June), so there is no yearly seasonality.
- 36.5% of lines have no Customer ID, and 94% of known customers appear at several branches, so customer-level conclusions are uncertain.
- <more>

## Approaches we considered and rejected
<What we tried or decided against, and why.>

## Data quality
See [`data/README.md`](data/README.md): row counts, duplicates removed, missing values and formula checks.

## How to reproduce
```bash
pip install -r requirements.txt
# place stories_transactions.csv in data/ (see data/README.md)
python src/<script>.py
```
Summary tables are saved in `results/`, figures in `figures/`.
