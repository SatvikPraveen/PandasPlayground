"""Seeded synthetic data generation for the bundled datasets.

The generator is a faithful, parameterised port of the original ``generate_mock_data.py`` and
consumes NumPy's legacy global random stream in exactly the same order. With the default
``seed=42`` and ``n_rows=10_000`` it reproduces every numeric, categorical and date column of the
committed files bit-for-bit. Person names come from Faker, which the original script did not
seed; they are now seeded too, so future regenerations are fully deterministic.

Known properties of the synthetic data (see ``docs/DATA_CARD.md``):

* All variables are drawn independently; there is no causal or correlational structure to find.
* Each "daily" series has one row per day for ``n_rows`` consecutive days (2020-2047 by default).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from pandasplayground.config import DEFAULT_SEED

logger = logging.getLogger(__name__)

WEATHER_CONDITIONS = ["Sunny", "Rain", "Cloudy", "Storm", "Snow"]
LOAN_PURPOSES = ["Car", "Home", "Education", "Business", "Medical", "Vacation"]
APPROVALS = ["Yes", "No"]
COUNTRIES = ["USA", "India", "Brazil", "Germany", "Canada"]
VARIANTS = ["Alpha", "Delta", "Omicron", "BA.5", "XBB"]
LOAN_REGIONS = ["East", "West", "North", "South"]
STORE_REGIONS = ["East", "West", "Central", "South"]
SEGMENTS = ["Consumer", "Corporate", "Home Office"]
PRODUCT_CATALOGUE = {
    "Furniture": ["Bookcases", "Chairs", "Tables"],
    "Office Supplies": ["Binders", "Pens", "Paper", "Labels"],
    "Technology": ["Phones", "Accessories", "Copiers", "Machines"],
}


@dataclass(frozen=True)
class SyntheticData:
    weather: pd.DataFrame
    loans: pd.DataFrame
    covid: pd.DataFrame
    superstore: pd.DataFrame


def generate(n_rows: int = 10_000, seed: int = DEFAULT_SEED) -> SyntheticData:
    """Generate all synthetic datasets in memory."""
    try:
        from faker import Faker

        Faker.seed(seed)
        fake: Faker | None = Faker()
    except ImportError:
        fake = None

    def names(n: int, prefix: str) -> list[str]:
        if fake is None:
            return [f"{prefix} {i}" for i in range(n)]
        return [fake.name() for _ in range(n)]

    # NOTE: the draw order below mirrors the original script so the legacy stream is reproduced.
    np.random.seed(seed)  # noqa: NPY002 - intentional, for bit-for-bit reproducibility

    dates = pd.date_range(start="2022-01-01", periods=n_rows)
    weather = pd.DataFrame(
        [
            {
                "date": str(d.date()),
                "temperature_c": np.random.randint(-10, 40),  # noqa: NPY002
                "humidity": np.random.randint(30, 100),  # noqa: NPY002
                "condition": np.random.choice(WEATHER_CONDITIONS),  # noqa: NPY002
            }
            for d in dates
        ]
    )

    loans = pd.DataFrame(
        {
            "Customer_ID": range(1001, 1001 + n_rows),
            "Customer_Name": names(n_rows, "Customer"),
            "Age": np.random.randint(21, 65, size=n_rows),  # noqa: NPY002
            "Income": np.random.randint(25000, 150000, size=n_rows),  # noqa: NPY002
            "Loan_Amount": np.random.randint(3000, 80000, size=n_rows),  # noqa: NPY002
            "Loan_Purpose": np.random.choice(LOAN_PURPOSES, size=n_rows),  # noqa: NPY002
            "Approved": np.random.choice(APPROVALS, size=n_rows),  # noqa: NPY002
        }
    )

    covid = pd.DataFrame(
        {
            "date": pd.date_range(start="2020-01-01", periods=n_rows).astype("datetime64[ns]"),
            "country": np.random.choice(COUNTRIES, size=n_rows),  # noqa: NPY002
            "variant": np.random.choice(VARIANTS, size=n_rows),  # noqa: NPY002
            "new_cases": np.random.poisson(500, size=n_rows),  # noqa: NPY002
            "new_deaths": np.random.poisson(10, size=n_rows),  # noqa: NPY002
            "hospitalized": np.random.randint(0, 5000, size=n_rows),  # noqa: NPY002
        }
    )

    products = [
        (cat, sub, f"{sub} Model {i + 1}") for cat, subs in PRODUCT_CATALOGUE.items() for sub in subs for i in range(5)
    ]
    superstore = pd.DataFrame(
        {
            "Order ID": [f"ORD-{i + 10000}" for i in range(n_rows)],
            "Customer ID": [f"CUST-{np.random.randint(1000, 9999)}" for _ in range(n_rows)],  # noqa: NPY002
            "Customer Name": names(n_rows, "Shopper"),
            "Segment": np.random.choice(SEGMENTS, size=n_rows),  # noqa: NPY002
            "Region": np.random.choice(STORE_REGIONS, size=n_rows),  # noqa: NPY002
            "Order Date": pd.date_range(start="2020-01-01", periods=n_rows),
            "Ship Date": pd.date_range(start="2020-01-03", periods=n_rows),
        },
        dtype=str,
    )
    sampled = [products[i % len(products)] for i in range(n_rows)]
    superstore["Category"] = [c for c, _, _ in sampled]
    superstore["Sub-Category"] = [s for _, s, _ in sampled]
    superstore["Product Name"] = [p for _, _, p in sampled]
    superstore["Sales"] = np.round(np.random.uniform(10.0, 2000.0, size=n_rows), 2)  # noqa: NPY002
    superstore["Quantity"] = np.random.randint(1, 10, size=n_rows)  # noqa: NPY002
    superstore["Discount"] = np.round(np.random.choice([0.0, 0.1, 0.2, 0.3, 0.5], size=n_rows), 2)  # noqa: NPY002
    superstore["Profit"] = np.round(superstore["Sales"] * (0.05 + np.random.randn(n_rows) * 0.05), 2)  # noqa: NPY002

    return SyntheticData(weather=weather, loans=loans, covid=covid, superstore=superstore)


def write_all(data: SyntheticData, out_dir: Path) -> list[Path]:
    """Persist generated data using the same file names and formats as ``data/``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    weather_path = out_dir / "weather_data.json"
    weather_path.write_text(json.dumps(data.weather.to_dict(orient="records"), indent=2, default=int))
    paths.append(weather_path)

    loans_path = out_dir / "bank_loans.xlsx"
    data.loans.to_excel(loans_path, index=False)
    paths.append(loans_path)

    covid_path = out_dir / "covid_data.parquet"
    data.covid.to_parquet(covid_path, index=False)
    paths.append(covid_path)

    multi_path = out_dir / "bank_loans_multisheet.xlsx"
    with pd.ExcelWriter(multi_path) as writer:
        for region in LOAN_REGIONS:
            data.loans.assign(Region=region).to_excel(writer, sheet_name=region, index=False)
    paths.append(multi_path)

    store_path = out_dir / "superstore_sales.csv"
    data.superstore.to_csv(store_path, index=False)
    paths.append(store_path)

    for p in paths:
        logger.info("Wrote %s", p)
    return paths
