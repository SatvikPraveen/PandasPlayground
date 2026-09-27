"""Command-line interface: ``pandasplayground <command>``.

Commands:
    validate     Validate the bundled datasets (or any file) against their schemas.
    pipeline     Run the end-to-end pipeline and write the export + provenance manifest.
    generate     Regenerate the synthetic datasets from a seed.
    benchmark    Run the micro-benchmark suite and write JSON (+ optional Markdown).
    docs         Regenerate documentation derived from code (the data dictionary).
    info         Print environment and package versions.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from pandasplayground import __version__
from pandasplayground.config import DEFAULT_SEED, PATHS

logger = logging.getLogger("pandasplayground")


def _cmd_validate(args: argparse.Namespace) -> int:
    import pandas as pd

    from pandasplayground import io, schemas

    failed = 0
    data_dir = Path(args.data_dir)
    targets: list[tuple[str, pd.DataFrame, schemas.DataFrameSchema]] = []
    for fname, schema in schemas.RAW_SCHEMAS.items():
        targets.append((fname, io.read(data_dir / fname), schema))
    multi = data_dir / "bank_loans_multisheet.xlsx"
    if multi.exists():
        for sheet, frame in pd.read_excel(multi, sheet_name=None).items():
            targets.append((f"{multi.name}[{sheet}]", frame, schemas.BANK_LOANS_REGIONAL))
    export = Path(args.export)
    if export.exists():
        targets.append((export.name, io.read(export), schemas.FINAL_MERGED))

    for label, frame, schema in targets:
        report = schema.validate(frame)
        print(f"{'PASS' if report.ok else 'FAIL'}  {label:<40} {len(frame):>7,} rows")
        if not report.ok:
            failed += 1
            for failure in report.failures:
                print(f"      - {failure}")
    print(f"\n{len(targets) - failed}/{len(targets)} datasets passed validation.")
    return 1 if failed else 0


def _cmd_pipeline(args: argparse.Namespace) -> int:
    from pandasplayground.pipeline import PipelineConfig, run_pipeline

    cfg = PipelineConfig(data_dir=Path(args.data_dir), output_path=Path(args.output), rolling_window=args.window)
    result = run_pipeline(cfg)
    print(f"Wrote {len(result.frame)} rows to {cfg.output_path}")
    print(f"Manifest: {cfg.resolved_manifest_path}")
    print("Output fingerprint:", result.manifest.outputs[0].fingerprint)
    return 0


def _cmd_generate(args: argparse.Namespace) -> int:
    from pandasplayground.datagen import generate, write_all

    out = Path(args.out)
    if out.resolve() == PATHS.data.resolve() and not args.force:
        print("Refusing to overwrite the bundled data/ directory without --force.", file=sys.stderr)
        return 2
    paths = write_all(generate(n_rows=args.rows, seed=args.seed), out)
    for p in paths:
        print(f"Wrote {p}")
    return 0


def _cmd_benchmark(args: argparse.Namespace) -> int:
    from pandasplayground.benchmark import run_suite

    run = run_suite(n_rows=args.rows, repeat=args.repeat, seed=args.seed)
    out = run.write_json(Path(args.out))
    print(run.to_markdown())
    print(f"\nRaw results written to {out}")
    if args.markdown:
        md = Path(args.markdown)
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(run.to_markdown() + "\n")
        print(f"Markdown table written to {md}")
    return 0


DATA_DICTIONARY_HEADER = """# Data Dictionary

> **Generated file.** Do not edit by hand. It is rendered from the schemas in
> `src/pandasplayground/schemas.py` with `pandasplayground docs data-dictionary`,
> and CI fails if it drifts from them. The same schemas are enforced at runtime
> by `pandasplayground validate` and by the pipeline.

All datasets are **synthetic**. See [DATA_CARD.md](DATA_CARD.md) for how they were generated and their limitations.
"""


def render_data_dictionary() -> str:
    from pandasplayground import schemas

    sections = [DATA_DICTIONARY_HEADER]
    for schema in schemas.ALL_SCHEMAS:
        sections.append(f"## `{schema.name}`\n\n{schema.description}\n\n{schema.to_markdown()}\n")
    return "\n".join(sections)


def _cmd_docs(args: argparse.Namespace) -> int:
    target = Path(args.out)
    content = render_data_dictionary()
    if args.check:
        current = target.read_text() if target.exists() else ""
        if current != content:
            print(f"{target} is out of date. Run: pandasplayground docs data-dictionary", file=sys.stderr)
            return 1
        print(f"{target} is up to date.")
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    print(f"Wrote {target}")
    return 0


def _cmd_info(_: argparse.Namespace) -> int:
    from pandasplayground.provenance import environment_info, git_state

    print(json.dumps({"version": __version__, "environment": environment_info(), "git": git_state()}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pandasplayground", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="enable debug logging")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="validate datasets against their schemas")
    p.add_argument("--data-dir", default=str(PATHS.data))
    p.add_argument("--export", default=str(PATHS.exports / "final_merged_pipeline.csv"))
    p.set_defaults(func=_cmd_validate)

    p = sub.add_parser("pipeline", help="run the end-to-end pipeline")
    p.add_argument("--data-dir", default=str(PATHS.data))
    p.add_argument("--output", default=str(PATHS.exports / "final_merged_pipeline.csv"))
    p.add_argument("--window", type=int, default=3, help="rolling window (months) for rolling_profit")
    p.set_defaults(func=_cmd_pipeline)

    p = sub.add_parser("generate", help="regenerate synthetic datasets")
    p.add_argument("--out", default=str(PATHS.runs / "generated"))
    p.add_argument("--rows", type=int, default=10_000)
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--force", action="store_true", help="allow overwriting the bundled data/ directory")
    p.set_defaults(func=_cmd_generate)

    p = sub.add_parser("benchmark", help="run the benchmark suite")
    p.add_argument("--rows", type=int, default=100_000)
    p.add_argument("--repeat", type=int, default=7)
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--out", default=str(PATHS.root / "benchmarks" / "results" / "latest.json"))
    p.add_argument("--markdown", default=None, help="also write the results table to this Markdown file")
    p.set_defaults(func=_cmd_benchmark)

    p = sub.add_parser("docs", help="regenerate code-derived documentation")
    p.add_argument("target", choices=["data-dictionary"])
    p.add_argument("--out", default=str(PATHS.root / "docs" / "DATA_DICTIONARY.md"))
    p.add_argument("--check", action="store_true", help="exit non-zero if the file is out of date")
    p.set_defaults(func=_cmd_docs)

    p = sub.add_parser("info", help="print environment information")
    p.set_defaults(func=_cmd_info)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING, format="%(levelname)s %(name)s: %(message)s"
    )
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
