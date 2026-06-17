import pandas as pd
from typing import Union, Dict
from utils.calculations.fact_metrics import (
    get_total_margin, get_parts_profit, get_jobcard_count
)
from utils.calculations.revenue import calculate_net_revenue
from utils.calculations.common import calc_ratio, calc_growth_pct

def calculate_total_margin(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Calculates total margin across all categories."""
    return get_total_margin(df, aggregate)

def calculate_parts_margin(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Calculates total parts margin."""
    return get_parts_profit(df, aggregate)

def calculate_margin_per_jobcard(df: pd.DataFrame) -> float:
    """Calculates average margin per job card."""
    mar = calculate_total_margin(df, aggregate=True)
    jcs = get_jobcard_count(df, aggregate=True)
    return float(calc_ratio(mar, jcs, fill_value=0.0))

def calculate_margin_growth(cp: pd.DataFrame, pp: pd.DataFrame) -> float:
    """Calculates total margin growth percentage."""
    cp_mar = calculate_total_margin(cp, aggregate=True)
    pp_mar = calculate_total_margin(pp, aggregate=True)
    return float(calc_growth_pct(cp_mar, pp_mar, fill_value=0.0))

def calculate_margin_kpis(cp: pd.DataFrame, pp: pd.DataFrame) -> Dict[str, float]:
    """Returns a dictionary of key margin KPIs."""
    cp_mar = float(calculate_total_margin(cp, aggregate=True))
    pp_mar = float(calculate_total_margin(pp, aggregate=True))
    growth = float(calc_growth_pct(cp_mar, pp_mar, fill_value=0.0))
    
    cp_parts_mar = float(calculate_parts_margin(cp, aggregate=True))
    pp_parts_mar = float(calculate_parts_margin(pp, aggregate=True))
    parts_growth = float(calc_growth_pct(cp_parts_mar, pp_parts_mar, fill_value=0.0))
    
    return {
        "Total Margin": cp_mar,
        "PP Margin": pp_mar,
        "YoY Growth %": growth,
        "Parts Margin": cp_parts_mar,
        "PP Parts Margin": pp_parts_mar,
        "Parts YoY Growth %": parts_growth
    }
