Measured on 2026-09-27T06:30:43+00:00: 7 repeats per case, seed 42. The row-wise `apply` case uses a smaller input because it is orders of magnitude slower.

Environment: Python 3.13.13 on macOS-26.6.2-arm64-arm-64bit-Mach-O (arm64, 10 logical CPUs); pandas 3.0.6, numpy 2.5.3, scipy 1.18.1, pyarrow 25.0.1, openpyxl 3.1.5, pandasplayground 2.0.0

| Case | Rows | Baseline (median ± IQR) | Optimised (median ± IQR) | Speed-up (median) | Speed-up range |
| --- | ---: | --- | --- | --- | --- |
| Sum of sales grouped by two low-cardinality keys: object dtype vs category dtype. | 100,000 | object keys: 5.01 ms ± 401.5 µs | category keys: 1.90 ms ± 197.7 µs | **2.6x** | 1.9x to 3.5x |
| Net revenue sales*quantity*(1-discount): row-wise DataFrame.apply vs vectorised arithmetic. | 20,000 | apply(axis=1): 66.46 ms ± 6.14 ms | vectorised: 111.9 µs ± 6.6 µs | **594.0x** | 345.8x to 727.3x |
| str.lower().str.contains('product 1'): NumPy object strings vs PyArrow-backed strings. | 100,000 | object: 15.88 ms ± 1.71 ms | string[pyarrow]: 3.62 ms ± 134.2 µs | **4.4x** | 3.1x to 5.3x |
| Filter rows in 3 regions: chained == comparisons with \| vs Series.isin. | 100,000 | chained \|: 11.72 ms ± 620.2 µs | isin: 4.99 ms ± 379.0 µs | **2.3x** | 1.9x to 2.7x |
| Read the full frame from disk: CSV vs Parquet (pyarrow). | 100,000 | read_csv: 45.09 ms ± 5.56 ms | read_parquet: 4.39 ms ± 945.9 µs | **10.3x** | 5.7x to 12.9x |

Memory: `optimize_dataframe(auto_category_threshold=0.5, float_rtol=1e-6)` reduced the benchmark frame from 18.72 MiB to 1.24 MiB (**93.4%** smaller) with dtype changes: `region` object->category, `segment` object->category, `product` object->category, `sales` float64->float32, `quantity` int64->int8, `discount` float64->float32.
