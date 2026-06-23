# WSMIS Global Filter Synchronization Architecture Audit

## Executive Summary
A critical architectural flaw exists in the global filter pipeline, causing a P0 desynchronization between the UI state and the actual data state. This bug specifically affects the **Location** and **Business Unit (MP/PB)** filters when navigating between dashboards. The root cause lies in Streamlit's implicit garbage collection of widget keys during aborted script runs triggered by sidebar navigation.

## Observed Behaviour Explained
1. **User interacts with a filter** (e.g., selects "Indore"). The widget returns `["Indore"]`, `df` is filtered correctly, and the dashboard displays "Indore" data.
2. **User clicks a sidebar navigation button** (e.g., "Executive").
3. **The Navigation Callback executes `st.rerun()`**. Because `sidebar_navigation()` is located at the top of `app.py` (line 673), the script execution is immediately aborted *before* it reaches `render_month_picker()` (line 706).
4. **Streamlit Garbage Collection**: At the end of the aborted run, Streamlit assumes that any widget not rendered during that run has been permanently removed from the application. It therefore **deletes** the widget keys `filter_location` and `filter_mp_pb` from `st.session_state`.
5. **The New Run Begins**: When the next run executes, the widgets are initialized from scratch since their session state keys were deleted. They return their default values (e.g., `[]` for Location, `"All"` for MP/PB).
6. **Data Loads Unfiltered**: `render_global_filters()` reads the deleted/default state, receiving `[]` and `"All"`. It skips the filter logic and passes the **ALL DATA** (unfiltered) dataframe to the dashboard.
7. **UI Desynchronization**: Due to React DOM reconciliation and frontend rendering speed, the browser may retain the visual selection ("Indore") on screen, even though the Python backend has reset the widget to `[]`. This creates the dangerous state where the UI claims data is filtered, but the charts represent the entire group.

## Why Other Filters Survive
The architecture audit reveals why other global filters (Month, Comparison Mode, Service Type) do **not** suffer from this bug:
They implement a **Persistent State Backup** pattern.

*   **Month Filter**: Uses `key="ui_selected_months"` but immediately backs up the value to `st.session_state.selected_months_custom`.
*   **Comparison Mode**: Uses `key="ui_comparison_mode_radio"` and backs up to `st.session_state.comparison_mode_radio`.
*   **Business View (Labour)**: Uses `key="lab_biz_ui"` and backs up via `StateManager.set("lab_business_view", new_b)`.

**Location** and **Business Unit (MP/PB)** are uniquely vulnerable because their widget keys (`filter_location`, `filter_mp_pb`) are used directly as the canonical source of truth by `render_global_filters()`. They lack a persistent backup key.

## Recommended Corrective Action

Do not attempt to fix this with caching. The fix requires implementing the Persistent State Backup pattern for the vulnerable filters.

1.  **Separate Widget Keys from State Keys**:
    *   Rename the multiselect widget key to `ui_filter_location`.
    *   Rename the segmented control widget key to `ui_filter_mp_pb`.
2.  **Initialize Widgets from Persistent State**:
    *   Pass `default=st.session_state.get("filter_location", [])` to the Location multiselect.
    *   Pass `default=st.session_state.get("filter_mp_pb", "All")` to the MP/PB control.
3.  **Backup Widget Returns Synchronously**:
    *   Assign the widget's return value to the persistent state key immediately after declaration:
        ```python
        ui_loc = st.multiselect(..., key="ui_filter_location", default=st.session_state.get("filter_location", []))
        st.session_state.filter_location = ui_loc
        ```
4.  **No changes required to `render_global_filters()`**: It will continue to read from the persistent `filter_location` and `filter_mp_pb` keys, which will now safely survive `st.rerun()` aborts.

## Validation Status
The root cause has been formally documented without modifying production code. The application is ready for the fix to be implemented prior to Production Freeze.
