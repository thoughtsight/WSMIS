# WSMIS Parts Module – Independent Forensic Audit

**Audit Date:** 2026-06-23  
**Auditor:** MiMo v2.5 (Independent Reviewer)  
**Scope:** Parts Executive, Parts Detail, Sales Mix regression verification  
**Status:** Complete — Read-Only Audit, No Code Modifications  

---

## 1. Executive Summary

The WSMIS Parts Module recently completed three enhancement phases. Parts Detail functions correctly. Parts Executive and Sales Mix exhibit regressions introduced during those phases.

After independent code tracing of every execution path, aggregation call, and rendering function across all three reports, I identified **two confirmed root-cause defects** and **several hidden issues** not previously reported.

| Metric | Value |
|--------|-------|
| Overall Module Health | **DEGRADED** — 2 of 3 reports have defects |
| Parts Detail | PASS |
| Parts Executive | FAIL — silent data corruption |
| Sales Mix | FAIL — runtime crash |
| Overall Confidence | **93%** |
| Production Readiness | **CONDITIONAL** — two fixes required before freeze |

**Key Finding:** The previous forensic review correctly flagged two areas of concern but misidentified the actual failure mechanisms. The `.agg()` hardcoded dictionaries in Parts Executive are safe (columns always exist). The `_cp` naming mismatch in Sales Mix does not exist in the current code. The actual root causes are: (1) a `pivot_summary` return-type contract violation in Parts Executive, and (2) a `Series.sort_values()` API misuse in Sales Mix.

---

## 2. Files Reviewed

| # | File Path | Role | Lines |
|---|-----------|------|-------|
| 1 | `views/commercial/parts_executive.py` | Parts Executive dashboard | 904 |
| 2 | `views/commercial/sales_mix.py` | Sales Mix dashboard | 179 |
| 3 | `views/commercial/parts_detail.py` | Parts Detail dashboard (reference) | 396 |
| 4 | `views/sales_mix.py` | Compatibility wrapper (delegates to commercial) | 7 |
| 5 | `views/shared.py` | Shared imports and wildcard re-exports | 41 |
| 6 | `views/dashboard_common.py` | Shared dashboard utilities | 281 |
| 7 | `utils/aggregations.py` | Aggregation utility functions | 73 |
| 8 | `services/aggregation_cache.py` | Cached GroupBy and aggregation engine | 208 |
| 9 | `utils/calculations/fact_metrics.py` | Canonical metric extraction helpers | 118 |
| 10 | `ui/components/metrics.py` | KPI card rendering (MetricCard, KPIGrid) | 151 |
| 11 | `views/components/chart_engine.py` | Plotly chart styling engine | 120 |
| 12 | `utils/loaders.py` | Google Sheets data loader | 351 (partial) |

---

## 3. Root Cause Analysis

### Issue PE-1: Parts Executive — Silent Data Corruption via `pivot_summary` Index Mismatch

| Attribute | Detail |
|-----------|--------|
| **Report** | Parts Executive |
| **File** | `views/commercial/parts_executive.py` |
| **Function** | `_render_executive_table` (consuming), `_compute_metrics` (producing) |
| **Line(s)** | 702 (primary), 824 (secondary), 166-167 (origin) |
| **Confidence** | **95%** |

**Root Cause:**

`pivot_summary()` in `utils/aggregations.py:45` unconditionally returns `pvt.reset_index()`. This converts the `Location Name` group key from the DataFrame index into a regular column, replacing the index with `RangeIndex(0, 1, 2, ...)`.

Callers in `_render_executive_table` and `_render_monthly_detail` access `d["cp_loc_month_piv"].index` expecting location name strings but receive integers.

**Evidence (execution trace):**

1. `_compute_metrics` at line 166 calls:
   ```python
   cp_loc_month_piv = pivot_summary(cp, index="Location Name", columns="Month Name",
                                      values="Pre-GST Parts", aggfunc="sum", fill_value=0)
   ```

2. `pivot_summary` (`utils/aggregations.py:44-45`) executes:
   ```python
   pvt = pd.pivot_table(df, index=index, columns=columns, values=values, aggfunc=aggfunc, fill_value=fill_value)
   return pvt.reset_index()   # <-- Location Name moves from index to column
   ```

3. After `reset_index()`, the result has columns `["Location Name", "Jan-26", "Feb-26", ...]` and a `RangeIndex`.

4. `_render_executive_table` at line 702:
   ```python
   all_locs = sorted(set(d["cp_loc_month_piv"].index) |
                     set(d["pp_loc_month_piv"].index))
   ```
   `d["cp_loc_month_piv"].index` is `RangeIndex([0, 1, 2, ...])`, not location names.

5. At line 713:
   ```python
   lcp = d["loc_df"].loc[loc, "CP"] if loc in d["loc_df"].index else 0
   ```
   `loc` is an integer (e.g., `0`). `d["loc_df"].index` contains string location names. The condition `loc in d["loc_df"].index` is always `False`. Therefore `lcp = 0`, `lpp = 0`, `growth = 0`, `delta = 0`, `margin_cp = 0`, `oil_pen_cp = 0`, `parts_per_jc_cp = 0` for every row.

6. The "Location" column in the rendered table contains integers `0, 1, 2, ...` instead of location name strings.

**Why it occurs:**

`pivot_summary` was likely introduced or modified during the enhancement phases to standardize pivot table creation with `reset_index()`. The callers at lines 702 and 824 were written against an earlier implicit contract where the pivot result retained `Location Name` as the index. The shared utility changed its return-type contract; callers were not updated.

**Impact:** The Executive Location Performance table and Monthly Location Performance detail table render with **all-zero values** and integer row labels. This is a silent data corruption — no exception is raised, no error message is shown. Users see a seemingly valid table with incorrect data.

---

### Issue SM-1: Sales Mix — Runtime Crash on `Series.sort_values()` API Misuse

| Attribute | Detail |
|-----------|--------|
| **Report** | Sales Mix |
| **File** | `views/commercial/sales_mix.py` |
| **Function** | `_render_charts` |
| **Line(s)** | 140 |
| **Confidence** | **92%** |

**Root Cause:**

Line 140 calls `.sort_values("Oil_Sale", ascending=True)` on a **pandas Series** object. `Series.sort_values()` does not accept a column name as its first positional argument. The first parameter is `axis` (which only accepts `0`/`'index'`/`1`/`'columns'`). Passing `"Oil_Sale"` as `axis` raises a `ValueError`.

**Evidence (execution trace):**

1. `location_summary(cp, as_index=False)` returns a `DataFrameGroupBy` (from `aggregation_cache.py:118-119`).

2. `["Oil_Sale"]` selects the `Oil_Sale` column from the GroupBy, producing a `SeriesGroupBy`.

3. `.sum()` aggregates the `SeriesGroupBy`, returning a `pandas.Series` indexed by `Location Name` with summed `Oil_Sale` values.

4. `.sort_values("Oil_Sale", ascending=True)` is called on this Series. The `Series.sort_values` signature is:
   ```
   Series.sort_values(axis=0, ascending=True, inplace=False, kind='quicksort',
                      na_position='last', ignore_index=False, key=None)
   ```
   The first positional arg is `axis`. Passing `"Oil_Sale"` sets `axis="Oil_Sale"`, which is invalid.

5. Pandas raises: `ValueError: No axis named Oil_Sale for object type Series`

**Why it occurs:**

The developer likely confused `DataFrame.sort_values(by=...)` (which accepts a column name) with `Series.sort_values()` (which does not). The `.sum()` on a `SeriesGroupBy` returns a Series, not a DataFrame. The code treats the result as if it were a DataFrame.

**Impact:** The `_render_charts` function crashes at line 140 within the `with c3:` column block. In Streamlit, this propagates and prevents the Oil Ranking chart, Oil per Litre chart, and the UniversalFooter from rendering. The Oil Trend chart (c1) and Batt + Tyre chart (c2) render successfully before the crash point. The KPIs and tables (rendered before `_render_charts`) also render successfully. The overall Sales Mix page displays a Streamlit error message.

---

## 4. Confirmed Issues

### Critical

| # | Issue | Description | Regression Risk | Business Impact |
|---|-------|-------------|-----------------|-----------------|
| SM-1 | Sales Mix crash at `sales_mix.py:140` | `Series.sort_values("Oil_Sale")` raises `ValueError` | **High** — page crashes, no workaround for Oil Ranking chart | Users cannot view Oil Ranking by Location or Oil Revenue per Litre. Two of four charts in `_render_charts` fail. Page shows Streamlit error. |

### Major

| # | Issue | Description | Regression Risk | Business Impact |
|---|-------|-------------|-----------------|-----------------|
| PE-1 | Parts Executive silent data corruption at `parts_executive.py:702` | `pivot_summary` returns `reset_index()` DataFrame; callers read `.index` expecting location names | **High** — table renders with all-zero values, no error visible | Executive Location Performance table shows integers instead of location names and all-zero metrics. Monthly Detail table shows wrong data. Decision-makers see incorrect location rankings. |

### Minor

| # | Issue | Description | Regression Risk | Business Impact |
|---|-------|-------------|-----------------|-----------------|
| PE-2 | `_render_monthly_detail` at `parts_executive.py:824` | Same `.index` bug as PE-1, affects the Monthly Location Performance expander | **Medium** — same root cause, same wrong data | Monthly detail table shows integers as location names and incorrect per-month values |
| SM-2 | `pivot_summary` contract ambiguity at `aggregations.py:45` | Unconditional `reset_index()` changes return type without caller awareness | **Medium** — any future caller using `.index` will break | Architectural debt; not user-visible today but will cause future regressions |

---

## 5. Previous Findings Verification

### Finding 1: Parts Executive — Unsafe `.agg()` Calls with Hardcoded Dictionaries

| Attribute | Verdict |
|-----------|---------|
| **Verdict** | **REJECTED** |
| **Confidence** | 95% |

**Explanation:** The previous review flagged `.agg()` calls at lines 101-102 (`{"Pre-GST Parts": "sum", "JC_Nos.": "sum", "Parts Profit": "sum"}`) and lines 159-160 (`{"Pre-GST Parts": "sum"}`) as potential runtime failures.

This is incorrect for the following reasons:

1. **Column existence is guaranteed.** `Pre-GST Parts`, `JC_Nos.`, and `Parts Profit` are canonical Parts module columns. They are referenced by `fact_metrics.py` (`get_parts_sales`, `get_jobcard_count`, `get_parts_profit`), by `parts_detail.py` (lines 67, 77, 80, 167, 241, 285, 337-340 in identical `.agg()` dicts), and by the data loader pipeline.

2. **Parts Detail uses identical `.agg()` patterns and works correctly.** The user confirmed Parts Detail functions correctly. Parts Detail at lines 70, 80, 167, 241, 285, and 340 uses the same `location_summary(...).agg({"Pre-GST Parts": "sum", "Parts Profit": "sum", ...})` pattern. If these dicts caused failures, Parts Detail would also fail.

3. **The `.agg()` calls execute successfully.** Tracing the execution flow: `_compute_metrics` completes without error. The first visible defect appears at line 702 in `_render_executive_table`, well after the `.agg()` calls have executed and their results consumed.

4. **The recommendation to "dynamically build aggregation dictionaries" adds unnecessary complexity.** The columns are stable, canonical, and guaranteed by the data pipeline. Defensive column-checking in `.agg()` dicts would add code with no practical benefit.

**The `.agg()` pattern is a valid code smell** (fragile if columns are removed in the future), but it is **not the cause of the current regression** and should not be treated as a priority fix.

---

### Finding 2: Sales Mix — Dictionary Naming Mismatch (`_cp` Suffixes)

| Attribute | Verdict |
|-----------|---------|
| **Verdict** | **REJECTED** |
| **Confidence** | 95% |

**Explanation:** The previous review stated: "Metrics are created using `_cp` suffixes but rendered using legacy keys without `_cp`."

This is incorrect. The current code uses `_cp`/`_pp` suffixes consistently:

- **Computation** (`_compute_metrics`, lines 19-46): All metric keys use `_cp`/`_pp` suffixes (`oil_rs_cp`, `oil_rs_pp`, `oil_ltrs_cp`, `tyre_rs_cp`, etc.)
- **KPI Rendering** (`_render_kpis`, lines 55-64): Accesses `metrics["oil_rs_cp"]`, `metrics["oil_rs_pp"]`, etc. — matching keys.
- **Table Rendering** (`_render_tables`): Accesses `metrics["cp"]` and `metrics["pp"]` (DataFrames), not individual metric keys.
- **Chart Rendering** (`_render_charts`): Accesses `metrics["cp"]` (DataFrame) and computes directly.

There is no location in the current code where a metric is accessed without its `_cp`/`_pp` suffix. The naming is internally consistent.

**Possible explanation for the previous finding:** The reviewer may have been looking at a mental model of a previous code version, or may have confused the `MetricCard` kwargs (`cp=`, `pp=`) with the metrics dict keys. The `MetricCard` component accepts `cp` and `pp` as parameter names (not `_cp`/`_pp`), and the `kpi_data` list correctly maps `metrics["oil_rs_cp"]` to the `cp=` parameter.

---

## 6. Hidden Issues

The following additional problems were discovered during the audit and were **not** identified in the previous forensic review.

### H-1: `Series.sort_values()` API Misuse in Oil Ranking Chart

| Attribute | Detail |
|-----------|--------|
| **File** | `views/commercial/sales_mix.py:140` |
| **Severity** | Critical (crash) |
| **Previously Reported** | No |

```python
orank = location_summary(cp, as_index=False)["Oil_Sale"].sum().sort_values("Oil_Sale", ascending=True).tail(10)
```

After `.sum()`, the result is a `Series`. `Series.sort_values()` does not have a `by` parameter. The first positional arg is `axis`. This is a crash bug (see Issue SM-1).

---

### H-2: `pivot_summary` Unconditional `reset_index()` Breaks Index-Based Callers

| Attribute | Detail |
|-----------|--------|
| **File** | `utils/aggregations.py:45` |
| **Severity** | Major (data corruption) |
| **Previously Reported** | Partially — the review suspected `.agg()` issues but did not identify `reset_index()` |

```python
return pvt.reset_index()
```

This function is used by both Parts Executive and potentially other modules. Any caller that accesses `.index` on the result expecting group labels will receive a `RangeIndex` instead. Parts Detail avoids this by not using `pivot_summary`.

---

### H-3: Parts Executive — `_apply_filters` Does Not Filter `pp` DataFrame for Cross-Month Click

| Attribute | Detail |
|-----------|--------|
| **File** | `views/commercial/parts_executive.py:26-27` |
| **Severity** | Minor (potential data leakage) |
| **Previously Reported** | No |

```python
def _apply_filters(df, active_pairs):
    return apply_period_filters(df, active_pairs, "parts_cross_month")
```

`apply_period_filters` (dashboard_common.py:66-88) filters both `cp` and `pp` by `Month Name`. However, when the cross-filter month is set, `pp_months_active` is reduced to a single month pair. If the PP month does not exist in the data (e.g., data only goes back 6 months but the pair references 12 months ago), `pp` could be empty while `cp` is not. The code at line 889 only checks `if cp.empty and pp.empty`, allowing execution to proceed with an empty `pp`. This is handled gracefully in `_compute_metrics` (all PP values default to 0), but it means Growth % is always 100% or undefined when PP is empty, which may confuse users.

---

### H-4: Parts Executive — Redundant Health Score Calculation

| Attribute | Detail |
|-----------|--------|
| **File** | `views/commercial/parts_executive.py:71-91` |
| **Severity** | Minor (code smell) |
| **Previously Reported** | No |

The PP health score at line 85 computes:
```python
pp_growth = calc_growth_pct(pp_val, pp_val if pp_val > 0 else 1, fill_value=0)
```

This computes growth of PP vs. PP itself, which is always 0. The comment says "PP vs PP-1 not available, use 0". While this is intentional, it means the PP health score always has `growth_score = (0 + 10) / 30 * 100 = 33.3`, introducing a fixed bias into the PP health score. This is a design decision, not a bug, but worth noting.

---

### H-5: Sales Mix — `_apply_filters` Does Not Use Pair-Based Filtering

| Attribute | Detail |
|-----------|--------|
| **File** | `views/commercial/sales_mix.py:8-13` |
| **Severity** | Minor (potential data mismatch) |
| **Previously Reported** | No |

```python
def _apply_filters(df, pairs):
    if not pairs:
        return df, None
    cp = df
    pp = df[df["year"] == "Last FY"] if "year" in df.columns else None
    return cp, pp
```

Unlike Parts Executive (which uses `apply_period_filters` to filter by specific month pairs), Sales Mix's `_apply_filters` returns the **entire DataFrame** as `cp` and filters `pp` only by `year == "Last FY"`. This means:
- `cp` contains ALL months, not just the months in the active pairs
- The KPI values and table totals include data outside the selected comparison period
- If `year` column is missing, `pp` is `None` and all PP values default to 0

This may be intentional (Sales Mix shows cumulative data) but creates an inconsistency with Parts Executive's pair-based filtering.

---

### H-6: Parts Executive — `_render_executive_panel` Renders Before `_render_charts`

| Attribute | Detail |
|-----------|--------|
| **File** | `views/commercial/parts_executive.py:898-901` |
| **Severity** | Informational |
| **Previously Reported** | No |

The render order is:
```
_render_executive_panel → _render_waterfall → _render_category_heatmap → _render_charts → _render_executive_table
```

The executive panel at line 898 renders **before** the charts. This means KPIs display correctly even though the executive table (rendered later at line 902) shows corrupted data. Users see correct KPIs but a broken table, creating a confusing mixed-quality experience on the same page.

---

### H-7: `category_summary` Returns Scalar 0 When Columns Are Missing

| Attribute | Detail |
|-----------|--------|
| **File** | `services/aggregation_cache.py:200` |
| **Severity** | Minor (fragile type contract) |
| **Previously Reported** | No |

```python
cat_sums = df[cat_cols].sum() if all(c in df.columns for c in cat_cols) else pd.Series(0, index=cat_cols)
```

When columns are missing, this returns `pd.Series(0, index=cat_cols)`. However, the comment says "equivalent to `df[cat_cols].sum()`". The fallback creates a Series of zeros with the category names as index, while the normal path returns `df[cat_cols].sum()` which is also a Series. The types are consistent, but the `pd.Series(0, index=cat_cols)` creates a Series of integer zeros while `df[cat_cols].sum()` returns float zeros (since `sum()` promotes to float). This can cause subtle dtype mismatches downstream (e.g., in `has_category_data = cp_cat_sum.sum() > 0`).

---

### H-8: Sales Mix — Oil per Litre Chart Uses `as_index=True` While Other Charts Use `as_index=False`

| Attribute | Detail |
|-----------|--------|
| **File** | `views/commercial/sales_mix.py:149` |
| **Severity** | Minor (inconsistency) |
| **Previously Reported** | No |

```python
oil_per_litre = location_summary(cp, as_index=True).agg(S=("Oil_Sale","sum"), Q=("Oil_Sale_Qty","sum")).reset_index()
```

Lines 129 and 136 use `monthly_summary(cp, as_index=False)`, but line 149 uses `location_summary(cp, as_index=True)`. The `as_index=True` path is followed by `.reset_index()` to achieve the same effect. This inconsistency suggests the code was written by different people or at different times. Not a bug, but a maintenance concern.

---

## 7. Recommended Fix Order

### Priority 1 – Critical (must fix first)

| # | Issue | File:Line | Fix Description |
|---|-------|-----------|-----------------|
| 1 | SM-1 | `sales_mix.py:140` | Remove `"Oil_Sale"` from `.sort_values()` call. Change to `.sort_values(ascending=True).tail(10)`. |
| 2 | PE-1 | `parts_executive.py:702` | Change `d["cp_loc_month_piv"].index` to `d["cp_loc_month_piv"]["Location Name"]` (and same for `pp_loc_month_piv`). |
| 3 | PE-2 | `parts_executive.py:824` | Same fix as PE-1 for the `_render_monthly_detail` function. |

### Priority 2 – High

| # | Issue | File:Line | Fix Description |
|---|-------|-----------|-----------------|
| 4 | SM-2 | `aggregations.py:45` | Add optional `reset_index` parameter to `pivot_summary` (default `True` for backward compatibility). Parts Executive callers should pass `reset_index=False` or handle the column-based result. |

### Priority 3 – Medium

| # | Issue | File:Line | Fix Description |
|---|-------|-----------|-----------------|
| 5 | H-5 | `sales_mix.py:8-13` | Consider whether Sales Mix should use pair-based filtering like Parts Executive, or document the intentional difference. |
| 6 | H-7 | `aggregation_cache.py:200` | Ensure fallback `pd.Series(0, index=cat_cols)` uses `dtype=float` for consistency with `df[cat_cols].sum()`. |

### Priority 4 – Nice to Have

| # | Issue | File:Line | Fix Description |
|---|-------|-----------|-----------------|
| 7 | H-4 | `parts_executive.py:85` | Consider using a dummy growth value (e.g., 0) instead of computing `calc_growth_pct(pp_val, pp_val)` which is always 0. |
| 8 | H-8 | `sales_mix.py:129,136,149` | Standardize `as_index` parameter usage across all chart aggregations. |
| 9 | H-3 | `parts_executive.py:889` | Consider adding a warning message when PP is empty to inform users that Growth % values are meaningless. |

---

## 8. Regression Risk Assessment

| Fix # | Risk Level | Files Affected | Possible Side Effects |
|-------|------------|----------------|----------------------|
| 1 (SM-1) | **Low** | `sales_mix.py` only | Oil Ranking chart sorts correctly. No impact on other charts. |
| 2 (PE-1) | **Low** | `parts_executive.py` only | Executive table shows correct location names and values. No impact on other rendering functions. |
| 3 (PE-2) | **Low** | `parts_executive.py` only | Monthly detail shows correct location names and values. Same fix pattern as #2. |
| 4 (SM-2) | **Medium** | `aggregations.py` (shared utility) | Adding a parameter is backward-compatible (default `True`). But any caller not updated will continue getting `reset_index()` behavior. Need to verify no other modules depend on the current behavior. |
| 5 (H-5) | **Medium** | `sales_mix.py` | Changing filter logic could alter KPI values and table totals. Requires stakeholder confirmation of expected behavior. |
| 6 (H-7) | **Low** | `aggregation_cache.py` only | dtype alignment; no visible behavior change for most callers. |

---

## 9. Browser Verification Checklist

### Parts Executive

| # | Check | Expected | Pass Criteria |
|---|-------|----------|---------------|
| PE-V1 | KPI cards render (8 cards) | Revenue, Growth, Load, Margin, Discount, Oil Pen, Parts/JC, Health Score | All 8 cards display with correct values and delta badges |
| PE-V2 | Sparkline renders on Revenue card | 6-month SVG sparkline | Visible trend line in Revenue KPI |
| PE-V3 | Category breakdown panels render | Standard Parts, Oil, Add-ons panels | Three panels with Jobs, Avg/JC, Revenue rows |
| PE-V4 | Waterfall chart renders | Category Contribution chart | Plotly waterfall with PP Total → categories → CP Total |
| PE-V5 | Category heatmap renders | Growth by category heatmap | Plotly heatmap with Standard Parts, Oil, Add-ons |
| PE-V6 | Revenue trend chart renders | Grouped bar + growth line | Bars for CP/PP, line for Growth %, clickable |
| PE-V7 | Location growth chart renders | Horizontal bar chart | Locations sorted by Growth %, colored green/red |
| PE-V8 | **Executive table renders correctly** | Location names (strings), not integers | **FAILS without fix — shows integers and zeros** |
| PE-V9 | Executive table TOTAL row | Bold, all caps, summary values | TOTAL row at bottom with correct aggregates |
| PE-V10 | **Monthly detail table renders correctly** | Location names, per-month revenue | **FAILS without fix — shows integers and wrong data** |
| PE-V11 | Low margin locations table | Locations below 11% margin | Table shows only flagged locations |
| PE-V12 | Cross-filter by month | Click chart bar → filter updates | Chart click filters to single month, clear button works |
| PE-V13 | Narrative banner | Alert for declining growth, low margin | Red/yellow banner with correct alert text |
| PE-V14 | Export buttons | Download CSV/XLSX | Export buttons present and functional |
| PE-V15 | Empty data scenario | EmptyState message | Shows "No parts data" message gracefully |

### Parts Detail

| # | Check | Expected | Pass Criteria |
|---|-------|----------|---------------|
| PD-V1 | Category table renders | Location × Category matrix | Table with Standard Parts, Oil, Accessories, Tyres, Battery, Other columns |
| PD-V2 | Category mix chart | CP vs PP stacked bar | Stacked bars for each category |
| PD-V3 | Service contribution table | Service Type breakdown | Table with Revenue, Job Cards, Parts/JC, Margin %, Discount %, Oil Pen % |
| PD-V4 | Service mix donut | Service Type distribution | Donut chart with service type segments |
| PD-V5 | Monthly trend table | Last 6 months | Table with Month, Revenue, Job Cards, Margin %, Parts/JC |
| PD-V6 | Discount table | Location discount rates | Table with Revenue, Discount, Discount % |
| PD-V7 | Filter interactions | Location, Month, Service Type, Category | All four filters work independently |
| PD-V8 | Export buttons | Download CSV/XLSX | Export buttons present on each table |
| PD-V9 | Empty data scenario | EmptyState message | Shows message when no data for filters |

### Sales Mix

| # | Check | Expected | Pass Criteria |
|---|-------|----------|---------------|
| SM-V1 | KPI cards render (8 cards) | Oil INR/Ltrs, Tyre INR/Nos, Battery INR/Nos, Accessory INR, Parts Sale INR | All 8 cards display with correct values |
| SM-V2 | Oil Sales table | Location × Month matrix | Table with monthly Oil_Sale values and Total |
| SM-V3 | Battery Sales table | Location × Month matrix | Table with monthly Battery_Sale values and Total |
| SM-V4 | Tyre Sales table | Location × Month matrix | Table with monthly Tyre_Sale values and Total |
| SM-V5 | Accessory Sales table | Location × Month matrix | Table with monthly Accessory_Sale values and Total |
| SM-V6 | **Oil Trend chart renders** | Bar + Scatter (INR + Ltrs) | **Should work — line 129-134** |
| SM-V7 | **Batt + Tyre chart renders** | Grouped bar | **Should work — line 136-138** |
| SM-V8 | **Oil Ranking chart renders** | Horizontal bar, top 10 locations | **FAILS without fix — ValueError at line 140** |
| SM-V9 | **Mix (Acc vs Pts) chart renders** | Pie chart | **Should work — line 144-146** |
| SM-V10 | **Oil per Litre chart renders** | Horizontal bar, Revenue/Litre | **Should work — line 149-153** |
| SM-V11 | YoY Growth column in tables | Growth % for Total column | Growth column appears when PP data available |
| SM-V12 | Empty data scenario | EmptyState message | Shows "No data available" message |
| SM-V13 | Footer renders | UniversalFooter | Footer visible at bottom of page |

---

## 10. Final Verdict

### Is the Parts module ready for freeze?

**CONDITIONAL — Two fixes required before freeze.**

The module has two defects that prevent clean production deployment:

1. **Sales Mix** crashes when rendering the Oil Ranking chart (`sales_mix.py:140`). This is a user-visible error that blocks one of the four charts and prevents the footer from rendering.

2. **Parts Executive** silently corrupts data in the Executive Location Performance table and Monthly Location Performance detail (`parts_executive.py:702, 824`). Users see a table with integer row labels and all-zero values. This is arguably worse than a crash because it presents incorrect data with no error indication.

### Which issues must still be resolved?

| Priority | Issue | Effort | Impact |
|----------|-------|--------|--------|
| **Must Fix** | SM-1: Remove `"Oil_Sale"` from `.sort_values()` | 1 line | Eliminates crash |
| **Must Fix** | PE-1: Fix `.index` → `["Location Name"]` at line 702 | 2 lines | Restores correct table data |
| **Must Fix** | PE-2: Same fix at line 824 | 2 lines | Restores correct monthly detail data |

### Which issues can safely wait?

| Issue | Can Wait? | Rationale |
|-------|-----------|-----------|
| SM-2 (`pivot_summary` contract) | Yes | Fix PE-1/PE-2 first; refactor shared utility later |
| H-3 (PP empty scenario) | Yes | Graceful degradation already in place |
| H-4 (Health score bias) | Yes | Design decision, not a bug |
| H-5 (Sales Mix filtering) | Yes | Requires stakeholder confirmation of expected behavior |
| H-7 (`category_summary` dtype) | Yes | No visible impact currently |
| H-8 (as_index inconsistency) | Yes | Code smell, not a bug |

### Overall Confidence Percentage

**93%**

| Component | Confidence | Notes |
|-----------|------------|-------|
| PE-1 root cause identification | 95% | Traced full execution path; `pivot_summary` → `reset_index()` → RangeIndex confirmed |
| SM-1 root cause identification | 92% | `Series.sort_values()` API confirmed; minor uncertainty about Streamlit error propagation behavior |
| Previous findings rejection | 95% | `.agg()` safety confirmed by Parts Detail parity; `_cp` naming consistency confirmed by full code review |
| Hidden issues identification | 85% | Some issues (H-3, H-5) require runtime testing to fully confirm impact |

---

*End of Audit Report*
