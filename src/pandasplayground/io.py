"""Format-aware I/O helpers with directory creation and content hashing."""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

PathLike = str | Path

_READERS: dict[str, Callable[..., Any]] = {
    ".csv": pd.read_csv,
    ".tsv": lambda p, **kw: pd.read_csv(p, sep="\t", **kw),
    ".json": pd.read_json,
    ".parquet": pd.read_parquet,
    ".xlsx": pd.read_excel,
    ".xls": pd.read_excel,
    ".feather": pd.read_feather,
    ".pkl": pd.read_pickle,
}

SUPPORTED_FORMATS = tuple(sorted(_READERS))


def _ensure_parent(path: PathLike) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def read(path: PathLike, **kwargs: Any) -> pd.DataFrame:
    """Read a tabular file, dispatching on its extension.

    CSV/TSV floats are parsed with ``float_precision="round_trip"`` so that reading and re-writing
    a file reproduces it exactly on every platform.

    Raises:
        FileNotFoundError: if ``path`` does not exist.
        ValueError: if the extension is not supported.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    reader = _READERS.get(p.suffix.lower())
    if p.suffix.lower() in {".csv", ".tsv"}:
        # pandas' default fast float parser is not guaranteed to round-trip the last digit, and its
        # rounding can differ across CPU architectures. Exact parsing makes read -> write byte-stable.
        kwargs.setdefault("float_precision", "round_trip")
    if reader is None:
        raise ValueError(f"Unsupported file format {p.suffix!r}; expected one of {SUPPORTED_FORMATS}")
    df = reader(p, **kwargs)
    if not isinstance(df, pd.DataFrame):  # e.g. read_excel(sheet_name=None) returns a dict
        raise TypeError(f"Reader for {p.suffix} returned {type(df).__name__}; use the format-specific loader instead")
    logger.debug("Loaded %s with shape %s", p, df.shape)
    return df


def write(df: pd.DataFrame, path: PathLike, *, index: bool = False, **kwargs: Any) -> Path:
    """Write ``df`` to ``path`` using the format implied by its extension, creating parent directories."""
    out = _ensure_parent(path)
    suffix = out.suffix.lower()
    if suffix == ".csv":
        df.to_csv(out, index=index, **kwargs)
    elif suffix == ".tsv":
        df.to_csv(out, sep="\t", index=index, **kwargs)
    elif suffix == ".parquet":
        df.to_parquet(out, index=index, **kwargs)
    elif suffix in {".xlsx", ".xls"}:
        df.to_excel(out, index=index, engine="openpyxl", **kwargs)
    elif suffix == ".json":
        df.to_json(out, orient=kwargs.pop("orient", "records"), date_format="iso", indent=2, **kwargs)
    elif suffix == ".feather":
        df.reset_index(drop=not index).to_feather(out, **kwargs)
    else:
        raise ValueError(f"Unsupported file format {suffix!r}")
    logger.info("Wrote %s rows to %s", len(df), out)
    return out


def sha256_file(path: PathLike, chunk_size: int = 1 << 20) -> str:
    """Return the SHA-256 hex digest of a file's bytes."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def frame_fingerprint(df: pd.DataFrame) -> str:
    """Return an order-sensitive SHA-256 fingerprint of a DataFrame's content, index and columns.

    Unlike file hashes this is independent of serialisation details (float formatting, compression),
    which makes it suitable for asserting that two pipeline runs produced identical results.
    """
    digest = hashlib.sha256()
    digest.update(repr(list(df.columns)).encode())
    digest.update(repr([str(t) for t in df.dtypes]).encode())
    digest.update(pd.util.hash_pandas_object(df, index=True).to_numpy().tobytes())
    return digest.hexdigest()


# ---------------------------------------------------------------------------
# Thin, explicit loaders kept for readability in notebooks
# ---------------------------------------------------------------------------


def load_csv(path: PathLike, **kwargs: Any) -> pd.DataFrame:
    return read(Path(path).with_suffix(".csv") if Path(path).suffix == "" else path, **kwargs)


def load_excel(path: PathLike, sheet_name: str | int | list[str | int] | None = 0, **kwargs: Any) -> Any:
    """Load an Excel workbook. ``sheet_name=None`` returns a ``dict`` of all sheets."""
    if not Path(path).exists():
        raise FileNotFoundError(path)
    return pd.read_excel(path, sheet_name=sheet_name, **kwargs)


def load_json(path: PathLike, **kwargs: Any) -> pd.DataFrame:
    return read(path, **kwargs)


def load_parquet(path: PathLike, **kwargs: Any) -> pd.DataFrame:
    return read(path, **kwargs)


def save_csv(df: pd.DataFrame, path: PathLike, index: bool = False) -> Path:
    return write(df, path, index=index)


def save_parquet(df: pd.DataFrame, path: PathLike, index: bool = False) -> Path:
    return write(df, path, index=index)


def save_excel(df: pd.DataFrame, path: PathLike, index: bool = False) -> Path:
    return write(df, path, index=index)
