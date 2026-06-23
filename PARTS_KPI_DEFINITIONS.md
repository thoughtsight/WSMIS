# Parts Module KPI Definitions
# Phases 2 & 3 Implementation

This document defines all new KPIs introduced in Phases 2 and 3 of the Parts Module implementation.

---

## Phase 2 KPIs (Executive Enhancements)

### 1. Oil Penetration Rate
- **KPI Name**: Oil Penetration Rate
- **Business Purpose**: Measures the percentage of job cards that include oil/lubricant sales. Critical for understanding oil adoption and upsell effectiveness.
- **Formula**: `(JCs with Oil_Sale > 0 / Total JCs) × 100`
- **Data Source**: `Oil_Sale` column, `JC_Nos.` column
- **Benchmark**: 70%
- **Display Location**: 
  - Parts Executive: KPI panel
  - Parts Detail: Service Contribution table (per service type)
- **Notes/Assumptions**: 
  - Calculated at overall level for Executive
  - Calculated per service type for Detail
  - Uses `calc_ratio()` helper for safe division

### 2. Parts per Job Card (Parts/JC)
- **KPI Name**: Parts per Job Card
- **Business Purpose**: Average parts revenue per job card. Indicates parts attachment rate and upsell effectiveness.
- **Formula**: `Parts Revenue / Total JCs`
- **Data Source**: `Pre-GST Parts` column, `JC_Nos.` column
- **Benchmark**: 3.2
- **Display Location**:
  - Parts Executive: KPI panel
  - Parts Detail: Service Contribution table (per service type)
- **Notes/Assumptions**:
  - Uses Pre-GST Parts as parts revenue
  - Calculated at overall level for Executive
  - Calculated per service type for Detail

### 3. Parts Health Score
- **KPI Name**: Parts Health Score
- **Business Purpose**: Composite indicator (0-100) measuring overall parts business health across multiple dimensions.
- **Formula**: Weighted average of component scores:
  - Margin Score (30%): `(Margin % / 15) × 100` (capped at 100)
  - Oil Penetration Score (25%): `(Oil Pen % / 80) × 100` (capped at 100)
  - Parts/JC Score (25%): `(Parts/JC / 4) × 100` (capped at 100)
  - Growth Score (20%): `((Growth % + 10) / 30) × 100` (capped at 100, -10% = 0)
- **Data Source**: Margin %, Oil Pen %, Parts/JC, Growth %
- **Benchmark**: 80
- **Display Location**: Parts Executive: KPI panel
- **Notes/Assumptions**:
  - Only displayed in Executive (not Detail)
  - Each component score capped at 0-100 range
  - Growth score uses -10% as floor (0 score) and 20% as ceiling (100 score)
  - PP health score calculated for comparison but not displayed

---

## Phase 3 KPIs (Business KPI Enhancements)

### 4. Discount Rate
- **KPI Name**: Discount Rate
- **Business Purpose**: Measures the percentage of revenue given as discounts. Critical for pricing discipline and margin protection.
- **Formula**: `(Parts Discount / Parts Revenue) × 100`
- **Data Source**: `Parts Discount` column, `Pre-GST Parts` column
- **Benchmark**: 2%
- **Display Location**:
  - Parts Executive: KPI panel (with inverted trend - lower is better)
  - Parts Detail: Service Contribution table (per service type)
- **Notes/Assumptions**:
  - Lower discount rate is better (invert_trend=True in MetricCard)
  - Calculated at overall level for Executive
  - Calculated per service type for Detail
  - Conditional formatting: >2.5% red, >2.0% amber

### 5. Low-Performing Locations
- **KPI Name**: Low-Performing Locations
- **Business Purpose**: Identifies locations with margin below 10% for targeted intervention.
- **Formula**: Filter locations where `Margin_CP < 10%`, sort by margin ascending
- **Data Source**: Location-level margin from `loc_df`
- **Benchmark**: 10% (threshold)
- **Display Location**: Parts Executive: Dedicated table
- **Notes/Assumptions**:
  - Only displays if any locations have margin < 10%
  - Shows Revenue, Margin %, Growth %, Oil Pen %, Parts/JC
  - Sorted by margin (worst first)

### 6. Category Growth Heatmap
- **KPI Name**: Category Growth Heatmap
- **Business Purpose**: Visualizes growth performance across parts categories (Standard, Oil, Add-ons).
- **Formula**: Calculate YoY/MoM growth % for each category
- **Data Source**: Category CP/PP revenue from `std_stats`, `oil_stats`, `addon_stats`
- **Benchmark**: N/A
- **Display Location**: Parts Executive: Heatmap chart
- **Notes/Assumptions**:
  - Only displays if category data available (from Jan-26 onwards)
  - Uses RdYlGn colorscale (red=low growth, green=high growth)
  - Single-row heatmap with growth percentages

### 7. Service Type Mix Analysis
- **KPI Name**: Service Type Mix Analysis
- **Business Purpose**: Visualizes revenue distribution across service types (donut chart).
- **Formula**: Aggregate `Pre-GST Parts` by `Service Type`, calculate percentage
- **Data Source**: `Service Type` column, `Pre-GST Parts` column
- **Benchmark**: N/A
- **Display Location**: Parts Detail: Donut chart
- **Notes/Assumptions**:
  - Uses `CATEGORY_COLORS` from constants for consistent coloring
  - Shows legend with percentages
  - Uses cached `service_summary` for efficiency

### 8. Monthly Trend Table
- **KPI Name**: Monthly Trend Table
- **Business Purpose**: Shows last 6 months of revenue, job cards, margin, and parts/JC for trend analysis.
- **Formula**: Aggregate by month, sort by date, take last 6 months
- **Data Source**: `Month Name`, `Month_Sort`, `Pre-GST Parts`, `JC_Nos.`, `Parts Profit`
- **Benchmark**: N/A
- **Display Location**: Parts Detail: Table
- **Notes/Assumptions**:
  - Uses cached `monthly_summary` for efficiency
  - Sorts by `Month_Sort` if available, otherwise by `Month Name`
  - Shows Revenue, Job Cards, Margin %, Parts/JC
  - Conditional margin coloring

---

## Removed Features

### Top 5 Parts by Revenue (P3-02) - REMOVED
- **Reason**: Dataset does not contain item-level `Part Name` information
- **Alternative Recommendation**: The existing Category Mix chart in Parts Detail already provides category-level breakdown (Standard Parts, Oil, Tyres, Batteries, Accessories, Others). This executive-friendly alternative uses available data and serves a similar purpose by showing which categories drive revenue.

---

## Implementation Notes

### Reuse Strategy
- Core helper `calc_ratio()` is reused across all KPI calculations
- Executive and Detail calculations operate at different aggregation levels (overall vs per-service-type)
- Additional deduplication deferred to Phase 5 (Architecture Improvements)

### Color Coding
- **Green**: Meets or exceeds benchmark
- **Amber**: Below benchmark but within acceptable range
- **Red**: Significantly below benchmark

### Benchmarks
- All benchmarks are stored as constants in code (not hardcoded in display logic)
- Benchmarks are based on industry standards and internal targets
