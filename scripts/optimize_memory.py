"""Legacy memory helper. Prefer :mod:`pandasplayground.memory`."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

import scripts
from pandasplayground.memory import optimize_dataframe as _optimize


def optimize_dataframe(
    df: pd.DataFrame, category_cols: Iterable[str] | None = None, verbose: bool = True
) -> pd.DataFrame:
    if verbose:
        print("Memory usage BEFORE optimization:")
        df.info(memory_usage="deep")
    out = _optimize(df, category_cols=category_cols)
    assert isinstance(out, pd.DataFrame)
    if verbose:
        print("\nMemory usage AFTER optimization:")
        out.info(memory_usage="deep")
    return out
