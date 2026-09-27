"""Profit: trend, margin and distribution."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

import scripts  # noqa: F401
from pandasplayground import dashboard, stats

st.title("Profit insights")


@st.cache_data
def load() -> pd.DataFrame:
    panel = dashboard.load_panel()
    return panel.assign(margin=panel["profit"] / panel["sales"])


panel = load()

fig = px.line(
    panel.melt(id_vars="month", value_vars=["profit", "rolling_profit"], var_name="series"),
    x="month",
    y="value",
    color="series",
    template="plotly_white",
    title="Monthly profit and 3-month rolling mean",
)
fig.update_layout(yaxis_title="Profit ($)", xaxis_title=None, hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

est = stats.bootstrap_ci(panel["margin"], n_resamples=4999)
st.metric("Mean monthly profit margin (95% BCa bootstrap CI)", f"{est.point:.2%}", help=str(est))
st.write(f"95% CI: {est.low:.2%} to {est.high:.2%}")

fig = px.histogram(panel, x="margin", nbins=40, template="plotly_white", title="Distribution of monthly margin")
fig.update_layout(xaxis_tickformat=".0%", xaxis_title="Profit / sales", yaxis_title="Months")
st.plotly_chart(fig, use_container_width=True)
