"""
Audit Service Layer
Extracts the pure data loading and calculation logic from the legacy internal_audit_app.
"""

import pandas as pd
from datetime import datetime
from utils.loaders import _read_sheet as _utils_read_sheet, load_contacts as _utils_load_contacts

SHEET_ID = "1RUodK2UyYlG86DyGV3-0iyR7bdvkPLgeJJ0VlReHG_A"
PERIOD_FILTER = "All"

def _read_sheet(tab_name):
    """Wrapper to use utils.loaders._read_sheet with the global SHEET_ID."""
    return _utils_read_sheet(SHEET_ID, tab_name)

def load_contacts():
    """Wrapper to use utils.loaders.load_contacts with the global SHEET_ID."""
    return _utils_load_contacts(SHEET_ID)

def calc_missed_labour(data):
    """
    Benchmark hierarchy:
      L1 - Location + Model + Month  (mean FRT of YES rows)
      L2 - Location + Month          (mean FRT of YES rows, any model)
      L3 - 0
    Columns added: Job Source (PMS/FR2/FR3), Leak Type (Not Charged/Fully Discounted).
    """
    records = []
    services = [
        ('pms', 'PMS',  'PMS_FRT',  'PMS Flag'),
        ('pms', 'WA',   'WA_FRT',   'WA Flag'),
        ('pms', 'WB',   'WB_FRT',   'WB Flag'),
        ('pms', 'DC',   'DC_FRT',   'DC Flag'),
        ('pms', 'AC',   'AC_FRT',   'AC Flag'),
        ('pms', 'EVAP', 'Evap_FRT', 'Evap Flag'),
        ('fr2', 'WA',   'WA_FRT',   'WA Flag'),
        ('fr2', 'WB',   'WB_FRT',   'WB Flag'),
        ('fr3', 'WA',   'WA_FRT',   'WA Flag'),
        ('fr3', 'WB',   'WB_FRT',   'WB Flag'),
    ]
    for df_key, svc, frt_col, flag_col in services:
        if df_key not in data or data[df_key].empty:
            continue
        # Avoid creating full copies
        df = data[df_key]
        if frt_col not in df.columns or flag_col not in df.columns:
            continue
            
        frt_s = pd.to_numeric(df[frt_col], errors='coerce').fillna(0)
        if 'Bill Date' in df.columns:
            month_s = pd.to_datetime(df['Bill Date'], errors='coerce').dt.to_period('M').astype(str)
        else:
            month_s = pd.Series('unknown', index=df.index)
            
        flags_upper = df[flag_col].astype(str).str.upper()
        yes_mask = flags_upper.str.contains('YES') & (frt_s > 0)
        
        # Build benchmarks using multi-index series for fast mapping
        yes_df = pd.DataFrame({'Location': df.get('Location'), 'Model': df.get('Model'), '_month': month_s, 'FRT': frt_s})[yes_mask]
        
        l1_bm = yes_df.groupby(['Location', 'Model', '_month'])['FRT'].mean()
        l2_bm = yes_df.groupby(['Location', '_month'])['FRT'].mean()
        
        leak_mask = flags_upper.str.contains(r'\bNO\b|ZERO', regex=True)
        if not leak_mask.any():
            continue
            
        leaks = df[leak_mask]
        l_month = month_s[leak_mask]
        l_flags = flags_upper[leak_mask]
        
        # Vectorized mapping of benchmarks
        l1_idx = pd.MultiIndex.from_arrays([leaks.get('Location', pd.Series(index=leaks.index)), leaks.get('Model', pd.Series(index=leaks.index)), l_month])
        l2_idx = pd.MultiIndex.from_arrays([leaks.get('Location', pd.Series(index=leaks.index)), l_month])
        
        val_l1 = pd.Series(l1_idx.map(l1_bm))
        val_l2 = pd.Series(l2_idx.map(l2_bm))
        
        # Combine L1, L2, L3 (0)
        final_vals = val_l1.combine_first(val_l2).fillna(0)
        
        # Build records efficiently
        for i, (idx, row) in enumerate(leaks.iterrows()):
            records.append({
                'Location':     row.get('Location', ''),
                'Advisor Name': row.get('Advisor Name', ''),
                'Model':        row.get('Model', ''),
                'Job Card No':  row.get('Job Card No', ''),
                'Bill Date':    row.get('Bill Date', ''),
                'Service Type': svc,
                'Value':        final_vals.iloc[i],
                'Job Source':   df_key.upper(),
                'Leak Type':    'Not Charged' if 'NO' in l_flags.iloc[i] else 'Fully Discounted'
            })
            
    return pd.DataFrame(records) if records else pd.DataFrame()


def calc_penetration(df, flag_prefixes):
    if df.empty or "Advisor Name" not in df.columns or "Location" not in df.columns:
        return pd.DataFrame()
    result = []
    for (loc, adv), group in df.groupby(["Location", "Advisor Name"], sort=True):
        row = {"Location": loc, "Advisor Name": adv, "Total Bills": len(group), "IsTotalRow": 0}
        for prefix in flag_prefixes:
            flag_col = f"{prefix} Flag"
            if flag_col not in df.columns:
                row[f"{prefix} YES"] = row[f"{prefix} NO"] = row[f"{prefix} ZERO"] = 0
                row[f"{prefix} %"] = 0
                continue
            flag_vals = group[flag_col].astype(str).str.upper()
            yes_count = flag_vals.str.contains("YES").sum()
            zero_count = flag_vals.str.contains("ZERO").sum()
            no_count = flag_vals.str.contains("NO").sum()
            row[f"{prefix} YES"] = yes_count
            row[f"{prefix} NO"] = no_count
            row[f"{prefix} ZERO"] = zero_count
            total = len(group)
            row[f"{prefix} %"] = yes_count / total if total > 0 else 0
        result.append(row)
    return pd.DataFrame(result)

def filter_by_period(res, period_filter):
    """
    period_filter values:
      "All"                                    no filter
      "Latest Month" / "Last Available Month" / "1M"   latest calendar month
      "3M"                                     latest 3 months
      "6M"                                     latest 6 months
      "FY"                                     Indian FY (Apr-Mar) based on max date
      "FY 25-26"                               Apr 2025 - Mar 2026
      "FY 26-27"                               Apr 2026 - Mar 2027
    """
    if not period_filter or period_filter == "All":
        return res
    max_date = None
    for k in ["pms", "fr2", "fr3"]:
        if k in res and not res[k].empty and "Bill Date" in res[k].columns:
            d = pd.to_datetime(res[k]["Bill Date"], errors="coerce").dropna()
            if not d.empty:
                m = d.max()
                max_date = m if max_date is None else max(m, max_date)
    if not max_date:
        return res

    def _apply(cutoff=None, month_str=None):
        for k in ["pms", "fr2", "fr3"]:
            if k not in res or res[k].empty or "Bill Date" not in res[k].columns:
                continue
            d = pd.to_datetime(res[k]["Bill Date"], errors="coerce")
            if month_str:
                res[k] = res[k][d.dt.strftime("%Y-%m") == month_str]
            elif cutoff is not None:
                res[k] = res[k][d >= cutoff]

    if period_filter in ("Latest Month", "Last Available Month", "1M"):
        _apply(month_str=max_date.strftime("%Y-%m"))
    elif period_filter == "3M":
        _apply(cutoff=max_date - pd.DateOffset(months=3))
    elif period_filter == "6M":
        _apply(cutoff=max_date - pd.DateOffset(months=6))
    elif period_filter == "FY":
        fy_year  = max_date.year if max_date.month >= 4 else max_date.year - 1
        fy_start = pd.Timestamp(fy_year, 4, 1)
        _apply(cutoff=fy_start)
    elif period_filter == "FY 25-26":
        fy_start = pd.Timestamp(2025, 4, 1)
        fy_end   = pd.Timestamp(2026, 3, 31)
        for k in ["pms", "fr2", "fr3"]:
            if k not in res or res[k].empty or "Bill Date" not in res[k].columns:
                continue
            d = pd.to_datetime(res[k]["Bill Date"], errors="coerce")
            res[k] = res[k][(d >= fy_start) & (d <= fy_end)]
    elif period_filter == "FY 26-27":
        fy_start = pd.Timestamp(2026, 4, 1)
        fy_end   = pd.Timestamp(2027, 3, 31)
        for k in ["pms", "fr2", "fr3"]:
            if k not in res or res[k].empty or "Bill Date" not in res[k].columns:
                continue
            d = pd.to_datetime(res[k]["Bill Date"], errors="coerce")
            res[k] = res[k][(d >= fy_start) & (d <= fy_end)]
    return res

def load_data(period_filter=None):
    """
    Load main audit data sheets from Google Sheets.
    Dependencies on pre-computed penetration and avg labour sheets removed.
    """
    res = {
        "pms":     _read_sheet("Unbilled_PMS"),
        "fr2":     _read_sheet("Unbilled_FR2"),
        "fr3":     _read_sheet("Unbilled_FR3"),
    }
    
    # Use provided period_filter or fall back to PERIOD_FILTER constant
    filter_to_use = period_filter if period_filter is not None else PERIOD_FILTER
    res = filter_by_period(res, filter_to_use)
    
    # Generate penetration tables dynamically
    res["pms_pen"] = calc_penetration(res["pms"], ["PMS", "WA", "WB", "DC", "EVAP", "AC"]) if not res["pms"].empty else pd.DataFrame()
    res["fr2_pen"] = calc_penetration(res["fr2"], ["WA", "WB"]) if not res["fr2"].empty else pd.DataFrame()
    res["fr3_pen"] = calc_penetration(res["fr3"], ["WA", "WB"]) if not res["fr3"].empty else pd.DataFrame()
        
    res["missed"] = calc_missed_labour(res)
        
    return res


def get_month(data):
    """
    Derive audit period string from Bill Date in PMS/FR2/FR3 data.
    Replaces Excel version that also read Bill_Reg sheet.
    """
    for key in ["pms", "fr2", "fr3"]:
        df = data[key]
        if df.empty or "Bill Date" not in df.columns:
            continue
        d = pd.to_datetime(df["Bill Date"], errors="coerce").dropna()
        if not d.empty:
            return d.max().strftime("%B %Y")
    return datetime.now().strftime("%B %Y")


def all_locs(data, sort_map=None):
    s = set()
    for k in ["pms","fr2","fr3"]:
        df = data[k]
        if not df.empty and "Location" in df.columns:
            s.update(df["Location"].dropna().unique())
    if sort_map:
        return sorted(s, key=lambda l: sort_map.get(l, 999))
    return sorted(s)
