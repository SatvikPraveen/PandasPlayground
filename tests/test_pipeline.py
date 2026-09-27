"""Regression and reproducibility tests for the end-to-end pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from pandasplayground import io
from pandasplayground.pipeline import PipelineConfig, add_features, build_panel, days_observed, run_pipeline

from .conftest import DATA, EXPORTS

pytestmark = pytest.mark.integration


def test_pipeline_reproduces_committed_export():
    """Golden-file test: the scripted pipeline must reproduce the committed export from raw data."""
    result = run_pipeline(write=False)
    golden = io.read(EXPORTS / "final_merged_pipeline.csv")
    pd.testing.assert_frame_equal(result.frame, golden, check_dtype=False, rtol=1e-12)
    assert all(r.ok for r in result.reports.values())


def test_pipeline_is_deterministic():
    a = run_pipeline(write=False).frame
    b = run_pipeline(write=False).frame
    assert io.frame_fingerprint(a) == io.frame_fingerprint(b)


def test_pipeline_writes_output_and_manifest(tmp_path):
    cfg = PipelineConfig(data_dir=DATA, output_path=tmp_path / "out.csv")
    result = run_pipeline(cfg)
    manifest = json.loads(cfg.resolved_manifest_path.read_text())
    assert (tmp_path / "out.csv").exists()
    assert manifest["outputs"][0]["sha256"] == io.sha256_file(tmp_path / "out.csv")
    assert manifest["outputs"][0]["rows"] == len(result.frame)
    assert {Path(i["path"]).name for i in manifest["inputs"]} == {"superstore_sales.csv", "covid_data.parquet"}
    assert manifest["validation"] == {"superstore_sales": True, "covid_data": True, "final_merged_pipeline": True}
    assert manifest["environment"]["packages"]["pandas"] == pd.__version__


def test_add_features_sorts_before_order_dependent_features():
    panel = pd.DataFrame(
        {"month": ["2024-03", "2024-01", "2024-02"], "sales": [300.0, 100.0, 200.0], "profit": [3.0, 1.0, 2.0]}
    )
    out = add_features(panel, rolling_window=2)
    assert out["month"].tolist() == ["2024-01", "2024-02", "2024-03"]
    assert out["sales_pct_change"].tolist()[1:] == [1.0, 0.5]
    assert out["rolling_profit"].tolist()[1:] == [1.5, 2.5]


def test_build_panel_only_keeps_months_in_both_sources():
    store = pd.DataFrame({"Order Date": ["2024-01-01", "2024-02-01"], "Sales": [1.0, 2.0], "Profit": [0.1, 0.2]})
    covid = pd.DataFrame(
        {"date": pd.to_datetime(["2024-02-10", "2024-03-10"]), "new_cases": [5, 6], "hospitalized": [1, 2]}
    )
    out = build_panel(store, covid)
    assert out["month"].tolist() == ["2024-02"]


def test_days_observed_counts_calendar_and_partial_months():
    days = days_observed(io.read(DATA / "superstore_sales.csv"), io.read(DATA / "covid_data.parquet")).set_index(
        "month"
    )
    assert days.loc["2020-02", "store_days"] == 29  # leap year
    assert days.loc["2020-04", "covid_days"] == 30
    assert days.loc["2047-05", "store_days"] == 18  # series ends mid-month
    assert set(days.columns) == {"store_days", "covid_days"}
