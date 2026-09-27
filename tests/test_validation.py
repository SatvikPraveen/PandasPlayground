from __future__ import annotations

import pandas as pd
import pytest

from pandasplayground.validation import Check, Column, DataFrameSchema, SchemaError

SCHEMA = DataFrameSchema(
    "people",
    [
        Column("id", "int", nullable=False, unique=True),
        Column("age", "int", min=0, max=120),
        Column("grade", "string", allowed=("A", "B")),
        Column("code", "string", pattern=r"[A-Z]{2}\d"),
        Column("joined", "string", coerce_datetime=True, min="2020-01-01"),
    ],
    strict=True,
    min_rows=1,
    unique_together=[("grade", "code")],
    checks=[Check("age_below_200", lambda df: df["age"] < 200, "sanity")],
)


def valid() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": [1, 2],
            "age": [30, 40],
            "grade": ["A", "B"],
            "code": ["AB1", "CD2"],
            "joined": ["2021-01-01", "2022-05-05"],
        }
    )


def test_valid_frame_passes():
    report = SCHEMA.validate(valid())
    assert report.ok, str(report)
    report.raise_for_errors()


def test_collects_every_failure():
    bad = valid()
    bad.loc[1, ["id", "age", "grade", "code", "joined"]] = [1, 150, "C", "bad", "not a date"]
    bad["extra"] = 0
    report = SCHEMA.validate(bad)
    checks = {f.check for f in report.failures}
    assert {
        "unique",
        "<= 120",
        "in allowed set",
        "parseable as datetime",
        "unexpected column (strict schema)",
    } <= checks
    assert any(c.startswith("matches") for c in checks)
    with pytest.raises(SchemaError, match="people"):
        report.raise_for_errors()
    assert len(report.to_frame()) == len(report.failures)


def test_missing_column_and_dtype_mismatch():
    df = valid().drop(columns="code").assign(age=["x", "y"])
    report = SCHEMA.validate(df)
    assert any(f.column == "code" and f.check == "column present" for f in report.failures)
    assert any(f.column == "age" and f.check == "dtype is int" for f in report.failures)


def test_dtype_failure_does_not_hide_other_failures():
    df = valid().astype({"age": float})
    df.loc[0, "age"] = float("nan")
    df.loc[1, "age"] = 500.0
    checks = {f.check for f in SCHEMA.validate(df).failures}
    assert "dtype is int (missing values upcast integers to float)" in checks
    assert "<= 120" in checks


def test_nulls_min_rows_and_datetime_min():
    df = valid().iloc[:0]
    assert not SCHEMA.validate(df).ok
    df = valid()
    df.loc[0, "joined"] = "2019-12-31"
    assert any(f.check == ">= 2020-01-01" for f in SCHEMA.validate(df).failures)
    df = valid().astype({"id": "Int64"})
    df.loc[0, "id"] = pd.NA
    assert any(f.check == "not null" for f in SCHEMA.validate(df).failures)


def test_broken_check_is_reported_not_raised():
    schema = DataFrameSchema("x", [Column("a")], checks=[Check("boom", lambda df: df["missing"] > 0)])
    report = schema.validate(pd.DataFrame({"a": [1]}))
    assert "KeyError" in report.failures[0].check


def test_scalar_check_and_composite_uniqueness():
    schema = DataFrameSchema(
        "x", [Column("a"), Column("b")], unique_together=[("a", "b")], checks=[Check("never", lambda df: False)]
    )
    report = schema.validate(pd.DataFrame({"a": [1, 1], "b": [2, 2]}))
    assert {f.check for f in report.failures} == {"unique together", "never"}


def test_markdown_render():
    md = SCHEMA.to_markdown()
    assert md.startswith("| Column |")
    assert "`age`" in md and "range [0, 120]" in md
    assert "age_below_200" in md
