import pandas as pd
from pathlib import Path

import matplotlib.pyplot as plt

def load_csv(filepath, **kwargs):
    return pd.read_csv(filepath, **kwargs)

def load_excel(filepath, sheet_name=0, **kwargs):
    return pd.read_excel(filepath, sheet_name=sheet_name, **kwargs)

def load_json(filepath, **kwargs):
    return pd.read_json(filepath, **kwargs)

def load_parquet(filepath, **kwargs):
    return pd.read_parquet(filepath, **kwargs)

def save_csv(df, output_path, index=False):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=index)

def save_parquet(df, output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path)


def load_dataset_summary(df, name="Dataset"):
    print(f"📊 {name} — shape: {df.shape}")
    print("🔸 Columns:", list(df.columns))
    print("🔸 Sample:")
    return df.head()

def save_plot(fig, output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches='tight')

def export_styled_excel(df, path: str, style_func=None):
    styled = style_func(df) if style_func else df.style
    styled.to_excel(path, engine="openpyxl")

def export_csv(df: pd.DataFrame, path: str):
    """Export DataFrame to CSV and create directories if needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"✅ Exported CSV to: {path}")

def export_excel(df: pd.DataFrame, path: str):
    """Export DataFrame to Excel and create directories if needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(path, index=False, engine="openpyxl")
    print(f"✅ Exported Excel to: {path}")
