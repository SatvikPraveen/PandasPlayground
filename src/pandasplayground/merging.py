"""Merge and concat helpers that surface join cardinality and key coverage.

Silent row explosion (many-to-many joins) and silent row loss (unmatched keys) are two of the
most common sources of wrong results in tabular analysis. These helpers make both explicit.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, overload

import pandas as pd

logger = logging.getLogger(__name__)

How = Literal["left", "right", "outer", "inner", "cross"]
Validate = Literal["one_to_one", "1:1", "one_to_many", "1:m", "many_to_one", "m:1", "many_to_many", "m:m"]


@dataclass(frozen=True)
class MergeReport:
    """Diagnostics describing how two frames matched on their keys."""

    left_rows: int
    right_rows: int
    result_rows: int
    matched: int
    left_only: int
    right_only: int

    @property
    def left_coverage(self) -> float:
        """Share of left-side result rows that found a match."""
        denom = self.matched + self.left_only
        return self.matched / denom if denom else float("nan")

    @property
    def right_coverage(self) -> float:
        denom = self.matched + self.right_only
        return self.matched / denom if denom else float("nan")


def _as_list(keys: str | Sequence[str]) -> list[str]:
    return [keys] if isinstance(keys, str) else list(keys)


@overload
def safe_merge(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    on: str | Sequence[str],
    how: How = ...,
    suffixes: tuple[str, str] = ...,
    parse_dates: bool = ...,
    validate: Validate | None = ...,
    align_dtypes: bool = ...,
    verbose: bool = ...,
    return_report: Literal[False] = ...,
) -> pd.DataFrame: ...


@overload
def safe_merge(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    on: str | Sequence[str],
    how: How = ...,
    suffixes: tuple[str, str] = ...,
    parse_dates: bool = ...,
    validate: Validate | None = ...,
    align_dtypes: bool = ...,
    verbose: bool = ...,
    *,
    return_report: Literal[True],
) -> tuple[pd.DataFrame, MergeReport]: ...


def safe_merge(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    on: str | Sequence[str],
    how: How = "inner",
    suffixes: tuple[str, str] = ("_left", "_right"),
    parse_dates: bool = False,
    validate: Validate | None = None,
    align_dtypes: bool = True,
    verbose: bool = False,
    return_report: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MergeReport]:
    """Merge two frames with key checks, dtype alignment and optional cardinality validation.

    Neither input is modified. With ``validate`` set, pandas raises ``MergeError`` if the keys
    violate the declared relationship (e.g. duplicate keys on a ``"one_to_one"`` join).

    Args:
        return_report: also return a :class:`MergeReport` with match counts.
    """
    keys = _as_list(on)
    missing_left = [k for k in keys if k not in df1.columns]
    missing_right = [k for k in keys if k not in df2.columns]
    if missing_left or missing_right:
        raise KeyError(f"Missing merge keys -> left: {missing_left}, right: {missing_right}")

    left, right = df1.copy(), df2.copy()
    for key in keys:
        if parse_dates:
            left[key] = pd.to_datetime(left[key], errors="coerce")
            right[key] = pd.to_datetime(right[key], errors="coerce")
        elif align_dtypes and left[key].dtype != right[key].dtype:
            logger.info("Aligning dtype of key %r: %s -> %s", key, right[key].dtype, left[key].dtype)
            right[key] = right[key].astype(left[key].dtype)

    merged = left.merge(right, on=keys, how=how, suffixes=suffixes, validate=validate, indicator="_merge")
    counts = merged["_merge"].value_counts()
    report = MergeReport(
        left_rows=len(df1),
        right_rows=len(df2),
        result_rows=len(merged),
        matched=int(counts.get("both", 0)),
        left_only=int(counts.get("left_only", 0)),
        right_only=int(counts.get("right_only", 0)),
    )
    merged = merged.drop(columns="_merge")

    if verbose:
        logger.info(
            "Merged on %s using %r join: shape=%s, matched=%d, left_only=%d, right_only=%d",
            keys,
            how,
            merged.shape,
            report.matched,
            report.left_only,
            report.right_only,
        )
    return (merged, report) if return_report else merged


def safe_concat(
    dfs: Sequence[pd.DataFrame],
    axis: Literal[0, 1] = 0,
    ignore_index: bool = True,
    check_columns: bool = True,
    verbose: bool = False,
) -> pd.DataFrame:
    """Concatenate frames, optionally requiring identical column sets for row-wise concatenation."""
    if not dfs:
        raise ValueError("safe_concat requires at least one DataFrame")
    if check_columns and axis == 0:
        base = set(dfs[0].columns)
        for idx, frame in enumerate(dfs[1:], 1):
            cols = set(frame.columns)
            if cols != base:
                raise ValueError(
                    f"Column mismatch between df0 and df{idx}: "
                    f"missing={sorted(base - cols)}, extra={sorted(cols - base)}"
                )
    result = pd.concat(list(dfs), axis=axis, ignore_index=ignore_index)
    if verbose:
        logger.info("Concatenated %d DataFrames -> shape %s", len(dfs), result.shape)
    return result


def check_merge_key_overlap(df1: pd.DataFrame, df2: pd.DataFrame) -> list[str]:
    """Columns present in both frames (candidate merge keys), in ``df1`` order."""
    right = set(df2.columns)
    return [c for c in df1.columns if c in right]
