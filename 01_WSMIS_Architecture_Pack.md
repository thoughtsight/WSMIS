# 01 — WSMIS Architecture Pack
**Consolidated Reference for Code Review — Claude Review Package**
**Generated: 2026-06-22**

---

## Table of Contents

1. Product Requirements (PRD)
2. UX Blueprint
3. Master Engineering Reference
4. Architecture Documentation
5. Engineering Playbook
6. Architecture Review Board Resolutions
7. Dashboard Taxonomy (Frozen)
8. Dependency Rules

---

## 1. Product Requirements (PRD)

**Source:** WSMIS_PRD.md

### 1.1 Product Vision

Workshop Services Management Information System (WSMIS) — a unified Streamlit-based dashboard application for RKM Auto, providing:

- 21 operational dashboards across 6 functional domains
- Real-time KPI monitoring with drill-down capability
- AI-powered anomaly detection and recommendation engine
- Branch-level performance benchmarking

### 1.2 Core Capabilities

| Domain | Dashboards | Purpose |
|--------|-----------|---------|
| Executive | Cockpit, Overview, Executive | High-level performance summary, strategic KPIs |
| Commercial | Labour, Parts Executive, Parts Detail, Margin, Discounts, Sales Mix, Leakage Centre | Revenue and service revenue optimization |
| Operations | Advisors, Advisor MoM, Internal Audit, Audit Intelligence, Reports | Staff performance, compliance, audit |
| Performance | Locations, Targets | Branch benchmarking and target tracking |
| Financial | P&L, Expense | Financial analysis |
| Trend | Trends | Time-series analysis |

### 1.3 Key Business Rules

1. No permanent deletion — all removed content goes to archive/
2. LEGACY_NAV = True — V2 routing infrastructure exists but is dormant by default
3. Architecture is frozen — no redesign, no new architecture without explicit approval
4. 100% business behaviour preservation — calculations, KPI logic, dashboard layout unchanged
5. 21 dashboards are the frozen taxonomy — no new dashboards, no renamed dashboards
6. Delete never means permanent — all deleted content preserved in archive

### 1.4 Data Sources

- Primary: Google Sheets via gspread + OAuth2
- Export: CSV, Excel, PDF
- AI: Google Gemini API (optional, not enabled by default)

### 1.5 User Roles

| Role | Access Level |
|------|-------------|
| Admin | All dashboards + System Health |
| Senior | All dashboards (no System Health) |
| User | Subset of dashboards |
| Viewer | Read-only subset |

---

## 2. UX Blueprint

**Source:** WSMIS_UX_BLUEPRINT.md

### 2.1 Design System

- Design Tokens: Centralized in ui/design_tokens.py — single source of truth
- Color Palette: Dark theme with role-based accent colors
- Typography: System fonts, consistent sizing scale
- Spacing: 4px/8px grid system

### 2.2 Component Hierarchy

`
Page Layout
+-- UniversalHeader (ui/components/core.py)
+-- FilterToolbar (ui/components/filters.py)
+-- KPI Grid (views/components/kpi_engine.py -> ui/components/metrics.py)
+-- Charts (views/components/chart_engine.py)
+-- Tables (ui/tables.py -> ui/components/tables.py)
+-- UniversalFooter (ui/components/core.py)
`

### 2.3 Navigation

- V1 (Active): Sidebar radio button navigation via app.py main() function
- V2 (Dormant): URL-based routing via ?page=<slug> behind LEGACY_NAV = True
- Page slugs: Defined in PAGE_SLUGS dict in app.py (21 entries)
- Sidebar rendering: _sidebar_v1() or _sidebar_v2() selected by LEGACY_NAV flag

### 2.4 Export Pattern

All dashboards support CSV/Excel/PDF export via:
- ui/export_buttons.py — reusable button components
- services/export_service.py — backend export logic

---

## 3. Master Engineering Reference

**Source:** WSMIS_MASTER_ENGINEERING_REFERENCE.md (FROZEN)

### 3.1 Golden Rules

1. No architecture changes — existing architecture is frozen
2. No new modules — only modify existing files within approved scope
3. No import changes — unless explicitly approved per task
4. One commit per task — each independently revertable
5. Preserve business logic — calculations, KPIs, filters unchanged
6. Archive, don't delete — all removed content goes to archive/

### 3.2 Layer Architecture (Frozen)

`
app.py (Entry) — Route dispatch, global state, filters
views/ (Presentation) — V1 wrappers, V2 implementations, shared, components
ui/ (Design System) — design_tokens, components, formatters
services/ (Business Logic) — auth, state, route, export, alerts, caching
utils/ (Data Pipeline) — loaders, filters, aggregations, calculations
config/ (Settings) — environment, paths, settings, users
`

### 3.3 Import Flow Rules

`
ALLOWED:
  views/* -> views/shared.py -> services/*
  views/* -> ui/*
  views/* -> utils/*
  app.py -> views/*, services/*, utils/*

FORBIDDEN:
  services/* -> views/*
  utils/* -> views/*
  ui/* -> services/*
  Any circular imports
  Wildcard imports from services/utils (except views/shared.py)
`

### 3.4 Naming Conventions

| Layer | Convention | Example |
|-------|-----------|---------|
| Views | render_<page>() function | render_labour(data) |
| Services | <service>_service.py | auth_service.py |
| Utils | <category>.py | loaders.py |
| UI Components | <component>.py | metrics.py |
| Tests | test_<feature>.py | test_golden_snapshot.py |
| Config | <setting>.py | settings.py |

---

## 4. Architecture Documentation

**Source:** docs/ directory

| Document | Lines | Purpose |
|----------|-------|---------|
| docs/ARCHITECTURE.md | 11 | Brief architecture overview |
| docs/FRAMEWORK.md | 41 | Framework selection guide |
| docs/DEPENDENCY_RULES.md | 13 | Layer dependency flow rules |
| docs/FOLDER_STRUCTURE.md | 16 | Canonical directory layout |
| docs/KNOWN_ISSUES.md | 19 | Known issues tracking |
| docs/KNOWN_LIMITATIONS.md | 28 | System limitations |
| docs/PERFORMANCE_BASELINE.md | 42 | Performance benchmarks |
| docs/PERFORMANCE_PROFILE.md | 87 | Performance profiling data |
| docs/UAT_CHECKLIST.md | 56 | User acceptance testing checklist |
| docs/UAT_GUIDE.md | 36 | UAT execution guide |
| docs/UAT_SIGNOFF.md | 58 | UAT sign-off document |
| docs/CHANGELOG.md | 13 | Change log |
| docs/RELEASE_NOTES_v1.0.0.md | 30 | Release notes |
| docs/MIGRATION_GUIDE.md | 29 | Migration guide |
| docs/DEPLOYMENT_CHECKLIST.md | 31 | Deployment checklist |
| docs/SECURITY_MIGRATION.md | 15 | Security migration notes |

---

## 5. Engineering Playbook

**Source:** WSMIS_ENGINEERING_PLAYBOOK.md

### 5.1 Development Workflow

1. Read — Understand the task specification
2. Plan — Identify exact files to modify
3. Implement — Make minimal, targeted changes
4. Verify — Run tests (38/38 must pass)
5. Commit — One commit per task with descriptive message

### 5.2 Commit Message Format

`
fix(TASK-0N): <description>
`

### 5.3 Testing Requirements

- 38/38 tests must pass after every change
- Golden snapshot regression validates all 71 KPI baseline keys
- Zero KPI differences, zero visual regressions
- Manual verification of affected dashboards

### 5.4 Code Quality

- Linting: ruff (planned for TASK-07)
- Type hints: Not required for Phase 1
- Dead code: Remove when encountered (TASK-07B)

### 5.5 Architecture Compliance

- No wildcard imports from services/utils (except views/shared.py)
- No circular imports
- No new architecture patterns — follow existing patterns
- Preserve import flow — views -> services -> utils (one direction)

### 5.6 Error Handling

- safe_render decorator — wraps all dashboard rendering functions
- DataLoadError — raised for data loading failures
- FilterError — raised for filter application failures
- Graceful degradation — show user-friendly error messages

---

## 6. Architecture Review Board Resolutions

**Source:** TASK_11A_Architecture_Alignment_Report.md, TASK_12_Architecture_Realignment_Report.md

### 6.1 Resolution: Dashboard Taxonomy Alignment

**Issue:** TASK-11 placed 6 Commercial modules in views/performance/ instead of views/commercial/.

**Decision:** Move 6 modules from views/performance/ to views/commercial/ per approved PRD taxonomy.

**Resolution:** Completed in TASK-12. All 38 tests passed, zero KPI differences.

### 6.2 Resolution: Final Dashboard Taxonomy

| Dashboard | Domain | View Modules |
|-----------|--------|-------------|
| Executive | executive | views/executive/ — cockpit, overview, executive |
| Commercial | commercial | views/commercial/ — labour, parts_executive, parts_detail, margin, discount, sales_mix |
| Operations | operations | views/operations/ — advisor, advisor_mom, internal_audit, audit_intelligence, reports |
| Performance | performance | views/performance/ — locations, targets |
| Financial | financial | views/financial/ — pnl, expense |
| Trend | trend | views/trend/ — trends |
| Leakage Centre | commercial | views/leakage.py (direct V1) |

### 6.3 Resolution: V1/V2 Coexistence

**Decision:** V1 wrapper files (views/<page>.py) remain as thin delegation wrappers. V2 implementations live in domain-specific subdirectories.

**Implementation:**
- V1 wrappers: 6-line files that import from V2 modules
- V2 implementations: Full dashboard code in views/<domain>/
- LEGACY_NAV = True ensures V1 sidebar navigation is active by default

---

## 7. Dashboard Taxonomy (Frozen)

### 7.1 Complete Route Table

| # | Page Name | Route Key | View Module | Domain |
|---|-----------|-----------|-------------|--------|
| 1 | Overview | Overview | views/overview.py | executive |
| 2 | Executive | Executive | views/executive.py | executive |
| 3 | Cockpit | Cockpit | views/cockpit.py | executive |
| 4 | Labour | Labour | views/labour.py | commercial |
| 5 | Parts Executive | parts_executive | views/parts_executive.py | commercial |
| 6 | Parts Detail | parts_detail | views/parts_detail.py | commercial |
| 7 | Margin | Margin | views/margin.py | commercial |
| 8 | Discounts | Discounts | views/discount.py | commercial |
| 9 | Leakage Centre | Leakage Center | views/leakage.py | commercial |
| 10 | Sales Mix | Sales Mix | views/sales_mix.py | commercial |
| 11 | Advisors | Advisors | views/advisor.py | operations |
| 12 | Advisor MoM | Advisor MoM | views/advisor_mom.py | operations |
| 13 | Locations | Locations | views/locations.py | performance |
| 14 | Trends | Trends | views/trends.py | trend |
| 15 | Targets | Targets | views/targets.py | performance |
| 16 | Reports | Reports | views/reports.py | operations |
| 17 | Expense Analysis | Expense Analysis | views/expense.py | financial |
| 18 | Profit & Loss | Profit & Loss | views/pnl.py | financial |
| 19 | Internal Audit | Internal Audit | views/internal_audit.py | operations |
| 20 | Audit Intelligence | Audit Intelligence | views/audit_intelligence.py | operations |
| 21 | System Health | System Health | views/system_health.py | ops |

### 7.2 Page Capabilities (from app.py)

`python
PAGE_CAPABILITIES = {
    "Overview": {"auth": True},
    "Executive": {"auth": True},
    "Cockpit": {"auth": True},
    "Labour": {"auth": True},
    "parts_executive": {"auth": True},
    "parts_detail": {"auth": True},
    "Margin": {"auth": True},
    "Discounts": {"auth": True},
    "Leakage Center": {"auth": True},
    "Sales Mix": {"auth": True},
    "Advisors": {"auth": True},
    "Advisor MoM": {"auth": True},
    "Locations": {"auth": True},
    "Trends": {"auth": True},
    "Targets": {"auth": True},
    "Reports": {"auth": True},
    "Expense Analysis": {"auth": True},
    "Profit & Loss": {"auth": True},
    "Internal Audit": {"auth": True},
    "System Health": {"auth": True},
    "Audit Intelligence": {"auth": True},
}
`

### 7.3 V2 URL Slugs (from app.py)

`python
PAGE_SLUGS = {
    "cockpit": "Cockpit",
    "overview": "Overview",
    "executive": "Executive",
    "labour": "Labour",
    "parts-executive": "parts_executive",
    "parts-detail": "parts_detail",
    "margin": "Margin",
    "discounts": "Discounts",
    "sales-mix": "Sales Mix",
    "leakage-centre": "Leakage Center",
    "advisors": "Advisors",
    "advisor-mom": "Advisor MoM",
    "locations": "Locations",
    "targets": "Targets",
    "trends": "Trends",
    "reports": "Reports",
    "expense": "Expense Analysis",
    "pnl": "Profit & Loss",
    "internal-audit": "Internal Audit",
    "audit-intelligence": "Audit Intelligence",
    "system-health": "System Health",
}
`

---

## 8. Dependency Rules

### 8.1 Allowed Import Flow

`
app.py -> views/*.py, views/shared.py, services/*.py, utils/*.py, ui/*.py
views/*.py -> views/shared.py, views/components/*, views/<domain>/*, services/*, utils/*, ui/*
services/*.py -> utils/*, ui/*.py (design tokens only)
utils/*.py -> (no cross-layer imports)
ui/*.py -> (no cross-layer imports)
`

### 8.2 Forbidden Import Patterns

`
services/*.py -> views/*
utils/*.py -> views/*
ui/* -> services/*
Any circular imports
Wildcard imports from services/utils (except views/shared.py)
views/*.py -> app.py
`

### 8.3 Legacy Files (Root Level)

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| exp_report.py | 2081 | Legacy expense report | Standalone, pre-V2 |
| pnl_report.py | 1322 | Legacy P&L report | Standalone, pre-V2 |
| revenue_leakage_v31.py | 871 | Legacy revenue leakage | Standalone, pre-V2 |

**Note:** These legacy files are standalone Streamlit apps, not part of the main WSMIS application.
