# Visual Restoration Report

**Date:** 2026-06-22
**Session:** Sonnet 4.6 Review — Approved Visual Restoration Items
**Files Modified:** 3

---

## 1. Remove `.kpi-card` override from `inject_responsive_css()`

**File:** `views/dashboard_common.py:29`

**Before:**
```css
.kpi-card { height: 140px; display: flex; flex-direction: column; justify-content: space-between; }
```

**After:** Removed. The base `.kpi-card` in `static/style.css:166-174` now governs:
```css
.kpi-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-4) var(--space-5);
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.2s ease;
  height: 100%;
}
```

**Impact:** KPI cards no longer forced to fixed 140px height. They now use `height: 100%` from the base CSS, allowing natural content-driven sizing within their grid column.

---

## 2. Remove `.kpi-value` font-weight override

**File:** `views/dashboard_common.py:24,27`

**Before:**
```css
/* Global override */
.kpi-value { font-weight: 800 !important; }
/* Large-screen override */
@media (min-width: 1800px) {
    .kpi-value { font-size: var(--type-2xl) !important; font-weight: 800 !important; }
}
```

**After:** Both removed. The base `.kpi-value` in `static/style.css:185-191` now governs:
```css
.kpi-value {
  font-size: var(--type-xl);   /* 32px */
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.15;
  letter-spacing: -0.5px;
}
```

**Impact:** KPI values revert to design-system standard `font-weight: 700` (bold) instead of the overridden `800` (extrabold). Typography is now consistent with the design token system.

---

## 3. Replace Command Center section headers with `section_title()`

**File:** `views/executive/command_center.py` — 4 locations

**Before (identical pattern at lines 159, 232, 270, 343):**
```python
st.markdown(f"<div style='margin-top:{T.SPACE_6}px; margin-bottom:{T.SPACE_3}px; font-weight:700; font-size:{T.TYPE_LG}px;'>{title}</div>", unsafe_allow_html=True)
```

**After:**
```python
section_title("{title}")
```

**Section headers replaced:**
| Line | Header |
|------|--------|
| 159 | Alert & Opportunity Rail |
| 232 | Executive Brief |
| 270 | Workshop Intelligence |
| 343 | Deep Drill Navigation |

**Impact:** All 4 section headers now use the canonical `section_title()` function from `ui/components/core.py`, which renders `<div class="section-title">` with consistent design-token typography (`TYPE_MD` 16px, `font-weight: 600`, `SPACE_3` margin-bottom). Removes ~120 bytes of duplicated inline HTML per header.

---

## 4. Replace Alert Rail inline HTML styles with `.insight-card` classes

**File:** `views/executive/command_center.py` — `render_rail_cards()` + expander detail section

### 4a. Rail Cards (lines 163-181)

**Before:**
```python
def render_rail_cards(alert_list, color, border_color):
    ...
    card_html = f"""
    <div style="background:var(--color-surface);border:1px solid var(--color-border);border-left:3px solid {border_color};border-radius:{T.RADIUS_SM}px;padding:{T.SPACE_2}px {T.SPACE_3}px;margin-bottom:{T.SPACE_2}px;">
        <div style="font-weight:600;font-size:{T.TYPE_SM}px;color:var(--color-text-primary);">{rule}</div>
        <div style="font-size:{T.TYPE_XS}px;color:var(--color-text-secondary);margin-top:2px;">Impact: {impact}</div>
        <div style="font-size:{T.TYPE_XS}px;color:var(--color-text-tertiary);margin-top:2px;">Owner: 👤 {owner}</div>
    </div>
    """
```

**After:**
```python
def render_rail_cards(alert_list, modifier_class):
    ...
    card_html = f"""
    <div class="insight-card {modifier_class}">
        <div class="insight-title">{rule}</div>
        <div class="insight-stat">Impact: {impact}</div>
        <div class="insight-stat">Owner: 👤 {owner}</div>
    </div>
    """
```

**Modifier class mapping:**
| Alert Type | Before (color param) | After (CSS class) |
|------------|---------------------|-------------------|
| Critical | `T.COLOR_DANGER_FILL` | `neg` |
| Warning | `T.COLOR_WARNING_BG` | `warn` |
| Opportunity | `T.COLOR_PRIMARY` | `pos` |

**Empty state:** Replaced inline `style='font-size:13px; color:#1d1d1f;'` with `class="insight-stat"`.

**Overflow "+N More":** Replaced inline `style='font-size:11px; color:#6E6E73;'` with `class="insight-stat"`.

### 4b. Alert Detail Expander (lines 194-229)

**Before:** Fully inline-styled cards with hardcoded `background`, `border`, `border-left`, `border-radius`, `padding` and section labels with `style='font-size:{T.TYPE_MD}px; font-weight:600; color:...'`.

**After:** Cards use `class="insight-card {modifier_class}"` with `class="insight-title"` for rule/impact headers and `class="insight-stat"` for reason text. Section labels use `class="insight-title"` with inline `color` only.

**Impact:** ~400 bytes of inline CSS per card eliminated. Alert cards now inherit design system spacing, typography, and border treatment from `.insight-card`. Visual appearance matches the existing insight cards used throughout the app.

---

## 5. Add `pp_label` to all KPIGrid metric dictionaries

**File:** `views/executive/command_center.py:146-153`

**Before:** 6 KPI metrics with `cp`/`pp` raw values but no `pp_label`:
```python
{"label": "Total Revenue", "value": fmt_inr(cp_rev), "cp": cp_rev, "pp": pp_rev},
```

**After:** Same 6 metrics with `pp_label` for each:
```python
{"label": "Total Revenue", "value": fmt_inr(cp_rev), "cp": cp_rev, "pp": pp_rev, "pp_label": f"PP {fmt_inr(pp_rev)}"},
```

**pp_label values added:**
| Metric | pp_label |
|--------|----------|
| Total Revenue | `PP {fmt_inr(pp_rev)}` |
| Margin % | `PP {(pp_mar/pp_rev*100):.1f}%` |
| Total JCs | `PP {fmt_num(pp_jc)}` |
| Avg Labour / JC | `PP {fmt_inr(pp_avg_lab_jc)}` |
| Avg Discount % | `PP {pp_avg_disc:.1f}%` |
| Revenue vs Target | `Target 100%` |

**Impact:** KPI cards now display a human-readable previous-period reference value in the `.kpi-sub` area (rendered by `MetricCard` at `ui/components/metrics.py:17,31,49`), improving comparability without requiring users to mentally parse growth percentages.

---

## 6. Replace Deep Drill inline styles with `.nav-drill-card` CSS class

**File:** `views/executive/command_center.py:344-413` + `static/style.css`

### 6a. New CSS class in `static/style.css` (after `.insight-stat`):

```css
.nav-drill-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 12px 20px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  min-width: 140px;
  cursor: pointer;
}
.nav-drill-card:hover { box-shadow: var(--shadow-md); }
.nav-drill-icon { font-size: 24px; margin-bottom: 8px; }
.nav-drill-label { font-size: 14px; font-weight: 600; }
```

### 6b. Navigation cards (11 cards):

**Before (each card):**
```html
<div style="background:var(--color-surface);border:1px solid var(--color-border);border-radius:8px;padding:12px 20px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.05);min-width:140px;cursor:pointer;">
    <div style="font-size:24px;margin-bottom:8px;">👨‍🔧</div>
    <div style="font-size:14px;font-weight:600;">Labour</div>
</div>
```

**After (each card):**
```html
<div class="nav-drill-card"><div class="nav-drill-icon">👨‍🔧</div><div class="nav-drill-label">Labour</div></div>
```

**Impact:** ~200 bytes of inline CSS per card eliminated (11 cards = ~2.2KB total). Navigation cards now inherit design system tokens and gain a hover shadow effect. CSS class is reusable if navigation cards appear elsewhere.

---

## Test Results

| Suite | Result |
|-------|--------|
| Pytest | **39/39 passed** |
| Streamlit AppTest | **23/23 pages passed** (including `command_center`) |

**Zero regressions confirmed.**

---

## Summary

| # | Item | Files Changed | Lines Removed | Lines Added |
|---|------|--------------|---------------|-------------|
| 1 | Remove `.kpi-card` override | `dashboard_common.py` | 1 | 0 |
| 2 | Remove `.kpi-value` font-weight | `dashboard_common.py` | 3 | 0 |
| 3 | Section headers → `section_title()` | `command_center.py` | 4 | 4 |
| 4 | Alert Rail → `.insight-card` | `command_center.py` | ~30 | ~20 |
| 5 | Add `pp_label` to KPIGrid | `command_center.py` | 0 | 6 |
| 6 | Deep Drill → `.nav-drill-card` | `command_center.py` + `style.css` | ~70 | ~30 |
| **Total** | | **3 files** | **~108** | **~60** |

Net reduction: ~48 lines of inline CSS removed, replaced with 3 CSS class definitions and reusable component patterns.
