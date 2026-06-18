import pytest
import pandas as pd
from utils.aggregations import (
    location_summary,
    advisor_summary,
    monthly_summary,
    service_summary,
    pivot_summary,
    top_n
)

@pytest.fixture
def dummy_df():
    return pd.DataFrame({
        "Location Name": ["Loc A", "Loc A", "Loc B"],
        "Advisor": ["Adv 1", "Adv 2", "Adv 1"],
        "Month Name": ["Jan", "Feb", "Jan"],
        "Month_Sort": [1, 2, 1],
        "Service Type": ["MP", "PB", "MP"],
        "Value": [10, 20, 30]
    })

def test_location_summary(dummy_df):
    # With kwargs -> returns DataFrame
    res = location_summary(dummy_df, as_index=False, Total=("Value", "sum"))
    assert len(res) == 2
    loc_a = res[res["Location Name"] == "Loc A"]["Total"].iloc[0]
    loc_b = res[res["Location Name"] == "Loc B"]["Total"].iloc[0]
    assert loc_a == 30
    assert loc_b == 30

def test_advisor_summary(dummy_df):
    res = advisor_summary(dummy_df, as_index=True, Total=("Value", "sum"))
    assert "Adv 1" in res.index
    assert res.loc["Adv 1", "Total"] == 40
    assert res.loc["Adv 2", "Total"] == 20

def test_monthly_summary(dummy_df):
    res = monthly_summary(dummy_df, as_index=False, Total=("Value", "sum"))
    assert len(res) == 2
    # Should be sorted by Month_Sort
    assert res["Month Name"].iloc[0] == "Jan"
    assert res["Total"].iloc[0] == 40
    assert res["Total"].iloc[1] == 20

def test_service_summary(dummy_df):
    res = service_summary(dummy_df, as_index=False, Total=("Value", "sum"))
    assert len(res) == 2
    assert res[res["Service Type"] == "MP"]["Total"].iloc[0] == 40

def test_pivot_summary(dummy_df):
    res = pivot_summary(dummy_df, index="Location Name", columns="Service Type", values="Value")
    assert "Location Name" in res.columns
    assert "MP" in res.columns
    assert res[res["Location Name"] == "Loc A"]["MP"].iloc[0] == 10
    assert res[res["Location Name"] == "Loc A"]["PB"].iloc[0] == 20

def test_top_n(dummy_df):
    res = top_n(dummy_df, group_cols="Location Name", metric_col="Value", n=1)
    assert len(res) == 1
    # Both A and B sum to 30, so any one is fine.
    assert res["Value"].iloc[0] == 30
