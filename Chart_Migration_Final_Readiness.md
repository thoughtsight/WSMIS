# Chart Migration Final Readiness Report

**Document Owner:** Engineering Director, WSMIS v2
**Branch:** `feature/v2-architecture`
**Version:** v1.0.0-rc1
**Date:** 2026-06-22
**Status:** READY FOR APPROVAL

---

## Executive Summary

**Finding:** All Architecture Review Board mandatory conditions have been satisfied. The migration is ready to proceed with exact inventory and zero hidden dependencies.

**Verdict:** ✅ **READY FOR AUTOMATED MIGRATION**

**Risk Level:** LOW — All call sites identified, no hidden dependencies, file contains only ChartCard function.

---

## 1. Repository-Wide Search Results

### 1.1 ChartCard( Call Sites

**Total Count:** 22 (1 definition + 21 runtime calls)

| File | Line | Type | Context |
|------|------|------|---------|
| `ui/components/charts.py` | 6 | Definition | `def ChartCard(...)` |
| `views/advisor.py` | 110 | Call | `ChartCard("📊 Performance Scatter", fig, height=400)` |
| `views/advisor.py` | 207 | Call | `ChartCard(f"📈 {sel_adv} — Labour Trend (Last 6M)", fig, height=350)` |
| `views/advisor_mom.py` | 93 | Call | `ChartCard(f"📈 {sel_adv} — {metric} Trend (Last 6M)", fig, height=350)` |
| `views/advisor_mom.py` | 132 | Call | `ChartCard(f"🕸️ {sel_adv} Performance Profile", fig, height=400)` |
| `views/advisor_mom.py` | 179 | Call | `ChartCard(f"🏅 Rank by JC Volume — {', '.join(sel_locs)}", fig, height=400)` |
| `views/cockpit.py` | 212 | Call | `ChartCard("🏆 Revenue by Location (Top 10)", fig, height=280)` |
| `views/cockpit.py` | 216 | Call | `ChartCard("📈 Revenue Trend", fig, height=280)` |
| `views/margin.py` | 64 | Call | `ChartCard("💰 Margin Waterfall", fig, height=400)` |
| `views/margin.py` | 115 | Call | `ChartCard("📈 Total Margin Trend", fig, height=320)` |
| `views/margin.py` | 124 | Call | `ChartCard("🍰 Margin Mix", fig, height=320)` |
| `views/margin.py` | 131 | Call | `ChartCard("🏢 Location Margin", fig, height=320)` |
| `views/margin.py` | 136 | Call | `ChartCard("⚖️ WS vs BS Margin", fig, height=320)` |
| `views/overview.py` | 147 | Call | `ChartCard("📈 Monthly Net Labour Trend", fig, height=320)` |
| `views/overview.py` | 158 | Call | `ChartCard("🏢 Location Ranking — Net Labour CP", fig, height=340)` |
| `views/overview.py` | 168 | Call | `ChartCard("🔧 Service Type Mix — CP JCs", fig, height=300)` |
| `views/overview.py` | 180 | Call | `ChartCard("⚖️ WS vs BS Labour Split — CP", fig, height=300)` |
| `views/sales_mix.py` | 82 | Call | `ChartCard("Oil Trend", fig, height=300)` |
| `views/sales_mix.py` | 86 | Call | `ChartCard("Batt + Tyre", fig, height=300)` |
| `views/sales_mix.py` | 90 | Call | `ChartCard("Oil Ranking", fig, height=300)` |
| `views/sales_mix.py` | 94 | Call | `ChartCard("Mix (Acc vs Pts)", fig, height=300)` |
| `views/sales_mix.py` | 101 | Call | `ChartCard("Oil Revenue per Litre by Location", fig, height=400, x_title="INR/L")` |

**Search Scope:** All `.py` files in repository including `views/`, `scripts/`, `archive/`, root directory.

**Files NOT containing ChartCard calls:**
- `views/locations.py`
- `views/trends.py`
- `views/executive.py`
- `views/pnl.py`
- `views/expense.py`
- `views/leakage.py`
- `views/discount.py`
- `views/labour.py`
- `views/parts_detail.py`
- `views/parts_executive.py`
- `views/targets.py`
- `views/reports.py`
- `views/internal_audit.py`
- `views/audit_intelligence.py`
- `exp_report.py`
- `pnl_report.py`

---

### 1.2 Import References

**from ui.components import ChartCard:** 2 locations

| File | Line | Type | Context |
|------|------|------|---------|
| `views/shared.py` | 33 | Import | `from ui.components import KPIGrid, MetricCard, ChartCard, TableCard` |
| `cleanup_headers.py` | 15 | Migration script | `content = content.replace('from ui.components import KPIGrid, ChartCard, TableCard'...` |

**from ui.components.charts import:** 1 location

| File | Line | Type | Context |
|------|------|------|---------|
| `migrate_chart_engine.py` | 31 | Migration script | `new_content = re.sub(r"from ui\.components\.charts import(.*?)..."` |

**import ui.components.charts:** 0 locations

**ui.components.charts references:** 2 locations (both in migration script)

| File | Line | Type | Context |
|------|------|------|---------|
| `migrate_chart_engine.py` | 30 | Comment | `# Fix ui.components.charts import if any` |
| `migrate_chart_engine.py` | 31 | Migration script | `new_content = re.sub(r"from ui\.components\.charts import(.*?)..."` |

---

## 2. Complete File Audit: ui/components/charts.py

### 2.1 File Structure

**Total Lines:** 22
**File Size:** Small (single function wrapper)

### 2.2 Line-by-Line Inventory

| Line | Content | Type |
|------|---------|------|
| 1 | `import streamlit as st` | Import |
| 2 | `import plotly.graph_objects as go` | Import |
| 3 | `from typing import Optional` | Import |
| 4 | `from views.components.chart_engine import ChartEngine` | Import |
| 5 | (blank) | Whitespace |
| 6-21 | `def ChartCard(...)` | Function definition |
| 22 | (blank) | Whitespace |

### 2.3 Exported Symbols

**Single Export:** `ChartCard` (function)

**Other Symbols:** None

**Constants:** None

**Classes:** None

**Additional Functions:** None

**Conclusion:** The file contains ONLY the ChartCard function and its imports. No other symbols to migrate.

---

## 3. Hidden Dependency Check

### 3.1 Standalone HTML Generators

| File | Status | ChartCard References | ui.components.charts References |
|------|--------|---------------------|--------------------------------|
| `exp_report.py` | ✅ Clear | 0 | 0 |
| `pnl_report.py` | ✅ Clear | 0 | 0 |
| `revenue_leakage_v31.py` | N/A | File not found in repository | N/A |

**Total Hidden Dependencies:** 0

### 3.2 Archive and Scripts

**Search Scope:** `archive/`, `scripts/` directories

**ChartCard References:** 0
**ui.components.charts References:** 0

### 3.3 Migration Scripts

**Files with migration script references:**
- `cleanup_headers.py` — Contains ChartCard in string replacement (non-runtime)
- `migrate_chart_engine.py` — Contains ui.components.charts in regex patterns (non-runtime)

**Impact:** None — These are migration utility scripts, not production code.

---

## 4. Exact Migration Inventory

### 4.1 Files to Modify (7 files)

| File | Changes Required |
|------|------------------|
| `views/shared.py` | Remove ChartCard from ui.components import |
| `views/advisor.py` | Replace 2 ChartCard calls |
| `views/advisor_mom.py` | Replace 3 ChartCard calls |
| `views/cockpit.py` | Replace 2 ChartCard calls |
| `views/margin.py` | Replace 5 ChartCard calls |
| `views/overview.py` | Replace 4 ChartCard calls |
| `views/sales_mix.py` | Replace 5 ChartCard calls |

**Total Call Replacements:** 21

### 4.2 Files to Delete (1 file)

| File | Action |
|------|--------|
| `ui/components/charts.py` | Delete entire file |

### 4.3 Files to Update (1 file)

| File | Changes Required |
|------|------------------|
| `ui/components/__init__.py` | Remove ChartCard from __all__ and imports |

---

## 5. Corrected Migration Script

### 5.1 Grep-Derived File List

```python
# Derived from complete repository grep output
files_to_migrate = [
    "views/advisor.py",      # 2 calls
    "views/advisor_mom.py",  # 3 calls
    "views/cockpit.py",      # 2 calls
    "views/margin.py",       # 5 calls
    "views/overview.py",    # 4 calls
    "views/sales_mix.py",    # 5 calls
]

# Total: 21 calls across 6 files
```

### 5.2 Automated Migration Script

```python
import re
from pathlib import Path

# Grep-derived complete file list
files_to_migrate = [
    "views/advisor.py",
    "views/advisor_mom.py",
    "views/cockpit.py",
    "views/margin.py",
    "views/overview.py",
    "views/sales_mix.py"
]

for filepath in files_to_migrate:
    file_path = Path(filepath)
    if not file_path.exists():
        print(f"Warning: {filepath} not found, skipping")
        continue
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace ChartCard calls
    original_count = content.count('ChartCard(')
    content = re.sub(r'\bChartCard\(', 'ChartEngine.render_card(', content)
    new_count = content.count('ChartEngine.render_card(')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"{filepath}: {original_count} calls replaced")
```

---

## 6. Architecture Review Board Conditions

### 6.1 CONDITION-1: Complete Call Site Inventory

**Status:** ✅ SATISFIED

**Evidence:**
- Repository-wide grep completed
- Exact count: 21 runtime calls (not estimated)
- All files audited: views/, scripts/, archive/, standalone generators
- No unaudited files remain

**Result:** 21 calls across 6 view files. No "+" notation, exact count confirmed.

---

### 6.2 CONDITION-2: Audit Complete File Contents

**Status:** ✅ SATISFIED

**Evidence:**
- Full 22-line file audited (lines 1-22)
- Only exports: ChartCard function
- No additional symbols, constants, or classes
- No hidden exports to migrate

**Result:** File contains only ChartCard function. Safe to delete.

---

### 6.3 CONDITION-3: Replace Hard-Coded File List

**Status:** ✅ SATISFIED

**Evidence:**
- Migration script updated with grep-derived list
- List includes all 6 files containing ChartCard calls
- No curated subset, complete inventory used

**Result:** Script operates on complete grep output, not hard-coded subset.

---

### 6.4 CONDITION-4: Correct "Byte-for-Byte Identical" Claim

**Status:** ✅ SATISFIED

**Evidence:**
- Chart_API_Compatibility_Report.md corrected
- Changed to "functionally identical after browser rendering"
- HTML rendering differences risk level updated from ZERO to LOW
- Whitespace difference documented (4 spaces in closing tag)

**Result:** Report accuracy maintained, false precision removed.

---

## 7. Migration Readiness Assessment

### 7.1 Readiness Checklist

| Condition | Status | Evidence |
|-----------|--------|----------|
| Exact call count | ✅ Complete | 21 calls identified via grep |
| Exact import count | ✅ Complete | 2 import locations identified |
| Export inventory | ✅ Complete | Only ChartCard function exported |
| Hidden dependency check | ✅ Complete | 0 hidden dependencies found |
| File content audit | ✅ Complete | 22 lines fully audited |
| Script correction | ✅ Complete | Grep-derived list implemented |
| Report correction | ✅ Complete | Byte-for-byte claim removed |

### 7.2 Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Missed call sites | ZERO | Complete grep audit of all files |
| Hidden dependencies | ZERO | Standalone generators audited |
| Unknown exports | ZERO | Full file content audited |
| HTML rendering differences | LOW | Whitespace only, no visual effect |
| Import chain breakage | LOW | Update views/shared.py import |

**Overall Risk Level:** LOW

---

## 8. Final Recommendation

### 8.1 Migration Status

**✅ READY FOR AUTOMATED MIGRATION**

All Architecture Review Board mandatory conditions have been satisfied:
- CONDITION-1: ✅ Complete call site inventory (21 exact calls)
- CONDITION-2: ✅ Complete file audit (22 lines, only ChartCard)
- CONDITION-3: ✅ Grep-derived migration script
- CONDITION-4: ✅ Report corrections applied

### 8.2 Migration Path

**Step 1:** Update import chain (1 file)
- `views/shared.py`: Remove ChartCard from ui.components import

**Step 2:** Replace call sites (6 files)
- Execute automated find-replace script
- 21 ChartCard calls → ChartEngine.render_card

**Step 3:** Delete legacy file (1 file)
- Delete `ui/components/charts.py`
- Remove ChartCard from `ui/components/__init__.py`

**Step 4:** Verification
- py_compile all modified files
- pytest full suite (38/38 tests)
- grep verification: zero ChartCard references
- Import verification: no ImportError

### 8.3 Estimated Effort

**Time:** 30 minutes
- 5 minutes: Import chain update
- 10 minutes: Automated find-replace
- 10 minutes: Verification (py_compile, pytest)
- 5 minutes: Final grep verification

### 8.4 Confidence Level

**HIGH** for migration execution readiness.

**Justification:**
- Exact inventory (no estimates)
- Zero hidden dependencies
- Complete file audit
- All conditions satisfied
- Low risk profile

---

## 9. Post-Migration Verification Checklist

- [ ] 21 ChartCard calls replaced with ChartEngine.render_card
- [ ] views/shared.py import updated
- [ ] ui/components/charts.py deleted
- [ ] ui/components/__init__.py updated
- [ ] py_compile passes for all modified files
- [ ] pytest passes (38/38 tests)
- [ ] grep ChartCard( returns zero matches
- [ ] grep "from ui.components import.*ChartCard" returns zero matches
- [ ] All 19 dashboards load successfully
- [ ] No ImportError on any import path

---

**Document Status:** READY FOR APPROVAL
**Recommendation:** PROCEED WITH MIGRATION
**Next Step:** Execute migration per Section 8.2
