# Changelog

## [1.0.0-RC] - 2026-06-17

### Added
- **Configuration Layer**: Added `config/paths.py`, `config/settings.py`, and `config/environment.py` to standardize application configuration.
- **Logging Layer**: Added `logs/logger.py` replacing standard `print()` statements with structured log tracing.
- **Error Handling**: Added `services/error_handler.py` and `safe_render()` wrapper. This protects the Streamlit runtime from crashing globally when an individual dashboard view fails.
- **Documentation**: Generated `ARCHITECTURE.md`, `FOLDER_STRUCTURE.md`, `DEPENDENCY_RULES.md`, `DEPLOYMENT_CHECKLIST.md`, and `SECURITY_MIGRATION.md` inside `docs/`.

### Changed
- Refactored `app.py` routing logic to utilize the new `safe_render()` error handler.
- Converted all trace and debug console prints to `logger.info()`.

### Removed
- Moved all massive monolithic legacy files (`exp_report.py`, `pnl_report.py`, `internal_audit_app.py`, `revenue_leakage_*.py`) to the `archive/` directory.
- Moved all temporary refactoring scripts (`extract_*.py`, `replace_*.py`, etc.) to the `archive/tools/` directory.
