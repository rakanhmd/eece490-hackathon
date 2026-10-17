# Finding 8: Basket and cross-sell analysis

Code: [`src/basket_analysis.py`](src/basket_analysis.py) (about 10 seconds; seeded, reruns give identical tables). Tables: `results/basket_*.csv`. Figures: `figures/basket_attach_by_category.png`, `figures/basket_pair_ratio.png`. Data: Jan–Jun 2026, after removing the 132 duplicate rows (33,887 transactions).

## Short answer
Many drink orders carry no food, but the gain from fixing that is modest. 59% of drink transactions (13,865 of 23,428) have no food item. The share that do (the "attach rate", 40.8%) is almost the same in every branch, hour, weekday and month. Of the variables we measured, only drink type was linked to it. Raising the attach rate by 1 to 5 percentage points would add an estimated **$640 to $4,340 of gross profit per six months**, which is roughly **$1,290 to $8,680 per year** (six months × 2). Offering the pairing as a 10% discount would lose money unless the attach rate rose by more than 9.4 points. These dollar figures are estimates built on assumptions listed below. They are not measured results.

## Definitions
- **Drinks:** Hot Coffee, Cold Coffee, Cold Drinks, Matcha & Tea. **Food:** Bakery, Breakfast, Desserts, Meals, Sandwiches. Every product is one or the other.
- **Drink transaction:** has at least one drink line. **Attach rate:** share of drink transactions that also have at least one food line. **Drink-only transaction:** the opposite, our measure of "could have carried food".
- **Primary drink:** the most expensive drink line in the basket, so each drink transaction falls in exactly one drink category.

## Measured facts (computed from the data)
Counts: 33,887 transactions = 9,563 drink + food, 13,865 drink-only, 10,459 food-only.

**1. Attach rate is flat except by drink type** (`basket_attach_rates.csv`, `basket_attach_homogeneity.csv`, `basket_attach_adjusted_tests.csv`):

| Segment | Attach rate | Is the difference real? |
|---|---|---|
| Branch (Garden / Harbour / Uptown) | 41.8% / 40.2% / 40.9% | No (chi-square p = 0.10; 0.12 after adjusting for the other factors) |
| Hour (17 hours) | 39.4% to 43.1% | No (p = 0.89) |
| Weekday, month | 39.8% to 41.9%; 40.2% to 41.5% | No (p = 0.39; 0.82) |
| Dine-in / takeaway | 40.3% / 41.6% | Borderline (p = 0.046 alone, 0.067 adjusted); small, and opposite to what we expected |
| **Primary drink category** | Cold Coffee **38.1%**, Cold Drinks 40.7%, Hot Coffee 41.1%, Matcha & Tea **43.0%** | **Yes** (p < 0.0001, also after adjusting) |

The drink-category gap holds inside each branch (Cold Coffee is lowest at Garden, Harbour and Uptown; Matcha & Tea highest at all three). So the opportunity is not "fix the slow hours" or "fix one weak branch": there is no weak hour or branch in this data.

**2. Pair patterns.** For every drink item × food item we compared the number of baskets that contain both with what we would expect if each item were picked by its popularity, independently of the rest of the basket. The expected value comes from 2,000 random reshuffles that keep each basket's shape and branch (`basket_pairs.csv`).
- *Category level* (`basket_pairs_category.csv`, figure `basket_pair_ratio.png`). Observed ÷ expected:
  - Cold Drinks + Bakery **0.63** (605 observed vs 958 expected).
  - Matcha & Tea + Meals **0.72**, + Breakfast **0.75**, + Sandwiches **0.79**, + Desserts **0.82**.
  - Hot Coffee + Desserts **0.80**.
  - The reverse is also there: Matcha & Tea + Bakery **1.48**, Cold Drinks + Sandwiches **1.70**, Cold Drinks + Meals **1.57**.
  - Ten category pairs are significantly under-sold (false-discovery rate 5%): they sum to about 1,040 baskets below expectation in six months (`basket_undersold_category_pairs.csv`).
- *Item level.* 7 of 506 pairs are significantly under-sold and 34 over-sold. Three of the 7 are Cold Drinks + Bakery (Lemonade + Blueberry Muffin: 2 observed vs 14 expected; Peach Iced Tea + Chocolate Croissant: 8 vs 28; Lemonade + Butter Croissant: 15 vs 35). The other four are Strawberry Matcha + Turkey & Cheese Sandwich (7 vs 23), Vanilla Latte + Frozen Yoghurt Cup (8 vs 23), Classic Matcha + Brownie (20 vs 39) and Chai Latte + Brownie (8 vs 22). The same direction appears in both Jan–Mar and Apr–Jun for all 7. Treat the item-level list as a pointer, not as proof: the counts are small (2 to 20 baskets), and when we restrict the comparison to baskets that already hold a drink and food, only 2 of the 7 still pass (Peach Iced Tea + Chocolate Croissant, Strawberry Matcha + Turkey & Cheese Sandwich).
- *Two different effects are mixed in the "popularity" comparison.* (a) Some drinks attach less often overall (point 1). (b) Given that a basket has both, some drinks go with some foods more than others. Restricting the expectation to drink + food baskets (`obs_over_exp_given_basket`) isolates (b): **Cold Drinks + Bakery (0.62), Matcha & Tea + Meals (0.64) and Sandwiches (0.70) stay under-sold**, while Hot Coffee + Desserts (0.98) goes away. Hot Coffee + Desserts is under-sold only because desserts and breakfast items are bought **without a drink** more often than bakery items (Frozen Yoghurt Cup 0.66, Tiramisu 0.74, Brownie 0.75 of their food-only share; Chocolate Cookie 1.30, Almond Croissant 1.25) (`basket_food_mix.csv`).

**3. Margin of the food involved** (`basket_food_margin_category.csv`; gross profit after discounts). Gross profit per unit, Harbour / Garden:

| Food | Harbour | Garden | Harbour margin | Garden margin |
|---|---|---|---|---|
| Bakery | $2.79 | $1.97 | 65.7% | 48.7% |
| Desserts | $3.56 | $2.16 | 56.5% | 35.6% |
| Breakfast | $5.38 | $3.43 | 60.3% | 40.4% |
| Sandwiches | $5.80 | $3.37 | 56.2% | 34.2% |
| Meals | $6.48 | $4.04 | 59.0% | 38.3% |

Bakery is the cheapest food to add and the one most under-sold with Cold Drinks. Garden's food margin is 17–22 points lower, the same cost gap as Finding 1. Food gross profit per drink + food basket is $3.70 on average (95% bootstrap interval $3.66 to $3.73): Harbour $4.22, Uptown $4.00, Garden $2.77.

## Estimates (these rest on assumptions)
Basis: Jan–Jun 2026 volume (23,428 drink transactions), each branch's own food margin (`basket_value_scenarios.csv`). "Annualised" means six months × 2 (one convention across the repo) and ignores growth.

| Scenario | Extra food baskets (6 mo.) | Extra gross profit, 6 months | Annualised |
|---|---|---|---|
| +1 pp attach, cheap add-on margin | 234 | $644 | $1,289 |
| +1 pp, average food margin | 234 | $868 | $1,737 |
| +2.5 pp, cheap add-on margin | 586 | $1,611 | $3,222 |
| +2.5 pp, average margin | 586 | $2,171 | $4,341 |
| +5 pp, cheap add-on margin | 1,171 | $3,222 | $6,444 |
| +5 pp, average margin | 1,171 | $4,341 | $8,683 |
| Benchmark: every drink category reaches Matcha & Tea's 43.0% | 527 | $2,037 | $4,075 |

**Range: about $640 to $4,340 per six months** (the first and the sixth row), or about $1,290 to $8,680 per year (six months × 2). For scale, that is 0.4% to 2.4% of the six-month gross profit of $178,994.

Why these numbers: +1 pp is a change too small to notice; +5 pp is about the size of the whole gap between the best and the worst drink category (4.8 pp: 43.0% vs 38.1%); the benchmark row lifts every category to the best one. "Cheap add-on" prices the extra basket at Bakery's margin (0.74 × the average food margin, measured). None of these is a forecast. We have no data on how much a prompt, a menu placement or a pairing offer would move the attach rate.

**Discounted pairing loses money.** If the offer is 10% off any food sold with a drink, the discount is also given to the 9,563 baskets that already carry food. The discount then costs about $6,800 to $7,400 per six months, more than every scenario gains (net −$3,100 to −$6,200). The attach rate would need to rise by **9.4 points (40.8% to about 50%)** to break even (`basket_discount_breakeven.csv`). A prompt, a menu board or a counter display has no such hurdle.

**Steering toward under-sold pairs adds little by itself.** Closing the ten under-sold category gaps is worth at most about $3,560 per six months, but only if those baskets were extra. If customers just swap one food for another, the extra profit is only the margin difference. That number is an upper bound, not an expected gain.

## Assumptions
| Assumption | If it is wrong |
|---|---|
| An extra attached basket earns the branch's average food gross profit per basket, or 0.74 of it (Bakery's margin) | A cheaper add-on (cookie only) pushes toward the low scenario; a sandwich or meal pushes above the high one |
| Extra food does not reduce drink sales or the basket's other items | If people trade a second drink for a pastry, gain falls |
| No change in labour, waste or prep cost for the extra items | Unmeasured. Extra bakery waste or staff time lowers the net, and we have no data on either |
| Same volume as Jan–Jun; per year = six months × 2 | Monthly sales rose about 49% from January to June at Garden, so a later-year run rate could be higher; if the rise is seasonal, a full-year figure could be lower |
| The 132 removed duplicates were system errors | They are 0.26% of lines; including them would not change any conclusion |
| A transaction ID is one customer visit | If one visit is split over several IDs, attach rate is understated everywhere equally |

## Alternative explanations and what we checked
- **Branch, hour or day explains the pattern:** not supported by our tests. Attach rate is flat on all three (table above), and the drink-category effect survives adjustment for them.
- **Customers, not drinks, explain the gaps.** Matcha & Tea buyers may simply be people who like pastries. The data cannot separate "the drink makes people buy a croissant" from "people who buy matcha also buy croissants". That is why we do not claim a prompt would work; we propose a test.
- **Multiple testing.** 506 item pairs would produce about 25 "significant" pairs at p < 0.05 by chance alone. We use a false-discovery correction (Benjamini–Hochberg) and check the same direction in both half-years.
- **Interaction with other findings:** Harbour's 15% dessert promo (Mar 12 to May 19, 502 lines) may have nudged dessert pairings at Harbour; it covers 1% of lines, so we did not remove it. The Garden cost gap lowers Garden's food margin here; fixing Garden's costs would raise the cross-sell numbers a little. Do not add the two findings together as if they were independent.

## A practical test Stories could run
Question: does a counter prompt raise the share of drink orders that include a food item, and does it pay?
- **Offer (no discount):** the cashier or POS prompt suggests a bakery item with Cold Drinks, and a savoury item or bowl with Matcha & Tea, because those are the under-sold pairs.
- **Design: switchback by branch-week.** Each week, each branch is randomly switched on (prompt) or off, for about 8 weeks, so every branch spends time in both arms. With one treated branch, any change at that branch (staff, stock, a local event) would be mixed up with the prompt; rotating the treatment spreads those changes across both arms. Compare attach rates in on-weeks and off-weeks within each branch.
- **How long.** We have not computed the detectable effect for the switchback design. For reference, `basket_pilot_power.csv` (80% power, 5% test level, June volumes, a day-to-day noise factor we measured at 1.07–1.13) gives the days needed for designs with one treated branch: a 5-point gain needs about 59 days with Garden against Uptown and 22 days with Harbour against Garden and Uptown. Those designs rest on one treated branch, so the figures are only a rough guide. Under those two designs, a 2–3 point effect needs 62–366 days.
- **What to record:** attach rate on drink transactions (main measure); food gross profit per drink transaction; drinks per transaction and average ticket (to catch swapping); weekly numbers, so a trend at one branch is visible.
- **Decision rule, set before the test:** roll out only if the lower end of the 95% interval for the attach-rate change is above the level needed to cover the extra staff time and waste. Stories has to supply those costs, because we do not have them.

## Weak areas
- Everything about the effect of a prompt is a guess; the data only describes how baskets look today.
- Six months only; no yearly seasonality, and sales grew through the period.
- Item-level pairs rest on small counts; the category-level pattern is the reliable part.
- We do not know what a cashier says today, whether a bakery case is next to the register, or which items were out of stock. Any of these could explain the Cold Drinks + Bakery gap better than customer taste.
- A transaction with two drinks counts once, under its most expensive drink. We did not test another rule.

## Approaches we did not use
- **Market-basket "lift" or association rules on all baskets.** Most baskets have one or two lines, so plain lift is distorted by basket size (in a quick exploratory check, not in the script, average lift came out well below 1, which cannot be right for unrelated items). The shuffle that keeps each basket's shape fixes this.
- **A recommender or classifier for "will this basket take food".** Among the variables we tested, branch, hour, day and month showed no detectable association with taking food, and the drink type alone gives a 5-point range. A model would add complexity without a decision to support.
- **Customer-level cross-sell** (who buys what over time): not attempted in the time we had. The data is real Stories data with anonymized IDs; 36.5% of lines have no Customer ID, so customer results cover identified customers only. 94% of identified customers use more than one branch.

## Reproduce
```bash
python src/basket_analysis.py   # needs data/stories_transactions.csv (see data/README.md)
```
