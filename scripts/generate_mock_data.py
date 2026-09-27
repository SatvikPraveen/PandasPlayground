"""Regenerate the synthetic datasets. Equivalent to ``pandasplayground generate``.

Usage:
    python scripts/generate_mock_data.py [--out DIR] [--rows N] [--seed S] [--force]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pandasplayground.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["generate", *sys.argv[1:]]))
