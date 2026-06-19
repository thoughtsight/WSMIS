# Month Forensic Audit Report
## Feb-2025 and Mar-2025 Data Disappearance Investigation

---

## Executive Summary

**Status:** ✅ ROOT CAUSE IDENTIFIED

**Finding:** Feb-2025 and Mar-2025 data exists in the Google Sheet but is removed by the advisor filtering logic in `clean_dataframe()`.

**Gemini's Conclusion:** INCORRECT - Gemini concluded the months do not exist in the dataset. This is false. The months exist but are filtered out.

---

## Investigation Methodology

Traced the complete data pipeline:
1. Google Sheet → `load_raw_worksheet()`
2. `load_raw_worksheet()` → `clean_dataframe()`
3. `clean_dataframe()` → `load_data()`
4. `load_data()` → `app.py`
5. `app.py` → Labour page

At each stage, audited:
- Total rows
- Earliest month
- Latest month
- Distinct Month Name values
- Row counts for Feb-2025, Mar-2025, Apr-2025

---

## Root Cause

**File:** `utils/cleaning.py`
**Function:** `clean_dataframe()`
**Lines:** 33-34

**Code:**
```python
# Clean advisor names
if adv_col in df.columns:
    mask = df[adv_col].notna() & ~df[adv_col].astype(str).str.strip().isin(['', '@', 'nan', 'N/A'])
    df = df[mask]
```

**Problem:**
The advisor filter removes rows where the advisor value is empty, "@", "nan", or "N/A". Feb-2025 and Mar-2025 have ALL rows with advisor values of "@" or "N/A", so these months are completely removed.

---

## Evidence

### Stage 1: Google Sheet (Raw Data)

**Total rows:** 7,863

**Month Name values in raw data:**
- Apr-25: 412 rows
- Apr-26: 549 rows
- Aug-25: 508 rows
- Dec-25: 523 rows
- **Feb-25: 433 rows** ✅ EXISTS
- Feb-26: 535 rows
- Jan-25: 441 rows
- Jan-26: 602 rows
- Jul-25: 424 rows
- Jun-25: 483 rows
- **Mar-25: 470 rows** ✅ EXISTS
- Mar-26: 548 rows
- May-25: 428 rows
- Nov-25: 537 rows
- Oct-25: 565 rows
- Sep-25: 405 rows

**Feb-25 advisor values:**
- "@": 431 rows
- "N/A": 2 rows

**Mar-25 advisor values:**
- "@": 470 rows

### Stage 2: After Month Name Transformation

**Transformation:** `clean_dataframe()` line 58
```python
df['Month Name'] = df['Month Name'].apply(lambda x: __import__('datetime').datetime.strptime(x, "%b-%y").strftime("%b-%Y") if isinstance(x, str) and '-' in x else x)
```

**Result:**
- Feb-25 → Feb-2025 (433 rows) ✅
- Mar-25 → Mar-2025 (470 rows) ✅

**Status:** Transformation works correctly. No data loss.

### Stage 3: After Categorical Creation

**Categorical creation:** `clean_dataframe()` lines 60-61
```python
sorted_months = sorted(month_sort_order.keys(), key=lambda k: month_sort_order[k])
df['Month Name'] = pd.Categorical(df['Month Name'], categories=sorted_months, ordered=True)
```

**Result:**
- Feb-2025 in categories: True ✅
- Mar-2025 in categories: True ✅
- NaN values after categorical: 0 ✅

**Status:** Categorical creation works correctly. No data loss.

### Stage 4: After Advisor Filter

**Advisor filter:** `clean_dataframe()` lines 33-34
```python
mask = df[adv_col].notna() & ~df[adv_col].astype(str).str.strip().isin(['', '@', 'nan', 'N/A'])
df = df[mask]
```

**Result:**
- Rows before advisor filter: 7,863
- Rows after advisor filter: 6,398
- Rows removed: 1,465

**Feb-2025 after advisor filter:** 0 rows ❌
**Mar-2025 after advisor filter:** 0 rows ❌

**Status:** Advisor filter removes ALL rows from Feb-2025 and Mar-2025.

### Stage 5: After Service Type Exclusions

**Exclusions:** `load_data()` line 126
```python
df = df[~df['Service Type'].isin(EXCLUDE_SERVICE_TYPES)]
```

**Result:**
- After exclusions: 6,314 rows
- Feb-2025: 0 rows ❌
- Mar-2025: 0 rows ❌

**Status:** No additional impact (already 0 rows).

---

## Month-Related Columns in Pipeline

### Column: "Month Name"
- **Created in:** Google Sheet (source data)
- **Format in raw data:** "Feb-25", "Mar-25", etc.
- **Transformed by:** `clean_dataframe()` line 58
- **Transformation:** "Feb-25" → "Feb-2025" (datetime parsing)
- **Used for reporting:** Yes - this is the primary reporting month column
- **Used for YoY/MoM:** Yes - used in `build_pairs()` and `apply_month_filter()`

### Column: "Month Number"
- **Created in:** Google Sheet (source data)
- **Used for reporting:** No
- **Used for YoY/MoM:** No

### Column: "Month_Sort"
- **Created in:** `clean_dataframe()` line 62
- **Purpose:** Sorting helper for Month Name
- **Used for reporting:** No
- **Used for YoY/MoM:** No

### Column: "Date"
- **Created in:** Google Sheet (source data)
- **Format:** "01-Apr-25"
- **Used for reporting:** No
- **Used for YoY/MoM:** No

### Column: "year"
- **Created in:** Google Sheet (source data)
- **Used for reporting:** No
- **Used for YoY/MoM:** No

---

## Which Column Determines Reporting Month?

**Primary column:** `Month Name`

**Usage in pipeline:**
1. `render_month_picker()` (app.py line 189): Extracts unique months from `Month Name`
2. `build_pairs()` (app.py line 175): Uses `Month Name` with `MONTH_SORT_ORDER` for YoY/MoM pairing
3. `apply_month_filter()` (utils/filters.py): Filters data based on `Month Name`
4. All charts and tables: Use `Month Name` for grouping and display

**Transformation flow:**
```
Google Sheet: "Feb-25"
    ↓
clean_dataframe() line 58: "Feb-2025"
    ↓
clean_dataframe() line 60-61: Categorical with MONTH_SORT_ORDER
    ↓
Used throughout app for reporting
```

---

## Functions That Filter Months

### 1. `clean_dataframe()` - Advisor Filter
**File:** `utils/cleaning.py`
**Lines:** 33-34
**Impact:** Removes rows with invalid advisor values
**Effect on Feb/Mar 2025:** REMOVES ALL ROWS (root cause)

### 2. `load_data()` - Service Type Exclusions
**File:** `app.py`
**Line:** 126
**Impact:** Removes "Credit Note" and "Top Up" service types
**Effect on Feb/Mar 2025:** None (already 0 rows)

### 3. `apply_month_filter()` - Period Selection
**File:** `utils/filters.py`
**Impact:** Filters to selected months
**Effect on Feb/Mar 2025:** None (already 0 rows)

### 4. `build_pairs()` - YoY/MoM Pairing
**File:** `app.py`
**Lines:** 175-185
**Impact:** Creates month pairs for comparison
**Effect on Feb/Mar 2025:** None (already 0 rows)

---

## Exact Function, Line Number, and Reason

**Function:** `clean_dataframe()`
**File:** `utils/cleaning.py`
**Line:** 33-34

**Exact code:**
```python
mask = df[adv_col].notna() & ~df[adv_col].astype(str).str.strip().isin(['', '@', 'nan', 'N/A'])
df = df[mask]
```

**Reason:**
The advisor filter removes rows where the advisor column contains placeholder values ("@", "N/A"). Feb-2025 and Mar-2025 have ALL rows with these placeholder values, so they are completely removed from the dataset.

**Data evidence:**
- Feb-25: 431 rows with "@", 2 rows with "N/A" → 0 rows after filter
- Mar-25: 470 rows with "@" → 0 rows after filter

---

## Recommended Fix

### Option 1: Modify Advisor Filter (Recommended)
**File:** `utils/cleaning.py`
**Lines:** 33-34

**Current code:**
```python
mask = df[adv_col].notna() & ~df[adv_col].astype(str).str.strip().isin(['', '@', 'nan', 'N/A'])
df = df[mask]
```

**Proposed change:**
```python
mask = df[adv_col].notna() & ~df[adv_col].astype(str).str.strip().isin(['', 'nan', 'N/A'])
df = df[mask]
```

**Rationale:** Remove "@" from the exclusion list. "@" appears to be a valid placeholder in the source data for months where advisor assignment is pending. Removing "@" from the exclusion list will preserve Feb-2025 and Mar-2025 data.

### Option 2: Conditional Advisor Filter
**File:** `utils/cleaning.py`
**Lines:** 33-34

**Proposed change:**
```python
if adv_col in df.columns:
    # Only filter if there are valid advisor values in the dataset
    valid_advisors = df[adv_col].notna() & ~df[adv_col].astype(str).str.strip().isin(['', '@', 'nan', 'N/A'])
    if valid_advisors.sum() > 0:
        df = df[valid_advisors]
```

**Rationale:** Only apply advisor filter if there are valid advisor values present. This preserves months with only placeholder advisors.

### Option 3: Data Source Fix (Long-term)
**Action:** Update Google Sheet to have valid advisor names for Feb-2025 and Mar-2025

**Rationale:** The root cause is data quality. Fixing the source data is the most robust solution.

---

## Verification of Gemini's Conclusion

**Gemini's conclusion:** "Feb-2025 and Mar-2025 do not exist in the dataset"

**Assessment:** INCORRECT

**Evidence:**
- Google Sheet contains 433 rows for Feb-25 and 470 rows for Mar-25
- Transformation to Feb-2025 and Mar-2025 works correctly
- Categorical creation works correctly
- Data is removed by advisor filter, not by absence

**Correct conclusion:** Feb-2025 and Mar-2025 exist in the Google Sheet but are removed by the advisor filtering logic in `clean_dataframe()`.

---

## Pipeline Summary

| Stage | Total Rows | Feb-2025 | Mar-2025 | Apr-2025 |
|-------|-----------|----------|----------|----------|
| Google Sheet (Raw) | 7,863 | 433 ✅ | 470 ✅ | 412 ✅ |
| After Month Transformation | 7,863 | 433 ✅ | 470 ✅ | 412 ✅ |
| After Categorical | 7,863 | 433 ✅ | 470 ✅ | 412 ✅ |
| After Advisor Filter | 6,398 | 0 ❌ | 0 ❌ | 412 ✅ |
| After Service Exclusions | 6,314 | 0 ❌ | 0 ❌ | 412 ✅ |
| Final | 6,314 | 0 ❌ | 0 ❌ | 412 ✅ |

---

## Conclusion

**Root cause identified:** Advisor filter in `clean_dataframe()` removes all rows from Feb-2025 and Mar-2025 because these months have placeholder advisor values ("@" and "N/A").

**Gemini's assessment:** INCORRECT - The months exist in the source data but are filtered out.

**Recommended action:** Modify advisor filter to allow "@" as a valid placeholder value, or apply advisor filter conditionally based on data quality.

---

## Audit Timestamp

**Date:** 2026-06-19  
**Time:** 14:15 UTC+05:30  
**Auditor:** Cascade AI Assistant  
**Audit scripts:** forensic_audit.py, forensic_audit_v2.py, forensic_audit_v3.py, forensic_audit_v4.py
