import pytest
import pandas as pd
from utils.filters import (
    apply_month_filter,
    apply_location_filter,
    apply_location_group_filter,
    apply_service_type_filter,
    apply_advisor_filter,
    apply_mp_pb_filter,
    split_cp_pp
)

@pytest.fixture
def dummy_df():
    return pd.DataFrame({
        "Month Name": ["Jan", "Feb", "Mar", "Jan"],
        "Location Name": ["Loc A", "Loc B", "Loc A", "Loc C"],
        "Model Group": ["Arena", "Nexa", "Arena", "Other"],
        "Service Type": ["Running Repair", "Bodyshop", "Free Service", "Running Repair"],
        "Advisor": ["Adv 1", "Adv 2", "Adv 1", "Adv 3"],
        "MP_PB": ["MP", "PB", "MP", "MP"],
        "Value": [10, 20, 30, 40]
    })

def test_apply_month_filter(dummy_df):
    res = apply_month_filter(dummy_df, "Month Name", ["Jan"])
    assert len(res) == 2
    assert res["Value"].sum() == 50

    res2 = apply_month_filter(dummy_df, "Month Name", [])
    assert len(res2) == 4 # Empty list means no filter

def test_apply_location_filter(dummy_df):
    res = apply_location_filter(dummy_df, "Location Name", ["Loc A"])
    assert len(res) == 2
    assert res["Value"].sum() == 40

def test_apply_location_group_filter(dummy_df):
    res = apply_location_group_filter(dummy_df, "Model Group", ["Arena"])
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

def test_apply_mp_pb_filter(dummy_df):
    res_ws = apply_mp_pb_filter(dummy_df, "MP_PB", "MP")
    assert len(res_ws) == 3
    
    res_bs = apply_mp_pb_filter(dummy_df, "MP_PB", "PB")
    assert len(res_bs) == 1
    
    res_all = apply_mp_pb_filter(dummy_df, "MP_PB", "All")
    assert len(res_all) == 4

def test_split_cp_pp(dummy_df):
    cp, pp = split_cp_pp(dummy_df, "Month Name", ["Mar"], ["Feb"])
    assert len(cp) == 1
    assert cp["Value"].iloc[0] == 30
    assert len(pp) == 1
    assert pp["Value"].iloc[0] == 20
