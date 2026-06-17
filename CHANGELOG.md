# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.0.0-rc1] - 2026-06-17

### Added
- **UI Component Library Foundation**: Decoupled presentation code into dedicated `ui/` modules (`kpi_cards.py`, `tables.py`, `formatters.py`).
- **Automated Test Infrastructure**: Implemented `pytest` suite validating loaders, cleaning, filters, aggregations, and mathematical calculations.
- **Integration Test Suite**: `AppTest` regression suite validating all 18 Streamlit dashboard routes and rendering paths.
- **Documentation**: Standardized `README.md`, `INSTALL.md`, `DEPLOYMENT.md`, `CONTRIBUTING.md`, and this `CHANGELOG`.
- **Fail-Fast Configuration**: Added `validate_environment()` to prevent the application from starting without explicit deployment configurations.
- **Structured Error Handling**: Centralized `WSMISError` exception hierarchy with decorators to wrap unreliable data source connections gracefully.

### Changed
- **Architectural Routing**: `app.py` heavily refactored to remove spaghetti code; replaced with a clean `render_page_router` design.
- **Aggregation Engine**: Migrated grouped calculations to `aggregation_cache.py` to prevent redundant group-by logic.
- **Cache Determinism**: Streamlit `@st.cache_data` now utilizes deterministic hashing via `pd.util.hash_pandas_object()` instead of volatile memory references (`id(df)`).
- **FinancialService Decoupling**: Purged proxy exports from `financial_service.py` requiring pages to cleanly import math functions directly.

### Optimized
- **Expense Alert Engine**: Completely rewrote the AI Alert Generation engine leveraging vectorized pandas operations to achieve a >9x speedup, eliminating nested iteration over the main dataframe.
