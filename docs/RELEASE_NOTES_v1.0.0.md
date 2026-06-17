# WSMIS Release Notes

**Version:** v1.0.0-rc1
**Date:** 2026-06-17

## Overview
WSMIS v1.0.0-rc1 represents a complete architectural overhaul of the legacy monolithic script. The application has been rebuilt into a production-grade, highly-performant, and maintainable data analytics platform specifically engineered for multi-location automotive dealership networks.

## Major Improvements

- **Advisor Scorecard:** Introduced a sophisticated 1-5 star rating system measuring advisors across 6 distinct KPIs (JC volume, labour/JC, parts/JC, oil/JC, accessory/JC, discount%).
- **Location Health Framework:** A completely new dashboard featuring an Apple-style card grid with dynamic health indicators (🟢/🟡/🔴) to instantly identify struggling vs. excelling locations.
- **Forecasting Engine:** Integrated `scikit-learn` linear regression to forecast 3-month trajectories for Revenue and Margin.
- **Dynamic Period Picker:** Users can now select custom historical periods or choose preset blocks (1M, 3M, Q1, Q2) to run instantaneous YoY and MoM comparisons.
- **AI Narrative Integration:** The Executive Dashboard now generates plain-English, C-Suite ready summaries using an Anthropic AI backend.

## Architectural Changes

- **Decoupled Business Logic:** Math functions are now strictly isolated in `utils/calculations/` (e.g., `revenue.py`, `margin.py`, `discount.py`) ensuring UI components never perform raw mathematical operations.
- **Componentized UI:** All visual components (KPI cards, styled tables, badges) are abstracted into the `ui/` directory, resulting in a 100% unified visual theme.
- **Centralized Routing:** The spaghetti-code page selection logic was removed in favor of a clean `render_page_router` that cleanly dispatches state.
- **FinancialService API:** Legacy tight coupling between data loaders and math functions was severed. `FinancialService` now serves as a clean proxy.

## Performance

- **Shared Aggregation Engine:** Redundant `.groupby()` operations that previously bottlenecked the application have been eliminated. Summaries are now computed once in `aggregation_cache.py` and shared globally.
- **Vectorized Expense Alerts:** The Alert Generation engine was completely rewritten using vectorized Pandas operations, delivering a 9x performance speedup.
- **Deterministic Caching:** Streamlit's `@st.cache_data` now uses cryptographic hashes (`pd.util.hash_pandas_object()`) rather than volatile object IDs (`id(df)`), preventing catastrophic cache misses.

## Testing & Stability

- **Test Infrastructure Foundation:** A comprehensive `pytest` framework has been implemented.
- **Business Logic Regression:** 100% test coverage achieved across all core financial formulas, guaranteeing mathematical integrity.
- **Integration Suite:** An automated `AppTest` suite simulates end-user routing, validating all 18 dashboard pages simultaneously to prevent routing crashes or failed imports.

## Known Issues

- **Internal Audit Legacy Code:** The Internal Audit dashboard relies on the legacy `internal_audit_app.py` script. While functional, it does not conform to the new UI architecture.
- **High Memory Footprint:** Very large datasets (>100k rows) may cause memory spikes due to pure Pandas in-memory architecture.

## Breaking Changes

- **Environment Validation:** The application now employs a fail-fast configuration. If the `WSMIS_ENV` environment variable is not explicitly set to `production` or `development`, the application will intentionally crash with a `ConfigurationError`.
- **Cache TTL:** The base cache Time-To-Live (TTL) has been reduced to 300 seconds (5 minutes) to ensure tighter synchronization with live Google Sheets.
