# Parts Module Maintenance Guide

**Version:** 1.0  
**Date:** June 23, 2026  
**Purpose:** Technical documentation for Parts Module maintenance and troubleshooting

---

## Overview

The Parts Module consists of three integrated dashboards for parts revenue analysis:
- **Parts Executive** - High-level revenue overview with KPIs, charts, and location performance
- **Parts Detail** - Category-level drill-down with service mix and trend analysis
- **Sales Mix** - Category-focused analysis of Oil, Battery, Tyre, and Accessory sales

This guide documents the module structure, data flows, and integration points for maintenance purposes.

---

## Main Files

### Core Module Files

#### views/commercial/parts_executive.py
**Purpose:** Parts Executive Dashboard  
**Key Functions:**
- `render(df, targets_df, pairs, comparison_mode, selected_months)` - Main entry point
- `_init_state()` - Initialize StateManager defaults
- `_apply_filters(df, active_pairs)` - Apply CP/PP period filters
- `_compute_metrics(cp, pp, df)` - Calculate all KPIs and metrics
- `_render_cross_filter_bar()` - Render global filter controls
- `_render_narrative_banner(d)` - Render narrative summary banner
- `_render_ai_narrative(d, mode_str)` - Render AI-generated narrative
- `_render_executive_panel(d, mode_str)` - Render KPI grid
- `_render_waterfall(d, mode_str)` - Render category contribution waterfall
- `_render_category_heatmap(d, mode_str)` - Render category growth heatmap
- `_render_charts(d, active_pairs, mode_str, targets_df)` - Render monthly trend with target overlay
- `_render_executive_table(d, active_pairs, mode_str)` - Render location performance table
- `_render_low_margin_locations(d)` - Render low margin location alert
- `_render_monthly_detail(d, active_pairs, mode_str)` - Render monthly detail table

**Dependencies:**
- `views.shared` - Shared imports and utilities
- `views.components.chart_engine` - ChartEngine for chart rendering
- `ui.components.metrics` - KPIGrid for KPI rendering
- `services.state_manager` - StateManager for state management
- `views.dashboard_common` - Navigation and filter utilities

---

#### views/commercial/parts_detail.py
**Purpose:** Parts Detail Dashboard  
**Key Functions:**
- `render(df, pairs, comparison_mode, selected_months)` - Main entry point
- `_apply_detail_filters(df)` - Apply category and drill-through filters
- `_render_category_table(fdf, sel_cat)` - Render category revenue table
- `_render_category_mix_chart(fdf, mode_str)` - Render category mix donut
- `_render_service_contribution(fdf)` - Render service contribution chart
- `_render_service_mix_donut(fdf)` - Render service mix donut
- `_render_monthly_trend_table(fdf)` - Render monthly trend table
- `_render_discount_table(fdf)` - Render discount analysis table

**Dependencies:**
- `views.shared` - Shared imports and utilities
- `views.components.chart_engine` - ChartEngine for chart rendering
- `views.dashboard_common` - Styling, drill-through utilities
- `utils.constants` - CATEGORY_COLORS constant

---

#### views/commercial/sales_mix.py
**Purpose:** Sales Mix Dashboard  
**Key Functions:**
- `render(df, pairs, comparison_mode, selected_months)` - Main entry point
- `_apply_filters(df, pairs)` - Apply CP/PP period filters
- `_compute_metrics(cp, pp)` - Calculate KPIs with growth
- `_get_table_data(cp, col, pp, comparison_mode)` - Generate table data with growth column
- `_render_kpis(metrics)` - Render KPI grid
- `_render_tables(metrics, comparison_mode)` - Render category tables with exports
- `_render_charts(metrics, comparison_mode)` - Render category charts with comparison

**Dependencies:**
- `views.shared` - Shared imports and utilities
- `views.components.chart_engine` - ChartEngine for chart rendering
- `ui.design_tokens` - T theme tokens for colors

---

### Infrastructure Files

#### services/state_registry.py
**Purpose:** StateManager namespace registration  
**Parts Module Namespaces:**
- `parts_cross_month` - Selected month for cross-filter
- `parts_drill_location` - Drill-through location parameter
- `parts_drill_category` - Drill-through category parameter
- `parts_drill_from_page` - Drill-through source page

**Registration:**
```python
register_namespace("parts_", {
    "parts_cross_month": None,
    "parts_drill_location": None,
    "parts_drill_category": None,
    "parts_drill_from_page": None
})
```

---

#### views/dashboard_common.py
**Purpose:** Shared dashboard utilities  
**Navigation Functions:**
- `navigate_to_page(page)` - Navigate to specified page
- `get_drill_params()` - Retrieve drill-through parameters
- `clear_drill_params()` - Clear drill-through state

**Filter Functions:**
- `apply_period_filters(df, selected_months)` - Apply month filter
- `render_cross_filter_bar()` - Render global filter controls

**Styling Functions:**
- `style_table_bold_total(axis)` - Bold TOTAL row
- `style_margin_color(val)` - Color-code margin values
- `style_color_growth(val)` - Color-code growth values

---

#### app.py
**Purpose:** Application routing and data loading  
**Parts Module Routing:**
```python
elif page == "Parts Executive":
    from views.parts_executive import render
    safe_render(render, df_filtered_full, targets_df, pairs, comparison_mode, selected_months)
elif page == "Parts Detail":
    from views.parts_detail import render
    safe_render(render, df_filtered_full, pairs, comparison_mode, selected_months)
elif page == "Sales Mix":
    from views.sales_mix import render
    safe_render(render, df_filtered_cp, pairs, comparison_mode, selected_months)
```

**Data Loading:**
- `targets_df` - Loaded via `load_targets()` from utils/loaders.py
- Passed to Parts Executive for target overlay functionality

---

## Shared Helpers

### Canonical Aggregation Functions
**Location:** `utils/aggregations.py`

**Functions Used:**
- `location_summary(df, as_index=False)` - Aggregate by location
- `monthly_summary(df, as_index=False)` - Aggregate by month
- `category_summary(df, category_cols)` - Aggregate by category
- `service_summary(df, as_index=False)` - Aggregate by service type
- `pivot_summary(df, index, columns, values)` - Create pivot table

**Usage Pattern:**
```python
loc_sum = location_summary(df, as_index=True).agg(
    Parts_Revenue=("Pre-GST Parts", "sum"),
    Parts_Profit=("Parts Profit", "sum")
)
```

---

### Canonical Calculation Functions
**Location:** `utils/calculations/common.py`

**Functions Used:**
- `calc_ratio(numerator, denominator, multiplier=1, fill_value=0)` - Calculate ratio
- `calc_growth_pct(current, prior, fill_value=0)` - Calculate growth percentage

**Usage Pattern:**
```python
margin_pct = calc_ratio(profit, revenue, multiplier=100, fill_value=0)
growth = calc_growth_pct(cp_value, pp_value, fill_value=0)
```

---

### Canonical Filter Functions
**Location:** `utils/filters.py`

**Functions Used:**
- `apply_month_filter(df, month_col, months)` - Filter by month
- `apply_location_filter(df, location_col, locations)` - Filter by location
- `apply_location_group_filter(df, group_col, groups)` - Filter by location group
- `apply_service_type_filter(df, service_col, service_types)` - Filter by service type
- `apply_advisor_filter(df, advisor_col, advisors)` - Filter by advisor
- `split_cp_pp(df, pairs)` - Split dataframe into CP and PP based on pairs

**Usage Pattern:**
```python
cp, pp = split_cp_pp(df, pairs)
```

---

### Canonical Formatters
**Location:** `ui/formatters.py`

**Functions Used:**
- `fmt_inr(value)` - Format as INR with compact notation (e.g., ₹1.2Cr)
- `fmt_inr_full(value)` - Format as INR with full notation (e.g., ₹12,34,567)
- `fmt_inr_short(value)` - Format as INR with short notation (e.g., ₹12L)
- `fmt_pct(value)` - Format as percentage
- `fmt_num(value)` - Format as number

---

## Calculation Flow

### Parts Executive Calculation Flow

```
1. render() entry point
   ↓
2. _init_state() - Initialize StateManager defaults
   ↓
3. _apply_filters(df, active_pairs) - Split into CP and PP
   ↓
4. _compute_metrics(cp, pp, df) - Calculate all metrics
   ├─ Calculate KPI values (revenue, profit, margin, etc.)
   ├─ Calculate monthly sums (cp_month_sum, pp_month_sum)
   ├─ Calculate category sums (category_totals)
   ├─ Calculate location sums (location_totals)
   ├─ Calculate growth percentages
   └─ Build kpi_data list for KPIGrid
   ↓
5. _render_* functions - Render UI components
   ├─ _render_cross_filter_bar() - Global filters
   ├─ _render_narrative_banner() - Summary banner
   ├─ _render_ai_narrative() - AI narrative
   ├─ _render_executive_panel() - KPI grid
   ├─ _render_waterfall() - Waterfall chart
   ├─ _render_category_heatmap() - Heatmap chart
   ├─ _render_charts() - Trend chart with target overlay
   ├─ _render_executive_table() - Location table
   ├─ _render_low_margin_locations() - Margin alert
   └─ _render_monthly_detail() - Monthly detail table
```

### Parts Detail Calculation Flow

```
1. render() entry point
   ↓
2. _apply_detail_filters(df) - Apply category and drill-through filters
   ├─ Get selected category from UI
   ├─ Get drill-through parameters from StateManager
   ├─ Apply category filter if selected
   ├─ Apply drill-through filters if present
   └─ Return filtered dataframe and selected category
   ↓
3. _render_* functions - Render UI components
   ├─ _render_category_table(fdf, sel_cat) - Category table
   │  ├─ Calculate category sums by location
   │  ├─ Filter to selected category if not "All"
   │  ├─ Calculate margin percentages
   │  └─ Add export buttons
   ├─ _render_category_mix_chart(fdf, mode_str) - Category mix donut
   ├─ _render_service_contribution(fdf) - Service contribution
   ├─ _render_service_mix_donut(fdf) - Service mix donut
   ├─ _render_monthly_trend_table(fdf) - Monthly trend
   └─ _render_discount_table(fdf) - Discount analysis
```

### Sales Mix Calculation Flow

```
1. render() entry point
   ↓
2. _apply_filters(df, pairs) - Split into CP and PP
   ↓
3. _compute_metrics(cp, pp) - Calculate KPIs with growth
   ├─ Calculate Oil metrics (revenue, quantity, growth)
   ├─ Calculate Tyre metrics (revenue, quantity, growth)
   ├─ Calculate Battery metrics (revenue, quantity, growth)
   ├─ Calculate Accessory metrics (revenue, growth)
   ├─ Calculate Parts Sale metrics (revenue, growth)
   └─ Build kpi_data list with cp/pp for growth calculation
   ↓
4. _render_kpis(metrics) - Render KPI grid
   ↓
5. _render_tables(metrics, comparison_mode) - Render tables
   ├─ _get_table_data(cp, col, pp, comparison_mode) - Generate table data
   │  ├─ Pivot by location and month
   │  ├─ Calculate totals
   │  ├─ Add growth column (YoY or MoM based on mode)
   │  └─ Format values
   ├─ Render Oil Sales table with export
   ├─ Render Battery Sales table with export
   ├─ Render Tyre Sales table with export
   └─ Render Accessory Sales table with export
   ↓
6. _render_charts(metrics, comparison_mode) - Render charts
   ├─ Oil Trend chart with PP comparison
   ├─ Battery + Tyre chart with PP comparison
   ├─ Oil Ranking chart
   ├─ Mix (Acc vs Pts) pie chart
   └─ Oil Per Litre chart
```

---

## Navigation Flow

### Cross-Report Drill-Through Flow

```
User Action: Click drill-through button in Parts Executive location table
   ↓
navigate_to_page("Parts Detail") called
   ↓
StateManager.set("parts_drill_location", location)
StateManager.set("parts_drill_category", category)
StateManager.set("parts_drill_from_page", "Parts Executive")
   ↓
st.rerun() - Navigate to Parts Detail
   ↓
Parts Detail render() called
   ↓
_apply_detail_filters() called
   ↓
get_drill_params() retrieves drill-through parameters
   ↓
Filters applied based on drill-through parameters
   ↓
Drill-through context banner displayed
   ↓
User can click "Clear drill-through filters" to reset
   ↓
clear_drill_params() resets all drill-through state
   ↓
st.rerun() - Reload without filters
```

### State Management Flow

```
Initialization (parts_executive.py _init_state):
   ↓
StateManager.set("parts_cross_month", None)
StateManager.set("parts_drill_location", None)
StateManager.set("parts_drill_category", None)
StateManager.set("parts_drill_from_page", None)
   ↓
User Interaction (e.g., select month on chart):
   ↓
StateManager.set("parts_cross_month", selected_month)
   ↓
st.rerun() - Re-render with new state
   ↓
Subsequent renders read from StateManager
   ↓
Filters applied based on state values
```

---

## Target Integration

### Target Data Loading

```
app.py load_targets():
   ↓
load_targets() from utils/loaders.py
   ↓
Read from Google Sheet "MP_PB_Targets"
   ↓
Return targets_df with columns: Month, Parts, Labour, etc.
   ↓
Pass to Parts Executive render function
```

### Target Overlay Flow

```
_render_charts(d, active_pairs, mode_str, targets_df):
   ↓
Check if targets_df is available and not empty
   ↓
For each month in active_pairs:
   ├─ Find target row for month in targets_df
   ├─ Extract target value from "Parts" column
   ├─ Calculate achievement % = (actual / target) * 100
   └─ Calculate variance = actual - target
   ↓
Add target line trace to chart:
   ├─ mode="lines+markers"
   ├─ line=dict(dash="dash", color=T.COLOR_WARNING)
   └─ hovertemplate shows target value
   ↓
Add achievement annotations:
   ├─ Display "Ach: X% | Var: ₹Y"
   ├─ Positioned at target line
   └─ Only shown if target > 0
   ↓
Chart renders with target overlay
```

### Target Data Structure

**Expected columns in targets_df:**
- `Month` - Month name (e.g., "Jan-26")
- `Parts` - Parts revenue target for the month
- `Labour` - Labour revenue target (not used in Parts module)
- Other columns as needed for other modules

**Example:**
```
Month      Parts       Labour
Jan-26     5000000     3000000
Feb-26     5200000     3100000
Mar-26     5500000     3200000
```

---

## Export Flow

### Export Button Implementation

```
_render_tables() or table rendering function:
   ↓
Create DataFrame for export
   ↓
Create ExportMeta:
   ├─ report_title - Title for export
   ├─ location - Location context
   └─ date_range - Date range context
   ↓
Call render_export_buttons(df, meta, key_prefix):
   ├─ Render CSV export button
   ├─ Render Excel export button
   └─ Render PDF export button
   ↓
User clicks export button
   ↓
Export service generates file
   ↓
File downloaded to user's browser
```

### Export Metadata Structure

```python
from services.export_service import ExportMeta

meta = ExportMeta(
    report_title="Parts Category",
    location="All Locations",
    date_range="",
)
```

### Export Key Prefixes

**Parts Executive:**
- `parts_executive_kpi` - KPI grid export
- `parts_executive_location` - Location table export
- `parts_executive_monthly` - Monthly detail export

**Parts Detail:**
- `parts_category` - Category table export
- `parts_service_contribution` - Service contribution export
- `parts_monthly_trend` - Monthly trend export
- `parts_discount` - Discount analysis export

**Sales Mix:**
- `sales_mix_oil` - Oil Sales table export
- `sales_mix_battery` - Battery Sales table export
- `sales_mix_tyre` - Tyre Sales table export
- `sales_mix_accessory` - Accessory Sales table export

---

## Drill-Through Flow

### Drill-Through Parameter Setting

```
User clicks drill-through button in Parts Executive:
   ↓
Button click handler:
   ├─ Get selected location from table
   ├─ Get selected category from context
   └─ Call navigate_to_page("Parts Detail")
   ↓
navigate_to_page(page):
   ├─ StateManager.set("parts_drill_location", location)
   ├─ StateManager.set("parts_drill_category", category)
   ├─ StateManager.set("parts_drill_from_page", "Parts Executive")
   └─ st.rerun()
```

### Drill-Through Parameter Retrieval

```
Parts Detail render():
   ↓
_apply_detail_filters(df):
   ↓
get_drill_params():
   ├─ location = StateManager.get("parts_drill_location")
   ├─ category = StateManager.get("parts_drill_category")
   └─ from_page = StateManager.get("parts_drill_from_page")
   ↓
Apply filters:
   ├─ If location: filter by location
   ├─ If category: filter by category
   └─ If from_page: show context banner
   ↓
Return filtered dataframe
```

### Drill-Through Context Display

```
If drill_params["from_page"] is set:
   ↓
st.info(f"🔍 Drilled from {drill_params['from_page']}")
   ↓
If st.button("Clear drill-through filters"):
   ↓
clear_drill_params():
   ├─ StateManager.set("parts_drill_location", None)
   ├─ StateManager.set("parts_drill_category", None)
   └─ StateManager.set("parts_drill_from_page", None)
   ↓
st.rerun()
```

---

## Troubleshooting

### Common Issues

#### Issue: Category data not showing
**Symptom:** Category breakdown shows "Category breakdown available from Jan-26 onwards"  
**Cause:** Data before Jan-26 does not have category columns  
**Solution:** This is expected behavior. Category data is only available from Jan-26 onwards.

#### Issue: Target overlay not showing
**Symptom:** Target line not visible on monthly trend chart  
**Cause:** targets_df is empty or not available  
**Solution:** Verify targets_df is loaded correctly in app.py and contains data for the selected months.

#### Issue: Drill-through not working
**Symptom:** Clicking drill-through button does not navigate  
**Cause:** StateManager parameters not set correctly  
**Solution:** Verify navigate_to_page() is called with correct parameters and StateManager.set() is successful.

#### Issue: Export buttons not appearing
**Symptom:** No export buttons visible on tables  
**Cause:** render_export_buttons() not called or ExportMeta not created  
**Solution:** Verify render_export_buttons() is called with valid DataFrame and ExportMeta.

#### Issue: Growth badges not showing
**Symptom:** KPI cards not showing growth badges  
**Cause:** cp/pp values not passed to MetricCard  
**Solution:** Verify kpi_data structure includes cp and pp keys for all KPIs.

---

## Performance Optimization

### Aggregation Cache

The module uses canonical aggregation functions that leverage caching:
- `location_summary()` - Cached by default
- `monthly_summary()` - Cached by default
- `category_summary()` - Cached by default
- `service_summary()` - Cached by default

**Best Practices:**
- Use canonical helpers instead of custom aggregations
- Avoid redundant aggregations in the same render cycle
- Leverage cached results for multiple uses

### Filter Optimization

**Best Practices:**
- Apply filters early in the data flow
- Use canonical filter functions
- Avoid filtering on already-filtered data
- Use vectorized operations instead of loops

---

## Testing Checklist

### Unit Testing
- [ ] Test _apply_filters() with various pair configurations
- [ ] Test _compute_metrics() with edge cases (empty data, single month)
- [ ] Test growth calculations with zero prior values
- [ ] Test drill-through parameter setting and retrieval
- [ ] Test export button rendering with various DataFrame sizes

### Integration Testing
- [ ] Test end-to-end drill-through flow
- [ ] Test target overlay with various target data scenarios
- [ ] Test export functionality with actual file downloads
- [ ] Test comparison mode switching (YoY ↔ MoM)
- [ ] Test category filter in Parts Detail

### Regression Testing
- [ ] Verify all KPIs render correctly
- [ ] Verify all charts render without errors
- [ ] Verify all tables render with correct formatting
- [ ] Verify no Python exceptions in browser console
- [ ] Verify no Plotly warnings

---

## Contact

For issues or questions regarding the Parts Module:
- Refer to PARTS_MODULE_RELEASE_NOTES_v1.0.md for feature documentation
- Refer to PARTS_MODULE_CHANGELOG.md for implementation history
- Refer to PARTS_MODULE_TECHNICAL_DEBT.md for known technical debt
