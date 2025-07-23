# 2_Profit_Insights.py

import streamlit as st
import pandas as pd
import plotly.express as px
from scripts import utils_io
from pathlib import Path

st.title("💰 Monthly Profit Trend")

@st.cache_data
def load_data():
    df = utils_io.load_csv(Path("exports/final_merged_pipeline.csv"))
    df["month"] = pd.to_datetime(df["month"])  # ✅ Fix: parse existing 'month'
    return df

df = load_data()

monthly_profit = df.groupby("month")["profit"].sum().reset_index()

fig = px.line(
    monthly_profit,
    x="month",
    y="profit",
    title="Profit Over Time",
    markers=True,
    template="plotly_white"
)
fig.update_layout(
    xaxis_tickformat="%b %Y",
    yaxis_title="Profit ($)",
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)
