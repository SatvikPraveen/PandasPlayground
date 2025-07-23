# streamlit_app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from scripts import utils_io

# ------------------------------------------------
# 📌 Page Config
# ------------------------------------------------
st.set_page_config(
    page_title="PandasPlayground Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 PandasPlayground Interactive Dashboard")
st.markdown("Explore trends, correlations, and filtered insights from the cleaned and merged datasets used across the pipeline.")

# ------------------------------------------------
# 📂 Load Final Dataset
# ------------------------------------------------
DATA_PATH = Path("exports/final_merged_pipeline.csv")

@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    try:
        df = utils_io.load_csv(path)
        df["month"] = pd.to_datetime(df["month"])  # ✅ Fix: parse existing 'month'
        return df
    except Exception as e:
        st.error(f"🚨 Failed to load data: {e}")
        return pd.DataFrame()

df = load_data(DATA_PATH)

if df.empty:
    st.stop()

# ------------------------------------------------
# 🔧 Sidebar Filters
# ------------------------------------------------
st.sidebar.title("🔧 Filter Options")

# Filter by month (non-destructive)
df_filtered = df.copy()
if "month" in df.columns:
    month_options = sorted(df["month"].dropna().unique())
    selected_month = st.sidebar.selectbox("📅 Select Month", options=month_options)
    df_filtered = df[df["month"] == selected_month]


# ------------------------------------------------
# 📊 KPI Cards
# ------------------------------------------------
st.markdown("---")
st.markdown("### 📌 Key Performance Indicators")

total_sales = df["sales"].sum()
total_profit = df["profit"].sum()
total_cases = df["new_cases"].sum()
avg_hospitalized = df["hospitalized"].mean()

col1, col2, col3, col4 = st.columns(4)
col1.metric("🛒 Total Sales", f"${total_sales:,.0f}")
col2.metric("💵 Total Profit", f"${total_profit:,.0f}")
col3.metric("🦠 Total New Cases", f"{total_cases:,}")
col4.metric("🏥 Avg. Hospitalized", f"{avg_hospitalized:,.0f}")

# ------------------------------------------------
# 📈 Monthly Sales Trend (Unfiltered)
# ------------------------------------------------
st.subheader("📈 Monthly Sales Trend")
fig = px.line(
    df,
    x="month", y="sales",
    title="Sales Over Time",
    markers=True,
    template="plotly_white"
)
fig.update_layout(xaxis_tickformat="%b %Y", yaxis_title="Sales ($)", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------
# 💰 Monthly Profit Trend (Unfiltered)
# ------------------------------------------------
st.subheader("💰 Monthly Profit Trend")
fig2 = px.line(
    df,
    x="month", y="profit",
    title="Profit Over Time",
    markers=True,
    template="plotly_white"
)
fig2.update_layout(xaxis_tickformat="%b %Y", yaxis_title="Profit ($)", hovermode="x unified")
st.plotly_chart(fig2, use_container_width=True)

# ------------------------------------------------
# 🧪 Raw Data Preview
# ------------------------------------------------
st.subheader("🧾 Raw Data Snapshot")
st.dataframe(df_filtered.head(10), use_container_width=True)

# ------------------------------------------------
# 🧠 Future Ideas
# ------------------------------------------------
st.markdown("---")
st.markdown("### 💡 Future Enhancements")
st.markdown("""
- Add multi-category filtering (e.g., Region, Segment)
- Use interactive widgets like `st.slider`, `st.multiselect`
- Add summary KPIs using `st.metric`
- Schedule pipeline using cron jobs or Airflow
- Turn this into a full reporting system with export buttons
- Embed anomaly detection charts and insights
""")
