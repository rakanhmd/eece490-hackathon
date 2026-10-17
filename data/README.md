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
| Revenue formula | Line Revenue = Quantity × Unit Price × (1 − Discount Rate) holds on every row within rounding (±$0.01) |
| Profit formula | Line Gross Profit = Line Revenue − Quantity × Unit Cost holds on every row; no negative values |
| Quantity / prices | No zero or negative values; quantity is 1 or 2 |
| Customer IDs across branches | 94% of known customers bought at more than one branch. We read this as regulars using several branches; anonymized IDs are assumed to be consistent |

## External data (`data/external/`, committed)
Downloaded or compiled on **2026-10-17** for `src/external_factors.py`. **Assumption:** Stories is a Lebanese chain and branch addresses are not in the data, so all three branches are treated as being in Greater Beirut (lat 33.89, lon 35.50). Weather and calendar are therefore the same for every branch.

| File | What | Source |
|---|---|---|
| `weather_beirut_2026H1.csv` | Daily max temperature (°C) and precipitation (mm), 2026-01-01 to 2026-06-30, timezone Asia/Beirut. Open-Meteo snaps to the nearest grid cell, 33.85 N 35.53 E. | Open-Meteo historical weather API: `https://archive-api.open-meteo.com/v1/archive?latitude=33.89&longitude=35.50&start_date=2026-01-01&end_date=2026-06-30&daily=temperature_2m_max,precipitation_sum&timezone=Asia%2FBeirut&format=csv` |
| `DCOILBRENTEU.csv` | Daily Brent crude oil price (USD per barrel), full FRED history; used by `src/garden_cost_cause.py` (see GARDEN_CAUSE.md) | FRED series DCOILBRENTEU: `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU` |
| `coffee_price_arabica_fred.csv` | Monthly world price of arabica coffee (US cents per pound), Jul 2025 to Jul 2026 | IMF series via FRED, PCOFFOTMUSDM: `https://fred.stlouisfed.org/graph/fredgraph.csv?id=PCOFFOTMUSDM&cosd=2025-07-01&coed=2026-09-01` |
| `lebanon_calendar_2026H1.csv` | Public holidays, Ramadan, school closures, AUB calendar and the security escalation, compiled by hand from the sources below | see below |

Sources for the calendar. Some news pages blocked automated download. For those, marked "via search summary", we used the dates as reported in web search results and could not read the page ourselves.
- **Public holidays:** [holidaydb.com, Lebanon 2026](https://holidaydb.com/guides/public-holidays/lebanon/2026) and [calendarlabs.com, Lebanon 2026](https://www.calendarlabs.com/holidays/lebanon/2026).
  - The two sites agree except on a few dates. Eid holiday lengths differ, and so do the Islamic New Year (Jun 16 or 17) and Ashoura (Jun 25 or 26), so both possible days are included.
  - Calendarlabs swaps the Western and Orthodox Easter labels. In 2026 Western Easter was April 5 and Orthodox Easter April 12.
  - The official [Banque du Liban holiday list](https://bdl.gov.lb/bankingholidays.php) blocked automated access.
- **Ramadan, Feb 18 to Mar 19:** L'Orient Today, [Ramadan to begin Feb 18](https://today.lorientlejour.com/article/1495201/first-day-of-ramadan-will-fall-on-feb-18-shiite-cleric-fadlallah.html) and [Higher Islamic Shiite Council: Feb 19](https://today.lorientlejour.com/article/1495346/higher-islamic-shiite-council-says-ramadan-will-begin-on-thursday-feb-19.html), via search summary.
- **Security escalation from Mar 2:** [Al-Monitor, April 2026](https://www.al-monitor.com/originals/2026/04/israel-strikes-beirut-us-warns-iran-may-hit-lebanese-universities), via search summary.
- **School closures:**
  - [LBC, 2026-03-03](https://v7cdn.lbcgroup.tv/news/lebanon-news/909926/lebanese-ministry-of-education-announces-closure-of-public-schools-adv/en): public schools closed that week, sheltering displaced families.
  - [L'Orient Today, schools may restart Mar 10](https://today.lorientlejour.com/article/1498259/karameh-lets-schools-decide-between-remote-and-in-person-classes.html), via search summary.
  - [LBC, 2026-03-17](https://v7cdn.lbcgroup.tv/news/lebanon-news/915562/lebanon-closes-schools-for-eid-al-fitr-holiday-through-march-23/en): Eid closure through Mar 23.
  - [LBC, 2026-03-27](https://v7cdn.lbcgroup.tv/news/lebanon-news/918939/lebanon-announces-school-closures-for-catholic-and-orthodox-easter-hol/en): Easter closures Apr 2–6 and Apr 9–13.
- **End of school year:** no official 2025–26 date was found. We **assume** schools were out from June 15.
- **AUB:**
  - [Jordan Times](https://jordantimes.com/news/region/american-university-of-beirut-moves-to-online-learning-after-iran-threats): fully online Mar 30–31.
  - [AUB Provost message, 2026-04-07](https://www.aub.edu.lb/Registrar/Documents/announcements/provostmessage-students-semester-remainder-planning.pdf): classes synchronously online until further notice, last class May 4, reading period May 5–7, finals May 8–17, commencement Jun 5–6.

### Benchmarks (`data/external/benchmarks.csv`, compiled 2026-10-17)
Published figures used only as context in `src/benchmarks.py`. Each row of the CSV holds its value, unit, period, scope, source and URL. Numbers we could not trace to a page we read are left out. These include the BizBuySell café margins (access blocked), a Restaurant Warehouse page (no cost figure on it) and a third-party report of a Starbucks Tuesday record that we could not confirm.
- [Placer.ai, "Starbucks and Dunkin' 2023 in four data points" (2024-01-29)](https://placer.ai/blog/starbucks-and-dunkin-2023-in-four-data-points): Starbucks tends to be busiest on Saturdays.
- [Restaurant Online, 2026-06-11, citing Square UK transaction data](https://www.restaurantonline.co.uk/Article/2026/06/11/not-joe-friday-saturday-is-the-biggest-day-for-coffee-consumption-data-reveals/): Saturday has 49% more cups sold than the average weekday.
- [Starbucks Form 10-K, fiscal 2025 (SEC)](https://www.sec.gov/Archives/edgar/data/829224/000082922425000114/sbux-20250928.htm): product and distribution costs were $11,658.2m, 31.4% of total net revenues of $37,184.4m. We read this line directly from the filing.
- [Zest Specialty Coffee, "6 key benchmarks every café owner in Australia should know" (2025-10-01)](https://www.zestcoffee.com.au/blogs/news/6-key-benchmarks-every-cafe-owner-in-australia-should-know): target coffee costs of 20–25% of coffee sales and food costs of 25–35% of food sales.
- [BLOMINVEST Bank, 2026-07-28, citing the Central Administration of Statistics](https://blog.blominvestbank.com/lebanons-inflation-rate-increased-by-17-25-yoy-by-june-2026/): Lebanon CPI +17.25% year on year in June 2026, and +19.04% in May.
- [QSR Web, "The Weather Effect report" (2019-07-12), Foursquare and AccuWeather](https://www.qsrweb.com/news/the-weather-effect-report-tracks-weather-trends-related-to-dining-traffic): an industry report, not peer-reviewed.
- [United Baristas, 2026-07-08](https://unitedbaristas.com/articles/explainers/cold-coffee-demand-is-more-predictable-than-the-british-weather/): cold coffee share rose 2.2 points per 1 °C at one London café. This is a trade analysis, not peer-reviewed.

### Reference shop datasets (`data/external/reference/`, gitignored; downloaded 2026-10-17)
Used by `src/reference_compare.py` as a picture of what shop data looks like. They are not a cause of anything in our data. The raw files are not committed. Download them with:
```bash
cd data/external/reference
kaggle datasets download -d ahmedabbas757/coffee-sales -p ahmedabbas757_coffee-sales --unzip
kaggle datasets download -d matthieugimbert/french-bakery-daily-sales -p matthieugimbert_french-bakery-daily-sales --unzip
kaggle datasets download -d ihelon/coffee-sales -p ihelon_coffee-sales --unzip
```

| Dataset | URL | License (Kaggle) | Real or fictional, per its own description |
|---|---|---|---|
| Coffee Shop Sales (Maven Roasters; 3 NYC stores, 2023-01-01 to 2023-06-30) | https://www.kaggle.com/datasets/ahmedabbas757/coffee-sales | GNU LGPL 3.0 | **Fictional**: "Transaction records for Maven Roasters, a fictitious coffee shop operating out of three NYC locations". The upload says the data is from Maven Analytics |
| French bakery daily sales (2021-01-02 to 2022-09-30) | https://www.kaggle.com/datasets/matthieugimbert/french-bakery-daily-sales | copyright-authors | **Claims real**: "The dataset belongs to a French bakery". No city is given; we **assume Paris** for weather and holidays |
| Coffee Sales (one vending machine, 2024-03-01 to 2025-03-23 in our download; file `index_1.csv`) | https://www.kaggle.com/datasets/ihelon/coffee-sales | CC0-1.0 | **Claims real**: "coffee sales from a vending machine", run by the dataset author. No location is given in the description, and the file is used for its signatures only |

Extra files committed in `data/external/` for the bakery test:
- `weather_paris_2021_2022.csv`: Open-Meteo archive, daily max temperature and precipitation, 2021-01-01 to 2022-09-30, Europe/Paris. Open-Meteo snaps to the nearest grid cell, 48.89 N 2.29 E. URL: `https://archive-api.open-meteo.com/v1/archive?latitude=48.86&longitude=2.35&start_date=2021-01-01&end_date=2022-09-30&daily=temperature_2m_max,precipitation_sum&timezone=Europe%2FParis&format=csv`
- `france_holidays_2021_2022.csv`: French public holidays for metropolitan France, from the official government API at `https://calendrier.api.gouv.fr/jours-feries/metropole/2021.json` and `.../2022.json`.
