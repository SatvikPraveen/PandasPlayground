from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st

from pandasplayground import cleaning


def test_standardize_strings_preserves_missing_values():
    df = pd.DataFrame({"name": ["  Alice ", None, np.nan, "BOB"]})
    out = cleaning.standardize_strings(df)
    assert out["name"].tolist()[0] == "alice"
    assert out["name"].tolist()[3] == "bob"
    assert out["name"].isna().sum() == 2
    assert "nan" not in out["name"].dropna().tolist()


def test_standardize_strings_does_not_mutate_input():
    df = pd.DataFrame({"name": [" A "]})
    cleaning.standardize_strings(df)
    assert df["name"].iloc[0] == " A "


def test_standardize_collapses_internal_whitespace():
    out = cleaning.standardize_strings(pd.DataFrame({"s": ["New    York\tCity"]}))
    assert out["s"].iloc[0] == "new york city"


def test_standardize_handles_categoricals():
    df = pd.DataFrame({"c": pd.Categorical([" A", "a ", "B"])})
    out = cleaning.standardize_strings(df, columns=["c"])
    assert isinstance(out["c"].dtype, pd.CategoricalDtype)
    assert out["c"].tolist() == ["a", "a", "b"]


def test_clean_dataframe_dedupes_after_normalising():
    df = pd.DataFrame({"name": [" Alice", "alice ", "Bob"], "score": [1, 1, 2]})
    assert len(cleaning.clean_dataframe(df)) == 2


def test_clean_dataframe_unknown_dropna_column():
    with pytest.raises(KeyError):
        cleaning.clean_dataframe(pd.DataFrame({"a": [1]}), drop_na_cols=["b"])


def test_text_columns_ignores_mixed_object_columns():
    df = pd.DataFrame({"txt": ["a", "b"], "mixed": pd.Series([1, "x"], dtype=object), "num": [1, 2]})
    assert cleaning.text_columns(df) == ["txt"]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("Order Date", "order_date"), ("Sub-Category", "sub_category"), ("loanAmount", "loan_amount"), (" ID ", "id")],
)
def test_normalize_column_names(raw, expected):
    assert cleaning.normalize_column_names(pd.DataFrame(columns=[raw])).columns[0] == expected


def test_normalize_column_names_rejects_collisions():
    with pytest.raises(ValueError, match="duplicates"):
        cleaning.normalize_column_names(pd.DataFrame(columns=["A B", "a_b"]))


@pytest.mark.parametrize("method", ["iqr", "zscore", "mad"])
def test_outlier_methods_flag_extreme_value(method):
    values = [*np.random.default_rng(0).normal(0, 1, 200), 50.0]
    out = cleaning.detect_outliers(pd.DataFrame({"v": values}), "v", method=method)
    assert 50.0 in out["v"].to_numpy()


def test_iqr_bounds_match_tukey_definition():
    b = cleaning.outlier_bounds(pd.Series([1, 2, 3, 4, 5, 6, 7, 8]), "iqr")
    q1, q3 = 2.75, 6.25
    assert b.lower == pytest.approx(q1 - 1.5 * (q3 - q1))
    assert b.upper == pytest.approx(q3 + 1.5 * (q3 - q1))


def test_outlier_bounds_empty_and_unknown_method():
    assert np.isnan(cleaning.outlier_bounds(pd.Series([], dtype=float)).lower)
    with pytest.raises(ValueError):
        cleaning.outlier_bounds(pd.Series([1.0, 2.0]), "bogus")  # type: ignore[arg-type]


def test_missingness_report():
    rep = cleaning.missingness_report(pd.DataFrame({"a": [1, None, None, 4], "b": [1, 2, 3, 4]}))
    assert rep.loc["a", "n_missing"] == 2
    assert rep.loc["a", "pct_missing"] == 50
    assert rep.index[0] == "a"


def test_align_customer_ids_casts_integer_ids():
    out = cleaning.align_customer_ids(pd.DataFrame({"customer_id": [1001, 1002]}))
    assert out["customer_id"].tolist() == ["1001", "1002"]


def test_align_customer_ids():
    out = cleaning.align_customer_ids(pd.DataFrame({"customer_id": [" 7 ", "8"]}))
    assert out["customer_id"].tolist() == ["7", "8"]


# --- property-based -------------------------------------------------------

text_or_none = st.one_of(st.none(), st.text(max_size=20))


@given(st.lists(text_or_none, min_size=1, max_size=30))
def test_standardize_is_idempotent_and_null_preserving(values):
    df = pd.DataFrame({"s": pd.Series(values, dtype=object)})
    once = cleaning.standardize_strings(df, columns=["s"])
    twice = cleaning.standardize_strings(once, columns=["s"])
    pd.testing.assert_frame_equal(once, twice)
    assert once["s"].isna().tolist() == df["s"].isna().tolist()
