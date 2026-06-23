import pytest
import pandas as pd
from utils.filters import (
    apply_month_filter,
    apply_location_filter,
    apply_location_group_filter,
    apply_service_type_filter,
    apply_advisor_filter,
    split_cp_pp
)

@pytest.fixture
def dummy_df():
    return pd.DataFrame({
        "Month Name": ["Jan", "Feb", "Mar", "Jan"],
        "Location Name": ["Loc A", "Loc B", "Loc A", "Loc C"],
        "Location Group": ["Arena", "Nexa", "Arena", "Other"],
        "Service Type": ["Running Repair", "Bodyshop", "Free Service", "Running Repair"],
        "Advisor": ["Adv 1", "Adv 2", "Adv 1", "Adv 3"],
        "Service_Type_Group": ["WS", "BS", "WS", "WS"],
        "Value": [10, 20, 30, 40]
    })

def test_apply_month_filter(dummy_df):
    res = apply_month_filter(dummy_df, "Month Name", ["Jan"])
    assert len(res) == 2
    assert res["Value"].sum() == 50

    res2 = apply_month_filter(dummy_df, "Month Name", [])
    assert len(res2) == 0 # Empty list means empty df

def test_apply_location_filter(dummy_df):
    res = apply_location_filter(dummy_df, "Location Name", ["Loc A"])
    assert len(res) == 2
    assert res["Value"].sum() == 40

def test_apply_location_group_filter(dummy_df):
    res = apply_location_group_filter(dummy_df, "Location Group", ["Arena"])
    assert len(res) == 2
    assert res["Value"].sum() == 40

def test_apply_service_type_filter(dummy_df):
    res = apply_service_type_filter(dummy_df, "Service Type", ["Bodyshop"])
    assert len(res) == 1
    assert res["Value"].sum() == 20

def test_apply_advisor_filter(dummy_df):
    res = apply_advisor_filter(dummy_df, "Advisor", ["Adv 1", "Adv 3"])
    assert len(res) == 3
    assert res["Value"].sum() == 80



def test_split_cp_pp(dummy_df):
    cp, pp = split_cp_pp(dummy_df, "Month Name", ["Mar"], ["Feb"])
    assert len(cp) == 1
    assert cp["Value"].iloc[0] == 30
    assert len(pp) == 1
    assert pp["Value"].iloc[0] == 20
