# Contributing to PandasPlayground

Thanks for your interest. Contributions of notebooks, package features, tests, documentation and bug reports are welcome.

## Setup

```bash
git clone https://github.com/<your-fork>/PandasPlayground.git
cd PandasPlayground
./scripts/setup.sh && source .venv/bin/activate
pre-commit install
```

## Workflow

1. Create a branch: `git checkout -b feat/short-description`.
2. Make your change, with tests.
3. Run `make check`, which covers lint, format, types and fast tests. If you changed notebooks or data code, also run `make reproduce`.
4. Open a pull request using the template. CI must pass.

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `test:`,
`refactor:`, `perf:`, `ci:`, `build:`, `chore:`.

## Where code goes

- **Reusable logic** belongs in `src/pandasplayground/`. It must be typed, must not mutate its inputs, and needs tests in `tests/`.
- **`scripts/`** only re-exports package functions for older notebooks. Do not add new logic there.
- **Notebooks** should import from `pandasplayground` and run top to bottom from a clean kernel. CI executes them all.
  If a notebook writes a CSV to `assets/` or `exports/`, re-running it must reproduce the committed file exactly.
- **Streamlit pages** keep data logic in `pandasplayground.dashboard`, so it can be tested without Streamlit.

## Changing data or schemas

- Schemas in `src/pandasplayground/schemas.py` are the contract. After editing one, run
  `pandasplayground docs data-dictionary` and commit the regenerated `docs/DATA_DICTIONARY.md`.
- Never hand-edit files in `data/`. Change `datagen.py` and regenerate with `pandasplayground generate --out data --force`.
  Then update `docs/DATA_CARD.md` and explain why in the pull request.
- If a change intentionally alters `exports/final_merged_pipeline.csv`, run `pandasplayground pipeline` and commit the export
  and its manifest together.

## Statistical and performance claims

- Report intervals and effect sizes, not just p-values, and correct for multiple comparisons.
- Performance numbers in docs must come from `pandasplayground benchmark`, with the results JSON committed.

## Questions

Open an issue using the question template.
