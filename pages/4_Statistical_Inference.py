"""Statistical inference on the bundled data, with uncertainty and effect sizes."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

import scripts  # noqa: F401
from pandasplayground import dashboard, io, stats
from pandasplayground.config import PATHS
from pandasplayground.pipeline import days_observed

st.title("Statistical inference")
st.caption("Every estimate is reported with a 95% interval and every test with an effect size.")


@st.cache_data
def load_panel() -> pd.DataFrame:
    return dashboard.load_panel()


@st.cache_data
def load_loans() -> pd.DataFrame:
    return io.read(PATHS.data / "bank_loans.xlsx")


@st.cache_data
def load_days() -> pd.DataFrame:
    return days_observed(io.read(PATHS.data / "superstore_sales.csv"), io.read(PATHS.data / "covid_data.parquet"))


panel, loans, days = load_panel(), load_loans(), load_days()

st.header("1. Are sales related to COVID cases?")
st.markdown(
    "Sales and cases were generated independently, yet their **monthly totals** correlate. Both are sums "
    "of daily values, so longer months have more of each, and the last month is only partly observed. "
    "Differencing does not remove this. Dividing by the number of observed days does. "
    "An interval that spans zero means no evidence of association."
)
st.dataframe(dashboard.correlation_table(panel, days=days).style.format(precision=3), hide_index=True)
fig = px.scatter(panel, x="new_cases", y="sales", trendline="ols", template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

st.header("2. Does approval rate differ by loan purpose?")
rates = dashboard.approval_rates(loans)
fig = px.scatter(
    rates,
    x="rate",
    y="Loan_Purpose",
    error_x=rates["ci_high"] - rates["rate"],
    error_x_minus=rates["rate"] - rates["ci_low"],
    template="plotly_white",
    title="Approval rate with Wilson 95% intervals",
)
fig.update_layout(xaxis_tickformat=".0%", xaxis_title="Approval rate", yaxis_title=None)
st.plotly_chart(fig, use_container_width=True)
chi = stats.chi2_independence(loans, "Loan_Purpose", "Approved")
st.write(
    f"Chi-square test of independence: χ² = {chi.statistic:.2f}, dof = {chi.extra['dof'] if chi.extra else '?'}, "
    f"p = {chi.p_value:.3f}; bias-corrected Cramér's V = {chi.effect_size:.3f}."
)

st.header("3. Does income differ between approved and rejected applicants?")
approved = loans.loc[loans["Approved"] == "Yes", "Income"]
rejected = loans.loc[loans["Approved"] == "No", "Income"]
perm = stats.permutation_test_means(approved, rejected, n_resamples=4999)
st.write(
    f"Permutation test on the difference in mean income: Δ = ${perm.statistic:,.0f}, p = {perm.p_value:.3f}, "
    f"Hedges' g = {perm.effect_size:.3f}."
)
st.info(
    "The bundled data is synthetic with independently drawn columns, so null results are the expected, "
    "correct outcome. See docs/DATA_CARD.md."
)
