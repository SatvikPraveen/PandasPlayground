from __future__ import annotations

import pandas as pd
import pytest

from pandasplayground import io


@pytest.mark.parametrize("suffix", [".csv", ".tsv", ".parquet", ".xlsx", ".json", ".feather"])
def test_roundtrip_all_formats(tmp_path, suffix):
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"], "c": [0.5, 1.5, 2.5]})
    path = io.write(df, tmp_path / "nested" / f"frame{suffix}")
    assert path.exists()
    pd.testing.assert_frame_equal(io.read(path), df, check_dtype=False)


def test_read_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        io.read(tmp_path / "missing.csv")


def test_unsupported_format(tmp_path):
    bad = tmp_path / "x.txt"
    bad.write_text("hi")
    with pytest.raises(ValueError, match="Unsupported"):
        io.read(bad)
    with pytest.raises(ValueError, match="Unsupported"):
        io.write(pd.DataFrame({"a": [1]}), tmp_path / "x.txt")


def test_sha256_is_stable_and_content_sensitive(tmp_path):
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_bytes(b"hello")
    b.write_bytes(b"hello!")
    assert io.sha256_file(a) == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert io.sha256_file(a) != io.sha256_file(b)


def test_frame_fingerprint_detects_value_order_and_dtype_changes():
    df = pd.DataFrame({"a": [1, 2], "b": [3.0, 4.0]})
    base = io.frame_fingerprint(df)
    assert base == io.frame_fingerprint(df.copy())
    assert base != io.frame_fingerprint(df.assign(b=[3.0, 4.5]))
    assert base != io.frame_fingerprint(df.iloc[::-1])
    assert base != io.frame_fingerprint(df.astype({"a": "int32"}))


def test_load_excel_all_sheets(tmp_path):
    path = tmp_path / "multi.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame({"x": [1]}).to_excel(writer, sheet_name="one", index=False)
        pd.DataFrame({"x": [2]}).to_excel(writer, sheet_name="two", index=False)
    sheets = io.load_excel(path, sheet_name=None)
    assert set(sheets) == {"one", "two"}
