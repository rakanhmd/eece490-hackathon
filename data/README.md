# Data

`stories_transactions.csv`: Stories coffee transaction lines, provided by the course for the EECE 490 hackathon (October 17, 2026). Transaction IDs are replacement IDs (`SYN-…`), as stated in the brief.

The raw file is **not committed**. It is company transaction data, so we keep it out of a public repo. To reproduce our results, place the file here as `data/stories_transactions.csv`. Every summary table we rely on is saved in `results/` so the evidence can be inspected without the raw data.

## Columns
Transaction ID, Date, Time, Branch, Customer ID, Order Type, Product, Category, Quantity, Unit Price (USD), Discount Rate, Unit Cost (USD), Line Revenue (USD), Line Gross Profit (USD)

## Data quality checks (measured)
| Check | Result |
|---|---|
| Rows | 51,177 lines, 2026-01-01 to 2026-06-30 (181 days), 3 branches, 45 products, 9 categories |
| Exact duplicate rows | 132 (same transaction, time, product and values). **Removed** → 51,045 lines, 33,887 transactions |
| Missing Customer ID | 36.5% of lines (anonymous purchases) |
| Revenue formula | Line Revenue = Quantity × Unit Price × (1 − Discount Rate) holds on every row |
| Profit formula | Line Gross Profit = Line Revenue − Quantity × Unit Cost holds on every row; no negative values |
| Quantity / prices | No zero or negative values; quantity is 1 or 2 |
| Customer IDs across branches | 94% of known customers bought at more than one branch, which is unusual for a café chain. Treated as a caveat: customer IDs may not identify real individuals reliably |
