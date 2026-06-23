# TARGET_USAGE_MAP — WSMIS Targets & Discount Thresholds Audit

**Date:** 2026-06-23
**Scope:** Usage audit of `targets_df`, `load_targets()`, `load_discount_thresholds()`
**Status:** Complete

---

## 1. Loader Layer (`utils/loaders.py`)

### 1.1 Constants

| Constant | Value | Line | Purpose |
|----------|-------|------|---------|
| `TARGET_TAB` | `"MP_PB_Targets"` | 156 | Google Sheet tab name for WS/BS targets |
| `APPROVED_DISC_TAB` | `"MP_PB_Targets"` | 161 | Google Sheet tab name for approved discount thresholds |
| `TARGET_COLS` | `["Month Name","Location Name","WS_Labour_Target","BS_Labour_Target","WS_Parts_Target","BS_Parts_Target"]` | 157-159 | Expected columns for target data |
| `DEFAULT_APPR_LAB_DISC` | `15.0` | 166 | Default labour discount % when sheet lacks columns |
| `DEFAULT_APPR_PARTS_DISC` | `1.0` | 167 | Default parts discount % when sheet lacks columns |

### 1.2 Functions

#### `load_targets(sheet_id)` — Line 239
- **Returns:** `pd.DataFrame` with `TARGET_COLS`
- **Behavior:** Opens spreadsheet → finds tab matching `TARGET_TAB` → reads all records → strips column names → converts numeric columns
- **Cache:** `@st.cache_resource(ttl=300)` (5 min)
- **Fallback:** Returns empty DataFrame with `TARGET_COLS` if tab not found

#### `load_discount_thresholds(sheet_id)` — Line 171
- **Returns:** `pd.DataFrame` with columns `["Location Name", "Appr_Lab_Disc", "Appr_Parts_Disc"]`
- **Behavior:** Opens spreadsheet → finds tab matching `APPROVED_DISC_TAB` → reads all records → strips column names → tries to find approved discount columns (pattern: `"labour" + "disc" + "appr"` and `"parts" + "disc" + "appr"`)
- **Cache:** `@st.cache_resource(ttl=300)` (5 min)
- **Fallback:** If approved discount columns absent, returns defaults for all locations found in the sheet
- **Error handling:** Never raises to UI for missing optional columns — falls back to defaults

---

## 2. Consumer Layer — Data Flow

### 2.1 Loading Points

| Location | Function Called | Tab Read | Purpose |
|----------|----------------|----------|---------|
| `app.py:896` | `load_targets(CLIENTS[sel_client]["sheet_id"])` | `MP_PB_Targets` | Load targets for page routing |
| `command_center.py:121` | `load_targets(sheet_id)` | `MP_PB_Targets` | Independent load for executive KPIs |
| `discount.py:915` | `load_discount_thresholds(sheet_id)` | `MP_PB_Targets` | Independent load for discount thresholds |

### 2.2 Consumer Hierarchy

```
app.py (main entry)
├── load_targets() → targets_df
├── render_page_router(..., targets_df, ...)
│   ├── Targets page (app.py:770)
│   │   └── views/performance/targets.py
│   │       └── render(df_act, targets_df, pairs)
│   ├── Discount page (app.py:741)
│   │   └── views/commercial/discount.py
│   │       └── render(df, pairs, comparison_mode, selected_months)
│   │           └── load_discount_thresholds() ← INDEPENDENT LOAD
│   └── Executive page (app.py:777)
│       └── views/executive/command_center.py
│           └── render(df, pairs, alerts, comparison_mode, selected_months)
│               └── load_targets() ← INDEPENDENT LOAD
```

---

## 3. Detailed Consumer Analysis

### 3.1 `app.py` — Main Entry Point

**Loading:**
- Line 891: `targets_df = pd.DataFrame(columns=TARGET_COLS)` (default)
- Line 896: `targets_df = load_targets(CLIENTS[sel_client]["sheet_id"])`
- Line 980: Passes `targets_df` to `render_page_router()`

**Passing to pages:**
- Targets page (line 770): `safe_render(render, df_filtered_cp, targets_df, pairs)` — receives `targets_df` as 2nd param
- Discount page (line 742): `safe_render(render, df_filtered_cp, pairs, comparison_mode, selected_months)` — does NOT receive `targets_df`
- Executive page (line 779): `safe_render(render, df_filtered_full, pairs, comparison_mode, selected_months)` — does NOT receive `targets_df`

### 3.2 `views/performance/targets.py` — Targets Page

**Receives:** `targets_df` as parameter (line 14: `def render(df_act, targets_df, pairs)`)

**Usage:**
- Checks if empty (line 19)
- Filters by Month Name (line 31): `tgt = targets_df[targets_df["Month Name"].isin(act["Month Name"].unique())]`
- Aggregates by location, merges with actuals (lines 40-54)
- Renders achievement KPIs and charts

**Mutations:** None — only reads and filters

### 3.3 `views/executive/command_center.py` — Executive Command Center

**Loads independently:** Line 121: `targets_df = load_targets(sheet_id) if sheet_id else pd.DataFrame()`
**Default:** Line 123: `targets_df = pd.DataFrame()`

**Usage:**
- Filters by Month Name (line 125): `tgt_cp = targets_df[targets_df["Month Name"].isin(cp["Month Name"].unique())]`
- Sums target columns for KPIs (line 143): `tgt_rev = tgt_cp["WS_Labour_Target"].sum() + tgt_cp["BS_Labour_Target"].sum() + tgt_cp["WS_Parts_Target"].sum() + tgt_cp["BS_Parts_Target"].sum()`
- Calculates revenue vs target percentage (line 144)

**Mutations:** None — only reads and filters

### 3.4 `views/commercial/discount.py` — Discount Dashboard

**Loads independently:** Line 915: `targets = load_discount_thresholds(sheet_id)`

**Usage:**
- Passes to `_compute_discount_metrics(cp, pp, targets)` (line 929)
- Computes discount metrics against thresholds

**Mutations:** None — only reads and filters

---

## 4. Duplicate Reader Issue — CRITICAL FINDING

### 4.1 Same Tab, Different Functions

| Function | Constant Used | Tab Value |
|----------|---------------|-----------|
| `load_targets()` | `TARGET_TAB` | `"MP_PB_Targets"` |
| `load_discount_thresholds()` | `APPROVED_DISC_TAB` | `"MP_PB_Targets"` |

**Both functions read from the exact same Google Sheet tab.**

### 4.2 Triple Load for Same Data

When the app starts and a user navigates:
1. **app.py:896** — loads `MP_PB_Targets` via `load_targets()` → cached
2. **command_center.py:121** — loads `MP_PB_Targets` via `load_targets()` → same cache
3. **discount.py:915** — loads `MP_PB_Targets` via `load_discount_thresholds()` → separate cache

Since both functions use `@st.cache_resource(ttl=300)`, they maintain **separate caches** despite reading the same tab. This means:
- Two API calls to Google Sheets for the same data on first load
- Two separate cache entries for the same tab
- Potential inconsistency if one cache refreshes before the other

### 4.3 Schema Assumption

The `load_discount_thresholds()` function assumes the tab may contain approved discount columns (pattern: `"labour" + "disc" + "appr"` and `"parts" + "disc" + "appr"`). If absent, it falls back to defaults. The `load_targets()` function reads the same tab but expects `TARGET_COLS`.

**If the sheet lacks approved discount columns:**
- `load_targets()` reads 6 columns successfully
- `load_discount_thresholds()` reads the same 6 columns but returns defaults for discount thresholds

**If the sheet adds approved discount columns later:**
- `load_targets()` ignores them (only reads `TARGET_COLS`)
- `load_discount_thresholds()` uses them

---

## 5. Direct Google Sheets Reads — Audit

### 5.1 All gspread Usage Locations

| File | Line | Usage | Type |
|------|------|-------|------|
| `utils/loaders.py` | 56-64 | `get_gc()` — authorization | **Loader** |
| `utils/loaders.py` | 73 | `open_by_key(sheet_id).worksheet(tab_name)` | **Loader** |
| `utils/loaders.py` | 181 | `get_gc().open_by_key(sheet_id)` | **Loader** |
| `utils/loaders.py` | 242 | `get_gc().open_by_key(sheet_id)` | **Loader** |
| `utils/loaders.py` | 276 | `get_gc().open_by_key(sheet_id)` | **Loader** |
| `utils/loaders.py` | 305 | `get_gc().open_by_key(sheet_id)` | **Loader** |
| `utils/loaders.py` | 328 | `get_gc().open_by_key(sheet_id)` | **Loader** |
| `app.py` | 16 | `import gspread` | Import only |
| `config/environment.py` | 22 | `SCOPES` definition | Config |
| `tests/test_golden_snapshot.py` | 7 | `from utils.loaders import load_raw_worksheet` | Test |

### 5.2 Verdict

**ALL Google Sheets reads are centralized in `utils/loaders.py`.** No direct reads exist outside this file.

Files with gspread references are limited to:
- `app.py`: Import only (no direct API calls)
- `config/environment.py`: OAuth scope definitions
- `ui/export_buttons.py`: MIME type for Excel export (not gspread)
- `views/operations/reports.py`: openpyxl for Excel writing (not gspread)
- `tests/test_golden_snapshot.py`: Uses `load_raw_worksheet` (properly through loader)

---

## 6. Mutations After Loading — Audit

### 6.1 Search Results

Searched for:
- `targets_df.drop`, `targets_df.rename`, `targets_df.columns`, `targets_df.pop`, `targets_df.del`
- `targets_df[`, `targets_df =`

### 6.2 Findings

| File | Line | Operation | Type |
|------|------|-----------|------|
| `app.py` | 891 | `targets_df = pd.DataFrame(columns=TARGET_COLS)` | Default initialization |
| `app.py` | 896 | `targets_df = load_targets(...)` | Assignment |
| `command_center.py` | 121 | `targets_df = load_targets(sheet_id)` | Assignment |
| `command_center.py` | 123 | `targets_df = pd.DataFrame()` | Default initialization |
| `command_center.py` | 125 | `targets_df[targets_df["Month Name"].isin(...)]` | Filter (read-only) |
| `targets.py` | 31 | `targets_df[targets_df["Month Name"].isin(...)]` | Filter (read-only) |

### 6.3 Verdict

**NO mutations found.** All consumers only:
1. Filter by Month Name (read-only)
2. Read columns
3. Sum/aggregate values

No column drops, renames, or structural modifications exist.

---

## 7. Summary Table

| Consumer | Loader Used | Tab Read | Receives from app.py | Independent Load | Mutations |
|----------|-------------|----------|----------------------|------------------|-----------|
| `app.py` → `render_page_router` | `load_targets()` | `MP_PB_Targets` | N/A (is the source) | No | None |
| `views/performance/targets.py` | None (receives param) | N/A | Yes (`targets_df`) | No | None |
| `views/executive/command_center.py` | `load_targets()` | `MP_PB_Targets` | No | Yes | None |
| `views/commercial/discount.py` | `load_discount_thresholds()` | `MP_PB_Targets` | No | Yes | None |

---

## 8. Risk Assessment

### 8.1 Data Consistency Risk — MEDIUM
- Three separate loads of the same Google Sheet tab
- Separate caches may refresh at different times
- Discount thresholds and targets may be temporarily out of sync

### 8.2 API Usage Risk — LOW
- `@st.cache_resource(ttl=300)` mitigates repeated API calls
- But duplicate caches mean 2x cache memory for the same data

### 8.3 Schema Evolution Risk — MEDIUM
- `load_discount_thresholds()` uses pattern matching to find columns
- If sheet columns change names, fallback to defaults silently
- No validation that approved discount columns exist

### 8.4 Maintenance Risk — HIGH
- Two functions reading the same tab with different assumptions
- Future developers may modify one without the other
- Tab name duplicated in two constants (`TARGET_TAB` and `APPROVED_DISC_TAB`)

---

## 9. Recommendations

### 9.1 Immediate (Before Parts Module Freeze)

1. **Consolidate tab name constants:**
   ```python
   # utils/loaders.py
   MP_PB_TARGETS_TAB = "MP_PB_Targets"  # Single source of truth
   TARGET_TAB = MP_PB_TARGETS_TAB       # Deprecated alias
   APPROVED_DISC_TAB = MP_PB_TARGETS_TAB # Deprecated alias
   ```

2. **Add cross-reference comment:**
   ```python
   # NOTE: load_discount_thresholds() reads the same tab as load_targets()
   # Both use MP_PB_Targets. Approved discount columns are optional.
   ```

### 9.2 Short-Term (Next Sprint)

3. **Consider consolidating into single loader:**
   - Create `load_targets_and_thresholds(sheet_id)` that returns both
   - Single cache entry, single API call
   - Return tuple: `(targets_df, discount_thresholds_df)`

4. **Add schema validation logging:**
   - Log when approved discount columns are not found
   - Log when fallback defaults are used
   - Help debugging in production

### 9.3 Long-Term

5. **Separate tabs for targets and discount thresholds:**
   - Current: Both read from `MP_PB_Targets`
   - Proposed: Move discount thresholds to `MP_PB_Discount_Thresholds`
   - Benefits: Independent schema evolution, clearer data ownership

6. **Add unit tests for loader functions:**
   - Test with missing tab
   - Test with missing columns
   - Test with correct schema
   - Test cache behavior

---

## 10. Appendix: File References

| File | Lines | Purpose |
|------|-------|---------|
| `utils/loaders.py` | 156-161 | Constants: `TARGET_TAB`, `APPROVED_DISC_TAB`, `TARGET_COLS` |
| `utils/loaders.py` | 169-235 | `load_discount_thresholds()` function |
| `utils/loaders.py` | 237-264 | `load_targets()` function |
| `app.py` | 891-896 | Load targets in main entry |
| `app.py` | 980 | Pass targets to page router |
| `app.py` | 767-770 | Route to targets page |
| `app.py` | 739-742 | Route to discount page |
| `app.py` | 776-779 | Route to executive page |
| `views/performance/targets.py` | 14 | `render(df_act, targets_df, pairs)` signature |
| `views/performance/targets.py` | 31 | Filter targets by Month Name |
| `views/executive/command_center.py` | 15 | Import `load_targets` |
| `views/executive/command_center.py` | 121 | Independent `load_targets()` call |
| `views/executive/command_center.py` | 125 | Filter targets by Month Name |
| `views/commercial/discount.py` | 19 | Import `load_discount_thresholds` |
| `views/commercial/discount.py` | 915 | Independent `load_discount_thresholds()` call |
