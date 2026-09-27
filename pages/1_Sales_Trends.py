"""Sales trends: levels, growth and seasonality."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

import scripts  # noqa: F401
from pandasplayground import dashboard

st.title("Sales trends")


@st.cache_data
def load() -> pd.DataFrame:
    return dashboard.load_panel()


panel = load()

fig = px.line(panel, x="month", y="sales", template="plotly_white", title="Monthly sales")
fig.update_layout(yaxis_title="Sales ($)", xaxis_title=None, hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

fig = px.bar(panel, x="month", y="sales_pct_change", template="plotly_white", title="Month-over-month growth")
fig.update_layout(yaxis_tickformat=".0%", yaxis_title="Change vs previous month", xaxis_title=None)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Seasonality check")
st.caption("Distribution of monthly sales by calendar month. Overlapping boxes mean no seasonal pattern.")
by_month = panel.assign(calendar_month=panel["month"].dt.strftime("%m %b"))
fig = px.box(by_month.sort_values("calendar_month"), x="calendar_month", y="sales", template="plotly_white")
fig.update_layout(xaxis_title=None, yaxis_title="Sales ($)")
st.plotly_chart(fig, use_container_width=True)
