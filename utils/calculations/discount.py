import pandas as pd
from typing import Union, Dict
from utils.calculations.fact_metrics import (
    get_labour_discount, get_parts_discount, get_labour_sales, get_parts_sales, get_jobcard_count
)
from utils.calculations.revenue import calculate_gross_revenue
from utils.calculations.common import calc_ratio, calc_growth_pct





def calculate_total_discount(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Calculates combined labour and parts discount."""
    return get_labour_discount(df, aggregate) + get_parts_discount(df, aggregate)

def calculate_labour_discount_pct(df: pd.DataFrame) -> float:
    """Calculates labour discount percentage over gross labour revenue."""
    disc = get_labour_discount(df, aggregate=True)
    rev = get_labour_sales(df, aggregate=True)
    return float(calc_ratio(disc, rev, multiplier=100.0, fill_value=0.0))

def calculate_parts_discount_pct(df: pd.DataFrame) -> float:
    """Calculates parts discount percentage over gross parts revenue."""
    disc = get_parts_discount(df, aggregate=True)
    rev = get_parts_sales(df, aggregate=True)
    return float(calc_ratio(disc, rev, multiplier=100.0, fill_value=0.0))

def calculate_overall_discount_pct(df: pd.DataFrame) -> float:
    """Calculates overall discount percentage over total gross revenue."""
    disc = calculate_total_discount(df, aggregate=True)
    rev = calculate_gross_revenue(df, aggregate=True)
    return float(calc_ratio(disc, rev, multiplier=100.0, fill_value=0.0))

def calculate_discount_per_jobcard(df: pd.DataFrame) -> float:
    """Calculates average discount amount per job card."""
    disc = calculate_total_discount(df, aggregate=True)
    jcs = get_jobcard_count(df, aggregate=True)
    return float(calc_ratio(disc, jcs, fill_value=0.0))

def calculate_discount_growth(cp: pd.DataFrame, pp: pd.DataFrame) -> float:
    """Calculates growth percentage of total discount between current and prior period."""
    cp_disc = calculate_total_discount(cp, aggregate=True)
    pp_disc = calculate_total_discount(pp, aggregate=True)
    return float(calc_growth_pct(cp_disc, pp_disc, fill_value=0.0))

def calculate_discount_kpis(cp: pd.DataFrame, pp: pd.DataFrame) -> Dict[str, float]:
    """Calculates a comprehensive set of discount KPIs for comparison."""
    cp_lab_disc = float(get_labour_discount(cp, aggregate=True))
    pp_lab_disc = float(get_labour_discount(pp, aggregate=True))
    lab_growth = float(calc_growth_pct(cp_lab_disc, pp_lab_disc, fill_value=0.0))
    
    cp_parts_disc = float(get_parts_discount(cp, aggregate=True))
    pp_parts_disc = float(get_parts_discount(pp, aggregate=True))
    parts_growth = float(calc_growth_pct(cp_parts_disc, pp_parts_disc, fill_value=0.0))
    
    cp_lab_pct = calculate_labour_discount_pct(cp)
    pp_lab_pct = calculate_labour_discount_pct(pp)
    
    cp_overall_pct = calculate_overall_discount_pct(cp)
    pp_overall_pct = calculate_overall_discount_pct(pp)
    
    return {
        "Total Discount": cp_lab_disc + cp_parts_disc,
        "PP Total Discount": pp_lab_disc + pp_parts_disc,
        "Labour Discount": cp_lab_disc,
        "PP Labour Discount": pp_lab_disc,
        "Labour YoY Growth %": lab_growth,
        "Parts Discount": cp_parts_disc,
        "PP Parts Discount": pp_parts_disc,
        "Parts YoY Growth %": parts_growth,
        "Labour Discount %": cp_lab_pct,
        "PP Labour Discount %": pp_lab_pct,
        "Overall Discount %": cp_overall_pct,
        "PP Overall Discount %": pp_overall_pct
    }
