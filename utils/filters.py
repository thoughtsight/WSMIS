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

def apply_month_filter(df: pd.DataFrame, month_col: str, months: Optional[List[str]]) -> pd.DataFrame:
    """Filters a DataFrame by a list of months. If months is [], returns empty DataFrame."""
    if months is not None and month_col in df.columns:
        return df[df[month_col].isin(months)]
    return df

def split_cp_pp(df: pd.DataFrame, month_col: str, cp_months: List[str], pp_months: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Splits a DataFrame into Current Period (CP) and Prior Period (PP) DataFrames."""
    cp = apply_month_filter(df, month_col, cp_months)
    pp = apply_month_filter(df, month_col, pp_months)
    return cp, pp

def filter_valid_advisors(df: pd.DataFrame, adv_col: str = "Advisor Name") -> pd.DataFrame:
    """Filters out invalid advisors ('Unassigned') from the DataFrame for advisor-specific reports."""
    actual_col = adv_col if adv_col in df.columns else "Advisor"
    if actual_col in df.columns:
        return df[df[actual_col] != "Unassigned"]
    return df

def apply_global_filters(df: pd.DataFrame, 
                           locations: Optional[List[str]] = None, 
                           location_group: Optional[str] = None, 
                           service_type_group: Optional[str] = None,
                           svc_types: Optional[List[str]] = None, 
                           advisors: Optional[List[str]] = None) -> pd.DataFrame:
    """Applies multiple filters efficiently using a single boolean mask to avoid repeated DataFrame copies."""
    mask = pd.Series(True, index=df.index)
    
    if locations and 'Location Name' in df.columns:
        mask &= df['Location Name'].isin(locations)
        
    if location_group and location_group != "All" and 'Location_Group' in df.columns:
        mask &= df['Location_Group'] == location_group
        
    if service_type_group and service_type_group != "All" and 'Service_Type_Group' in df.columns:
        mask &= df['Service_Type_Group'] == service_type_group
        
    if svc_types and 'Service Type' in df.columns:
        mask &= df['Service Type'].isin(svc_types)
        
    if advisors:
        actual_col = "Advisor Name" if "Advisor Name" in df.columns else "Advisor"
        if actual_col in df.columns:
            mask &= df[actual_col].isin(advisors)
            
    return df[mask]
