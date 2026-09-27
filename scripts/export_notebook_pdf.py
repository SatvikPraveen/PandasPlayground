"""Export a notebook to PDF via nbconvert (requires a LaTeX install such as TeX Live / MacTeX).

Usage:
    python scripts/export_notebook_pdf.py [NOTEBOOK] [--out-dir exports]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebook", nargs="?", default="notebooks/09_reporting_exporting.ipynb")
    parser.add_argument("--out-dir", default="exports")
    args = parser.parse_args(argv)

    notebook, out_dir = Path(args.notebook), Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["jupyter", "nbconvert", "--to", "pdf", "--output-dir", str(out_dir), str(notebook)]
    try:
        subprocess.run(cmd, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"PDF export failed: {exc}\nTip: install xelatex (TeX Live / MacTeX) and nbconvert.", file=sys.stderr)
        return 1
    print(f"Exported {notebook} to {out_dir / notebook.with_suffix('.pdf').name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
