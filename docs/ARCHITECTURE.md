# WSMIS Architecture Overview

WSMIS is built as a highly modular Streamlit dashboarding application designed to minimize the core router footprint while standardizing the UI generation and business logic calculation layer.

## Dependency Flow
The repository adheres to a strict uni-directional flow of dependencies:

1. **app.py**: The global router. It handles memory-caching of the master datasets, handles authentication or environment bootstrapping, and routes to individual pages.
2. **pages/**: Individual dashboard views (e.g., `cockpit.py`, `margin.py`). These contain Streamlit layout commands (`st.columns`, `st.tabs`). They do NOT compute logic directly.
3. **ui/**: Isolated UI component library (`ui/helpers.py`, `ui/formatters.py`, `ui/traffic.py`). Used exclusively for rendering HTML, metrics, tables, and standard charts.
4. **services/**: Orchestration layer (e.g., `financial_service.py`). Coordinates calculations and provides clean dataframes or metrics to the pages.
5. **utils/**: The bedrock calculation engines, aggregations, data cleaners, and data loaders. 
    - `calculations/`: Subject-specific mathematical engines (Revenue, Margin, Discounts).
    - `fact_metrics.py`: Direct extraction from the canonical datasets.
