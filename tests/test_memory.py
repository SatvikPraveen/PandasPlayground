from __future__ import annotations

import numpy as np
import pandas as pd
from hypothesis import given
from hypothesis.extra.pandas import column, data_frames

from pandasplayground.memory import optimize_dataframe


def test_report_and_dtype_changes():
    df = pd.DataFrame({"i": np.arange(100, dtype="int64"), "s": ["a", "b"] * 50, "f": np.linspace(0, 1, 100)})
    out, rep = optimize_dataframe(df, category_cols=["s"], return_report=True)
    assert rep.after_bytes < rep.before_bytes
    assert 0 < rep.reduction < 1
    assert rep.dtype_changes["i"] == ("int64", "int8")
    assert isinstance(out["s"].dtype, pd.CategoricalDtype)


def test_float_downcast_is_exact_by_default():
    precise = pd.DataFrame({"f": [1.0000001234567, 1292.63]})
    assert optimize_dataframe(precise)["f"].dtype == np.float64
    assert optimize_dataframe(precise, float_rtol=1e-6)["f"].dtype == np.float32
    exact = pd.DataFrame({"f": [0.5, 2.0, -8.25]})
    assert optimize_dataframe(exact)["f"].dtype == np.float32


def test_auto_category_threshold():
    df = pd.DataFrame({"low": ["x", "y"] * 50, "high": [f"id{i}" for i in range(100)]})
    out = optimize_dataframe(df, auto_category_threshold=0.5)
    assert isinstance(out["low"].dtype, pd.CategoricalDtype)
    assert not isinstance(out["high"].dtype, pd.CategoricalDtype)


def test_bools_untouched_and_input_not_mutated():
    df = pd.DataFrame({"b": [True, False], "i": [1, 2]})
    before = df.dtypes.copy()
    out = optimize_dataframe(df)
    assert out["b"].dtype == bool
    pd.testing.assert_series_equal(df.dtypes, before)


@given(data_frames([column("x", dtype="int64"), column("y", dtype="float64")]))
def test_integer_downcast_is_exact(df):
    out = optimize_dataframe(df, downcast_floats=False)
    assert out["x"].astype("int64").equals(df["x"])
    pd.testing.assert_series_equal(out["y"], df["y"])
