# WSMIS Product Audit Report

**Application:** Workshop Management Information System v1.0.0-rc1
**Stack:** Python / Streamlit / Plotly / Google Sheets
**Scope:** 19 pages, 6 navigation sections, 5 global filters
**Methodology:** Static code + UI review from 6 stakeholder perspectives

---

## I. EXECUTIVE SUMMARY

WSMIS is a feature-rich, well-engineered Streamlit dashboard for multi-location Maruti Suzuki dealership analytics. It covers revenue, margin, discounts, leakage, advisors, locations, forecasting, expense, P&L, and audit workflows. The Apple-inspired design is visually clean and consistent.

**Overall Score: 7.2/10** -- Strong product with specific, fixable gaps.

| Dimension | Score | Verdict |
|---|---|---|
| Navigation | 7/10 | Logical grouping, but some redundancy |
| Filter Consistency | 6/10 | Inconsistent CP-only vs full-df passing |
| Visual Hierarchy | 8/10 | Strong Apple CSS, occasional flatness |
| KPI Usefulness | 7/10 | Good coverage, some missing business metrics |
| Tables | 6/10 | Functional but no sorting, no search, no pinning |
| Exports | 7/10 | CSV/Excel/PDF present, but inconsistent placement |
| Business Workflow | 6/10 | Data-heavy, action-light |
| Loading Experience | 5/10 | Basic spinners, no skeleton loading |

---

## II. STAKEHOLDER-SPECIFIC FINDINGS

### A. Internal Auditor Perspective

| Issue | Severity | Location |
|---|---|---|
| **Duplicate leakage analysis** -- Leakage Center (pages/leakage.py) and Internal Audit Tab 1 (internal_audit.py) both compute the same location/advisor leakage tables with the same benchmarks (15%/10%). The user sees identical data in two places. | HIGH | leakage.py + internal_audit.py |
| **Duplicate discount trend** -- Discount page shows Labour Disc % Trend with 15% benchmark. Leakage page shows the exact same chart. Internal Audit Tab 3 shows it again. | HIGH | discount.py:95, leakage.py:168, internal_audit.py:192 |
| **No audit trail** -- Findings have "Owner" and "Priority" fields but no status tracking (Open/In-Progress/Closed), no date stamps, no assignment confirmation. | HIGH | All `_render_finding()` calls |
| **No export from Internal Audit** -- The Exception Audit tab (557 lines) has zero export buttons. An auditor cannot download findings. | HIGH | internal_audit.py |
| **Benchmark values hardcoded** -- `LAB_BENCH = 15`, `PARTS_BENCH = 10` appear in leakage.py, internal_audit.py, and discount.py separately. If benchmarks change, 3+ files need manual edits. | MEDIUM | Multiple files |
| **Missing:** Revenue leakage dollar-to-action tracker. The system identifies leakage but never tracks whether corrective action was taken. | HIGH | Gap |

### B. GM / CEO Perspective

| Issue | Severity | Location |
|---|---|---|
| **No executive summary on landing** -- Cockpit (default page) dumps 5 KPIs, alerts, problems, opportunities, trends, and rankings in one long scroll. No "What needs my attention today?" single-line summary. | HIGH | cockpit.py |
| **Cockpit vs Overview vs Executive -- overlapping KPIs** -- All three show Total Revenue, Net Labour, Margin, Discount %, Growth. A CEO opening Cockpit, then Overview, then Executive sees the same 5 numbers three times with slight formatting differences. | HIGH | cockpit.py, overview.py, executive.py |
| **No "Business Health Score"** -- No composite health indicator (e.g., "78/100 - Good") that a CEO can glance at. Each KPI is isolated. | MEDIUM | Gap across all dashboards |
| **No period-over-period trend table** -- Executive page shows narrative text but no structured "This Month vs Last Month vs Same Month Last Year" comparison table. | MEDIUM | executive.py |
| **Missing KPI: Revenue per Location** -- No dedicated "Average revenue per location" or "Revenue concentration" (top 3 locations as % of total) metric. | MEDIUM | Gap |
| **Missing KPI: Customer Retention / Repeat Visit Rate** -- Not available in data, but no mention of it as a limitation. | LOW | Data gap |
| **Forecast disclaimer is buried** -- "Simple linear projection. Actual results may vary" appears as small italic text below charts. A CEO might treat forecasts as commitments. | MEDIUM | trends.py:223 |

### C. Workshop Manager Perspective

| Issue | Severity | Location |
|---|---|---|
| **No job card level drilldown** -- The system shows aggregated JC counts but never lets a Workshop Manager click a number to see individual job cards. The lowest granularity is advisor-level monthly. | HIGH | All pages |
| **No TAT (Turnaround Time) analysis** -- The source sheet is named `JC_TAT(24-25)` suggesting TAT data exists, but no page analyzes turnaround time. | HIGH | Gap |
| **No service type drilldown from Location** -- Location cards show JCs, Labour, Margin but don't break down by service type (PMS, Repairs, etc.). | MEDIUM | locations.py |
| **Targets page only shows WS/BS Labour** -- Workshop managers need Parts targets too, but only Labour and Parts achievement are shown. No target for Oil, Battery, or Consumables. | MEDIUM | targets.py |
| **No "My Location" quick filter** -- A Workshop Manager managing 1 location has to use the sidebar multiselect every time. No "remember my location" or "default to my location" feature. | MEDIUM | app.py global filters |

### D. Finance Head Perspective

| Issue | Severity | Location |
|---|---|---|
| **Expense Analysis and P&L are embedded HTML** -- These render inside `st.components.v1.html()` with fixed heights (2800px, 1400px). They are not filterable by the global sidebar filters. The Finance Head cannot filter expenses by location or advisor. | HIGH | expense.py:102, pnl.py:75 |
| **No margin waterfall on Cockpit** -- The Margin page has a waterfall chart, but the Cockpit (default view) doesn't show margin decomposition. Finance needs to navigate 2 levels deep. | MEDIUM | cockpit.py |
| **No "Discount as % of Margin" KPI** -- Finance wants to see discount leakage as a proportion of total margin earned. This calculation doesn't exist. | MEDIUM | Gap |
| **Missing: Cost per Job Card** -- No "Total cost / JC" metric. Finance has expense data but it's in a separate embedded module not connected to the main KPI system. | HIGH | Gap between expense.py and main dashboard |
| **Duplicate download buttons on Reports page** -- Report 5 (AI Narrative) has two download buttons doing nearly identical things: "Download .txt" and "Download as .txt". | LOW | reports.py:307-321 |
| **No PDF export from Cockpit/Overview** -- The `render_export_buttons()` component exists in `ui/export_buttons.py` but is never used on the main overview pages. Only CSV and Excel are offered. | MEDIUM | overview.py, cockpit.py |

### E. Operations Head Perspective

| Issue | Severity | Location |
|---|---|---|
| **System Health is hidden** -- Only accessible via `?admin=true` URL param. Operations Head may not know this exists. | MEDIUM | app.py:563 |
| **No data freshness SLA** -- "Last Synced" timestamp is shown but there's no alert if data is stale (e.g., >24 hours old). | MEDIUM | app.py |
| **No user activity tracking** -- No way to know which reports are being downloaded, which pages are viewed, which exports are generated. | LOW | Gap |
| **Loading experience is basic** -- `st.spinner("Loading Cockpit...")` is the only feedback. No skeleton screens, no progress bars for heavy operations like report generation. | MEDIUM | All pages |
| **4 embedded HTML modules** -- Expense, P&L, Revenue Leakage, Dealer Audit all render as HTML iframes. These break the filter chain, have their own styling, and feel like separate applications. | HIGH | expense.py, pnl.py, internal_audit.py tabs 2-3 |

### F. Service Advisor Perspective (via Workshop Manager)

| Issue | Severity | Location |
|---|---|---|
| **Advisor name typo preserved** -- `ADV_COL = "Advisior Name"` (misspelling of "Advisor") is hardcoded in constants.py and appears in all exported Excel files and reports. | LOW | constants.py |
| **Advisor Scorecard uses min JC slider default=20** -- New advisors with <20 JCs are excluded from scoring. No way to see their trajectory. | MEDIUM | advisor.py |
| **Coaching Note is generic** -- The auto-generated coaching note in Advisor MoM is rule-based and repetitive. Every advisor with >15% discount gets the same text. | MEDIUM | advisor_mom.py |

---

## III. CROSS-CUTTING ISSUES

### 1. Dashboard Overlap Matrix

| Metric | Cockpit | Overview | Executive | YoY | Leakage | Discount | Internal Audit |
|---|---|---|---|---|---|---|---|
| Total Revenue | YES | YES | YES | | | | |
| Net Labour | | YES | YES | YES | | | |
| Total Margin | YES | YES | YES | | | | |
| Discount % | YES | | YES | | | YES | YES |
| Labour Disc Trend | | | | | YES | YES | YES |
| Location Ranking | YES | YES | | | YES | | |
| Advisor Ranking | YES | | YES | | YES | YES | YES |
| WS/BS Split | YES | YES | YES | YES | | | |

**Verdict:** Labour Discount % Trend appears on **3 separate pages** with the same benchmark line. Advisor leakage appears on **4 pages**. This creates confusion about which page is the "source of truth."

### 2. Filter Inconsistency

Some pages receive `df_filtered_full` (both CP and PP months), others receive `df_filtered_cp` (CP months only). This is inconsistent:

| Page | Data Received | Why |
|---|---|---|
| Cockpit | `df_filtered_full` | Computes CP/PP internally |
| Overview | `df_filtered_full` | Computes CP/PP internally |
| Executive | `df_filtered_full` | Uses CP directly, filters PP |
| Labour/YoY | `df_filtered_full` | Computes CP/PP internally |
| Margin | `df_filtered_cp` | CP only |
| Discounts | `df_filtered_cp` | CP only |
| Leakage | `df_filtered_full` | Computes CP/PP internally |
| Sales Mix | `df_filtered_cp` | CP only |
| Advisors | `df_filtered_cp` | CP only |
| Advisor MoM | `df_filtered_full` | Computes internally |
| Locations | `df_filtered_cp` | CP only |
| Trends | `df_filtered_full` | Computes internally |
| Targets | `df_filtered_cp` | CP only |

This means the comparison (CP vs PP) behavior differs by page. A user switching from Discounts (CP-only, no PP comparison) to Leakage (full, with PP) will see inconsistent delta arrows.

### 3. Visual Hierarchy Issues

- **Emoji overload** -- Section titles use emojis (📊 🚨 🔥 💎 📈 ⚖️ 🎯 🏢 📅). While modern, some emojis render differently across OS/browsers. The 🔥 emoji for "Top 3 Problems" may not convey seriousness to a CEO.
- **All sections have equal visual weight** -- No page uses size, color intensity, or spacing to distinguish "this is the most important section" from "this is supporting detail." Everything is the same card style.
- **KPI cards lack context** -- `kpi("Total Revenue", fmt_inr(cp_rev), f"PP: {fmt_inr(pp_rev)}", cp_rev, pp_rev)` shows a delta arrow but no target or benchmark. Is ₹5Cr good? The user needs external knowledge.

### 4. Color Usage

- **Consistent palette** -- Apple Blue (#0071E3), Green (#34C759), Red (#FF3B30), Orange (#FF9500) used consistently across all pages. This is a strength.
- **WS/BS color coding** -- WS = Blue, BS = Orange is maintained everywhere. Good.
- **Arena/Nexa** -- Arena = Blue, Nexa = Green. But Blue is also used for WS, creating potential confusion when viewing WS data at an Arena location.
- **Heatmap scale** -- Green → Orange → Red is used for discount heatmaps. This is intuitive.

### 5. Table Limitations

- **No column sorting** -- `html_table()` renders static HTML tables. Users cannot sort by any column.
- **No search/filter within tables** -- With 22 locations and 100+ advisors, finding a specific row requires scrolling.
- **No column pinning** -- Location name scrolls away when viewing wide tables (e.g., Targets page with 10 columns).
- **No row click/drilldown** -- Tables are display-only. Clicking a location row should navigate to that location's detail page.

---

## IV. MISSING ITEMS

### Missing KPIs

1. **Revenue per Location** (group average)
2. **Revenue Concentration** (Top 3 locations as % of total)
3. **Discount as % of Margin**
4. **Cost per Job Card** (requires expense data integration)
5. **Labour-to-Parts Ratio** (L100P exists on Trends but not as a KPI card anywhere)
6. **VOR % of JCs** (VOR charges exist but not as a ratio)
7. **Oil Revenue per Litre** (exists on Sales Mix but not on Cockpit)
8. **Cumulative YTD Achievement** (vs annual target)

### Missing Drilldowns

1. **Location → Service Type → Advisor** (3-level hierarchy)
2. **KPI card → underlying data** (clicking "Total Revenue" should show location breakdown)
3. **Chart point → detail table** (clicking a bar in Location Ranking should filter the page)
4. **Executive narrative → source data** (clicking "discount at 18.2%" should show which advisors)

### Missing Executive Summaries

1. **No "Month-End Close" summary** -- A single-page PDF-ready summary for board meetings
2. **No "Weekly Flash"** -- Quick weekly comparison (this week vs last week)
3. **No "Location Report Card"** -- Per-location one-pager with all metrics

### Unnecessary / Redundant Content

1. **Duplicate download buttons on Reports page** (narrative_copy vs narrative_download)
2. **Three overlapping overview pages** (Cockpit, Overview, Executive) -- consider consolidating into one with tabs
3. **Internal Audit Tab 2 & 3** are fully embedded HTML modules with their own filter systems -- these feel like separate apps bolted on

---

## V. SPECIFIC RECOMMENDATIONS

### Quick Wins (No Architecture Change)

| # | Recommendation | Impact | Effort |
|---|---|---|---|
| 1 | Add "Export" button to Internal Audit Tab 1 (Exception Audit findings) | High | Low |
| 2 | Consolidate the 3 duplicate Labour Discount Trend charts into a shared component | Medium | Low |
| 3 | Remove duplicate "Download .txt" / "Download as .txt" on Reports page | Low | Trivial |
| 4 | Add "Sort by" to all `html_table()` calls (column header click) | High | Medium |
| 5 | Add "Search" box above tables with >10 rows | High | Medium |
| 6 | Show System Health in sidebar without `?admin=true` (just label it "Admin") | Medium | Trivial |
| 7 | Add data staleness alert (>24h since last sync) | Medium | Low |
| 8 | Add `st.progress()` for report generation (5 Excel reports) | Medium | Low |
| 9 | Add "Business Health Score" (0-100) to Cockpit as the first KPI | High | Medium |
| 10 | Fix "Advisior Name" typo in exports (or keep as-is if source column is locked) | Low | Trivial |

### Medium-Term Improvements

| # | Recommendation | Impact | Effort |
|---|---|---|---|
| 11 | Merge Cockpit + Overview into a single page with tabbed sub-views | High | Medium |
| 12 | Add "My Location" preference for Workshop Managers (session-state default) | Medium | Low |
| 13 | Connect Expense/P&L modules to global filter chain (replace HTML embeds) | High | High |
| 14 | Add TAT analysis page (data exists in source sheet name) | High | Medium |
| 15 | Add "Discount as % of Margin" KPI to Cockpit | Medium | Low |
| 16 | Add benchmark/target indicators to all KPI cards (not just delta) | High | Medium |
| 17 | Create "Month-End Board Summary" export (single PDF with key charts) | High | Medium |
| 18 | Add row-click drilldown on Location Ranking charts (click → filter to location) | Medium | Medium |
| 19 | Standardize benchmark values into a single config dict (replace hardcoded 15/10) | Medium | Low |
| 20 | Add "Advisor Performance Trend" (rolling 6-month composite score line chart) | Medium | Medium |

---

## VI. FINAL VERDICT BY ROLE

| Role | Would they use daily? | Biggest frustration | Biggest win |
|---|---|---|---|
| **CEO** | Weekly, not daily | Too many pages to find the one number they need | Cockpit alerts + Executive narrative |
| **GM** | Daily | No "action required" queue | Top 3 Problems + Top 3 Opportunities |
| **Workshop Manager** | Daily | No JC-level drilldown, no TAT | Location health cards |
| **Finance Head** | Weekly | Expense/P&L disconnected from filters | Margin waterfall + Discount leakage |
| **Operations Head** | Weekly | Embedded HTML modules feel like separate apps | System Health + data pipeline visibility |
| **Internal Auditor** | Monthly | Duplicate leakage analysis, no export from audit | Exception Audit findings with severity |

---

**Bottom line:** WSMIS is a strong v1.0 with comprehensive coverage of Maruti dealership metrics. The core analytics engine (aggregations, calculations, filters) is solid. The primary gaps are **actionability** (data → decision flow), **consolidation** (reducing duplicate views), and **interactivity** (table sorting, click-through drilldowns). These are UI/UX improvements that don't require architectural changes.
