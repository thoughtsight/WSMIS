# WSMIS UI Audit Package
**Prepared for: Sonnet 4.6 Architecture Review**
**Date: 22 Jun 2026**

---

## Table of Contents

1. [Global CSS Architecture](#1-global-css-architecture)
2. [Colour Palette Audit](#2-colour-palette-audit)
3. [Typography System](#3-typography-system)
4. [Shared UI Components](#4-shared-ui-components)
5. [Executive Command Center Page](#5-executive-command-center-page)
6. [UI Helpers & Traffic Utilities](#6-ui-helpers--traffic-utilities)

---

## 1. Global CSS Architecture

**File:** `static/style.css` (560 lines)

### 1.1 Design Token Layer (`:root`)

All values are token-driven. No hardcoded hex below `:root`.

| Token Category | Tokens | Values |
|---|---|---|
| **Backgrounds** | `--color-app-bg` | `#F2F2F7` (soft neutral grey) |
| | `--color-surface` | `#FFFFFF` |
| | `--color-surface2` | `#F8F8FA` |
| **Borders** | `--color-border` | `#E5E5EA` |
| | `--color-border-sub` | `#F0F0F5` |
| | `--color-divider` | `#D4AF37` (gold — report header accent ONLY) |
| **Text** | `--color-text-primary` | `#1D1D1F` |
| | `--color-text-secondary` | `#6E6E73` |
| | `--color-text-tertiary` | `#8E8E93` |
| **Semantic** | `--color-primary` | `#0071E3` |
| | `--color-success` | `#1A7F37` (4.6:1 on white) |
| | `--color-danger` | `#CF222E` (5.5:1 on white) |
| | `--color-warning` | `#B45309` (4.7:1 on white) |
| **Badge BGs** | `--color-success-bg` | `#E8F9EE` |
| | `--color-danger-bg` | `#FFEBE9` |
| | `--color-warning-bg` | `#FFF3E0` |
| | `--color-info-bg` | `#E8F0FE` |
| **Typography** | `--font-family` | `'Inter', -apple-system, BlinkMacSystemFont, sans-serif` |
| | `--type-xs` through `--type-2xl` | 11px → 40px (Major Third 1.25× scale) |
| **Spacing** | `--space-1` through `--space-12` | 4px → 48px (4px base unit) |
| **Radius** | `--radius-sm` / `--radius-md` / `--radius-lg` | 6px / 8px / 10px |
| **Shadows** | `--shadow-xs` through `--shadow-lg` + `--shadow-inset` | 5-tier Apple-grade depth system |

### 1.2 Elevation System (5 Tiers)

```
--shadow-xs:    0 1px 2px rgba(0,0,0,0.04)
--shadow-sm:    0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)
--shadow-md:    0 4px 8px rgba(0,0,0,0.06), 0 2px 4px rgba(0,0,0,0.04)
--shadow-lg:    0 12px 24px rgba(0,0,0,0.08), 0 4px 8px rgba(0,0,0,0.04)
--shadow-inset: inset 0 1px 2px rgba(0,0,0,0.04)
```

### 1.3 Component Classes

| Class | Purpose | Shadow | Radius | Hover |
|---|---|---|---|---|
| `.kpi-card` | KPI metric card | `shadow-sm` | `radius-lg` (10px) | `shadow-md` + border `#D1D1D6` |
| `.section-card` | Section container | `shadow-sm` | `radius-lg` | `shadow-md` |
| `.insight-card` | Alert/finding card | `shadow-sm` | `radius-lg` | `shadow-md` |
| `.insight-card.pos` | Opportunity | Gradient green→white | `radius-lg` | `shadow-md` |
| `.insight-card.neg` | Critical alert | Gradient red→white | `radius-lg` | `shadow-md` |
| `.insight-card.warn` | Warning | Gradient amber→white | `radius-lg` | `shadow-md` |
| `.nav-drill-card` | Deep drill nav | `shadow-xs` | `radius-lg` | `shadow-md` + border primary + translateY(-1px) |
| `.report-header` | Universal header | `shadow-sm` | `radius-lg` | — |
| `.report-footer` | Universal footer | — | `radius-md` | — |
| `.filter-toolbar` | Filter bar | `shadow-xs` | `radius-lg` | — |
| `.ai-band` | AI narrative | `shadow-xs` | `radius-lg` | — |
| `.loc-card` | Location card | — | `radius-lg` | `shadow-md` + border `#D1D1D6` |
| `.forecast-card` | Forecast | `shadow-sm` | `radius-lg` | — |
| `.styled-table` | Data table | — | `radius-md` | row hover → `surface2` |

### 1.4 Badges

| Class | BG | Text | Used for |
|---|---|---|---|
| `.badge-pos` | `success-bg` | `success` | Positive growth |
| `.badge-neg` | `danger-bg` | `danger` | Negative growth |
| `.badge-new` | `info-bg` | `primary` | New location |
| `.badge-warn` | `warning-bg` | `warning` | Warning |
| `.badge-neutral` | `surface2` | `text-secondary` | No change |

### 1.5 Responsive Breakpoints

| Breakpoint | Behaviour |
|---|---|
| `≥1800px` | KPI value → `type-2xl` (40px), label → `type-sm` |
| `≤1400px` | 3+ columns → 48% flex |
| `≤1024px` | All columns → 48%; section-card/kpi-card compact padding; chart 100% |
| `≤768px` | All columns → 100%; KPI value → 20px |

### 1.6 Print Stylesheet

- Strips sidebar, header, footer, tabs, filter toolbar
- Forces white backgrounds, no shadows
- KPI value → 20pt, table → 11pt
- Page-break-inside: avoid on cards and table rows

### 1.7 Hardcoded Hex Audit

| Location | Value | Justified? |
|---|---|---|
| `:root` block | All design tokens | ✅ Source of truth |
| `.rh-confidential` | `#0A1B3F` | ✅ Dark badge — semantic (confidential tag) |
| `.report-footer` | `#0A1B3F` | ✅ Dark footer — semantic |
| `.rf-bottom` | `#D2D2D7` | ✅ Footer text on dark bg |
| `.filter-chip` border | `#B5D4F4` | ⚠️ Should reference a token |
| `.alert-banner` border | `#FFCCCB` | ⚠️ Should reference a token |
| `.neg-lab-alert` border-fill | `COLOR_DANGER_FILL` | ✅ Uses token |
| Radio pill active shadow | `rgba(0,113,227,0.25)` | ⚠️ Hardcoded primary alpha |
| `.loc-card:hover` border | `#D1D1D6` | ⚠️ Should reference a token |
| `.kpi-card:hover` border | `#D1D1D6` | ⚠️ Same as above — deduplicate |

**Recommendation:** Add `--color-border-hover: #D1D1D6` and `--color-info-border: #B5D4F4` tokens for the 4 hardcoded values.

---

## 2. Colour Palette Audit

### 2.1 Python Token Registry

**File:** `ui/design_tokens.py` (164 lines)

| Category | Token | Hex | WCAG Ratio on White |
|---|---|---|---|
| **Primary** | `COLOR_PRIMARY` | `#0071E3` | 4.6:1 ✅ |
| **Success** | `COLOR_SUCCESS` | `#1A7F37` | 4.6:1 ✅ |
| **Danger** | `COLOR_DANGER` | `#CF222E` | 5.5:1 ✅ |
| **Warning** | `COLOR_WARNING` | `#B45309` | 4.7:1 ✅ |
| **Fill (icons only)** | `COLOR_SUCCESS_FILL` | `#34C759` | ❌ 1.4:1 — NOT for text |
| | `COLOR_DANGER_FILL` | `#FF3B30` | ❌ 2.0:1 — NOT for text |

### 2.2 CSS ↔ Python Sync

| CSS Token | Python Token | Match |
|---|---|---|
| `--color-primary` | `COLOR_PRIMARY` | ✅ |
| `--color-success` | `COLOR_SUCCESS` | ✅ |
| `--color-danger` | `COLOR_DANGER` | ✅ |
| `--color-warning` | `COLOR_WARNING` | ✅ |
| `--color-text-primary` | `COLOR_TEXT_PRIMARY` | ✅ |
| `--color-text-secondary` | `COLOR_TEXT_SECONDARY` | ✅ |
| `--color-text-tertiary` | `COLOR_TEXT_TERTIARY` | ✅ |
| `--color-surface` | `COLOR_SURFACE` | ✅ |
| `--color-border` | `COLOR_BORDER` | ✅ |

### 2.3 Legacy Constants

**File:** `utils/constants.py`

| Constant | Values |
|---|---|
| `MP_COLORS` | `{"Workshop": "#0071E3", "Bodyshop": "#FF9500"}` — aligns with `T.COLOR_PRIMARY` and `T.C["orange"]` |
| `LOC_COLORS` | 15 location colours — mostly unique; `#0071E3` reused as default |

### 2.4 Semantic Fill Usage (Correct vs Incorrect)

| File | Usage | Correct? |
|---|---|---|
| `ui/helpers.py:192` | `_render_finding` — `COLOR_DANGER` as text on `COLOR_DANGER_BG` | ✅ |
| `views/executive/command_center.py:171-178` | Alert rail — `.insight-card.neg/.warn/.pos` classes | ✅ CSS classes handle it |
| `ui/components/core.py:121` | `AlertBanner` — `COLOR_DANGER` as text on `COLOR_DANGER_BG` | ✅ |
| `dashboard_common.py:219` | `style_margin_color` — hardcoded `#D97706` | ⚠️ Should use `T.COLOR_WARNING` |

---

## 3. Typography System

### 3.1 Scale (Major Third 1.25×, base 11px)

| Token | Size | Usage |
|---|---|---|
| `TYPE_XS` | 11px | Metadata, timestamps, badges, axis ticks |
| `TYPE_SM` | 12px | Table cells, axis labels, secondary labels |
| `TYPE_BASE` | 14px | Body text, insight cards, tooltips |
| `TYPE_MD` | 16px | Section headings, card subtitles |
| `TYPE_LG` | 20px | Page sub-headings |
| `TYPE_XL` | 32px | KPI values (platform standard) |
| `TYPE_2XL` | 40px | KPI hero on large screens |

### 3.2 Font Weights

| Weight | Value | Usage |
|---|---|---|
| `WEIGHT_REGULAR` | 400 | Body text |
| `WEIGHT_MEDIUM` | 500 | Secondary text, AI band |
| `WEIGHT_SEMIBOLD` | 600 | Labels, badges, table headers |
| `WEIGHT_BOLD` | 700 | KPI values, section titles, chart titles |
| `WEIGHT_EXTRABOLD` | 800 | Brand title, `.rh-client` |

### 3.3 CSS Class Typography Mapping

| CSS Class | Font Size | Weight | Color | Letter Spacing |
|---|---|---|---|---|
| `.kpi-label` | `type-xs` (11px) | 600 | `text-primary` | 0.8px uppercase |
| `.kpi-value` | `type-xl` (32px) | 700 | `text-primary` | -0.5px |
| `.kpi-sub` | `type-xs` (11px) | — | `text-secondary` | — |
| `.kpi-meta` | `type-xs` (11px) | — | `text-tertiary` | 0.2px |
| `.kpi-delta-pos` | `type-sm` (12px) | 700 | `success` | — |
| `.kpi-delta-neg` | `type-sm` (12px) | 700 | `danger` | — |
| `.section-title` | `type-md` (16px) | 700 | `text-primary` | -0.2px |
| `.insight-title` | `type-base` (14px) | 700 | `text-primary` | — |
| `.insight-stat` | `type-sm` (12px) | — | `text-primary` | — |
| `.rh-client` | `type-lg` (20px) | 800 | `text-primary` | -0.5px |
| `.rh-title` | `type-md` (16px) | 700 | `text-primary` | — |
| `.rh-period` | `type-sm` (12px) | — | `text-secondary` | — |
| `.brand-title` | 20px | 800 | `text-primary` | -0.3px |
| `.report-header` font-family | `var(--font-family)` | — | — | Inter only (no serif) |

### 3.4 Contrast Audit

| Element | Foreground | Background | Ratio | WCAG AA (4.5:1) |
|---|---|---|---|---|
| `.kpi-label` | `#1D1D1F` | `#FFFFFF` | 16.75:1 | ✅ |
| `.kpi-value` | `#1D1D1F` | `#FFFFFF` | 16.75:1 | ✅ |
| `.kpi-sub` | `#6E6E73` | `#FFFFFF` | 5.74:1 | ✅ |
| `.kpi-meta` | `#8E8E93` | `#FFFFFF` | 3.57:1 | ⚠️ Metadata only |
| `.kpi-delta-pos` | `#1A7F37` | `#FFFFFF` | 4.56:1 | ✅ |
| `.kpi-delta-neg` | `#CF222E` | `#FFFFFF` | 5.63:1 | ✅ |
| `.insight-stat` | `#1D1D1F` | `#FFFFFF` | 16.75:1 | ✅ |
| `.badge-pos` text | `#1A7F37` | `#E8F9EE` | 4.2:1 | ⚠️ Close to threshold |
| `.badge-neg` text | `#CF222E` | `#FFEBE9` | 4.8:1 | ✅ |
| `.badge-warn` text | `#B45309` | `#FFF3E0` | 4.5:1 | ✅ |
| `.rh-confidential` | `#FFFFFF` | `#0A1B3F` | 15.3:1 | ✅ |

### 3.5 Typography Issues

| Issue | Location | Fix |
|---|---|---|
| `.kpi-label` weight 600 in CSS, `font-weight:600` in Python `MetricCard` | Both sources | ✅ Aligned |
| `.kpi-value` weight 700 in CSS, hardcoded in `MetricCard` HTML | Both sources | ✅ Aligned |
| `inject_responsive_css()` `.kpi-sub` override hardcoded `#6E6E73` | `dashboard_common.py:26` | ⚠️ Uses `var(--color-text-secondary)` now (fixed) |
| `dashboard_common.py:219` `style_margin_color` hardcoded `#D97706` | Line 219 | ⚠️ Should use `T.COLOR_WARNING` |

---

## 4. Shared UI Components

### 4.1 Component Inventory

| Component | File | Lines | Purpose |
|---|---|---|---|
| `UniversalHeader` | `ui/components/core.py:3` | 64 | Report header with client, title, period, firm branding |
| `UniversalFooter` | `ui/components/core.py:66` | 78 | Confidential footer |
| `EmptyState` | `ui/components/core.py:80` | 90 | Empty data placeholder |
| `AlertBanner` | `ui/components/core.py:92` | 125 | Standardized alert (warning/error/info/success) |
| `section_title` | `ui/components/core.py:137` | 141 | Section heading |
| `section_card` | `ui/components/core.py:131` | 135 | Card wrapper |
| `badge` | `ui/components/core.py:143` | 157 | Inline status badge |
| `divider` | `ui/components/core.py:159` | 162 | Horizontal rule |
| `spacer` | `ui/components/core.py:127` | 129 | Vertical spacer |
| `MetricCard` | `ui/components/metrics.py:11` | 73 | KPI card with growth badge |
| `KPIGrid` | `ui/components/metrics.py:76` | 91 | Responsive grid of MetricCards |
| `TableCard` | `ui/components/tables.py:5` | 22 | DataFrame in card wrapper |
| `FilterToolbar` | `ui/components/filters.py:4` | 71 | Dynamic filter bar |
| `ChartEngine.apply_chart` | `views/components/chart_engine.py:11` | 76 | Plotly chart styling |
| `ChartEngine.render_card` | `views/components/chart_engine.py:79` | 94 | Chart in card wrapper |
| `KPIEngine.render_grid` | `views/components/kpi_engine.py:10` | 19 | Delegates to `KPIGrid` |

### 4.2 `MetricCard` Architecture

```python
# ui/components/metrics.py
MetricCard(
    label, value, sub=None, cp=None, pp=None,
    pp_label=None, benchmark=None, target=None, invert_trend=False
)
```

**HTML output structure:**
```html
<div class="kpi-card">
  <div class="kpi-label">{label}</div>
  <div class="kpi-value">{value}</div>
  <div class="kpi-sub">{sub}</div>           <!-- if sub -->
  <div class="kpi-delta-{pos|neg|new}">...</div>  <!-- if cp/pp -->
  <div class="kpi-sub">{pp_label}</div>      <!-- if pp_label -->
  <div class="kpi-meta">Bench: ... · Target: ...</div>  <!-- if benchmark/target -->
</div>
```

### 4.3 `KPIGrid` Architecture

```python
KPIGrid(metrics: list, cols: int = None)
# metrics = [{"label": "...", "value": "...", "cp": ..., "pp": ..., ...}, ...]
# cols defaults to len(metrics)
```

### 4.4 `ChartEngine` Architecture

```python
ChartEngine.apply_chart(fig, title, height=360, text_col=None, 
                        bar_text_pos="outside", size="medium",
                        x_title=None, y_title=None, barmode=None)
ChartEngine.render_card(title, fig, description=None, height=400, 
                        x_title=None, y_title=None, barmode=None)
```

**Note:** `ChartEngine.apply_chart` and `ui/helpers.apply_chart` are near-identical duplicates. The helpers version is used by `render_discount_heatmap` and a few legacy pages; `ChartEngine` is used by `command_center.py` and newer pages.

### 4.5 `FilterToolbar` Architecture

```python
FilterToolbar(capabilities: dict, all_months: List[str], advisors: List[str] = None)
# capabilities = {
#     "show_period_filter": True,
#     "show_comparison_filter": True,
#     "show_service_type_filter": False,
#     "default_period": "3M",
#     "additional_module_filters": ["Advisor"]
# }
```

**Note:** FilterToolbar uses `background: var(--color-surface2)` in inline style but CSS `.filter-toolbar` uses `var(--color-surface)`. The inline style wins — this is intentional (recessed filter bar vs elevated card).

### 4.6 `_render_finding` Architecture

```python
_render_finding(finding, cause, impact, recommendation, owner, priority)
# Used by: internal_audit.py, leakage.py
# Renders a 6-field structured audit finding card with priority-based color coding
```

**Priority color mapping:**
| Priority | Text Color | Background | Icon |
|---|---|---|---|
| Critical | `COLOR_DANGER` | `COLOR_DANGER_BG` | 🔴 |
| High | `COLOR_WARNING` | `COLOR_WARNING_BG` | 🟠 |
| Medium | `COLOR_PRIMARY` | `COLOR_INFO_BG` | 🔵 |
| Low | `COLOR_TEXT_SECONDARY` | `COLOR_SURFACE2` | ⚪ |

---

## 5. Executive Command Center Page

**File:** `views/executive/command_center.py` (381 lines)

### 5.1 Page Structure

| Zone | Lines | Content |
|---|---|---|
| **Zone A: Identity & Health Strip** | 127-153 | 6 KPIGrid metrics (Revenue, Margin%, JCs, Avg Labour/JC, Discount%, Revenue vs Target) |
| **Zone B: Alert & Opportunity Rail** | 155-228 | 3-column Critical/Warning/Opportunity cards + expandable detail |
| **Executive Brief** | 230-266 | AI-enhanced narrative with rule-based fallback |
| **Zone C: Workshop Intelligence** | 268-339 | 4 rows: Trend+Location, WS/BS+ServiceMix, Advisors (Top/Bottom 5), Locations (Top/Bottom 5) |
| **Zone D: Deep Drill Navigation** | 341-381 | 11 nav cards → page routing via `session_state["current_page"]` |

### 5.2 KPI Grid Metrics

| Metric | Label | CP | PP | pp_label | Special |
|---|---|---|---|---|---|
| 1 | Total Revenue | `fmt_inr(cp_rev)` | `pp_rev` | `PP {fmt_inr(pp_rev)}` | — |
| 2 | Margin % | `{cp_mar/cp_rev*100:.1f}%` | `{pp_mar/pp_rev*100:.1f}%` | `PP {pp_mar/pp_rev*100:.1f}%` | — |
| 3 | Total JCs | `fmt_num(cp_jc)` | `pp_jc` | `PP {fmt_num(pp_jc)}` | — |
| 4 | Avg Labour / JC | `fmt_inr(cp_avg_lab_jc)` | `pp_avg_lab_jc` | `PP {fmt_inr(pp_avg_lab_jc)}` | — |
| 5 | Avg Discount % | `{avg_disc:.1f}%` | — | `PP {pp_avg_disc:.1f}%` | `target`, `benchmark`, `invert_trend=True` |
| 6 | Revenue vs Target | `{rev_tgt_pct:.1f}%` | `100` | `Target 100%` — `None` if NaN | — |

### 5.3 Alert Rail Architecture

```python
engine = ExecutiveAlertEngine(DefaultBenchmarkProvider())
structured_alerts = engine.evaluate(cp, pp)
# Returns: {"critical": [...], "warning": [...], "opportunities": [...]}

# Each alert dict: {"rule", "impact", "owner", "current", "benchmark", "variance", "reason", "action"}
```

**Rendering:** Each column renders up to 3 cards using `.insight-card.{neg|warn|pos}` CSS classes. Overflow shows "+N More..."

### 5.4 Executive Brief (AI with Fallback)

```python
# Rule-based sections generated by generate_executive_narrative()
sections = {
    "period", "locations", "advisors", "discount",
    "sales_mix", "forecast", "actions"
}

# AI enhancement via Anthropic API (get_ai_client())
# Fallback: renders each section in `.ai-band` class
```

### 5.5 Deep Drill Navigation (Post-Fix)

```python
NAV_ITEMS = [
    ("👨‍🔧", "Labour",         "Labour"),
    ("⚙️",  "Parts Detail",   "Parts Detail"),
    ("💰",  "Margin",         "Margin"),
    ("✂️",  "Discounts",      "Discounts"),
    ("🕳️", "Leakage",        "Leakage Center"),
    ("📊",  "Sales Mix",      "Sales Mix"),
    ("🗣️", "Advisors",       "Advisors"),
    ("🏢",  "Locations",      "Locations"),
    ("🎯",  "Targets",        "Targets"),
    ("📈",  "Profit & Loss",  "Profit & Loss"),
    ("🔍",  "Internal Audit", "Internal Audit"),
]
```

**Routing mechanism:** `session_state["current_page"]` → `app.py:resolve_page()` → `PAGE_SLUGS` dict lookup.

**Bug fix applied:** All 11 cards previously used hardcoded `?page=Labour`. Now uses `NAV_ITEMS` list with correct page names matching `PAGE_SLUGS` values.

### 5.6 Command Center Visual Inventory

| Element | CSS Class Used | Source |
|---|---|---|
| KPI Cards | `.kpi-card` | `MetricCard` |
| Alert Rail Cards | `.insight-card.neg/.warn/.pos` | `render_rail_cards()` |
| Section Headers | `.section-title` | `section_title()` |
| AI Band | `.ai-band` | Fallback narrative |
| Nav Cards | `.nav-drill-card` | `NAV_ITEMS` loop |
| Trend Chart | `ChartEngine.render_card` | Plotly line |
| Location Bar | `ChartEngine.render_card` | Plotly horizontal bar |
| WS/BS Pie | `ChartEngine.render_card` | Plotly donut |
| Service Mix Pie | `ChartEngine.render_card` | Plotly donut |
| Advisor Tables | `TableCard` | Streamlit dataframe |
| Location Tables | `TableCard` | Streamlit dataframe |

---

## 6. UI Helpers & Traffic Utilities

### 6.1 `ui/helpers.py` (208 lines)

| Function | Lines | Purpose | Used by |
|---|---|---|---|
| `apply_chart` | 13-87 | Plotly chart styling (duplicate of `ChartEngine.apply_chart`) | `render_discount_heatmap` |
| `clean_hover` | 90-106 | Hover template formatter | Legacy pages |
| `csv_btn` | 109-114 | Export button wrapper | Multiple pages |
| `render_neg_labour_alert` | 116-135 | Red alert banner for negative net labour | Labour, Command Center |
| `render_alerts` | 138-145 | Generic alert renderer (severity → color) | Executive overview |
| `render_discount_heatmap` | 148-180 | Discount recoverability heatmap | Leakage Center |
| `_render_finding` | 183-206 | Structured audit finding card | Internal Audit, Leakage |

### 6.2 `ui/traffic.py` (29 lines)

| Function | Purpose | Used by |
|---|---|---|
| `yoy_badge(cp, pp)` | Returns HTML badge: ▲ X% / ▼ X% / — 0% / New ✦ | Multiple pages |
| `traffic_light(cp, pp)` | Returns emoji: 🟢 / 🟡 / 🔴 / ⚪ | Multiple pages |
| `tgt_badge(pct)` | Returns target badge: 🟢/🟡/🔴 with % | Targets page |

### 6.3 `ui/formatters.py`

Referenced by all UI files. Key formatters:
- `fmt_inr(val)` — ₹ with comma separation
- `fmt_inr_full(val)` — Full ₹ format
- `fmt_inr_short(val)` — Short ₹ (Cr/Lakhs)
- `fmt_pct(val)` — Percentage
- `fmt_num(val)` — Comma-separated number

### 6.4 `dashboard_common.py` Helpers (246 lines)

| Function | Lines | Purpose |
|---|---|---|
| `inject_responsive_css()` | 14-28 | Responsive CSS overrides (idempotent) |
| `apply_period_filters()` | 31-53 | CP/PP period filtering with cross-filter |
| `render_kpi_card()` | 56-99 | Legacy KPI card (used by non-upgraded pages) |
| `render_svc_row_with_delta()` | 102-130 | Service panel row with delta pill |
| `render_svc_panel()` | 133-156 | Service panel (WS/BS detail) |
| `render_cross_filter_bar()` | 159-191 | Cross-filter chip bar with clear buttons |
| `style_table_bold_total()` | 194-206 | Table row styling for TOTAL row |
| `style_color_growth()` | 209-212 | Growth value coloring |
| `style_margin_color()` | 215-220 | Margin value coloring with thresholds |
| `format_rank_movement()` | 223-231 | Rank movement formatting |
| `compute_rank_movement()` | 234-246 | Rank delta computation |

### 6.5 Duplicate `apply_chart` Audit

| Location | Lines | Used by |
|---|---|---|
| `ui/helpers.py:13-87` | 75 lines | `render_discount_heatmap`, legacy pages |
| `views/components/chart_engine.py:11-76` | 66 lines | `command_center.py`, newer pages |

**Difference:** `ChartEngine.apply_chart` adds `x_title`, `y_title`, `barmode` params. `helpers.apply_chart` does not. Otherwise nearly identical.

**Recommendation:** Deprecate `helpers.apply_chart` in favor of `ChartEngine.apply_chart`.

---

## Appendix A: Files Inventory

| File | Lines | Role |
|---|---|---|
| `static/style.css` | 560 | Global CSS — all design tokens and component styles |
| `ui/design_tokens.py` | 164 | Python token registry (T class) |
| `ui/components/core.py` | 162 | Universal header/footer, section_title, badge, etc. |
| `ui/components/metrics.py` | 91 | MetricCard + KPIGrid |
| `ui/components/tables.py` | 22 | TableCard |
| `ui/components/filters.py` | 71 | FilterToolbar |
| `ui/helpers.py` | 208 | Chart helpers, alert renderers, finding cards |
| `ui/traffic.py` | 29 | YoY badge, traffic light, target badge |
| `ui/formatters.py` | — | Number/currency formatters |
| `views/components/chart_engine.py` | 94 | Plotly chart engine |
| `views/components/kpi_engine.py` | 19 | KPI engine (delegates to KPIGrid) |
| `views/dashboard_common.py` | 246 | Shared dashboard utilities |
| `views/executive/command_center.py` | 381 | Executive Command Center page |

## Appendix B: Known Issues Summary

| # | Issue | Severity | File:Line |
|---|---|---|---|
| 1 | `#D1D1D6` hardcoded in `.kpi-card:hover` and `.loc-card:hover` | Low | `style.css:178,446` |
| 2 | `#B5D4F4` hardcoded in `.filter-chip` and `.forecast-card` border | Low | `style.css:378,454` |
| 3 | `#FFCCCB` hardcoded in `.alert-banner` border | Low | `style.css:421` |
| 4 | `rgba(0,113,227,0.25)` hardcoded in radio pill shadow | Low | `style.css:403` |
| 5 | `#D97706` hardcoded in `style_margin_color` | Low | `dashboard_common.py:219` |
| 6 | Duplicate `apply_chart` in `helpers.py` and `chart_engine.py` | Medium | Both files |
| 7 | `FilterToolbar` inline `surface2` vs CSS `surface` mismatch | Low | `filters.py:10` vs `style.css:370` |
