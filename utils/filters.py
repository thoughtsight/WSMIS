import pandas as pd
from typing import List, Tuple, Optional

def apply_location_group_filter(df: pd.DataFrame, group_col: str, loc_groups: Optional[List[str]]) -> pd.DataFrame:
    """Filters a DataFrame by Location Group."""
    if loc_groups and group_col in df.columns:
        return df[df[group_col].isin(loc_groups)]
    return df

def apply_location_filter(df: pd.DataFrame, loc_col: str, locations: Optional[List[str]]) -> pd.DataFrame:
    """Filters a DataFrame by specific Locations."""
    if locations and loc_col in df.columns:
        return df[df[loc_col].isin(locations)]
    return df

def apply_service_type_filter(df: pd.DataFrame, svc_col: str, svc_types: Optional[List[str]]) -> pd.DataFrame:
    """Filters a DataFrame by Service Types."""
    if svc_types and svc_col in df.columns:
        return df[df[svc_col].isin(svc_types)]
    return df

def apply_advisor_filter(df: pd.DataFrame, adv_col: str, advisors: Optional[List[str]]) -> pd.DataFrame:
    """Filters a DataFrame by Advisors."""
    if advisors and adv_col in df.columns:
        return df[df[adv_col].isin(advisors)]
    return df

def apply_ws_bs_filter(df: pd.DataFrame, ws_bs_col: str, ws_bs_val: Optional[str]) -> pd.DataFrame:
    """Filters a DataFrame by WS/BS flag."""
    if ws_bs_val and ws_bs_val != "All" and ws_bs_col in df.columns:
        return df[df[ws_bs_col] == ws_bs_val]
    return df

def apply_month_filter(df: pd.DataFrame, month_col: str, months: Optional[List[str]]) -> pd.DataFrame:
    """Filters a DataFrame by a list of months."""
    if months and month_col in df.columns:
        return df[df[month_col].isin(months)]
    return df

def split_cp_pp(df: pd.DataFrame, month_col: str, cp_months: List[str], pp_months: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Splits a DataFrame into Current Period (CP) and Prior Period (PP) DataFrames."""
    cp = apply_month_filter(df, month_col, cp_months)
    pp = apply_month_filter(df, month_col, pp_months)
    return cp, pp
