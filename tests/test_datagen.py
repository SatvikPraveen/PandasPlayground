from __future__ import annotations

import pandas as pd
import pytest

from pandasplayground import datagen, io, schemas

from .conftest import DATA


def test_generation_is_deterministic():
    a, b = datagen.generate(n_rows=50, seed=3), datagen.generate(n_rows=50, seed=3)
    for name in ("weather", "loans", "covid", "superstore"):
        pd.testing.assert_frame_equal(getattr(a, name), getattr(b, name))
    c = datagen.generate(n_rows=50, seed=4)
    assert not a.superstore["Sales"].equals(c.superstore["Sales"])


def test_generated_data_satisfies_schemas(tmp_path):
    paths = datagen.write_all(datagen.generate(n_rows=120, seed=1), tmp_path)
    assert len(paths) == 5
    for fname, schema in schemas.RAW_SCHEMAS.items():
        assert schema.validate(io.read(tmp_path / fname)).ok, fname


@pytest.mark.integration
def test_default_seed_reproduces_bundled_data():
    """The committed datasets are exactly reproducible from seed 42 (except unseeded Faker names)."""
    gen = datagen.generate()
    store = io.read(DATA / "superstore_sales.csv", dtype=str)
    cols = [c for c in store.columns if c != "Customer Name"]
    assert (gen.superstore[cols].astype(str).to_numpy() == store[cols].to_numpy()).all()

    loans = io.read(DATA / "bank_loans.xlsx")
    cols = [c for c in loans.columns if c != "Customer_Name"]
    pd.testing.assert_frame_equal(gen.loans[cols], loans[cols], check_dtype=False)

    covid = io.read(DATA / "covid_data.parquet")
    pd.testing.assert_frame_equal(gen.covid, covid, check_dtype=False)

    weather = io.read(DATA / "weather_data.json")
    pd.testing.assert_frame_equal(
        gen.weather.assign(date=pd.to_datetime(gen.weather["date"])), weather, check_dtype=False
    )
