# Contributing to WSMIS

We welcome internal contributions to the WSMIS dashboard!

## Branching Strategy
- `main` is the production branch.
- Create feature branches off `main` (e.g., `feature/advisor-scorecard`, `bugfix/cache-invalidation`).
- Open a Pull Request (PR) against `main`.

## Testing Requirements
All new calculations and data processing logic must be accompanied by unit tests.
Before submitting a PR, ensure that the regression suite passes:

```bash
python -m pytest tests/ -v
```

If you modify UI elements or add new pages, the integration test in `tests/test_pages.py` must also pass.

## Coding Standards
- **Decoupling**: Dashboard pages must import business logic directly from `utils.calculations.*` or `utils.aggregations.*`.
- **Performance**: Do not use `apply()` loops if vectorized pandas functions are available.
- **Fail-Fast**: Ensure configuration validation logic catches errors at startup.
- **Type Hints**: Use standard python typing annotations on all new functions.
