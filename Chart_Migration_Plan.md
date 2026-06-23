# Chart Component Migration Plan

**Document Owner:** Engineering Director, WSMIS v2
**Branch:** `feature/v2-architecture`
**Version:** v1.0.0-rc1
**Date:** 2026-06-22
**Status:** PLANNING — No code changes yet

---

## Executive Summary

**Objective:** Migrate from legacy `ui/components/charts.py` to canonical `views/components/chart_engine.py` and enable safe deletion of the legacy file.

**Current State:** 35+ runtime references across 11 production files prevent deletion.

**Key Finding:** The legacy `ChartCard` in `ui/components/charts.py` is functionally identical to `ChartEngine.render_card` in the canonical implementation. Migration can be largely automated.

**Estimated Effort:** 2-3 hours across 3 migration batches.

**Risk Level:** LOW — Direct 1:1 replacement with identical functionality.

---

## 1. Dependency Analysis

### 1.1 Component Architecture

```
LEGACY (to be deleted):
├── ui/components/charts.py
│   ├── ChartCard() → calls ChartEngine.apply_chart()
│   └── Exported via ui/components/__init__.py

CANONICAL (target):
├── views/components/chart_engine.py
│   ├── ChartEngine.apply_chart() — styling function
│   └── ChartEngine.render_card() — card wrapper (identical to legacy ChartCard)
│   └── Exported via views/shared.py
```

### 1.2 Dependency Graph

```
Production Views (8 files)
├── views/advisor.py
├── views/advisor_mom.py
├── views/cockpit.py
├── views/margin.py
├── views/overview.py
├── views/sales_mix.py
├── views/discount.py
├── views/labour.py
├── views/leakage.py
├── views/parts_detail.py
├── views/parts_executive.py
└── views/targets.py
    ↓
views/shared.py (import hub)
    ↓
ui/components/__init__.py (export hub)
    ↓
ui/components/charts.py (LEGACY - to delete)
```

### 1.3 Reference Classification

#### ChartCard References (23+ calls)

| File | Line(s) | Type | Migration Feasibility |
|------|---------|------|----------------------|
| `views/shared.py` | 33 | Import | AUTOMATIC — change import source |
| `views/advisor.py` | 110, 207 | Call | AUTOMATIC — replace with ChartEngine.render_card |
| `views/advisor_mom.py` | 93, 132, 179 | Call | AUTOMATIC — replace with ChartEngine.render_card |
| `views/cockpit.py` | 212, 216 | Call | AUTOMATIC — replace with ChartEngine.render_card |
| `views/margin.py` | 64, 115, 124, 131, 136 | Call | AUTOMATIC — replace with ChartEngine.render_card |
| `views/overview.py` | 147, 158, 168, 180 | Call | AUTOMATIC — replace with ChartEngine.render_card |
| `views/sales_mix.py` | 82, 86, 90, 94, 101 | Call | AUTOMATIC — replace with ChartEngine.render_card |
| `ui/components/charts.py` | 6 | Definition | DELETE — entire file |
| `ui/components/__init__.py` | 7, 22 | Export | DELETE — remove from export list |

#### apply_chart References (12+ calls)

| File | Line(s) | Type | Migration Feasibility |
|------|---------|------|----------------------|
| `ui/helpers.py` | 138 | Call | MANUAL — review context, may keep as-is |
| `ui/components/charts.py` | 13 | Call | DELETE — part of file deletion |
| `views/discount.py` | 496, 669 | Call | MANUAL — review context |
| `views/labour.py` | 414, 415, 458 | Call | MANUAL — review context |
| `views/leakage.py` | 133, 148 | Call | MANUAL — review context |
| `views/parts_detail.py` | 141 | Call | MANUAL — review context |
| `views/parts_executive.py` | 301, 339 | Call | MANUAL — review context |
| `views/targets.py` | 139 | Call | MANUAL — review context |
| `views/components/chart_engine.py` | 11, 86 | Definition | KEEP — canonical implementation |

---

## 2. Migration Strategy

### 2.1 Migration Batches

#### BATCH 1: Import Chain Migration (LOW RISK)
**Objective:** Update import paths to bypass legacy file.

**Files:** 1
- `views/shared.py`

**Changes:**
```python
# BEFORE:
from ui.components import KPIGrid, MetricCard, ChartCard, TableCard

# AFTER:
from ui.components import KPIGrid, MetricCard, TableCard
# ChartCard now available via ChartEngine.render_card
```

**Effort:** 5 minutes

**Verification:** py_compile views/shared.py

---

#### BATCH 2: ChartCard Call Migration (LOW RISK)
**Objective:** Replace all ChartCard calls with ChartEngine.render_card.

**Files:** 8
- `views/advisor.py`
- `views/advisor_mom.py`
- `views/cockpit.py`
- `views/margin.py`
- `views/overview.py`
- `views/sales_mix.py`

**Pattern:**
```python
# BEFORE:
ChartCard("Title", fig, height=400, description="Desc")

# AFTER:
ChartEngine.render_card("Title", fig, height=400, description="Desc")
```

**Effort:** 30 minutes (automated find-replace with verification)

**Verification:** 
- py_compile all modified files
- pytest for affected dashboards

---

#### BATCH 3: apply_chart Review (MEDIUM RISK)
**Objective:** Review and potentially migrate direct apply_chart calls.

**Files:** 7
- `ui/helpers.py`
- `views/discount.py`
- `views/labour.py`
- `views/leakage.py`
- `views/parts_detail.py`
- `views/parts_executive.py`
- `views/targets.py`

**Analysis Required:**
- Determine if calls are to legacy or canonical ChartEngine
- If calling canonical ChartEngine.apply_chart → NO CHANGE NEEDED
- If calling via other path → MIGRATE to ChartEngine.apply_chart

**Effort:** 60 minutes (manual review per file)

**Verification:**
- py_compile all modified files
- pytest for affected dashboards
- Visual regression test for chart rendering

---

#### BATCH 4: Legacy File Deletion (ZERO RISK)
**Objective:** Delete legacy files after verification.

**Files:** 2
- `ui/components/charts.py` (DELETE)
- `ui/components/__init__.py` (REMOVE ChartCard export)

**Changes:**
```python
# ui/components/__init__.py
# REMOVE from __all__ list: "ChartCard"
# REMOVE from imports: from .charts import ChartCard
```

**Effort:** 5 minutes

**Verification:**
- Full pytest suite (38/38 tests)
- Import verification: no references to ui.components.charts
- Grep verification: zero ChartCard references outside canonical location

---

### 2.2 Migration Order

1. **BATCH 1** — Import chain (foundation)
2. **BATCH 2** — ChartCard calls (bulk migration)
3. **BATCH 3** — apply_chart review (manual verification)
4. **BATCH 4** — File deletion (cleanup)

**Total Estimated Time:** 2-3 hours

---

## 3. Rollback Strategy

### 3.1 Per-Batch Rollback

Each batch can be independently rolled back via `git revert`:

- **BATCH 1:** Revert `views/shared.py` change
- **BATCH 2:** Revert all 8 view file changes
- **BATCH 3:** Revert all 7 view file changes
- **BATCH 4:** Restore deleted files via `git checkout`

### 3.2 Full Rollback

If critical issues arise after all batches:

```bash
git revert <commit-range>
# This restores all files to pre-migration state
```

### 3.3 Rollback Triggers

- Any pytest failure
- Any ImportError on dashboard load
- Visual regression in chart rendering
- Performance degradation > 10%

---

## 4. Final Deletion Criteria

**Pre-deletion Checklist:**

- [ ] All 4 migration batches completed
- [ ] 38/38 pytest tests passing
- [ ] Zero references to `ui.components.charts` in codebase
- [ ] Zero references to `ChartCard` outside `views/components/chart_engine.py`
- [ ] All 19 dashboards load successfully
- [ ] Visual verification of chart rendering on 3 sample dashboards
- [ ] No ImportError on any import path
- [ ] `ui/components/charts.py` deleted
- [ ] `ui/components/__init__.py` updated (ChartCard removed)

**Post-deletion Verification:**

```bash
# Verify zero references
grep -r "ui.components.charts" . --exclude-dir=.git
grep -r "from ui.components import.*ChartCard" . --exclude-dir=.git
grep -r "ChartCard(" . --exclude-dir=.git --exclude="chart_engine.py"

# Expected: Zero matches
```

---

## 5. Risk Assessment

### 5.1 Risk Matrix

| Batch | Risk Level | Impact | Likelihood | Mitigation |
|-------|------------|--------|------------|------------|
| BATCH 1 | LOW | Import error only | LOW | py_compile verification |
| BATCH 2 | LOW | Visual regression | LOW | Identical function signature |
| BATCH 3 | MEDIUM | Chart styling change | MEDIUM | Manual review per file |
| BATCH 4 | ZERO | N/A | N/A | Post-deletion verification |

### 5.2 Key Risks

1. **apply_chart Context Differences**
   - **Risk:** Some calls may rely on legacy-specific behavior
   - **Mitigation:** Manual review in BATCH 3
   - **Fallback:** Keep legacy apply_chart if behavior differs

2. **Import Chain Breakage**
   - **Risk:** views/shared.py change may break downstream imports
   - **Mitigation:** py_compile after BATCH 1
   - **Fallback:** Revert BATCH 1 immediately

3. **Visual Regression**
   - **Risk:** Chart rendering differences between legacy and canonical
   - **Mitigation:** Visual verification on sample dashboards
   - **Fallback:** Revert affected batch

---

## 6. Success Metrics

### 6.1 Technical Metrics

- 38/38 pytest tests passing
- Zero ImportError on any dashboard
- Zero references to legacy file
- All 19 dashboards load successfully

### 6.2 Quality Metrics

- No visual regression in chart rendering
- No performance degradation
- Code reduction: -22 lines (charts.py deleted)
- Import simplification: 1 import removed from shared.py

---

## 7. Post-Migration Cleanup

### 7.1 Documentation Updates

- Update `WSMIS_Phase1_Implementation_Summary.md` with TASK-06 completion
- Update `WSMIS_Implementation_Roadmap.md` to reflect actual migration complexity
- Archive this migration plan to `docs/migration/`

### 7.2 Code Cleanup

- Remove any TODO comments referencing legacy charts
- Update any docstrings mentioning ChartCard from ui.components
- Verify no stale imports in __pycache__

---

## 8. Approval Gates

### Gate 1: Pre-Migration
- [ ] Dependency analysis approved
- [ ] Migration plan approved
- [ ] Rollback strategy documented

### Gate 2: Post-BATCH 2
- [ ] py_compile passes
- [ ] pytest passes for affected dashboards
- [ ] No ImportError

### Gate 3: Post-BATCH 3
- [ ] All apply_chart calls reviewed
- [ ] Manual verification complete
- [ ] pytest passes (38/38)

### Gate 4: Post-Deletion
- [ ] Zero references to legacy file
- [ ] All dashboards load
- [ ] Visual verification complete
- [ ] Documentation updated

---

## 9. Appendix

### 9.1 File Inventory

**Files to Modify:** 16
- 1 import file (views/shared.py)
- 8 view files (ChartCard calls)
- 7 view files (apply_chart review)
- 2 component files (deletion/export removal)

**Files to Delete:** 1
- ui/components/charts.py

**Lines of Code Impact:**
- Added: 0
- Modified: ~30 (import changes)
- Deleted: 22 (charts.py)
- Net: -22 lines

### 9.2 Test Coverage

**Existing Tests:** 38 pytest tests
- All should pass post-migration
- No new tests required (functionality unchanged)

**Manual Tests Required:**
- Visual verification on 3 dashboards (Cockpit, Margin, Overview)
- Chart rendering comparison (before/after screenshots)

---

**Document Status:** READY FOR APPROVAL
**Next Step:** Await approval to begin BATCH 1
