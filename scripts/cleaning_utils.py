"""Legacy cleaning helpers. Prefer :mod:`pandasplayground.cleaning`."""

import scripts
from pandasplayground.cleaning import (
    align_customer_ids,
    clean_dataframe,
    detect_outliers,
    detect_outliers_iqr,
    missingness_report,
    normalize_column_names,
    standardize_strings,
)
