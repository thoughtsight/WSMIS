"""
RKM Motors — Internal Audit Standalone App
==========================================
Reads all audit data directly from Google Sheets.
Generates HTML reports identical to rkm_report_generator_v10.py output.

SETUP:
    pip install pandas gspread google-auth openpyxl pyautogui pyperclip

DATA SOURCE (Google Sheets tabs):
    Unbilled_PMS, Unbilled_FR2, Unbilled_FR3
    PMS_Pentration, FR2_Pentration, FR3_Pentration
    Avg PMS Lab, Help

LOCATION MAPPING (Help sheet columns):
    Location Number -> sort order
    Location Name   -> DMS location name (key used in all data sheets)
    Loc CD          -> workshop code (E103* = PortBlair)

CHANGES FROM v10:
    - EXCEL_FILE removed; replaced by SHEET_ID + SERVICE_ACCOUNT
    - load_data()     reads from Google Sheets instead of Excel
    - load_contacts() reads location map from Help sheet
    - get_month()     derives period from Bill Date in PMS/FR2/FR3 data
    - Everything else (CSS, JS, all HTML builders) copied verbatim
"""

import os, re, sys, time, subprocess
import pandas as pd
from datetime import datetime
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials

# ═══════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════

SHEET_ID        = "1RUodK2UyYlG86DyGV3-0iyR7bdvkPLgeJJ0VlReHG_A"
SERVICE_ACCOUNT = r"D:\RKM-INDORE\Reports\WSMIS\service_account.json"
PERIOD_FILTER   = "All"  # Disabled: Missed Labour follows WSMIS period selection only

# ═══════════════════════════════════════════════════════════════
#  CONTACTS
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
#  GOOGLE SHEETS CLIENT
# ═══════════════════════════════════════════════════════════════

from utils.loaders import _read_sheet as _utils_read_sheet, load_contacts as _utils_load_contacts

def _read_sheet(tab_name):
    """Wrapper to use utils.loaders._read_sheet with the global SHEET_ID."""
    return _utils_read_sheet(SHEET_ID, tab_name)

def load_contacts():
    """Wrapper to use utils.loaders.load_contacts with the global SHEET_ID."""
    return _utils_load_contacts(SHEET_ID)

def _find_in(df, keywords):
    for c in df.columns:
        if all(k.lower() in str(c).lower() for k in keywords):
            return c
    return None


# ═══════════════════════════════════════════════════════════════
#  DATA LOADER  — Google Sheets
# ═══════════════════════════════════════════════════════════════

def calc_missed_labour(data):
    """
    Benchmark hierarchy:
      L1 — Location + Model + Month  (mean FRT of YES rows)
      L2 — Location + Month          (mean FRT of YES rows, any model)
      L3 — 0
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
        df = data[df_key].copy()
        if frt_col not in df.columns or flag_col not in df.columns:
            continue
        df[frt_col] = pd.to_numeric(df[frt_col], errors='coerce').fillna(0)
        if 'Bill Date' in df.columns:
            df['_month'] = pd.to_datetime(df['Bill Date'], errors='coerce').dt.to_period('M').astype(str)
        else:
            df['_month'] = 'unknown'
        flags_upper = df[flag_col].astype(str).str.upper()
        yes_df = df[flags_upper.str.contains('YES') & (df[frt_col] > 0)]
        l1_bm = yes_df.groupby(['Location', 'Model', '_month'])[frt_col].mean().to_dict()
        l2_bm = yes_df.groupby(['Location', '_month'])[frt_col].mean().to_dict()
        leaks = df[flags_upper.str.contains(r'\bNO\b|ZERO', regex=True)].copy()
        for _, row in leaks.iterrows():
            loc   = row.get('Location', '')
            model = row.get('Model', '')
            mon   = row.get('_month', '')
            fval  = str(row.get(flag_col, '')).upper()
            val   = l1_bm.get((loc, model, mon)) or l2_bm.get((loc, mon), 0) or 0
            records.append({
                'Location':     loc,
                'Advisor Name': row.get('Advisor Name', ''),
                'Model':        model,
                'Job Card No':  row.get('Job Card No', ''),
                'Bill Date':    row.get('Bill Date', ''),
                'Service Type': svc,
                'Job Source':   df_key.upper(),
                'Leak Type':    'Not Charged' if ('NO' in fval and 'ZERO' not in fval) else 'Fully Discounted',
                'Missed Revenue': float(val),
                '_month':       mon,
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

def flt(df, loc):
    if df.empty or "Location" not in df.columns: return df
    return df[df["Location"] == loc].copy()

def flt_pen(df, loc):
    if df.empty or "Location" not in df.columns: return df
    rows = df[df["Location"] == loc].copy()
    if "IsTotalRow" in rows.columns:
        rows = rows[rows["IsTotalRow"] == 0]
    return rows

# ═══════════════════════════════════════════════════════════════
#  FORMATTERS  +  COLOUR THRESHOLDS
# ═══════════════════════════════════════════════════════════════

from ui.formatters import fmt_pct_ratio, fmt_pct_100, fmt_amt

# PMS WA/WB/DC/Evap/AC  — ratio (0-1)
def cls_pms(v):
    try:
        f = float(v)
        return "hi" if f >= 0.80 else ("mid" if f >= 0.60 else "lo")
    except: return ""

# PMS% (job card charged as PMS labour) — ratio (0-1), binary: 100% = green else red
def cls_pms_pct(v):
    try:
        return "hi" if float(v) >= 0.999 else "lo"
    except: return ""

# FR2/FR3 — can be ratio (0-1) or 0-100 depending on sheet
def cls_fr_ratio(v):
    try:
        f = float(v)
        return "hi" if f >= 0.60 else ("mid" if f >= 0.50 else "lo")
    except: return ""

def cls_fr_100(v):
    try:
        f = float(v) / 100.0
        return "hi" if f >= 0.60 else ("mid" if f >= 0.50 else "lo")
    except: return ""

def flag_chip(val):
    if not isinstance(val, str): return str(val)
    v = val.upper()
    if "YES"  in v: return f'<span class="chip yes">{val}</span>'
    if "ZERO" in v: return f'<span class="chip zero">{val}</span>'
    if "NO"   in v: return f'<span class="chip no">{val}</span>'
    return val

def clean_adv(name):
    return re.sub(r'[-_]([A-Z]{1,6}\d*|[A-Z]{2,8}[A-Z0-9]{0,6})$', '',
                  str(name), flags=re.IGNORECASE).strip()

def clean_mod(name):
    return str(name).replace('"', '').replace("'", "").strip()

def clean_mod(name):
    return str(name).replace('"', '').replace("'", "").strip()

def clean_mod(name):
    return str(name).replace('"', '').replace("'", "").strip()

def _loc_id(loc):
    return re.sub(r'[^A-Za-z0-9]', '_', loc)

# ═══════════════════════════════════════════════════════════════
#  CSS (RESTORED from archive)
# ═══════════════════════════════════════════════════════════════

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;font-size:13px;
     background:#F5F6F8;color:#1C1C1E;-webkit-font-smoothing:antialiased}
.wrap{max-width:1160px;margin:0 auto;padding:16px 14px}

/* Header */
.hdr{background:#fff;border:1px solid #E8ECF0;border-radius:14px;
     padding:16px 22px;margin-bottom:12px;
     display:flex;justify-content:space-between;align-items:flex-start}
.hdr-brand{font-size:17px;font-weight:500;color:#1C1C1E}
.hdr-brand em{color:#185FA5;font-style:normal}
.hdr-locs{font-size:11px;color:#9CA3AF;margin-top:4px;max-width:600px;line-height:1.5}
.hdr-right{text-align:right;flex-shrink:0}
.hdr-period{font-size:12px;font-weight:500;color:#1C1C1E}
.hdr-gen{font-size:10px;color:#9CA3AF;margin-top:3px}

/* Page nav */
.page-nav{display:flex;justify-content:center;gap:8px;margin-bottom:14px}
.pnav{padding:8px 24px;border-radius:20px;font-size:12px;font-weight:500;
      cursor:pointer;user-select:none;border:1px solid #E8ECF0;
      background:#fff;color:#6B7280;transition:background .15s,color .15s}
.pnav.on{background:#185FA5;color:#fff;border-color:#185FA5}
.pnav:hover:not(.on){background:#F0F4FA;color:#185FA5}

/* Location bar */
.loc-bar{background:#fff;border:1px solid #E8ECF0;border-radius:12px;
         padding:9px 16px;margin-bottom:12px;
         display:flex;align-items:center;gap:10px;flex-wrap:wrap;
         justify-content:space-between}
.loc-bar label{font-size:11px;font-weight:500;color:#6B7280;white-space:nowrap}
.loc-bar select{font-size:13px;font-family:inherit;padding:6px 10px;
                border:1px solid #E8ECF0;border-radius:10px;
                background:#F5F6F8;color:#1C1C1E;outline:none;cursor:pointer;
                flex:1;max-width:440px}
.loc-bar select:focus{border-color:#185FA5}
.loc-bar-left{display:flex;align-items:center;gap:10px;flex:1;flex-wrap:wrap}

/* PortBlair filter toggle */
.pb-filter{display:flex;align-items:center;gap:8px;flex-shrink:0;margin-left:auto}
.pb-filter label{font-size:10px;font-weight:500;color:#9CA3AF;white-space:nowrap}
.pb-toggle{display:flex;border:1.5px solid #185FA5;border-radius:20px;overflow:hidden;
           background:#fff}
.pb-opt{padding:5px 12px;font-size:10px;font-weight:600;cursor:pointer;
        user-select:none;color:#185FA5;background:#fff;
        transition:background .12s,color .12s;white-space:nowrap;letter-spacing:.02em}
.pb-opt:not(:last-child){border-right:1px solid #E8ECF0}
.pb-opt.on{background:#185FA5;color:#fff}
.pb-opt:hover:not(.on){background:#EBF2FC}
.loc-counts{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.lc-pill{font-size:10px;font-weight:500;padding:3px 10px;border-radius:20px;
         border:1px solid #E8ECF0;background:#F5F6F8;color:#6B7280;white-space:nowrap}
.lc-pill.has-data{background:#FEE2E2;border-color:#FECACA;color:#991B1B}
.lc-pill.no-data{background:#D1FAE5;border-color:#A7F3D0;color:#065F46}

/* Location heading */
.loc-heading{background:#fff;border:1px solid #E8ECF0;
             border-left:3px solid #185FA5;border-radius:0 12px 12px 0;
             padding:10px 16px;margin-bottom:12px;
             display:flex;justify-content:space-between;align-items:center}
.loc-heading-name{font-size:13px;font-weight:500;color:#185FA5}
.loc-heading-sub{font-size:11px;color:#9CA3AF;margin-top:2px}
.avg-pill{font-size:11px;font-weight:500;padding:4px 12px;border-radius:20px;
          border:1px solid #E8ECF0;background:#F5F6F8;color:#6B7280}
.avg-pill.hi{background:#D1FAE5;border-color:#A7F3D0;color:#065F46}
.avg-pill.mid{background:#FEF3C7;border-color:#FDE68A;color:#92400E}
.avg-pill.lo{background:#FEE2E2;border-color:#FECACA;color:#991B1B}

/* KPI cards */
.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));
         gap:8px;margin-bottom:14px}
.kpi{background:#fff;border:1px solid #E8ECF0;border-radius:12px;padding:14px 16px}
.kpi-lbl{font-size:10px;font-weight:500;color:#9CA3AF;text-transform:uppercase;
         letter-spacing:.05em;margin-bottom:8px}
.kpi-val{font-size:22px;font-weight:500;line-height:1}
.kpi-val.hi{color:#3B6D11}.kpi-val.mid{color:#BA7517}
.kpi-val.lo{color:#A32D2D}.kpi-val.neu{color:#1C1C1E}

/* Section cards */
.sec{background:#fff;border:1px solid #E8ECF0;border-radius:14px;
     margin-bottom:12px;overflow:hidden}
.sec-hdr{background:#F8F9FB;padding:9px 16px;font-size:12px;font-weight:500;
         display:flex;justify-content:space-between;align-items:center;
         flex-wrap:wrap;gap:6px;border-bottom:1px solid #E8ECF0}

/* Tables */
.tbl-badges{padding:6px 16px;display:flex;flex-wrap:wrap;gap:5px;
            border-bottom:1px solid #F5F6F8;min-height:1px}
.tbl-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12px}
th{background:#F8F9FB;font-size:10px;font-weight:500;text-transform:uppercase;
   letter-spacing:.05em;color:#9CA3AF;padding:8px 12px;text-align:left;
   border-bottom:1px solid #E8ECF0;white-space:nowrap}
th.r{text-align:right}
td{padding:7px 12px;border-bottom:1px solid #F5F6F8;vertical-align:middle;color:#374151}
td.r{text-align:right}
tr:last-child td{border-bottom:none}
.r-adv{background:#F8F9FB;cursor:pointer;user-select:none}
.r-adv:hover{background:#EEF2F8}
.r-mod{background:#FAFBFC;cursor:pointer;user-select:none}
.r-mod:hover{background:#EEF2F8}
.r-jc{background:#fff}.r-jc:hover{background:#F8F9FB}
.tot-row{background:#F0F4F8;font-weight:500;border-top:1px solid #E8ECF0}
.arr{display:inline-block;width:14px;font-size:9px;color:#9CA3AF;margin-right:3px;
     transition:transform .15s}

/* Chips */
.adv-chips{display:inline-flex;gap:4px;flex-wrap:nowrap;margin-left:8px;vertical-align:middle}
.chip{display:inline-block;font-size:10px;font-weight:500;padding:2px 8px;
      border-radius:20px;white-space:nowrap}
.chip.yes{background:#E8F5E9;color:#2E7D32}
.chip.zero{background:#FFF8E1;color:#E65100}
.chip.no{background:#FFEBEE;color:#C62828}
.pbadge{display:inline-block;font-size:10px;font-weight:500;padding:3px 10px;
        border-radius:20px;white-space:nowrap}
.pbadge.no{background:#FFEBEE;color:#C62828}
.pbadge.zero{background:#FFF8E1;color:#E65100}

/* Penetration % */
.pct{font-weight:500;font-size:12px}
.pct.hi{color:#3B6D11}.pct.mid{color:#BA7517}.pct.lo{color:#A32D2D}

/* FR pen side by side */
.pen-row{display:flex;gap:12px}
.pen-row .sec{flex:1;min-width:0}

/* Legend */
.legend{display:flex;gap:14px;padding:7px 16px;font-size:10px;color:#9CA3AF;
        border-top:1px solid #F5F6F8;flex-wrap:wrap}

/* Empty */
.empty{padding:24px;color:#9CA3AF;font-size:12px;text-align:center}

/* Avg Labour bars */
.bar-cell{display:flex;align-items:center;gap:8px;min-width:180px}
.bar-track{flex:1;height:5px;background:#F0F4F8;border-radius:3px;overflow:hidden}
.bar-fill{height:100%;border-radius:3px}
.bar-fill.hi{background:#3B6D11}.bar-fill.mid{background:#BA7517}.bar-fill.lo{background:#A32D2D}
.bar-label{font-size:12px;font-weight:500;white-space:nowrap}
.bar-label.hi{color:#3B6D11}.bar-label.mid{color:#BA7517}.bar-label.lo{color:#A32D2D}
.rank-badge{display:inline-block;font-size:9px;font-weight:500;padding:2px 7px;
            border-radius:20px;margin-left:6px}
.rank-badge.best{background:#E8F5E9;color:#2E7D32}
.rank-badge.worst{background:#FFEBEE;color:#C62828}
.loc-pill{display:inline-block;background:#EBF2FC;color:#185FA5;font-size:10px;
          font-weight:500;padding:2px 8px;border-radius:20px;margin-right:4px}

/* Count badge */
.cnt{display:inline-block;font-size:10px;font-weight:500;padding:1px 7px;
     border-radius:20px;background:#EBF2FC;color:#185FA5;margin-left:4px}

/* Advisor colour bands — alternating left-border per advisor block */
.r-adv.band0,.r-mod.band0,.r-jc.band0{border-left:3px solid #93C5FD}
.r-adv.band1,.r-mod.band1,.r-jc.band1{border-left:3px solid #6EE7B7}

/* Attention section — eyecatching PMS NO/Zero alert */
.attn-section{background:#fff;border:1px solid #FECACA;border-radius:14px;
              margin-bottom:12px;overflow:hidden}
.attn-hdr{background:#FEF2F2;padding:10px 16px;display:flex;
          justify-content:space-between;align-items:center;
          border-bottom:1px solid #FECACA}
.attn-title{font-size:12px;font-weight:500;color:#991B1B;display:flex;
            align-items:center;gap:8px}
.attn-dot{width:8px;height:8px;border-radius:50%;background:#EF4444;
          animation:pulse 1.8s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}
.attn-cnt{font-size:10px;font-weight:500;padding:3px 10px;border-radius:20px;
          background:#FEE2E2;color:#991B1B;border:1px solid #FECACA}
.attn-empty{padding:16px;font-size:11px;color:#9CA3AF;text-align:center}

/* Combined flag+amount cell in JC rows */
.jc-svc{display:inline-flex;flex-direction:column;align-items:center;
        gap:2px;min-width:52px}
.jc-amt{font-size:10px;color:#374151;font-weight:500}
.jc-flag{font-size:9px;font-weight:500;padding:1px 6px;border-radius:20px;
         white-space:nowrap}
.jc-flag.yes{background:#E8F5E9;color:#2E7D32}
.jc-flag.zero{background:#FFF8E1;color:#E65100}
.jc-flag.no{background:#FFEBEE;color:#C62828}

/* Summary dashboard */
.dash-tabs{display:flex;gap:0;background:#fff;border:1px solid #E8ECF0;
           border-radius:12px;overflow:hidden;margin-bottom:12px}
.dash-tab{flex:1;padding:9px 16px;font-size:11px;font-weight:500;
          text-align:center;cursor:pointer;color:#6B7280;
          border-right:1px solid #E8ECF0;transition:background .12s,color .12s;
          user-select:none}
.dash-tab:last-child{border-right:none}
.dash-tab.on{background:#185FA5;color:#fff}
.dash-tab:hover:not(.on){background:#F0F4FA;color:#185FA5}
.dash-panel{display:none}.dash-panel.on{display:block}
.dash-wrap{overflow-x:auto}
.dash-tbl{width:100%;border-collapse:collapse;font-size:12px}
.dash-tbl th{background:#F8F9FB;font-size:10px;font-weight:500;
             text-transform:uppercase;letter-spacing:.05em;color:#9CA3AF;
             padding:8px 12px;text-align:left;border-bottom:1px solid #E8ECF0;
             white-space:nowrap}
.dash-tbl th.r{text-align:right}
.dash-tbl td{padding:8px 12px;border-bottom:1px solid #F5F6F8;vertical-align:middle}
.dash-tbl tr:last-child td{border-bottom:none}
.dash-tbl tr:hover td{background:#F8F9FB;cursor:pointer}
.dash-loc{font-weight:500;color:#185FA5;font-size:12px}
.dash-sub{font-size:10px;color:#9CA3AF;margin-top:1px}
.dash-cnt{display:inline-block;font-size:11px;font-weight:500;padding:2px 9px;
          border-radius:20px;background:#FEE2E2;color:#991B1B}
.dash-cnt.ok{background:#D1FAE5;color:#065F46}
.dash-pct{font-size:12px;font-weight:500}
.dash-pct.hi{color:#3B6D11}.dash-pct.mid{color:#BA7517}.dash-pct.lo{color:#A32D2D}
.dash-tot td{background:#F0F4F8;font-weight:500;border-top:1px solid #E8ECF0}

/* Footer */
.footer{padding:12px 14px;margin-top:8px;border-top:1px solid #E8ECF0;
        display:flex;justify-content:space-between;align-items:flex-start;
        flex-wrap:wrap;gap:8px}
.footer-left{font-size:10px;color:#9CA3AF;line-height:1.6}
.footer-right{text-align:right;font-size:10px;color:#9CA3AF;line-height:1.6}
.footer-confidential{font-size:9px;font-weight:600;color:#991B1B;
                     background:#FEE2E2;border:1px solid #FECACA;
                     padding:2px 8px;border-radius:4px;letter-spacing:.06em;
                     text-transform:uppercase;margin-top:4px;display:inline-block}
/* Confidential badge in header */
.conf-badge{display:inline-block;font-size:9px;font-weight:600;color:#991B1B;
            background:#FEE2E2;border:1px solid #FECACA;padding:2px 8px;
            border-radius:4px;letter-spacing:.06em;text-transform:uppercase;
            margin-top:5px}

/* Responsive */
@media(max-width:640px){
  .wrap{padding:10px 8px}
  .hdr{flex-direction:column;gap:8px;padding:12px 14px;border-radius:10px}
  .hdr-brand{font-size:15px}
  .hdr-right{text-align:left}
  .page-nav{flex-wrap:wrap;gap:6px}
  .pnav{padding:7px 16px;font-size:11px}
  .loc-bar{flex-direction:column;align-items:stretch;gap:8px;padding:8px 12px}
  .loc-bar-left{flex-direction:column;align-items:stretch}
  .loc-bar select{max-width:100%;font-size:12px}
  .loc-counts{flex-wrap:wrap}
  .pb-filter{margin-left:0;justify-content:flex-start}
  .kpi-row{grid-template-columns:repeat(2,1fr);gap:6px}
  .kpi{padding:10px 12px}
  .kpi-val{font-size:18px}
  .kpi-lbl{font-size:9px;margin-bottom:5px}
  .tbl-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
  table{min-width:480px}
  td,th{padding:6px 8px;font-size:11px}
  th{font-size:9px}
  .adv-chips{flex-wrap:wrap;gap:3px}
  .chip{font-size:9px;padding:1px 6px}
  .sec-hdr{flex-direction:column;gap:4px;padding:8px 12px}
  .loc-heading{flex-direction:column;gap:6px;padding:8px 12px}
  .bar-cell{min-width:120px}
  .pen-row{flex-direction:column}
  .dash-tab{font-size:10px;padding:8px 10px}
  .attn-hdr{flex-direction:column;gap:6px;align-items:flex-start}
  .footer{flex-direction:column;gap:6px}
  .footer-right{text-align:left}
}
@media print{
  .page-nav,.loc-bar{display:none!important}
  .loc-sec{display:block!important}
  tr[style*="display:none"]{display:table-row!important}
}
"""

# ═══════════════════════════════════════════════════════════════
#  JAVASCRIPT (RESTORED from archive)
# ═══════════════════════════════════════════════════════════════

JS = """
function tog(id){
  var rows=document.querySelectorAll('.p-'+id);
  var arrow=document.getElementById('arr_'+id);
  var hidden=rows.length>0&&rows[0].style.display==='none';
  rows.forEach(function(r){
    if(hidden){r.style.display='';}
    else{
      r.style.display='none';
      Array.from(r.classList).forEach(function(c){
        if(c.startsWith('p-')&&c!=='p-'+id){
          var cid=c.replace('p-','');
          document.querySelectorAll('.p-'+cid).forEach(function(cr){
            cr.style.display='none';});
        }
      });
    }
  });
  if(arrow){
    arrow.style.transform=hidden?'rotate(90deg)':'rotate(0deg)';
  }
}
function showPage(pid){
  document.querySelectorAll('.pnav').forEach(function(el){el.classList.remove('on');});
  document.querySelector('[data-p="'+pid+'"]').classList.add('on');
  var locs=document.querySelectorAll('.loc-sec');
  locs.forEach(function(l){
    var lid=l.id.replace('ls_','');
    var pms=document.getElementById('lsp_'+lid+'_pms');
    var fr=document.getElementById('lsp_'+lid+'_fr');
    var avg=document.getElementById('lsp_'+lid+'_avg');
    if(pms)pms.style.display='none';
    if(fr)fr.style.display='none';
    if(avg)avg.style.display='none';
    if(pid==='page-pms'&&pms)pms.style.display='block';
    if(pid==='page-fr'&&fr)fr.style.display='block';
    if(pid==='page-avg'&&avg)avg.style.display='block';
  });
}
function switchLoc(lid){
  document.querySelectorAll('.loc-sec').forEach(function(el){el.style.display='none';});
  var target=document.getElementById('ls_'+lid);
  if(target)target.style.display='block';
  var sel=document.getElementById('loc-sel');
  if(sel)sel.value=lid;
  if(typeof updateAdvDropdown === 'function') updateAdvDropdown(lid);
  if(typeof updateModDropdown === 'function') updateModDropdown(lid);
}
function changePeriod(period){
  // Update URL query parameter and reload
  var url = new URL(window.location.href);
  url.searchParams.set('period', period);
  window.location.href = url.toString();
}
function setPBFilter(filter){
  document.querySelectorAll('.pb-opt').forEach(function(el){el.classList.remove('on');});
  document.querySelector('[data-pb="'+filter+'"]').classList.add('on');
  
  var sel=document.getElementById('loc-sel');
  if(sel){
    var options=sel.options;
    var currentVal=sel.value;
    var isCurrentValHidden=false;
    
    for(var i=0; i<options.length; i++){
      var opt=options[i];
      if(opt.value==='__ALL__') continue;
      
      var isPB=opt.getAttribute('data-pb')==='1';
      var shouldShow=true;
      if(filter==='mainland'&&isPB) shouldShow=false;
      else if(filter==='portblair'&&!isPB) shouldShow=false;
      
      opt.style.display=shouldShow?'':'none';
      if(!shouldShow && opt.value===currentVal) {
        isCurrentValHidden=true;
      }
    }
    
    if(isCurrentValHidden || currentVal !== '__ALL__') {
      switchLoc('__ALL__');
    }
  }

  // Filter summary dashboard rows
  var dashRows=document.querySelectorAll('.dash-tbl tbody tr[data-pb]');
  dashRows.forEach(function(r){
    var isPB=r.getAttribute('data-pb')==='1';
    if(filter==='mainland'&&!isPB)r.style.display='';
    else if(filter==='mainland'&&isPB)r.style.display='none';
    else if(filter==='portblair'&&isPB)r.style.display='';
    else if(filter==='portblair'&&!isPB)r.style.display='none';
    else r.style.display='';
  });

  // Swap dynamic total rows
  var totRows=document.querySelectorAll('.dash-tot[data-tot]');
  totRows.forEach(function(r){
    if(r.getAttribute('data-tot') === filter) r.style.display='';
    else r.style.display='none';
  });
}
function dashGoto(lid){
  switchLoc(lid);
  var activeNav = document.querySelector('.pnav.on');
  if(activeNav) {
    showPage(activeNav.getAttribute('data-p'));
  } else {
    showPage('page-pms');
  }
}
window.addEventListener('load',function(){
  var hash=window.location.hash.replace('#','');
  if(hash)switchLoc(hash);
  else switchLoc('__ALL__');
  
  var activePB = document.querySelector('.pb-opt.on');
  if(activePB) setPBFilter(activePB.getAttribute('data-pb'));
});
"""

# ═══════════════════════════════════════════════════════════════
#  KPI BUILDERS
# ═══════════════════════════════════════════════════════════════

PMS_PEN_DEFS = [
    ("WA",   "WA %",   "WA YES",   "WA ZERO",   "WA NO",   cls_pms),
    ("WB",   "WB %",   "WB YES",   "WB ZERO",   "WB NO",   cls_pms),
    ("DC",   "DC %",   "DC YES",   "DC ZERO",   "DC NO",   cls_pms),
    ("AC",   "AC %",   "AC YES",   "AC ZERO",   "AC NO",   cls_pms),
    ("EVAP", "EVAP %", "EVAP YES", "EVAP ZERO", "EVAP NO", cls_pms),
    ("PMS",  "PMS %",  "PMS YES",  "PMS ZERO",  "PMS NO",  cls_pms_pct),
]
FR_PEN_DEFS = [
    ("WA", "WA %", "WA YES", "WA ZERO", "WA NO", cls_fr_100),
    ("WB", "WB %", "WB YES", "WB ZERO", "WB NO", cls_fr_100),
]

def _kpi_card(lbl, val, cls="neu"):
    return (f'<div class="kpi">'
            f'<div class="kpi-lbl">{lbl}</div>'
            f'<div class="kpi-val {cls}">{val}</div>'
            f'</div>')

def build_kpis_pms(pms_df, pen_df):
    cards = [_kpi_card("PMS Billed", len(pms_df), "neu")]
    if not pen_df.empty and "Total Bills" in pen_df.columns:
        tb = pen_df["Total Bills"].sum() or 1
        for nm, lbl, yc, zc, nc, cls_fn in PMS_PEN_DEFS:
            if yc in pen_df.columns:
                pct = pen_df[yc].sum() / tb
                cards.append(_kpi_card(lbl, fmt_pct_ratio(pct), cls_fn(pct)))
    return '<div class="kpi-row">' + "".join(cards) + '</div>'

def build_kpis_fr(fr2_df, fr2_pen_df, fr3_df, fr3_pen_df):
    def wa_pct(pen_df, flag="WA"):
        if pen_df.empty or f"{flag} YES" not in pen_df.columns: return None
        tb = pen_df["Total Bills"].sum() if "Total Bills" in pen_df.columns else 0
        return (pen_df[f"{flag} YES"].sum() / tb * 100) if tb else None
    f2p = wa_pct(fr2_pen_df, "WA")
    f2w = wa_pct(fr2_pen_df, "WB")
    f3p = wa_pct(fr3_pen_df, "WA")
    f3w = wa_pct(fr3_pen_df, "WB")
    cards = [
        _kpi_card("FR2 Billed", len(fr2_df), "neu"),
        _kpi_card("FR2 WA %",
                  fmt_pct_100(f2p) if f2p is not None else "—",
                  cls_fr_100(f2p)  if f2p is not None else ""),
        _kpi_card("FR2 WB %",
                  fmt_pct_100(f2w) if f2w is not None else "—",
                  cls_fr_100(f2w)  if f2w is not None else ""),
        _kpi_card("FR3 Billed", len(fr3_df), "neu"),
        _kpi_card("FR3 WA %",
                  fmt_pct_100(f3p) if f3p is not None else "—",
                  cls_fr_100(f3p)  if f3p is not None else ""),
        _kpi_card("FR3 WB %",
                  fmt_pct_100(f3w) if f3w is not None else "—",
                  cls_fr_100(f3w)  if f3w is not None else ""),
    ]
    return '<div class="kpi-row">' + "".join(cards) + '</div>'

# ═══════════════════════════════════════════════════════════════
#  UNBILLED TABLE  (Net + Count, no FRT toggle)
# ═══════════════════════════════════════════════════════════════

def unbilled_table(df, uid, flag_cols, pen_df=None):
    if df.empty:
        return '<div class="empty">No unbilled records.</div>'

    net_cols = [c for c in ["WA_Net","Net_WA","WB_Net","Net_WB",
                             "DC_Net","AC_Net","Evap_Net"] if c in df.columns]

    # Problem badges above table
    badges = ""
    for fc in flag_cols:
        if fc not in df.columns: continue
        no_c   = (df[fc].str.contains(r"\bNO\b", case=False, na=False) &
                  ~df[fc].str.contains("ZERO|YES", case=False, na=False)).sum()
        zero_c = df[fc].str.contains("Zero", case=False, na=False).sum()
        nm     = fc.replace(" Flag","")
        if no_c:   badges += f'<span class="pbadge no">{no_c} NO {nm}</span>'
        if zero_c: badges += f'<span class="pbadge zero">{zero_c} Zero {nm}</span>'

    # Advisor pen lookup — NO/Zero chips only
    pen_lookup = {}
    if pen_df is not None and not pen_df.empty:
        for _, pr in pen_df.iterrows():
            adv = str(pr.get("Advisor Name","")).strip()
            chips = ""
            for fc in flag_cols:
                nm     = fc.replace(" Flag","")
                no_c   = int(pr.get(f"{nm} NO",  0) or 0)
                zero_c = int(pr.get(f"{nm} ZERO", 0) or 0)
                if no_c:   chips += f'<span class="chip no">{no_c} NO {nm}</span>'
                if zero_c: chips += f'<span class="chip zero">{zero_c} Zero {nm}</span>'
            pen_lookup[adv] = chips

    def row_chips(sub, fcs):
        out = ""
        for fc in fcs:
            if fc not in sub.columns: continue
            no_c   = (sub[fc].str.contains(r"\bNO\b", case=False, na=False) &
                      ~sub[fc].str.contains("ZERO|YES", case=False, na=False)).sum()
            zero_c = sub[fc].str.contains("Zero", case=False, na=False).sum()
            nm     = fc.replace(" Flag","")
            if no_c:   out += f'<span class="chip no">{no_c} NO {nm}</span>'
            if zero_c: out += f'<span class="chip zero">{zero_c} Zero {nm}</span>'
        return out

    th_net = "".join(
        f'<th class="r">{c.replace("_Net","").replace("Net_","").replace("_"," ")} Net</th>'
        for c in net_cols)
    th_flg = "".join(f'<th>{fc.replace(" Flag","")}</th>' for fc in flag_cols)

    tbl_id = f"tbl_{uid}"
    rows   = ""
    ai     = 0

    for advisor, adf in df.groupby("Advisor Name", sort=True):
        aid   = f"{uid}_a{ai}"; ai += 1
        clean = clean_adv(advisor)
        cnt   = len(adf)
        chips = pen_lookup.get(advisor, row_chips(adf, flag_cols)) if pen_df is not None \
                else row_chips(adf, flag_cols)

        td_net = "".join(
            f'<td class="r">{fmt_amt(adf[c].sum()) if c in adf.columns else "—"}</td>'
            for c in net_cols)

        rows += (f'<tr class="r-adv" onclick="tog(\'{aid}\')">'
                 f'<td><span class="arr" id="arr_{aid}">▶</span>{clean}'
                 f'<span class="cnt">{cnt}</span>'
                 f'<span class="adv-chips">{chips}</span></td>'
                 f'<td></td><td></td>{td_net}'
                 f'{"".join("<td></td>" for _ in flag_cols)}</tr>')

        mi = 0
        for model, mdf in adf.groupby("Model", sort=True):
            mid  = f"{aid}_m{mi}"; mi += 1
            mcnt = len(mdf)
            mchips = row_chips(mdf, flag_cols)
            td_net_m = "".join(
                f'<td class="r">{fmt_amt(mdf[c].sum()) if c in mdf.columns else "—"}</td>'
                for c in net_cols)

            c_mod = clean_mod(model)
            rows += (f'<tr class="r-mod p-{aid}" data-mod="{c_mod}" onclick="tog(\'{mid}\')" style="display:none">'
                     f'<td style="padding-left:22px">'
                     f'<span class="arr" id="arr_{mid}">▶</span>{model}'
                     f'<span class="cnt">{mcnt}</span>'
                     f'<span class="adv-chips">{mchips}</span></td>'
                     f'<td></td><td></td>{td_net_m}'
                     f'{"".join("<td></td>" for _ in flag_cols)}</tr>')

            for _, row in mdf.sort_values("Bill Date").iterrows():
                jc  = row.get("Job Card No","—")
                reg = row.get("Registration No","—")
                dt  = pd.to_datetime(row.get("Bill Date"), errors="coerce")
                ds  = dt.strftime("%d-%b") if pd.notna(dt) else "—"
                td_net_j = "".join(
                    f'<td class="r">{fmt_amt(row.get(c))}</td>' for c in net_cols)
                td_flg_j = "".join(
                    f'<td>{flag_chip(str(row.get(fc,"—")))}</td>' for fc in flag_cols)
                rows += (f'<tr class="r-jc p-{mid}" style="display:none">'
                         f'<td style="padding-left:40px;font-size:11px;color:#6B7280">{jc}</td>'
                         f'<td style="font-size:11px">{reg}</td>'
                         f'<td style="font-size:11px">{ds}</td>'
                         f'{td_net_j}{td_flg_j}</tr>')

    return f"""<div class="tbl-badges">{badges}</div>
<div class="tbl-wrap" id="{tbl_id}">
<table>
<thead><tr>
  <th style="min-width:200px">Advisor / Model / Job Card</th>
  <th>Reg No</th><th>Date</th>
  {th_net}{th_flg}
</tr></thead>
<tbody>{rows}</tbody>
</table>
</div>
<div class="legend">
  <span><span class="chip no">NO</span> Absent from bill</span>
  <span><span class="chip zero">Zero</span> Billed ₹0</span>
  <span><span class="chip yes">YES</span> Correctly billed</span>
  <span style="margin-left:auto"><span class="cnt">n</span> Job card count</span>
</div>"""

# ═══════════════════════════════════════════════════════════════
#  PENETRATION TABLE  — collapsible Advisor → Model → JC
# ═══════════════════════════════════════════════════════════════

def pen_table(pen_df, unbilled_df, pct_defs, uid):
    """
    Unified table: Advisor → Model → JC
    Advisor row : bills count + penetration % + NO/Zero chips
    Model row   : count + avg net per service (Net FRT ÷ count)
    JC row      : JC No | Reg·Date | combined flag+amount per service
    Alternating 2-colour left-border bands per advisor block.
    """
    if pen_df.empty:
        return '<div class="empty">No penetration data</div>'

    active_defs = [(nm,pc,yc,zc,nc,cf) for nm,pc,yc,zc,nc,cf in pct_defs
                   if pc in pen_df.columns]
    if not active_defs:
        return '<div class="empty">No % columns found</div>'

    # Net col lookup: service name → column in unbilled_df
    def net_col(nm, df):
        return next((c for c in [f"{nm}_Net", f"Net_{nm}",
                     f"{nm.capitalize()}_Net"] if c in df.columns), None)

    # Single unified header — no % suffix, no separate JC columns
    th_svc = "".join(f'<th class="r">{nm}</th>' for nm,*_ in active_defs)

    tot_bills = 0
    tot_yes   = {nm: 0 for nm,*_ in active_defs}
    rows      = ""
    ai        = 0

    for _, pr in pen_df.iterrows():
        adv   = str(pr.get("Advisor Name","—"))
        clean = clean_adv(adv)
        bills = int(pr.get("Total Bills", 0) or 0)
        tot_bills += bills
        aid  = f"pen_{uid}_a{ai}"
        band = f"band{ai % 2}"
        ai  += 1

        # Advisor row — % per service
        svc_cells = ""
        for nm,pc,yc,zc,nc,cf in active_defs:
            pv = pr.get(pc, 0)
            tot_yes[nm] += int(pr.get(yc, 0) or 0)
            svc_cells += (f'<td class="r">'
                          f'<span class="pct {cf(pv)}">'
                          f'{fmt_pct_ratio(pv) if float(pv or 0) <= 1 else fmt_pct_100(pv)}'
                          f'</span></td>')

        # NO/Zero problem chips on advisor row
        chips = ""
        for nm,pc,yc,zc,nc,cf in active_defs:
            no_c   = int(pr.get(f"{nm} NO",  0) or 0)
            zero_c = int(pr.get(f"{nm} ZERO", 0) or 0)
            if no_c:   chips += f'<span class="chip no">{no_c} NO {nm}</span>'
            if zero_c: chips += f'<span class="chip zero">{zero_c} Zero {nm}</span>'

        rows += (f'<tr class="r-adv {band}" data-aid="{aid}" data-adv="{clean}" onclick="tog(\'{aid}\')">'
                 f'<td><span class="arr" id="arr_{aid}">▶</span>{clean}'
                 f'<span class="adv-chips">{chips}</span></td>'
                 f'<td class="r">{bills}</td>{svc_cells}</tr>')

        # Model rows — avg Net FRT ÷ count per service
        if not unbilled_df.empty and "Advisor Name" in unbilled_df.columns:
            adv_df = unbilled_df[unbilled_df["Advisor Name"] == adv]
            mi = 0
            for model, mdf in adv_df.groupby("Model", sort=True):
                mid  = f"{aid}_m{mi}"; mi += 1
                mcnt = len(mdf)

                avg_cells = ""
                for nm,pc,yc,zc,nc,cf in active_defs:
                    nc2 = net_col(nm, mdf)
                    if nc2:
                        m_avg = mdf[nc2].sum() / mcnt if mcnt else 0
                        avg_cells += f'<td class="r" style="font-size:11px;color:#6B7280">{fmt_amt(m_avg)}</td>'
                    else:
                        avg_cells += '<td class="r" style="color:#9CA3AF">—</td>'

                c_mod = clean_mod(model)
                rows += (f'<tr class="r-mod {band} p-{aid}" data-mod="{c_mod}" onclick="tog(\'{mid}\')" style="display:none">'
                         f'<td style="padding-left:22px">'
                         f'<span class="arr" id="arr_{mid}">▶</span>{model}'
                         f'<span class="cnt">{mcnt}</span></td>'
                         f'<td class="r" style="color:#9CA3AF">{mcnt}</td>'
                         f'{avg_cells}</tr>')

                # JC rows — reuse same columns:
                #   YES  → actual net amount collected (green tint)
                #   Zero → ₹0 (amber tint)
                #   NO   → — (red tint)
                for _, jrow in mdf.sort_values("Bill Date").iterrows():
                    jc  = jrow.get("Job Card No","—")
                    reg = jrow.get("Registration No","—")
                    dt  = pd.to_datetime(jrow.get("Bill Date"), errors="coerce")
                    ds  = dt.strftime("%d-%b") if pd.notna(dt) else "—"

                    jc_cells = ""
                    for nm,pc,yc,zc,nc,cf in active_defs:
                        fc  = f"{nm} Flag"
                        nc2 = net_col(nm, mdf)
                        fv  = str(jrow.get(fc, "")).upper()
                        if "YES" in fv:
                            amt = fmt_amt(jrow.get(nc2)) if nc2 else "—"
                            jc_cells += f'<td class="r" style="color:#2E7D32;font-size:11px">{amt}</td>'
                        elif "ZERO" in fv:
                            jc_cells += '<td class="r" style="color:#E65100;font-size:11px">₹0</td>'
                        elif "NO" in fv:
                            jc_cells += '<td class="r" style="color:#C62828;font-size:11px">—</td>'
                        else:
                            jc_cells += '<td></td>'

                    rows += (f'<tr class="r-jc {band} p-{mid}" style="display:none">'
                             f'<td style="padding-left:40px;font-size:11px;color:#6B7280">{jc}</td>'
                             f'<td style="font-size:11px;color:#6B7280;white-space:nowrap">{reg} · {ds}</td>'
                             f'{jc_cells}</tr>')

    # Total row — % across all advisors
    tb = tot_bills or 1
    tot_cells = "".join(
        f'<td class="r"><span class="pct {cf(tot_yes[nm]/tb)}">'
        f'{fmt_pct_ratio(tot_yes[nm]/tb)}</span></td>'
        for nm,pc,yc,zc,nc,cf in active_defs)
    rows += f'<tr class="tot-row"><td>TOTAL</td><td class="r">{tot_bills}</td>{tot_cells}</tr>'

    return (f'<div class="tbl-wrap"><table>'
            f'<thead><tr>'
            f'<th style="min-width:180px">Advisor / Model / Job Card</th>'
            f'<th class="r">Bills</th>{th_svc}'
            f'</tr></thead>'
            f'<tbody>{rows}</tbody>'
            f'</table></div>'
            f'<div class="legend">'
            f'<span>Advisor row: penetration %</span>'
            f'<span>Model row: avg Net FRT ÷ JC count</span>'
            f'<span style="color:#2E7D32">● YES = amount collected</span>'
            f'<span style="color:#E65100">● Zero = ₹0 billed</span>'
            f'<span style="color:#C62828">● — = not billed</span>'
            f'</div>')

# ═══════════════════════════════════════════════════════════════
#  AVG LABOUR TABLE
# ═══════════════════════════════════════════════════════════════

def pms_attention_section(pms_df, uid):
    """
    Eyecatching red-border card showing only JCs where PMS Flag = NO or Zero.
    Grouped by advisor (collapsed by default), shows count in header.
    """
    if pms_df.empty or "PMS Flag" not in pms_df.columns:
        return ""

    bad = pms_df[
        pms_df["PMS Flag"].str.contains(r"\bNO\b|Zero", case=False, na=False)
    ].copy()

    total = len(bad)
    if total == 0:
        return (f'<div class="attn-section">'
                f'<div class="attn-hdr">'
                f'<span class="attn-title">PMS Labour Alert</span>'
                f'<span style="font-size:10px;color:#065F46;background:#D1FAE5;'
                f'padding:3px 10px;border-radius:20px;border:1px solid #A7F3D0">'
                f'✓ All PMS billed</span></div></div>')

    rows = ""
    ai   = 0
    for advisor, adf in bad.groupby("Advisor Name", sort=True):
        aid   = f"attn_{uid}_a{ai}"; ai += 1
        clean = clean_adv(advisor)
        cnt   = len(adf)
        no_c  = (adf["PMS Flag"].str.contains(r"\bNO\b", case=False, na=False) &
                 ~adf["PMS Flag"].str.contains("ZERO|YES", case=False, na=False)).sum()
        zero_c= adf["PMS Flag"].str.contains("Zero", case=False, na=False).sum()
        chips = ""
        if no_c:   chips += f'<span class="chip no">{no_c} NO</span>'
        if zero_c: chips += f'<span class="chip zero">{zero_c} Zero</span>'

        rows += (f'<tr class="r-adv" onclick="tog(\'{aid}\')" '
                 f'style="background:#FEF2F2">'
                 f'<td><span class="arr" id="arr_{aid}">▶</span>{clean}'
                 f'<span class="adv-chips">{chips}</span></td>'
                 f'<td></td><td></td><td></td></tr>')

        for _, row in adf.sort_values("Bill Date").iterrows():
            jc  = row.get("Job Card No","—")
            reg = row.get("Registration No","—")
            dt  = pd.to_datetime(row.get("Bill Date"), errors="coerce")
            ds  = dt.strftime("%d-%b") if pd.notna(dt) else "—"
            fv  = str(row.get("PMS Flag","—"))
            fc  = "no" if "NO" in fv.upper() and "ZERO" not in fv.upper() else "zero"
            amt = fmt_amt(row.get("PMS_Net"))
            rows += (f'<tr class="r-jc p-{aid}" style="display:none">'
                     f'<td style="padding-left:32px;font-size:11px;color:#6B7280">{jc}</td>'
                     f'<td style="font-size:11px;color:#6B7280">{reg}</td>'
                     f'<td style="font-size:11px;color:#6B7280">{ds}</td>'
                     f'<td><div class="jc-svc">'
                     f'<span class="jc-amt">{amt}</span>'
                     f'<span class="jc-flag {fc}">{fv}</span>'
                     f'</div></td></tr>')

    return (f'<div class="attn-section">'
            f'<div class="attn-hdr">'
            f'<span class="attn-title">'
            f'<span class="attn-dot"></span>PMS Labour Alert</span>'
            f'<span class="attn-cnt">{total} JC{"s" if total>1 else ""} — PMS not billed</span>'
            f'</div>'
            f'<div class="tbl-wrap"><table>'
            f'<thead><tr>'
            f'<th style="min-width:180px">Advisor / Job Card</th>'
            f'<th>Reg No</th><th>Date</th><th>PMS Net</th>'
            f'</tr></thead>'
            f'<tbody>{rows}</tbody>'
            f'</table></div></div>')

# ═══════════════════════════════════════════════════════════════
#  ATTENTION SECTION — FR2 / FR3  WA / WB NO/Zero alert
# ═══════════════════════════════════════════════════════════════

def fr_attention_section(fr_df, uid, label="FR2"):
    """
    Same pulsing red card as PMS attention section but for FR2 or FR3.
    Shows JCs where WA Flag OR WB Flag = NO or Zero.
    """
    if fr_df.empty:
        return ""
    flag_cols = [c for c in ["WA Flag", "WB Flag"] if c in fr_df.columns]
    if not flag_cols:
        return ""

    bad = fr_df[
        fr_df[flag_cols].apply(
            lambda col: col.str.contains(r"\bNO\b|Zero", case=False, na=False)
        ).any(axis=1)
    ].copy()

    total = len(bad)
    if total == 0:
        return (f'<div class="attn-section">'
                f'<div class="attn-hdr">'
                f'<span class="attn-title">{label} WA/WB Alert</span>'
                f'<span style="font-size:10px;color:#065F46;background:#D1FAE5;'
                f'padding:3px 10px;border-radius:20px;border:1px solid #A7F3D0">'
                f'✓ All {label} WA/WB billed</span></div></div>')

    rows = ""
    ai   = 0
    for advisor, adf in bad.groupby("Advisor Name", sort=True):
        aid   = f"frattn_{uid}_a{ai}"; ai += 1
        clean = clean_adv(advisor)
        chips = ""
        for fc in flag_cols:
            if fc not in adf.columns: continue
            nm     = fc.replace(" Flag","")
            no_c   = (adf[fc].str.contains(r"\bNO\b", case=False, na=False) &
                      ~adf[fc].str.contains("ZERO|YES", case=False, na=False)).sum()
            zero_c = adf[fc].str.contains("Zero", case=False, na=False).sum()
            if no_c:   chips += f'<span class="chip no">{no_c} NO {nm}</span>'
            if zero_c: chips += f'<span class="chip zero">{zero_c} Zero {nm}</span>'

        rows += (f'<tr class="r-adv" onclick="tog(\'{aid}\')" '
                 f'style="background:#FEF2F2">'
                 f'<td><span class="arr" id="arr_{aid}">▶</span>{clean}'
                 f'<span class="adv-chips">{chips}</span></td>'
                 f'<td></td><td></td>'
                 f'{"".join("<td></td>" for _ in flag_cols)}</tr>')

        for _, row in adf.sort_values("Bill Date").iterrows():
            jc  = row.get("Job Card No","—")
            reg = row.get("Registration No","—")
            dt  = pd.to_datetime(row.get("Bill Date"), errors="coerce")
            ds  = dt.strftime("%d-%b") if pd.notna(dt) else "—"
            flag_cells = ""
            for fc in flag_cols:
                fv  = str(row.get(fc,"—"))
                fvu = fv.upper()
                fc2 = "no" if ("NO" in fvu and "ZERO" not in fvu) else ("zero" if "ZERO" in fvu else "yes")
                net_c = "Net_" + fc.replace(" Flag","")
                amt   = fmt_amt(row.get(net_c, row.get(fc.replace(" Flag","_Net"), None)))
                flag_cells += (f'<td><div class="jc-svc">'
                               f'<span class="jc-amt">{amt}</span>'
                               f'<span class="jc-flag {fc2}">{fv}</span>'
                               f'</div></td>')
            rows += (f'<tr class="r-jc p-{aid}" style="display:none">'
                     f'<td style="padding-left:32px;font-size:11px;color:#6B7280">{jc}</td>'
                     f'<td style="font-size:11px;color:#6B7280">{reg}</td>'
                     f'<td style="font-size:11px;color:#6B7280">{ds}</td>'
                     f'{flag_cells}</tr>')

    th_flags = "".join(f'<th>{fc.replace(" Flag","")}</th>' for fc in flag_cols)
    return (f'<div class="attn-section">'
            f'<div class="attn-hdr">'
            f'<span class="attn-title">'
            f'<span class="attn-dot"></span>{label} WA/WB Alert</span>'
            f'<span class="attn-cnt">{total} JC{"s" if total>1 else ""} — WA/WB not fully billed</span>'
            f'</div>'
            f'<div class="tbl-wrap"><table>'
            f'<thead><tr>'
            f'<th style="min-width:180px">Advisor / Job Card</th>'
            f'<th>Reg No</th><th>Date</th>{th_flags}'
            f'</tr></thead>'
            f'<tbody>{rows}</tbody>'
            f'</table></div></div>')


# ═══════════════════════════════════════════════════════════════
#  SUMMARY DASHBOARD  (All Locations view)
# ═══════════════════════════════════════════════════════════════

def summary_dashboard(locations, loc_map, data, wc_map=None):
    """
    Two-tab dashboard: PMS tab + FR2/FR3 tab.
    One row per location, clickable → switches to that location's detail.
    Used when __ALL__ is selected in the dropdown.
    """
    pb_locs = set()
    if wc_map:
        pb_locs = {l for l in locations if str(wc_map.get(l, "")).strip().upper() in ("PBA", "POB")}
    pms_df  = data["pms"]
    fr2_df  = data["fr2"]
    fr3_df  = data["fr3"]
    pen_df  = data["pms_pen"]
    fp2_df  = data["fr2_pen"]
    fp3_df  = data["fr3_pen"]

    # ── PMS summary tab ──────────────────────────────────────────
    pms_rows = ""
    pms_tot = {
        "all": {"bills":0,"unbilled":0},
        "mainland": {"bills":0,"unbilled":0},
        "portblair": {"bills":0,"unbilled":0}
    }
    pms_yes = {
        "all": {nm:0 for nm,*_ in PMS_PEN_DEFS},
        "mainland": {nm:0 for nm,*_ in PMS_PEN_DEFS},
        "portblair": {nm:0 for nm,*_ in PMS_PEN_DEFS}
    }

    for loc in locations:
        lid   = _loc_id(loc)
        short = loc_map.get(loc, loc)
        lcdf  = flt(pms_df, loc)
        pp    = flt_pen(pen_df, loc)
        unbill= len(lcdf)
        zone  = "portblair" if loc in pb_locs else "mainland"

        tb = pp["Total Bills"].sum() if not pp.empty and "Total Bills" in pp.columns else 0
        pms_tot["all"]["bills"]   += tb
        pms_tot[zone]["bills"]    += tb
        pms_tot["all"]["unbilled"]+= unbill
        pms_tot[zone]["unbilled"] += unbill

        pct_cells = ""
        for nm,pc,yc,zc,nc,cf in PMS_PEN_DEFS:
            if not pp.empty and yc in pp.columns and tb:
                pct = pp[yc].sum() / tb
                yv  = int(pp[yc].sum())
                pms_yes["all"][nm] += yv
                pms_yes[zone][nm]  += yv
                pct_cells += (f'<td class="r">'
                              f'<span class="dash-pct {cf(pct)}">{fmt_pct_ratio(pct)}</span>'
                              f'</td>')
            else:
                pct_cells += '<td class="r">—</td>'

        ucls = "dash-cnt" if unbill > 0 else "dash-cnt ok"

        pb_attr = ' data-pb="1"' if loc in pb_locs else ' data-pb="0"'
        
        # Get advisors for this location from penetration data
        loc_advs = set()
        if not pp.empty and "Advisor Name" in pp.columns:
            loc_advs = set(pp["Advisor Name"].dropna().unique())
        adv_list = ",".join(sorted(loc_advs)) if loc_advs else ""
        adv_attr = f' data-advs="{adv_list}"'
        
        pms_rows += (f'<tr onclick="dashGoto(\'{lid}\')"{pb_attr}{adv_attr}>'
                     f'<td><div class="dash-loc">{short}</div>'
                     f'<div class="dash-sub">{loc}</div></td>'
                     f'<td class="r"><span class="{ucls}">{unbill}</span></td>'
                     f'{pct_cells}'
                     f'</tr>')

    # PMS total rows
    pms_tot_html = ""
    for z, z_lbl in [("mainland", f"MAINLAND — {len([l for l in locations if l not in pb_locs])} locations"), 
                     ("portblair", f"PORT BLAIR — {len(pb_locs)} locations"), 
                     ("all", f"TOTAL — {len(locations)} locations")]:
        if "PORT BLAIR — 0" in z_lbl: continue
        tb_z = pms_tot[z]["bills"] or 1
        tot_pct = "".join(
            f'<td class="r"><span class="dash-pct {cf(pms_yes[z][nm]/tb_z)}">'
            f'{fmt_pct_ratio(pms_yes[z][nm]/tb_z)}</span></td>'
            for nm,pc,yc,zc,nc,cf in PMS_PEN_DEFS)
        pms_tot_html += (f'<tr class="dash-tot" data-tot="{z}">'
                         f'<td>{z_lbl}</td>'
                         f'<td class="r">{pms_tot[z]["unbilled"]}</td>'
                         f'{tot_pct}</tr>')
    pms_rows += pms_tot_html

    pms_th = "".join(f'<th class="r">{nm} %</th>' for nm,*_ in PMS_PEN_DEFS)
    pms_tab = (f'<div class="dash-wrap"><table class="dash-tbl">'
               f'<thead><tr>'
               f'<th style="min-width:280px">Location</th>'
               f'<th class="r">Billed</th>'
               f'{pms_th}'
               f'</tr></thead>'
               f'<tbody>{pms_rows}</tbody>'
               f'</table></div>')

    # ── FR2/FR3 summary tab ──────────────────────────────────────
    fr_rows = ""
    fr_tot = {
        "all": {"fr2":0,"fr3":0,"f2y":0,"f3y":0,"f2b":0,"f3b":0,"f2wy":0,"f3wy":0},
        "mainland": {"fr2":0,"fr3":0,"f2y":0,"f3y":0,"f2b":0,"f3b":0,"f2wy":0,"f3wy":0},
        "portblair": {"fr2":0,"fr3":0,"f2y":0,"f3y":0,"f2b":0,"f3b":0,"f2wy":0,"f3wy":0}
    }

    for loc in locations:
        lid   = _loc_id(loc)
        short = loc_map.get(loc, loc)
        lf2   = flt(fr2_df, loc)
        lf3   = flt(fr3_df, loc)
        lp2   = flt_pen(fp2_df, loc)
        lp3   = flt_pen(fp3_df, loc)
        zone  = "portblair" if loc in pb_locs else "mainland"

        f2_cnt = len(lf2)
        f3_cnt = len(lf3)
        fr_tot["all"]["fr2"] += f2_cnt; fr_tot[zone]["fr2"] += f2_cnt
        fr_tot["all"]["fr3"] += f3_cnt; fr_tot[zone]["fr3"] += f3_cnt

        def fr_pct(pen, k, flag="WA"):
            if pen.empty or f"{flag} YES" not in pen.columns: return None, 0, 0
            tb = pen["Total Bills"].sum() if "Total Bills" in pen.columns else 0
            yes= pen[f"{flag} YES"].sum()
            return (yes/tb*100 if tb else None), int(yes), int(tb)

        f2p, f2y, f2b = fr_pct(lp2, "fr2", "WA")
        f2w, f2wy, f2wb = fr_pct(lp2, "fr2", "WB")
        f3p, f3y, f3b = fr_pct(lp3, "fr3", "WA")
        f3w, f3wy, f3wb = fr_pct(lp3, "fr3", "WB")
        fr_tot["all"]["f2y"] += f2y; fr_tot["all"]["f2b"] += f2b; fr_tot["all"]["f2wy"] += f2wy
        fr_tot[zone]["f2y"] += f2y; fr_tot[zone]["f2b"] += f2b; fr_tot[zone]["f2wy"] += f2wy
        fr_tot["all"]["f3y"] += f3y; fr_tot["all"]["f3b"] += f3b; fr_tot["all"]["f3wy"] += f3wy
        fr_tot[zone]["f3y"] += f3y; fr_tot[zone]["f3b"] += f3b; fr_tot[zone]["f3wy"] += f3wy

        def pct_cell(v):
            if v is None: return '<td class="r">—</td>'
            return (f'<td class="r"><span class="dash-pct {cls_fr_100(v)}">'
                    f'{fmt_pct_100(v)}</span></td>')

        f2_cls = "dash-cnt" if f2_cnt > 0 else "dash-cnt ok"
        f3_cls = "dash-cnt" if f3_cnt > 0 else "dash-cnt ok"
        pb_attr = ' data-pb="1"' if loc in pb_locs else ' data-pb="0"'
        
        # Get advisors for this location from FR2/FR3 penetration data
        loc_advs = set()
        if not lp2.empty and "Advisor Name" in lp2.columns:
            loc_advs.update(lp2["Advisor Name"].dropna().unique())
        if not lp3.empty and "Advisor Name" in lp3.columns:
            loc_advs.update(lp3["Advisor Name"].dropna().unique())
        adv_list = ",".join(sorted(loc_advs)) if loc_advs else ""
        adv_attr = f' data-advs="{adv_list}"'
        
        fr_rows += (f'<tr onclick="dashGoto(\'{lid}\')"{pb_attr}{adv_attr}>'
                    f'<td><div class="dash-loc">{short}</div>'
                    f'<div class="dash-sub">{loc}</div></td>'
                    f'<td class="r"><span class="{f2_cls}">{f2_cnt}</span></td>'
                    f'{pct_cell(f2p)}'
                    f'{pct_cell(f2w)}'
                    f'<td class="r"><span class="{f3_cls}">{f3_cnt}</span></td>'
                    f'{pct_cell(f3p)}'
                    f'{pct_cell(f3w)}'
                    f'</tr>')

    def tot_pct_cell(v):
        if v is None: return '<td class="r">—</td>'
        return (f'<td class="r"><span class="dash-pct {cls_fr_100(v)}">'
                f'{fmt_pct_100(v)}</span></td>')
                
    fr_tot_html = ""
    for z, z_lbl in [("mainland", f"MAINLAND — {len([l for l in locations if l not in pb_locs])} locations"), 
                     ("portblair", f"PORT BLAIR — {len(pb_locs)} locations"), 
                     ("all", f"TOTAL — {len(locations)} locations")]:
        if "PORT BLAIR — 0" in z_lbl: continue
        f2p_z = fr_tot[z]["f2y"]/fr_tot[z]["f2b"]*100 if fr_tot[z]["f2b"] else None
        f2w_z = fr_tot[z]["f2wy"]/fr_tot[z]["f2b"]*100 if fr_tot[z]["f2b"] else None
        f3p_z = fr_tot[z]["f3y"]/fr_tot[z]["f3b"]*100 if fr_tot[z]["f3b"] else None
        f3w_z = fr_tot[z]["f3wy"]/fr_tot[z]["f3b"]*100 if fr_tot[z]["f3b"] else None
        fr_tot_html += (f'<tr class="dash-tot" data-tot="{z}">'
                        f'<td>{z_lbl}</td>'
                        f'<td class="r">{fr_tot[z]["fr2"]}</td>'
                        f'{tot_pct_cell(f2p_z)}'
                        f'{tot_pct_cell(f2w_z)}'
                        f'<td class="r">{fr_tot[z]["fr3"]}</td>'
                        f'{tot_pct_cell(f3p_z)}'
                        f'{tot_pct_cell(f3w_z)}'
                        f'</tr>')
    fr_rows += fr_tot_html

    fr_tab = (f'<div class="dash-wrap"><table class="dash-tbl">'
              f'<thead><tr>'
              f'<th style="min-width:280px">Location</th>'
              f'<th class="r">FR2 Billed</th>'
              f'<th class="r">FR2 WA %</th>'
              f'<th class="r">FR2 WB %</th>'
              f'<th class="r">FR3 Billed</th>'
              f'<th class="r">FR3 WA %</th>'
              f'<th class="r">FR3 WB %</th>'
              f'</tr></thead>'
              f'<tbody>{fr_rows}</tbody>'
              f'</table></div>')

    hint = '<span style="font-size:10px;color:#9CA3AF">Click any row to drill into that location</span>'
    return (f'<div class="loc-sec" id="ls___ALL__" style="display:none">'
            f'<div class="sec" style="margin-bottom:12px">'
            f'<div class="sec-hdr"><span>All Locations — Summary Dashboard</span>{hint}</div>'
            f'<div id="lsp___ALL___pms">{pms_tab}</div>'
            f'<div id="lsp___ALL___fr" style="display:none">{fr_tab}</div>'
            f'</div></div>')




def build_missed_labour_page(leak_df, uid="global"):
    """
    Renders Missed Labour Revenue using existing CSS classes.
    uid must be unique per call — prevents duplicate HTML element IDs.
    Returns raw HTML; caller wraps in lsp_{lid}_avg.
    """
    if leak_df is None or leak_df.empty:
        return '<div class="empty">No missed labour data for this period.</div>'
        
    tot = leak_df["Missed Revenue"].sum()
    nc  = leak_df[leak_df["Leak Type"] == "Not Charged"]["Missed Revenue"].sum()
    fd  = leak_df[leak_df["Leak Type"] == "Fully Discounted"]["Missed Revenue"].sum()

    def _kpi(lbl, val, cls="neu"):
        return (f'<div class="kpi">'
                f'<div class="kpi-lbl">{lbl}</div>'
                f'<div class="kpi-val {cls}">{val}</div>'
                f'</div>')

    src_cards = ""
    for src in ["PMS", "FR2", "FR3"]:
        v = leak_df[leak_df["Job Source"] == src]["Missed Revenue"].sum() \
            if "Job Source" in leak_df.columns else 0.0
        src_cards += _kpi(src + " Lost", fmt_amt(v))

    kpis = (
        '<div class="kpi-row">'
        + _kpi("Total Revenue Lost",      fmt_amt(tot), "lo")
        + _kpi("Not Charged (NO)",        fmt_amt(nc),  "lo"  if nc else "neu")
        + _kpi("Fully Discounted (ZERO)", fmt_amt(fd),  "mid" if fd else "neu")
        + src_cards
        + '</div>'
    )

    def _agg(group_col):
        return (
            leak_df.groupby(group_col)
            .apply(lambda x: pd.Series({
                "NC":  x[x["Leak Type"] == "Not Charged"]["Missed Revenue"].sum(),
                "FD":  x[x["Leak Type"] == "Fully Discounted"]["Missed Revenue"].sum(),
                "Tot": x["Missed Revenue"].sum(),
            }))
            .reset_index()
            .sort_values("Tot", ascending=False)
        )

    def _ranked_tbl(df_agg, col_label):
        if df_agg.empty:
            return '<div class="empty">No data.</div>'
        rows = "".join(
            f'<tr><td>{r[col_label]}</td>'
            f'<td class="r">{fmt_amt(r["NC"])}</td>'
            f'<td class="r">{fmt_amt(r["FD"])}</td>'
            f'<td class="r" style="font-weight:500;color:#A32D2D">{fmt_amt(r["Tot"])}</td></tr>'
            for _, r in df_agg.iterrows()
        )
        return (
            f'<div class="tbl-wrap"><table>'
            f'<thead><tr><th style="min-width:180px">{col_label}</th>'
            f'<th class="r">Not Charged</th>'
            f'<th class="r">Fully Discounted</th>'
            f'<th class="r">Total Lost</th>'
            f'</tr></thead><tbody>{rows}</tbody></table></div>'
        )

    svc_agg  = _agg("Service Type")
    svc_rows = "".join(
        f'<tr><td><strong>{r["Service Type"]}</strong></td>'
        f'<td class="r">{fmt_amt(r["NC"])}</td>'
        f'<td class="r">{fmt_amt(r["FD"])}</td>'
        f'<td class="r" style="font-weight:500;color:#A32D2D">{fmt_amt(r["Tot"])}</td></tr>'
        for _, r in svc_agg.iterrows()
    )
    svc_tbl = (
        '<div class="tbl-wrap"><table>'
        '<thead><tr><th style="min-width:120px">Service</th>'
        '<th class="r">Not Charged</th>'
        '<th class="r">Fully Discounted</th>'
        '<th class="r">Total Lost</th>'
        f'</tr></thead><tbody>{svc_rows}</tbody></table></div>'
    )

    loc_tbl = _ranked_tbl(_agg("Location").head(30), "Location")
    adv_tbl = _ranked_tbl(_agg("Advisor Name").head(20), "Advisor Name")

    mod_agg = (
        leak_df.groupby("Model")
        .apply(lambda x: pd.Series({
            "NO":   len(x[x["Leak Type"] == "Not Charged"]),
            "ZERO": len(x[x["Leak Type"] == "Fully Discounted"]),
            "Tot":  x["Missed Revenue"].sum(),
        }))
        .reset_index()
        .sort_values("Tot", ascending=False)
        .head(20)
    )
    mod_rows = "".join(
        f'<tr><td>{r["Model"]}</td>'
        f'<td class="r">{int(r["NO"])}</td>'
        f'<td class="r">{int(r["ZERO"])}</td>'
        f'<td class="r" style="font-weight:500;color:#A32D2D">{fmt_amt(r["Tot"])}</td></tr>'
        for _, r in mod_agg.iterrows()
    )
    mod_tbl = (
        '<div class="tbl-wrap"><table>'
        '<thead><tr><th style="min-width:160px">Model</th>'
        '<th class="r">NO Count</th><th class="r">ZERO Count</th><th class="r">Total Lost</th>'
        f'</tr></thead><tbody>{mod_rows}</tbody></table></div>'
    )

    dr_rows = ""
    for di, (loc, l_df) in enumerate(leak_df.groupby("Location", sort=True)):
        ltot = l_df["Missed Revenue"].sum()
        lid2 = f"ml_{uid}_{di}"
        nc_c = len(l_df[l_df["Leak Type"] == "Not Charged"])
        fd_c = len(l_df[l_df["Leak Type"] == "Fully Discounted"])
        adv_rows = ""
        for ai, (adv, a_df) in enumerate(l_df.groupby("Advisor Name", sort=True)):
            atot = a_df["Missed Revenue"].sum()
            aid2 = f"mla_{uid}_{di}_{ai}"
            jc_rows = ""
            for _, r in a_df.sort_values("Missed Revenue", ascending=False).iterrows():
                chip_cls = "no" if r["Leak Type"] == "Not Charged" else "zero"
                jc_rows += (
                    f'<tr class="r-jc p-{aid2}" style="display:none">'
                    f'<td style="padding-left:40px;font-size:11px;color:#6B7280">{r["Job Card No"]}</td>'
                    f'<td style="font-size:11px">{r["Model"]}</td>'
                    f'<td><span class="chip {chip_cls}">{r["Leak Type"]}</span></td>'
                    f'<td style="font-size:11px;color:#6B7280">{r["Service Type"]}</td>'
                    f'<td class="r" style="font-weight:500;color:#A32D2D">{fmt_amt(r["Missed Revenue"])}</td>'
                    f'</tr>'
                )
            adv_rows += (
                f'<tr class="r-adv p-{lid2}" onclick="tog(\'{aid2}\')" style="display:none">'
                f'<td style="padding-left:22px"><span class="arr" id="arr_{aid2}">&#9658;</span>{adv}</td>'
                f'<td class="r">{len(a_df[a_df["Leak Type"]=="Not Charged"])}</td>'
                f'<td class="r">{len(a_df[a_df["Leak Type"]=="Fully Discounted"])}</td>'
                f'<td></td>'
                f'<td class="r" style="font-weight:500">{fmt_amt(atot)}</td>'
                f'</tr>' + jc_rows
            )
        dr_rows += (
            f'<tr class="r-adv" onclick="tog(\'{lid2}\')">'
            f'<td><span class="arr" id="arr_{lid2}">&#9658;</span>{loc}</td>'
            f'<td class="r">{nc_c}</td><td class="r">{fd_c}</td><td></td>'
            f'<td class="r" style="font-weight:500;color:#A32D2D">{fmt_amt(ltot)}</td>'
            f'</tr>' + adv_rows
        )

    dr_tbl = (
        '<div class="tbl-wrap"><table>'
        '<thead><tr>'
        '<th style="min-width:200px">Location / Advisor / Job Card</th>'
        '<th class="r">NO</th><th class="r">ZERO</th><th>Service</th><th class="r">Revenue Lost</th>'
        f'</tr></thead><tbody>{dr_rows}</tbody></table></div>'
        '<div class="legend">'
        '<span><span class="chip no">Not Charged</span> Labour absent from bill</span>'
        '<span><span class="chip zero">Fully Discounted</span> Billed at &#8377;0</span>'
        '</div>'
    )

    return (
        kpis
        + sec_card("Top Leakage by Service", "", svc_tbl)
        + sec_card("Location Ranking", "", loc_tbl)
        + sec_card("Advisor Ranking (Top 20)", "", adv_tbl)
        + sec_card("Model Ranking (Top 20)", "", mod_tbl)
        + sec_card(
            "Drilldown &#8212; Location &#8594; Advisor &#8594; Job Card",
            '<span style="font-size:10px;color:#9CA3AF">Click row to expand</span>',
            dr_tbl,
          )
    )




def count_spans(loc, pms_df, fr2_df, fr3_df):
    lid = _loc_id(loc)
    p   = len(flt(pms_df, loc))
    r2  = len(flt(fr2_df, loc))
    r3  = len(flt(fr3_df, loc))
    def sp(k, n, lbl):
        return (f'<span id="lc_{k}_{lid}" data-count="{n}" '
                f'data-label="{lbl}" style="display:none"></span>')
    return sp("pms",p,f"PMS {p}") + sp("fr2",r2,f"FR2 {r2}") + sp("fr3",r3,f"FR3 {r3}")

def sec_card(title, badge, body):
    return (f'<div class="sec"><div class="sec-hdr">'
            f'<span>{title}</span>{badge}</div>{body}</div>')

# ═══════════════════════════════════════════════════════════════
#  LOCATION SECTION
# ═══════════════════════════════════════════════════════════════

def loc_section(loc, data, loc_map, compare_locs, uid, is_pb=False):
    pdf   = flt(data["pms"],     loc)
    f2    = flt(data["fr2"],     loc)
    f3    = flt(data["fr3"],     loc)
    pp    = flt_pen(data["pms_pen"], loc)
    fp2   = flt_pen(data["fr2_pen"], loc)
    fp3   = flt_pen(data["fr3_pen"], loc)
    short = loc_map.get(loc, loc)
    ap = ""

    heading = (f'<div class="loc-heading">'
               f'<div><div class="loc-heading-name">{short}</div>'
               f'<div class="loc-heading-sub">{loc}</div></div>'
               f'{ap}</div>')

    # PMS panel — attention alert + unified pen_table (no separate unbilled_table)
    pms_panel = (
        build_kpis_pms(pdf, pp) +
        pms_attention_section(pdf, f"{uid}attn") +
        sec_card("PMS Penetration — Advisor Detail",
                 '<span style="font-size:10px;color:#9CA3AF">Click advisor to expand models → job cards</span>',
                 pen_table(pp, pdf, PMS_PEN_DEFS, f"{uid}pp")))


    # FR2/FR3 panel — same structure as PMS (attention + pen_table, no separate unbilled_table)
    hint = '<span style="font-size:10px;color:#9CA3AF">Click advisor to expand models → job cards</span>'
    fr_panel = (
        build_kpis_fr(f2, fp2, f3, fp3) +
        fr_attention_section(f2, f"{uid}f2attn", "FR2") +
        sec_card("FR2 Penetration — Advisor Detail", hint,
                 pen_table(fp2, f2, FR_PEN_DEFS, f"{uid}f2p")) +
        fr_attention_section(f3, f"{uid}f3attn", "FR3") +
        sec_card("FR3 Penetration — Advisor Detail", hint,
                 pen_table(fp3, f3, FR_PEN_DEFS, f"{uid}f3p")))

    # Labour Leakage removed — now served by native Labour Compliance & Leakage dashboard
    cspans = count_spans(loc, data["pms"], data["fr2"], data["fr3"])
    lid    = _loc_id(loc)
    pb_attr = ' data-pb="1"' if is_pb else ' data-pb="0"'

    return (f'<div class="loc-sec" id="ls_{lid}" style="display:none"{pb_attr}>'
            f'{cspans}{heading}'
            f'<div id="lsp_{lid}_pms">{pms_panel}</div>'
            f'<div id="lsp_{lid}_fr"  style="display:none">{fr_panel}</div>'
            f'</div>')

# ═══════════════════════════════════════════════════════════════
#  HTML WRAPPER
# ═══════════════════════════════════════════════════════════════

def html_wrap(title, loc_line, month, body):
    gen_dt = datetime.now().strftime("%d-%b-%Y %H:%M")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{title}</title>
  <style>{CSS}</style>
</head>
<body>
<div class="wrap">
  {body}

</div>
<script>{JS}</script>
</body>
</html>"""

# ═══════════════════════════════════════════════════════════════
#  NAV + LOC BAR
# ═══════════════════════════════════════════════════════════════

def build_nav_locbar(locations, loc_map, data, month, show_all_option=True, wc_map=None, available_months=None):
    import json
    # Identify PortBlair locations by E103 workshop code
    pb_locs = set()
    if wc_map:
        pb_locs = {l for l in locations if str(wc_map.get(l,"")).strip().upper() in ("PBA", "POB")}

    has_pb = bool(pb_locs)

    # Build period options
    period_opts = ""
    if available_months:
        for m in available_months:
            selected = 'selected' if m == month else ''
            period_opts += f'<option value="{m}" {selected}>{m}</option>'
    else:
        period_opts = f'<option value="{month}" selected>{month}</option>'

    opts = ""
    if show_all_option and len(locations) > 1:
        opts += '<option value="__ALL__">— All Locations —</option>'
    for l in locations:
        is_pb   = l in pb_locs
        pb_attr = ' data-pb="1"' if is_pb else ' data-pb="0"'
        label   = loc_map.get(l, l)
        tag     = " 🏝" if is_pb else ""
        display = f"{label}{tag} — {l}" if label != l else f"{label}{tag}"
        opts   += f'<option value="{_loc_id(l)}"{pb_attr}>{display}</option>'

    adv_dict = {}
    mod_dict = {}
    if data:
        advs = []
        mods = []
        for k in ["pms", "fr2", "fr3"]:
            df = data.get(k)
            if df is not None and not df.empty and "Location" in df.columns:
                if "Advisor Name" in df.columns:
                    advs.append(df[["Location", "Advisor Name"]].dropna())
                if "Model" in df.columns:
                    mods.append(df[["Location", "Model"]].dropna())
        if advs:
            adv_df = pd.concat(advs).drop_duplicates()
            for l, group in adv_df.groupby("Location"):
                adv_dict[_loc_id(l)] = sorted(group["Advisor Name"].apply(clean_adv).unique().tolist())
        if mods:
            mod_df = pd.concat(mods).drop_duplicates()
            for l, group in mod_df.groupby("Location"):
                mod_dict[_loc_id(l)] = sorted(group["Model"].apply(clean_mod).unique().tolist())
    
    adv_json = json.dumps(adv_dict)
    mod_json = json.dumps(mod_dict)

    page_nav = """<div class="page-nav" style="display:flex; gap:8px;">
  <div class="pnav on" data-p="page-pms" onclick="showPage('page-pms')">PMS</div>
  <div class="pnav"    data-p="page-fr"  onclick="showPage('page-fr')">FR2 / FR3</div>
</div>"""

    pb_toggle = ""
    if has_pb:
        pb_toggle = """<div class="pb-filter">
    <div class="pb-toggle">
      <div class="pb-opt on" data-pb="mainland" onclick="setPBFilter('mainland')">MP</div>
      <div class="pb-opt"    data-pb="portblair" onclick="setPBFilter('portblair')">PB</div>
      <div class="pb-opt"    data-pb="all"        onclick="setPBFilter('all')">All</div>
    </div>
  </div>"""

    top_nav_bar = f"""
  <div style="display:flex; justify-content:space-between; align-items:center; width:100%; margin-top:8px;">
    {page_nav}
    <div style="width:1px; height:24px; background:#E5E7EB; margin:0 16px;"></div>
    {pb_toggle}
  </div>""" if has_pb else f"""
  <div style="display:flex; justify-content:flex-start; align-items:center; width:100%; margin-top:8px;">
    {page_nav}
  </div>"""

    loc_bar = f"""<div class="loc-bar" style="display:flex; flex-direction:column; gap:16px; align-items:stretch; border-radius:8px; padding:16px;">
  <div style="display:flex; gap:16px; align-items:flex-end; width:100%; flex-wrap:wrap;">
    <div style="flex:1; min-width:200px;">
      <label style="display:block; margin-bottom:6px; font-size:12px; font-weight:500; color:#374151;">Period</label>
      <select id="period-sel" onchange="changePeriod(this.value)" style="width:100%; border-radius:6px; font-size:14px; border:1px solid #D1D5DB; padding:6px 10px; color:#1F2937;">
        {period_opts}
      </select>
    </div>
    <div style="flex:1; min-width:200px;">
      <label style="display:block; margin-bottom:6px; font-size:12px; font-weight:500; color:#374151;">Location</label>
      <select id="loc-sel" onchange="switchLoc(this.value)" style="width:100%; border-radius:6px; font-size:14px; border:1px solid #D1D5DB; padding:6px 10px; color:#1F2937;">{opts}</select>
    </div>
    <div style="flex:1; min-width:200px;">
      <label style="display:block; margin-bottom:6px; font-size:12px; font-weight:500; color:#374151;">Advisor Name</label>
      <select id="adv-sel" onchange="filterAdv(this.value)" style="width:100%; border-radius:6px; font-size:14px; border:1px solid #D1D5DB; padding:6px 10px; color:#1F2937;">
        <option value="__ALL__">All Advisors</option>
      </select>
    </div>
  </div>

  <details style="margin-top:4px;">
    <summary style="cursor:pointer; font-weight:500; font-size:13px; color:#4B5563; outline:none; user-select:none;">Advanced Filters</summary>
    <div style="padding-top:12px; display:flex; gap:16px; align-items:center; flex-wrap:wrap; border-top:1px solid #E5E7EB; margin-top:12px;">
      <div style="flex:1; min-width:200px; max-width:300px;">
        <label style="display:block; margin-bottom:6px; font-size:12px; font-weight:500; color:#374151;">Model</label>
        <select id="mod-sel" onchange="filterMod(this.value)" style="width:100%; border-radius:6px; font-size:14px; border:1px solid #D1D5DB; padding:6px 10px; color:#1F2937;">
          <option value="__ALL__">All Models</option>
        </select>
      </div>
    </div>
  </details>
  
  {top_nav_bar}
</div>

<script>
const ADV_MAP = {adv_json};
const MOD_MAP = {mod_json};

function updateAdvDropdown(lid) {{
  var sel = document.getElementById('adv-sel');
  if(!sel) return;
  var validAdvs = new Set();
  
  if (lid === '__ALL__') {{
     for (var loc in ADV_MAP) {{
         ADV_MAP[loc].forEach(function(a) {{ validAdvs.add(a); }});
     }}
  }} else {{
     if (ADV_MAP[lid]) {{
         ADV_MAP[lid].forEach(function(a) {{ validAdvs.add(a); }});
     }}
  }}
  
  sel.innerHTML = '<option value="__ALL__">All Advisors</option>';
  Array.from(validAdvs).sort().forEach(function(a) {{
     var opt = document.createElement('option');
     opt.value = a;
     opt.textContent = a;
     sel.appendChild(opt);
  }});
  
  // User Requirement: Automatic advisor reset when changing locations.
  sel.value = '__ALL__';
  filterAdv('__ALL__');
}}

function updateModDropdown(lid) {{
  var sel = document.getElementById('mod-sel');
  if(!sel) return;
  var validMods = new Set();
  
  if (lid === '__ALL__') {{
     for (var loc in MOD_MAP) {{
         MOD_MAP[loc].forEach(function(a) {{ validMods.add(a); }});
     }}
  }} else {{
     if (MOD_MAP[lid]) {{
         MOD_MAP[lid].forEach(function(a) {{ validMods.add(a); }});
     }}
  }}
  
  sel.innerHTML = '<option value="__ALL__">All Models</option>';
  Array.from(validMods).sort().forEach(function(a) {{
     var opt = document.createElement('option');
     opt.value = a;
     opt.textContent = a;
     sel.appendChild(opt);
  }});
  
  sel.value = '__ALL__';
  filterMod('__ALL__');
}}

function filterAdv(adv) {{
  // Collapse expanded rows first to avoid orphans
  document.querySelectorAll('.r-adv').forEach(function(r){{
    var aid = r.getAttribute('data-aid');
    if(!aid) return;
    var arr = document.getElementById('arr_'+aid);
    if(arr && arr.style.transform === 'rotate(90deg)') {{
      tog(aid);
    }}
  }});
  if(adv !== '__ALL__') {{
    document.querySelectorAll('.r-mod').forEach(function(el){{el.style.display='none';}});
    document.querySelectorAll('.r-jc').forEach(function(el){{el.style.display='none';}});
  }}

  // Apply visibility filter to Summary Dashboard
  var dashRows = document.querySelectorAll('.dash-tbl tbody tr[data-advs]');
  dashRows.forEach(function(r) {{
    if(adv === '__ALL__') {{
      r.style.display = '';
    }} else {{
      var locAdvs = r.getAttribute('data-advs');
      if(locAdvs && locAdvs.includes(adv)) {{
        r.style.display = '';
      }} else {{
        r.style.display = 'none';
      }}
    }}
  }});

  // Apply visibility filter to location sections
  var locs = document.querySelectorAll('.loc-sec');
  locs.forEach(function(l) {{
    if (l.style.display !== 'none') {{
      var rows = l.querySelectorAll('.r-adv');
      rows.forEach(function(r) {{
        var advName = r.getAttribute('data-adv');
        if(adv === '__ALL__' || advName === adv) {{
          r.style.display = '';
        }} else {{
          r.style.display = 'none';
        }}
      }});
    }}
  }});
}}


function filterMod(mod) {{
  if(mod !== '__ALL__') {{
    document.querySelectorAll('.r-jc').forEach(function(el){{el.style.display='none';}});
  }}
  
  var locs = document.querySelectorAll('.loc-sec');
  locs.forEach(function(l) {{
    if (l.style.display !== 'none') {{
      var rows = l.querySelectorAll('.r-mod');
      rows.forEach(function(r) {{
        var modName = r.getAttribute('data-mod');
        if(mod === '__ALL__') {{
          // Do not explicitly force show models as they should expand via advisor click.
          // Hide them so that toggling advisor works cleanly.
          r.style.display = 'none';
        }} else if (modName === mod) {{
          r.style.display = '';
        }} else {{
          r.style.display = 'none';
        }}
      }});
    }}
  }});
}}
</script>
"""
    return loc_bar


# ═══════════════════════════════════════════════════════════════
#  CONTACT REPORT
# ═══════════════════════════════════════════════════════════════

def build_contact_report(contact_name, locations, loc_map, month, data, wc_map=None):
    loc_labels = " · ".join(loc_map.get(l,l) for l in locations)
    nav        = build_nav_locbar(locations, loc_map, data, month, show_all_option=True, wc_map=wc_map)
    dash       = summary_dashboard(locations, loc_map, data, wc_map=wc_map) if len(locations) > 1 else ""
    sections   = "".join(
        loc_section(loc, data, loc_map, locations, uid=_loc_id(loc))
        for loc in locations)
    return html_wrap(
        f"RKM — {contact_name} — {month}",
        f"Locations: {loc_labels}",
        month, nav + dash + sections)


# ═══════════════════════════════════════════════════════════════
#  MASTER REPORT
# ═══════════════════════════════════════════════════════════════

def build_master_report(locations, loc_map, month, data, wc_map=None, available_months=None):
    pb_locs = set()
    if wc_map:
        pb_locs = {l for l in locations if str(wc_map.get(l,"")).strip().upper() in ("PBA", "POB")}
        
    nav      = build_nav_locbar(locations, loc_map, data, month, show_all_option=True, wc_map=wc_map, available_months=available_months)
    dash     = summary_dashboard(locations, loc_map, data, wc_map=wc_map)
    sections = "".join(
        loc_section(loc, data, loc_map, locations, uid=_loc_id(loc), is_pb=(loc in pb_locs))
        for loc in locations)
    return html_wrap(
        f"RKM Motors — All Locations — {month}",
        "Management View — All Locations",
        month, nav + dash + sections)

# ═══════════════════════════════════════════════════════════════
#  INDIVIDUAL LOCATION REPORT
# ═══════════════════════════════════════════════════════════════

def build_location_report(loc, loc_map, month, data, wc_map=None):
    short = loc_map.get(loc, loc)
    is_pb = False
    if wc_map and str(wc_map.get(loc,"")).strip().upper() in ("PBA", "POB"):
        is_pb = True
        
    # Single location — no dropdown, no All option
    nav   = """<div class="page-nav">
  <div class="pnav on" data-p="page-pms" onclick="showPage('page-pms')">PMS</div>
  <div class="pnav"    data-p="page-fr"  onclick="showPage('page-fr')">FR2 / FR3</div>
</div>"""
    section = loc_section(loc, data, loc_map, [loc], uid=_loc_id(loc), is_pb=is_pb)
    # Auto-show on load — no dropdown needed
    autoshow = f"""<script>
window.addEventListener('load',function(){{
  var el=document.getElementById('ls_{_loc_id(loc)}');
  if(el)el.style.display='block';
  showPage('page-pms');
}});
</script>"""
    body = nav + section
    html = html_wrap(
        f"RKM — {short} — {month}",
        f"Location: {short} — {loc}",
        month, body)
    # Inject autoshow before </body>
    return html.replace("</body>", autoshow + "</body>")

# ═══════════════════════════════════════════════════════════════
#  WHATSAPP
# ═══════════════════════════════════════════════════════════════

def _find_whatsapp_exe():
    for p in [os.path.expandvars(r"%LOCALAPPDATA%\WhatsApp\WhatsApp.exe"),
              os.path.expandvars(r"%APPDATA%\WhatsApp\WhatsApp.exe"),
              os.path.expandvars(r"%LOCALAPPDATA%\Programs\WhatsApp\WhatsApp.exe")]:
        if os.path.exists(p): return p
    return None

def wa_send(phone, message, file_path):
    try: import pyautogui, pyperclip
    except ImportError:
        print("  ✗ pip install pyautogui pyperclip"); return False
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        print(f"  ✗ File not found: {abs_path}"); return False
    exe = _find_whatsapp_exe()
    if not exe:
        print("  ✗ WhatsApp Desktop not found"); return False
    try:
        pyautogui.FAILSAFE = True
        subprocess.Popen([exe, f"--url=whatsapp://send?phone={phone}"])
        time.sleep(7)
        pyperclip.copy(message)
        pyautogui.hotkey('ctrl','v'); time.sleep(1)
        pyautogui.press('enter');     time.sleep(2)
        pyautogui.hotkey('alt','a');  time.sleep(3)
        pyautogui.press('d');         time.sleep(1)
        pyautogui.press('enter');     time.sleep(3)
        pyautogui.hotkey('ctrl','l'); time.sleep(0.5)
        pyperclip.copy(abs_path)
        pyautogui.hotkey('ctrl','v'); time.sleep(1)
        pyautogui.press('enter');     time.sleep(2)
        pyautogui.press('enter');     time.sleep(5)
        pyautogui.press('enter');     time.sleep(3)
        print(f"    ✓ Sent to +{phone}: {os.path.basename(file_path)}")
        return True
    except Exception as e:
        print(f"    ✗ Failed for +{phone}: {e}"); return False

def send_all(contacts, generated, month, loc_map):
    exe = _find_whatsapp_exe()
    if exe: subprocess.Popen([exe]); print("  Opening WhatsApp..."); time.sleep(6)
    else:   print("  ⚠ Open WhatsApp Desktop manually.")
    print("\n⚠  Do NOT touch mouse/keyboard.\n")
    time.sleep(3)
    for c in contacts:
        name  = c["name"]; phone = c["phone"]; locs = c["locations"]
        fpath = generated.get(name)
        if not fpath or not os.path.exists(fpath):
            print(f"  ⚠ Skipping {name} — file missing"); continue
        loc_label = ", ".join(loc_map.get(l,l) for l in locs)
        summary   = "\n".join(f"📍 *{loc_map.get(l,l)}*" for l in locs[:5])
        if len(locs) > 5: summary += f"\n  ...and {len(locs)-5} more"
        msg = MESSAGE_TEMPLATE.format(
            name=name, month=month, location=loc_label, summary=summary)
        print(f"→ {name} (+{phone})")
        wa_send(phone, msg, fpath)
        time.sleep(WAIT_BETWEEN)
    print("\n✓ All sends complete.")

# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print("RKM Motors — Internal Audit App  (Google Sheets)")
    print("=" * 65)
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    print(f"\nConnecting to Google Sheets: {SHEET_ID[:30]}...")
    data = load_data()

    for k, v in data.items():
        if hasattr(v, '__len__'):
            n = len(v)
            print(f"  {'checkmark' if n else 'warn'} {k:12s}: {n} rows")

    month                               = get_month(data)
    contacts, loc_map, wc_map, sort_map = load_contacts()
    locations                           = all_locs(data, sort_map=sort_map)

    if not locations:
        print("\nAll sheets empty - check SHEET_ID and service-account credentials.")
        sys.exit(1)

    print(f"Period    : {month}")
    print(f"Locations : {len(locations)}")
    print(f"Contacts  : {len(contacts)}")
    for c in contacts:
        print(f"  • {c['name']} → "
              f"{', '.join(loc_map.get(l,l) for l in c['locations'])}")

    run_date  = datetime.now().strftime("%d%b%Y")
    generated = {}

    # ── Individual per-location HTMLs → OUTPUT_DIR root ──────────
    print(f"\n{'─'*50}\nGenerating individual location reports ...")
    for loc in locations:
        safe  = re.sub(r'[\\/:*?"<>| ]', '_', loc)
        fname = f"RKM_{safe}_{run_date}.html"
        fpath = os.path.join(OUTPUT_DIR, fname)
        html  = build_location_report(loc, loc_map, month, data)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  ✓ {fname}  ({len(html)//1024} KB)")

    # ── Per-contact combined HTMLs → contact subfolders ──────────
    print(f"\n{'─'*50}\nGenerating contact reports ...")
    for c in contacts:
        name  = c["name"]
        safe  = re.sub(r'[\\/:*?"<>| ]', '_', name)
        cdir  = os.path.join(OUTPUT_DIR, safe)
        Path(cdir).mkdir(parents=True, exist_ok=True)
        fname = f"RKM_{safe}_COMBINED_{run_date}.html"
        fpath = os.path.join(cdir, fname)
        html  = build_contact_report(name, c["locations"], loc_map, month, data, wc_map=wc_map)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(html)
        generated[name] = fpath
        print(f"  ✓ {safe}/{fname}  ({len(html)//1024} KB)")

    # ── Master ALL LOCATIONS → OUTPUT_DIR root ───────────────────
    print(f"\n{'─'*50}\nGenerating master report ...")
    mfname = f"RKM_ALL_LOCATIONS_{run_date}.html"
    mpath  = os.path.join(OUTPUT_DIR, mfname)
    mhtml  = build_master_report(locations, loc_map, month, data, wc_map=wc_map)
    with open(mpath, "w", encoding="utf-8") as f:
        f.write(mhtml)
    print(f"  ✓ {mfname}  ({len(mhtml)//1024} KB)")

    print(f"\n✓ Done. Output folder:\n  {OUTPUT_DIR}")

    if not SEND_WHATSAPP:
        print("\nWhatsApp disabled. Set SEND_WHATSAPP=True to enable."); return
    if not contacts:
        print("\n⚠ No contacts."); return
    print(f"\n{'─'*50}")
    send_all(contacts, generated, month, loc_map)
    print("\n" + "="*65)


if __name__ == "__main__":
    import traceback
    try:
        main()
    except Exception:
        print("\n" + "="*65 + "\nCRASH:")
        traceback.print_exc()
        log = os.path.join(OUTPUT_DIR, "crash_log.txt")
        try:
            with open(log, "w") as f: f.write(traceback.format_exc())
            print(f"\nLog: {log}")
        except: pass
        input("\nPress Enter to close...")
