# 1_Sales_Trends.py

import streamlit as st
import pandas as pd
import plotly.express as px
from scripts import utils_io
from pathlib import Path

st.title("📈 Monthly Sales Trend")

@st.cache_data
def load_data():
    df = utils_io.load_csv(Path("exports/final_merged_pipeline.csv"))
    df["month"] = pd.to_datetime(df["month"])  # ✅ Fix: parse existing 'month'
    return df

df = load_data()

monthly_sales = df.groupby("month")["sales"].sum().reset_index()

fig = px.line(
    monthly_sales,
    x="month",
    y="sales",
    title="Sales Over Time",
    markers=True,
    template="plotly_white"
)
fig.update_layout(
    xaxis_tickformat="%b %Y",
    yaxis_title="Sales ($)",
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)
