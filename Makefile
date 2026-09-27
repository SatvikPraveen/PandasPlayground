# PandasPlayground developer tasks. Run `make help` for a list.
PY ?= python

.PHONY: help install install-dev lint format typecheck test test-all coverage notebooks validate pipeline \
        reproduce benchmark docs check clean run-jupyter run-streamlit docker-build docker-run

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install runtime + notebook + dashboard dependencies
	$(PY) -m pip install -r requirements.txt

install-dev: ## Install everything needed for development
	$(PY) -m pip install -r requirements_dev.txt
	pre-commit install

lint: ## Lint and check formatting
	ruff check src scripts tests pages STREAMLIT_App.py
	ruff format --check src scripts tests pages STREAMLIT_App.py

format: ## Auto-format and fix lint issues
	ruff check --fix src scripts tests pages STREAMLIT_App.py
	ruff format src scripts tests pages STREAMLIT_App.py

typecheck: ## Strict type-check the package
	mypy

test: ## Fast test suite
	pytest -m "not slow"

test-all: ## All tests, including slow statistical property tests
	pytest

coverage: ## Tests with an HTML coverage report
	pytest --cov --cov-report=term --cov-report=html

notebooks: ## Execute every notebook top to bottom
	pytest --nbmake --nbmake-timeout=900 notebooks -o addopts=""

validate: ## Validate all datasets against their schemas
	pandasplayground validate

pipeline: ## Rebuild the final export from raw data (+ provenance manifest)
	pandasplayground pipeline

reproduce: validate pipeline notebooks ## Full reproducibility check: exports must not change
	git diff --exit-code -- exports/final_merged_pipeline.csv '*.csv'

benchmark: ## Run the benchmark suite and refresh docs/benchmark_results.md
	pandasplayground benchmark --markdown docs/benchmark_results.md

docs: ## Regenerate code-derived documentation
	pandasplayground docs data-dictionary

check: lint typecheck test ## Everything CI's lint + test jobs run

clean: ## Remove caches and build artefacts
	find . -type d \( -name __pycache__ -o -name .ipynb_checkpoints \) -prune -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache .hypothesis htmlcov .coverage coverage.xml build dist *.egg-info src/*.egg-info runs

run-jupyter: ## Start JupyterLab
	jupyter lab --no-browser

run-streamlit: ## Start the Streamlit dashboard
	streamlit run STREAMLIT_App.py

docker-build: ## Build the Docker image
	docker build -t pandasplayground:latest .

docker-run: ## Run JupyterLab in Docker on http://localhost:8888
	docker run --rm -p 8888:8888 pandasplayground:latest
