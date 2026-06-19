import pandas as pd
import hashlib
import time
import threading
from typing import Dict, Any, Union, List, Optional
from services.error_handler import with_error_context, AggregationError
from config.settings import VERSION

# Cache architecture:
# _CACHE[hash] = {
#     "groupby_location": GroupBy object,
#     "location_sum": DataFrame,
#     "timestamp": float,  # Last access time for LRU eviction
#     "ttl": float  # Time-to-live in seconds
# }
_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_LOCK = threading.RLock()  # Thread-safe cache access
_DEFAULT_TTL = 3600  # 1 hour default TTL
_MAX_CACHE_SIZE = 10  # Maximum number of DataFrame entries in cache

def _get_df_hash(df: pd.DataFrame) -> str:
    """Returns a deterministic hash for a DataFrame using full content.
    
    Uses dataset version (from settings) and full dataframe hash for accuracy.
    Replaces the previous head/tail sampling approach.
    """
    if df.empty:
        return "empty"
    h = hashlib.md5()
    # Include dataset version to invalidate cache on app updates
    h.update(str(VERSION).encode())
    # Include shape and columns
    h.update(str(df.shape).encode())
    h.update(str(list(df.columns)).encode())
    # Use full dataframe hash instead of head/tail sampling
    h.update(pd.util.hash_pandas_object(df).values.tobytes())
    return h.hexdigest()

def _evict_if_needed() -> None:
    """Evict least recently used entries if cache exceeds max size.
    
    Uses LRU (least recently used) eviction policy instead of FIFO.
    Keeps recently used entries, not recently inserted.
    """
    with _CACHE_LOCK:
        if len(_CACHE) <= _MAX_CACHE_SIZE:
            return
        
        # Sort by last access time (timestamp) and evict oldest
        sorted_entries = sorted(_CACHE.items(), key=lambda x: x[1].get("timestamp", 0))
        num_to_evict = len(_CACHE) - _MAX_CACHE_SIZE
        for i in range(num_to_evict):
            del _CACHE[sorted_entries[i][0]]

def _update_access_time(df_id: str) -> None:
    """Update the last access time for a cache entry."""
    with _CACHE_LOCK:
        if df_id in _CACHE:
            _CACHE[df_id]["timestamp"] = time.time()

def _is_expired(df_id: str) -> bool:
    """Check if a cache entry has expired based on TTL."""
    with _CACHE_LOCK:
        if df_id not in _CACHE:
            return True
        entry = _CACHE[df_id]
        ttl = entry.get("ttl", _DEFAULT_TTL)
        timestamp = entry.get("timestamp", 0)
        return (time.time() - timestamp) > ttl

def _get_cache_gb(df: pd.DataFrame, key: str, cols: Union[str, List[str]], as_index: bool = False, dropna: bool = False) -> pd.core.groupby.DataFrameGroupBy:
    df_id = _get_df_hash(df)
    
    # Check if expired and remove if so
    if _is_expired(df_id):
        with _CACHE_LOCK:
            if df_id in _CACHE:
                del _CACHE[df_id]
    
    # Evict if cache is full (LRU policy)
    _evict_if_needed()
    
    with _CACHE_LOCK:
        if df_id not in _CACHE:
            _CACHE[df_id] = {"timestamp": time.time(), "ttl": _DEFAULT_TTL}
        else:
            _update_access_time(df_id)
        
        cache_key = f"gb_{key}_{as_index}_{dropna}"
        if cache_key not in _CACHE[df_id]:
            _CACHE[df_id][cache_key] = df.groupby(cols, as_index=as_index, dropna=dropna)
        
        return _CACHE[df_id][cache_key]

@with_error_context(AggregationError)
def group_summary(df: pd.DataFrame, group_cols: Union[str, List[str]], as_index: bool = False, dropna: bool = False, **kwargs) -> Union[pd.DataFrame, pd.core.groupby.DataFrameGroupBy]:
    # We use string representation of group_cols as cache key component
    key = str(group_cols)
    gb = _get_cache_gb(df, key, group_cols, as_index, dropna)
    
    if not kwargs:
        return gb
        
    # If kwargs are provided, we can memoize the exact aggregation result!
    df_id = _get_df_hash(df)
    agg_key = f"agg_{key}_{as_index}_{dropna}_{str(kwargs)}"
    
    with _CACHE_LOCK:
        _update_access_time(df_id)
        if agg_key not in _CACHE[df_id]:
            _CACHE[df_id][agg_key] = gb.agg(**kwargs)
        
        return _CACHE[df_id][agg_key].copy()

@with_error_context(AggregationError)
def get_location_summary(df: pd.DataFrame, as_index: bool = False, dropna: bool = False, **kwargs) -> Union[pd.DataFrame, pd.core.groupby.DataFrameGroupBy]:
    return group_summary(df, "Location Name", as_index=as_index, dropna=dropna, **kwargs)

@with_error_context(AggregationError)
def get_advisor_summary(df: pd.DataFrame, as_index: bool = False, dropna: bool = False, **kwargs) -> Union[pd.DataFrame, pd.core.groupby.DataFrameGroupBy]:
    adv_col = "Advisor Name" if "Advisor Name" in df.columns else "Advisor"
    valid_df = df[df[adv_col] != "Unassigned"] if adv_col in df.columns else df
    return group_summary(valid_df, adv_col, as_index=as_index, dropna=dropna, **kwargs)

@with_error_context(AggregationError)
def get_month_summary(df: pd.DataFrame, as_index: bool = False, dropna: bool = False, sort_col: str = "Month_Sort", **kwargs) -> Union[pd.DataFrame, pd.core.groupby.DataFrameGroupBy]:
    gb = group_summary(df, ["Month_Sort", "Month Name"], as_index=as_index, dropna=dropna)
    if not kwargs:
        return gb
    
    df_id = _get_df_hash(df)
    agg_key = f"agg_month_{as_index}_{dropna}_{str(kwargs)}"
    
    with _CACHE_LOCK:
        _update_access_time(df_id)
        if agg_key not in _CACHE[df_id]:
            res = gb.agg(**kwargs)
            if sort_col and sort_col in (res.columns if not as_index else res.index.names):
                res = res.sort_values(sort_col)
            _CACHE[df_id][agg_key] = res
        
        return _CACHE[df_id][agg_key].copy()

def get_service_summary(df: pd.DataFrame, as_index: bool = False, dropna: bool = False, **kwargs) -> Union[pd.DataFrame, pd.core.groupby.DataFrameGroupBy]:
    return group_summary(df, "Service Type", as_index=as_index, dropna=dropna, **kwargs)

def get_revenue_summary(df: pd.DataFrame) -> pd.DataFrame:
    # Dedicated dashboard metric summary
    return get_location_summary(df, as_index=False).agg(
        Labour=("Net_Labour", "sum"), Parts=("Net_Parts", "sum"), JCs=("JC_Nos.", "sum")
    )

def get_margin_summary(df: pd.DataFrame) -> pd.DataFrame:
    return get_location_summary(df, as_index=False).agg(
        Total_Margin=("Total Margin", "sum"), Parts_Margin=("Parts_Margin", "sum")
    )

def get_discount_summary(df: pd.DataFrame) -> pd.DataFrame:
    return get_location_summary(df, as_index=False).agg(
        Labour_Discount=("Labour Discount", "sum"), Parts_Discount=("Parts Discount", "sum")
    )
