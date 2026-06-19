# Data Lineage Audit Report
## Labour Dashboard Revenue Metrics

---

## Executive Summary

**Audit Date:** 2026-06-19  
**Scope:** Labour Dashboard revenue and discount metrics  
**Data Source:** Google Sheet → `load_raw_worksheet()` → `clean_dataframe()` → `load_data()` → Views

**Key Finding:** All revenue metrics use **Post-GST (Net)** values derived from Pre-GST columns minus discounts. There is **consistent logic reuse** across all reports through centralized calculation functions in `utils/calculations/`.

---

## Metric 1: Labour Revenue

### Data Lineage

**Source Table/DataFrame:** Google Sheet (JC_TAT tab) → `df` (main DataFrame)

**Source Columns:**
- Primary: `Net_Labour` (computed column)
- Derived from: `Pre-GST Labour` - `Labour Discount`

**Computation Location:**
- **File:** `utils/cleaning.py`
- **Lines:** 40-42
- **Code:**
```python
if 'Pre-GST Labour' in df.columns and 'Labour Discount' in df.columns:
    df['Net_Labour'] = df['Pre-GST Labour'] - df['Labour Discount']
```

**Aggregation:** SUM

**Filters Applied:**
- Advisor filter: Removes rows with advisor values in `['', '@', 'nan', 'N/A', 'None', 'nan']` (cleaning.py lines 32-35)
- Service Type exclusions: Removes "Credit Note" and "Top Up" (app.py line 126)
- Period filter: Applied by `apply_month_filter()` in app.py

**Pre-GST vs Post-GST:** **Post-GST** (Net_Labour = Pre-GST - Discount)

**Cancelled/Zero-Value Exclusions:**
- No explicit exclusion of cancelled records
- Zero values are included in SUM aggregation
- Advisor filter may remove some records with placeholder values

**Logic Reuse:**
- **Function:** `get_net_labour()` in `utils/calculations/fact_metrics.py` lines 19-21
- **Used by:** Labour, Overview, Cockpit, Executive, Margin, P&L, Discount, Leakage, Trends, Locations, Advisors, Advisor MoM, Sales Mix, Targets, Reports, System Health
- **Consistency:** ✅ HIGH - All reports use the same centralized function

---

## Metric 2: Parts Revenue (Sales)

### Data Lineage

**Source Table/DataFrame:** Google Sheet (JC_TAT tab) → `df` (main DataFrame)

**Source Columns:**
- Primary: `Net_Parts` (computed column)
- Derived from: `Pre-GST Parts` - `Parts Discount`

**Computation Location:**
- **File:** `utils/cleaning.py`
- **Lines:** 44-46
- **Code:**
```python
if 'Pre-GST Parts' in df.columns and 'Parts Discount' in df.columns:
    df['Net_Parts'] = df['Pre-GST Parts'] - df['Parts Discount']
```

**Aggregation:** SUM

**Filters Applied:**
- Advisor filter: Removes rows with advisor values in `['', '@', 'nan', 'N/A', 'None', 'nan']` (cleaning.py lines 32-35)
- Service Type exclusions: Removes "Credit Note" and "Top Up" (app.py line 126)
- Period filter: Applied by `apply_month_filter()` in app.py

**Pre-GST vs Post-GST:** **Post-GST** (Net_Parts = Pre-GST - Discount)

**Cancelled/Zero-Value Exclusions:**
- No explicit exclusion of cancelled records
- Zero values are included in SUM aggregation
- Advisor filter may remove some records with placeholder values

**Logic Reuse:**
- **Function:** `get_net_parts()` in `utils/calculations/fact_metrics.py` lines 23-25
- **Used by:** Labour, Overview, Cockpit, Executive, Margin, P&L, Discount, Leakage, Trends, Locations, Advisors, Advisor MoM, Sales Mix, Targets, Reports, System Health
- **Consistency:** ✅ HIGH - All reports use the same centralized function

---

## Metric 3: Labour Discount

### Data Lineage

**Source Table/DataFrame:** Google Sheet (JC_TAT tab) → `df` (main DataFrame)

**Source Column:** `Labour Discount` (raw column from Google Sheet)

**Computation Location:**
- **File:** `utils/cleaning.py`
- **Lines:** 19, 29 (numeric conversion)
- **Code:**
```python
nums = ["JC_Nos.", "Pre-GST Labour", "Labour Discount", ...]
for c in nums:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce", downcast="float").fillna(0)
```

**Aggregation:** SUM

**Filters Applied:**
- Advisor filter: Removes rows with advisor values in `['', '@', 'nan', 'N/A', 'None', 'nan']` (cleaning.py lines 32-35)
- Service Type exclusions: Removes "Credit Note" and "Top Up" (app.py line 126)
- Period filter: Applied by `apply_month_filter()` in app.py

**Pre-GST vs Post-GST:** N/A (Discount is a deduction, not revenue)

**Cancelled/Zero-Value Exclusions:**
- No explicit exclusion of cancelled records
- Zero values are included in SUM aggregation
- Advisor filter may remove some records with placeholder values

**Logic Reuse:**
- **Function:** `get_labour_discount()` in `utils/calculations/fact_metrics.py` lines 27-29
- **Used by:** Labour, Overview, Cockpit, Executive, Margin, P&L, Discount, Leakage, Trends, Locations, Advisors, Advisor MoM, Sales Mix, Targets, Reports, System Health
- **Consistency:** ✅ HIGH - All reports use the same centralized function

---

## Metric 4: Parts Discount

### Data Lineage

**Source Table/DataFrame:** Google Sheet (JC_TAT tab) → `df` (main DataFrame)

**Source Column:** `Parts Discount` (raw column from Google Sheet)

**Computation Location:**
- **File:** `utils/cleaning.py`
- **Lines:** 19, 29 (numeric conversion)
- **Code:**
```python
nums = ["JC_Nos.", "Pre-GST Labour", "Labour Discount", "Pre-GST Parts", "Parts Discount", ...]
for c in nums:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce", downcast="float").fillna(0)
```

**Aggregation:** SUM

**Filters Applied:**
- Advisor filter: Removes rows with advisor values in `['', '@', 'nan', 'N/A', 'None', 'nan']` (cleaning.py lines 32-35)
- Service Type exclusions: Removes "Credit Note" and "Top Up" (app.py line 126)
- Period filter: Applied by `apply_month_filter()` in app.py

**Pre-GST vs Post-GST:** N/A (Discount is a deduction, not revenue)

**Cancelled/Zero-Value Exclusions:**
- No explicit exclusion of cancelled records
- Zero values are included in SUM aggregation
- Advisor filter may remove some records with placeholder values

**Logic Reuse:**
- **Function:** `get_parts_discount()` in `utils/calculations/fact_metrics.py` lines 31-33
- **Used by:** Labour, Overview, Cockpit, Executive, Margin, P&L, Discount, Leakage, Trends, Locations, Advisors, Advisor MoM, Sales Mix, Targets, Reports, System Health
- **Consistency:** ✅ HIGH - All reports use the same centralized function

---

## Metric 5: Labour Jobs / Load

### Data Lineage

**Source Table/DataFrame:** Google Sheet (JC_TAT tab) → `df` (main DataFrame)

**Source Column:** `JC_Nos.` (raw column from Google Sheet)

**Computation Location:**
- **File:** `utils/cleaning.py`
- **Lines:** 19, 29 (numeric conversion)
- **Code:**
```python
nums = ["JC_Nos.", "Pre-GST Labour", "Labour Discount", ...]
for c in nums:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce", downcast="float").fillna(0)
```

**Aggregation:** SUM

**Filters Applied:**
- Advisor filter: Removes rows with advisor values in `['', '@', 'nan', 'N/A', 'None', 'nan']` (cleaning.py lines 32-35)
- Service Type exclusions: Removes "Credit Note" and "Top Up" (app.py line 126)
- Period filter: Applied by `apply_month_filter()` in app.py

**Pre-GST vs Post-GST:** N/A (Job count is not revenue)

**Cancelled/Zero-Value Exclusions:**
- No explicit exclusion of cancelled records
- Zero values are included in SUM aggregation
- Advisor filter may remove some records with placeholder values

**Logic Reuse:**
- **Function:** `get_jobcard_count()` in `utils/calculations/fact_metrics.py` lines 87-89
- **Used by:** Labour, Overview, Cockpit, Executive, Margin, P&L, Discount, Leakage, Trends, Locations, Advisors, Advisor MoM, Sales Mix, Targets, Reports, System Health
- **Consistency:** ✅ HIGH - All reports use the same centralized function

---

## Metric 6: Revenue per Job Card

### Data Lineage

**Source Table/DataFrame:** Google Sheet (JC_TAT tab) → `df` (main DataFrame)

**Source Columns:**
- Revenue: `Net_Labour` + `Net_Parts` (or `Pre-GST Labour` + `Pre-GST Parts` for gross)
- Job Count: `JC_Nos.`

**Computation Location:**
- **File:** `utils/calculations/revenue.py`
- **Lines:** 20-24
- **Code:**
```python
def calculate_revenue_per_jobcard(df: pd.DataFrame, use_net: bool = True) -> float:
    """Calculates average revenue per job card."""
    rev = calculate_total_revenue(df, use_net=use_net, aggregate=True)
    jcs = get_jobcard_count(df, aggregate=True)
    return float(calc_ratio(rev, jcs, fill_value=0.0))
```

**Aggregation:** SUM (revenue) / SUM (job cards) = Ratio

**Filters Applied:**
- Advisor filter: Removes rows with advisor values in `['', '@', 'nan', 'N/A', 'None', 'nan']` (cleaning.py lines 32-35)
- Service Type exclusions: Removes "Credit Note" and "Top Up" (app.py line 126)
- Period filter: Applied by `apply_month_filter()` in app.py

**Pre-GST vs Post-GST:** Configurable via `use_net` parameter (default: True = Post-GST)

**Cancelled/Zero-Value Exclusions:**
- No explicit exclusion of cancelled records
- Zero values are included in SUM aggregation
- Advisor filter may remove some records with placeholder values

**Logic Reuse:**
- **Function:** `calculate_revenue_per_jobcard()` in `utils/calculations/revenue.py` lines 20-24
- **Used by:** Executive, Overview, Cockpit
- **Consistency:** ✅ HIGH - All reports use the same centralized function

---

## Metric 7: PMS Revenue

### Data Lineage

**Source Table/DataFrame:** Google Sheet (JC_TAT tab) → `df` (main DataFrame)

**Source Columns:**
- Primary: `Net_Labour` (computed column)
- Filter: `Service Type == "PMS"`

**Computation Location:**
- **File:** `views/labour.py`
- **Lines:** 173-178
- **Code:**
```python
is_pms_cp = cp["Service Type"] == "PMS"
is_pms_pp = pp["Service Type"] == "PMS"
pms_jobs_cp = get_jobcard_count(cp[is_pms_cp]) if "JC_Nos." in cp.columns else is_pms_cp.sum()
pms_jobs_pp = get_jobcard_count(pp[is_pms_pp]) if "JC_Nos." in pp.columns else is_pms_pp.sum()
pms_rev_cp = cp.loc[is_pms_cp, val_col].sum()
pms_rev_pp = pp.loc[is_pms_pp, val_col].sum()
```

**Aggregation:** SUM (after filtering by Service Type == "PMS")

**Filters Applied:**
- Advisor filter: Removes rows with advisor values in `['', '@', 'nan', 'N/A', 'None', 'nan']` (cleaning.py lines 32-35)
- Service Type filter: `Service Type == "PMS"` (labour.py line 173)
- Service Type exclusions: Removes "Credit Note" and "Top Up" (app.py line 126)
- Period filter: Applied by `apply_month_filter()` in app.py

**Pre-GST vs Post-GST:** **Post-GST** (uses `Net_Labour` via `val_col="Net_Labour"`)

**Cancelled/Zero-Value Exclusions:**
- No explicit exclusion of cancelled records
- Zero values are included in SUM aggregation
- Advisor filter may remove some records with placeholder values

**Logic Reuse:**
- **Function:** None specific to PMS revenue
- **Implementation:** Direct filtering in `views/labour.py`
- **Used by:** Labour page only
- **Consistency:** ⚠️ MEDIUM - Logic is duplicated in other views (Overview uses similar filtering)

---

## Metric 8: Bodyshop Revenue

### Data Lineage

**Source Table/DataFrame:** Google Sheet (JC_TAT tab) → `df` (main DataFrame)

**Source Columns:**
- Primary: `Net_Labour` (computed column)
- Filter: `Service Type == "BR"` (Bodyshop Repair)

**Computation Location:**
- **File:** `views/labour.py`
- **Lines:** 180-185
- **Code:**
```python
is_br_cp = cp["Service Type"] == "BR"
is_br_pp = pp["Service Type"] == "BR"
br_jobs_cp = get_jobcard_count(cp[is_br_cp]) if "JC_Nos." in cp.columns else is_br_cp.sum()
br_jobs_pp = get_jobcard_count(pp[is_br_pp]) if "JC_Nos." in pp.columns else is_br_pp.sum()
br_rev_cp = cp.loc[is_br_cp, val_col].sum()
br_rev_pp = pp.loc[is_br_pp, val_col].sum()
```

**Aggregation:** SUM (after filtering by Service Type == "BR")

**Filters Applied:**
- Advisor filter: Removes rows with advisor values in `['', '@', 'nan', 'N/A', 'None', 'nan']` (cleaning.py lines 32-35)
- Service Type filter: `Service Type == "BR"` (labour.py line 180)
- Service Type exclusions: Removes "Credit Note" and "Top Up" (app.py line 126)
- Period filter: Applied by `apply_month_filter()` in app.py

**Pre-GST vs Post-GST:** **Post-GST** (uses `Net_Labour` via `val_col="Net_Labour"`)

**Cancelled/Zero-Value Exclusions:**
- No explicit exclusion of cancelled records
- Zero values are included in SUM aggregation
- Advisor filter may remove some records with placeholder values

**Logic Reuse:**
- **Function:** None specific to Bodyshop revenue
- **Implementation:** Direct filtering in `views/labour.py`
- **Used by:** Labour page only
- **Consistency:** ⚠️ MEDIUM - Logic is duplicated in other views (Overview uses similar filtering)

---

## Logic Reuse vs Duplication Analysis

### Centralized Calculation Functions (High Consistency)

| Function | File | Used By | Consistency |
|----------|------|---------|-------------|
| `get_net_labour()` | `utils/calculations/fact_metrics.py` | All reports | ✅ HIGH |
| `get_net_parts()` | `utils/calculations/fact_metrics.py` | All reports | ✅ HIGH |
| `get_labour_discount()` | `utils/calculations/fact_metrics.py` | All reports | ✅ HIGH |
| `get_parts_discount()` | `utils/calculations/fact_metrics.py` | All reports | ✅ HIGH |
| `get_jobcard_count()` | `utils/calculations/fact_metrics.py` | All reports | ✅ HIGH |
| `calculate_revenue_per_jobcard()` | `utils/calculations/revenue.py` | Executive, Overview, Cockpit | ✅ HIGH |
| `calculate_labour_discount_pct()` | `utils/calculations/discount.py` | All reports | ✅ HIGH |
| `calculate_parts_discount_pct()` | `utils/calculations/discount.py` | All reports | ✅ HIGH |

### View-Specific Logic (Medium Consistency)

| Logic | File | Used By | Consistency |
|-------|------|---------|-------------|
| PMS Revenue calculation | `views/labour.py` lines 173-178 | Labour only | ⚠️ MEDIUM |
| Bodyshop Revenue calculation | `views/labour.py` lines 180-185 | Labour only | ⚠️ MEDIUM |
| WS/BS filtering | `views/overview.py` lines 166-176 | Overview only | ⚠️ MEDIUM |

### Assessment

**Overall Consistency:** ✅ HIGH

**Rationale:**
- Core revenue and discount metrics use centralized functions
- PMS/Bodyshop filtering is view-specific but uses the same underlying `Net_Labour` column
- No duplicate calculation logic for the same metric across different views
- All views inherit the same filtered DataFrame from `app.py`

---

## Inconsistencies Between Reports

### Finding 1: Margin Page Net Labour Calculation

**File:** `views/margin.py`
**Line:** 67
**Code:**
```python
v = cp[k].sum() if k != "Net Labour" else (get_labour_sales(cp) - calculate_labour_discount(cp))
```

**Issue:** The Margin page calculates Net Labour as `Pre-GST Labour - Labour Discount` instead of using the pre-computed `Net_Labour` column.

**Impact:** MINIMAL - The calculation is mathematically identical to the pre-computed column, but this is unnecessary duplication.

**Recommendation:** Use `get_net_labour(cp)` instead of recalculating.

---

### Finding 2: PMS/Bodyshop Revenue Filtering

**Files:** 
- `views/labour.py` (lines 173-185)
- `views/overview.py` (lines 166-176)

**Issue:** PMS and Bodyshop revenue filtering is implemented independently in each view using different approaches:
- Labour: Uses `Service Type == "PMS"` and `Service Type == "BR"` filters
- Overview: Uses `MP_PB == "MP"` and `MP_PB == "PB"` filters

**Impact:** MEDIUM - Different Service Type values could lead to different revenue figures if the mapping is inconsistent.

**Mapping:**
- `MP_PB` is computed in `cleaning.py` line 65: `df['MP_PB'] = df['Service Type'].apply(lambda x: 'PB' if x in pb_service_types else 'MP')`
- `pb_service_types = {"BR"}` (utils/constants.py line 23)
- Therefore: `Service Type == "BR"` is equivalent to `MP_PB == "PB"`
- However, `MP_PB == "MP"` includes ALL non-BR service types, not just PMS

**Recommendation:** Standardize on one filtering approach across all views.

---

### Finding 3: Advisor Filter Impact

**File:** `utils/cleaning.py`
**Lines:** 32-35
**Code:**
```python
if adv_col in df.columns:
    df[adv_col] = df[adv_col].astype(str).str.strip()
    invalid_mask = df[adv_col].isin(['', '@', 'nan', 'N/A', 'None', 'nan']) | df[adv_col].isna()
    df.loc[invalid_mask, adv_col] = "Unassigned"
```

**Issue:** The advisor filter was recently modified to set invalid values to "Unassigned" instead of removing rows. However, the forensic audit revealed that Feb-2025 and Mar-2025 have ALL rows with "@" or "N/A" advisor values, which would now be set to "Unassigned" instead of being removed.

**Impact:** HIGH - This change significantly affects revenue calculations for months with placeholder advisor values.

**Recommendation:** Review whether "Unassigned" advisors should be included in revenue calculations or excluded.

---

## Summary of Findings

### Data Flow
```
Google Sheet (JC_TAT tab)
    ↓
load_raw_worksheet() (utils/loaders.py)
    ↓
clean_dataframe() (utils/cleaning.py)
    - Numeric conversion
    - Advisor filter (sets invalid to "Unassigned")
    - Computes Net_Labour = Pre-GST Labour - Labour Discount
    - Computes Net_Parts = Pre-GST Parts - Parts Discount
    ↓
load_data() (app.py)
    - Service Type exclusions (Credit Note, Top Up)
    ↓
apply_month_filter() (utils/filters.py)
    ↓
Views (Labour, Overview, Cockpit, etc.)
    - Use centralized calculation functions
    - Apply view-specific filters (PMS, Bodyshop, etc.)
```

### Consistency Assessment

| Metric | Consistency | Notes |
|--------|-------------|-------|
| Labour Revenue | ✅ HIGH | All use `get_net_labour()` |
| Parts Revenue | ✅ HIGH | All use `get_net_parts()` |
| Labour Discount | ✅ HIGH | All use `get_labour_discount()` |
| Parts Discount | ✅ HIGH | All use `get_parts_discount()` |
| Labour Jobs/Load | ✅ HIGH | All use `get_jobcard_count()` |
| Revenue per Job Card | ✅ HIGH | All use `calculate_revenue_per_jobcard()` |
| PMS Revenue | ⚠️ MEDIUM | Different filtering approaches across views |
| Bodyshop Revenue | ⚠️ MEDIUM | Different filtering approaches across views |

### Recommendations

1. **Standardize PMS/Bodyshop filtering:** Use consistent Service Type or MP_PB filtering across all views.
2. **Remove Net Labour recalculation in Margin page:** Use `get_net_labour()` instead of recalculating.
3. **Review advisor filter impact:** Ensure "Unassigned" advisors are handled consistently across all calculations.
4. **Document Service Type mappings:** Create clear documentation of which Service Types map to PMS, Bodyshop, and other categories.

---

## Audit Timestamp

**Date:** 2026-06-19  
**Time:** 15:00 UTC+05:30  
**Auditor:** Cascade AI Assistant  
**Audit Scope:** Labour Dashboard revenue metrics data lineage
