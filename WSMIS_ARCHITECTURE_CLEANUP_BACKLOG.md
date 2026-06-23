# WSMIS Architecture Cleanup Backlog

**Date:** June 23, 2026  
**Version:** 1.0  
**Purpose:** Comprehensive audit of architecture issues across the WSMIS repository

---

## Executive Summary

This backlog documents all architecture issues identified through a comprehensive audit of the WSMIS repository. Issues are grouped into epics and prioritized based on severity, effort, and timing (before v1.0, after v1.0, or deferred to v2.0).

**Total Issues:** 15  
**Critical (Before v1.0):** 2  
**High (After v1.0):** 6  
**Medium (After v1.0):** 4  
**Low (Deferred to v2.0):** 3

---

## Epic 1: Duplicate Google Sheets Loaders

### Issue 1.1: Duplicate load_data() Functions
**Files Affected:**
- `app.py` (line 118)
- `services/audit_service.py` (line 185)

**Description:**
Two separate `load_data()` functions exist with different purposes:
- `app.py:load_data()` - Main data loader for the application
- `services/audit_service.py:load_data()` - Audit-specific data loader

**Severity:** Medium  
**Estimated Effort:** 2-3 hours  
**Regression Risk:** Medium  
**Timing:** After v1.0

**Rationale:**
The two functions serve different purposes but share the same name, which can cause confusion. Renaming one or consolidating into a single loader with parameters would improve clarity.

---

### Issue 1.2: Duplicate load_contacts() Functions
**Files Affected:**
- `services/audit_service.py` (line 17)
- `utils/loaders.py` (line 112)

**Description:**
Two separate `load_contacts()` functions exist with potentially different implementations. This creates ambiguity about which function should be used.

**Severity:** Medium  
**Estimated Effort:** 1-2 hours  
**Regression Risk:** Low  
**Timing:** After v1.0

**Rationale:**
Consolidate into a single canonical loader in utils/loaders.py and update all imports.

---

### Issue 1.3: gspread Import in app.py
**Files Affected:**
- `app.py` (line 16)
- `utils/loaders.py` (line 2)

**Description:**
`gspread` is imported in both app.py and utils/loaders.py. The canonical loader is in utils/loaders.py, so the import in app.py is redundant.

**Severity:** Low  
**Estimated Effort:** 0.5 hours  
**Regression Risk:** Low  
**Timing:** After v1.0

**Rationale:**
Remove gspread import from app.py since all gspread operations should go through utils/loaders.py.

---

## Epic 2: Duplicate Calculations

### Issue 2.1: Inline Growth Calculations (Canonical Helpers Available)
**Files Affected:**
- `ui/components/metrics.py` (line 98)
- `ui/traffic.py` (lines 10, 20)
- `utils/calculations/discount.py` (lines 45, 51, 55)
- `utils/calculations/margin.py` (lines 27, 33)

**Description:**
While canonical helpers (`calc_growth_pct`, `calc_ratio`) exist in `utils/calculations/common.py`, some files still perform inline calculations. This is not a duplicate but rather inconsistent usage.

**Severity:** Low  
**Estimated Effort:** 1-2 hours  
**Regression Risk:** Low  
**Timing:** After v1.0

**Rationale:**
Ensure all calculations use canonical helpers for consistency and maintainability.

---

## Epic 3: Duplicate Repositories/Services

**Status:** No issues found. Services are well-organized with clear separation of concerns.

---

## Epic 4: Duplicate Pivots/GroupBy Logic

### Issue 4.1: Direct groupby() Calls Instead of Canonical Helpers
**Files Affected:**
- `services/audit_service.py` (lines 62, 63, 104)
- `ui/helpers.py` (lines 127, 162, 170)
- `utils/calculations/leakage.py` (lines 23, 42)
- `views/commercial/discount.py` (lines 142, 153, 172, 198, 207)
- `views/commercial/labour.py` (lines 27, 28, 29)

**Description:**
Many files use direct `df.groupby()` calls instead of canonical aggregation helpers (`location_summary`, `monthly_summary`, etc.). This creates inconsistent aggregation patterns.

**Severity:** Medium  
**Estimated Effort:** 4-6 hours  
**Regression Risk:** Medium  
**Timing:** After v1.0

**Rationale:**
Migrate direct groupby calls to canonical helpers for consistency and to leverage caching benefits.

---

### Issue 4.2: Direct pivot_table() Calls Instead of Canonical Helpers
**Files Affected:**
- `ui/helpers.py` (lines 167, 175)
- `views/commercial/labour.py` (lines 89, 91)
- `views/commercial/sales_mix.py` (lines 81, 88)
- `exp_report.py` (lines 746, 753, 782, 783)

**Description:**
Many files use direct `pd.pivot_table()` calls instead of the canonical `pivot_summary()` helper in `utils/aggregations.py`.

**Severity:** Medium  
**Estimated Effort:** 3-4 hours  
**Regression Risk:** Medium  
**Timing:** After v1.0

**Rationale:**
Migrate direct pivot_table calls to canonical helper for consistency.

---

## Epic 5: Duplicate Filters

**Status:** No issues found. Filters are well-centralized in `utils/filters.py` and widely used across the codebase.

---

## Epic 6: Duplicate KPI Logic

### Issue 6.1: Unused KPIEngine Imports
**Files Affected:**
- `views/components/kpi_engine.py` (entire file)

**Description:**
`views/components/kpi_engine.py` exists as a wrapper around `KPIGrid` from `ui/components/metrics.py`. The wrapper provides no additional functionality and creates confusion about which component to use.

**Severity:** Low  
**Estimated Effort:** 1 hour  
**Regression Risk:** Low  
**Timing:** After v1.0

**Rationale:**
Remove the wrapper and update all imports to use `KPIGrid` directly from `ui/components/metrics.py`.

---

## Epic 7: Duplicate Exports

**Status:** No issues found. Exports are well-centralized in `services/export_service.py` and `ui/export_buttons.py`.

---

## Epic 8: Duplicate Navigation/State

### Issue 8.1: Inconsistent StateManager Namespace Usage
**Files Affected:**
- `views/commercial/labour.py` (lines 10, 15, 16, 165, 182, 185, 427, 428)
- `views/commercial/parts_executive.py` (lines 9, 19, 20, 701, 702)
- `views/executive/command_center.py` (line 10)
- `views/dashboard_common.py` (lines 9, 203, 222, 225, 292, 297, 298)

**Description:**
While StateManager is centralized, the namespace prefixes are inconsistent (`lab_`, `parts_`, etc.). There is no framework-level enforcement of namespace conventions.

**Severity:** Low  
**Estimated Effort:** 2-3 hours  
**Regression Risk:** Low  
**Timing:** Deferred to v2.0

**Rationale:**
Add framework-level namespace validation or linting rules to ensure consistent naming conventions.

---

## Epic 9: Duplicate Theme/Color Usage

### Issue 9.1: Hardcoded Colors in Deprecated Files
**Files Affected:**
- `archive/deprecated/revenue_leakage_v2.py` (multiple lines)

**Description:**
Deprecated files in the archive folder contain hardcoded hex colors. This is not an issue for active code but should be noted for historical context.

**Severity:** None  
**Estimated Effort:** 0 hours  
**Regression Risk:** None  
**Timing:** N/A (archived code)

**Rationale:**
No action needed. These files are deprecated and archived.

---

### Issue 9.2: Deprecated apply_chart() Function
**Files Affected:**
- `ui/helpers.py` (lines 13-23)
- `ui/helpers.py` (line 185)

**Description:**
`apply_chart()` in `ui/helpers.py` is deprecated in favor of `ChartEngine.apply_chart()` from `views/components/chart_engine.py`. The function still exists and is called in one location.

**Severity:** Low  
**Estimated Effort:** 1 hour  
**Regression Risk:** Low  
**Timing:** After v1.0

**Rationale:**
Remove the deprecated function and update the single call site to use ChartEngine directly.

---

## Epic 10: Performance Bottlenecks

### Issue 10.1: Inconsistent Aggregation Cache Usage
**Files Affected:**
- `views/commercial/discount.py` (multiple groupby calls)
- `views/commercial/labour.py` (multiple groupby calls)
- `views/commercial/sales_mix.py` (multiple groupby calls)

**Description:**
While an aggregation cache exists in `services/aggregation_cache.py`, not all aggregation operations use it. Direct groupby/pivot operations bypass the cache, potentially causing performance issues.

**Severity:** High  
**Estimated Effort:** 6-8 hours  
**Regression Risk:** Medium  
**Timing:** Before v1.0

**Rationale:**
Migrate all aggregation operations to use canonical helpers that leverage the cache. This will improve performance for large datasets.

---

### Issue 10.2: Redundant DataFrame Operations
**Files Affected:**
- Multiple view files with repeated filtering and aggregation

**Description:**
Some views perform the same filtering and aggregation operations multiple times within a single render cycle. This can be optimized by caching intermediate results.

**Severity:** Medium  
**Estimated Effort:** 4-6 hours  
**Regression Risk:** Medium  
**Timing:** After v1.0

**Rationale:**
Audit render functions for redundant operations and cache intermediate results where appropriate.

---

## Epic 11: Technical Debt

### Issue 11.1: TODO Comment in utils/loaders.py
**Files Affected:**
- `utils/loaders.py` (line 163)

**Description:**
A TODO comment exists regarding schema mapping for approved-discount columns in MP_PB_Targets. This is pending schema changes in the data source.

**Severity:** Low  
**Estimated Effort:** 1 hour (when schema is available)  
**Regression Risk:** Low  
**Timing:** Deferred to v2.0

**Rationale:**
This is blocked by external schema changes. Implement when the schema is available.

---

### Issue 11.2: Archive Folder Cleanup
**Files Affected:**
- `archive/` directory (entire folder)

**Description:**
The archive folder contains deprecated and test files that are no longer needed. These files create confusion and increase repository size.

**Severity:** Low  
**Estimated Effort:** 2-3 hours  
**Regression Risk:** None  
**Timing:** Deferred to v2.0

**Rationale:**
Clean up the archive folder by removing truly deprecated files. Keep only files that have historical value for reference.

---

### Issue 11.3: Deprecated Chart Engine Migration Script
**Files Affected:**
- `scripts/migrate_chart_engine.py` (entire file)

**Description:**
The migration script for ChartEngine is no longer needed after the migration is complete. It should be removed or archived.

**Severity:** Low  
**Estimated Effort:** 0.5 hours  
**Regression Risk:** None  
**Timing:** After v1.0

**Rationale:**
Remove or archive the migration script since the migration is complete.

---

## Summary by Timing

### Before v1.0 (Critical)
1. **Issue 10.1:** Inconsistent Aggregation Cache Usage - HIGH severity, 6-8 hours

### After v1.0 (High Priority)
1. **Issue 1.1:** Duplicate load_data() Functions - MEDIUM severity, 2-3 hours
2. **Issue 1.2:** Duplicate load_contacts() Functions - MEDIUM severity, 1-2 hours
3. **Issue 4.1:** Direct groupby() Calls - MEDIUM severity, 4-6 hours
4. **Issue 4.2:** Direct pivot_table() Calls - MEDIUM severity, 3-4 hours
5. **Issue 10.2:** Redundant DataFrame Operations - MEDIUM severity, 4-6 hours
6. **Issue 9.2:** Deprecated apply_chart() Function - LOW severity, 1 hour

### After v1.0 (Medium Priority)
1. **Issue 1.3:** gspread Import in app.py - LOW severity, 0.5 hours
2. **Issue 2.1:** Inline Growth Calculations - LOW severity, 1-2 hours
3. **Issue 6.1:** Unused KPIEngine Imports - LOW severity, 1 hour
4. **Issue 11.3:** Deprecated Chart Engine Migration Script - LOW severity, 0.5 hours

### Deferred to v2.0 (Low Priority)
1. **Issue 8.1:** Inconsistent StateManager Namespace Usage - LOW severity, 2-3 hours
2. **Issue 11.1:** TODO Comment in utils/loaders.py - LOW severity, 1 hour
3. **Issue 11.2:** Archive Folder Cleanup - LOW severity, 2-3 hours

---

## Implementation Sequence Recommendation

### Phase 1: Before v1.0 (Critical Performance)
1. **Issue 10.1:** Migrate all aggregations to use canonical helpers with cache support

### Phase 2: After v1.0 (Consistency & Cleanup)
1. **Issue 1.1:** Consolidate duplicate load_data() functions
2. **Issue 1.2:** Consolidate duplicate load_contacts() functions
3. **Issue 4.1:** Migrate direct groupby() calls to canonical helpers
4. **Issue 4.2:** Migrate direct pivot_table() calls to canonical helpers
5. **Issue 10.2:** Optimize redundant DataFrame operations
6. **Issue 9.2:** Remove deprecated apply_chart() function

### Phase 3: After v1.0 (Low-Hanging Fruit)
1. **Issue 1.3:** Remove redundant gspread import from app.py
2. **Issue 2.1:** Ensure all calculations use canonical helpers
3. **Issue 6.1:** Remove unused KPIEngine wrapper
4. **Issue 11.3:** Remove deprecated migration script

### Phase 4: v2.0 (Infrastructure Improvements)
1. **Issue 8.1:** Add framework-level namespace validation
2. **Issue 11.1:** Implement TODO comment when schema is available
3. **Issue 11.2:** Clean up archive folder

---

## Notes

### Positive Findings
- **Filters:** Well-centralized in `utils/filters.py` with consistent usage
- **Exports:** Well-centralized in `services/export_service.py` and `ui/export_buttons.py`
- **Calculations:** Canonical helpers exist in `utils/calculations/common.py` and are widely used
- **Theme/Colors:** Active code consistently uses `T.COLOR_*` tokens from `ui/design_tokens.py`
- **State Management:** StateManager is centralized in `services/state_manager.py`

### Areas of Excellence
- Canonical aggregation helpers exist and are used in many places
- Aggregation cache infrastructure is in place
- Export service is unified across all modules
- Design tokens provide consistent theming

### Key Observations
- Most "duplicates" are actually inconsistent usage of canonical helpers rather than true duplicates
- The architecture is generally well-organized with clear separation of concerns
- Performance improvements can be achieved by ensuring all aggregations use the cache
- Low-hanging fruit exists in removing deprecated functions and cleaning up imports
