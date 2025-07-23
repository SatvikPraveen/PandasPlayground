# scripts/optimize_memory.py

import pandas as pd

def optimize_dataframe(df: pd.DataFrame, category_cols=None, verbose=True) -> pd.DataFrame:
    """
    Optimize memory usage of a pandas DataFrame by:
    - Converting object columns to category (if specified)
    - Downcasting numeric columns where safe

    Parameters:
    - df (pd.DataFrame): The input DataFrame to optimize.
    - category_cols (List[str], optional): List of columns to convert to 'category' dtype.
    - verbose (bool): Whether to print memory usage before/after.

    Returns:
    - pd.DataFrame: Optimized DataFrame
    """
    import numpy as np

    if verbose:
        print("📦 Memory usage BEFORE optimization:")
        df.info(memory_usage="deep")

    df_optimized = df.copy()

    # 1. Convert specified columns to category
    if category_cols:
        for col in category_cols:
            if col in df_optimized.columns:
                df_optimized[col] = df_optimized[col].astype("category")

    # 2. Downcast numeric columns
    for col in df_optimized.select_dtypes(include=["int", "float"]).columns:
        col_min = df_optimized[col].min()
        col_max = df_optimized[col].max()
        if pd.api.types.is_integer_dtype(df_optimized[col]):
            df_optimized[col] = pd.to_numeric(df_optimized[col], downcast="integer")
        else:
            df_optimized[col] = pd.to_numeric(df_optimized[col], downcast="float")

    if verbose:
        print("\n✅ Memory usage AFTER optimization:")
        df_optimized.info(memory_usage="deep")

    return df_optimized
