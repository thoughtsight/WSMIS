# Labour Revenue Page — Revision 3 Implementation Summary

## File Modified

`views/labour.py` (749 → 1027 lines)

## Verification

- Syntax: **OK**
- Full module import: **OK**
- All 7 Plotly chart patterns: **OK**
- All formatters: **OK**
- `get_jobcard_count` import: **OK**

---

## What Changed

| Area | Before | After |
|---|---|---|
| **Session state** | 4 keys (2 page-local) | 17 keys (full page-local ownership) |
| **Period/Comparison** | Read-only from app.py | Interactive page controls, recomputed locally |
| **Business View** | MP/PB from global state | All/Workshop/Bodyshop, page-local |
| **Location filter** | Cross-filter only | Single/multi toggle (⊞/⊟) + Section B control |
| **Service type** | Full multiselect with chips | Count-only display |
| **Data preparation** | Single combined dataset | Triple computation: combined + workshop + bodyshop |
| **KPI Tier 1** | 4 cards (incl. Absolute Growth) | 3 cards (Absolute Growth removed) |
| **KPI Tier 2** | 4 cards (incl. Neg Labour + buttons) | 4 cards (Active Svc Types replaces Neg Labour, read-only, single-location edge case) |
| **Neg Labour** | Always rendered + success fallback | Conditional (n>0 only), no success message |
| **Charts** | Stacked vertically | Trend + Service Mix side by side [3,2] |
| **Heatmap** | Sets individual cross-filters | Sets both loc + month chips simultaneously |
| **Waterfalls** | Sets cross-filter only | Sets chip AND opens drill-down panel |
| **Drill-down** | Tied to cross-filter state | Decoupled (`lab_drill_*` keys), close doesn't clear chips |
| **Executive table** | Single table | Two tabs: Performance + YoY Comparison |
| **AI narrative** | Basic payload | Workshop/Bodyshop attribution when View=All |
| **Opps/Actions** | Basic payload | Workshop/Bodyshop summary when View=All |

---

## Components Removed

- Absolute Growth KPI card (duplicate of CP Revenue delta)
- "Filter to X" buttons on Best/Worst location cards (diagnostic cards are read-only)
- Period badge as separate element (now lives in Section B summary line)
- "Reset Page" floating text link (now Section B button)
- MP/PB segmented control (replaced by Workshop/Bodyshop/All)
- All 14 service type chips rendered inline (replaced by count-only dropdown + Section C chips)
- Any st.write/st.markdown that repeats a number already shown in a KPI card
- Red left border on KPI cards (audit alerts belong only in Section G)
- "Neg Labour Alerts" row inside Tier 2 KPI cards (belongs only in Section G)
- `st.success("No negative labour detected...")` fallback message

---

## Components Added

- Section B: Business View segmented control (All / Workshop / Bodyshop)
- Section B: Location filter with single/multi toggle (⊞ / ⊟)
- Section B: Dynamic period summary line (plain text, one instance only)
- Section C: Active Cross-Filter Bar (conditional, chips only, individually removable)
- Section I: Location Growth Heatmap (diverging color scale, click sets two chips)
- Section L Tab 2: YoY Comparison table (Lab_CP | Lab_PP | YoY% per month per location)
- Section G: Collapsible audit zone for negative labour (conditional on n > 0)

---

## Comparison Rules Implemented

When Business View = "All":

- Overall KPIs = Workshop + Bodyshop combined
- Every analysis section internally calculates:
  - Workshop vs Workshop
  - Bodyshop vs Bodyshop
- Never compares Workshop growth against Bodyshop growth
- AI narrative attributes source: "Workshop contributed +₹18.2L (PMS), while Bodyshop declined ₹6.1L due to BR"

### Business View behavior:

- **All** → Show Combined + internally analyse Workshop and Bodyshop separately
- **Workshop** → Exclude BR completely
- **Bodyshop** → Include only BR

---

## Session State Keys (17)

| Key | Type | Default | Set By |
|---|---|---|---|
| `lab_period` | str | None (init from pairs) | Section B control |
| `lab_comparison` | str | None (init from app.py) | Section B control |
| `lab_business_view` | str | "All" | Section B control |
| `lab_loc_mode` | str | "single" | Section B toggle |
| `lab_location` | str/list | "All" | Section B control |
| `lab_service_types` | list | [] (all) | Section B control |
| `lab_cross_loc` | str/None | None | Chart/waterfall click |
| `lab_cross_month` | str/None | None | Chart/heatmap click |
| `lab_cross_svc` | str/None | None | Chart click |
| `lab_drill_open` | bool | False | Waterfall click |
| `lab_drill_type` | str/None | None | Waterfall click |
| `lab_drill_value` | str/None | None | Waterfall click |
| `lab_ai_hash` | str/None | None | AI section |
| `lab_ai_narrative` | str/None | None | AI section |
| `lab_ai_opps` | str/None | None | AI section |

---

## Filter Hierarchy (7 levels, applied in order)

1. **Period** → `_resolve_period()` produces active_pairs from `lab_period` + `lab_comparison`
2. **Business View** → Workshop: exclude BR / Bodyshop: only BR
3. **Location** → Single: exact match / Multi: isin list
4. **Service Type** → If not empty: isin selected
5. **Cross-filter loc** → If set: exact match
6. **Cross-filter month** → If set: restrict CP to that month, PP to paired month
7. **Cross-filter svc** → If set: exact match

---

## Data Preparation

```python
_prepare_datasets(cp, pp, df) → {
    "combined":  _compute_metrics(cp, pp, df),           # Workshop + Bodyshop
    "workshop":  _compute_metrics(cp[ws], pp_ws, df_ws),  # Service Type != BR
    "bodyshop":  _compute_metrics(cp[bs], pp_bs, df_bs),  # Service Type == BR
}
```

Display sections use `datasets["combined"]`.
AI sections (D, M) receive all three datasets for attribution.

---

## Section Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ A. Universal Header (UniversalHeader)                            │
├──────────────────────────────────────────────────────────────────┤
│ B. Global Control Bar                                            │
│    [3M ▾] [YoY|MoM] [All|Workshop|Bodyshop] [Location ⊞]       │
│    [14 service types ▾]                           [⟳ Reset]     │
│    Showing: Apr-2026 → Jun-2026 vs Apr-2025 → Jun-2025 (YoY)   │
├──────────────────────────────────────────────────────────────────┤
│ C. Active Cross-Filter Bar (conditional)                         │
│    Filtered by: 📍 GBS ✕  📅 Jun-2026 ✕  🔧 PMS ✕  [Clear]   │
├──────────────────────────────────────────────────────────────────┤
│ D. AI Executive Insight Band (2 sentences, workshop/bodyshop)   │
├──────────────────────────────────────────────────────────────────┤
│ E. Tier 1 KPIs (3 cards)                                         │
│    [CP Revenue] [PP Revenue] [Revenue per Jobcard]              │
├──────────────────────────────────────────────────────────────────┤
│ F. Tier 2 KPIs (4 cards, read-only)                             │
│    [Best Loc] [Worst Loc] [Locations Growing] [Active Svc Types]│
├──────────────────────────────────────────────────────────────────┤
│ G. ⚠ Negative Labour Audit (conditional, collapsed)             │
├──────────────────────────────────────────────────────────────────┤
│ H. Charts [3:2]                                                  │
│    [Revenue Trend] [Service Type Mix]                            │
├──────────────────────────────────────────────────────────────────┤
│ I. Location Growth Heatmap (full width, diverging colors)        │
├──────────────────────────────────────────────────────────────────┤
│ J. Waterfall Bridges [1:1]                                       │
│    [Location Bridge] [Service Type Bridge]                       │
├──────────────────────────────────────────────────────────────────┤
│ K. Drill-Down Panel (conditional, dashed border)                 │
├──────────────────────────────────────────────────────────────────┤
│ L. Executive Table [2 tabs]                                      │
│    [Performance Table] [YoY Comparison]                          │
├──────────────────────────────────────────────────────────────────┤
│ M. Opportunities + Actions (AI-generated, 3+3)                  │
├──────────────────────────────────────────────────────────────────┤
│ N. Universal Footer                                              │
└──────────────────────────────────────────────────────────────────┘
```

---

## Cross-Filter Click Behaviors

| Source | Chips Set | Drill-Down Opens |
|---|---|---|
| Trend chart bar click | 📅 month | No |
| Service Mix segment click | 🔧 service type | No |
| Heatmap cell click | 📍 location + 📅 month | No |
| Location Waterfall bar click | 📍 location | Yes (location breakdown) |
| Service Waterfall bar click | 🔧 service type | Yes (service breakdown) |
| Close drill-down button | Chips preserved | Panel closes |
| Clear all filters chip | All chips removed | Panel closes |
