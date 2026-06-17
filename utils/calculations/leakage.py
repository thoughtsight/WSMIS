import pandas as pd
import numpy as np
from typing import Union
from utils.calculations.fact_metrics import (
    get_labour_sales, get_labour_discount, get_parts_sales, get_parts_discount
)
from utils.calculations.common import calc_ratio

def compute_discount_aggregates(df: pd.DataFrame, group_col: str, benchmark: float = 15.0) -> pd.DataFrame:
    """Computes labour discount aggregations over a grouping column to identify recoverable leakage."""
    if df.empty or group_col not in df.columns:
        return pd.DataFrame()
        
    lab_sales = get_labour_sales(df, aggregate=False)
    lab_disc = get_labour_discount(df, aggregate=False)
    
    temp_df = pd.DataFrame({
        group_col: df[group_col],
        'Revenue': lab_sales,
        'DiscRs': lab_disc
    })
    
    g = temp_df.groupby(group_col, dropna=False).sum().reset_index()
    g["Disc_Pct"] = calc_ratio(g["DiscRs"], g["Revenue"], multiplier=100.0, fill_value=0.0)
    g["Recoverable"] = np.maximum(0, (g["Disc_Pct"] - benchmark) / 100.0 * g["Revenue"])
    return g

def compute_parts_leakage(df: pd.DataFrame, group_col: str, benchmark: float = 10.0) -> pd.DataFrame:
    """Computes parts discount aggregations over a grouping column to identify recoverable leakage."""
    if df.empty or group_col not in df.columns:
        return pd.DataFrame()
        
    parts_sales = get_parts_sales(df, aggregate=False)
    parts_disc = get_parts_discount(df, aggregate=False)
    
    temp_df = pd.DataFrame({
        group_col: df[group_col],
        'Revenue': parts_sales,
        'DiscRs': parts_disc
    })
    
    g = temp_df.groupby(group_col, dropna=False).sum().reset_index()
    g["Disc_Pct"] = calc_ratio(g["DiscRs"], g["Revenue"], multiplier=100.0, fill_value=0.0)
    g["Recoverable"] = np.maximum(0, (g["Disc_Pct"] - benchmark) / 100.0 * g["Revenue"])
    return g

def compute_leakage_delta(cp: pd.DataFrame, pp: pd.DataFrame, group_col: str, benchmark: float = 15.0) -> pd.DataFrame:
    """Computes the delta in discount leakage between current and prior periods for a specified grouping column."""
    cp_lkg = compute_discount_aggregates(cp, group_col, benchmark)
    if cp_lkg.empty:
        return pd.DataFrame()
    pp_lkg = compute_discount_aggregates(pp, group_col, benchmark) if not pp.empty else pd.DataFrame()
    if pp_lkg.empty:
        cp_lkg["PP_Recoverable"] = 0.0
        cp_lkg["Delta_Pct"] = 0.0
        cp_lkg["Leakage_Delta"] = 0.0
        return cp_lkg
    merged = cp_lkg.merge(
        pp_lkg[[group_col, "Disc_Pct", "Recoverable"]], on=group_col, suffixes=("", "_PP"), how="left"
    ).fillna(0)
    merged["Delta_Pct"] = merged["Disc_Pct"] - merged["Disc_Pct_PP"]
    merged["Leakage_Delta"] = merged["Recoverable"] - merged["Recoverable_PP"]
    merged.rename(columns={"Recoverable_PP": "PP_Recoverable"}, inplace=True)
    return merged
