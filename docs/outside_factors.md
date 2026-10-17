# Outside factors: full detail

This is the long version of the README section "Did outside factors cause this?". The README keeps the figure and one merged table of patterns, tests, verdicts, remaining explanations and next tests.

We tested whether public data explains the two biggest patterns, the Tuesday surge and Garden's 1.43× unit cost. We also compared our data with real shops. **Assumption:** Stories is a Lebanese chain, and branch addresses are not in the data, so all three branches are treated as being in Greater Beirut (lat 33.89, lon 35.50). Brackets are 95% intervals. Real-shop values are references, not causes. All datasets, URLs, licenses and download dates are in [`data/README.md`](../data/README.md).

![Real shops vs Stories](../figures/outside_factors_summary.png)

| Factor | Data source | Real-world effect | Our effect | Verdict |
|---|---|---|---|---|
| Public holidays | holidaydb.com, calendarlabs.com; French government holiday API | French bakery: +36% [+19, +54] | −0.5% [−3.9, +3.0] over 26 holiday days | Not supported by our test. Ours lacks an effect our data could detect |
| Temperature | Open-Meteo, Beirut; Paris for the bakery | French bakery, within month: +0.82% per °C [+0.37, +1.27] | −0.09% per °C [−0.54, +0.37] within month | Not supported by our test. The difference is borderline: the intervals touch |
| Hot days and cold drinks | Open-Meteo; United Baristas | One London café: cold-coffee share +2.2 points per °C | +0.08 points per °C [−0.06, +0.22]; 24.4% in January, 25.0% in June | Not supported by our test |
| Rain | Open-Meteo; Foursquare and AccuWeather | French bakery: −2.6% [−6.9, +2.0]; US coffee shops: less traffic in rain | −0.9% [−3.6, +1.9] | Not supported by our test. Cannot tell if different |
| Ramadan | L'Orient Today | — | Evening share +0.4 points [−1.4, +2.2] vs before, −1.6 [−3.6, +0.4] vs after | Not supported by our test |
| Security escalation from Mar 2 | Al-Monitor, LBC | — | March +2.4% [−2.6, +6.8], April +0.8% [−2.2, +5.3] vs the January–February trend | Not supported by our test |
| School or campus (Tuesday) | AUB Provost calendar, LBC school closures | — | Tuesday ratio −0.026 [−0.096, +0.050] with AUB online or out; still 1.50× | Not supported by our test |
| University Tue/Thu timetable | Transactions | — | Thursday / Mon, Wed, Fri = 0.971 [0.940, 1.003] | Not supported by our test |
| A local cause near one branch | Transactions | — | Tuesday ratio Garden 1.56 [1.49, 1.66], Harbour 1.56 [1.47, 1.65], Uptown 1.53 [1.42, 1.67] | Not supported by our test |
| Tuesday peak itself | Kaggle shop data; Placer.ai; Square UK | Bakery 0.97, vending machine 1.08, Maven (fictitious) 0.98. Starbucks and UK coffee buyers peak on Saturday, 1.49× the average weekday | 1.53; Saturday is our quietest day, 0.69× (both against the Mon, Wed, Thu, Fri average) | Ours is unusual |
| Day-to-day variation | Kaggle shop data | Bakery 8.45, vending machine 1.84, Maven (fictitious) 4.76 | 0.98, inside the pure-chance range 0.88–1.14 | Not supported by our test. Ours is much steadier; habitual demand from regulars is our hypothesis |
| Growth, weather and inflation | Open-Meteo; Lebanon CPI (Central Administration of Statistics) | Consumer prices +17.25% a year (June 2026) | +52.6% transactions, January to June; the weather change implies a −0.75% change in transactions (−1.78% of the log growth); no price changed in six months | Not supported by our test. Growth is volume, not price; prices did not change |
| Fuel and Garden's costs | FRED Brent crude ([`GARDEN_CAUSE.md`](../GARDEN_CAUSE.md)) | Brent weekly mean $62.93 to $124.61 | Garden's mix-neutral cost ratio moved by 0.0001 | Not supported by our test |
| World coffee price and costs | IMF arabica price via FRED | Arabica −15.4%, January to June | All 135 product-branch unit costs unchanged | Not supported by our test. Unit costs are consistent with standard recipe costs in the till system |
| Location of Garden | Transactions ([`GARDEN_CAUSE.md`](../GARDEN_CAUSE.md)) | — | Garden's hours, basket size and customers match the other branches (hour-profile p = 0.81) | Not supported by our test, but rent and delivery cannot be tested without addresses |
| Industry cost levels | Starbucks 10-K; Zest café targets | Starbucks 31.4% cost of goods; café targets 20–25% coffee, 25–35% food | Harbour 35.0%, Uptown 37.4%, Garden 53.1% | Context: Garden is the abnormal branch |

**Overall verdict.** No external cause we could test is supported for either pattern. The Tuesday surge is the same at all three branches, so it is not unique to one branch; weather, calendar, conflict, school and campus are weakened by our tests, and our hypothesis is an internal driver, something Stories itself does on Tuesdays; this is not established. Garden's 1.43× ignores world coffee and fuel prices and is about the same on every product (1.426–1.439), which is consistent with how Garden's standard costs are set; location costs (rent, delivery distance) could not be tested without branch addresses.

**What the steadiness means.**
- **Steadier than the reference shops.** Stories' daily counts vary by 0.98, inside the pure-chance range of 0.88–1.14. A real bakery varies by 8.45, a real vending machine by 1.84 and a fictitious shop by 4.76. Stories also shows no weather, holiday or conflict effect.
- **Habitual demand (hypothesis).** We read this as stable, habitual demand from regulars. The figures below fit that reading but do not prove it (`results/customer_regulars.csv`):
  - 98.5% of identified customers bought more than once in six months;
  - 93.1% came back within 30 days of their first visit;
  - 93.8% used more than one branch.
- **Standard costs.** Unit costs that never change are consistent with standard recipe costs held in the till system.
- **Prices.** Prices did not change during about 17% annual inflation.

### Details
**Method.** Weather and calendar effects come from the weekday + log-trend model of finding 5, with p-values from shuffling weather across days within each month. Adding temperature and rain raises R² by only 0.00018 (p = 0.56). Source: `src/external_factors.py`, `results/external_*.csv`, `figures/weather_vs_sales.png`, `figures/tuesday_by_branch_school.png`.

**Tuesday.**
- **Same at every branch.** The surge does not differ between branches, which argues against a school, market day or office next to one shop.
- **Campus and school.** It did not fade while AUB taught online, after its exams, or in late June; the June 23 week has the highest ratio of the half-year at 1.74.
- **One test was sensitive to how we chose weeks.** Keeping only weeks with three or more non-holiday comparison days gives a small dip with the campus out, −0.068 [−0.135, −0.001], p = 0.08. Keeping weeks with two comparison days gives −0.026, p = 0.51. Either way Tuesday stays about 1.5×.
- **Calendar caveats.** The school Easter and Eid closures contained no Tuesday. Late June rests on two weeks, one of them a holiday. The end-of-school date of June 15 is an assumption.

**Garden's costs.** Recorded unit costs never change in six months, while world arabica fell 15.4% and Brent roughly doubled. So the cost column is consistent with standard recipe costs from the till system, not month-by-month purchase prices. [`GARDEN_CAUSE.md`](../GARDEN_CAUSE.md) has the fuel, flat-factor and location tests.

**Security escalation.** Errors of about ±6% are normal for this model: scored on February, with no escalation, it gives +5.7%. So the March and April results are inconsistent only with drops larger than about 3%.

**Day-to-day variation.** Real shop counts usually vary more than a pure-chance (Poisson) model, because of weather, events and promotions. Stories' per-branch ratios are Garden 0.86, Harbour 1.10 and Uptown 0.99, against pure-chance ranges of about 0.76 to 1.25. The pooled 0.98 in the table uses year-month cells, so the same method fits every reference dataset. A ratio near 1 means demand barely moves beyond its weekday pattern; a regular customer base is one explanation (hypothesis).

**Published benchmarks** (`src/benchmarks.py`, `data/external/benchmarks.csv`, `results/benchmarks_comparison.csv`).
- **Day of week.** We found no published source with a Tuesday peak. Among the reference shops, the vending machine's busiest weekday is Tuesday (1.08×), far below Stories' 1.53×.
- **Costs.** Coffee-drink costs are 28.8% of coffee sales at Harbour, 30.2% at Uptown and 43.2% at Garden. Food costs are 39.6%, 42.1% and 59.9%. Harbour and Uptown sit somewhat above the targets, which may reflect import costs in Lebanon. Garden is far outside every benchmark.
- **Growth.** No price changed in six months while Lebanon's consumer prices rose about 17% a year, so the growth is volume, not price. Stories prices in US dollars, while the inflation rate is measured on Lebanese pounds.
- **Weather sources.** These are industry and trade analyses; we found no peer-reviewed café study.

**Real shop datasets** (`src/reference_compare.py`, `results/reference_*.csv`, `figures/reference_signatures.png`). The French bakery and the vending machine claim to be real. Maven describes itself as a fictitious three-store New York coffee shop.
- **Other signatures.**

  | Signature | Stories | French bakery | Vending machine | Maven (fictitious) |
  |---|---|---|---|---|
  | Busiest day (ratio to Mon, Wed, Thu, Fri average) | Tue (1.53) | Sun (1.34) | Tue (1.08) | Fri (1.01) |
  | Peak hour | 21:00 | 11:00 | 10:00 | 10:00 |
  | Items per transaction | 1.59 | 2.67 | 1.00 | 1.44 |
  | Top-3 category share of items | 52% | 48% | 60% | 85% |

  A late peak may be local habit, so on its own it proves nothing. Basket size and category spread look normal.
- **Bakery effect transfer.** We assume Paris, because the dataset names no city, and fit log(daily transactions) on weekday, trend, temperature, rain day and holiday. Without month effects, the bakery's temperature effect is +3.2% per °C [+2.9, +3.6], but that mixes in its summer season. The within-month value in the summary table is the fair comparison. The French holiday effect need not apply in Beirut: the test shows only that effects of this size would be visible in our data.
- **No sign of being derived from a public template.** Our data shares only the framing of the public Maven dataset: January 1 to June 30, three stores and nine categories. Almost everything else differs:
  - only 3 of our 45 product names appear in Maven (Almond Croissant, Cappuccino, Chocolate Croissant);
  - a median price of $5.41 against $3.00;
  - 1.51 lines per transaction against 1;
  - 62 transactions per store per day against 275;
  - an hourly profile running opposite to Maven's, with a correlation of −0.58;
  - no Tuesday peak in Maven.

