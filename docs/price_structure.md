# Garden's price structure: one multiplier, like its cost?

Code: `src/pricing_analysis.py`. Table: `results/pricing_structure.csv`.

## Test
For each product, the branch's value is divided by Harbour's. Prices and costs are stored in cents, so if a branch's value is round(m × Harbour's value, 2), each product's ratio can sit anywhere in m ± 0.005 ÷ Harbour's value. If one multiplier m fits inside every product's band, a single branch-level multiplier plus cent rounding reproduces all 45 values. We also fit branch value = slope × Harbour's value + intercept, and check whether the ratio rises or falls with the item's value (Spearman correlation).

## Results
| Ratio to Harbour (45 products) | Range | Std | One multiplier fits all within cent rounding? | Fit slope | Intercept (USD) | Spearman with item value |
|---|---|---|---|---|---|---|
| Garden price | 0.9512–0.9532 | 0.0005 | Yes, 0.9522–0.9526 | 0.9524 | −0.0003 | −0.0802 |
| Uptown price | 0.9122–0.9158 | 0.0008 | No | 0.9144 | −0.0015 | 0.1772 |
| Garden cost | 1.4261–1.4386 | 0.0019 | Yes, 1.4299–1.4302 | 1.4302 | −0.0003 | 0.1114 |
| Uptown cost | 0.9524–0.9651 | 0.0027 | Yes, 0.9599–0.9601 | 0.9598 | 0.0001 | 0.1934 |

## Reading it carefully
- **Garden's prices follow the same kind of rule as its costs.** Every Garden price is Harbour's price times about 0.952, rounded to the cent, and every Garden cost is Harbour's cost times about 1.430. There is no fixed amount per item, and the ratio does not drift with the item's price.
- **Uptown's prices are almost as uniform** (std 0.0008), but no single multiplier reproduces every price within cent rounding, so a few Uptown prices were set or rounded differently.
- **What this suggests.** A branch-level rule, such as a price list and a standard-cost table derived from Harbour's with one factor each, fits better than product-by-product setting. That makes the Garden cost gap more likely to come from one decision, such as a costing factor or an overhead loading, than from 45 separate supplier prices.
- **What it does not prove.** A supplier could charge a flat percentage on every item, and the anonymization could in principle have rescaled fields; we assume it changed only branch names and IDs. The invoice and allocation audit is still the test.
