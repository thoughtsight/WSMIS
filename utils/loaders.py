import pandas as pd
import gspread
import streamlit as st
import os
import json
import time
from google.oauth2.service_account import Credentials
from typing import Dict, List, Tuple, Optional, Any, Callable
from utils.constants import SERVICE_ACCOUNT
from services.error_handler import with_error_context, LoaderError
from services.logger import app_logger

SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Maximum allowed duration (seconds) for any single Google Sheets network operation.
# Used both as the gspread socket timeout and as an elapsed-time guard.
GSHEET_TIMEOUT = 20


def _timed_op(label: str, func: Callable[[], Any]) -> Any:
    """Run a Google Sheets network operation with structured logging, timing,
    and a hard timeout guard.

    Logs the start and completion of each operation and measures elapsed time.
    Converts any failure (including socket timeouts) or an over-budget duration
    into a descriptive LoaderError that names the exact operation that failed.
    """
    app_logger.info(f"[GSheets] ▶ {label} — starting...")
    start = time.perf_counter()
    try:
        result = func()
    except Exception as e:
        elapsed = time.perf_counter() - start
        app_logger.error(f"[GSheets] ✗ {label} — FAILED after {elapsed:.2f}s: {e}")
        # Surface socket/read timeouts explicitly as a timeout LoaderError.
        if elapsed >= GSHEET_TIMEOUT or "timeout" in str(e).lower() or "timed out" in str(e).lower():
            raise LoaderError(
                f"Google Sheets operation '{label}' timed out after {elapsed:.2f}s "
                f"(limit {GSHEET_TIMEOUT}s): {e}"
            ) from e
        raise LoaderError(f"Google Sheets operation '{label}' failed after {elapsed:.2f}s: {e}") from e

    elapsed = time.perf_counter() - start
    app_logger.info(f"[GSheets] ✓ {label} — completed in {elapsed:.2f}s")
    if elapsed >= GSHEET_TIMEOUT:
        app_logger.error(f"[GSheets] ✗ {label} — exceeded {GSHEET_TIMEOUT}s budget ({elapsed:.2f}s)")
        raise LoaderError(
            f"Google Sheets operation '{label}' exceeded the {GSHEET_TIMEOUT}s budget "
            f"(took {elapsed:.2f}s)"
        )
    return result


@st.cache_resource
@with_error_context(LoaderError)
def get_gc() -> gspread.client.Client:
    """Authenticates and returns the Google Sheets client.
    Priority: Streamlit Secrets > Environment Variable > File (local dev only).
    A 20-second network timeout is applied so stalled connections fail fast.
    """
    from config.environment import get_google_credentials
    try:
        creds = get_google_credentials()
        gc = gspread.authorize(creds)
        gc.set_timeout(GSHEET_TIMEOUT)
        return gc
    except Exception as e:
        raise LoaderError(str(e)) from e

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

TARGET_TAB = "MP_PB_Targets"
TARGET_COLS_REQUIRED = ["Month Name","Location Name",
                        "WS_Labour_Target","BS_Labour_Target",
                        "WS_Parts_Target","BS_Parts_Target"]
TARGET_COLS_OPTIONAL = ["Appr_Lab_Disc","Appr_Parts_Disc"]
TARGET_COLS = TARGET_COLS_REQUIRED + TARGET_COLS_OPTIONAL

APPROVED_DISC_TAB = "MP_PB_Targets"

DEFAULT_APPR_LAB_DISC   = 15.0
DEFAULT_APPR_PARTS_DISC = 1.0


@st.cache_resource(ttl=300)
@with_error_context(LoaderError)
def load_targets(sheet_id: str) -> pd.DataFrame:
    """Load WS/BS monthly targets from a separate sheet tab. Returns empty DF if sheet not found."""
    try:
        wb = _timed_op(f"load_targets: open spreadsheet [{sheet_id}]", lambda: get_gc().open_by_key(sheet_id))
        ws = _timed_op(
            f"load_targets: list worksheets / locate '{TARGET_TAB}'",
            lambda: next((s for s in wb.worksheets() if s.title.strip() == TARGET_TAB), None),
        )
        if not ws:
            # Optional targets sheet not found - safe to return empty DataFrame
            return pd.DataFrame(columns=TARGET_COLS)
        records = _timed_op(f"load_targets: fetch records from '{TARGET_TAB}'", lambda: ws.get_all_records())
        df = pd.DataFrame(records)
        
        # Schema validation: required columns must be present
        missing_required = [col for col in TARGET_COLS_REQUIRED if col not in df.columns]
        if missing_required:
            raise LoaderError(f"Target sheet '{TARGET_TAB}' is missing required columns: {', '.join(missing_required)}. "
                            f"Please add these columns to the Google Sheet before loading targets.")
        
        # Schema validation: optional columns generate warnings if missing
        missing_optional = [col for col in TARGET_COLS_OPTIONAL if col not in df.columns]
        if missing_optional:
            import streamlit as st
            st.warning(f"⚠️ Target sheet '{TARGET_TAB}' is missing optional columns: {', '.join(missing_optional)}. "
                      f"Default values will be used: Appr_Lab_Disc={DEFAULT_APPR_LAB_DISC}%, Appr_Parts_Disc={DEFAULT_APPR_PARTS_DISC}%")
        
        for c in TARGET_COLS[2:]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
        return df
    except LoaderError:
        # Already descriptive (named operation + timing) — propagate unchanged.
        raise
    except gspread.exceptions.APIError as e:
        raise LoaderError(f"Google Sheets API error loading targets: {e}") from e
    except gspread.exceptions.GSpreadException as e:
        raise LoaderError(f"Google Sheets authentication/access error loading targets: {e}") from e
    except Exception as e:
        raise LoaderError(f"Failed to load targets: {e}") from e

@st.cache_resource(ttl=300)
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
    wb = _timed_op(f"load_data: open spreadsheet [{sheet_id}]", lambda: get_gc().open_by_key(sheet_id))
    try:
        ws = _timed_op(f"load_data: load worksheet '{sheet_tab}'", lambda: wb.worksheet(sheet_tab))
    except LoaderError as le:
        # The named worksheet was not found; fall back to a case-insensitive / JC-TAT search.
        if not isinstance(le.__cause__, gspread.exceptions.WorksheetNotFound):
            raise
        target = sheet_tab.lower()
        ws = _timed_op(
            f"load_data: locate worksheet (fallback) for '{sheet_tab}'",
            lambda: next((s for s in wb.worksheets() if s.title.lower() == target), None)
            or next((s for s in wb.worksheets() if "JC" in s.title.upper() and "TAT" in s.title.upper()), None),
        )
        if not ws:
            raise ValueError(f"Could not find sheet tab matching '{sheet_tab}'")

    records = _timed_op(f"load_data: fetch records from '{ws.title}'", lambda: ws.get_all_records())
    return pd.DataFrame(records)

@with_error_context(LoaderError)
def load_raw_expense(sheet_id: str) -> pd.DataFrame:
    """Raw loading logic for EXP sheet. Required sheet - errors propagate as LoaderError."""
    try:
        wb = _timed_op(f"load_expense: open spreadsheet [{sheet_id}]", lambda: get_gc().open_by_key(sheet_id))
        exp_ws = _timed_op(
            "load_expense: list worksheets / locate 'EXP'",
            lambda: next((s for s in wb.worksheets() if s.title.strip() == "EXP."), None)
            or next((s for s in wb.worksheets() if s.title.strip() == "EXP"), None),
        )
        if not exp_ws:
            raise ValueError("EXP sheet not found in workbook")
        exp_data = _timed_op("load_expense: fetch values from 'EXP'", lambda: exp_ws.get_all_values())
        if not exp_data or len(exp_data) < 2:
            raise ValueError("EXP sheet is empty or has no data")
        exp_df = pd.DataFrame(exp_data[1:], columns=exp_data[0])
        # Drop empty columns
        exp_df = exp_df[[c for c in exp_df.columns if str(c).strip() != ""]]
        return exp_df
    except LoaderError:
        # Already descriptive (named operation + timing) — propagate unchanged.
        raise
    except gspread.exceptions.APIError as e:
        raise LoaderError(f"Google Sheets API error loading EXP sheet: {e}") from e
    except gspread.exceptions.GSpreadException as e:
        raise LoaderError(f"Google Sheets authentication/access error loading EXP sheet: {e}") from e
    except Exception as e:
        raise LoaderError(f"Failed to load EXP sheet: {e}") from e
