"""Legacy aggregation/merge helpers. Prefer :mod:`pandasplayground.aggregation` and :mod:`pandasplayground.merging`.

``safe_merge`` and ``compute_approval_rate`` keep their original defaults here so the notebooks'
outputs are unchanged.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

import scripts
from pandasplayground import aggregation as _agg
from pandasplayground import merging as _merge
from pandasplayground.aggregation import (
    groupby_summary,
    grouped_eval,
    melt_summary,
    pivot_table_summary,
    resample_monthly,
    rolling_rank,
    stacked_groupby_unstack,
)
from pandasplayground.merging import check_merge_key_overlap


def compute_approval_rate(
    df: pd.DataFrame, region_col: str = "region", approval_col: str = "approved", approval_value: Any = "yes"
) -> pd.DataFrame:
    """Original semantics: exact (case-sensitive) match and no ``n`` column."""
    out = _agg.compute_approval_rate(df, region_col, approval_col, approval_value, case_insensitive=False)
    return out.drop(columns="n")


def safe_merge(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    on: str | list[str],
    how: Any = "inner",
    suffixes: tuple[str, str] = ("_x", "_y"),
    parse_dates: bool = False,
    verbose: bool = False,
    **kwargs: Any,
) -> pd.DataFrame:
    merged = _merge.safe_merge(df1, df2, on=on, how=how, suffixes=suffixes, parse_dates=parse_dates, **kwargs)
    assert isinstance(merged, pd.DataFrame)
    if verbose:
        print(f"Merged on {on} using '{how}' join, shape: {merged.shape}")
    return merged


def safe_concat(
    dfs: list[pd.DataFrame], axis: Any = 0, ignore_index: bool = True, check_columns: bool = True, verbose: bool = False
) -> pd.DataFrame:
    result = _merge.safe_concat(dfs, axis=axis, ignore_index=ignore_index, check_columns=check_columns)
    if verbose:
        print(f"Concatenated {len(dfs)} DataFrames, shape: {result.shape}")
    return result
