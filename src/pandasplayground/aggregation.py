"""Grouped, pivoted and time-based aggregation helpers (all non-mutating)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Literal

import pandas as pd

GroupKeys = str | Sequence[str]

#: Month-end offset alias. ``"M"`` was deprecated in pandas 2.2 in favour of ``"ME"``.
MONTH_END = "ME"


def groupby_summary(
    df: pd.DataFrame, group_col: GroupKeys, agg_dict: Mapping[str, Any], reset: bool = True
) -> pd.DataFrame:
    """Group by ``group_col`` and aggregate with ``agg_dict`` (``{"sales": "sum"}``)."""
    keys = [group_col] if isinstance(group_col, str) else list(group_col)
    missing = [k for k in keys if k not in df.columns]
    if missing:
        raise KeyError(f"Group columns not found: {missing}")
    result = df.groupby(keys, observed=True).agg(dict(agg_dict))
    return result.reset_index() if reset else result


def compute_approval_rate(
    df: pd.DataFrame,
    region_col: str = "region",
    approval_col: str = "approved",
    approval_value: Any = "yes",
    case_insensitive: bool = True,
) -> pd.DataFrame:
    """Share of rows per group whose ``approval_col`` equals ``approval_value``, plus the group size ``n``."""
    target = df[approval_col]
    if case_insensitive and isinstance(approval_value, str):
        hit = target.astype("string").str.strip().str.lower() == approval_value.strip().lower()
    else:
        hit = target == approval_value
    return (
        df.assign(_hit=hit.fillna(False).astype(float))
        .groupby(region_col, observed=True)
        .agg(approval_rate=("_hit", "mean"), n=("_hit", "size"))
        .reset_index()
    )


def pivot_table_summary(
    df: pd.DataFrame, index: GroupKeys, columns: GroupKeys, values: str, aggfunc: Any = "mean"
) -> pd.DataFrame:
    return pd.pivot_table(df, index=index, columns=columns, values=values, aggfunc=aggfunc, observed=True)


def resample_period(df: pd.DataFrame, date_col: str, metrics: Mapping[str, Any], freq: str = MONTH_END) -> pd.DataFrame:
    """Resample by calendar period on ``date_col`` without mutating ``df``."""
    frame = df.assign(**{date_col: pd.to_datetime(df[date_col])})
    return frame.set_index(date_col).resample(freq).agg(dict(metrics)).reset_index()


def resample_monthly(df: pd.DataFrame, date_col: str, metrics_dict: Mapping[str, Any]) -> pd.DataFrame:
    """Monthly (month-end) resampling; see :func:`resample_period`."""
    return resample_period(df, date_col, metrics_dict, freq=MONTH_END)


def monthly_period_summary(df: pd.DataFrame, date_col: str, metrics: Mapping[str, Any]) -> pd.DataFrame:
    """Aggregate to ``YYYY-MM`` period strings (only months present in the data are returned)."""
    month = pd.to_datetime(df[date_col]).dt.to_period("M").astype(str)
    return df.assign(month=month).groupby("month", as_index=False).agg(dict(metrics))


def melt_summary(df: pd.DataFrame, id_vars: GroupKeys, var_name: str, value_name: str) -> pd.DataFrame:
    """Convert a wide (pivoted) frame to long format."""
    return df.reset_index().melt(id_vars=id_vars, var_name=var_name, value_name=value_name)


def stacked_groupby_unstack(
    df: pd.DataFrame, group_cols: Sequence[str], value_col: str, unstack_col: str, fill_value: Any = 0
) -> pd.DataFrame:
    """Sum ``value_col`` over ``group_cols`` and pivot ``unstack_col`` into columns."""
    return df.groupby(list(group_cols), observed=True)[value_col].sum().unstack(unstack_col, fill_value=fill_value)  # noqa: PD010


def rolling_rank(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    window: int,
    date_col: str = "order_date",
    ascending: bool = False,
    rank_method: Literal["average", "min", "max", "first", "dense"] = "average",
) -> pd.DataFrame:
    """Rank of each row's value among the trailing ``window`` rows of its group (ordered by ``date_col``).

    Adds ``rolling_rank_{value_col}``. Rank 1 is the largest value when ``ascending=False``.
    """
    new_col = f"rolling_rank_{value_col}"
    ordered = df.sort_values([group_col, date_col], kind="stable")

    def _last_rank(window_values: pd.Series) -> float:
        return float(window_values.rank(method=rank_method, ascending=ascending).iloc[-1])

    ranks = (
        ordered.groupby(group_col, observed=True, group_keys=False)[value_col]
        .rolling(window, min_periods=1)
        .apply(_last_rank, raw=False)
        .reset_index(level=0, drop=True)
    )
    return ordered.assign(**{new_col: ranks})


def grouped_eval(df: pd.DataFrame, group_cols: GroupKeys, target_col: str, new_col: str, func: Any) -> pd.DataFrame:
    """Add ``new_col`` = ``groupby(group_cols)[target_col].transform(func)``."""
    keys = [group_cols] if isinstance(group_cols, str) else list(group_cols)
    return df.assign(**{new_col: df.groupby(keys, observed=True)[target_col].transform(func)})
