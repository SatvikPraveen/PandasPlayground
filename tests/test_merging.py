from __future__ import annotations

import pandas as pd
import pytest

from pandasplayground import merging


@pytest.fixture
def frames():
    left = pd.DataFrame({"k": [1, 2, 3], "a": ["x", "y", "z"]})
    right = pd.DataFrame({"k": ["2", "3", "4"], "b": [20, 30, 40]})
    return left, right


def test_safe_merge_aligns_dtypes_without_mutating(frames):
    left, right = frames
    before = right.copy()
    out = merging.safe_merge(left, right, on="k")
    assert out["k"].tolist() == [2, 3]
    pd.testing.assert_frame_equal(right, before)


def test_merge_report_counts(frames):
    left, right = frames
    out, rep = merging.safe_merge(left, right, on="k", how="outer", return_report=True)
    assert (rep.matched, rep.left_only, rep.right_only, rep.result_rows) == (2, 1, 1, 4)
    assert rep.left_coverage == pytest.approx(2 / 3)
    assert "_merge" not in out.columns


def test_validate_detects_many_to_many():
    left = pd.DataFrame({"k": [1, 1], "a": [1, 2]})
    right = pd.DataFrame({"k": [1, 1], "b": [3, 4]})
    with pytest.raises(pd.errors.MergeError):
        merging.safe_merge(left, right, on="k", validate="one_to_one")


def test_missing_keys(frames):
    left, right = frames
    with pytest.raises(KeyError, match="Missing merge keys"):
        merging.safe_merge(left, right, on="nope")


def test_parse_dates():
    left = pd.DataFrame({"d": ["2024-01-01"], "a": [1]})
    right = pd.DataFrame({"d": pd.to_datetime(["2024-01-01"]), "b": [2]})
    assert len(merging.safe_merge(left, right, on="d", parse_dates=True)) == 1


def test_safe_concat_reports_column_diff():
    with pytest.raises(ValueError, match="missing=\\['b'\\]"):
        merging.safe_concat([pd.DataFrame({"a": [1], "b": [2]}), pd.DataFrame({"a": [1]})])
    with pytest.raises(ValueError):
        merging.safe_concat([])
    assert len(merging.safe_concat([pd.DataFrame({"a": [1]})] * 3)) == 3


def test_check_merge_key_overlap(frames):
    assert merging.check_merge_key_overlap(*frames) == ["k"]
