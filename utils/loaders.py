import pandas as pd
import gspread
import streamlit as st
import os
import json
from google.oauth2.service_account import Credentials
from typing import Dict, List, Tuple, Optional, Any
from utils.constants import SERVICE_ACCOUNT
from services.error_handler import with_error_context, LoaderError

SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
@with_error_context(LoaderError)
def get_gc() -> gspread.client.Client:
    """Authenticates and returns the Google Sheets client.
    Priority: Streamlit Secrets > Environment Variable > File (local dev only).
    """
    # 1. Try Streamlit Secrets (Cloud/Deployment)
    if "service_account" in st.secrets:
        creds_dict = st.secrets["service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(creds)

    # 2. Try Environment Variable (JSON string)
    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        try:
            creds_dict = json.loads(service_account_json)
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            return gspread.authorize(creds)
        except json.JSONDecodeError as e:
            raise LoaderError(f"Invalid JSON in GOOGLE_SERVICE_ACCOUNT_JSON: {e}") from e

    # 3. Try File (local development only - file should be gitignored)
    if os.path.exists(SERVICE_ACCOUNT):
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT, scopes=SCOPES)
        return gspread.authorize(creds)

    raise LoaderError(
        "Google credentials not found. Set one of:\n"
        "- Streamlit Secret: service_account (JSON)\n"
        "- Environment Variable: GOOGLE_SERVICE_ACCOUNT_JSON (JSON string)\n"
        "- Local file: service_account.json (development only)"
    )

def _read_sheet(sheet_id: str, tab_name: str) -> pd.DataFrame:
    """Read a Google Sheet tab into a DataFrame. Returns empty DF only for missing optional sheets."""
    try:
        ws = get_gc().open_by_key(sheet_id).worksheet(tab_name)
        data = ws.get_all_values()
        if not data or len(data) < 2:
            return pd.DataFrame()
        headers = data[0]
        seen = {}
        for i, h in enumerate(headers):
            h_str = str(h).strip()
            if not h_str: continue
            if h_str in seen:
                seen[h_str] += 1
                headers[i] = f"{h_str}_{seen[h_str]}"
            else:
                seen[h_str] = 0
                headers[i] = h_str
        df = pd.DataFrame(data[1:], columns=headers)
        # Drop columns with blank headers
        df = df[[c for c in df.columns if str(c).strip() != ""]]
        # Auto-cast strings to numbers like get_all_records() did
        for c in df.columns:
            try: df[c] = pd.to_numeric(df[c])
            except Exception: pass
        # Rename Net_WA/WB to WA/WB_Net to match Excel if needed
        df.rename(columns={"Net_WA": "WA_Net", "Net_WB": "WB_Net"}, inplace=True)
        return df
    except gspread.exceptions.WorksheetNotFound:
        # Optional sheet not found - safe to return empty DataFrame
        return pd.DataFrame()
    except gspread.exceptions.APIError as e:
        # Quota or API errors - must propagate
        raise LoaderError(f"Google Sheets API error reading '{tab_name}': {e}") from e
    except gspread.exceptions.GSpreadException as e:
        # Authentication or access errors - must propagate
        raise LoaderError(f"Google Sheets authentication/access error reading '{tab_name}': {e}") from e
    except Exception as e:
        # Network or other errors - must propagate
        raise LoaderError(f"Failed to read sheet '{tab_name}': {e}") from e

@with_error_context(LoaderError)
def load_contacts(sheet_id: str) -> Tuple[List[Any], Dict[str, str], Dict[str, str], Dict[str, int]]:
    """
    Load location mapping from Google Sheets 'Help' tab.
    """
    df = _read_sheet(sheet_id, "Help")
    loc_map: Dict[str, str] = {}
    wc_map: Dict[str, str] = {}
    sort_map: Dict[str, int] = {}
    contacts: List[Any] = []

    if df.empty:
        print("  ⚠ Help sheet is empty or missing")
        return contacts, loc_map, wc_map, sort_map

    def _find(keywords: List[str], exact: bool = False) -> Optional[str]:
        for c in df.columns:
            clean_c = str(c).strip().lower()
            if exact:
                if clean_c == keywords[0].lower(): return str(c)
            else:
                if all(k.lower() in clean_c for k in keywords): return str(c)
        return None

    loc_col = _find(["Location Name"], exact=True) or _find(["location", "name"])
    sort_col = _find(["Location Number"], exact=True) or _find(["location", "number"])
    wc_col = _find(["Loc CD"], exact=True) or _find(["loc", "cd"])
    short_col = _find(["short"])

    if loc_col is None:
        print("  ⚠ Help sheet: 'Location Name' column not found")
        return contacts, loc_map, wc_map, sort_map

    for _, row in df.iterrows():
        loc = str(row.get(loc_col, "")).strip()
        if not loc or loc.lower() == "nan":
            continue
        short = str(row.get(short_col, "")).strip() if short_col else ""
        loc_map[loc] = short if short and short.lower() != "nan" else loc
        wc_map[loc] = str(row.get(wc_col, "")).strip() if wc_col else ""
        try:    sort_map[loc] = int(float(row.get(sort_col, 999)))
        except: sort_map[loc] = 999

    return contacts, loc_map, wc_map, sort_map

TARGET_TAB = "WS_BS_Targets"
TARGET_COLS = ["Month Name","Location Name",
               "WS_Labour_Target","BS_Labour_Target",
               "WS_Parts_Target","BS_Parts_Target"]

@st.cache_data(ttl=300)
@with_error_context(LoaderError)
def load_targets(sheet_id: str) -> pd.DataFrame:
    """Load WS/BS monthly targets from a separate sheet tab. Returns empty DF if sheet not found."""
    try:
        wb = get_gc().open_by_key(sheet_id)
        ws = next((s for s in wb.worksheets() if s.title.strip() == TARGET_TAB), None)
        if not ws:
            # Optional targets sheet not found - safe to return empty DataFrame
            return pd.DataFrame(columns=TARGET_COLS)
        df = pd.DataFrame(ws.get_all_records())
        for c in TARGET_COLS[2:]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
        return df
    except gspread.exceptions.APIError as e:
        raise LoaderError(f"Google Sheets API error loading targets: {e}") from e
    except gspread.exceptions.GSpreadException as e:
        raise LoaderError(f"Google Sheets authentication/access error loading targets: {e}") from e
    except Exception as e:
        raise LoaderError(f"Failed to load targets: {e}") from e

@st.cache_data(ttl=300)
@with_error_context(LoaderError)
def load_unbilled_sheets(sheet_id: str) -> Dict[str, pd.DataFrame]:
    """
    Load unbilled data from three Google Sheets tabs: Unbilled_PMS, Unbilled_FR2, Unbilled_FR3.
    Returns a dictionary with keys: 'pms', 'fr2', 'fr3' containing DataFrames.
    Missing sheets return empty DataFrames; auth/network errors propagate as LoaderError.
    """
    result = {"pms": pd.DataFrame(), "fr2": pd.DataFrame(), "fr3": pd.DataFrame()}
    try:
        wb = get_gc().open_by_key(sheet_id)
        tab_names = ["Unbilled_PMS", "Unbilled_FR2", "Unbilled_FR3"]
        result_keys = ["pms", "fr2", "fr3"]
        
        for tab_name, key in zip(tab_names, result_keys):
            try:
                ws = next((s for s in wb.worksheets() if s.title.strip() == tab_name), None)
                if ws:
                    df = pd.DataFrame(ws.get_all_records())
                    if not df.empty:
                        result[key] = df
                # Sheet not found - leave as empty DataFrame (optional)
            except gspread.exceptions.APIError as e:
                raise LoaderError(f"Google Sheets API error loading '{tab_name}': {e}") from e
            except gspread.exceptions.GSpreadException as e:
                raise LoaderError(f"Google Sheets authentication/access error loading '{tab_name}': {e}") from e
            except Exception as e:
                raise LoaderError(f"Failed to load '{tab_name}': {e}") from e
    except gspread.exceptions.APIError as e:
        raise LoaderError(f"Google Sheets API error loading unbilled sheets: {e}") from e
    except gspread.exceptions.GSpreadException as e:
        raise LoaderError(f"Google Sheets authentication/access error loading unbilled sheets: {e}") from e
    except Exception as e:
        raise LoaderError(f"Failed to load unbilled sheets: {e}") from e
    return result

@with_error_context(LoaderError)
def load_raw_worksheet(sheet_id: str, sheet_tab: str) -> pd.DataFrame:
    """Raw loading logic for main WSMIS data."""
    wb = get_gc().open_by_key(sheet_id)
    try:
        ws = wb.worksheet(sheet_tab)
    except gspread.exceptions.WorksheetNotFound:
        target = sheet_tab.lower()
        ws = next((s for s in wb.worksheets() if s.title.lower() == target), None)
        if not ws:
            ws = next((s for s in wb.worksheets() if "JC" in s.title.upper() and "TAT" in s.title.upper()), None)
        if not ws:
            raise ValueError(f"Could not find sheet tab matching '{sheet_tab}'")
    
    return pd.DataFrame(ws.get_all_records())

@with_error_context(LoaderError)
def load_raw_expense(sheet_id: str) -> pd.DataFrame:
    """Raw loading logic for EXP sheet. Required sheet - errors propagate as LoaderError."""
    try:
        wb = get_gc().open_by_key(sheet_id)
        exp_ws = next((s for s in wb.worksheets() if s.title.strip() == "EXP."), None)
        if not exp_ws:
            exp_ws = next((s for s in wb.worksheets() if s.title.strip() == "EXP"), None)
        if not exp_ws:
            raise ValueError("EXP sheet not found in workbook")
        exp_data = exp_ws.get_all_values()
        if not exp_data or len(exp_data) < 2:
            raise ValueError("EXP sheet is empty or has no data")
        exp_df = pd.DataFrame(exp_data[1:], columns=exp_data[0])
        # Drop empty columns
        exp_df = exp_df[[c for c in exp_df.columns if str(c).strip() != ""]]
        return exp_df
    except gspread.exceptions.APIError as e:
        raise LoaderError(f"Google Sheets API error loading EXP sheet: {e}") from e
    except gspread.exceptions.GSpreadException as e:
        raise LoaderError(f"Google Sheets authentication/access error loading EXP sheet: {e}") from e
    except Exception as e:
        raise LoaderError(f"Failed to load EXP sheet: {e}") from e
