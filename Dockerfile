# syntax=docker/dockerfile:1
# Reproducible environment for PandasPlayground: package, CLI, notebooks and dashboard.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies first to maximise layer caching.
COPY pyproject.toml README.md ./
COPY src/pandasplayground/__init__.py src/pandasplayground/__init__.py
RUN pip install ".[viz,app,datagen,notebooks,perf]" && pip uninstall -y pandasplayground

# Copy the project and install the package itself (no dependency resolution needed).
COPY . .
RUN pip install --no-deps -e . \
    && useradd --create-home --uid 1000 analyst \
    && chown -R analyst:analyst /app
USER analyst

EXPOSE 8888 8501

# Default: JupyterLab. Override with e.g. `docker run ... pandasplayground pipeline`
# or `docker run -p 8501:8501 ... streamlit run STREAMLIT_App.py --server.address=0.0.0.0`.
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--ServerApp.root_dir=/app"]
