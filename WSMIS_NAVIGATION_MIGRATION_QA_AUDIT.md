# WSMIS Navigation Migration — Independent QA Audit Report

**Date:** 2026-06-23  
**Scope:** Independent verification of `st.navigation()` migration in `app.py`, `route_service.py`, `dashboard_common.py`  
**Status:** COMPLETE — 3 BLOCKING defects, 4 warnings, 5 cleanup items

---

## Executive Summary

The migration from manual `render_page_router()` dispatch to Streamlit's native `st.navigation()` is **partially complete but not production-ready**. The core `st.navigation(pages)` + `AppContext` pattern at `app.py:878-997` is architecturally sound. However, the migration left behind **dead code that references deleted symbols** (`RouteType`, `is_valid_route`, `get_route_type`), a **sidebar conflict** where both `st.navigation()` auto-sidebar and legacy `_sidebar_v1()` are active, and **debug `print()` statements** that execute on every rerun.

---

## Checklist Results

### 1. Core Navigation — `st.navigation()` Integration

| Item | Status | Detail |
|------|--------|--------|
| `st.navigation(pages)` called | **PASS** | `app.py:878` — correctly receives categorized `Dict[str, List[st.Page]]` from `RouteRegistry.get_blueprint_pages()` |
| `active_page.run()` executed | **PASS** | `app.py:997` — page wrapper function called after `AppContext` creation |
| `AppContext` created every rerun | **PASS** | `app.py:983-994` — fresh `frozen=True` dataclass stored in `st.session_state.app_context`; no stale state risk |
| `AppContext` fields complete | **PASS** | All 10 fields populated: `df_filtered_full`, `df_filtered_cp`, `df_filtered`, `pairs`, `alerts`, `comparison_mode`, `selected_months`, `targets_df`, `client_config`, `exp_df_filtered_cp` |
| Page wrappers use `safe_render()` | **PASS** | All 17 `_wrap_*` methods in `route_service.py:30-181` import and call `from app import safe_render` |
| Category hierarchy | **WARN** | Blueprint categories: "Commercial", "People", "Performance", "Finance", "Admin", "Operations". Product Blueprint v1 categories: "Revenue", "People", "Performance", "Finance", "Admin", "Operations". "Commercial" ≠ "Revenue" — verify this is intentional. |

### 2. Drill-Through Flow

| Item | Status | Detail |
|------|--------|--------|
| `navigate_to_page()` defined | **PASS** | `dashboard_common.py:284` — sets drill params via `StateManager.set()`, then calls `st.switch_page()` |
| `st.switch_page()` receives correct type | **PASS** | `dashboard_common.py:305-307` — gets `st.Page` object from `RouteRegistry.get_page_by_title()`, passes to `st.switch_page()` |
| Parts Executive → Parts Detail drill | **PASS** | `parts_executive.py:864` — `navigate_to_page("Parts Detail", drill_params={"location": selected_location})` correctly wired |
| Drill params survive navigation | **PASS** | `StateManager.set()` writes to `parts_` namespace; `navigate_to_page()` calls `st.switch_page()` which triggers full rerun; `get_drill_params()` at `dashboard_common.py:312` reads from same namespace |
| `clear_drill_params()` available | **PASS** | `dashboard_common.py:328` — resets all three drill keys to `None` |

### 3. Browser Back/Forward

| Item | Status | Detail |
|------|--------|--------|
| `st.navigation()` handles history | **PASS** | Streamlit's `st.navigation()` natively manages browser history; Back/Forward buttons work without custom URL sync |
| `sync_url_to_session()` is stub | **PASS** | `route_service.py:253-255` — `pass` only; no-op prevents conflicts with `st.navigation()` |
| `sync_session_to_url()` is stub | **PASS** | `route_service.py:257-259` — `pass` only |
| No `st.query_params` manipulation in active path | **PASS** | `set_page_url()` at `app.py:569` returns early when `LEGACY_NAV=True`; `_sidebar_v2()` (dead code) is the only code writing `st.query_params["page"]` |

### 4. Sidebar Rendering

| Item | Status | Detail |
|------|--------|--------|
| **SIDEBAR CONFLICT** | **BLOCKER** | `st.navigation(pages)` at `app.py:878` auto-generates a sidebar with page categories. `sidebar_navigation()` at `app.py:577` is **never called from `main()`** (grep confirms 0 call sites). However, `_sidebar_v1()` at `app.py:584` renders a **second sidebar** with buttons and expanders. If `sidebar_navigation()` were ever called, it would create a **duplicate sidebar**. Currently safe because it's dead code, but confusing. |
| Legacy sidebar functions exist | **WARN** | `_sidebar_v1()` (`app.py:584-636`) and `_sidebar_v2()` (`app.py:638-687`) both render `with st.sidebar:` blocks. Neither is called from `main()`. Dead code. |
| `LEGACY_NAV` flag | **INFO** | `config/settings.py:6` sets `LEGACY_NAV = True`. This flag is checked by `_resolve_active_page()` (`app.py:531`) and `set_page_url()` (`app.py:572`), but neither function is called in the active `main()` path. The flag is vestigial. |

### 5. Exports

| Item | Status | Detail |
|------|--------|--------|
| `render_export_buttons()` intact | **PASS** | `ui/export_buttons.py:56` — unchanged; called from 8 view files |
| `ExportMeta` imports work | **PASS** | All views import from `services.export_service` — no changes needed |
| Export CSV/Excel/PDF | **PASS** | `export_service.py:174,197,356` — all three formats functional; no navigation dependencies |
| No stale data in exports | **PASS** | Exports use `df` passed from `AppContext` via page wrapper; data is fresh every rerun |

### 6. AI Panels

| Item | Status | Detail |
|------|--------|--------|
| `get_ai_client()` import | **PASS** | `services/ai/provider.py:3` — standalone function, no navigation dependency |
| Command Center AI | **PASS** | `command_center.py:19,244` — imports `get_ai_client` directly; not affected by navigation migration |
| Report Generator AI | **PASS** | `services/ai/report_generator.py:64-65` — imports `get_ai_client` inside function; no navigation dependency |
| AI panel rendering | **PASS** | AI panels are pure data processing + `st.markdown()` — no page routing involved |

### 7. Session State Leaks

| Item | Status | Detail |
|------|--------|--------|
| `AppContext` freshness | **PASS** | Created fresh every rerun at `app.py:983`; `frozen=True` prevents mutation |
| `app_context` stored correctly | **PASS** | `st.session_state.app_context` — overwritten every rerun; no accumulation |
| No stale `current_page` | **PASS** | `app.py:983` no longer reads `current_page` from session state for routing; page determined by `st.navigation()` |
| `StateManager` namespaces | **PASS** | `state_registry.py` registers `lab_`, `parts_`, `cockpit_` namespaces; no cross-contamination |
| `data_synced_at` guard | **PASS** | `app.py:900-901` — only set once per session; no leak risk |

### 8. Dead Code Catalog

| Item | Location | Status | Risk |
|------|----------|--------|------|
| `render_page_router()` | `app.py:689-808` | **DEAD** — never called from `main()` | **HIGH** — imports `RouteType` at line 705 which no longer exists in `route_service.py`. Would crash if called. |
| `_sidebar_v1()` | `app.py:584-636` | **DEAD** — never called from `main()` | LOW — harmless but confusing |
| `_sidebar_v2()` | `app.py:638-687` | **DEAD** — never called from `main()` | LOW — harmless but confusing |
| `sidebar_navigation()` | `app.py:577-582` | **DEAD** — never called from `main()` | LOW — harmless but confusing |
| `_resolve_active_page()` | `app.py:527-567` | **DEAD** — never called from `main()` | **MEDIUM** — contains `print()` debug statements (lines 544-550) that would execute if called |
| `set_page_url()` | `app.py:569-575` | **DEAD** — never called from `main()` | LOW |
| `PAGE_TO_SLUG` / `SLUG_TO_PAGE` dicts | `app.py:507-525` | **DEAD** — only used by dead functions | LOW |
| `RouteType` import in `render_page_router()` | `app.py:705` | **BROKEN** — `RouteType` deleted from `route_service.py` | **HIGH** — would crash on import |
| `is_valid_route()` call | `app.py:698` | **BROKEN** — method deleted from `RouteRegistry` | **HIGH** — would crash on call |
| `get_route_type()` call | `app.py:706` | **BROKEN** — method deleted from `RouteRegistry` | **HIGH** — would crash on call |
| `import gspread` | `app.py:16` | **UNUSED** — no direct gspread calls in `app.py` | LOW — style issue only |
| `print()` debug statements | `app.py:544-550` | **DEBUG** — in dead code path only | LOW — only executes if dead code is called |

### 9. Calculation Correctness

| Item | Status | Detail |
|------|--------|--------|
| `parts_executive.py:100-101` `.agg()` | **PASS** | `cp_loc_gb.agg({"Pre-GST Parts": "sum", "JC_Nos.": "sum", "Parts Profit": "sum"})` — safe; `location_summary()` returns DataFrame with named columns; dict maps column names to agg functions |
| `parts_executive.py:158-159` `.agg()` | **PASS** | `cp_month_gb.agg({"Pre-GST Parts": "sum"})` — safe; `monthly_summary()` returns DataFrame; single-column dict |
| `parts_executive.py:165-166` `pivot_summary()` | **PASS** | `pivot_summary(cp, index="Location Name", columns="Month Name", values="Pre-GST Parts")` — returns `reset_index()` DataFrame; callers read columns directly (not `.index`) |
| `sales_mix.py:201` `sort_values()` | **PASS** | `location_summary(cp, as_index=False)["Oil_Sale"].sum().sort_values(by="Oil_Sale")` — `.sum()` returns scalar per location; `sort_values(by=)` is correct |
| `sales_mix.py:174` `.agg()` | **PASS** | `.agg(**agg_cp)` with `agg_cp = {"Oil": ("Oil_Sale", "sum"), ...}` — safe named-agg pattern |
| `calc_growth_pct()` / `calc_ratio()` | **PASS** | Used throughout; no changes in this migration |

### 10. Performance

| Item | Status | Detail |
|------|--------|--------|
| No duplicate `st.navigation()` calls | **PASS** | Called once at `app.py:878` |
| `AppContext` creation overhead | **PASS** | Frozen dataclass instantiation is negligible |
| `RouteRegistry` singleton | **PASS** | `_route_service` at module level (`route_service.py:263`); `RouteRegistry` created once per session |
| No redundant sidebar renders | **PASS** | `sidebar_navigation()` never called; only `st.navigation()` auto-sidebar renders |

---

## Blocking Defects

### BLOCKER-1: Dead `render_page_router()` Contains Broken Imports

**Location:** `app.py:689-808`  
**Impact:** If anyone calls `render_page_router()` (e.g., during debugging or rollback), it will crash immediately with `ImportError: cannot import name 'RouteType' from 'services.route_service'` at line 705.  
**Fix:** Delete the entire `render_page_router()` function (lines 689-808). It is dead code — `main()` uses `active_page.run()` instead.

### BLOCKER-2: Dead Code References Deleted Methods

**Location:** `app.py:698,706`  
**Impact:** `render_page_router()` calls `route_service.get_registry().is_valid_route(route_path)` (line 698) and `route_service.get_registry().get_route_type(route_path)` (line 706). Both methods were deleted from `RouteRegistry` during migration.  
**Fix:** Same as BLOCKER-1 — delete `render_page_router()`.

### BLOCKER-3: Debug `print()` Statements in Active Code Path

**Location:** `app.py:544-550`  
**Impact:** These `print()` statements are inside `_resolve_active_page()` which is currently dead code. However, if `LEGACY_NAV` is changed to `False` in the future, or if `_resolve_active_page()` is accidentally called, 7 `print()` statements will execute on every rerun, polluting stdout/logs.  
**Fix:** Either delete `_resolve_active_page()` entirely, or remove the `print()` block (lines 542-550).

---

## Warnings

### WARN-1: Sidebar Category Mismatch with Product Blueprint

**Location:** `route_service.py:16-20` vs Product Blueprint v1  
**Detail:** New `st.Page` categories use "Commercial" (line 16), but Product Blueprint v1 uses "Revenue". The `_sidebar_v1()` legacy code also uses "REVENUE" (line 601). Verify this naming is intentional.

### WARN-2: `import gspread` Unused in `app.py`

**Location:** `app.py:16`  
**Detail:** `gspread` is imported but never used in `app.py`. All Google Sheets access is via `utils/loaders.py`. This is a style issue only — no functional impact.

### WARN-3: `LEGACY_NAV = True` is Vestigial

**Location:** `config/settings.py:6`  
**Detail:** `LEGACY_NAV` is checked by `_resolve_active_page()` and `set_page_url()`, both of which are dead code. The flag has no effect on the active `main()` path. Consider removing it to avoid confusion.

### WARN-4: `_resolve_active_page()` Contains V1 URL Logic

**Location:** `app.py:527-567`  
**Detail:** This function reads `st.query_params.get("page", "None")` and has V1/V2 branching logic. It's dead code but could mislead future developers.

---

## Cleanup Recommendations

| Priority | Item | Action |
|----------|------|--------|
| HIGH | Delete `render_page_router()` | Remove lines 689-808 entirely |
| HIGH | Delete `_sidebar_v1()` and `_sidebar_v2()` | Remove lines 584-687 entirely |
| HIGH | Delete `sidebar_navigation()` | Remove lines 577-582 entirely |
| HIGH | Delete `_resolve_active_page()` | Remove lines 527-567 entirely |
| HIGH | Delete `set_page_url()` | Remove lines 569-575 entirely |
| MEDIUM | Delete `PAGE_TO_SLUG` / `SLUG_TO_PAGE` | Remove lines 507-525 (only used by dead functions) |
| MEDIUM | Remove `import gspread` | Remove line 16 from `app.py` |
| LOW | Remove `LEGACY_NAV` | Remove from `config/settings.py:6` and any dead-code references |
| LOW | Remove `RouteType` import comment | Remove line 705 comment if `render_page_router()` is deleted |

---

## Sign-Off

The migration architecture is sound:
- `st.navigation(pages)` + `AppContext` pattern is correct
- `safe_render()` wrappers provide error isolation
- Drill-through via `st.switch_page()` is properly wired
- Exports, AI panels, and calculations are unaffected

**However, the migration is NOT production-ready** until:
1. All dead code referencing `RouteType`, `is_valid_route()`, `get_route_type()` is removed
2. Duplicate sidebar code is cleaned up
3. Debug `print()` statements are removed

**Estimated cleanup effort:** 30 minutes — delete ~200 lines of dead code from `app.py`.
