"""Integration tests: every committed dataset must satisfy its published contract."""

from __future__ import annotations

import pandas as pd
import pytest

from pandasplayground import io, schemas
from pandasplayground.cli import render_data_dictionary

from .conftest import DATA, EXPORTS, ROOT

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(("filename", "schema"), list(schemas.RAW_SCHEMAS.items()), ids=list(schemas.RAW_SCHEMAS))
def test_raw_datasets_conform(filename, schema):
    report = schema.validate(io.read(DATA / filename))
    assert report.ok, str(report)


def test_regional_workbook_conforms():
    sheets = pd.read_excel(DATA / "bank_loans_multisheet.xlsx", sheet_name=None)
    assert set(sheets) == set(schemas.LOAN_REGIONS)
    for name, frame in sheets.items():
        assert schemas.BANK_LOANS_REGIONAL.validate(frame).ok, name
        assert (frame["Region"] == name).all()


def test_final_export_conforms():
    report = schemas.FINAL_MERGED.validate(io.read(EXPORTS / "final_merged_pipeline.csv"))
    assert report.ok, str(report)


def test_data_dictionary_is_up_to_date():
    committed = (ROOT / "docs" / "DATA_DICTIONARY.md").read_text()
    assert committed == render_data_dictionary(), "Run: pandasplayground docs data-dictionary"
