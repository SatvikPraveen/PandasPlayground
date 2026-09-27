from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, settings

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EXPORTS = ROOT / "exports"

settings.register_profile("ci", max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
settings.register_profile("dev", max_examples=50, deadline=None)
settings.load_profile("dev")


@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(12345)


@pytest.fixture
def sales_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_date": pd.to_datetime(
                ["2024-01-05", "2024-01-20", "2024-02-03", "2024-02-28", "2024-03-15", "2024-03-16"]
            ),
            "region": ["East", "West", "East", "West", "East", "East"],
            "sales": [100.0, 200.0, 150.0, 50.0, 300.0, 10.0],
            "profit": [10.0, -5.0, 20.0, 5.0, 30.0, 1.0],
        }
    )
