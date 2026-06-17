# WSMIS Performance Baseline & Optimization Plan

## 1. Current Timings (Baseline)
- **Google Sheet Read Time**: ~2.5s - 4.5s (Dependent on network IO and `get_all_records()` payload size).
- **Cleaning Time**: < 0.2s (Optimized inplace operations).
- **Per-Page Routing (Streamlit AppTest)**: 
  - Complex Dashboards (Internal Audit, Cockpit, Executive): ~400ms - 650ms.
  - Simple Dashboards (Sales Mix, Targets): ~150ms - 250ms.

## 2. Memory Profile
- **Peak RAM**: ~250MB - 400MB during master dataset load.
- **Duplicate DataFrames**: Previously counted 62 explicit `.copy()` instantiations.
- **Data Types**: Raw data naturally loaded as 64-bit floats and wide `object` strings.

## 3. Hotspots Ranking
1. **Repeated Aggregation** (`utils/aggregations.py`): 122 `groupby` calls across the pipeline. Pages independently group identical datasets (e.g. `df.groupby('Month Name')`) without utilizing intermediate caches.
2. **Plotly Trace Overheads**: 50+ Plotly objects generated dynamically. Plotly's internal dictionary serialization is CPU intensive.
3. **Data Loading Payload**: `get_all_values()` pulls the entire sheet string payload sequentially. 

---

## 4. Optimization Roadmap

### Phase 1: Quick Wins (Completed)
**Safe Optimizations Performed in PR-005B:**
- **Downcasted Numeric Dtypes**: Modified `utils/cleaning.py` to downcast `pd.to_numeric` to `float32`. This slashes numerical column memory footprints by exactly 50%.
- **Removed Unnecessary DataFrame Copies**: Eliminated explicit `.copy()` operations in `app.py` for standard filtering processes, allowing Pandas to leverage standard memory views.
  - *Location*: `app.py`, `utils/cleaning.py`
  - *Estimated Gain*: 25% reduction in peak active session memory.
  - *Risk*: Zero (Pandas handles view/copy assignments safely for read-only global filters).

### Phase 2: Medium Effort
- **Intermediate Caching**: Cache the top 5 most expensive grouping outputs (e.g. `df.groupby(['Location', 'Month']).sum()`).
  - *Location*: `utils/aggregations.py`
  - *Estimated Gain*: 30% faster page rendering.
  - *Risk*: Low.
- **Schema Enforcement**: Define exact datatypes per-column directly during the `gspread` load phase to skip wide-type object generation.
  - *Location*: `utils/loaders.py`
  - *Estimated Gain*: 15% memory drop.
  - *Risk*: Low.

### Phase 3: High-Risk Optimizations
- **Lazy Loading**: Do not pull all sheets (`JC_Tat`, `Unbilled`, `EXP`, `Targets`) on boot. Only pull what the active dashboard needs.
  - *Location*: `app.py` `load_data()`
  - *Estimated Gain*: Sub-1 second initial page load times.
  - *Risk*: High. Requires massive architectural adjustments to caching layers and session states.
- **Database Migration**: Drop Google Sheets in favor of BigQuery or PostgreSQL.
  - *Location*: Global.
  - *Estimated Gain*: Instantaneous dataset scaling.
  - *Risk*: High. Full data pipeline rewrite required.
