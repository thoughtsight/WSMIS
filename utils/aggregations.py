import pandas as pd
from typing import List, Union, Dict, Any, Optional

from services import aggregation_cache
from utils.profiler import profiler

@profiler.measure_agg("group_summary")
def group_summary(df: pd.DataFrame, group_cols: Union[str, List[str]], as_index: bool = False, dropna: bool = False, **kwargs) -> Union[pd.DataFrame, pd.core.groupby.DataFrameGroupBy]:
    return aggregation_cache.group_summary(df, group_cols, as_index=as_index, dropna=dropna, **kwargs)

@profiler.measure_agg("location_summary")
def location_summary(df: pd.DataFrame, loc_col: str = "Location Name", as_index: bool = False, dropna: bool = False, **kwargs) -> Union[pd.DataFrame, pd.core.groupby.DataFrameGroupBy]:
    if loc_col == "Location Name":
        return aggregation_cache.get_location_summary(df, as_index=as_index, dropna=dropna, **kwargs)
    return aggregation_cache.group_summary(df, loc_col, as_index=as_index, dropna=dropna, **kwargs)

@profiler.measure_agg("advisor_summary")
def advisor_summary(df: pd.DataFrame, adv_col: str = "Advisor", as_index: bool = False, dropna: bool = False, **kwargs) -> Union[pd.DataFrame, pd.core.groupby.DataFrameGroupBy]:
    if adv_col in ("Advisor", "Advisor Name"):
        return aggregation_cache.get_advisor_summary(df, as_index=as_index, dropna=dropna, **kwargs)
    return aggregation_cache.group_summary(df, adv_col, as_index=as_index, dropna=dropna, **kwargs)

@profiler.measure_agg("monthly_summary")
def monthly_summary(df: pd.DataFrame, month_cols: List[str] = ["Month_Sort", "Month Name"], as_index: bool = False, dropna: bool = False, sort_col: str = "Month_Sort", **kwargs) -> Union[pd.DataFrame, pd.core.groupby.DataFrameGroupBy]:
    if month_cols == ["Month_Sort", "Month Name"]:
        return aggregation_cache.get_month_summary(df, as_index=as_index, dropna=dropna, sort_col=sort_col, **kwargs)
    return aggregation_cache.group_summary(df, month_cols, as_index=as_index, dropna=dropna, **kwargs)

@profiler.measure_agg("service_summary")
def service_summary(df: pd.DataFrame, svc_col: str = "Service Type", as_index: bool = False, dropna: bool = False, **kwargs) -> Union[pd.DataFrame, pd.core.groupby.DataFrameGroupBy]:
    if svc_col == "Service Type":
        return aggregation_cache.get_service_summary(df, as_index=as_index, dropna=dropna, **kwargs)
    return aggregation_cache.group_summary(df, svc_col, as_index=as_index, dropna=dropna, **kwargs)

def dealer_summary(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """Global aggregation across the entire dealer DataFrame."""
    return df.agg(**kwargs).to_frame().T

def pivot_summary(df: pd.DataFrame, index: Union[str, List[str]], columns: Optional[Union[str, List[str]]] = None, values: Optional[Union[str, List[str]]] = None, aggfunc: str = "sum", fill_value: float = 0.0) -> pd.DataFrame:
    """Generic pivot table utility."""
    if columns is None:
        pvt = pd.pivot_table(df, index=index, values=values, aggfunc=aggfunc, fill_value=fill_value)
    else:
        pvt = pd.pivot_table(df, index=index, columns=columns, values=values, aggfunc=aggfunc, fill_value=fill_value)
    return pvt.reset_index()

def top_n(df: pd.DataFrame, group_cols: Union[str, List[str]], metric_col: Union[str, List[str]], n: int = 10, ascending: bool = False, dropna: bool = False) -> pd.DataFrame:
    """Aggregate by group_cols, sum the metric_col, and return top N."""
    res = df.groupby(group_cols, as_index=False, dropna=dropna)[metric_col].sum()
    if isinstance(metric_col, list):
        sort_col = metric_col[0]
    else:
        sort_col = metric_col
    return res.sort_values(sort_col, ascending=ascending).head(n)

def bottom_n(df: pd.DataFrame, group_cols: Union[str, List[str]], metric_col: Union[str, List[str]], n: int = 10, dropna: bool = False) -> pd.DataFrame:
    """Aggregate by group_cols, sum the metric_col, and return bottom N."""
    return top_n(df, group_cols, metric_col, n=n, ascending=True, dropna=dropna)

def aggregate_metrics(df: pd.DataFrame, agg_dict: Optional[Dict[str, Any]] = None, **kwargs) -> pd.DataFrame:
    """Generic aggregation returning a DataFrame."""
    if agg_dict:
        return df.agg(agg_dict).to_frame().T
    return df.agg(**kwargs).to_frame().T

def rank_entities(df: pd.DataFrame, group_col: Union[str, List[str]], metric_col: str, ascending: bool = False, dropna: bool = False) -> pd.DataFrame:
    """Rank entities based on a summed metric."""
    res = df.groupby(group_col, as_index=False, dropna=dropna)[metric_col].sum()
    return res.sort_values(metric_col, ascending=ascending)
