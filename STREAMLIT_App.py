"""PandasPlayground dashboard: home page with KPIs and trends over a selectable month range."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

import scripts  # noqa: F401  (makes the package importable from a fresh clone)
from pandasplayground import dashboard

st.set_page_config(page_title="PandasPlayground", layout="wide", initial_sidebar_state="expanded")


@st.cache_data
def load() -> pd.DataFrame:
    return dashboard.load_panel()


try:
    panel = load()
except FileNotFoundError:
    st.error("exports/final_merged_pipeline.csv not found. Build it with `pandasplayground pipeline`.")
    st.stop()

st.title("PandasPlayground dashboard")
st.caption(
    "Monthly retail sales joined to monthly COVID indicators, rebuilt deterministically from raw data by "
    "`pandasplayground pipeline`. All data is synthetic."
)

# ---------------------------------------------------------------- filters
months = panel["month"].dt.to_pydatetime().tolist()
start, end = st.sidebar.select_slider(
    "Month range",
    options=months,
    value=(months[0], months[-1]),
    format_func=lambda d: d.strftime("%b %Y"),
)
view = dashboard.filter_months(panel, pd.Timestamp(start), pd.Timestamp(end))
st.sidebar.metric("Months selected", len(view))

# ---------------------------------------------------------------- KPIs
k = dashboard.kpis(view)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total sales", f"${k.total_sales:,.0f}")
c2.metric("Total profit", f"${k.total_profit:,.0f}")
c3.metric("Profit margin", f"{k.profit_margin:.1%}")
c4.metric("New cases", f"{k.total_cases:,}")
c5.metric("Mean daily hospitalised", f"{k.mean_hospitalized:,.0f}")

# ---------------------------------------------------------------- trends
left, right = st.columns(2)
with left:
    fig = px.line(view, x="month", y="sales", markers=True, template="plotly_white", title="Monthly sales")
    fig.update_layout(yaxis_title="Sales ($)", xaxis_title=None, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
with right:
    fig = px.line(
        view.melt(id_vars="month", value_vars=["profit", "rolling_profit"], var_name="series"),
        x="month",
        y="value",
        color="series",
        template="plotly_white",
        title="Monthly profit and 3-month rolling mean",
    )
    fig.update_layout(yaxis_title="Profit ($)", xaxis_title=None, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Data")
st.dataframe(view, use_container_width=True, hide_index=True)
