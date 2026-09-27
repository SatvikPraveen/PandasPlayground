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


def correlation_table(df: pd.DataFrame, x: str = "sales", y: str = "new_cases") -> pd.DataFrame:
    """Raw vs first-differenced correlation between two monthly series, with 95% CIs."""
    rows = []
    for label, est in (
        ("levels (Pearson)", stats.correlation_ci(df[x], df[y])),
        ("levels (Spearman)", stats.correlation_ci(df[x], df[y], method="spearman")),
        ("first differences (Pearson)", stats.differenced_correlation(df[x], df[y])),
    ):
        rows.append({"series": label, "r": est.point, "ci_low": est.low, "ci_high": est.high})
    return pd.DataFrame(rows)


def approval_rates(loans: pd.DataFrame, by: str = "Loan_Purpose", approved_col: str = "Approved") -> pd.DataFrame:
    """Approval rate per group with Wilson 95% intervals."""
    rows = []
    for group, frame in loans.groupby(by, observed=True):
        n = len(frame)
        k = int((frame[approved_col].astype(str).str.lower() == "yes").sum())
        est = stats.proportion_ci(k, n)
        rows.append({by: group, "n": n, "approved": k, "rate": est.point, "ci_low": est.low, "ci_high": est.high})
    return pd.DataFrame(rows).sort_values("rate", ascending=False).reset_index(drop=True)
