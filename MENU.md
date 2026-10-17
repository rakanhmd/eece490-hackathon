# Menu profit: which products earn the money

Code: [`src/menu_profit.py`](src/menu_profit.py) (a few seconds; a rerun gave identical output and tables). Tables: `results/menu_*.csv`. Figures: `figures/menu_units_vs_margin.png`, `figures/menu_garden_margins.png`. Data: Jan–Jun 2026, 33,887 transactions after removing 132 duplicate rows; total revenue $305,184, gross profit $178,994 (58.7%). **Measured** facts and **estimates** are kept apart: the tables marked ESTIMATE rest on assumptions listed next to them.

## Short answer
- **Profit is spread across many products.** The top 5 earn 21.4% of gross profit, the top 10 earn 35.9%, the top 20 earn 60.1%, and the bottom 10 only 10.9% (`menu_products.csv`). The biggest earners are Iced Matcha, Iced Latte, Classic Matcha, Strawberry Matcha and Cold Brew; no single item matters much alone.
- **Food earns less per dollar than drinks, but more per unit.** Sandwiches 49.2% margin, Desserts 47.7%, Meals 51.8%, Breakfast 53.3% against Hot Coffee 66.7%, Cold Coffee 66.1%, Cold Drinks 63.3%, Matcha & Tea 60.9% (Bakery 60.1% is the exception among foods).
- **Seven items are low-profit and low-volume** (flagged by a fixed rule below), together 8.0% of gross profit; four items are **low-margin basket drivers**. Both lists are flags for a conversation, not decisions: nothing in the data shows what would happen if an item were repriced or removed.
- **Garden needs its own reading.** Garden's margin on every product is 17–24 points below Harbour's, so by its own menu 25 of 45 products earn under 50% margin (13 under 40%); Harbour and Uptown have none below 50%. Product rankings by margin are the same at Garden as elsewhere (rank correlation 0.999), because every Garden cost is about 1.43 × Harbour's. The product list does not point at one item to fix; it points at Garden's cost level (Finding 1; `GARDEN_CAUSE.md`).

## Every product (measured)
`results/menu_products.csv` has all 45 products with units, revenue, gross profit, margin, gross profit per unit, shares of units and profit, the share of transactions that include the product, its basket role and its flags. The highlights:

| | Product | Units | Gross profit | Margin | Profit share |
|---|---|---|---|---|---|
| Top 5 by profit | Iced Matcha | 2,314 | $9,427 | 58.9% | 5.3% |
| | Iced Latte | 2,617 | $9,179 | 65.2% | 5.1% |
| | Classic Matcha | 1,956 | $7,713 | 60.5% | 4.3% |
| | Strawberry Matcha | 1,481 | $6,128 | 53.5% | 3.4% |
| | Cold Brew | 1,494 | $5,796 | 74.8% | 3.2% |
| Lowest margins | Sparkling Water | 1,064 | $1,335 | 45.2% | 0.7% |
| | Turkey & Cheese Sandwich | 1,067 | $4,720 | 45.6% | 2.6% |
| | Brownie | 1,317 | $3,143 | 46.1% | 1.8% |
| | Chicken Pesto Sandwich | 1,145 | $5,734 | 46.3% | 3.2% |
| Highest margins | English Breakfast Tea | 473 | $1,355 | 81.8% | 0.8% |
| | Mint Tea | 631 | $1,882 | 80.8% | 1.1% |
| | Cold Brew / Iced Americano / Americano | 1,494 / 1,542 / 1,124 | | 74.8% / 74.7% / 74.6% | |

By category (`menu_category_summary.csv`): Matcha & Tea earns the largest profit share (17.1%), then Bakery (16.1%), Cold Coffee (15.2%), Hot Coffee (14.8%), Sandwiches (10.7%), Desserts (7.6%), Cold Drinks (7.5%), Breakfast (6.4%), Meals (4.7%). Gross profit per unit: Meals $5.55, Sandwiches $4.90, Breakfast $4.60, Matcha & Tea $3.83, Cold Coffee $3.52, Hot Coffee $3.09, Desserts $2.92, Bakery $2.47, Cold Drinks $2.46.

## Role in the basket (measured)
For a drink: of the transactions that include it, what share also carry a food item (the chain average is 40.8%). For a food: what share also carry a drink (average 47.8%). A product is labelled only if its 95% interval lies fully on one side of the average.
- **No drink clearly pulls food along.** Seventeen of the 23 drinks (every Hot Coffee and Cold Coffee item, plus all five Cold Drinks) sit *below* the average: they are bought alone more often than the typical drink. The six Matcha & Tea drinks are at or near the average, and none is clearly above it.
- **Most foods are stand-alone** (10 of 22 clearly so, 11 neutral). Sandwiches (Chicken Pesto, Turkey & Cheese), breakfast items (Egg Sandwich, Avocado Toast, Granola Yoghurt), all four desserts (Cheesecake, Brownie, Frozen Yoghurt, Tiramisu) and Soup of the Day are bought without a drink more often than average. **Chocolate Cookie is the only clear add-on** (usually bought with a drink). Most other bakery items are close to the average.
- This is the same pattern as in `FINDING_8.md` (food pairs with some drinks more than others, and desserts and breakfast are often bought alone), now by product.

## Flags (rules fixed before looking at the lists)
- **Low-profit, low-volume:** units in the bottom quartile of the menu (967 units or fewer) *and* gross profit in the bottom quartile ($3,143 or less over six months).
- **Low-margin basket driver:** share of transactions that include the item in the top quartile (3.9% or more) *and* margin below the menu median (59.8%).

**Low-profit, low-volume (7 items, together $14,234 or 8.0% of gross profit):**

| Product | Units | Gross profit | Margin |
|---|---|---|---|
| Quinoa Bowl | 502 | $3,090 | 52.4% |
| Granola Yoghurt | 575 | $2,408 | 52.7% |
| Blueberry Muffin | 928 | $2,327 | 62.7% |
| Mint Tea | 631 | $1,882 | 80.8% |
| Soup of the Day | 449 | $1,836 | 56.3% |
| English Breakfast Tea | 473 | $1,355 | 81.8% |
| Espresso | 686 | $1,336 | 72.7% |

Three of these (Mint Tea, English Breakfast Tea, Espresso) have high margins and are cheap, so they are small mainly because few are sold, not because each sale earns little. The data cannot say whether they matter to customers who buy them with other things. Whether to keep an item also depends on kitchen complexity, waste and stock, none of which is in the data.

**Low-margin basket drivers (4 items):** Iced Matcha (in 6.4% of transactions, 58.9% margin), Strawberry Matcha (4.1%, 53.5%), Cinnamon Roll (4.2%, 51.8%), Chocolate Croissant (4.3%, 58.2%). They are bought often and earn slightly less than the menu median. Iced Matcha is the largest profit source and Strawberry Matcha the fourth, so any change to them would be significant.

## Garden separately (measured)
Garden's margin is 46.9% against 65.0% at Harbour and 62.6% at Uptown. At Garden, 13 of 45 products earn under 40% margin and 25 under 50%; the lowest are Sparkling Water 29.4% (Harbour 52.9%), Turkey & Cheese Sandwich 29.7% (53.1%), Chicken Pesto Sandwich 30.8% (54.0%), Brownie 33.7% (55.3%), Cheesecake Slice 34.4% (55.7%), Chicken Salad Bowl 34.7% (56.5%), Avocado Toast 36.2%, Frozen Yoghurt Cup 37.1% (`menu_garden_vs_others.csv`, `figures/menu_garden_margins.png`). Harbour's lowest margin is 52.9% and Uptown's 50.5%, both Sparkling Water.

Applying the same flag rules to Garden's own menu (its own quartiles: units 319 or fewer and gross profit $770 or less; in 3.9% or more of Garden's transactions and margin under 48.7%):
- *Low-profit, low-volume at Garden:* Blueberry Muffin, Granola Yoghurt, Espresso, English Breakfast Tea, Mint Tea, Chicken Salad Bowl, Soup of the Day, Tuna Sandwich. Six of these are also flagged on the chain-wide list.
- *Low-margin basket drivers at Garden:* Chocolate Croissant, Brownie, Cheesecake Slice, Frozen Yoghurt Cup, Iced Matcha, Strawberry Matcha. The desserts appear here because Garden's low margins hit them hardest.

**ESTIMATE: where Garden's cost gap is concentrated.** If Garden bought each item at Harbour's unit cost, its gross profit would be $15,888 higher over six months (the same figure as the README's Garden estimate; this assumes Garden could buy at Harbour's costs, which is not known). By product the gain is spread out: Iced Matcha $826 (5.0%), Chicken Pesto Sandwich $784 (5.0%), Strawberry Matcha $655 (4.0%), Turkey & Cheese Sandwich $644 (4.0%), Classic Matcha $637 (4.0%); the top five give 22.3% (`menu_garden_cost_gap_by_product.csv`). No product-level fix recovers a large part of it; the cost level is the issue, which is why a menu change at Garden would not substitute for finding the cause of the 1.43× unit cost.

## ESTIMATES: what the flags might be worth (assumptions stated)
**Price rise on the 4 low-margin basket drivers.** Assumption: +5% on those four items only, same volumes and discounts, no shift to other items. Price sensitivity cannot be measured because prices never change in the data, so three elasticities are shown (`menu_price_scenarios.csv`; six months, annual figure = ×2 as elsewhere in the README):

| Elasticity (assumed) | Units | Gross profit change, six months | Per year (×2) |
|---|---|---|---|
| 0 | 0% | +$2,101 | +$4,201 |
| −1 | −4.8% | +$881 | +$1,762 |
| −2 | −9.3% | −$281 | −$562 |

The gain disappears at an elasticity of about −1.8. The estimate leaves out customers who give up a drink or a food item together with the item that rose, which would lower the gain.

**Removing the 7 low-profit, low-volume items.** The items earn $14,234 over six months. What is lost depends on how many buyers switch to another item, which the data cannot show (`menu_drop_scenarios.csv`). Assumption: a share of the buyers choose another item that earns the same gross profit per unit.

| Buyers who switch | Gross profit lost, six months |
|---|---|
| 0% | $14,234 |
| 50% | $7,117 |
| 80% | $2,847 |

The saving from a shorter menu (less waste, simpler kitchen) is not in the data, so we do not compare it. We would not remove an item on this evidence.

## What the data cannot tell us
- **Whether anything would change if a price or a menu item changed.** Prices never change in the data and no item is ever removed, so there is no variation to learn elasticity or substitution from. The two estimate tables above are scenarios.
- **Why a product sells.** A product's basket role is an association: Chocolate Cookie is bought with drinks, but we do not know whether the cookie causes the sale of a drink or the other way round.
- **Cost accuracy.** Margins use each product's recorded unit cost, which is a fixed number per product per branch for the whole period (`GARDEN_CAUSE.md`); real purchase costs may differ.
- **Waste, preparation time, kitchen capacity and stock-outs** are not recorded, but they decide whether an item is worth its place.

## A test Stories could run
For the price estimate, a week-level chain-wide price switchback is specified in `EXPERIMENTS.md` (pilot 3); its power calculation shows that a 20-week pilot can measure the loss of visits but cannot confirm a gross-profit change as small as the +$881 to +$2,101 above (about 0.5% to 1.2% of six-month gross profit), so a price change on four items is better judged from a smaller, item-level pilot: raise the price of the four items in randomly chosen weeks and compare units of those items and of the items normally bought with them. We have not simulated that design, so we make no claim about how long it would take.

## Reproduce
```bash
python src/menu_profit.py   # needs data/stories_transactions.csv (see data/README.md)
```
