"""Lossless-by-default dtype optimisation with a before/after report."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal, overload

import numpy as np
import pandas as pd

from pandasplayground.cleaning import text_columns

logger = logging.getLogger(__name__)


def memory_bytes(df: pd.DataFrame) -> int:
    """Deep memory usage in bytes (includes Python string payloads)."""
    return int(df.memory_usage(deep=True).sum())


@dataclass(frozen=True)
class MemoryReport:
    before_bytes: int
    after_bytes: int
    dtype_changes: dict[str, tuple[str, str]]

    @property
    def reduction(self) -> float:
        """Fractional reduction, e.g. ``0.73`` for a 73% smaller frame."""
        return 1 - self.after_bytes / self.before_bytes if self.before_bytes else 0.0


def _downcast_float(series: pd.Series, rtol: float) -> pd.Series:
    candidate = series.astype(np.float32)
    # Only accept float32 if it represents every value within tolerance (float32 has ~7 significant digits).
    if np.allclose(candidate.to_numpy(dtype=np.float64), series.to_numpy(dtype=np.float64), rtol=rtol, equal_nan=True):
        return candidate
    return series


@overload
def optimize_dataframe(
    df: pd.DataFrame,
    category_cols: Iterable[str] | None = ...,
    auto_category_threshold: float | None = ...,
    downcast_floats: bool = ...,
    float_rtol: float = ...,
    verbose: bool = ...,
    return_report: Literal[False] = ...,
) -> pd.DataFrame: ...


@overload
def optimize_dataframe(
    df: pd.DataFrame,
    category_cols: Iterable[str] | None = ...,
    auto_category_threshold: float | None = ...,
    downcast_floats: bool = ...,
    float_rtol: float = ...,
    verbose: bool = ...,
    *,
    return_report: Literal[True],
) -> tuple[pd.DataFrame, MemoryReport]: ...


def optimize_dataframe(
    df: pd.DataFrame,
    category_cols: Iterable[str] | None = None,
    auto_category_threshold: float | None = None,
    downcast_floats: bool = True,
    float_rtol: float = 1e-6,
    verbose: bool = False,
    return_report: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MemoryReport]:
    """Reduce memory usage by downcasting numerics and converting low-cardinality text to ``category``.

    Args:
        category_cols: columns to convert to ``category`` unconditionally.
        auto_category_threshold: also convert any text column whose unique-value ratio is below
            this fraction (e.g. ``0.5``). ``None`` disables automatic detection.
        downcast_floats: allow float64 -> float32 when it is lossless within ``float_rtol``.
        return_report: also return a :class:`MemoryReport`.

    Integer downcasting is always exact. Float downcasting is verified per column, so the
    default behaviour never silently loses precision beyond ``float_rtol``.
    """
    before = memory_bytes(df)
    out = df.copy()
    changes: dict[str, tuple[str, str]] = {}

    targets = {c for c in (category_cols or []) if c in out.columns}
    if auto_category_threshold is not None and len(out):
        for col in text_columns(out):
            if out[col].nunique(dropna=True) / len(out) < auto_category_threshold:
                targets.add(col)

    for col in out.columns:
        original = str(out[col].dtype)
        series = out[col]
        if col in targets:
            out[col] = series.astype("category")
        elif pd.api.types.is_bool_dtype(series):
            continue
        elif pd.api.types.is_integer_dtype(series):
            out[col] = pd.to_numeric(series, downcast="integer")
        elif pd.api.types.is_float_dtype(series) and downcast_floats:
            out[col] = _downcast_float(series, float_rtol)
        new = str(out[col].dtype)
        if new != original:
            changes[str(col)] = (original, new)

    report = MemoryReport(before, memory_bytes(out), changes)
    if verbose:
        logger.info(
            "Memory: %.2f MB -> %.2f MB (%.1f%% reduction); %d dtype changes",
            before / 2**20,
            report.after_bytes / 2**20,
            report.reduction * 100,
            len(changes),
        )
    return (out, report) if return_report else out
