# 03 — WSMIS Codebase Index
**Auto-Generated Repository Reference — Claude Review Package**
**Generated: 2026-06-22**

---

## Table of Contents

1. [Repository Overview](#1-repository-overview)
2. [Folder Tree](#2-folder-tree)
3. [Layer Architecture](#3-layer-architecture)
4. [Dashboard Routing Table](#4-dashboard-routing-table)
5. [Services Layer](#5-services-layer)
6. [UI Layer](#6-ui-layer)
7. [Calculation Layer](#7-calculation-layer)
8. [View Components](#8-view-components)
9. [Views — V2 Implementations](#9-views--v2-implementations)
10. [Views — V1 Wrappers](#10-views--v1-wrappers)
11. [Tests](#11-tests)
12. [Configuration](#12-configuration)
13. [Dependency Graph](#13-dependency-graph)
14. [Summary Statistics](#14-summary-statistics)

---

## 1. Repository Overview

| Metric | Value |
|--------|-------|
| Total Python Files | ~110 |
| Total Python LOC | ~17,500 |
| Dashboard Count | 21 (frozen) |
| Test Count | 5 test files, 38 test cases |
| Framework | Streamlit + Plotly + pandas |
| Data Source | Google Sheets (gspread + OAuth2) |

---

## 2. Folder Tree

`
WSMIS/
+-- .streamlit/
¦   +-- config.toml                          (2 lines)
+-- config/
¦   +-- __init__.py                          (0 lines)
¦   +-- environment.py                       (82 lines)
¦   +-- paths.py                             (7 lines)
¦   +-- settings.py                          (16 lines)
¦   +-- users.yaml                           (277 lines)
+-- docs/
¦   +-- ARCHITECTURE.md                      (11 lines)
¦   +-- BUG_TEMPLATE.md                      (22 lines)
¦   +-- CHANGELOG.md                         (13 lines)
¦   +-- DEPENDENCY_RULES.md                  (13 lines)
¦   +-- DEPLOYMENT_CHECKLIST.md              (31 lines)
¦   +-- FEATURE_REQUEST_TEMPLATE.md          (21 lines)
¦   +-- FOLDER_STRUCTURE.md                  (16 lines)
¦   +-- FRAMEWORK.md                         (41 lines)
¦   +-- KNOWN_ISSUES.md                      (19 lines)
¦   +-- KNOWN_LIMITATIONS.md                 (28 lines)
¦   +-- MIGRATION_GUIDE.md                   (29 lines)
¦   +-- PERFORMANCE_BASELINE.md              (42 lines)
¦   +-- PERFORMANCE_PROFILE.md               (87 lines)
¦   +-- RELEASE_NOTES_v1.0.0.md              (30 lines)
¦   +-- SECURITY_MIGRATION.md                (15 lines)
¦   +-- UAT_CHECKLIST.md                     (56 lines)
¦   +-- UAT_GUIDE.md                         (36 lines)
¦   +-- UAT_SIGNOFF.md                       (58 lines)
+-- logs/
¦   +-- logger.py                            (0 lines)
+-- reports/
¦   +-- global_filter_sync_audit.md          (35 lines)
+-- scripts/
¦   +-- migrate_chart_engine.py              (44 lines)
¦   +-- rewrite_imports.py                   (57 lines)
¦   +-- test_ai_report.py                    (41 lines)
+-- services/
¦   +-- __init__.py                          (1 line)
¦   +-- aggregation_cache.py                 (193 lines)
¦   +-- audit_service.py                     (218 lines)
¦   +-- auth_service.py                      (257 lines)
¦   +-- benchmark_provider.py                (30 lines)
¦   +-- error_handler.py                     (69 lines)
¦   +-- executive_alert_engine.py            (147 lines)
¦   +-- export_service.py                    (474 lines)
¦   +-- financial_service.py                 (66 lines)
¦   +-- logger.py                            (41 lines)
¦   +-- logging_service.py                   (66 lines)
¦   +-- route_service.py                     (284 lines)
¦   +-- state_manager.py                     (272 lines)
¦   +-- state_registry.py                    (46 lines)
¦   +-- ai/
¦       +-- __init__.py                      (36 lines)
¦       +-- context_builder.py               (245 lines)
¦       +-- gemini_provider.py               (45 lines)
¦       +-- models.py                        (100 lines)
¦       +-- prompt_builder.py                (62 lines)
¦       +-- report_generator.py              (233 lines)
¦       +-- templates.py                     (108 lines)
+-- static/
¦   +-- style.css                            (512 lines)
+-- templates/                               (empty)
+-- tests/
¦   +-- __init__.py                          (0 lines)
¦   +-- golden_snapshots.json                (1360 lines)
¦   +-- test_aggregations.py                 (55 lines)
¦   +-- test_calculations.py                 (85 lines)
¦   +-- test_filters.py                      (49 lines)
¦   +-- test_golden_snapshot.py              (120 lines)
¦   +-- test_pages.py                        (34 lines)
+-- ui/
¦   +-- __init__.py                          (1 line)
¦   +-- design_tokens.py                     (144 lines)
¦   +-- executive_tooltip.py                 (142 lines)
¦   +-- export_buttons.py                    (136 lines)
¦   +-- formatters.py                        (113 lines)
¦   +-- helpers.py                           (120 lines)
¦   +-- tables.py                            (39 lines)
¦   +-- traffic.py                           (22 lines)
¦   +-- components/
¦       +-- __init__.py                      (20 lines)
¦       +-- core.py                          (148 lines)
¦       +-- filters.py                       (69 lines)
¦       +-- metrics.py                       (80 lines)
¦       +-- tables.py                        (19 lines)
+-- utils/
¦   +-- __init__.py                          (0 lines)
¦   +-- aggregations.py                      (60 lines)
¦   +-- cleaning.py                          (88 lines)
¦   +-- constants.py                         (94 lines)
¦   +-- filters.py                           (65 lines)
¦   +-- loaders.py                           (324 lines)
¦   +-- profiler.py                          (50 lines)
¦   +-- calculations/
¦       +-- __init__.py                      (0 lines)
¦       +-- common.py                        (39 lines)
¦       +-- discount.py                      (65 lines)
¦       +-- fact_metrics.py                  (95 lines)
¦       +-- leakage.py                       (61 lines)
¦       +-- margin.py                        (41 lines)
¦       +-- revenue.py                       (25 lines)
+-- views/
¦   +-- __init__.py                          (1 line)
¦   +-- shared.py                            (35 lines)
¦   +-- dashboard_common.py                  (223 lines)
¦   +-- system_health.py                     (106 lines)
¦   +-- unauthorized.py                      (91 lines)
¦   +-- leakage.py                           (240 lines)
¦   +-- advisor.py                           (6 lines)
¦   +-- advisor_mom.py                       (6 lines)
¦   +-- audit_intelligence.py                (6 lines)
¦   +-- cockpit.py                           (6 lines)
¦   +-- discount.py                          (6 lines)
¦   +-- executive.py                         (6 lines)
¦   +-- expense.py                           (6 lines)
¦   +-- internal_audit.py                    (6 lines)
¦   +-- labour.py                            (6 lines)
¦   +-- locations.py                         (6 lines)
¦   +-- margin.py                            (6 lines)
¦   +-- overview.py                          (6 lines)
¦   +-- parts_detail.py                      (6 lines)
¦   +-- parts_executive.py                   (6 lines)
¦   +-- pnl.py                               (6 lines)
¦   +-- reports.py                           (6 lines)
¦   +-- sales_mix.py                         (6 lines)
¦   +-- targets.py                           (6 lines)
¦   +-- trends.py                            (6 lines)
¦   +-- components/
¦   ¦   +-- chart_engine.py                  (91 lines)
¦   ¦   +-- kpi_engine.py                    (18 lines)
¦   +-- executive/
¦   ¦   +-- __init__.py                      (12 lines)
¦   ¦   +-- cockpit.py                       (320 lines)
¦   ¦   +-- executive.py                     (295 lines)
¦   ¦   +-- overview.py                      (205 lines)
¦   +-- commercial/
¦   ¦   +-- __init__.py                      (12 lines)
¦   ¦   +-- discount.py                      (833 lines)
¦   ¦   +-- labour.py                        (664 lines)
¦   ¦   +-- margin.py                        (130 lines)
¦   ¦   +-- parts_detail.py                  (229 lines)
¦   ¦   +-- parts_executive.py               (492 lines)
¦   ¦   +-- sales_mix.py                     (112 lines)
¦   +-- operations/
¦   ¦   +-- __init__.py                      (11 lines)
¦   ¦   +-- advisor.py                       (226 lines)
¦   ¦   +-- advisor_mom.py                   (195 lines)
¦   ¦   +-- audit_intelligence.py            (195 lines)
¦   ¦   +-- internal_audit.py                (473 lines)
¦   ¦   +-- reports.py                       (250 lines)
¦   +-- performance/
¦   ¦   +-- __init__.py                      (8 lines)
¦   ¦   +-- locations.py                     (163 lines)
¦   ¦   +-- targets.py                       (128 lines)
¦   +-- financial/
¦   ¦   +-- __init__.py                      (8 lines)
¦   ¦   +-- expense.py                       (45 lines)
¦   ¦   +-- pnl.py                           (22 lines)
¦   +-- trend/
¦       +-- __init__.py                      (10 lines)
¦       +-- trends.py                        (186 lines)
+-- app.py                                   (846 lines)
+-- exp_report.py                            (2081 lines)
+-- pnl_report.py                            (1322 lines)
+-- revenue_leakage_v31.py                   (871 lines)
+-- requirements.txt                         (15 lines)
+-- requirements-dev.txt                     (3 lines)
+-- README.md                                (87 lines)
+-- INSTALL.md                               (61 lines)
+-- ROOT_CAUSE_ANALYSIS.md                   (126 lines)
`

---

## 3. Layer Architecture

### 3.1 Dependency Flow (Frozen)

`
app.py (Entry Point — 846 lines)
  +-- views/*.py (V1 Wrappers — 18 files, ~6 lines each)
  ¦     +-- views/<domain>/*.py (V2 Implementations — 22 files, ~5,355 lines)
  +-- views/shared.py (Wildcard Import Hub — 35 lines)
  +-- views/components/kpi_engine.py (KPI Renderer — 18 lines)
  +-- views/components/chart_engine.py (Chart Engine — 91 lines)
  +-- services/*.py (Business Logic — 14 files, ~2,172 lines)
  ¦     +-- services/ai/*.py (AI Subsystem — 7 files, ~829 lines)
  +-- utils/*.py (Data Pipeline — 5 files, ~681 lines)
  ¦     +-- utils/calculations/*.py (Calculations — 6 files, ~286 lines)
  +-- ui/*.py (Design System — 8 files, ~757 lines)
  ¦     +-- ui/components/*.py (UI Components — 4 files, ~236 lines)
  +-- config/*.py (Settings — 5 files, ~384 lines)
`

### 3.2 Import Rules

| Source | Target | Allowed |
|--------|--------|---------|
| app.py | views/*, services/*, utils/*, ui/* | YES |
| views/* | views/shared.py, views/components/*, services/*, utils/*, ui/* | YES |
| views/* | views/<domain>/* | YES |
| services/* | utils/*, ui/* (design tokens) | YES |
| utils/* | (nothing cross-layer) | NO |
| ui/* | (nothing cross-layer) | NO |
| services/* | views/* | NO |
| utils/* | views/* | NO |
| ui/* | services/* | NO |

---

## 4. Dashboard Routing Table

### 4.1 Route Key -> View Module -> V2 Implementation

| # | Route Key | V1 Wrapper | V2 Implementation | Domain | Lines |
|---|-----------|------------|-------------------|--------|-------|
| 1 | Overview | views/overview.py | views/executive/overview.py | executive | 205 |
| 2 | Executive | views/executive.py | views/executive/executive.py | executive | 295 |
| 3 | Cockpit | views/cockpit.py | views/executive/cockpit.py | executive | 320 |
| 4 | Labour | views/labour.py | views/commercial/labour.py | commercial | 664 |
| 5 | parts_executive | views/parts_executive.py | views/commercial/parts_executive.py | commercial | 492 |
| 6 | parts_detail | views/parts_detail.py | views/commercial/parts_detail.py | commercial | 229 |
| 7 | Margin | views/margin.py | views/commercial/margin.py | commercial | 130 |
| 8 | Discounts | views/discount.py | views/commercial/discount.py | commercial | 833 |
| 9 | Leakage Center | views/leakage.py | (direct V1) | commercial | 240 |
| 10 | Sales Mix | views/sales_mix.py | views/commercial/sales_mix.py | commercial | 112 |
| 11 | Advisors | views/advisor.py | views/operations/advisor.py | operations | 226 |
| 12 | Advisor MoM | views/advisor_mom.py | views/operations/advisor_mom.py | operations | 195 |
| 13 | Locations | views/locations.py | views/performance/locations.py | performance | 163 |
| 14 | Trends | views/trends.py | views/trend/trends.py | trend | 186 |
| 15 | Targets | views/targets.py | views/performance/targets.py | performance | 128 |
| 16 | Reports | views/reports.py | views/operations/reports.py | operations | 250 |
| 17 | Expense Analysis | views/expense.py | views/financial/expense.py | financial | 45 |
| 18 | Profit & Loss | views/pnl.py | views/financial/pnl.py | financial | 22 |
| 19 | Internal Audit | views/internal_audit.py | views/operations/internal_audit.py | operations | 473 |
| 20 | Audit Intelligence | views/audit_intelligence.py | views/operations/audit_intelligence.py | operations | 195 |
| 21 | System Health | views/system_health.py | (direct V1) | ops | 106 |

### 4.2 V2 URL Slugs

`
cockpit -> Cockpit
overview -> Overview
executive -> Executive
labour -> Labour
parts-executive -> parts_executive
parts-detail -> parts_detail
margin -> Margin
discounts -> Discounts
sales-mix -> Sales Mix
leakage-centre -> Leakage Center
advisors -> Advisors
advisor-mom -> Advisor MoM
locations -> Locations
targets -> Targets
trends -> Trends
reports -> Reports
expense -> Expense Analysis
pnl -> Profit & Loss
internal-audit -> Internal Audit
audit-intelligence -> Audit Intelligence
system-health -> System Health
`

---

## 5. Services Layer

| File | Lines | Purpose |
|------|-------|---------|
| services/__init__.py | 1 | Package marker |
| services/aggregation_cache.py | 193 | Thread-safe LRU cache for aggregated DataFrames |
| services/audit_service.py | 218 | Audit data loading + missed labour calculation |
| services/auth_service.py | 257 | RBAC authentication, role checking, user management |
| services/benchmark_provider.py | 30 | Abstract base class for business threshold providers |
| services/error_handler.py | 69 | Custom exceptions + safe_render decorator |
| services/executive_alert_engine.py | 147 | Alert evaluation engine (threshold-based) |
| services/export_service.py | 474 | CSV/Excel/PDF export for all dashboards |
| services/financial_service.py | 66 | Financial metrics orchestrator |
| services/logger.py | 41 | Rotating file logger configuration |
| services/logging_service.py | 66 | Performance/error logging decorators |
| services/route_service.py | 284 | Route registry, protection, page authorization |
| services/state_manager.py | 272 | Namespace-driven session state management |
| services/state_registry.py | 46 | Dashboard namespace registration |

### 5.1 AI Sub-system

| File | Lines | Purpose |
|------|-------|---------|
| services/ai/__init__.py | 36 | Package init + public API exports |
| services/ai/context_builder.py | 245 | Builds context dictionaries for AI prompts |
| services/ai/gemini_provider.py | 45 | Google Gemini API wrapper |
| services/ai/models.py | 100 | Pydantic data models for AI requests/responses |
| services/ai/prompt_builder.py | 62 | Constructs structured prompts for AI analysis |
| services/ai/report_generator.py | 233 | Orchestrates full AI report generation pipeline |
| services/ai/templates.py | 108 | Prompt templates for different analysis types |

---

## 6. UI Layer

| File | Lines | Purpose |
|------|-------|---------|
| ui/__init__.py | 1 | Package marker |
| ui/design_tokens.py | 144 | Design token registry (T class) — colors, spacing, typography |
| ui/executive_tooltip.py | 142 | Plotly tooltip templates for executive charts |
| ui/export_buttons.py | 136 | Reusable export button components (CSV/Excel/PDF) |
| ui/formatters.py | 113 | Number formatters: fmt_inr, fmt_pct, fmt_num |
| ui/helpers.py | 120 | Chart helpers, negative labour alert, revenue table builder |
| ui/tables.py | 39 | HTML table renderer + searchable table component |
| ui/traffic.py | 22 | YoY badge, traffic light indicator, target badge |

### 6.1 UI Components

| File | Lines | Purpose |
|------|-------|---------|
| ui/components/__init__.py | 20 | Barrel exports for all UI components |
| ui/components/core.py | 148 | UniversalHeader, UniversalFooter, EmptyState, AlertBanner |
| ui/components/filters.py | 69 | FilterToolbar — reusable filter controls |
| ui/components/metrics.py | 80 | MetricCard — single KPI metric display |
| ui/components/tables.py | 19 | TableCard — styled table wrapper |

---

## 7. Calculation Layer

| File | Lines | Purpose |
|------|-------|---------|
| utils/calculations/__init__.py | 0 | Package marker |
| utils/calculations/common.py | 39 | safe_divide, calc_ratio, calc_growth_pct, calc_achievement_pct |
| utils/calculations/fact_metrics.py | 95 | Column extractors: labour_sales, parts_sales, net_labour, etc. |
| utils/calculations/revenue.py | 25 | Revenue aggregation functions |
| utils/calculations/margin.py | 41 | Margin aggregation functions |
| utils/calculations/discount.py | 65 | Discount aggregation functions |
| utils/calculations/leakage.py | 61 | Leakage/recoverable computation |

### 7.1 Other Utils

| File | Lines | Purpose |
|------|-------|---------|
| utils/__init__.py | 0 | Package marker |
| utils/aggregations.py | 60 | General-purpose aggregation helpers |
| utils/cleaning.py | 88 | DataFrame cleaning/transformation utilities |
| utils/constants.py | 94 | Application-wide constants and column mappings |
| utils/filters.py | 65 | Filter application functions for DataFrames |
| utils/loaders.py | 324 | Data loading from Google Sheets/API (core data pipeline) |
| utils/profiler.py | 50 | Performance profiling decorators |

---

## 8. View Components

| File | Lines | Purpose |
|------|-------|---------|
| views/components/chart_engine.py | 91 | Plotly chart standardization (colors, layout, responsive sizing) |
| views/components/kpi_engine.py | 18 | KPI grid renderer (delegates to ui/components/metrics.py) |

### 8.1 Shared View Utilities

| File | Lines | Purpose |
|------|-------|---------|
| views/shared.py | 35 | Central barrel-import hub — imports all V2 view modules |
| views/dashboard_common.py | 223 | Shared dashboard utilities (header, filters, export, common charts) |

---

## 9. Views — V2 Implementations

### 9.1 Executive Domain

| File | Lines | Purpose |
|------|-------|---------|
| views/executive/__init__.py | 12 | Package init + exports |
| views/executive/cockpit.py | 320 | Executive cockpit dashboard |
| views/executive/overview.py | 205 | Overview dashboard |
| views/executive/executive.py | 295 | Executive summary dashboard |

### 9.2 Commercial Domain

| File | Lines | Purpose |
|------|-------|---------|
| views/commercial/__init__.py | 12 | Package init + exports |
| views/commercial/labour.py | 664 | Labour dashboard |
| views/commercial/parts_executive.py | 492 | Parts executive dashboard |
| views/commercial/parts_detail.py | 229 | Parts detail dashboard |
| views/commercial/margin.py | 130 | Margin dashboard |
| views/commercial/discount.py | 833 | Discount dashboard |
| views/commercial/sales_mix.py | 112 | Sales mix dashboard |

### 9.3 Operations Domain

| File | Lines | Purpose |
|------|-------|---------|
| views/operations/__init__.py | 11 | Package init + exports |
| views/operations/advisor.py | 226 | Advisor dashboard |
| views/operations/advisor_mom.py | 195 | Advisor month-over-month dashboard |
| views/operations/internal_audit.py | 473 | Internal audit dashboard |
| views/operations/audit_intelligence.py | 195 | Audit intelligence dashboard |
| views/operations/reports.py | 250 | Reports dashboard |

### 9.4 Performance Domain

| File | Lines | Purpose |
|------|-------|---------|
| views/performance/__init__.py | 8 | Package init + exports |
| views/performance/locations.py | 163 | Locations (branch comparison) dashboard |
| views/performance/targets.py | 128 | Targets dashboard |

### 9.5 Financial Domain

| File | Lines | Purpose |
|------|-------|---------|
| views/financial/__init__.py | 8 | Package init + exports |
| views/financial/pnl.py | 22 | Profit & Loss dashboard |
| views/financial/expense.py | 45 | Expense analysis dashboard |

### 9.6 Trend Domain

| File | Lines | Purpose |
|------|-------|---------|
| views/trend/__init__.py | 10 | Package init + exports |
| views/trend/trends.py | 186 | Trends (time-series) dashboard |

### 9.7 Direct V1 (No V2 Delegation)

| File | Lines | Purpose |
|------|-------|---------|
| views/leakage.py | 240 | Leakage Centre dashboard (direct V1) |
| views/system_health.py | 106 | System Health dashboard (admin only) |
| views/unauthorized.py | 91 | Unauthorized access page |

---

## 10. Views — V1 Wrappers

All V1 wrappers are 6-line delegation files:

`python
from views.shared import *

def render():
    # delegates to V2 module via shared imports
    pass
`

| Wrapper | Delegates To |
|---------|-------------|
| views/cockpit.py | views/executive/cockpit.py |
| views/overview.py | views/executive/overview.py |
| views/executive.py | views/executive/executive.py |
| views/labour.py | views/commercial/labour.py |
| views/parts_executive.py | views/commercial/parts_executive.py |
| views/parts_detail.py | views/commercial/parts_detail.py |
| views/margin.py | views/commercial/margin.py |
| views/discount.py | views/commercial/discount.py |
| views/sales_mix.py | views/commercial/sales_mix.py |
| views/advisor.py | views/operations/advisor.py |
| views/advisor_mom.py | views/operations/advisor_mom.py |
| views/internal_audit.py | views/operations/internal_audit.py |
| views/audit_intelligence.py | views/operations/audit_intelligence.py |
| views/reports.py | views/operations/reports.py |
| views/locations.py | views/performance/locations.py |
| views/targets.py | views/performance/targets.py |
| views/pnl.py | views/financial/pnl.py |
| views/expense.py | views/financial/expense.py |
| views/trends.py | views/trend/trends.py |

---

## 11. Tests

| File | Lines | Purpose |
|------|-------|---------|
| tests/__init__.py | 0 | Package marker |
| tests/test_pages.py | 34 | Streamlit AppTest for all 19 dashboard pages (smoke test) |
| tests/test_calculations.py | 85 | Unit tests for revenue, margin, discount calculation functions |
| tests/test_filters.py | 49 | Unit tests for filter application functions |
| tests/test_aggregations.py | 55 | Unit tests for aggregation helper functions |
| tests/test_golden_snapshot.py | 120 | Golden snapshot regression test (71 KPI baseline keys) |
| tests/golden_snapshots.json | 1360 | Reference data for golden snapshot tests |

### 11.1 Test Dependencies

`
tests/test_pages.py -> app.py (Streamlit AppTest)
tests/test_calculations.py -> utils/calculations/*
tests/test_filters.py -> utils/filters.py
tests/test_aggregations.py -> utils/aggregations.py
tests/test_golden_snapshot.py -> tests/golden_snapshots.json
`

---

## 12. Configuration

| File | Lines | Purpose |
|------|-------|---------|
| .streamlit/config.toml | 2 | Streamlit server config (theme) |
| .streamlit/secrets.toml | 39 | Secrets (GCP credentials, API keys) — SECURITY BLOCKER |
| config/__init__.py | 0 | Package marker |
| config/environment.py | 82 | Environment detection (local vs. production) |
| config/paths.py | 7 | Path constants for data directories |
| config/settings.py | 16 | Application settings constants |
| config/users.yaml | 277 | User role definitions and permissions |
| requirements.txt | 15 | Production dependencies |
| requirements-dev.txt | 3 | Development/test dependencies |

---

## 13. Dependency Graph

### 13.1 Module Dependency Map

`
app.py
  +-- views/shared.py
  ¦     +-- views/executive/*
  ¦     +-- views/commercial/*
  ¦     +-- views/operations/*
  ¦     +-- views/performance/*
  ¦     +-- views/financial/*
  ¦     +-- views/trend/*
  +-- views/components/kpi_engine.py
  +-- views/components/chart_engine.py
  +-- services/auth_service.py
  +-- services/state_manager.py
  +-- services/route_service.py
  +-- services/export_service.py
  +-- services/executive_alert_engine.py
  +-- services/aggregation_cache.py
  +-- services/error_handler.py
  +-- utils/loaders.py
  +-- utils/filters.py
  +-- utils/constants.py
  +-- ui/design_tokens.py
  +-- ui/formatters.py
  +-- ui/export_buttons.py
  +-- config/settings.py

services/*
  +-- utils/loaders.py
  +-- utils/aggregations.py
  +-- ui/design_tokens.py

views/<domain>/*
  +-- views/shared.py
  +-- views/components/kpi_engine.py
  +-- views/components/chart_engine.py
  +-- views/dashboard_common.py
  +-- services/*
  +-- utils/*
  +-- ui/*
`

### 13.2 Cross-Module Import Count

| Source Module | Imported By (count) |
|---------------|---------------------|
| ui/design_tokens.py | 15+ |
| views/shared.py | 18 (V1 wrappers) |
| services/error_handler.py | 12+ |
| utils/constants.py | 10+ |
| ui/formatters.py | 8+ |
| utils/loaders.py | 6+ |

---

## 14. Summary Statistics

| Category | Files | Total Lines |
|----------|-------|-------------|
| Core (app.py) | 1 | 846 |
| Views (V1 wrappers) | 18 | ~114 |
| Views (V2 implementations) | 22 | ~5,355 |
| Views (shared/components) | 4 | ~367 |
| Services | 14 | ~2,172 |
| Services (AI) | 7 | ~829 |
| UI | 8 | ~757 |
| UI Components | 4 | ~236 |
| Calculations | 6 | ~286 |
| Utils | 5 | ~681 |
| Tests | 5 | ~343 |
| Config | 5 | ~384 |
| Root legacy | 3 | ~4,274 |
| Documentation | 18+ | ~1,200+ |
| **Grand Total (Python)** | **~110** | **~17,544** |

---

**End of Codebase Index**
