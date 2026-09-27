"""Browse, search and download the monthly panel."""

from __future__ import annotations

import pandas as pd
import streamlit as st

import scripts  # noqa: F401
from pandasplayground import dashboard

st.title("Raw data")
st.caption("The monthly panel produced by the pipeline.")


@st.cache_data
def load() -> pd.DataFrame:
    return dashboard.load_panel()


df = load()
c1, c2 = st.columns(2)
c1.metric("Rows", f"{len(df):,}")
c2.metric("Columns", df.shape[1])

year_options = sorted(df["month"].dt.year.unique())
years = st.multiselect("Years", options=year_options, default=year_options[:3])
filtered = df[df["month"].dt.year.isin(years)] if years else df

st.dataframe(filtered, use_container_width=True, hide_index=True)
st.download_button(
    "Download filtered CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="final_merged_pipeline_filtered.csv",
    mime="text/csv",
)

st.subheader("Summary statistics")
st.dataframe(filtered.describe().T, use_container_width=True)
