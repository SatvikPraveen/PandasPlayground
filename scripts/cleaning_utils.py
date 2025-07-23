import pandas as pd
import numpy as np
from typing import List, Optional


def clean_dataframe(
    df: pd.DataFrame,
    drop_na_cols: Optional[List[str]] = None,
    dedupe: bool = True,
    clean_strings: bool = True
) -> pd.DataFrame:
    """
    Cleans a dataframe by:
    - Dropping rows with NA in specified columns
    - Removing duplicate rows
    - Stripping, lowering, and normalizing string/categorical columns
    """
    if drop_na_cols:
        df = df.dropna(subset=drop_na_cols)

    if clean_strings:
        string_cols = df.select_dtypes(include=['object', 'category']).columns
        for col in string_cols:
            df[col] = df[col].astype(str).str.strip().str.lower().str.replace(r"\s+", " ", regex=True)

    if dedupe:
        df = df.drop_duplicates()

    return df


def detect_outliers_iqr(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    Returns rows considered outliers in a given numeric column using the IQR method.
    """
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    return df[(df[col] < lower) | (df[col] > upper)]


def standardize_strings(df):
    """
    Strip whitespace and convert all string columns to lowercase.
    Useful for ensuring consistency in column values.
    """
    df_copy = df.copy()
    for col in df_copy.select_dtypes(include="object").columns:
        df_copy[col] = df_copy[col].str.strip().str.lower()
    return df_copy


def align_customer_ids(df):
    """
    Ensure customer_id column is of string type and trimmed.
    """
    df_copy = df.copy()
    if 'customer_id' in df_copy.columns:
        df_copy['customer_id'] = df_copy['customer_id'].astype(str).str.strip()
    return df_copy
