# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [2.0.0] - 2026-09-27

### Added
- `pandasplayground` package (src layout, fully typed) with modules for I/O, cleaning, aggregation,
  merging, memory optimisation, validation, statistics, provenance, benchmarking, data generation and the pipeline.
- `pandasplayground` command-line interface: `validate`, `pipeline`, `generate`, `benchmark`, `docs`, `info`.
- Declarative schema validation, with schemas for every bundled dataset. The data dictionary is generated from them.
- Deterministic pipeline that rebuilds the final export from raw data and writes a provenance manifest.
- Statistics module: BCa bootstrap, Wilson and Fisher-z intervals, permutation and Welch tests,
  chi-square with Cramér's V, Kruskal-Wallis, FDR and FWER correction, differenced correlation.
- Seeded data generator that reproduces the bundled data bit-for-bit (except unseeded Faker names).
- Benchmark harness with calibrated timing, medians and IQRs, and environment capture. Results are committed.
- Notebook 11 on statistical inference and reproducibility.
- Dashboard pages for statistical inference and live data quality. KPIs now follow the selected month range.
- `pipeline.days_observed` and per-day-rate correlations in the dashboard.
- Test suite of 128 tests: unit, Hypothesis property, golden-file regression, notebook execution and dashboard smoke tests.
- CI across Python 3.10 to 3.13, pandas 2.2 and 3.x, and Linux, macOS and Windows, with reproducibility and drift checks.
- `docs/METHODOLOGY.md`, `docs/DATA_CARD.md`, `CITATION.cff`, Dependabot.

### Changed
- `scripts/` is now a compatibility layer over the package, so notebooks run unchanged.
- Tooling consolidated in `pyproject.toml`. Ruff replaces black, isort and flake8. Python 3.10+ is required.
- Dockerfile runs as a non-root user without a hard-coded empty Jupyter token.
- `docs/PERFORMANCE.md` rewritten around measured, reproducible results.

### Fixed
- Monthly sales and COVID totals correlated only through calendar length (r ≈ 0.26). The confound is now documented,
  and the dashboard and notebook 11 report per-day rates.
- CSV reads used pandas' fast float parser, which does not round-trip exactly and differs across CPUs. Re-exported
  reports drifted between macOS and Linux. Reads now use exact parsing.
- The validator stopped checking a column after a dtype mismatch, hiding nulls and range violations.
- Notebook 03 double-counted every loan on re-runs because a glob also matched a combined output file.
- `clean_dataframe` converted missing values into the literal string `"nan"`.
- `optimize_dataframe` silently rounded floats when downcasting to float32. It is now exact by default.
- `align_customer_ids` failed on integer IDs under pandas 3.
- Helpers mutated their input DataFrames (`resample_monthly`, `safe_merge`).
- `resample_monthly` and `safe_merge` were each defined twice, and the second silently replaced the first.
- The deprecated `"M"` resample alias was replaced with `"ME"`.
- `pytest.ini` used a `[tool:pytest]` header, so its settings were silently ignored.
- The data dictionary described columns that do not exist.
- Missing `plotly` dependency for the dashboard.

### Removed
- `docs/PROJECT_COMPLETION_SUMMARY.md` and `assets/PROJECT_PREVIEW_PLACEHOLDER.md` (stale status notes).
- Unreproducible benchmark figures from the README and performance guide.

## [1.0.0] - 2025-07-27

- Initial release: ten notebooks, helper scripts, synthetic datasets and a Streamlit dashboard.
