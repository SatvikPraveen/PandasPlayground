from __future__ import annotations

import pandas as pd
import pytest

from pandasplayground import aggregation as agg


def test_groupby_summary(sales_frame):
    out = agg.groupby_summary(sales_frame, "region", {"sales": "sum"})
    assert dict(zip(out["region"], out["sales"], strict=True)) == {"East": 560.0, "West": 250.0}


def test_groupby_summary_missing_key(sales_frame):
    with pytest.raises(KeyError):
        agg.groupby_summary(sales_frame, "nope", {"sales": "sum"})


def test_compute_approval_rate_case_insensitive_with_counts():
    df = pd.DataFrame({"region": ["E", "E", "W"], "approved": ["Yes", "no", " YES "]})
    out = agg.compute_approval_rate(df).set_index("region")
    assert out.loc["E", "approval_rate"] == 0.5
    assert out.loc["W", "approval_rate"] == 1.0
    assert out.loc["E", "n"] == 2


def test_resample_monthly_does_not_mutate(sales_frame):
    before = sales_frame.copy()
    out = agg.resample_monthly(sales_frame, "order_date", {"sales": "sum"})
    pd.testing.assert_frame_equal(sales_frame, before)
    assert out["sales"].tolist() == [300.0, 200.0, 310.0]
    assert out["order_date"].dt.is_month_end.all()


def test_monthly_period_summary(sales_frame):
    out = agg.monthly_period_summary(sales_frame, "order_date", {"profit": "sum"})
    assert out["month"].tolist() == ["2024-01", "2024-02", "2024-03"]
    assert out["profit"].tolist() == [5.0, 25.0, 31.0]


def test_pivot_melt_roundtrip(sales_frame):
    wide = agg.pivot_table_summary(sales_frame, "region", "order_date", "sales", "sum")
    long = agg.melt_summary(wide, "region", "order_date", "sales").dropna()
    assert long["sales"].sum() == pytest.approx(sales_frame["sales"].sum())


def test_stacked_groupby_unstack(sales_frame):
    out = agg.stacked_groupby_unstack(
        sales_frame.assign(m=sales_frame.order_date.dt.month), ["m", "region"], "sales", "region"
    )
    assert out.loc[1, "East"] == 100.0
    assert out.loc[3, "West"] == 0


def test_rolling_rank(sales_frame):
    out = agg.rolling_rank(sales_frame, "region", "sales", window=2)
    east = out[out.region == "East"]["rolling_rank_sales"].tolist()
    # East sales in date order: 100, 150, 300, 10 -> rank of latest within trailing 2 (descending)
    assert east == [1.0, 1.0, 1.0, 2.0]


def test_grouped_eval_share(sales_frame):
    out = agg.grouped_eval(sales_frame, "region", "sales", "region_total", "sum")
    assert (out.loc[out.region == "West", "region_total"] == 250.0).all()
