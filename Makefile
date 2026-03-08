# ========================================
# 🛠️ Makefile for PandasPlayground
# ========================================
# Common development tasks automated

.PHONY: help install install-dev test clean run-jupyter run-streamlit docker-build docker-run lint format

# Default target
help:
	@echo "📊 PandasPlayground - Available Commands:"
	@echo ""
	@echo "  make install        - Install production dependencies"
	@echo "  make install-dev    - Install development dependencies"
	@echo "  make test           - Run all tests"
	@echo "  make lint           - Run code linting (flake8)"
	@echo "  make format         - Format code with black"
	@echo "  make clean          - Remove Python artifacts and cache"
	@echo "  make run-jupyter    - Start Jupyter Lab"
	@echo "  make run-streamlit  - Start Streamlit app"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-run     - Run Docker container"
	@echo ""

# Install dependencies
install:
	pip install --upgrade pip
	pip install -r requirements.txt

install-dev:
	pip install --upgrade pip
	pip install -r requirements_dev.txt

# Run tests
test:
	pytest -v

# Code quality
lint:
	flake8 scripts/ STREAMLIT_App.py pages/ --max-line-length=120

format:
	black scripts/ STREAMLIT_App.py pages/ --line-length=120
	isort scripts/ STREAMLIT_App.py pages/

# Clean artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true

# Run development servers
run-jupyter:
	jupyter lab --ip=0.0.0.0 --no-browser

run-streamlit:
	streamlit run STREAMLIT_App.py

# Docker commands
docker-build:
	docker build -t pandasplayground:latest .

docker-run:
	docker run -p 8899:8888 -v $$(pwd):/app pandasplayground:latest
