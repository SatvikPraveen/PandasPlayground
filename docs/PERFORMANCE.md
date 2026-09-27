# Performance guide

This guide explains the pandas performance techniques demonstrated in the project and how to measure them.
Every number it cites comes from the benchmark harness. **Measured results live in
[benchmark_results.md](benchmark_results.md)**, and raw samples with full environment details live in
[`benchmarks/results/latest.json`](../benchmarks/results/latest.json).

> Earlier versions of this page quoted figures such as "73% memory reduction" and "65% faster
> groupby" that no script could reproduce. They have been removed. Treat any number you cannot
> regenerate with the commands below as unverified.

## Reproducing the measurements

```bash
pandasplayground benchmark --rows 100000 --repeat 7 --markdown docs/benchmark_results.md
# or
make benchmark
```

Methodology (calibrated `timeit` loops, medians with IQR, recorded environment) is described in
[METHODOLOGY.md, section 4](METHODOLOGY.md#4-benchmarking). Timings depend on hardware and library
versions. Compare them within one machine and one run.

## Techniques and what the benchmark shows

| Technique | Why it helps | Benchmark case |
| --- | --- | --- |
| Vectorise instead of `DataFrame.apply(axis=1)` | Row-wise `apply` calls a Python function per row. Column arithmetic runs in compiled loops. | `vectorized_vs_apply` |
| Parquet instead of CSV for intermediate data | Columnar, typed and compressed. No text parsing or dtype inference on read. | `read_csv_vs_parquet` |
| PyArrow-backed strings | Arrow string kernels avoid per-element Python objects. pandas 3 uses them by default for `str`. | `string_ops_pyarrow` |
| `category` dtype for low-cardinality keys | Grouping works on small integer codes instead of hashing strings. | `groupby_category_keys` |
| `Series.isin` instead of chained `==` / `\|` | One hash-set lookup pass instead of several full comparisons plus boolean combination. | `isin_vs_chained_or` |
| Downcast numerics and categorise text | Smaller dtypes reduce memory and cache pressure. | Memory line of the results |

### Memory

```python
from pandasplayground.memory import optimize_dataframe

optimized, report = optimize_dataframe(df, auto_category_threshold=0.5, return_report=True)
print(f"{report.reduction:.1%} smaller", report.dtype_changes)
```

Integer downcasting is always exact. Float64 is converted to float32 only when every value round-trips
exactly, unless you opt in with a tolerance such as `float_rtol=1e-6`. Values like `1292.63` are not
exactly representable in float32, so the default leaves such columns as float64.

### Other techniques covered in the notebooks

These are demonstrated in `notebooks/06_advanced_pandas.ipynb` and `notebooks/10_performance_diagnostics.ipynb`.
The benchmark suite does not measure them yet.

- **Chunked reading** with `pd.read_csv(..., chunksize=n)` bounds peak memory for files larger than RAM.
- **`DataFrame.eval` / `query`** can help for long arithmetic expressions on large frames through numexpr.
  For small frames the parsing overhead dominates.
- **Avoid chained indexing** (`df[mask]["col"] = x`). Use `df.loc[mask, "col"] = x`. With pandas 3
  Copy-on-Write, chained assignment never modifies the original.
- **Dask** parallelises pandas-style operations across cores or machines when data exceeds memory.

## Profiling your own code

```python
# Deep memory usage per column
df.memory_usage(deep=True)

# Time an expression in IPython or Jupyter
%timeit df.groupby("region")["sales"].sum()

# Line-by-line memory (pip install memory_profiler)
%load_ext memory_profiler
%memit df.groupby("region")["sales"].sum()
```

To add a benchmark case, write a function in `src/pandasplayground/benchmark.py` that returns a
`Comparison` of a baseline and an optimised `Timing`, and add it to `run_suite`.
