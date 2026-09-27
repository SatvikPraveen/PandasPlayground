from __future__ import annotations

import pandas as pd
import pytest

from pandasplayground import dashboard, io
from pandasplayground.pipeline import days_observed

from .conftest import DATA

pytestmark = pytest.mark.integration


def test_load_and_filter_panel():
    panel = dashboard.load_panel()
    assert pd.api.types.is_datetime64_any_dtype(panel["month"])
    assert panel["month"].is_monotonic_increasing
    view = dashboard.filter_months(panel, pd.Timestamp("2020-03-01"), pd.Timestamp("2020-05-01"))
    assert len(view) == 3


def test_kpis_follow_filter():
    panel = dashboard.load_panel()
    full, part = dashboard.kpis(panel), dashboard.kpis(panel.head(12))
    assert part.total_sales < full.total_sales
    assert part.months == 12
    assert full.profit_margin == pytest.approx(full.total_profit / full.total_sales)
    empty = dashboard.kpis(panel.iloc[:0])
    assert empty.total_sales == 0


def test_correlation_table_and_approval_rates():
    panel = dashboard.load_panel()
    days = days_observed(io.read(DATA / "superstore_sales.csv"), io.read(DATA / "covid_data.parquet"))
    table = dashboard.correlation_table(panel, days=days).set_index("series")
    assert len(table) == 5
    assert ((table["ci_low"] <= table["r"]) & (table["r"] <= table["ci_high"])).all()
    # Known confound: raw monthly totals correlate through calendar length; per-day rates do not.
    assert table.loc["monthly totals (Pearson)", "ci_low"] > 0
    assert table.loc["per-day rates (Pearson)", "ci_low"] < 0 < table.loc["per-day rates (Pearson)", "ci_high"]
    assert len(dashboard.correlation_table(panel)) == 3
    rates = dashboard.approval_rates(io.read(DATA / "bank_loans.xlsx"))
    assert rates["n"].sum() == 10_000
    assert ((rates["ci_low"] <= rates["rate"]) & (rates["rate"] <= rates["ci_high"])).all()
