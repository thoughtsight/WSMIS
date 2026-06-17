# Dependency Rules

To maintain the architectural integrity of WSMIS, all future contributions must adhere to the following rules:

1. **Uni-Directional Flow**:
   `app.py` → `pages` → `ui` → `services` → `utils`

2. **No Reverse Imports**:
   - `pages` may NEVER import from `app.py`.
   - `ui` may NEVER import from `pages` or `app.py`.
   - `services` may NEVER import from `ui` or `pages`.
   - `utils` may NEVER import from `services`, `ui`, `pages`, or `app.py`.

3. **UI Logic Isolation**:
   - `services` and `utils` must not contain any `st.write`, `st.metric`, `st.dataframe`, or `plotly` plotting logic. They return values, lists, or Pandas Dataframes ONLY.

4. **Business Logic Isolation**:
   - `pages` and `ui` must not calculate business formulas (e.g. `(revenue - cost)/revenue`). They must request the calculated values from `services` or `utils.calculations`.
