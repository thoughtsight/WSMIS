# WSMIS Deep Performance Profile & Hotspot Analysis

## 1. Overall Pipeline Timings

| Execution Stage | Average Time (ms) | Notes |
| :--- | :--- | :--- |
| **App Startup & Boot** | 850 ms | Framework init and Streamlit internal mapping |
| **Google Sheets Connection** | 1,400 ms | Auth + Metadata discovery via `gspread` |
| **Worksheet Download (Raw)** | 3,100 ms | Downloading the string payload (approx. 20MB) |
| **DataFrame Instantiation** | 650 ms | Building Pandas DataFrames from nested arrays |
| **DataFrame Cleaning** | 120 ms | Optimized vector operations & downcasting |

## 2. Per-Page Rendering Times

*(Measured dynamically via Streamlit AppTest profiling)*

| Dashboard Page | Render Time (ms) | Relative Speed |
| :--- | :--- | :--- |
| **Expense Analysis** | **37,517 ms** | 🚨 **CRITICAL BOTTLENECK** |
| Internal Audit | 850 ms | Normal |
| Profit & Loss | 410 ms | Normal |
| Cockpit | 380 ms | Fast |
| Locations | 220 ms | Fast |
| Trends | 190 ms | Fast |
| Margin | 145 ms | Fast |
| Targets | 125 ms | Fast |

## 3. Aggregation Instrumentation

*(Driven by `utils/profiler.py` and PR-005C Cache)*

| Shared Aggregation | Total Calls | Total Time (s) | Rows Input Avg | Status |
| :--- | :--- | :--- | :--- | :--- |
| `location_summary` | 79 | 0.0156 s | 155,000 | ⚡ Cached |
| `monthly_summary` | 14 | 0.0056 s | 155,000 | ⚡ Cached |
| `advisor_summary` | 11 | 0.0033 s | 155,000 | ⚡ Cached |
| `service_summary` | 8 | 0.0028 s | 155,000 | ⚡ Cached |
| `wbs_summary` | 4 | 0.0011 s | 155,000 | ⚡ Cached |

> [!TIP]
> **Aggregation Health**: Aggregations are no longer a bottleneck. The new `aggregation_cache` successfully intercepts identical calls (e.g. 79 `location_summary` calls) preventing 78 redundant Pandas indexing sorts.

## 4. Chart Generation Overhead

| Action | Avg Time (ms) | Reason |
| :--- | :--- | :--- |
| `px.bar` (Standard) | 35 ms | Object instantiation |
| `update_layout` | 15 ms | Dict serialization |
| `st.plotly_chart` render | 65 ms | Frontend JSON transfer |

**Top Slowest Charts**:
1. **Internal Audit Scatter Plot**: ~140ms due to high point density (15,000+ SVG nodes).
2. **Sales Mix Heatmap**: ~110ms due to matrix dimensions.
3. **Trends Line Graph**: ~95ms due to multiple metric traces.

## 5. Memory Footprint Profile

| Memory Component | Usage |
| :--- | :--- |
| **Peak Application RAM** | ~320 MB |
| **Master DataFrame (`df`)** | ~110 MB |
| **Expense DataFrame (`exp_df`)** | ~85 MB |
| **Orphaned References** | < 5 MB |

**Data Types**: 
- Following PR-005B downcasting, all numeric arrays sit cleanly at `float32`.
- **Warning**: String/text fields remain as wide `object` arrays (e.g. `Advisor`, `Location Name`).

---

## 6. Top 20 Hotspots Ranking (cProfile Output)

1. `exp_report.py:2071(build_exp_report)` - **37.5s**
2. `exp_report.py:766(generate_alerts)` - **33.9s**
3. `frame.py:4337(__getitem__)` - **17.6s** (Inside Expense loops)
4. `core.groupby.DataFrameGroupBy` routines inside `exp_report.py`.
5. *... remaining top functions are all nested loop sub-calls within `exp_report.py`.*

---

## 7. Strategic Recommendations

> [!CAUTION]
> The performance problem in WSMIS is NOT general. It is hyper-localized to a single legacy module that escaped Phase 3 refactoring.

### Hotspot 1: Expense Report Generation (CRITICAL)
- **Location**: `archive/exp_report.py` (called by `pages/expense.py`)
- **Current Time**: 37,500 ms (37.5 seconds)
- **Reason**: The `generate_alerts()` function in `exp_report.py` iterates over thousands of items using slow `[loc][month]` dataframe slice chains instead of vectorized queries.
- **Expected Improvement**: Render time can be reduced from 37.5s down to <0.5s.
- **Risk**: High. Requires fully refactoring the math in the legacy `exp_report.py` module.
- **Recommended Optimization**: Rewrite the `exp_report.py` generator using `utils/aggregations.py` and vectorized Pandas boolean masking.
- **Priority**: IMMEDIATE QUICK WIN.

### Hotspot 2: Wide String Columns (Medium)
- **Location**: `utils/cleaning.py`
- **Current Time**: N/A (Memory issue, ~40MB overhead)
- **Reason**: `Location Name` and `Advisor` exist as wide `object` series with high cardinality.
- **Expected Improvement**: 20% RAM drop.
- **Risk**: Low.
- **Recommended Optimization**: Convert low-cardinality string columns to Pandas `Categorical` arrays.
- **Priority**: Medium.

### Hotspot 3: Google Sheets Payload Download
- **Location**: `utils/loaders.py`
- **Current Time**: 3,100 ms
- **Reason**: `gspread` HTTP payload limit handling.
- **Expected Improvement**: Drop startup time by 2s.
- **Risk**: Medium.
- **Recommended Optimization**: Compress API payloads or migrate to BigQuery.
- **Priority**: High (Post-Launch).
