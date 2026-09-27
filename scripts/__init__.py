"""Backwards-compatibility layer for the original ``scripts.*`` helpers used by the notebooks.

New code should import from :mod:`pandasplayground` directly. This package makes the notebooks
work whether or not the project has been ``pip install``-ed, by falling back to ``src/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import pandasplayground
except ImportError:  # running from a fresh clone without `pip install -e .`
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
