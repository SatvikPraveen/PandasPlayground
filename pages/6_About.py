"""About this dashboard."""

import streamlit as st

import scripts  # noqa: F401
from pandasplayground import __version__

st.title("About PandasPlayground")
st.markdown(
    f"""
Version **{__version__}**.

This dashboard sits on top of a tested Python package (`pandasplayground`) and a deterministic pipeline:

- **Sales trends** and **Profit insights** plot the monthly panel built by `pandasplayground pipeline`.
- **Statistical inference** reports interval estimates and effect sizes rather than bare p-values.
- **Data quality** runs the same schema checks that CI enforces.

Every number here can be regenerated from the raw files in `data/` with:

```bash
pandasplayground validate && pandasplayground pipeline
```

All data is synthetic. See `docs/DATA_CARD.md` for its generating process and limitations,
and `docs/METHODOLOGY.md` for the statistical and benchmarking methods.
"""
)
