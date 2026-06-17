import pandas as pd
from typing import Union
from utils.calculations.fact_metrics import (
    get_labour_sales, get_parts_sales, get_net_labour, get_net_parts, get_jobcard_count
)
from utils.calculations.common import calc_ratio, calc_growth_pct

def calculate_gross_revenue(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Calculates total gross revenue by summing Pre-GST Labour and Parts."""
    return get_labour_sales(df, aggregate) + get_parts_sales(df, aggregate)

def calculate_net_revenue(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Calculates total net revenue by summing Net_Labour and Net_Parts."""
    return get_net_labour(df, aggregate) + get_net_parts(df, aggregate)

def calculate_total_revenue(df: pd.DataFrame, use_net: bool = True, aggregate: bool = True) -> Union[float, pd.Series]:
    """Calculates either net or gross revenue based on flag."""
    return calculate_net_revenue(df, aggregate) if use_net else calculate_gross_revenue(df, aggregate)

def calculate_revenue_per_jobcard(df: pd.DataFrame, use_net: bool = True) -> float:
    """Calculates average revenue per job card."""
    rev = calculate_total_revenue(df, use_net=use_net, aggregate=True)
    jcs = get_jobcard_count(df, aggregate=True)
    return float(calc_ratio(rev, jcs, fill_value=0.0))

def calculate_revenue_growth(cp: pd.DataFrame, pp: pd.DataFrame, use_net: bool = True) -> float:
    """Calculates revenue growth percentage between current and prior periods."""
    cp_rev = calculate_total_revenue(cp, use_net=use_net, aggregate=True)
    pp_rev = calculate_total_revenue(pp, use_net=use_net, aggregate=True)
    return float(calc_growth_pct(cp_rev, pp_rev, fill_value=0.0))
