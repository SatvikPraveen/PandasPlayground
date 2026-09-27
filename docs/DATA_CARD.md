# Data Card: PandasPlayground synthetic datasets

This card follows the structure of *Datasheets for Datasets* (Gebru et al., 2021). Column-level
contracts live in the generated [data dictionary](DATA_DICTIONARY.md).

## Motivation

The datasets exist to exercise pandas across file formats (CSV, Excel, multi-sheet Excel, JSON,
Parquet) and across common tasks: cleaning, reshaping, joining, resampling and aggregation.
They are **teaching and testing fixtures**, not observations of any real process.

## Composition

| File | Format | Rows | Unit of observation |
| --- | --- | --- | --- |
| `data/superstore_sales.csv` | CSV | 10,000 | One retail order |
| `data/bank_loans.xlsx` | Excel | 10,000 | One loan application |
| `data/bank_loans_multisheet.xlsx` | Excel, 4 sheets | 4 × 10,000 | The same applications, one sheet per region label |
| `data/covid_data.parquet` | Parquet | 10,000 | One day |
| `data/weather_data.json` | JSON records | 10,000 | One day |

No record describes a real person. Names are produced by the Faker library.

## Generating process

All files are produced by `pandasplayground.datagen.generate(n_rows=10_000, seed=42)`.
Regenerate them with:

```bash
pandasplayground generate --out runs/generated
```

The generator draws from NumPy's legacy global random stream in a fixed order. It reproduces
every numeric, categorical and date column of the committed files bit-for-bit, and a test
enforces this. The committed person names were produced before Faker was seeded, so they are
the only values that regenerate differently.

Each variable is drawn **independently**:

| Variable | Distribution |
| --- | --- |
| Superstore `Sales` | Uniform(10, 2000), rounded to cents |
| Superstore `Quantity` | Uniform integer 1 to 9 |
| Superstore `Discount` | Uniform over {0, 0.1, 0.2, 0.3, 0.5} |
| Superstore `Profit` | `Sales × (0.05 + 0.05·Z)`, Z ~ N(0, 1) |
| Superstore `Segment`, `Region` | Uniform over categories |
| Superstore `Category`, `Sub-Category`, `Product Name` | Deterministic round-robin over 55 products |
| Loans `Age` | Uniform integer 21 to 64 |
| Loans `Income` | Uniform integer 25,000 to 149,999 |
| Loans `Loan_Amount` | Uniform integer 3,000 to 79,999 |
| Loans `Loan_Purpose`, `Approved` | Uniform over categories |
| COVID `new_cases` | Poisson(500) |
| COVID `new_deaths` | Poisson(10) |
| COVID `hospitalized` | Uniform integer 0 to 4,999 |
| COVID `country`, `variant` | Uniform over categories, one per day |
| Weather `temperature_c` | Uniform integer −10 to 39 |
| Weather `humidity` | Uniform integer 30 to 99 |
| Weather `condition` | Uniform over categories |

## Known artefacts and limitations

These are properties of the generator, not bugs in the analysis. Anyone using the data should know them.

1. **There is no signal to find.** Apart from `Profit` scaling with `Sales`, every variable is
   independent of every other. Approval does not depend on income, age or purpose. Profit does not
   depend on discount. Sales do not depend on COVID cases. Null results are the correct result, and
   any "significant" finding is a false positive or a sign of a flawed method.
2. **Implausibly long daily series.** Each daily file has 10,000 consecutive days, so dates run from
   2020 (or 2022 for weather) to 2047 (or 2049). The monthly panel therefore spans 329 months.
3. **One country per day.** The COVID file is not a country panel. Each day has a single, randomly
   chosen country, so per-country time series are irregular samples.
4. **Constant shipping lag.** `Ship Date` is always `Order Date` plus two days.
5. **Region sheets are copies.** Each sheet of `bank_loans_multisheet.xlsx` is the full loans table
   with a constant `Region` label. Concatenating sheets quadruples every customer, and grouping by
   region yields four identical summaries.
6. **Weather humidity and temperature are integers** drawn uniformly, with no seasonality.
7. **Profit margins are symmetric** around 5% with a 5% standard deviation, so about 16% of orders lose money.
8. **Monthly totals share a calendar-length confound.** The pipeline sums daily values to months, and months
   have 28 to 31 days. The last month is only partly observed, with 18 days. As a result, monthly sales and
   monthly COVID cases correlate (Pearson r ≈ 0.26, 95% CI 0.15 to 0.35) although the daily series are
   independent. Divide by `pandasplayground.pipeline.days_observed` before comparing: the per-day
   correlation's interval spans zero. Notebook 11 walks through this.

## Recommended uses

- Practising pandas mechanics: I/O, dtypes, reshaping, joins, time-based grouping.
- Testing data pipelines, schema validation and memory optimisation.
- Demonstrating statistical pitfalls on data with a known null: spurious correlation between trending
  series, multiple comparisons, and "significance" at large sample sizes.

## Uses to avoid

- Drawing any substantive conclusion about retail, lending, epidemiology or climate.
- Benchmarking predictive models. There is nothing to predict beyond `Profit ≈ 0.05 × Sales`.

## Maintenance

The schemas in `src/pandasplayground/schemas.py` are the contract. CI validates every file on each
push, regenerates the data from the seed, and fails if the pipeline export or any notebook CSV output changes.

## Reference

Gebru, T., Morgenstern, J., Vecchione, B., Vaughan, J. W., Wallach, H., Daumé III, H., & Crawford, K. (2021).
Datasheets for datasets. *Communications of the ACM*, 64(12), 86–92. https://doi.org/10.1145/3458723
