"""Repeatable micro-benchmarks for common pandas idioms.

Methodology:

* Each case is timed with :class:`timeit.Timer`: the loop count is calibrated with ``autorange`` so a
  single sample lasts at least ~0.2 s, then ``repeat`` independent samples are drawn.
* We report the **median** per-call time and the **interquartile range** (robust to scheduler noise),
  plus the minimum. Speed-ups are ratios of medians, with a range from the fastest/slowest samples.
* Inputs are generated from a fixed seed; the environment (CPU, OS, library versions, git SHA) is
  recorded with every result so numbers are never quoted without their context.

Timings are hardware-dependent. Treat them as relative comparisons on one machine, not absolutes.
"""

from __future__ import annotations

import datetime as dt
import gc
import json
import tempfile
import timeit
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from pandasplayground.config import DEFAULT_SEED
from pandasplayground.memory import memory_bytes, optimize_dataframe
from pandasplayground.provenance import environment_info, git_state


@dataclass(frozen=True)
class Timing:
    name: str
    samples: tuple[float, ...]  # seconds per call, one entry per repeat
    loops: int

    @property
    def median(self) -> float:
        return float(np.median(self.samples))

    @property
    def iqr(self) -> float:
        q1, q3 = np.percentile(self.samples, [25, 75])
        return float(q3 - q1)

    @property
    def best(self) -> float:
        return float(min(self.samples))


@dataclass(frozen=True)
class Comparison:
    """A baseline idiom vs an optimised idiom solving the same task."""

    case: str
    description: str
    n_rows: int
    baseline: Timing
    optimized: Timing

    @property
    def speedup(self) -> float:
        return self.baseline.median / self.optimized.median

    @property
    def speedup_range(self) -> tuple[float, float]:
        return (
            min(self.baseline.samples) / max(self.optimized.samples),
            max(self.baseline.samples) / min(self.optimized.samples),
        )

    def as_dict(self) -> dict[str, Any]:
        def timing(t: Timing) -> dict[str, Any]:
            return {
                "name": t.name,
                "median_s": t.median,
                "iqr_s": t.iqr,
                "best_s": t.best,
                "loops": t.loops,
                "samples_s": list(t.samples),
            }

        return {
            "case": self.case,
            "description": self.description,
            "n_rows": self.n_rows,
            "baseline": timing(self.baseline),
            "optimized": timing(self.optimized),
            "speedup_median": self.speedup,
            "speedup_range": list(self.speedup_range),
        }


def time_callable(name: str, fn: Callable[[], object], repeat: int = 7, min_time: float = 0.2) -> Timing:
    """Time ``fn`` with calibrated loop counts; returns per-call seconds for each repeat."""
    timer = timeit.Timer(fn)
    loops, _ = timer.autorange()
    loops = max(1, int(np.ceil(loops * min_time / 0.2)))
    gc.collect()
    raw = timer.repeat(repeat=repeat, number=loops)
    return Timing(name, tuple(t / loops for t in raw), loops)


def make_frame(n_rows: int, seed: int = DEFAULT_SEED) -> pd.DataFrame:
    """Deterministic benchmark input resembling the superstore data."""
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "region": rng.choice(["East", "West", "Central", "South"], n_rows),
            "segment": rng.choice(["Consumer", "Corporate", "Home Office"], n_rows),
            "product": rng.choice([f"Product {i:03d}" for i in range(200)], n_rows),
            "sales": rng.uniform(10, 2000, n_rows).round(2),
            "quantity": rng.integers(1, 10, n_rows),
            "discount": rng.choice([0.0, 0.1, 0.2, 0.3, 0.5], n_rows),
        }
    ).astype({"region": object, "segment": object, "product": object})


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------


def _case_groupby_category(df: pd.DataFrame, repeat: int) -> Comparison:
    cat = df.astype({"region": "category", "segment": "category"})
    return Comparison(
        "groupby_category_keys",
        "Sum of sales grouped by two low-cardinality keys: object dtype vs category dtype.",
        len(df),
        time_callable("object keys", lambda: df.groupby(["region", "segment"])["sales"].sum(), repeat),
        time_callable(
            "category keys", lambda: cat.groupby(["region", "segment"], observed=True)["sales"].sum(), repeat
        ),
    )


def _case_vectorize_apply(df: pd.DataFrame, repeat: int) -> Comparison:
    return Comparison(
        "vectorized_vs_apply",
        "Net revenue sales*quantity*(1-discount): row-wise DataFrame.apply vs vectorised arithmetic.",
        len(df),
        time_callable(
            "apply(axis=1)",
            lambda: df.apply(lambda r: r["sales"] * r["quantity"] * (1 - r["discount"]), axis=1),
            repeat,
        ),
        time_callable("vectorised", lambda: df["sales"] * df["quantity"] * (1 - df["discount"]), repeat),
    )


def _case_string_dtype(df: pd.DataFrame, repeat: int) -> Comparison:
    obj = df["product"].astype(object)
    arrow = df["product"].astype("string[pyarrow]")
    return Comparison(
        "string_ops_pyarrow",
        "str.lower().str.contains('product 1'): NumPy object strings vs PyArrow-backed strings.",
        len(df),
        time_callable("object", lambda: obj.str.lower().str.contains("product 1", regex=False), repeat),
        time_callable("string[pyarrow]", lambda: arrow.str.lower().str.contains("product 1", regex=False), repeat),
    )


def _case_isin_vs_or(df: pd.DataFrame, repeat: int) -> Comparison:
    return Comparison(
        "isin_vs_chained_or",
        "Filter rows in 3 regions: chained == comparisons with | vs Series.isin.",
        len(df),
        time_callable(
            "chained |",
            lambda: df[(df["region"] == "East") | (df["region"] == "West") | (df["region"] == "South")],
            repeat,
        ),
        time_callable("isin", lambda: df[df["region"].isin(["East", "West", "South"])], repeat),
    )


def _case_io_formats(df: pd.DataFrame, repeat: int, workdir: Path) -> Comparison:
    csv_path, pq_path = workdir / "bench.csv", workdir / "bench.parquet"
    df.to_csv(csv_path, index=False)
    df.to_parquet(pq_path, index=False)
    return Comparison(
        "read_csv_vs_parquet",
        "Read the full frame from disk: CSV vs Parquet (pyarrow).",
        len(df),
        time_callable("read_csv", lambda: pd.read_csv(csv_path), repeat),
        time_callable("read_parquet", lambda: pd.read_parquet(pq_path), repeat),
    )


@dataclass
class BenchmarkRun:
    n_rows: int
    repeat: int
    seed: int
    comparisons: list[Comparison]
    memory: dict[str, Any]
    environment: dict[str, Any] = field(default_factory=environment_info)
    git: dict[str, Any] = field(default_factory=git_state)
    timestamp: str = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_rows": self.n_rows,
            "repeat": self.repeat,
            "seed": self.seed,
            "timestamp": self.timestamp,
            "environment": self.environment,
            "git": self.git,
            "memory": self.memory,
            "comparisons": [c.as_dict() for c in self.comparisons],
        }

    def write_json(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n")
        return path

    def to_markdown(self) -> str:
        env = self.environment
        lines = [
            f"Measured on {self.timestamp} with {self.n_rows:,} rows, "
            f"{self.repeat} repeats per case (seed {self.seed}).",
            "",
            f"Environment: Python {env['python']} on {env['platform']} "
            f"({env['machine']}, {env['cpu_count']} logical CPUs); "
            + ", ".join(f"{k} {v}" for k, v in env["packages"].items() if v),
            "",
            "| Case | Baseline (median ± IQR) | Optimised (median ± IQR) | Speed-up (median) | Speed-up range |",
            "| --- | --- | --- | --- | --- |",
        ]
        for c in self.comparisons:
            lo, hi = c.speedup_range
            base, opt = _md(c.baseline.name), _md(c.optimized.name)
            lines.append(
                f"| {_md(c.description)} | {base}: {_fmt(c.baseline.median)} ± {_fmt(c.baseline.iqr)} "
                f"| {opt}: {_fmt(c.optimized.median)} ± {_fmt(c.optimized.iqr)} "
                f"| **{c.speedup:.1f}x** | {lo:.1f}x to {hi:.1f}x |"
            )
        m = self.memory
        lines += [
            "",
            "Memory: `optimize_dataframe(auto_category_threshold=0.5, float_rtol=1e-6)` reduced the benchmark frame "
            f"from {m['before_bytes'] / 2**20:.2f} MiB to "
            f"{m['after_bytes'] / 2**20:.2f} MiB (**{m['reduction'] * 100:.1f}%** smaller) with dtype changes: "
            + ", ".join(f"`{k}` {a}->{b}" for k, (a, b) in m["dtype_changes"].items())
            + ".",
        ]
        return "\n".join(lines)


def _md(text: str) -> str:
    """Escape characters that would break a Markdown table cell."""
    return text.replace("|", "\\|")


def _fmt(seconds: float) -> str:
    if seconds >= 1:
        return f"{seconds:.2f} s"
    if seconds >= 1e-3:
        return f"{seconds * 1e3:.2f} ms"
    return f"{seconds * 1e6:.1f} µs"


def run_suite(
    n_rows: int = 100_000, repeat: int = 7, seed: int = DEFAULT_SEED, apply_rows: int | None = 20_000
) -> BenchmarkRun:
    """Run every case. ``apply_rows`` caps the (very slow) row-wise ``apply`` case's input size."""
    df = make_frame(n_rows, seed)
    comparisons = [
        _case_groupby_category(df, repeat),
        _case_vectorize_apply(df.head(apply_rows) if apply_rows else df, repeat),
        _case_string_dtype(df, repeat),
        _case_isin_vs_or(df, repeat),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        comparisons.append(_case_io_formats(df, repeat, Path(tmp)))

    optimized, report = optimize_dataframe(df, auto_category_threshold=0.5, float_rtol=1e-6, return_report=True)
    assert memory_bytes(optimized) == report.after_bytes
    memory = {
        "before_bytes": report.before_bytes,
        "after_bytes": report.after_bytes,
        "reduction": report.reduction,
        "dtype_changes": report.dtype_changes,
    }
    return BenchmarkRun(n_rows, repeat, seed, comparisons, memory)
