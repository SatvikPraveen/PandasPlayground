# scripts/agg_utils.py

import pandas as pd

def groupby_summary(df, group_col, agg_dict, reset=True):
    """
    Perform grouped aggregation based on column and aggregation dictionary.

    Args:
        df (pd.DataFrame): The input dataframe.
        group_col (str or list): Column(s) to group by.
        agg_dict (dict): Dictionary of aggregations.
        reset (bool): Whether to reset index.

    Returns:
        pd.DataFrame: Aggregated dataframe.
    """
    result = df.groupby(group_col).agg(agg_dict)
    return result.reset_index() if reset else result


def compute_approval_rate(df, region_col="region", approval_col="approved", approval_value="yes"):
    """
    Calculate approval rate (as a proportion of 'yes') by region.

    Args:
        df (pd.DataFrame): Loan dataframe.
        region_col (str): Column with region.
        approval_col (str): Column indicating approval status.
        approval_value (str): Value that indicates approval.

    Returns:
        pd.DataFrame: Region-wise approval rate.
    """
    return (
        df.groupby(region_col)
        .agg(approval_rate=(approval_col, lambda x: (x == approval_value).mean()))
        .reset_index()
    )


def pivot_table_summary(df, index, columns, values, aggfunc="mean"):
    """
    Generate a pivot table.

    Args:
        df (pd.DataFrame): DataFrame to pivot.
        index (str or list): Index columns.
        columns (str or list): Columns to pivot across.
        values (str): Values to aggregate.
        aggfunc (str or func): Aggregation function.

    Returns:
        pd.DataFrame: Pivoted table.
    """
    return pd.pivot_table(df, index=index, columns=columns, values=values, aggfunc=aggfunc)


def resample_monthly(df, date_col, metrics_dict):
    """
    Resample a time series dataframe to monthly frequency using given metrics.

    Args:
        df (pd.DataFrame): Time-indexed DataFrame.
        date_col (str): Date column to convert and set as index.
        metrics_dict (dict): Columns and aggregation methods.

    Returns:
        pd.DataFrame: Monthly resampled aggregation.
    """
    df[date_col] = pd.to_datetime(df[date_col])
    df.set_index(date_col, inplace=True)
    result = df.resample("M").agg(metrics_dict).reset_index()
    df.reset_index(inplace=True)  # Restore original
    return result

# groupby_summary, compute_approval_rate, pivot_table_summary, resample_monthly

def melt_summary(df, id_vars, var_name, value_name):
    """
    Flatten a pivoted DataFrame using melt.

    Args:
        df (pd.DataFrame): The pivoted DataFrame.
        id_vars (str or list): Columns to keep fixed (e.g., 'region').
        var_name (str): Name for the melted variable column.
        value_name (str): Name for the melted value column.

    Returns:
        pd.DataFrame: Melted long-format DataFrame.
    """
    return df.reset_index().melt(id_vars=id_vars, var_name=var_name, value_name=value_name)


def stacked_groupby_unstack(df, group_cols, value_col, unstack_col, fill_value=0):
    """
    Perform grouped aggregation and unstack to wide format.

    Args:
        df (pd.DataFrame): Input DataFrame.
        group_cols (list): List of grouping columns (e.g., ['region', 'segment', 'category']).
        value_col (str): Column to aggregate (e.g., 'sales').
        unstack_col (str): Column to unstack (e.g., 'category').
        fill_value (int or float): Fill missing values.

    Returns:
        pd.DataFrame: Unstacked pivoted DataFrame.
    """
    return (
        df.groupby(group_cols)[value_col]
        .sum()
        .unstack(unstack_col, fill_value=fill_value)
    )


def resample_monthly(df, date_col, metrics_dict):
    """
    Resample a time series dataframe to monthly frequency using given metrics.

    Args:
        df (pd.DataFrame): Time-indexed DataFrame.
        date_col (str): Date column to convert and set as index.
        metrics_dict (dict): Columns and aggregation methods, e.g., {"sales": "sum"}.

    Returns:
        pd.DataFrame: Monthly resampled aggregation.
    """
    df[date_col] = pd.to_datetime(df[date_col])
    df.set_index(date_col, inplace=True)
    result = df.resample("M").agg(metrics_dict).reset_index()
    df.reset_index(inplace=True)  # Restore original index
    return result



def safe_merge(
    df1,
    df2,
    on,
    how="inner",
    suffixes=("_left", "_right"),
    parse_dates=False,
    verbose=True
):
    """
    Safely merge two DataFrames with checks and options.

    Parameters:
    -----------
    df1 : pd.DataFrame
        Left dataframe.
    df2 : pd.DataFrame
        Right dataframe.
    on : str or list
        Column(s) to join on.
    how : str, default="inner"
        Type of join: 'left', 'right', 'outer', 'inner'.
    suffixes : tuple, default=('_left', '_right')
        Suffixes for overlapping column names.
    parse_dates : bool, default=False
        Whether to convert merge keys to datetime.
    verbose : bool, default=True
        Print a confirmation of the merge.

    Returns:
    --------
    pd.DataFrame
        Merged DataFrame.
    """

    import pandas as pd

    if isinstance(on, str):
        on = [on]

    # Check keys exist in both
    missing_df1 = [col for col in on if col not in df1.columns]
    missing_df2 = [col for col in on if col not in df2.columns]
    
    if missing_df1 or missing_df2:
        raise KeyError(
            f"Missing keys -> df1: {missing_df1}, df2: {missing_df2}"
        )

    # Optional date parsing
    if parse_dates:
        for col in on:
            df1[col] = pd.to_datetime(df1[col], errors="coerce")
            df2[col] = pd.to_datetime(df2[col], errors="coerce")

    # Perform merge
    merged = pd.merge(df1, df2, on=on, how=how, suffixes=suffixes)

    if verbose:
        print(f"✅ Merged on {on} using '{how}' join — shape: {merged.shape}")

    return merged


def safe_concat(
    dfs,
    axis=0,
    ignore_index=True,
    check_columns=True,
    verbose=True
):
    """
    Safely concatenates a list of DataFrames with optional column consistency checks.

    Parameters:
    -----------
    dfs : list of pd.DataFrame
        The list of DataFrames to concatenate.
    axis : int, default=0
        Axis to concatenate along: 0 for row-wise, 1 for column-wise.
    ignore_index : bool, default=True
        Whether to reset the index in the resulting DataFrame.
    check_columns : bool, default=True
        If True, validates that all DataFrames have matching columns (for axis=0).
    verbose : bool, default=True
        If True, prints a success message with shape info.

    Returns:
    --------
    pd.DataFrame
        Concatenated DataFrame.

    Raises:
    -------
    ValueError
        If `check_columns` is True and any DataFrame has mismatched columns.

    Example:
    --------
    >>> df_all = safe_concat([df1, df2], check_columns=True)
    """

    if check_columns:
        all_cols = [set(df.columns) for df in dfs]
        base = all_cols[0]
        for idx, cols in enumerate(all_cols[1:], 1):
            if cols != base:
                raise ValueError(f"❌ Column mismatch between df0 and df{idx}")

    concatenated = pd.concat(dfs, axis=axis, ignore_index=ignore_index)

    if verbose:
        print(f"✅ Concatenated {len(dfs)} DataFrames — shape: {concatenated.shape}")

    return concatenated


def check_merge_key_overlap(df1, df2):
    """
    Returns common columns that can be used as potential merge keys.
    """
    return list(set(df1.columns).intersection(set(df2.columns)))

def rolling_rank(df, group_col, value_col, window, ascending=False, rank_method="average"):
    """
    Apply a rolling rank to a value column within each group.
    Returns the original dataframe with a new column: f"rolling_rank_{value_col}".
    """
    new_col = f"rolling_rank_{value_col}"
    df = df.sort_values(by=[group_col, "order_date"])
    df[new_col] = (
        df
        .groupby(group_col)[value_col]
        .rolling(window, min_periods=1)
        .apply(lambda x: x.rank(method=rank_method, ascending=ascending).iloc[-1])
        .reset_index(level=0, drop=True)
    )
    return df

def grouped_eval(df, group_cols, target_col, new_col, func):
    """
    Apply a transformation function to a target column within groups.
    Adds a new column with the computed values.
    """
    df = df.copy()
    df[new_col] = (
        df.groupby(group_cols)[target_col]
        .transform(func)
    )
    return df


def safe_merge(df1, df2, on, how="inner", suffixes=("_x", "_y"), parse_dates=False, verbose=False):
    """
    Merge two DataFrames with safety checks and optional verbose output.
    Ensures key alignment and can handle date parsing.
    """
    # Ensure columns exist
    for df, name in [(df1, "df1"), (df2, "df2")]:
        for key in ([on] if isinstance(on, str) else on):
            if key not in df.columns:
                raise KeyError(f"{key} not found in {name}")

    # Coerce types
    for key in ([on] if isinstance(on, str) else on):
        if df1[key].dtype != df2[key].dtype:
            if verbose:
                print(f"Aligning key dtype for {key}")
            df2[key] = df2[key].astype(df1[key].dtype)

    if parse_dates:
        for key in ([on] if isinstance(on, str) else on):
            df1[key] = pd.to_datetime(df1[key], errors="coerce")
            df2[key] = pd.to_datetime(df2[key], errors="coerce")

    result = df1.merge(df2, on=on, how=how, suffixes=suffixes)
    if verbose:
        print(f"✅ Merged on {on} using '{how}' join — shape: {result.shape}")
    return result