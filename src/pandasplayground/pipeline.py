"""The end-to-end analysis pipeline: raw data -> validated monthly panel -> export + manifest.

This is the scripted, deterministic equivalent of ``notebooks/08_final_pipeline.ipynb``.
It reads the *raw* files in ``data/`` (not intermediate notebook outputs), validates every
input and the output against their schemas, and writes a provenance manifest next to the export.

Run it with ``pandasplayground pipeline``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from pandasplayground import aggregation, cleaning, io, merging, schemas
from pandasplayground.config import PATHS
from pandasplayground.provenance import RunManifest, describe_file
from pandasplayground.validation import ValidationReport

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineConfig:
    data_dir: Path = PATHS.data
    output_path: Path = PATHS.exports / "final_merged_pipeline.csv"
    manifest_path: Path | None = None
    rolling_window: int = 3
    validate: bool = True
    strict: bool = True

    @property
    def resolved_manifest_path(self) -> Path:
        return self.manifest_path or self.output_path.with_suffix(".manifest.json")


@dataclass
class PipelineResult:
    frame: pd.DataFrame
    manifest: RunManifest
    reports: dict[str, ValidationReport] = field(default_factory=dict)


def monthly_sales(superstore: pd.DataFrame) -> pd.DataFrame:
    """Total ``sales`` and ``profit`` per ``YYYY-MM`` month."""
    tidy = cleaning.normalize_column_names(superstore)
    return aggregation.monthly_period_summary(tidy, "order_date", {"sales": "sum", "profit": "sum"})


def monthly_covid(covid: pd.DataFrame) -> pd.DataFrame:
    """Total ``new_cases`` and mean daily ``hospitalized`` per ``YYYY-MM`` month."""
    return aggregation.monthly_period_summary(covid, "date", {"new_cases": "sum", "hospitalized": "mean"})


def days_observed(superstore: pd.DataFrame, covid: pd.DataFrame) -> pd.DataFrame:
    """Number of distinct observed days per month in each source.

    Monthly *sums* scale with the number of days observed, so two unrelated daily series summed to
    months correlate through calendar length alone (28 to 31 days, plus a partial final month).
    Divide by these counts to compare per-day rates instead.
    """
    store_dates = pd.to_datetime(cleaning.normalize_column_names(superstore)["order_date"]).dt.normalize()
    covid_dates = pd.to_datetime(covid["date"]).dt.normalize()

    def _count(dates: pd.Series, name: str) -> pd.Series:
        unique = pd.Series(dates.unique())
        return unique.dt.to_period("M").astype(str).value_counts().rename(name)

    return (
        pd.concat([_count(store_dates, "store_days"), _count(covid_dates, "covid_days")], axis=1)
        .fillna(0)
        .astype(int)
        .rename_axis("month")
        .reset_index()
        .sort_values("month", kind="stable")
        .reset_index(drop=True)
    )


def add_features(panel: pd.DataFrame, rolling_window: int = 3) -> pd.DataFrame:
    """Add a trailing rolling mean of profit and month-over-month sales growth.

    Rows must already be sorted chronologically; both features are order-dependent.
    """
    ordered = panel.sort_values("month", kind="stable").reset_index(drop=True)
    return ordered.assign(
        rolling_profit=ordered["profit"].rolling(rolling_window).mean(),
        sales_pct_change=ordered["sales"].pct_change(),
    )


def build_panel(superstore: pd.DataFrame, covid: pd.DataFrame, rolling_window: int = 3) -> pd.DataFrame:
    """Pure transformation from raw frames to the final monthly panel (no I/O)."""
    merged = merging.safe_merge(
        monthly_sales(superstore), monthly_covid(covid), on="month", how="inner", validate="one_to_one"
    )
    assert isinstance(merged, pd.DataFrame)
    return add_features(merged, rolling_window)


def run_pipeline(config: PipelineConfig | None = None, write: bool = True) -> PipelineResult:
    """Execute the pipeline, returning the panel, validation reports and a provenance manifest."""
    cfg = config or PipelineConfig()
    superstore_path = cfg.data_dir / "superstore_sales.csv"
    covid_path = cfg.data_dir / "covid_data.parquet"

    manifest = RunManifest(
        name="final_merged_pipeline",
        parameters={"rolling_window": cfg.rolling_window, "join": "inner on month (one_to_one)"},
    )

    superstore = io.read(superstore_path)
    covid = io.read(covid_path)
    manifest.inputs += [
        describe_file(superstore_path, superstore, PATHS.root),
        describe_file(covid_path, covid, PATHS.root),
    ]

    reports: dict[str, ValidationReport] = {}
    if cfg.validate:
        reports["superstore_sales"] = schemas.SUPERSTORE.validate(superstore)
        reports["covid_data"] = schemas.COVID.validate(covid)

    panel = build_panel(superstore, covid, cfg.rolling_window)

    if cfg.validate:
        reports["final_merged_pipeline"] = schemas.FINAL_MERGED.validate(panel)
        manifest.validation = {name: rep.ok for name, rep in reports.items()}
        for rep in reports.values():
            logger.info("%s", rep)
            if cfg.strict:
                rep.raise_for_errors()

    if write:
        io.write(panel, cfg.output_path)
        manifest.outputs.append(describe_file(cfg.output_path, panel, PATHS.root))
        manifest.finish().write(cfg.resolved_manifest_path)
        logger.info("Manifest written to %s", cfg.resolved_manifest_path)
    else:
        manifest.finish()

    return PipelineResult(panel, manifest, reports)
