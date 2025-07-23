# 3_Raw_Data.py

import streamlit as st
import pandas as pd
from scripts import utils_io
from pathlib import Path

# ------------------------------------------------
# 📄 Page Title & Caption
# ------------------------------------------------
st.title("🧾 Raw Data Snapshot")
st.caption("Explore the cleaned and enriched dataset used throughout this dashboard.")

# ------------------------------------------------
# 📂 Load Data
# ------------------------------------------------
@st.cache_data
def load_data():
    df = utils_io.load_csv(Path("exports/final_merged_pipeline.csv"))
    return df

df = load_data()

# ------------------------------------------------
# 🧮 Summary Info
# ------------------------------------------------
st.markdown("---")
st.markdown("### 🔢 Dataset Overview")
col1, col2 = st.columns(2)
col1.metric("Rows", f"{df.shape[0]:,}")
col2.metric("Columns", f"{df.shape[1]}")

# ------------------------------------------------
# 🔍 Filters & Search
# ------------------------------------------------
st.markdown("---")
st.markdown("### 🎛️ Interactive Filters")

# Column selector for dropdown filter
categorical_columns = df.select_dtypes(include=["object", "category"]).columns.tolist()
selected_col = st.selectbox("📂 Filter by Column", options=["None"] + categorical_columns)

# Dropdown filter if column selected
filtered_df = df.copy()
if selected_col != "None":
    unique_vals = sorted(df[selected_col].dropna().unique())
    selected_val = st.selectbox(f"🔎 Select a value from '{selected_col}'", unique_vals)
    filtered_df = filtered_df[filtered_df[selected_col] == selected_val]

# Search filter (case-insensitive, across all columns)
search_query = st.text_input("🔍 Search keyword (across all text columns)")
if search_query:
    text_cols = filtered_df.select_dtypes(include=["object"]).columns
    mask = filtered_df[text_cols].apply(lambda col: col.str.contains(search_query, case=False, na=False))
    filtered_df = filtered_df[mask.any(axis=1)]

# ------------------------------------------------
# 📊 Display Data
# ------------------------------------------------
st.markdown("### 📋 Filtered Data Preview")

with st.expander("📌 Click to expand preview", expanded=True):
    st.dataframe(filtered_df.head(100), use_container_width=True)

# ------------------------------------------------
# 📥 Export Filtered Data
# ------------------------------------------------
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Download Filtered Data as CSV",
    data=csv,
    file_name="filtered_snapshot.csv",
    mime="text/csv"
)

# ------------------------------------------------
# 📝 Tip
# ------------------------------------------------
st.info("Use search and dropdowns to refine your view. Download the filtered result using the button above.")
