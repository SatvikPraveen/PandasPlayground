"""Non-mutating data-cleaning utilities.

Every function returns a new DataFrame and never modifies its input, which avoids the
``SettingWithCopyWarning`` class of bugs and makes pipelines safe to re-run in notebooks.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

_WHITESPACE = re.compile(r"\s+")


def text_columns(df: pd.DataFrame, include_category: bool = False) -> list[str]:
    """Return columns holding text, working identically under pandas 2 (object) and 3 (str dtype)."""
    cols: list[str] = []
    for name in df.columns:
        dtype = df[name].dtype
        if isinstance(dtype, pd.CategoricalDtype):
            if include_category:
                cols.append(name)
        elif pd.api.types.is_string_dtype(dtype) or pd.api.types.is_object_dtype(dtype):
            # object columns may hold mixed types; only treat them as text if values are strings
            sample = df[name].dropna()
            if sample.empty or sample.map(lambda v: isinstance(v, str)).all():
                cols.append(name)
    return cols


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Convert column names to ``snake_case``.

    Examples: ``"Order Date"`` -> ``"order_date"``, ``"Sub-Category"`` -> ``"sub_category"``,
    ``"loanAmount"`` -> ``"loan_amount"``.
    """

    def _snake(name: object) -> str:
        s = re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip())
        s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", s)
        return s.strip("_").lower()

    renamed = [_snake(c) for c in df.columns]
    if len(set(renamed)) != len(renamed):
        dupes = sorted({c for c in renamed if renamed.count(c) > 1})
        raise ValueError(f"Normalising column names produced duplicates: {dupes}")
    return df.set_axis(renamed, axis=1)


def _normalize_text(series: pd.Series, lower: bool) -> pd.Series:
    # Operate only on non-missing values so NaN/None stay missing (a naive
    # ``astype(str)`` would turn them into the literal string "nan").
    out = series.copy()
    mask = out.notna()
    cleaned = out[mask].astype(str).str.strip().str.replace(_WHITESPACE, " ", regex=True)
    if lower:
        cleaned = cleaned.str.lower()
    out.loc[mask] = cleaned
    return out


def standardize_strings(df: pd.DataFrame, columns: Iterable[str] | None = None, lower: bool = True) -> pd.DataFrame:
    """Trim, collapse internal whitespace and (optionally) lowercase text columns, preserving missing values."""
    result = df.copy()
    targets = list(columns) if columns is not None else text_columns(result)
    for col in targets:
        if isinstance(result[col].dtype, pd.CategoricalDtype):
            result[col] = _normalize_text(result[col].astype(object), lower).astype("category")
        else:
            result[col] = _normalize_text(result[col], lower)
    return result


def clean_dataframe(
    df: pd.DataFrame,
    drop_na_cols: Sequence[str] | None = None,
    dedupe: bool = True,
    clean_strings: bool = True,
) -> pd.DataFrame:
    """Drop rows missing required fields, normalise strings, then drop exact duplicates.

    Strings are normalised *before* de-duplication so that ``" Alice"`` and ``"alice"`` collapse.
    """
    result = df.copy()
    if drop_na_cols:
        missing = [c for c in drop_na_cols if c not in result.columns]
        if missing:
            raise KeyError(f"Columns not found: {missing}")
        result = result.dropna(subset=list(drop_na_cols))
    if clean_strings:
        result = standardize_strings(result, columns=text_columns(result, include_category=True))
    if dedupe:
        result = result.drop_duplicates()
    return result


def align_customer_ids(df: pd.DataFrame, column: str = "customer_id") -> pd.DataFrame:
    """Cast an identifier column to trimmed strings so it joins reliably across sources."""
    result = df.copy()
    if column in result.columns:
        result[column] = _normalize_text(result[column], lower=False)
    return result


# ---------------------------------------------------------------------------
# Outliers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OutlierBounds:
    lower: float
    upper: float
    method: str


def outlier_bounds(
    series: pd.Series, method: Literal["iqr", "zscore", "mad"] = "iqr", threshold: float | None = None
) -> OutlierBounds:
    """Compute outlier fences for a numeric series.

    * ``iqr``: Tukey fences ``Q1 - k*IQR``, ``Q3 + k*IQR`` (default ``k=1.5``).
    * ``zscore``: ``mean ± k*std`` (default ``k=3``); sensitive to the outliers it is trying to find.
    * ``mad``: robust modified z-score using the median absolute deviation (default ``k=3.5``,
      Iglewicz & Hoaglin, 1993). Recommended for heavy-tailed data.
    """
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return OutlierBounds(float("nan"), float("nan"), method)
    if method == "iqr":
        k = 1.5 if threshold is None else threshold
        q1, q3 = s.quantile([0.25, 0.75])
        iqr = q3 - q1
        return OutlierBounds(float(q1 - k * iqr), float(q3 + k * iqr), method)
    if method == "zscore":
        k = 3.0 if threshold is None else threshold
        mu, sd = s.mean(), s.std(ddof=1)
        return OutlierBounds(float(mu - k * sd), float(mu + k * sd), method)
    if method == "mad":
        k = 3.5 if threshold is None else threshold
        med = s.median()
        mad = float(np.median(np.abs(s - med)))
        # 0.6745 = Phi^-1(0.75): scales MAD to be consistent with the std. dev. under normality.
        spread = k * mad / 0.6745
        return OutlierBounds(float(med - spread), float(med + spread), method)
    raise ValueError(f"Unknown outlier method {method!r}")


def detect_outliers(
    df: pd.DataFrame, col: str, method: Literal["iqr", "zscore", "mad"] = "iqr", threshold: float | None = None
) -> pd.DataFrame:
    """Return the rows of ``df`` whose ``col`` value lies strictly outside the outlier fences."""
    bounds = outlier_bounds(df[col], method=method, threshold=threshold)
    values = pd.to_numeric(df[col], errors="coerce")
    return df[(values < bounds.lower) | (values > bounds.upper)]


def detect_outliers_iqr(df: pd.DataFrame, col: str, k: float = 1.5) -> pd.DataFrame:
    """Backwards-compatible wrapper for :func:`detect_outliers` with Tukey's IQR rule."""
    return detect_outliers(df, col, method="iqr", threshold=k)


def missingness_report(df: pd.DataFrame) -> pd.DataFrame:
    """Per-column count and share of missing values, sorted by share descending."""
    n = len(df)
    counts = df.isna().sum()
    report = pd.DataFrame(
        {
            "n_missing": counts,
            "pct_missing": counts / n * 100 if n else counts.astype(float),
            "dtype": df.dtypes.astype(str),
        }
    )
    return report.sort_values("pct_missing", ascending=False)
