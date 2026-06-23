# WSMIS Implementation Roadmap

**Workshop Management Information System — 6-Dashboard Architecture Implementation Plan**

| Field | Value |
|---|---|
| **Project** | WSMIS v1.0.0-rc1 → v2.0 |
| **Architecture** | 6-Dashboard Reporting Suite (Frozen) |
| **Scope** | Implementation impact analysis and phased roadmap |
| **Date** | June 2026 |
| **Status** | Planning Only — No Code Changes |
| **Classification** | CONFIDENTIAL — Internal Engineering |

---

## Table of Contents

1. [Architecture Baseline](#1-architecture-baseline)
2. [Files to DELETE](#2-files-to-delete)
3. [Files to MERGE](#3-files-to-merge)
4. [Files to RENAME](#4-files-to-rename)
5. [Files to KEEP Unchanged](#5-files-to-keep-unchanged)
6. [Shared Components to Create](#6-shared-components-to-create)
7. [Common KPI Engine to Create](#7-common-kpi-engine-to-create)
8. [Common Chart Engine to Create](#8-common-chart-engine-to-create)
9. [Navigation Changes](#9-navigation-changes)
10. [Sidebar Changes](#10-sidebar-changes)
11. [Router Changes](#11-router-changes)
12. [Export Framework Changes](#12-export-framework-changes)
13. [AI Module Integration Points](#13-ai-module-integration-points)
14. [Report Center Integration](#14-report-center-integration)
15. [Presentation Manager Integration](#15-presentation-manager-integration)
16. [Role/Profile Manager Integration](#16-roleprofile-manager-integration)
17. [Dashboard Designer Integration](#17-dashboard-designer-integration)
18. [Database/Config Changes](#18-databaseconfig-changes)
19. [Estimated Implementation Phases](#19-estimated-implementation-phases)
20. [Risk Assessment](#20-risk-assessment)
21. [Dependency Graph](#21-dependency-graph)
22. [Suggested Implementation Order](#22-suggested-implementation-order)
23. [Regression Checklist](#23-regression-checklist)

---

## 1. Architecture Baseline

### 1.1 Current State (19 Pages)

| Current Page | Current Module | Lines |
|---|---|---|
| Cockpit | `views/cockpit.py` | 388 |
| Overview | `views/overview.py` | 260 |
| Executive | `views/executive.py` | 353 |
| Labour | `views/labour.py` | 732 |
| Parts Executive | `views/parts_executive.py` | 535 |
| Parts Detail | `views/parts_detail.py` | 247 |
| Margin | `views/margin.py` | 181 |
| Discounts | `views/discount.py` | 987 |
| Leakage Center | `views/leakage.py` | 315 |
| Sales Mix | `views/sales_mix.py` | 134 |
| Advisors | `views/advisor.py` | 278 |
| Advisor MoM | `views/advisor_mom.py` | 271 |
| Locations | `views/locations.py` | 217 |
| Trends | `views/trends.py` | 238 |
| Targets | `views/targets.py` | 191 |
| Reports | `views/reports.py` | 317 |
| Expense Analysis | `views/expense.py` | 102 |
| Profit & Loss | `views/pnl.py` | 75 |
| Internal Audit | `views/internal_audit.py` | 567 |
| Audit Intelligence | `views/audit_intelligence.py` | 232 |
| System Health | `views/system_health.py` | 112 |

### 1.2 Target State (6 Dashboards)

| Dashboard | Sub-Modules | Pages Mapped |
|---|---|---|
| **D1: Operations** | Cockpit, Overview, System Health | 3 current pages |
| **D2: Revenue** | Labour, Parts Executive, Parts Detail, Margin, Sales Mix, Discounts, Leakage Center | 7 current pages |
| **D3: People** | Advisors, Advisor MoM | 2 current pages |
| **D4: Performance** | Locations, Trends, Targets | 3 current pages |
| **D5: Finance** | Expense Analysis, Profit & Loss, Executive (Financial) | 3 current pages |
| **D6: Audit** | Internal Audit, Audit Intelligence, Reports | 3 current pages |

### 1.3 Current Module Map

```
app.py (808 lines)
├── PAGE_CAPABILITIES (dict)          # Per-page filter config
├── sidebar_navigation()              # Sidebar nav with expanders
├── render_month_picker()             # Global filter toolbar
├── render_global_filters()           # Location + BU filters
├── render_page_header_filters()      # Service type + advisor filters
├── render_page_router()              # if/elif page dispatcher
├── load_data()                       # Google Sheets → DataFrame
├── compute_alerts()                  # Alert engine
└── classify_location()               # Arena/Nexa classifier

views/shared.py (41 lines)
└── Barrel re-exports (wildcard imports)

views/dashboard_common.py (246 lines)
├── inject_responsive_css()
├── apply_period_filters()
├── render_kpi_card()
├── render_svc_panel()
├── render_cross_filter_bar()
└── style_table_*()

services/state_manager.py (279 lines)
└── StateManager (namespace-driven session state)

services/state_registry.py (52 lines)
└── Registers 3 namespaces: lab_, parts_, cockpit_

services/aggregation_cache.py (208 lines)
└── Thread-safe aggregation cache with LRU

services/financial_service.py (70 lines)
└── Static methods facade

services/export_service.py (561 lines)
└── CSV/Excel/PDF export

services/ai/ (6 files)
└── AI narrative generation pipeline

ui/components/ (6 files)
├── core.py (Header, Footer, EmptyState, AlertBanner)
├── charts.py (ChartCard, apply_chart)
├── metrics.py (MetricCard, KPIGrid)
├── filters.py (FilterToolbar)
└── tables.py (TableCard)

ui/formatters.py (129 lines)
└── Indian currency/number formatters

ui/design_tokens.py (167 lines)
└── Design token registry

utils/calculations/ (8 files)
├── common.py (safe_divide, calc_ratio)
├── fact_metrics.py (base extractors)
├── revenue.py
├── margin.py
├── discount.py
├── leakage.py
├── pnl.py (EMPTY)
└── targets.py (EMPTY)

utils/aggregations.py (97 lines)
└── Cached groupby wrappers

utils/filters.py (97 lines)
└── DataFrame filter functions

utils/cleaning.py (110 lines)
└── Data cleaning pipeline

utils/constants.py (97 lines)
└── Global constants

utils/loaders.py (213 lines)
└── Google Sheets loaders
```

---

## 2. Files to DELETE

### 2.1 Root-Level Dead Scripts (48 files)

| # | File | Reason |
|---|---|---|
| 1 | `apply_tokens_safe.py` | One-time migration, never imported |
| 2 | `apply_tokens.py` | One-time migration, never imported |
| 3 | `audit_scan.py` | Codebase scanner, never imported |
| 4 | `capture.py` | Screenshot tool, never imported |
| 5 | `capture_final.py` | Screenshot tool, never imported |
| 6 | `capture_mobile.py` | Screenshot tool, never imported |
| 7 | `capture_verify.py` | Screenshot tool, never imported |
| 8 | `cleanup_headers.py` | One-time cleanup, never imported |
| 9 | `component_api.py` | Codebase scanner, never imported |
| 10 | `find_copies.py` | Codebase scanner, never imported |
| 11 | `find_fixes.py` | Codebase scanner, never imported |
| 12 | `fix_copies.py` | One-time fix, never imported |
| 13 | `fix_parens.py` | One-time fix, never imported |
| 14 | `forensic_audit.py` | Forensic script, never imported |
| 15 | `forensic_audit_v2.py` | Forensic script, never imported |
| 16 | `forensic_audit_v3.py` | Forensic script, never imported |
| 17 | `forensic_audit_v4.py` | Forensic script, never imported |
| 18 | `matrix.py` | Codebase scanner, never imported |
| 19 | `refactor_advisor.py` | One-time refactor, never imported |
| 20 | `refactor_audit.py` | One-time refactor, never imported |
| 21 | `refactor_cache_hash.py` | One-time refactor, never imported |
| 22 | `refactor_cache.py` | One-time refactor, never imported |
| 23 | `refactor_creds.py` | One-time refactor, never imported |
| 24 | `refactor_exports.py` | One-time refactor, never imported |
| 25 | `refactor_html.py` | One-time refactor, never imported |
| 26 | `refactor_imports.py` | One-time refactor, never imported |
| 27 | `refactor_imports2.py` | One-time refactor, never imported |
| 28 | `refactor_imports3.py` | One-time refactor, never imported |
| 29 | `refactor_views.py` | One-time refactor, never imported |
| 30 | `repo_metrics.py` | Codebase scanner, never imported |
| 31 | `research_dup.py` | Codebase scanner, never imported |
| 32 | `run_production_suite.py` | Test runner, never imported |
| 33 | `run_test_apptest.py` | Test runner, never imported |
| 34 | `run_test_callback.py` | Test runner, never imported |
| 35 | `run_test_mock.py` | Test runner, never imported |
| 36 | `run_test_nav_bug.py` | Test runner, never imported |
| 37 | `run_test_rerun.py` | Test runner, never imported |
| 38 | `run_test_session_init.py` | Test runner, never imported |
| 39 | `run_validation.py` | Test runner, never imported |
| 40 | `update_advisor.py` | One-time update, never imported |
| 41 | `update_app.py` | One-time update, never imported |
| 42 | `update_charts.py` | One-time update, never imported |
| 43 | `unused_scan.py` | Codebase scanner, never imported |
| 44 | `verify_hotfix.py` | Verification script, never imported |
| 45 | `verify_imports.py` | Verification script, never imported |
| 46 | `verify_labour_render.py` | Verification script, never imported |
| 47 | `verify_startup.py` | Verification script, never imported |
| 48 | `verify_streamlit.py` | Verification script, never imported |

### 2.2 Root-Level Test Files (15 files)

| # | File | Reason |
|---|---|---|
| 49 | `test_alerts.py` | Standalone test, not pytest |
| 50 | `test_app_load.py` | Standalone test, not pytest |
| 51 | `test_apptest.py` | Standalone test, not pytest |
| 52 | `test_cache_hash.py` | Standalone test, not pytest |
| 53 | `test_callback_lag.py` | Standalone test, not pytest |
| 54 | `test_groupby.py` | Standalone test, not pytest |
| 55 | `test_gui.py` | Standalone test, not pytest |
| 56 | `test_interactive.py` | Standalone test, not pytest |
| 57 | `test_mock_app.py` | Standalone test, not pytest |
| 58 | `test_nav_bug.py` | Standalone test, not pytest |
| 59 | `test_rerun_lifecycle.py` | Standalone test, not pytest |
| 60 | `test_seg.py` | Standalone test, not pytest |
| 61 | `test_selectbox.py` | Standalone test, not pytest |
| 62 | `test_session_init.py` | Standalone test, not pytest |
| 63 | `test_sm.py` | Standalone test, not pytest |

### 2.3 Root-Level Artifact Files (9 files)

| # | File | Reason |
|---|---|---|
| 64 | `body.json` | API test payload |
| 65 | `profile_results.json` | Profiler output |
| 66 | `top_functions.txt` | Profiler output |
| 67 | `margin_real.png` | Screenshot artifact |
| 68 | `parts_detail_real.png` | Screenshot artifact |
| 69 | `screenshot_desktop.png` | Screenshot artifact |
| 70 | `screenshot_mobile.png` | Screenshot artifact |
| 71 | `screenshot_monthly.png` | Screenshot artifact |
| 72 | `screenshot_tooltip.png` | Screenshot artifact |

### 2.4 Orphaned Modules (5 files)

| # | File | Reason |
|---|---|---|
| 73 | `core/registry.py` | Never imported by production code |
| 74 | `core/framework.py` | Only imported by `core/registry.py` (also orphaned) |
| 75 | `services/ai_service.py` | Superseded by `services/ai/` package |
| 76 | `utils/validation.py` | Never imported |
| 77 | `dashboards/__init__.py` | Empty package, never imported |

### 2.5 Empty Files (2 files)

| # | File | Reason |
|---|---|---|
| 78 | `utils/calculations/pnl.py` | Empty placeholder |
| 79 | `utils/calculations/targets.py` | Empty placeholder |

**Total files to delete: 79**

---

## 3. Files to MERGE

### 3.1 Duplicate `apply_chart` Functions

| Source | Target | Action |
|---|---|---|
| `ui/helpers.py:49-123` (`apply_chart`) | `ui/components/charts.py:5-69` | Delete from `ui/helpers.py`. Update 2 imports in `views/expense.py:55` and `views/pnl.py:55`. |

### 3.2 Duplicate Import Blocks in Views

| Source | Target | Action |
|---|---|---|
| 14 view files with 50-line import blocks | `views/shared.py` | Replace with `from views.shared import *` in: `views/executive.py`, `views/overview.py`, `views/cockpit.py`, `views/locations.py`, `views/trends.py`, `views/targets.py`, `views/reports.py`, `views/internal_audit.py`, `views/expense.py`, `views/pnl.py`, `views/advisor.py`, `views/advisor_mom.py`, `views/leakage.py`, `views/margin.py` |

### 3.3 Inline KPI Card Implementations

| Source | Target | Action |
|---|---|---|
| `views/dashboard_common.py:56-99` (`render_kpi_card`) | `ui/components/metrics.py` (`KPIGrid`/`MetricCard`) | Replace calls with component library |
| `views/labour.py:209-232` (`_kpi_card`) | `ui/components/metrics.py` | Replace with `MetricCard` |
| `views/discount.py:312-336` (`_kpi`) | `ui/components/metrics.py` | Replace with `MetricCard` |

### 3.4 Duplicate Formatters

| Source | Target | Action |
|---|---|---|
| `revenue_leakage_v31.py:33` (`_fmt_inr`) | `ui/formatters.py:26` (`fmt_inr`) | Import from canonical source |
| `services/export_service.py:114` (`_fmt_inr`) | `ui/formatters.py:26` | Import from canonical source |
| `services/export_service.py:134` (`_fmt_pct`) | `ui/formatters.py:114` (`fmt_pct`) | Import from canonical source |

### 3.5 Duplicate Constants

| Source | Target | Action |
|---|---|---|
| `pnl_report.py:45` (`ADV_COL`) | `utils/constants.py:3` | Import from canonical source |
| `pnl_report.py:27` (`MONTH_ORDER`) | `utils/constants.py` | Import from canonical source |
| `exp_report.py` (`MONTH_ORDER`) | `utils/constants.py` | Import from canonical source |

### 3.6 Standalone Modules to Consolidate

| Module | Lines | Current Import | Target |
|---|---|---|---|
| `exp_report.py` | 2,340 | `views/expense.py:61` | Refactor into `views/finance/expense.py` |
| `pnl_report.py` | 1,537 | `views/pnl.py:59` | Refactor into `views/finance/pnl.py` |
| `revenue_leakage_v31.py` | 951 | `views/internal_audit.py:429` | Refactor into `views/audit/leakage.py` |

---

## 4. Files to RENAME

### 4.1 View Module Renaming (for 6-dashboard structure)

| Current Path | New Path | Rationale |
|---|---|---|
| `views/cockpit.py` | `views/operations/cockpit.py` | D1: Operations Dashboard |
| `views/overview.py` | `views/operations/overview.py` | D1: Operations Dashboard |
| `views/system_health.py` | `views/operations/system_health.py` | D1: Operations Dashboard |
| `views/labour.py` | `views/revenue/labour.py` | D2: Revenue Dashboard |
| `views/parts_executive.py` | `views/revenue/parts_executive.py` | D2: Revenue Dashboard |
| `views/parts_detail.py` | `views/revenue/parts_detail.py` | D2: Revenue Dashboard |
| `views/margin.py` | `views/revenue/margin.py` | D2: Revenue Dashboard |
| `views/sales_mix.py` | `views/revenue/sales_mix.py` | D2: Revenue Dashboard |
| `views/discount.py` | `views/revenue/discount.py` | D2: Revenue Dashboard |
| `views/leakage.py` | `views/revenue/leakage.py` | D2: Revenue Dashboard |
| `views/advisor.py` | `views/people/advisor.py` | D3: People Dashboard |
| `views/advisor_mom.py` | `views/people/advisor_mom.py` | D3: People Dashboard |
| `views/locations.py` | `views/performance/locations.py` | D4: Performance Dashboard |
| `views/trends.py` | `views/performance/trends.py` | D4: Performance Dashboard |
| `views/targets.py` | `views/performance/targets.py` | D4: Performance Dashboard |
| `views/expense.py` | `views/finance/expense.py` | D5: Finance Dashboard |
| `views/pnl.py` | `views/finance/pnl.py` | D5: Finance Dashboard |
| `views/executive.py` | `views/finance/executive.py` | D5: Finance Dashboard |
| `views/internal_audit.py` | `views/audit/internal_audit.py` | D6: Audit Dashboard |
| `views/audit_intelligence.py` | `views/audit/audit_intelligence.py` | D6: Audit Dashboard |
| `views/reports.py` | `views/audit/reports.py` | D6: Audit Dashboard |

### 4.2 Service Module Renaming

| Current Path | New Path | Rationale |
|---|---|---|
| `services/ai_service.py` | DELETE | Superseded by `services/ai/` |
| `services/logging_service.py` | `services/logging.py` | Consistent naming |
| `services/executive_alert_engine.py` | `services/alert_engine.py` | Shorter, consistent |
| `services/benchmark_provider.py` | `services/benchmarks.py` | Shorter, consistent |

### 4.3 Config Module Renaming

| Current Path | New Path | Rationale |
|---|---|---|
| `config/settings.py` | `config/settings.py` | KEEP — no change |
| `config/paths.py` | `config/paths.py` | KEEP — no change |
| `config/environment.py` | `config/environment.py` | KEEP — no change |

---

## 5. Files to KEEP Unchanged

### 5.1 Core Business Logic (DO NOT TOUCH)

| File | Lines | Reason |
|---|---|---|
| `utils/calculations/common.py` | 78 | Pure math functions |
| `utils/calculations/fact_metrics.py` | 187 | Base metric extractors |
| `utils/calculations/revenue.py` | 65 | Revenue calculations |
| `utils/calculations/margin.py` | 95 | Margin calculations |
| `utils/calculations/discount.py` | 130 | Discount calculations |
| `utils/calculations/leakage.py` | 115 | Leakage calculations |
| `utils/cleaning.py` | 110 | Data cleaning pipeline |
| `utils/constants.py` | 97 | Global constants |
| `config/settings.py` | 19 | Business thresholds |
| `services/financial_service.py` | 70 | Financial facade |

### 5.2 Infrastructure (KEEP, MAY EXTEND)

| File | Lines | Reason |
|---|---|---|
| `services/state_manager.py` | 279 | Session state — extend for new namespaces |
| `services/aggregation_cache.py` | 208 | Caching — keep as-is |
| `services/error_handler.py` | 76 | Error handling — keep as-is |
| `services/logger.py` | 47 | Logging — keep as-is |
| `services/audit_service.py` | 233 | Audit data — keep as-is |
| `utils/loaders.py` | 213 | Data loading — keep as-is |
| `utils/filters.py` | 97 | Filter functions — keep as-is |
| `utils/aggregations.py` | 97 | Aggregation wrappers — keep as-is |
| `utils/profiler.py` | 73 | Profiler — keep as-is |

### 5.3 UI Foundation (KEEP, MAY EXTEND)

| File | Lines | Reason |
|---|---|---|
| `ui/design_tokens.py` | 167 | Design system — keep as-is |
| `ui/formatters.py` | 129 | Formatters — keep as-is |
| `ui/components/core.py` | 160 | Header/Footer — keep as-is |
| `ui/components/charts.py` | 86 | ChartCard — keep as-is |
| `ui/components/metrics.py` | 95 | KPIGrid/MetricCard — keep as-is |
| `ui/components/tables.py` | 75 | TableCard — keep as-is |
| `ui/components/filters.py` | 65 | FilterToolbar — keep as-is |
| `ui/traffic.py` | 71 | Traffic badges — keep as-is |
| `ui/executive_tooltip.py` | 160 | Tooltips — keep as-is |
| `static/style.css` | — | CSS — keep as-is |

### 5.4 AI Module (KEEP, EXTEND)

| File | Lines | Reason |
|---|---|---|
| `services/ai/__init__.py` | 42 | Public API — keep |
| `services/ai/models.py` | 124 | Data models — keep |
| `services/ai/context_builder.py` | 288 | Context builder — keep |
| `services/ai/prompt_builder.py` | 77 | Prompt builder — keep |
| `services/ai/report_generator.py` | 278 | Report generator — keep |
| `services/ai/gemini_provider.py` | 48 | Gemini provider — keep |
| `services/ai/templates.py` | 116 | Report templates — keep |

### 5.5 Export Module (KEEP, EXTEND)

| File | Lines | Reason |
|---|---|---|
| `services/export_service.py` | 561 | Export engine — keep, extend for Report Center |
| `ui/export_buttons.py` | 158 | Export buttons — keep as-is |

### 5.6 Tests (KEEP)

| File | Lines | Reason |
|---|---|---|
| `tests/__init__.py` | 0 | Package marker |
| `tests/test_aggregations.py` | 65 | Aggregation tests |
| `tests/test_calculations.py` | 95 | Calculation tests |
| `tests/test_filters.py` | 65 | Filter tests |
| `tests/test_pages.py` | 45 | Page load tests |

### 5.7 Config (KEEP)

| File | Lines | Reason |
|---|---|---|
| `.streamlit/config.toml` | 2 | Streamlit config |
| `.gitignore` | — | Git ignore rules |
| `requirements.txt` | — | Dependencies |
| `requirements-dev.txt` | — | Dev dependencies |
| `run.bat` | 3 | Launch script |
| `README.md` | — | Documentation |
| `INSTALL.md` | — | Installation guide |
| `LICENSE` | — | License |

---

## 6. Shared Components to Create

### 6.1 New Shared View Infrastructure

| Component | Location | Purpose |
|---|---|---|
| `views/__init__.py` | `views/__init__.py` | Package init with dashboard registry |
| `views/shared.py` | `views/shared.py` | KEEP — extend with new re-exports |
| `views/dashboard_common.py` | `views/dashboard_common.py` | KEEP — extend with shared dashboard utilities |
| `views/base.py` | `views/base.py` | **NEW** — Base dashboard class with common render pattern |
| `views/registry.py` | `views/registry.py` | **NEW** — Dashboard registration and discovery |

### 6.2 New Shared View Components

| Component | Location | Purpose |
|---|---|---|
| `views/components/__init__.py` | `views/components/__init__.py` | **NEW** — View-specific shared components |
| `views/components/kpi_row.py` | `views/components/kpi_row.py` | **NEW** — Standard KPI row layout |
| `views/components/section_header.py` | `views/components/section_header.py` | **NEW** — Dashboard section header |
| `views/components/comparison_panel.py` | `views/components/comparison_panel.py` | **NEW** — CP vs PP comparison panel |
| `views/components/data_table.py` | `views/components/data_table.py` | **NEW** — Standardized data table with formatting |
| `views/components/chart_grid.py` | `views/components/chart_grid.py` | **NEW** — Grid layout for multiple charts |
| `views/components/insight_card.py` | `views/components/insight_card.py` | **NEW** — AI-generated insight card |
| `views/components/export_section.py` | `views/components/export_section.py` | **NEW** — Standardized export section |

### 6.3 New Dashboard Module Structure

| Dashboard | Package | Modules |
|---|---|---|
| D1: Operations | `views/operations/` | `__init__.py`, `cockpit.py`, `overview.py`, `system_health.py` |
| D2: Revenue | `views/revenue/` | `__init__.py`, `labour.py`, `parts_executive.py`, `parts_detail.py`, `margin.py`, `sales_mix.py`, `discount.py`, `leakage.py` |
| D3: People | `views/people/` | `__init__.py`, `advisor.py`, `advisor_mom.py` |
| D4: Performance | `views/performance/` | `__init__.py`, `locations.py`, `trends.py`, `targets.py` |
| D5: Finance | `views/finance/` | `__init__.py`, `expense.py`, `pnl.py`, `executive.py` |
| D6: Audit | `views/audit/` | `__init__.py`, `internal_audit.py`, `audit_intelligence.py`, `reports.py` |

---

## 7. Common KPI Engine to Create

### 7.1 Current State

KPI rendering is inconsistent:
- `views/dashboard_common.py:56-99` — `render_kpi_card()` returns HTML string
- `views/labour.py:209-232` — `_kpi_card()` local function
- `views/discount.py:312-336` — `_kpi()` with invert param
- `ui/components/metrics.py` — `KPIGrid`/`MetricCard` (canonical, underused)

### 7.2 Target KPI Engine

| Component | Location | Purpose |
|---|---|---|
| `views/components/kpi_engine.py` | `views/components/kpi_engine.py` | **NEW** — Centralized KPI computation and rendering |

**KPI Engine API:**

```python
class KPIEngine:
    """Centralized KPI computation and rendering engine."""
    
    def compute_kpis(cp_df, pp_df, metrics, group_col=None):
        """Compute KPI values with growth from CP/PP DataFrames."""
        # Returns: Dict[str, KPIValue]
    
    def render_kpi_row(kpis, columns=4):
        """Render a row of KPI cards using MetricCard/KPIGrid."""
        # Uses ui.components.metrics.KPIGrid
    
    def render_kpi_with_sparkline(kpi, trend_data):
        """Render KPI card with mini trend chart."""
        # Uses ChartCard for sparkline
    
    def render_kpi_comparison(kpi_cp, kpi_pp, label):
        """Render CP vs PP comparison KPI."""
        # Shows value, growth %, traffic light
```

### 7.3 KPI Standardization Points

| KPI Category | Current Location | Target |
|---|---|---|
| Revenue KPIs (Labour, Parts, Total) | `views/overview.py`, `views/executive.py` | `KPIEngine.compute_kpis()` |
| Margin KPIs | `views/margin.py` | `KPIEngine.compute_kpis()` |
| Discount KPIs | `views/discount.py` | `KPIEngine.compute_kpis()` |
| Leakage KPIs | `views/leakage.py` | `KPIEngine.compute_kpis()` |
| Job Card KPIs | `views/labour.py`, `views/parts_executive.py` | `KPIEngine.compute_kpis()` |
| Target Achievement KPIs | `views/targets.py` | `KPIEngine.compute_kpis()` |
| Expense KPIs | `views/expense.py` | `KPIEngine.compute_kpis()` |
| Audit KPIs | `views/internal_audit.py` | `KPIEngine.compute_kpis()` |

---

## 8. Common Chart Engine to Create

### 8.1 Current State

Chart rendering is inconsistent:
- 20 raw `st.plotly_chart` calls bypass `ChartCard`
- `ui/helpers.py:49-123` and `ui/components/charts.py:5-69` — duplicate `apply_chart`
- Some views use `ChartCard`, others use raw Plotly

### 8.2 Target Chart Engine

| Component | Location | Purpose |
|---|---|---|
| `views/components/chart_engine.py` | `views/components/chart_engine.py` | **NEW** — Centralized chart creation and rendering |

**Chart Engine API:**

```python
class ChartEngine:
    """Centralized chart creation and rendering engine."""
    
    def bar_chart(df, x, y, color=None, title="", size="medium", **kwargs):
        """Create standardized bar chart."""
        # Returns: go.Figure with apply_chart applied
    
    def line_chart(df, x, y, color=None, title="", size="medium", **kwargs):
        """Create standardized line chart."""
        # Returns: go.Figure with apply_chart applied
    
    def group_bar_chart(df, x, y_group, y_cp, y_pp, title="", size="medium"):
        """Create CP vs PP grouped bar chart."""
        # Standard comparison pattern
    
    def waterfall_chart(df, x, y, title="", size="medium"):
        """Create waterfall chart for variance analysis."""
        # Used in P&L, margin analysis
    
    def heatmap_chart(df, x, y, z, title="", size="medium"):
        """Create heatmap for cross-dimensional analysis."""
        # Used in leakage, discount heatmaps
    
    def render(fig, title="", height=360, key=None):
        """Render chart in a ChartCard wrapper."""
        # Uses ChartCard from ui.components.charts
```

### 8.3 Chart Standardization Points

| Chart Type | Current Location | Target |
|---|---|---|
| Revenue trend bars | `views/overview.py`, `views/executive.py` | `ChartEngine.group_bar_chart()` |
| Location comparison | `views/locations.py` | `ChartEngine.bar_chart()` |
| Advisor scatter | `views/advisor.py` | `ChartEngine.scatter_chart()` |
| Trend lines | `views/trends.py` | `ChartEngine.line_chart()` |
| Discount heatmap | `views/discount.py` | `ChartEngine.heatmap_chart()` |
| Leakage heatmap | `views/leakage.py` | `ChartEngine.heatmap_chart()` |
| Target achievement | `views/targets.py` | `ChartEngine.bar_chart()` |
| Monthly evolution | `views/labour.py`, `views/parts_executive.py` | `ChartEngine.line_chart()` |

---

## 9. Navigation Changes

### 9.1 Current Navigation

```python
# app.py:491 — sidebar_navigation()
with st.sidebar:
    with st.expander("📊 OVERVIEW"):
        nav_btn("Cockpit", "Cockpit")
        nav_btn("Overview", "Overview")
        nav_btn("Executive", "Executive")
    with st.expander("💰 REVENUE"):
        nav_btn("Labour", "Labour")
        nav_btn("Parts Executive", "Parts Executive")
        # ... 7 more items
    with st.expander("👥 PEOPLE"):
        nav_btn("Advisors", "Advisors")
        nav_btn("Advisor MoM", "Advisor MoM")
    with st.expander("📈 PERFORMANCE"):
        nav_btn("Locations", "Locations")
        nav_btn("Trends", "Trends")
        nav_btn("Targets", "Targets")
    with st.expander("🏦 FINANCE"):
        nav_btn("Expense Analysis", "Expense Analysis")
        nav_btn("Profit & Loss", "Profit & Loss")
    with st.expander("🛠 ADMIN"):
        nav_btn("Reports", "Reports")
        nav_btn("Internal Audit", "Internal Audit")
        nav_btn("Audit Intelligence", "Audit Intelligence")
    # System Health hidden behind query param
```

### 9.2 Target Navigation

```python
# New sidebar structure for 6-dashboard architecture
with st.sidebar:
    # Dashboard selector (top-level)
    dashboard = st.radio(
        "Dashboard",
        ["Operations", "Revenue", "People", "Performance", "Finance", "Audit"],
        label_visibility="collapsed"
    )
    
    # Sub-navigation per dashboard
    if dashboard == "Operations":
        page = st.radio("Section", ["Cockpit", "Overview", "System Health"])
    elif dashboard == "Revenue":
        page = st.radio("Section", [
            "Labour", "Parts Executive", "Parts Detail",
            "Margin", "Sales Mix", "Discounts", "Leakage Center"
        ])
    elif dashboard == "People":
        page = st.radio("Section", ["Advisors", "Advisor MoM"])
    elif dashboard == "Performance":
        page = st.radio("Section", ["Locations", "Trends", "Targets"])
    elif dashboard == "Finance":
        page = st.radio("Section", ["Expense Analysis", "Profit & Loss", "Executive"])
    elif dashboard == "Audit":
        page = st.radio("Section", ["Internal Audit", "Audit Intelligence", "Reports"])
```

### 9.3 Navigation Changes Summary

| Change | Current | Target |
|---|---|---|
| Top-level selector | Expander buttons | Radio button (dashboard) |
| Sub-navigation | Flat list in expanders | Radio button (section) |
| Active state | `st.button` with `type="primary"` | Radio button auto-selection |
| Session key | `current_page` | `current_dashboard` + `current_page` |
| URL scheme | `?page=Labour` | `?dashboard=Revenue&page=Labour` |

---

## 10. Sidebar Changes

### 10.1 Current Sidebar

| Element | Location | Purpose |
|---|---|---|
| Navigation expanders | `app.py:491-545` | Page selection |
| Client selector | `app.py:200` | Multi-client support |
| Refresh button | `app.py:200` | Data refresh |
| Version display | `app.py:200` | Version info |

### 10.2 Target Sidebar

| Element | Location | Purpose |
|---|---|---|
| Dashboard selector | `app.py:491` (rewrite) | Top-level dashboard selection |
| Section radio | `app.py:491` (rewrite) | Sub-page navigation within dashboard |
| Client selector | `app.py:200` (keep) | Multi-client support |
| Refresh button | `app.py:200` (keep) | Data refresh |
| Quick filters | `app.py:491` (new) | Dashboard-specific quick filters |
| Dashboard summary | `app.py:491` (new) | Mini KPI summary for current dashboard |
| Version display | `app.py:200` (keep) | Version info |

### 10.3 Sidebar State Management

| Key | Current | Target |
|---|---|---|
| `current_page` | Single page string | `current_dashboard` + `current_page` |
| `filter_location` | Global filter | Global filter (keep) |
| `filter_mp_pb` | Global filter | Global filter (keep) |
| `month_preset` | Global filter | Global filter (keep) |
| `comparison_mode_radio` | Global filter | Global filter (keep) |
| `filter_svc_type` | Page-level filter | Dashboard-scoped filter |
| `filter_advisor` | Page-level filter | Dashboard-scoped filter |

---

## 11. Router Changes

### 11.1 Current Router

```python
# app.py:548-738 — render_page_router()
def render_page_router(df_filtered_full, df_filtered_cp, df_filtered, pairs, alerts, 
                       comparison_mode, selected_months, targets_df, client_config, 
                       exp_df_filtered_cp=None):
    page = st.session_state.get("current_page", "Cockpit")
    
    if page == "Cockpit":
        from views.cockpit import render
        render(df_filtered_full, pairs, alerts, comparison_mode, selected_months)
    elif page == "Overview":
        from views.overview import render
        safe_render(render, df_filtered_full, pairs, alerts, comparison_mode, selected_months)
    elif page == "Labour":
        from views.labour import render
        safe_render(render, df_filtered_full, pairs, comparison_mode, selected_months)
    # ... 16 more elif branches
```

### 11.2 Target Router

```python
# New router with dashboard grouping
DASHBOARD_REGISTRY = {
    "Operations": {
        "Cockpit": {"module": "views.operations.cockpit", "args": ["full", "pairs", "alerts"]},
        "Overview": {"module": "views.operations.overview", "args": ["full", "pairs", "alerts"]},
        "System Health": {"module": "views.operations.system_health", "args": ["full"]},
    },
    "Revenue": {
        "Labour": {"module": "views.revenue.labour", "args": ["full", "pairs"]},
        "Parts Executive": {"module": "views.revenue.parts_executive", "args": ["full", "pairs"]},
        "Parts Detail": {"module": "views.revenue.parts_detail", "args": ["full", "pairs"]},
        "Margin": {"module": "views.revenue.margin", "args": ["cp", "pairs"]},
        "Sales Mix": {"module": "views.revenue.sales_mix", "args": ["cp", "pairs"]},
        "Discounts": {"module": "views.revenue.discount", "args": ["cp", "pairs"]},
        "Leakage Center": {"module": "views.revenue.leakage", "args": ["full", "pairs"]},
    },
    "People": {
        "Advisors": {"module": "views.people.advisor", "args": ["cp", "pairs"]},
        "Advisor MoM": {"module": "views.people.advisor_mom", "args": ["full", "pairs"]},
    },
    "Performance": {
        "Locations": {"module": "views.performance.locations", "args": ["cp", "pairs"]},
        "Trends": {"module": "views.performance.trends", "args": ["full", "pairs"]},
        "Targets": {"module": "views.performance.targets", "args": ["cp", "targets_df"]},
    },
    "Finance": {
        "Expense Analysis": {"module": "views.finance.expense", "args": ["exp_cp", "selected_months"]},
        "Profit & Loss": {"module": "views.finance.pnl", "args": ["cp", "exp_cp", "selected_months"]},
        "Executive": {"module": "views.finance.executive", "args": ["full", "pairs"]},
    },
    "Audit": {
        "Internal Audit": {"module": "views.audit.internal_audit", "args": ["full", "pairs", "alerts"]},
        "Audit Intelligence": {"module": "views.audit.audit_intelligence", "args": ["full", "pairs", "alerts"]},
        "Reports": {"module": "views.audit.reports", "args": ["cp", "pairs"]},
    },
}

def render_page_router(data):
    dashboard = st.session_state.get("current_dashboard", "Operations")
    page = st.session_state.get("current_page", "Cockpit")
    
    config = DASHBOARD_REGISTRY.get(dashboard, {}).get(page)
    if config:
        module = importlib.import_module(config["module"])
        args = resolve_args(config["args"], data)
        safe_render(module.render, *args)
    else:
        st.error(f"Page '{page}' not found in dashboard '{dashboard}'.")
```

### 11.3 Router Changes Summary

| Change | Current | Target |
|---|---|---|
| Dispatch mechanism | `if/elif` chain (19 branches) | Registry dict + dynamic import |
| Page resolution | `current_page` only | `current_dashboard` + `current_page` |
| Argument passing | Positional args per branch | Config-driven arg resolution |
| Error handling | `st.error()` | `st.error()` + logging |
| Extensibility | Add new `elif` branch | Add to registry dict |

---

## 12. Export Framework Changes

### 12.1 Current Export

| Component | Location | Purpose |
|---|---|---|
| `services/export_service.py` | 561 lines | `ExportMeta`, `export_csv`, `export_excel`, `export_pdf` |
| `ui/export_buttons.py` | 158 lines | `render_export_buttons()` |

### 12.2 Target Export Framework

| Component | Location | Purpose |
|---|---|---|
| `services/export_service.py` | KEEP | Core export engine |
| `ui/export_buttons.py` | KEEP | Export button components |
| `services/report_center.py` | **NEW** | Report Center integration |
| `services/presentation_manager.py` | **NEW** | Presentation Manager integration |

### 12.3 Export Integration Points

| Integration | Current | Target |
|---|---|---|
| Per-page export | `render_export_buttons(df, meta)` in each view | Standardized in `views/components/export_section.py` |
| Report Center | Not implemented | `services/report_center.py` — scheduled report generation |
| Presentation Manager | Not implemented | `services/presentation_manager.py` — PowerPoint generation |
| PDF templates | Basic reportlab layout | Branded templates with charts |

---

## 13. AI Module Integration Points

### 13.1 Current AI Module

| Component | Location | Purpose |
|---|---|---|
| `services/ai/__init__.py` | Public API | Exports `build_context`, `build_prompt`, `generate_report` |
| `services/ai/context_builder.py` | 288 lines | Builds `ReportContext` from DataFrames |
| `services/ai/prompt_builder.py` | 77 lines | Builds LLM prompt from context |
| `services/ai/report_generator.py` | 278 lines | Pipeline: context → prompt → LLM → Markdown |
| `services/ai/models.py` | 124 lines | Data models (`ReportContext`, `GeneratedReport`, etc.) |
| `services/ai/templates.py` | 116 lines | 9 canonical `ReportSection` definitions |
| `services/ai/gemini_provider.py` | 48 lines | Gemini API integration |

### 13.2 AI Integration Points

| Dashboard | Integration Point | Purpose |
|---|---|---|
| D1: Operations | `views/operations/cockpit.py` | AI-generated operational summary |
| D2: Revenue | `views/revenue/discount.py` | AI-generated discount insights |
| D2: Revenue | `views/revenue/leakage.py` | AI-generated leakage analysis |
| D3: People | `views/people/advisor.py` | AI-generated advisor performance insights |
| D4: Performance | `views/performance/trends.py` | AI-generated trend analysis |
| D5: Finance | `views/finance/executive.py` | AI-generated financial summary |
| D6: Audit | `views/audit/audit_intelligence.py` | AI-generated audit intelligence report |

### 13.3 AI Module Wiring

```python
# Target integration pattern for each dashboard
from services.ai import build_context, generate_report

def render(df_cp, df_pp, pairs, ...):
    # 1. Build context
    context = build_context(df_cp, df_pp, dashboard="revenue", metrics=[...])
    
    # 2. Generate report (with fallback)
    report = generate_report(df_cp, df_pp, context=context, provider="auto")
    
    # 3. Render insight cards
    if report.success:
        for section in report.sections:
            render_insight_card(section.title, section.content)
    else:
        render_insight_card("AI Analysis", report.fallback_content)
```

---

## 14. Report Center Integration

### 14.1 Current State

| Component | Location | Purpose |
|---|---|---|
| `views/reports.py` | 317 lines | Manual report generation page |
| `services/export_service.py` | 561 lines | CSV/Excel/PDF export |

### 14.2 Target Report Center

| Component | Location | Purpose |
|---|---|---|
| `services/report_center.py` | **NEW** | Centralized report scheduling and generation |
| `services/report_scheduler.py` | **NEW** | Cron-like report scheduling |
| `services/report_templates.py` | **NEW** | Report template definitions |
| `views/audit/reports.py` | REFACTOR | Report Center UI |

### 14.3 Report Center API

```python
class ReportCenter:
    """Centralized report scheduling and generation."""
    
    def schedule_report(report_type, schedule, recipients, config):
        """Schedule a recurring report."""
    
    def generate_report(report_type, config, format="pdf"):
        """Generate a single report on demand."""
    
    def list_reports(filters=None):
        """List available report templates."""
    
    def get_report_history(report_id=None):
        """Get generation history."""
    
    def export_report(report_id, format="pdf"):
        """Export a generated report."""
```

### 14.4 Report Types

| Report Type | Dashboard | Format | Schedule |
|---|---|---|---|
| Operations Summary | D1 | PDF | Weekly |
| Revenue Analysis | D2 | PDF/Excel | Monthly |
| People Performance | D3 | PDF | Monthly |
| Performance Trends | D4 | PDF | Quarterly |
| Financial Summary | D5 | PDF/Excel | Monthly |
| Audit Report | D6 | PDF | Monthly |
| Discount Alert | D2 | PDF | On-demand |
| Leakage Alert | D2 | PDF | On-demand |

---

## 15. Presentation Manager Integration

### 15.1 Current State

Not implemented. Currently exports are limited to CSV/Excel/PDF data tables.

### 15.2 Target Presentation Manager

| Component | Location | Purpose |
|---|---|---|
| `services/presentation_manager.py` | **NEW** | PowerPoint generation engine |
| `services/presentation_templates.py` | **NEW** | Slide template definitions |
| `services/chart_export.py` | **NEW** | Chart-to-image export for slides |

### 15.3 Presentation Manager API

```python
class PresentationManager:
    """PowerPoint presentation generation engine."""
    
    def create_presentation(title, subtitle, date):
        """Create a new presentation."""
    
    def add_title_slide(pres, title, subtitle):
        """Add title slide."""
    
    def add_kpi_slide(pres, kpis, title):
        """Add KPI summary slide with cards."""
    
    def add_chart_slide(pres, fig, title, notes=""):
        """Add chart slide with embedded image."""
    
    def add_table_slide(pres, df, title, max_rows=15):
        """Add data table slide."""
    
    def add_insight_slide(pres, insights, title):
        """Add AI-generated insight slide."""
    
    def add_section_divider(pres, section_name):
        """Add section divider slide."""
    
    def export(pres, filename):
        """Export to .pptx file."""
```

### 15.4 Presentation Integration Points

| Dashboard | Slide Content | Source |
|---|---|---|
| D1: Operations | Executive summary, KPIs, alerts | `views/operations/cockpit.py` |
| D2: Revenue | Revenue trends, margin analysis, leakage | `views/revenue/*.py` |
| D3: People | Advisor rankings, performance scatter | `views/people/*.py` |
| D4: Performance | Location comparison, trends, targets | `views/performance/*.py` |
| D5: Finance | P&L summary, expense breakdown | `views/finance/*.py` |
| D6: Audit | Audit findings, recommendations | `views/audit/*.py` |

---

## 16. Role/Profile Manager Integration

### 16.1 Current State

Not implemented. All users see all dashboards with full access.

### 16.2 Target Role/Profile Manager

| Component | Location | Purpose |
|---|---|---|
| `services/auth.py` | **NEW** | Authentication service |
| `services/role_manager.py` | **NEW** | Role-based access control |
| `services/profile_manager.py` | **NEW** | User profile management |
| `config/roles.py` | **NEW** | Role definitions |

### 16.3 Role Definitions

| Role | Access | Dashboards |
|---|---|---|
| `admin` | Full access | All dashboards + admin |
| `manager` | Manager access | D1, D2, D3, D4, D5 |
| `analyst` | Analyst access | D1, D2, D3, D4 |
| `auditor` | Audit access | D1, D6 |
| `viewer` | Read-only | D1 (Cockpit only) |

### 16.4 Profile Manager API

```python
class ProfileManager:
    """User profile and preference management."""
    
    def get_user_profile(user_id):
        """Get user profile with preferences."""
    
    def update_preferences(user_id, preferences):
        """Update user preferences (default dashboard, filters, etc.)"""
    
    def get_default_dashboard(user_id):
        """Get user's default dashboard."""
    
    def get_saved_filters(user_id, dashboard):
        """Get saved filter presets for a dashboard."""
    
    def save_filter_preset(user_id, dashboard, name, filters):
        """Save a filter preset."""
```

---

## 17. Dashboard Designer Integration

### 17.1 Current State

Not implemented. Dashboard layout is hardcoded in view modules.

### 17.2 Target Dashboard Designer

| Component | Location | Purpose |
|---|---|---|
| `services/dashboard_designer.py` | **NEW** | Dashboard layout engine |
| `services/widget_registry.py` | **NEW** | Widget type definitions |
| `services/layout_engine.py` | **NEW** | Layout computation |
| `config/dashboard_templates.json` | **NEW** | Dashboard layout templates |

### 17.3 Widget Types

| Widget Type | Component | Purpose |
|---|---|---|
| `kpi_card` | `MetricCard` | Single KPI with growth |
| `kpi_grid` | `KPIGrid` | Grid of KPI cards |
| `bar_chart` | `ChartCard` | Bar chart |
| `line_chart` | `ChartCard` | Line chart |
| `heatmap` | `ChartCard` | Heatmap |
| `data_table` | `TableCard` | Data table |
| `insight_card` | `AlertBanner` | AI insight |
| `export_section` | `render_export_buttons` | Export buttons |

### 17.4 Dashboard Template Structure

```json
{
  "dashboard": "Revenue",
  "layout": "grid",
  "columns": 2,
  "sections": [
    {
      "title": "Key Metrics",
      "widgets": [
        {"type": "kpi_grid", "metrics": ["labour_revenue", "parts_revenue", "total_revenue", "margin"]},
        {"type": "kpi_grid", "metrics": ["job_cards", "avg_per_jc", "labour_per_100_parts"]}
      ]
    },
    {
      "title": "Revenue Analysis",
      "widgets": [
        {"type": "bar_chart", "data": "monthly_revenue", "group": "service_type"},
        {"type": "line_chart", "data": "revenue_trend", "compare": true}
      ]
    },
    {
      "title": "Detailed Analysis",
      "widgets": [
        {"type": "data_table", "data": "location_breakdown", "sortable": true},
        {"type": "heatmap", "data": "discount_heatmap"}
      ]
    }
  ]
}
```

---

## 18. Database/Config Changes

### 18.1 Config Changes

| File | Change | Purpose |
|---|---|---|
| `config/settings.py` | ADD | Dashboard registry config |
| `config/settings.py` | ADD | Role definitions |
| `config/settings.py` | ADD | Report schedule defaults |
| `config/paths.py` | ADD | Report output directory |
| `config/paths.py` | ADD | Template directory |
| `config/roles.py` | **NEW** | Role definitions |
| `config/dashboard_templates.json` | **NEW** | Dashboard layout templates |

### 18.2 Session State Changes

| Key | Current | Target |
|---|---|---|
| `current_page` | Single page string | `current_dashboard` + `current_page` |
| `user_role` | Not present | User role string |
| `user_id` | Not present | User identifier |
| `saved_filters` | Not present | Dict of saved filter presets |
| `report_schedule` | Not present | Report schedule config |

### 18.3 State Registry Changes

| Namespace | Current | Target |
|---|---|---|
| `lab_` | Labour view state | KEEP — extend for D2 |
| `parts_` | Parts view state | KEEP — extend for D2 |
| `cockpit_` | Cockpit view state | KEEP — extend for D1 |
| `ops_` | Not present | **NEW** — Operations dashboard state |
| `rev_` | Not present | **NEW** — Revenue dashboard state |
| `people_` | Not present | **NEW** — People dashboard state |
| `perf_` | Not present | **NEW** — Performance dashboard state |
| `fin_` | Not present | **NEW** — Finance dashboard state |
| `audit_` | Not present | **NEW** — Audit dashboard state |

---

## 19. Estimated Implementation Phases

### Phase 1: Cleanup (Week 1)

| Task | Effort | Risk | Dependencies |
|---|---|---|---|
| Delete 79 dead/test/artifact files | 2 hrs | Low | None |
| Move standalone modules to archive | 1 hr | Low | None |
| Fix undefined `kpi()` calls | 30 min | Low | None |
| Verify credentials untracked | 15 min | Low | None |
| Add `test_venv/` to `.gitignore` | 5 min | Low | None |
| Replace 14 view import blocks | 4 hrs | Low | None |
| Delete duplicate `apply_chart` | 30 min | Low | None |
| Add `__all__` to 9 modules | 1 hr | Low | None |
| **Phase 1 Total** | **~9 hrs** | | |

### Phase 2: Shared Components (Week 2)

| Task | Effort | Risk | Dependencies |
|---|---|---|---|
| Create `views/components/` package | 2 hrs | Low | Phase 1 |
| Create `KPIEngine` | 4 hrs | Medium | Phase 1 |
| Create `ChartEngine` | 4 hrs | Medium | Phase 1 |
| Create `views/base.py` | 2 hrs | Medium | Phase 1 |
| Create `views/registry.py` | 2 hrs | Low | Phase 1 |
| Standardize KPI rendering | 4 hrs | Medium | KPIEngine |
| Standardize chart rendering | 4 hrs | Medium | ChartEngine |
| **Phase 2 Total** | **~22 hrs** | | |

### Phase 3: Dashboard Restructuring (Week 3-4)

| Task | Effort | Risk | Dependencies |
|---|---|---|---|
| Create `views/operations/` package | 2 hrs | Low | Phase 2 |
| Create `views/revenue/` package | 2 hrs | Low | Phase 2 |
| Create `views/people/` package | 2 hrs | Low | Phase 2 |
| Create `views/performance/` package | 2 hrs | Low | Phase 2 |
| Create `views/finance/` package | 2 hrs | Low | Phase 2 |
| Create `views/audit/` package | 2 hrs | Low | Phase 2 |
| Refactor `app.py` router | 6 hrs | High | Phase 2 |
| Refactor sidebar navigation | 4 hrs | High | Phase 2 |
| Refactor filter system | 4 hrs | High | Phase 2 |
| Migrate 19 views to new structure | 16 hrs | High | Phase 2 |
| Update `views/shared.py` | 2 hrs | Low | Phase 3 |
| Update `views/dashboard_common.py` | 2 hrs | Low | Phase 3 |
| **Phase 3 Total** | **~46 hrs** | | |

### Phase 4: Integration Points (Week 5-6)

| Task | Effort | Risk | Dependencies |
|---|---|---|---|
| Create `services/report_center.py` | 8 hrs | Medium | Phase 3 |
| Create `services/presentation_manager.py` | 12 hrs | Medium | Phase 3 |
| Create `services/chart_export.py` | 4 hrs | Medium | Phase 3 |
| Wire AI module to dashboards | 8 hrs | Medium | Phase 3 |
| Create `services/auth.py` | 8 hrs | Medium | Phase 3 |
| Create `services/role_manager.py` | 6 hrs | Medium | Phase 3 |
| Create `services/profile_manager.py` | 4 hrs | Low | Phase 3 |
| Create `config/roles.py` | 2 hrs | Low | Phase 3 |
| Create `config/dashboard_templates.json` | 4 hrs | Low | Phase 3 |
| **Phase 4 Total** | **~56 hrs** | | |

### Phase 5: Polish & Testing (Week 7-8)

| Task | Effort | Risk | Dependencies |
|---|---|---|---|
| Hardcoded color replacement | 8 hrs | Low | Phase 3 |
| Inline KPI card replacement | 4 hrs | Low | Phase 2 |
| Raw chart/table standardization | 8 hrs | Low | Phase 2 |
| Test coverage expansion | 12 hrs | Low | Phase 3 |
| Performance optimization | 4 hrs | Medium | Phase 3 |
| Documentation update | 4 hrs | Low | Phase 4 |
| UAT testing | 8 hrs | Medium | Phase 5 |
| **Phase 5 Total** | **~48 hrs** | | |

### Total Implementation Effort

| Phase | Hours | Weeks |
|---|---|---|
| Phase 1: Cleanup | 9 | 1 |
| Phase 2: Shared Components | 22 | 2 |
| Phase 3: Dashboard Restructuring | 46 | 3-4 |
| Phase 4: Integration Points | 56 | 5-6 |
| Phase 5: Polish & Testing | 48 | 7-8 |
| **Total** | **~181 hrs** | **8 weeks** |

---

## 20. Risk Assessment

### 20.1 High-Risk Items

| # | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| 1 | Breaking business logic during view migration | Medium | Critical | Automated regression tests before/after each view |
| 2 | Session state regression during router refactor | High | High | Incremental migration with feature flags |
| 3 | Filter system regression | Medium | High | Test all filter combinations per dashboard |
| 4 | Performance regression during restructuring | Medium | Medium | Profile before/after, cache validation |
| 5 | AI module integration failures | Low | Medium | Fallback to offline provider |

### 20.2 Medium-Risk Items

| # | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| 6 | Import path changes breaking modules | Medium | Medium | Use `try/except` with fallback imports |
| 7 | CSS/class name conflicts during consolidation | Low | Medium | Audit CSS before consolidation |
| 8 | Export format regression | Low | Medium | Test all export formats per dashboard |
| 9 | State namespace conflicts | Low | Medium | Validate namespace uniqueness |

### 20.3 Low-Risk Items

| # | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| 10 | Design token inconsistencies | Low | Low | Token audit before/after |
| 11 | Documentation drift | Medium | Low | Update docs as part of each phase |
| 12 | Test coverage gaps | Medium | Low | Add tests for each new component |

---

## 21. Dependency Graph

### 21.1 Phase Dependencies

```
Phase 1 (Cleanup)
    ↓
Phase 2 (Shared Components)
    ↓
Phase 3 (Dashboard Restructuring)
    ├──→ Phase 4a (Report Center)
    ├──→ Phase 4b (Presentation Manager)
    ├──→ Phase 4c (AI Integration)
    ├──→ Phase 4d (Auth/Roles)
    └──→ Phase 4e (Dashboard Designer)
         ↓
    Phase 5 (Polish & Testing)
```

### 21.2 Module Dependencies

```
app.py
├── config.settings
├── config.environment
├── config.roles (NEW)
├── config.dashboard_templates.json (NEW)
├── services.state_registry → services.state_manager
├── services.auth (NEW) → services.role_manager (NEW)
├── services.report_center (NEW)
├── services.presentation_manager (NEW)
├── services.export_service
├── services.ai
├── views.{dashboard}.{page} → views.shared
├── views.components.kpi_engine (NEW)
├── views.components.chart_engine (NEW)
└── ui.components.*
```

### 21.3 Component Dependencies

```
views/components/kpi_engine.py
├── ui.components.metrics (KPIGrid, MetricCard)
├── utils.calculations.*
└── ui.formatters

views/components/chart_engine.py
├── ui.components.charts (ChartCard, apply_chart)
├── utils.calculations.*
└── ui.design_tokens

views/components/data_table.py
├── ui.components.tables (TableCard)
├── ui.tables (html_table)
└── ui.formatters

views/components/insight_card.py
├── services.ai
├── ui.components.core (AlertBanner)
└── ui.design_tokens

views/components/export_section.py
├── ui.export_buttons
└── services.export_service
```

---

## 22. Suggested Implementation Order

### Week 1: Foundation

1. **Day 1-2:** Execute Phase 1 cleanup (delete 79 files, fix imports, verify security)
2. **Day 3:** Create `views/components/` package structure
3. **Day 4:** Implement `KPIEngine` with tests
4. **Day 5:** Implement `ChartEngine` with tests

### Week 2: Shared Components

1. **Day 1-2:** Implement `views/base.py` (BaseDashboard class)
2. **Day 3:** Implement `views/registry.py` (dashboard registry)
3. **Day 4-5:** Create `views/components/data_table.py`, `insight_card.py`, `export_section.py`

### Week 3: Dashboard Packages

1. **Day 1-2:** Create all 6 dashboard packages (`views/operations/`, etc.)
2. **Day 3-4:** Migrate D1 (Operations) and D2 (Revenue) views
3. **Day 5:** Migrate D3 (People) and D4 (Performance) views

### Week 4: Migration Complete

1. **Day 1-2:** Migrate D5 (Finance) and D6 (Audit) views
2. **Day 3-4:** Refactor `app.py` router and sidebar
3. **Day 5:** Refactor filter system, update `views/shared.py`

### Week 5: Integration

1. **Day 1-3:** Implement `services/report_center.py`
2. **Day 4-5:** Implement `services/presentation_manager.py`

### Week 6: Integration (continued)

1. **Day 1-3:** Wire AI module to all dashboards
2. **Day 4-5:** Implement `services/auth.py` and `services/role_manager.py`

### Week 7: Polish

1. **Day 1-3:** Replace hardcoded colors with design tokens
2. **Day 4-5:** Standardize all KPI/chart/table rendering

### Week 8: Testing

1. **Day 1-3:** Expand test coverage
2. **Day 4-5:** UAT testing, bug fixes, documentation

---

## 23. Regression Checklist

### 23.1 Pre-Migration Baseline

| # | Check | Method | Pass Criteria |
|---|---|---|---|
| 1 | All 19 pages render without error | Manual/automated | No exceptions |
| 2 | Global filters apply correctly | Manual | Location, BU, period filters work |
| 3 | Page-specific filters work | Manual | Service type, advisor filters work |
| 4 | Comparison modes work | Manual | YoY and MoM comparisons render |
| 5 | KPI cards display correctly | Manual | Values match data source |
| 6 | Charts render correctly | Manual | No broken charts |
| 7 | Tables display correctly | Manual | Data integrity maintained |
| 8 | Export buttons work | Manual | CSV, Excel, PDF download |
| 9 | Navigation works | Manual | All 19 pages accessible |
| 10 | Session state persists | Manual | Filters survive page switches |
| 11 | Alert system works | Manual | Alerts display correctly |
| 12 | AI narratives generate | Manual | Reports generate (or offline fallback) |

### 23.2 Post-Migration Validation

| # | Check | Method | Pass Criteria |
|---|---|---|---|
| 13 | All 6 dashboards render | Manual/automated | No exceptions |
| 14 | All sub-pages within each dashboard work | Manual | 21 sub-pages accessible |
| 15 | Dashboard selector works | Manual | Radio button switches dashboard |
| 16 | Section radio works | Manual | Radio button switches page |
| 17 | Global filters apply across dashboards | Manual | Location, BU, period persist |
| 18 | Dashboard-specific filters work | Manual | Service type, advisor filters scoped |
| 19 | KPI values match pre-migration | Automated | Values within 0.01% tolerance |
| 20 | Chart data matches pre-migration | Automated | Data points identical |
| 21 | Table data matches pre-migration | Automated | Row/column counts match |
| 22 | Export formats work | Manual | CSV, Excel, PDF download |
| 23 | AI narratives generate | Manual | Reports generate per dashboard |
| 24 | Report Center works | Manual | Scheduled reports generate |
| 25 | Presentation Manager works | Manual | PowerPoint exports correctly |
| 26 | Role-based access works | Manual | Users see only authorized dashboards |
| 27 | Session state persists | Manual | Filters survive dashboard switches |
| 28 | Alert system works | Manual | Alerts display correctly |
| 29 | Performance acceptable | Profiler | No >20% regression in load time |
| 30 | All tests pass | pytest | 100% pass rate |

### 23.3 Business Logic Regression

| # | Check | Method | Pass Criteria |
|---|---|---|---|
| 31 | Revenue calculations correct | Automated | `calculate_gross_revenue()` matches |
| 32 | Margin calculations correct | Automated | `calculate_total_margin()` matches |
| 33 | Discount calculations correct | Automated | `calculate_labour_discount_pct()` matches |
| 34 | Leakage calculations correct | Automated | `compute_discount_aggregates()` matches |
| 35 | Target achievement correct | Automated | `calc_achievement_pct()` matches |
| 36 | Growth calculations correct | Automated | `calc_growth_pct()` matches |
| 37 | Ratio calculations correct | Automated | `calc_ratio()` matches |
| 38 | Aggregation results correct | Automated | `location_summary()` matches |
| 39 | Filter semantics preserved | Automated | `apply_global_filters()` matches |
| 40 | Cleaning pipeline unchanged | Automated | `clean_dataframe()` output identical |

---

**End of Implementation Roadmap**

*This document is planning only. No code has been modified. All implementation must follow the phased approach with regression testing at each stage.*
