import pytest
import pandas as pd
import numpy as np
from utils.calculations.revenue import calculate_net_revenue, calculate_total_revenue, calculate_revenue_growth
from utils.calculations.margin import calculate_total_margin, calculate_margin_kpis
from utils.calculations.discount import calculate_labour_discount, calculate_labour_discount_pct, calculate_overall_discount_pct
from utils.calculations.common import calc_ratio, calc_growth_pct

@pytest.fixture
def dummy_cp():
    return pd.DataFrame({
        "Net_Labour": [1000, 2000],
        "Net_Parts": [3000, 4000],
        "Total Margin": [500, 1000],
        "Labour Discount": [100, 200],
        "Parts Discount": [50, 150],
        "Pre-GST Labour": [1100, 2200],
        "Pre-GST Parts": [3050, 4150],
        "JC_Nos.": [2, 3]
    })

@pytest.fixture
def dummy_pp():
    return pd.DataFrame({
        "Net_Labour": [800, 1500],
        "Net_Parts": [2500, 3500],
        "Total Margin": [400, 800],
        "Labour Discount": [50, 100],
        "Parts Discount": [20, 80],
        "Pre-GST Labour": [850, 1600],
        "Pre-GST Parts": [2520, 3580],
        "JC_Nos.": [1, 2]
    })

def test_revenue_calculations(dummy_cp):
    net_rev = calculate_net_revenue(dummy_cp)
    assert net_rev == 10500  # Pre-GST Labour (3300) + Pre-GST Parts (7200)
    
    total_rev = calculate_total_revenue(dummy_cp)
    # Total revenue currently equals Net Revenue in the function
    assert total_rev == net_rev

def test_margin_calculations(dummy_cp):
    mar = calculate_total_margin(dummy_cp)
    assert mar == 1500

def test_discount_calculations(dummy_cp):
    lab_disc = calculate_labour_discount(dummy_cp)
    assert lab_disc == 300
    
    lab_disc_pct = calculate_labour_discount_pct(dummy_cp)
    assert round(lab_disc_pct, 2) == round((300 / 3300) * 100, 2)
    
    overall_pct = calculate_overall_discount_pct(dummy_cp)
    assert round(overall_pct, 2) == round(((300 + 200) / (3300 + 7200)) * 100, 2)

def test_growth_kpis(dummy_cp, dummy_pp):
    cp_rev = calculate_net_revenue(dummy_cp) # 10500
    pp_rev = calculate_net_revenue(dummy_pp) # 8550
    
    rev_growth = calculate_revenue_growth(dummy_cp, dummy_pp)
    assert round(rev_growth, 2) == round(((10500 - 8550) / 8550) * 100, 2)

def test_leakage_calculations(dummy_cp):
    # Leakage calculations generally look at discounts over a threshold
    from utils.calculations.leakage import compute_discount_aggregates
    # Create a simple df for leakage
    df = pd.DataFrame({
        "Location Name": ["Loc A", "Loc A"],
        "Pre-GST Labour": [1000, 2000],
        "Labour Discount": [200, 500] # 20% and 25% discounts
    })
    res = compute_discount_aggregates(df, "Location Name", benchmark=15.0)
    assert len(res) == 1
    # Total Labour = 3000, Total Discount = 700 (23.3%)
    # Expected leakage = (23.33% - 15%) of 3000 = 8.33% of 3000 = 250
    assert "Recoverable" in res.columns
    assert abs(res["Recoverable"].iloc[0] - 250) < 1.0

def test_common_math():
    from utils.calculations.common import calc_ratio, calc_growth_pct, calc_achievement_pct, calc_variance
    assert calc_ratio(10, 20) == 0.5
    assert np.isnan(calc_ratio(10, 0, fill_value=np.nan))
    
    assert calc_growth_pct(150, 100) == 50.0
    assert calc_growth_pct(100, 0, fill_value=0) == 0
    
    assert round(calc_achievement_pct(90, 100), 2) == 90.0
    assert round(calc_achievement_pct(110, 100), 2) == 110.0
    assert calc_achievement_pct(10, 0, fill_value=0) == 0
    
    assert calc_variance(90, 100) == -10
    assert calc_variance(110, 100) == 10
