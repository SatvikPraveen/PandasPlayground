"""Live schema validation of every bundled dataset."""

from __future__ import annotations

import pandas as pd
import streamlit as st

import scripts  # noqa: F401
from pandasplayground import io, schemas
from pandasplayground.config import PATHS

st.title("Data quality")
st.caption("Each dataset is checked against the contract in `src/pandasplayground/schemas.py`.")


@st.cache_data
def run_validation() -> pd.DataFrame:
    rows = []
    for fname, schema in schemas.RAW_SCHEMAS.items():
        report = schema.validate(io.read(PATHS.data / fname))
        rows.append({"dataset": fname, "rows": report.n_rows, "passed": report.ok, "issues": len(report.failures)})
    export = PATHS.exports / "final_merged_pipeline.csv"
    report = schemas.FINAL_MERGED.validate(io.read(export))
    rows.append({"dataset": export.name, "rows": report.n_rows, "passed": report.ok, "issues": len(report.failures)})
    return pd.DataFrame(rows)


results = run_validation()
st.metric("Datasets passing", f"{int(results['passed'].sum())} / {len(results)}")
st.dataframe(results, use_container_width=True, hide_index=True)

with st.expander("Schema details"):
    for schema in schemas.ALL_SCHEMAS:
        st.markdown(f"#### `{schema.name}`\n\n{schema.description}\n\n{schema.to_markdown()}")
