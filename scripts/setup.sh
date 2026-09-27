#!/usr/bin/env bash
# One-shot development setup: virtualenv, dependencies, and a verification run.
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON=${PYTHON:-python3}
if ! "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "Python 3.10+ is required (found $("$PYTHON" --version 2>&1))." >&2
    exit 1
fi

if [ ! -d .venv ]; then
    echo "Creating virtual environment in .venv"
    "$PYTHON" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip --quiet
echo "Installing dependencies (this can take a few minutes)"
pip install -r requirements_dev.txt --quiet

echo "Verifying installation"
pandasplayground validate
pytest -m "not slow" -q

cat <<'MSG'

Setup complete. Next steps:
  source .venv/bin/activate
  make help            # list all tasks
  make run-jupyter     # open the notebooks
  make reproduce       # rebuild every output and check nothing drifts
MSG
