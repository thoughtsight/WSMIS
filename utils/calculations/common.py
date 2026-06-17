import pandas as pd
import numpy as np
from typing import Union, Any

def safe_divide(numerator: Union[float, int, pd.Series, pd.DataFrame], 
                denominator: Union[float, int, pd.Series, pd.DataFrame], 
                fill_value: float = 0.0) -> Union[float, pd.Series, pd.DataFrame]:
    """Safely divide series or scalars, returning fill_value on division by zero."""
    if isinstance(numerator, (pd.Series, pd.DataFrame)) or isinstance(denominator, (pd.Series, pd.DataFrame)):
        res = numerator / denominator
        return res.replace([np.inf, -np.inf], np.nan).fillna(fill_value)
    
    if denominator == 0 or pd.isna(denominator):
        return fill_value
    return numerator / denominator

def calc_ratio(numerator: Union[float, pd.Series], 
               denominator: Union[float, pd.Series], 
               multiplier: float = 1.0, 
               fill_value: float = 0.0) -> Union[float, pd.Series]:
    """Calculates ratio (e.g. percentage if multiplier=100)"""
    return safe_divide(numerator, denominator, fill_value) * multiplier

def calc_growth_pct(current: Union[float, pd.Series], 
                    prior: Union[float, pd.Series], 
                    fill_value: float = 0.0) -> Union[float, pd.Series]:
    """Calculates YoY or MoM growth percentage."""
    return safe_divide(current - prior, prior, fill_value) * 100

def calc_contribution_pct(part: Union[float, pd.Series], 
                          total: Union[float, pd.Series], 
                          fill_value: float = 0.0) -> Union[float, pd.Series]:
    """Calculates percentage contribution of a part to the whole."""
    return calc_ratio(part, total, multiplier=100.0, fill_value=fill_value)

def calc_achievement_pct(actual: Union[float, pd.Series], 
                         target: Union[float, pd.Series], 
                         fill_value: float = 0.0) -> Union[float, pd.Series]:
    """Calculates achievement percentage against a target."""
    return calc_ratio(actual, target, multiplier=100.0, fill_value=fill_value)

def calc_variance(current: Union[float, pd.Series], 
                  target: Union[float, pd.Series]) -> Union[float, pd.Series]:
    """Calculates absolute variance."""
    return current - target
