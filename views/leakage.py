import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from io import BytesIO
from datetime import datetime



from services.financial_service import FinancialService
from utils.calculations.fact_metrics import (
    get_labour_sales, get_parts_sales, get_net_labour, get_net_parts,
    get_labour_discount, get_parts_discount, get_oil_sales, get_tyre_sales,
    get_battery_sales, get_accessory_sales, get_total_margin, get_parts_profit,
    get_jobcard_count
)
from utils.calculations.revenue import (
    calculate_gross_revenue, calculate_net_revenue, calculate_total_revenue,
    calculate_revenue_per_jobcard, calculate_revenue_growth
)
from utils.calculations.margin import (
    calculate_total_margin, calculate_parts_margin, calculate_margin_per_jobcard,
    calculate_margin_growth, calculate_margin_kpis
)
from utils.calculations.discount import (
    calculate_labour_discount, calculate_parts_discount, calculate_total_discount,
    calculate_labour_discount_pct, calculate_parts_discount_pct,
    calculate_overall_discount_pct, calculate_discount_per_jobcard,
    calculate_discount_growth
)
from utils.calculations.leakage import (
    compute_discount_aggregates, compute_parts_leakage, compute_leakage_delta
)
from utils.calculations.common import (
    safe_divide, calc_ratio, calc_growth_pct, calc_contribution_pct,
    calc_achievement_pct, calc_variance
)
from utils.aggregations import (
    group_summary, location_summary, advisor_summary, monthly_summary,
    service_summary, dealer_summary, pivot_summary, top_n
)
from utils.filters import (
    apply_month_filter, apply_location_filter, apply_location_group_filter,
    apply_service_type_filter, apply_advisor_filter, apply_mp_pb_filter, split_cp_pp,
    filter_valid_advisors
)
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num
from utils.constants import ADV_COL, MP_COLORS, C
from config.settings import LABOUR_DISC_BENCH, PARTS_DISC_BENCH, HIGH_DISC_ALERT

# Import shared UI helpers from app
from ui.components import KPIGrid, MetricCard
from ui.tables import html_table
from ui.traffic import yoy_badge, traffic_light, tgt_badge
from ui.helpers import apply_chart, clean_hover, _render_finding, render_discount_heatmap, render_alerts

def render(df, pairs, comparison_mode=True, selected_months=None):
    with st.spinner("Computing Leakage..."):
        if df.empty:
            from ui.components.core import EmptyState
            EmptyState('No data available for the selected period. Adjust your filters or check data freshness.')
            return

    cp_months = selected_months if selected_months else []
    pp_months = [p[1] for p in pairs]
    cp = apply_month_filter(df, "Month Name", cp_months) if cp_months else df.copy()
    pp = apply_month_filter(df, "Month Name", pp_months) if pp_months else pd.DataFrame(columns=df.columns)
    if cp.empty:
        st.warning("No data for the selected period.")
        return

    LAB_BENCH   = LABOUR_DISC_BENCH
    PARTS_BENCH = PARTS_DISC_BENCH

    # ── Pre-compute all aggregates upfront ───────────────────────
    loc_lab  = compute_discount_aggregates(cp, "Location Name", LAB_BENCH)
    loc_parts = compute_parts_leakage(cp, "Location Name", PARTS_BENCH)

    if not loc_lab.empty and not loc_parts.empty:
        loc_merged = loc_lab.merge(
            loc_parts[["Location Name", "Recoverable"]], on="Location Name",
            suffixes=("_lab", "_parts"), how="left"
        ).fillna(0)
        loc_merged["Total_Leakage"] = loc_merged["Recoverable_lab"] + loc_merged["Recoverable_parts"]
        loc_merged = loc_merged.sort_values("Total_Leakage", ascending=False).reset_index(drop=True)
    elif not loc_lab.empty:
        loc_merged = loc_lab.copy()
        loc_merged.rename(columns={"Recoverable": "Recoverable_lab"}, inplace=True)
        loc_merged["Recoverable_parts"] = 0.0
        loc_merged["Total_Leakage"] = loc_merged["Recoverable_lab"]
        loc_merged = loc_merged.sort_values("Total_Leakage", ascending=False).reset_index(drop=True)
    else:
        loc_merged = pd.DataFrame()

    adv_lab = filter_valid_advisors(cp, ADV_COL).groupby([ADV_COL, "Location Name"], dropna=False).agg(
        JCs=("JC_Nos.", "sum"), Revenue=("Pre-GST Labour", "sum"), DiscRs=("Labour Discount", "sum")
    ).reset_index()
    adv_lab = adv_lab[adv_lab["Revenue"] > 0].copy()
    if not adv_lab.empty:
        adv_lab["Disc_Pct"] = calc_ratio(adv_lab["DiscRs"], adv_lab["Revenue"], multiplier=100, fill_value=0)
        adv_lab["Leakage"]  = np.maximum(0, (adv_lab["Disc_Pct"] - LAB_BENCH) / 100 * adv_lab["Revenue"])
        adv_lab = adv_lab.sort_values("Leakage", ascending=False).reset_index(drop=True)

    total_lab_disc   = calculate_labour_discount(cp)
    total_parts_disc = calculate_parts_discount(cp)
    total_lab_rev    = get_labour_sales(cp)
    total_parts_rev  = get_parts_sales(cp)
    total_rev        = calculate_gross_revenue(cp)
    total_lab_leakage   = loc_lab["Recoverable"].sum()   if not loc_lab.empty   else 0
    total_parts_leakage = loc_parts["Recoverable"].sum() if not loc_parts.empty else 0
    total_recoverable   = total_lab_leakage + total_parts_leakage
    overall_disc_pct    = calculate_overall_discount_pct(cp)
    locs_above_bench    = int((loc_lab["Disc_Pct"] > LAB_BENCH).sum()) if not loc_lab.empty else 0

    # ── Hero KPIs ────────────────────────────────────────────────
    st.markdown('<div class="section-card"><div class="section-title">💸 Leakage Summary</div>', unsafe_allow_html=True)
    c = st.columns(5)
    with c[0]: kpi("Labour Leakage ₹",     fmt_inr(total_lab_leakage))
    with c[1]: kpi("Parts Leakage ₹",      fmt_inr(total_parts_leakage))
    with c[2]: kpi("Total Recoverable ₹",  fmt_inr(total_recoverable))
    with c[3]: kpi("Leakage % of Revenue", f"{overall_disc_pct:.1f}%")
    with c[4]: kpi("Locs Above Benchmark", str(locs_above_bench))
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Location Leakage Table ────────────────────────────────────
    st.markdown('<div class="section-card"><div class="section-title">📍 Location Leakage Table</div>', unsafe_allow_html=True)
    if not loc_merged.empty:
        def _sev(d_pct):
            if d_pct >= 20: return "🔴"
            if d_pct >= 15: return "🟡"
            return "🟢"
        disp_loc = pd.DataFrame({
            "Location":       loc_merged["Location Name"],
            "Labour Rev":     loc_merged["Revenue"].apply(fmt_inr),
            "Lab Disc %":     loc_merged["Disc_Pct"].apply(lambda x: f"{x:.1f}%"),
            "Labour Leakage": loc_merged["Recoverable_lab"].apply(fmt_inr),
            "Parts Leakage":  loc_merged["Recoverable_parts"].apply(fmt_inr),
            "Total Leakage":  loc_merged["Total_Leakage"].apply(fmt_inr),
            "":               loc_merged["Disc_Pct"].apply(_sev),
        })
        html_table(disp_loc, height="400px")
    else:
        st.info("No location data available")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Advisor Leakage Table ─────────────────────────────────────
    st.markdown('<div class="section-card"><div class="section-title">🎯 Advisor Leakage Table</div>', unsafe_allow_html=True)
    if not adv_lab.empty:
        disp_adv = pd.DataFrame({
            "Advisor":        adv_lab[ADV_COL],
            "Location":       adv_lab["Location Name"],
            "JCs":            adv_lab["JCs"].apply(fmt_num),
            "Lab Disc %":     adv_lab["Disc_Pct"].apply(lambda x: f"{x:.1f}%"),
            "Labour Leakage": adv_lab["Leakage"].apply(fmt_inr),
        })
        html_table(disp_adv, height="400px")
    else:
        st.info("No advisor data available")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Heatmap ──────────────────────────────────────────────────
    heat_view = st.radio("Heatmap View", ["By Location", "By Advisor"], horizontal=True, key="lc_heat_view")
    st.markdown('<div class="section-card"><div class="section-title">🗺️ Recoverable Leakage Heatmap</div>', unsafe_allow_html=True)
    render_discount_heatmap(cp, heat_view, "lc")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Leakage Trend ─────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-card"><div class="section-title">📉 Labour Discount % Trend</div>', unsafe_allow_html=True)
        ltr = monthly_summary(cp, as_index=False).agg(
            L=("Pre-GST Labour", "sum"), D=("Labour Discount", "sum")
        ).sort_values("Month_Sort")
        ltr["D%"] = calc_ratio(ltr["D"], ltr["L"], multiplier=100, fill_value=0)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=ltr["Month Name"], y=ltr["D%"], name="Labour Disc%", marker_color=C["primary"]))
        fig.add_hline(y=LAB_BENCH, line_dash="dash", line_color=C["red"], annotation_text=f"{LAB_BENCH}% Benchmark")
        apply_chart(fig, "Labour Discount % vs Benchmark", 300)
        st.plotly_chart(fig, width='stretch', key="lc_lab_trend",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d", "lasso2d"],
                                "toImageButtonOptions": {"format": "png", "scale": 2}})
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="section-card"><div class="section-title">📉 Parts Discount % Trend</div>', unsafe_allow_html=True)
        ptr = monthly_summary(cp, as_index=False).agg(
            L=("Pre-GST Parts", "sum"), D=("Parts Discount", "sum")
        ).sort_values("Month_Sort")
        ptr["D%"] = calc_ratio(ptr["D"], ptr["L"], multiplier=100, fill_value=0)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=ptr["Month Name"], y=ptr["D%"], name="Parts Disc%", marker_color=C["orange"]))
        fig.add_hline(y=PARTS_BENCH, line_dash="dash", line_color=C["red"], annotation_text=f"{PARTS_BENCH}% Benchmark")
        apply_chart(fig, "Parts Discount % vs Benchmark", 300)
        st.plotly_chart(fig, width='stretch', key="lc_pts_trend",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d", "lasso2d"],
                                "toImageButtonOptions": {"format": "png", "scale": 2}})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Top 5 Recovery Opportunities ─────────────────────────────
    st.markdown('<div class="section-card"><div class="section-title">💎 Top 5 Recovery Opportunities</div>', unsafe_allow_html=True)
    if not loc_merged.empty:
        opps = loc_merged[loc_merged["Total_Leakage"] > 0].head(5)
        if opps.empty:
            st.info("No recovery opportunities identified — all locations within benchmark")
        for _, row in opps.iterrows():
            lab_pct = row["Disc_Pct"]
            cause   = f"Labour discount at {lab_pct:.1f}% (benchmark {LAB_BENCH}%)"
            owner   = "Service Head" if lab_pct > 25 else "Location Manager"
            priority = "High" if lab_pct > 25 else "Medium"
            _render_finding(
                finding=f"{row['Location Name']} Leakage",
                cause=cause,
                impact=fmt_inr(row["Total_Leakage"]),
                recommendation="Review labour discounting practices",
                owner=owner,
                priority=priority
            )
    else:
        st.info("No location data to evaluate")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Management Actions ────────────────────────────────────────
    st.markdown('<div class="section-card"><div class="section-title">✅ Management Actions</div>', unsafe_allow_html=True)
    actions = []

    if not loc_lab.empty:
        over_bench = loc_lab[loc_lab["Disc_Pct"] > LAB_BENCH].sort_values("Disc_Pct", ascending=False)
        if not over_bench.empty:
            w = over_bench.iloc[0]
            actions.append(("red", f"Immediate: Review discount approvals at {w['Location Name']} — {w['Disc_Pct']:.1f}% vs {LAB_BENCH}% benchmark"))

    if not adv_lab.empty and adv_lab.iloc[0]["Leakage"] > 0:
        ta = adv_lab.iloc[0]
        actions.append(("red", f"Investigate: {ta[ADV_COL]} ({ta['Location Name']}) has {fmt_inr(ta['Leakage'])} labour leakage ({ta['Disc_Pct']:.1f}% discount)"))

    if not loc_parts.empty:
        parts_over = loc_parts[loc_parts["Disc_Pct"] > PARTS_BENCH]
        if not parts_over.empty:
            actions.append(("yellow", f"Review parts discount approvals at {len(parts_over)} location(s) exceeding {PARTS_BENCH}% benchmark"))

    if total_recoverable > 100000:
        actions.append(("yellow", f"Group-wide: {fmt_inr(total_recoverable)} recoverable through discount controls — initiate quarterly review"))

    if not adv_lab.empty:
        multi = adv_lab[adv_lab["Disc_Pct"] > LAB_BENCH].groupby("Location Name").size()
        multi = multi[multi >= 3]
        if not multi.empty:
            ln = multi.index[0]
            actions.append(("red", f"Systemic issue at {ln} — {multi.iloc[0]} advisors above benchmark. Review branch discount controls."))

    if actions:
        render_alerts(actions)
    else:
        st.success("✅ All locations and advisors within discount benchmarks")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Drilldown ─────────────────────────────────────────────────
    st.markdown('<div class="section-card"><div class="section-title">🔍 Drilldown</div>', unsafe_allow_html=True)
    dc1, dc2 = st.columns(2)
    with dc1:
        all_locs = sorted(cp["Location Name"].dropna().unique().tolist())
        sel_loc  = st.selectbox("Drill into Location", ["— Select —"] + all_locs, key="lc_drilldown_loc")
    with dc2:
        all_advs = sorted(cp[ADV_COL].dropna().unique().tolist())
        sel_adv  = st.selectbox("Drill into Advisor",  ["— Select —"] + all_advs, key="lc_drilldown_adv")

    if sel_loc != "— Select —":
        loc_data = cp[cp["Location Name"] == sel_loc]
        if not loc_data.empty:
            st.markdown(f"##### 📍 {sel_loc} — Advisor Leakage Breakdown")
            adv_drill = advisor_summary(loc_data, adv_col=ADV_COL, as_index=True).agg(
                JCs=("JC_Nos.", "sum"), Revenue=("Pre-GST Labour", "sum"), DiscRs=("Labour Discount", "sum"),
                PartRev=("Pre-GST Parts", "sum"), PartDisc=("Parts Discount", "sum")
            ).reset_index()
            adv_drill = adv_drill[adv_drill["Revenue"] > 0].copy()
            if not adv_drill.empty:
                adv_drill["Lab Disc %"]    = calc_ratio(adv_drill["DiscRs"], adv_drill["Revenue"], multiplier=100, fill_value=0)
                adv_drill["Lab Leakage"]   = np.maximum(0, (adv_drill["Lab Disc %"] - LAB_BENCH) / 100 * adv_drill["Revenue"])
                adv_drill["Parts Disc %"]  = calc_ratio(adv_drill["PartDisc"], adv_drill["PartRev"], multiplier=100, fill_value=0)
                adv_drill["Parts Leakage"] = np.maximum(0, (adv_drill["Parts Disc %"] - PARTS_BENCH) / 100 * adv_drill["PartRev"])
                adv_drill["Total Leakage"] = adv_drill["Lab Leakage"] + adv_drill["Parts Leakage"]
                adv_drill = adv_drill.sort_values("Total Leakage", ascending=False)
                disp_drill = pd.DataFrame({
                    "Advisor":       adv_drill[ADV_COL],
                    "JCs":           adv_drill["JCs"].apply(fmt_num),
                    "Lab Disc %":    adv_drill["Lab Disc %"].apply(lambda x: f"{x:.1f}%"),
                    "Lab Leakage":   adv_drill["Lab Leakage"].apply(fmt_inr),
                    "Parts Disc %":  adv_drill["Parts Disc %"].apply(lambda x: f"{x:.1f}%"),
                    "Parts Leakage": adv_drill["Parts Leakage"].apply(fmt_inr),
                    "Total Leakage": adv_drill["Total Leakage"].apply(fmt_inr),
                })
                html_table(disp_drill, height="350px")

    if sel_adv != "— Select —":
        adv_monthly = cp[cp[ADV_COL] == sel_adv].groupby(["Month_Sort", "Month Name"], dropna=False).agg(
            JCs=("JC_Nos.", "sum"), Revenue=("Pre-GST Labour", "sum"), DiscRs=("Labour Discount", "sum")
        ).reset_index()
        adv_monthly = adv_monthly[adv_monthly["Revenue"] > 0].copy()
        if not adv_monthly.empty:
            st.markdown(f"##### 👤 {sel_adv} — Monthly Leakage Breakdown")
            adv_monthly["Lab Disc %"] = calc_ratio(adv_monthly["DiscRs"], adv_monthly["Revenue"], multiplier=100, fill_value=0)
            adv_monthly["Leakage"]    = np.maximum(0, (adv_monthly["Lab Disc %"] - LAB_BENCH) / 100 * adv_monthly["Revenue"])
            adv_monthly = adv_monthly.sort_values("Month_Sort")
            disp_adv_drill = pd.DataFrame({
                "Month":      adv_monthly["Month Name"],
                "JCs":        adv_monthly["JCs"].apply(fmt_num),
                "Revenue":    adv_monthly["Revenue"].apply(fmt_inr),
                "Lab Disc %": adv_monthly["Lab Disc %"].apply(lambda x: f"{x:.1f}%"),
                "Leakage":    adv_monthly["Leakage"].apply(fmt_inr),
            })
            html_table(disp_adv_drill, height="250px")
    st.markdown('</div>', unsafe_allow_html=True)

