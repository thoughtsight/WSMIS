# Git Commit Plan

**Date:** June 23, 2026  
**Purpose:** Classify all changed files for clean Parts Module v1.0 freeze milestone

---

## A. Parts Module Freeze

Files that are genuinely part of the completed Parts Module work.

| Path | Category | Reason |
|------|----------|--------|
| PARTS_MODULE_CHANGELOG.md | A | Parts Module documentation - changelog |
| PARTS_MODULE_FREEZE_REPORT.md | A | Parts Module documentation - freeze report |
| PARTS_MODULE_MAINTENANCE_GUIDE.md | A | Parts Module documentation - maintenance guide |
| PARTS_MODULE_RELEASE_NOTES_v1.0.md | A | Parts Module documentation - release notes |
| PARTS_MODULE_TECHNICAL_DEBT.md | A | Parts Module documentation - technical debt |
| SPRINT_4C_COMPLETION_REPORT.md | A | Parts Module documentation - Sprint 4C completion |
| app.py | A | Modified to pass targets_df to Parts Executive |
| ui/components/metrics.py | A | Modified for MetricCard growth calculation (used by Parts) |
| views/commercial/parts_executive.py | A | Parts Executive dashboard with target overlay |
| views/commercial/parts_detail.py | A | Parts Detail dashboard with category filter |
| views/commercial/sales_mix.py | A | Sales Mix dashboard with comparison support |
| views/dashboard_common.py | A | Navigation utilities for Parts drill-through |
| services/state_manager.py | A | State management infrastructure for Parts |
| services/state_registry.py | A | State registry for Parts namespace |
| views/shared.py | A | Shared imports used by Parts module |
| views/components/chart_engine.py | A | Chart engine used by Parts module |
| views/components/kpi_engine.py | A | KPI wrapper used by Parts module |

---

## B. Global Refactoring

Files modified because of wider architecture work (v2 refactoring).

| Path | Category | Reason |
|------|----------|--------|
| .gitignore | B | Global configuration update |
| config/environment.py | B | Credential handling refactoring |
| config/settings.py | B | Settings configuration update |
| exp_report.py | B | Expense report refactoring |
| pnl_report.py | B | P&L report refactoring |
| requirements.txt | B | Dependencies update |
| services/aggregation_cache.py | B | Caching infrastructure refactoring |
| services/ai/context_builder.py | B | AI context builder refactoring |
| services/ai/report_generator.py | B | AI report generator refactoring |
| services/financial_service.py | B | Financial service refactoring |
| static/style.css | B | Global styling update |
| tests/test_calculations.py | B | Test updates for refactoring |
| tests/test_filters.py | B | Test updates for refactoring |
| tests/test_pages.py | B | Test updates for refactoring |
| ui/components/__init__.py | B | Component exports refactoring |
| ui/components/core.py | B | Core components refactoring |
| ui/components/filters.py | B | Filter components refactoring |
| ui/components/tables.py | B | Table components refactoring |
| ui/design_tokens.py | B | Theme tokens refactoring |
| ui/helpers.py | B | Helper functions refactoring |
| ui/tables.py | B | Table utilities refactoring |
| ui/traffic.py | B | Traffic component refactoring |
| utils/aggregations.py | B | Aggregation helpers refactoring |
| utils/calculations/discount.py | B | Discount calculations refactoring |
| utils/cleaning.py | B | Data cleaning refactoring |
| utils/constants.py | B | Constants refactoring |
| utils/filters.py | B | Filter utilities refactoring |
| utils/loaders.py | B | Data loaders refactoring |
| utils/profiler.py | B | Profiling refactoring |
| views/advisor.py | B | Advisor view refactoring |
| views/advisor_mom.py | B | Advisor MoM view refactoring |
| views/audit_intelligence.py | B | Audit intelligence view refactoring |
| views/cockpit.py | B | Cockpit view refactoring |
| views/discount.py | B | Discount view refactoring |
| views/executive.py | B | Executive view refactoring |
| views/expense.py | B | Expense view refactoring |
| views/internal_audit.py | B | Internal audit view refactoring |
| views/labour.py | B | Labour view refactoring |
| views/leakage.py | B | Leakage view refactoring |
| views/locations.py | B | Locations view refactoring |
| views/margin.py | B | Margin view refactoring |
| views/overview.py | B | Overview view refactoring |
| views/pnl.py | B | P&L view refactoring |
| views/reports.py | B | Reports view refactoring |
| views/sales_mix.py | B | Sales Mix view refactoring (old location) |
| views/system_health.py | B | System health view refactoring |
| views/targets.py | B | Targets view refactoring |
| views/trends.py | B | Trends view refactoring |

---

## C. Navigation

Files related only to navigation infrastructure.

| Path | Category | Reason |
|------|----------|--------|
| views/executive/cockpit.py | C | Executive cockpit navigation |
| views/executive/command_center.py | C | Command center navigation |
| views/executive/executive.py | C | Executive navigation |
| views/executive/overview.py | C | Executive overview navigation |
| views/financial/ | C | Financial navigation module |
| views/operations/ | C | Operations navigation module |
| views/performance/ | C | Performance navigation module |
| views/trend/ | C | Trend navigation module |
| views/unauthorized.py | C | Unauthorized page navigation |

---

## D. Architecture Cleanup

Files related only to architecture cleanup (deprecated file removal).

| Path | Category | Reason |
|------|----------|--------|
| D .streamlit/config.toml | D | Deprecated Streamlit config |
| D CHANGELOG.md | D | Deprecated changelog |
| D CONTRIBUTING.md | D | Deprecated contributing guide |
| D DATA_LINEAGE_AUDIT.md | D | Deprecated audit document |
| D DEPLOYMENT.md | D | Deprecated deployment guide |
| D LABOUR_FINAL_CORRECTIONS_VALIDATION.md | D | Deprecated validation document |
| D LABOUR_FINAL_UAT_VALIDATION.md | D | Deprecated UAT document |
| D LABOUR_IMPLEMENTATION_VERIFICATION.md | D | Deprecated verification document |
| D LABOUR_REVISION_3_SUMMARY.md | D | Deprecated revision summary |
| D LABOUR_V3.2_IMPLEMENTATION.md | D | Deprecated implementation doc |
| D LABOUR_V3.3_IMPLEMENTATION.md | D | Deprecated implementation doc |
| D LABOUR_V3.4_VERIFICATION.md | D | Deprecated verification doc |
| D MERGE_TO_MAIN_REPORT.md | D | Deprecated merge report |
| D MONTH_FORENSIC_AUDIT.md | D | Deprecated audit document |
| D README.md | D | Deprecated README |
| D WSMIS_Audit_Intelligence_Framework.md | D | Deprecated framework doc |
| D WSMIS_Gemini_Diagnostic_Report.md | D | Deprecated diagnostic report |
| D WSMIS_Gemini_Validation.md | D | Deprecated validation report |
| D WSMIS_Performance_Audit.md | D | Deprecated performance audit |
| D WSMIS_Product_Audit.md | D | Deprecated product audit |
| D body.json | D | Deprecated JSON file |
| D cleanup_headers.py | D | Deprecated cleanup script |
| D dashboards/__init__.py | D | Deprecated dashboards module |
| D forensic_audit.py | D | Deprecated forensic audit script |
| D forensic_audit_v2.py | D | Deprecated forensic audit v2 |
| D forensic_audit_v3.py | D | Deprecated forensic audit v3 |
| D forensic_audit_v4.py | D | Deprecated forensic audit v4 |
| D internal_audit_app.py | D | Deprecated internal audit app |
| D scripts/test_audit_integration.py | D | Deprecated test script |
| D services/ai_service.py | D | Deprecated AI service |
| D test_alerts.py | D | Deprecated test script |
| D test_app_load.py | D | Deprecated test script |
| D test_cache_hash.py | D | Deprecated test script |
| D test_fmt.txt | D | Deprecated test file |
| D test_groupby.py | D | Deprecated test script |
| D ui/components/charts.py | D | Deprecated charts component |
| D ui/components/theme.py | D | Deprecated theme component |
| D update_app.py | D | Deprecated update script |
| D utils/calculations/pnl.py | D | Deprecated P&L calculations |
| D utils/calculations/targets.py | D | Deprecated targets calculations |
| D utils/chart_theme.py | D | Deprecated chart theme |
| D utils/validation.py | D | Deprecated validation utilities |
| D views/yoy.py | D | Deprecated YoY view |
| WSMIS_ARCHITECTURE_CLEANUP_BACKLOG.md | D | Architecture cleanup documentation |

---

## E. Temporary / Debug

Regression scripts, test harnesses, temporary markdown files, generated files, screenshots, logs, etc.

| Path | Category | Reason |
|------|----------|--------|
| ?? -H | E | Temporary file |
| ?? 01_WSMIS_Architecture_Pack.md | E | Temporary documentation |
| ?? 02_WSMIS_Implementation_Pack.md | E | Temporary documentation |
| ?? 03_WSMIS_Codebase_Index.md | E | Temporary documentation |
| ?? Chart_API_Compatibility_Report.md | E | Temporary documentation |
| ?? Chart_Migration_Final_Readiness.md | E | Temporary documentation |
| ?? Chart_Migration_Plan.md | E | Temporary documentation |
| ?? Executive Command Center Blueprint (Claude Sonnet).txt | E | Temporary documentation |
| ?? Executive Command Center Review (Claude Opus 4.8).md | E | Temporary documentation |
| ?? Executive Command Center Review (Claude Opus 4.8).md.bak | E | Temporary backup file |
| ?? Executive_Command_Center_BugFix_Report.md | E | Temporary documentation |
| ?? Mimo_Change_Audit_Report.md | E | Temporary documentation |
| ?? New Text Document.txt.bak | E | Temporary backup file |
| ?? PARTS_DEFERRED_BACKLOG.md | E | Temporary documentation (already in PARTS_MODULE_TECHNICAL_DEBT.md) |
| ?? PARTS_KPI_DEFINITIONS.md | E | Temporary documentation |
| ?? Presentation_Polish_Report.md | E | Temporary documentation |
| ?? TARGET_USAGE_MAP.md | E | Temporary documentation |
| ?? UI_Audit_Package.md | E | Temporary documentation |
| ?? Visual_Restoration_Report.md | E | Temporary documentation |
| ?? WSMIS_ARCHITECTURE_REVIEW_PACK.txt | E | Temporary documentation |
| ?? WSMIS_CodeReview_Bundle_Day3.txt | E | Temporary documentation |
| ?? WSMIS_Implementation_Roadmap.md | E | Temporary documentation |
| ?? WSMIS_PARTS_MODULE_REVIEW.txt | E | Temporary documentation |
| ?? WSMIS_Parts_Forensic_Audit_MiMo.md | E | Temporary documentation |
| ?? WSMIS_Phase1_Closure_Report.md | E | Temporary documentation |
| ?? WSMIS_Phase1_Engineering_Book.md | E | Temporary documentation |
| ?? WSMIS_Phase1_Final_Signoff_Report.md | E | Temporary documentation |
| ?? WSMIS_Phase1_Implementation_Summary.md | E | Temporary documentation |
| ?? WSMIS_Repository_Audit_Final.md | E | Temporary documentation |
| ?? WSMIS_Repository_Cleanup_Audit.md | E | Temporary documentation |
| ?? config/ai_config.py | E | Temporary configuration |
| ?? config/users.yaml | E | Temporary configuration |
| ?? diff_report.txt | E | Temporary diff output |
| ?? docs/FRAMEWORK.md | E | Temporary documentation |
| ?? docs/MIGRATION_GUIDE.md | E | Temporary documentation |
| ?? reports/ | E | Temporary reports directory |
| ?? run_parts_regression.py | E | Temporary regression script |
| ?? scratch_tokens.txt | E | Temporary debug file |
| ?? scripts/migrate_chart_engine.py | E | Temporary migration script |
| ?? scripts/rewrite_imports.py | E | Temporary migration script |
| ?? services/ai/provider.py | E | Temporary AI provider |
| ?? services/audit_service.py | E | Temporary audit service |
| ?? services/auth_service.py | E | Temporary auth service |
| ?? services/route_service.py | E | Temporary route service |
| ?? test_production.py | E | Temporary test script |
| ?? tests/golden_snapshots.json | E | Temporary test data |
| ?? tests/test_golden_snapshot.py | E | Temporary test script |
| ?? views/commercial/ | E | Temporary directory (should be in A) |
| ?? views/components/ | E | Temporary directory (should be in A) |
| ?? views/dashboard_common.py | E | Temporary file (should be in A) |
| ?? views/executive/ | E | Temporary directory (should be in C) |
| ?? views/financial/ | E | Temporary directory (should be in C) |
| ?? views/operations/ | E | Temporary directory (should be in C) |
| ?? views/parts_detail.py | E | Temporary file (should be in A) |
| ?? views/parts_executive.py | E | Temporary file (should be in A) |
| ?? views/performance/ | E | Temporary directory (should be in C) |
| ?? views/shared.py | E | Temporary file (should be in A) |
| ?? views/trend/ | E | Temporary directory (should be in C) |
| ?? views/unauthorized.py | E | Temporary file (should be in C) |

---

## Summary

**Category A (Parts Module Freeze):** 17 files  
**Category B (Global Refactoring):** 45 files  
**Category C (Navigation):** 9 files  
**Category D (Architecture Cleanup):** 53 files  
**Category E (Temporary/Debug):** 57 files

**Total:** 181 files

---

## Recommended Commit Strategy

### Problem
The working tree contains 181 changed files spanning multiple refactoring efforts. A single commit would mix Parts Module freeze with global v2 refactoring, making it impossible to create a clean milestone.

### Recommended Approach: Staged Commits

#### Option 1: Cherry-Pick Parts Module Files (Recommended)
1. **Create a new branch** from the current state: `git checkout -b parts-v1.0-freeze`
2. **Stage only Category A files**:
   - 7 documentation files (already staged)
   - app.py (selective diff for targets_df change only)
   - ui/components/metrics.py (selective diff for growth calculation)
   - views/commercial/parts_executive.py
   - views/commercial/parts_detail.py
   - views/commercial/sales_mix.py
   - views/dashboard_common.py
   - services/state_manager.py
   - services/state_registry.py
   - views/shared.py
   - views/components/chart_engine.py
   - views/components/kpi_engine.py
3. **Commit with Parts Module freeze message**
4. **Create tag:** `parts-v1.0-freeze`
5. **Switch back** to feature/v2-architecture
6. **Continue** with v2 refactoring commits

#### Option 2: Git Stash & Clean
1. **Stash all changes:** `git stash push -u -m "WIP: v2 refactoring"`
2. **Create clean branch:** `git checkout -b parts-v1.0-freeze`
3. **Apply only Parts Module changes** from stash
4. **Commit Parts Module freeze**
5. **Create tag:** `parts-v1.0-freeze`
6. **Pop stash** and continue v2 refactoring

#### Option 3: Selective Patch
1. **Create patch file** with only Category A changes
2. **Apply patch** to clean branch
3. **Commit Parts Module freeze**
4. **Create tag:** `parts-v1.0-freeze`

### Recommendation
**Option 1 (Cherry-Pick)** is recommended because:
- It preserves all work in the current branch
- It allows selective staging of specific file changes
- It's the most controlled approach
- It doesn't risk losing any work

### Next Steps
1. User approval of this classification
2. User approval of recommended strategy
3. Execute selective staging of Category A files
4. Review staged changes before commit
5. Commit with specified message
6. Create tag `parts-v1.0-freeze`
7. Provide final report

---

## Notes

**Category E Clarification:**
Several files marked as Category E (Temporary) are actually part of the Parts Module infrastructure:
- `views/commercial/` - Should be Category A
- `views/components/` - Should be Category A
- `views/dashboard_common.py` - Should be Category A
- `views/parts_detail.py` - Should be Category A
- `views/parts_executive.py` - Should be Category A
- `views/shared.py` - Should be Category A
- `views/executive/` - Should be Category C
- `views/financial/` - Should be Category C
- `views/operations/` - Should be Category C
- `views/performance/` - Should be Category C
- `views/trend/` - Should be Category C
- `views/unauthorized.py` - Should be Category C

These are marked as E because they are currently untracked (??) but should be included in the appropriate category when staged.
