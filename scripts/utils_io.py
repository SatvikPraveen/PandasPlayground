"""Legacy I/O helpers. Prefer :mod:`pandasplayground.io`."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

import scripts
from pandasplayground.io import (
    load_csv,
    load_excel,
    load_json,
    load_parquet,
    read,
    save_csv,
    save_excel,
    save_parquet,
    sha256_file,
    write,
)


def load_dataset_summary(df: pd.DataFrame, name: str = "Dataset") -> pd.DataFrame:
    print(f"{name}: shape={df.shape}")
    print("Columns:", list(df.columns))
    return df.head()


def save_plot(fig: Any, output_path: str | Path) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    return out


def export_styled_excel(df: pd.DataFrame, path: str | Path, style_func: Any = None) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    styled = style_func(df) if style_func else df.style
    styled.to_excel(out, engine="openpyxl")
    return out


def export_csv(df: pd.DataFrame, path: str | Path) -> Path:
    out = write(df, Path(path))
    print(f"Exported CSV to: {out}")
    return out


def export_excel(df: pd.DataFrame, path: str | Path) -> Path:
    out = write(df, Path(path).with_suffix(".xlsx") if Path(path).suffix == "" else Path(path))
    print(f"Exported Excel to: {out}")
    return out
