"""Framework-agnostic data logic for the Streamlit dashboard (kept here so it is unit-tested)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from pandasplayground import io, stats
from pandasplayground.config import PATHS

PANEL_PATH = PATHS.exports / "final_merged_pipeline.csv"


def load_panel(path: Path = PANEL_PATH) -> pd.DataFrame:
    """Load the monthly panel and parse ``month`` into a timestamp (first day of month)."""
    df = io.read(path)
    return df.assign(month=pd.to_datetime(df["month"], format="%Y-%m")).sort_values("month").reset_index(drop=True)


def filter_months(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Inclusive month-range filter."""
    return df[(df["month"] >= start) & (df["month"] <= end)]


@dataclass(frozen=True)
class Kpis:
    total_sales: float
    total_profit: float
    profit_margin: float
    total_cases: int
    mean_hospitalized: float
    months: int


def kpis(df: pd.DataFrame) -> Kpis:
    sales = float(df["sales"].sum())
    profit = float(df["profit"].sum())
    return Kpis(
        total_sales=sales,
        total_profit=profit,
        profit_margin=profit / sales if sales else float("nan"),
        total_cases=int(df["new_cases"].sum()),
        mean_hospitalized=float(df["hospitalized"].mean()) if len(df) else float("nan"),
        months=len(df),
    )


def correlation_table(
    df: pd.DataFrame, x: str = "sales", y: str = "new_cases", days: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Correlation between two monthly totals, with 95% CIs, under several adjustments.

    ``days`` (from :func:`pandasplayground.pipeline.days_observed`) adds per-day-rate rows, which remove
    the calendar-length confound that raw monthly sums share.
    """
    candidates = [
        ("monthly totals (Pearson)", stats.correlation_ci(df[x], df[y])),
        ("monthly totals (Spearman)", stats.correlation_ci(df[x], df[y], method="spearman")),
        ("first differences of totals (Pearson)", stats.differenced_correlation(df[x], df[y])),
    ]
    if days is not None:
        month_key = (
            df["month"].dt.strftime("%Y-%m") if pd.api.types.is_datetime64_any_dtype(df["month"]) else df["month"]
        )
        d = days.set_index("month").reindex(month_key.to_numpy())
        rate_x = df[x].to_numpy() / d["store_days"].to_numpy()
        rate_y = df[y].to_numpy() / d["covid_days"].to_numpy()
        candidates += [
            ("per-day rates (Pearson)", stats.correlation_ci(rate_x, rate_y)),
            ("first differences of per-day rates (Pearson)", stats.differenced_correlation(rate_x, rate_y)),
        ]
    return pd.DataFrame([{"series": s, "r": e.point, "ci_low": e.low, "ci_high": e.high} for s, e in candidates])


def approval_rates(loans: pd.DataFrame, by: str = "Loan_Purpose", approved_col: str = "Approved") -> pd.DataFrame:
    """Approval rate per group with Wilson 95% intervals."""
    rows = []
    for group, frame in loans.groupby(by, observed=True):
        n = len(frame)
        k = int((frame[approved_col].astype(str).str.lower() == "yes").sum())
        est = stats.proportion_ci(k, n)
        rows.append({by: group, "n": n, "approved": k, "rate": est.point, "ci_low": est.low, "ci_high": est.high})
    return pd.DataFrame(rows).sort_values("rate", ascending=False).reset_index(drop=True)
