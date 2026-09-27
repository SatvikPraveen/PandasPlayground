# Methodology

This document describes how PandasPlayground makes its results **reproducible**, **validated**,
**statistically honest** and **measurable**. Each section names the module that implements it.

## 1. Reproducibility

**Single source of randomness.** Every stochastic component takes an explicit seed that defaults to `42`
(`pandasplayground.config.DEFAULT_SEED`). This covers data generation, bootstrap resampling,
permutation tests and benchmark inputs. Resampling routines use independent `numpy.random.Generator`
instances, so results do not depend on call order.

**Deterministic pipeline.** `pandasplayground pipeline` (module `pipeline`) rebuilds
`exports/final_merged_pipeline.csv` from the raw files in `data/`. It is a pure function of its
inputs and parameters:

1. Load `superstore_sales.csv` and `covid_data.parquet`, and validate both against their schemas.
2. Normalise column names to `snake_case` and aggregate each source to calendar months (`YYYY-MM`).
3. Inner-join on `month` with `validate="one_to_one"`, so a duplicated month raises instead of silently multiplying rows.
4. Sort chronologically, then add `rolling_profit` (trailing 3-month mean) and `sales_pct_change`.
5. Validate the output schema, write the CSV, and write a provenance manifest.

**Provenance manifests** (module `provenance`). Each run writes `<output>.manifest.json` containing:

- the SHA-256 hash and row count of each input and output file;
- a content fingerprint of each DataFrame, from `pandas.util.hash_pandas_object` plus column names and
  dtypes, which does not depend on how the file was serialised;
- the parameters, validation outcomes, Python and library versions, platform, and git commit with a
  dirty-tree flag.

**Continuous verification.** On every push, CI:

- re-runs the pipeline and fails unless the export is byte-identical to the committed file;
- regenerates the synthetic data from the seed and validates it;
- executes all notebooks and fails if any CSV they write changes;
- runs the test suite on Python 3.10 to 3.13, pandas 2.2 and 3.x, and Linux, macOS and Windows.

This process has already caught a real defect. Notebook 03 gathered regional files with a glob that also
matched a combined file written by notebook 04, so every re-run double-counted loans.

## 2. Data validation

Module `validation` implements a small declarative schema language. A column contract covers:

- logical dtype and nullability;
- uniqueness and numeric or date ranges;
- allowed values and regular-expression patterns.

Table contracts add strictness (no unexpected columns), a minimum row count, composite uniqueness and
arbitrary row-level checks. Validation collects every failure rather than stopping at the first.
Each failure carries a count and example values.

The same schema objects produce the [data dictionary](DATA_DICTIONARY.md). A test fails if the
committed dictionary differs from what the schemas render, so documentation cannot drift from the
enforced contract.

## 3. Statistical inference

Module `stats` follows current reporting recommendations (Wasserstein & Lazar, 2016): report the
**magnitude** of an effect and the **uncertainty** around it, not only a p-value.

| Need | Method | Notes |
| --- | --- | --- |
| Interval for any statistic | Bootstrap, BCa by default | Efron (1987). BCa corrects bias and skewness. The percentile and basic intervals are also available. |
| Interval for a mean | Student-t | Exact under normality. |
| Interval for a proportion | Wilson score | Good coverage near 0 and 1, unlike the Wald interval (Newcombe, 1998). |
| Interval for a correlation | Fisher z-transform | Pearson or Spearman, on pairwise-complete data. |
| Two-sample location | Permutation test on the mean difference, or Welch's t | The permutation test makes no distributional assumption. Both report Hedges' g. |
| Several groups | Kruskal-Wallis | Reports epsilon-squared (Tomczak & Tomczak, 2014). |
| Categorical association | Pearson chi-square | Reports bias-corrected Cramér's V (Bergsma, 2013) and the minimum expected count. |
| Many tests at once | Benjamini-Hochberg or Benjamini-Yekutieli FDR, Holm, Bonferroni | Correct before interpreting. |
| Two time series | Correlation of first differences | Trending series correlate spuriously (Granger & Newbold, 1974). |

The tests check these methods against published reference values, such as Newcombe's Wilson
interval example. A slow test simulates bootstrap intervals and checks that their empirical coverage is near the nominal level.

## 4. Benchmarking

Module `benchmark` compares a baseline idiom with an optimised idiom for the same task.

- Loop counts are calibrated with `timeit.Timer.autorange` so each sample lasts at least about 0.2 s.
  The suite then draws `repeat` independent samples, 7 by default.
- Results report the **median** and **interquartile range**, which resist scheduler noise, plus the best
  sample. Speed-up is the ratio of medians, and its range comes from the extreme samples.
- Inputs are generated from a fixed seed. Each run records the machine, OS, library versions and git commit.
- Results are written as JSON to `benchmarks/results/` and as a Markdown table to
  [benchmark_results.md](benchmark_results.md).

Timings depend on hardware and library versions. Read them as relative comparisons on one machine.

## 5. Memory optimisation

`memory.optimize_dataframe` downcasts integers exactly. It converts float64 to float32 only when every
value survives the round trip, unless the caller passes a tolerance with `float_rtol`. It converts
text columns to `category` when asked explicitly, or when their unique-value ratio falls below a
threshold. It returns a `MemoryReport` listing every dtype change.

## 6. Software quality

- The package is fully annotated and type-checked by mypy with `disallow_untyped_defs`, and linted with ruff.
- Tests cover more than 90% of branches, and CI enforces at least 85%.
- Hypothesis property tests check invariants such as idempotent string normalisation, preserved
  missing values and exact integer downcasting.

## References

- Bergsma, W. (2013). A bias-correction for Cramér's V and Tschuprow's T. *Journal of the Korean Statistical Society*, 42(3), 323–328.
- Efron, B. (1987). Better bootstrap confidence intervals. *Journal of the American Statistical Association*, 82(397), 171–185.
- Gebru, T., et al. (2021). Datasheets for datasets. *Communications of the ACM*, 64(12), 86–92.
- Granger, C. W. J., & Newbold, P. (1974). Spurious regressions in econometrics. *Journal of Econometrics*, 2(2), 111–120.
- Iglewicz, B., & Hoaglin, D. C. (1993). *How to Detect and Handle Outliers*. ASQC Quality Press.
- Newcombe, R. G. (1998). Two-sided confidence intervals for the single proportion. *Statistics in Medicine*, 17(8), 857–872.
- Tomczak, M., & Tomczak, E. (2014). The need to report effect size estimates revisited. *Trends in Sport Sciences*, 1(21), 19–25.
- Wasserstein, R. L., & Lazar, N. A. (2016). The ASA statement on p-values. *The American Statistician*, 70(2), 129–133.
- Wickham, H. (2014). Tidy data. *Journal of Statistical Software*, 59(10), 1–23.
