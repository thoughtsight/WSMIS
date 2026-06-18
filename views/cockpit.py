import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

from services.financial_service import FinancialService
from utils.calculations.fact_metrics import (
    get_labour_sales, get_parts_sales, get_net_labour, get_net_parts,
    get_labour_discount, get_parts_discount, get_oil_sales, get_tyre_sales,
    get_battery_sales, get_accessory_sales, get_total_margin, get_parts_profit,
    get_jobcard_count, get_vor_charges
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
from utils.filters import apply_month_filter
from utils.constants import (
    ADV_COL, CLIENTS, EXCLUDE_SERVICE_TYPES, ARENA_LOCATIONS,
    NEXA_LOCATIONS, PB_SERVICE_TYPES, MONTH_SORT_ORDER, FY_MONTHS, SERVICE_ACCOUNT,
    MP_COLORS
)

# Import shared UI helpers from app
from ui.tables import html_table
from ui.traffic import yoy_badge, traffic_light, tgt_badge
from ui.helpers import apply_chart, clean_hover, _render_finding, render_neg_labour_alert
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num
from config.settings import LABOUR_DISC_BENCH, HIGH_DISC_ALERT, YOY_DECLINE_ALERT, VOR_ALERT_THRESHOLD

# Import new Phase B UI Components
from ui.components import KPIGrid, ChartCard, TableCard

def render(df, pairs, alerts, comparison_mode=True, selected_months=None):
    with st.spinner("Loading Cockpit..."):
        if df.empty:
            from ui.components.core import EmptyState
            EmptyState('No data available for the selected period. Adjust your filters or check data freshness.')
            return

    cp_months = selected_months if selected_months else []
    pp_months = [p[1] for p in pairs]
    cp = apply_month_filter(df, "Month Name", cp_months)
    pp = apply_month_filter(df, "Month Name", pp_months)
    

    def s(d, c): return d[c].sum() if not d.empty else 0

    # ── KPI Cards ────────────────────────────────────────────────
    
    cp_rev = calculate_net_revenue(cp)
    pp_rev = calculate_net_revenue(pp)
    cp_mar = calculate_total_margin(cp)
    pp_mar = calculate_total_margin(pp)
    cp_jc = s(cp, "JC_Nos.")
    pp_jc = s(pp, "JC_Nos.")
    cp_disc = calculate_labour_discount(cp)
    cp_pre_lab = s(cp, "Pre-GST Labour")
    avg_disc = calculate_labour_discount_pct(cp)

    KPIGrid([
        {"label": "Total Revenue", "value": fmt_inr(cp_rev), "cp": cp_rev, "pp": pp_rev},
        {"label": "Total Margin", "value": fmt_inr(cp_mar), "cp": cp_mar, "pp": pp_mar},
        {"label": "Total JCs", "value": fmt_num(cp_jc), "cp": cp_jc, "pp": pp_jc},
        {"label": "Avg Discount %", "value": f"{avg_disc:.1f}%", "benchmark": f"{LABOUR_DISC_BENCH}%", "invert_trend": True},
        {"label": "YoY Growth %", "value": fmt_pct(calc_growth_pct(cp_rev, pp_rev, fill_value=0), True), "cp": cp_rev, "pp": pp_rev}
    ])

    from datetime import datetime
    from services.benchmark_provider import DefaultBenchmarkProvider
    from services.executive_alert_engine import ExecutiveAlertEngine
    
    # ── Executive Summary Strip ──────────────────────────────────
    rev_trend = "↑" if cp_rev >= pp_rev else "↓"
    mar_trend = "↑" if cp_mar >= pp_mar else "↓"
    jc_trend = "↑" if cp_jc >= pp_jc else "↓"
    disc_trend = "↓" if avg_disc <= LABOUR_DISC_BENCH else "↑"
    
    engine = ExecutiveAlertEngine(DefaultBenchmarkProvider())
    structured_alerts = engine.evaluate(cp, pp)
    critical_count = len(structured_alerts["critical"])
    
    exec_strip_html = f"""
    <div style="background:#fff; border-radius:8px; padding:0 20px; border:1px solid #e5e5ea; box-shadow:0 1px 2px rgba(0,0,0,0.02); display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; height:60px;">
        <div style="font-size:14px; font-weight:600; color:#1d1d1f; display:flex; gap:24px; width:100%; justify-content:space-evenly;">
            <span>Revenue {rev_trend}</span>
            <span>Margin {mar_trend}</span>
            <span>JC Vol {jc_trend}</span>
            <span>Discount {disc_trend}</span>
        </div>
    </div>
    """
    st.markdown(exec_strip_html.replace('\n', ''), unsafe_allow_html=True)

    # ── Session State for Alert Tab ──────────────────────────────
    if 'cockpit_alert_tab' not in st.session_state:
        st.session_state.cockpit_alert_tab = 'critical'
        
    def set_alert_tab(tab_name):
        st.session_state.cockpit_alert_tab = tab_name

    # ── Executive Alert Center ───────────────────────────────────
    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**🔴 Critical Alerts ({critical_count})**")
        if structured_alerts['critical']:
            for i, a in enumerate(structured_alerts['critical']):
                if i < 3:
                    st.markdown(f"• {a['rule']}")
            if critical_count > 3:
                st.markdown(f"<div style='font-size:12px; color:#6E6E73;'>+ {critical_count - 3} More...</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-size:13px; color:#1d1d1f;'>✓ No critical rules triggered.</div>", unsafe_allow_html=True)
            
        st.button("View All →", key="btn_crit", on_click=set_alert_tab, args=('critical',), use_container_width=True, type="primary" if st.session_state.cockpit_alert_tab == 'critical' else "secondary")

    with col2:
        warning_count = len(structured_alerts['warning'])
        st.markdown(f"**🟡 Warning Alerts ({warning_count})**")
        if warning_count > 0:
            for i, a in enumerate(structured_alerts['warning']):
                if i < 3:
                    st.markdown(f"• {a['rule']}")
            if warning_count > 3:
                st.markdown(f"<div style='font-size:12px; color:#6E6E73;'>+ {warning_count - 3} More...</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-size:13px; color:#1d1d1f;'>✓ No warning rules triggered.</div><div style='font-size:12px; color:#6E6E73; margin-top:4px;'>All configured warning rules evaluated successfully.</div>", unsafe_allow_html=True)
            
        st.button("View All →", key="btn_warn", on_click=set_alert_tab, args=('warning',), use_container_width=True, type="primary" if st.session_state.cockpit_alert_tab == 'warning' else "secondary")

    with col3:
        opp_count = len(structured_alerts['opportunities'])
        st.markdown(f"**🔵 Opportunities ({opp_count})**")
        if opp_count > 0:
            for i, a in enumerate(structured_alerts['opportunities']):
                if i < 3:
                    st.markdown(f"• {a['opportunity']}")
            if opp_count > 3:
                st.markdown(f"<div style='font-size:12px; color:#6E6E73;'>+ {opp_count - 3} More...</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-size:13px; color:#1d1d1f;'>No new opportunities identified.</div>", unsafe_allow_html=True)
            
        st.button("View Details →", key="btn_opp", on_click=set_alert_tab, args=('opportunities',), use_container_width=True, type="primary" if st.session_state.cockpit_alert_tab == 'opportunities' else "secondary")

    # ── KPI Explainability ───────────────────────────────────────
    st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)
    with st.expander("🔍 KPI Details & Explainability", expanded=False):
        kpi_choice = st.selectbox("Select KPI to explain:", ["Total Revenue", "Total Margin", "Total JCs", "Avg Discount %", "YoY Growth %"], label_visibility="collapsed")
        
        if kpi_choice == "Total Revenue":
            ex_def = "Total recognized revenue after discounts and before taxes."
            ex_form = "Sum(Net_Labour) + Sum(Net_Parts)"
            ex_curr = fmt_inr(cp_rev)
            ex_prev = fmt_inr(pp_rev)
            ex_var = fmt_inr(cp_rev - pp_rev)
            ex_bus = "Primary indicator of business volume and throughput."
            ex_src = "DMS Invoice Register (Labour & Parts)"
        elif kpi_choice == "Total Margin":
            ex_def = "Total gross margin generated from operations."
            ex_form = "Sum(Total Margin)"
            ex_curr = fmt_inr(cp_mar)
            ex_prev = fmt_inr(pp_mar)
            ex_var = fmt_inr(cp_mar - pp_mar)
            ex_bus = "Indicates profitability and pricing power."
            ex_src = "DMS Invoice Register"
        elif kpi_choice == "Total JCs":
            ex_def = "Total Job Cards opened/invoiced."
            ex_form = "Sum(JC_Nos.)"
            ex_curr = fmt_num(cp_jc)
            ex_prev = fmt_num(pp_jc)
            ex_var = fmt_num(cp_jc - pp_jc)
            ex_bus = "Measures workshop footfall and capacity utilization."
            ex_src = "DMS Job Card Register"
        elif kpi_choice == "Avg Discount %":
            ex_def = "Average discount given on Labour."
            ex_form = "Sum(Labour Discount) / Sum(Pre-GST Labour)"
            ex_curr = f"{avg_disc:.2f}%"
            ex_prev = f"{calculate_labour_discount_pct(pp):.2f}%"
            ex_var = f"{avg_disc - calculate_labour_discount_pct(pp):+.2f}%"
            ex_bus = "Indicates pricing discipline and revenue leakage."
            ex_src = "DMS Invoice Register"
        elif kpi_choice == "YoY Growth %":
            ex_def = "Year-over-Year Revenue Growth."
            ex_form = "(Current Revenue - Previous Revenue) / Previous Revenue"
            pct = calc_growth_pct(cp_rev, pp_rev, fill_value=0)
            ex_curr = f"{pct:.2f}%"
            ex_prev = "N/A"
            ex_var = "N/A"
            ex_bus = "Measures overall business expansion."
            ex_src = "DMS Invoice Register"
            
        ex_html = f"""
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; font-size:13px; color:#1d1d1f; margin-top:8px;">
            <div><span style="color:#6E6E73;">Definition:</span> {ex_def}</div>
            <div><span style="color:#6E6E73;">Formula:</span> <code style="font-size:11px; color:#CF222E; background:#FFEBE9; padding:2px 4px; border-radius:4px;">{ex_form}</code></div>
            <div><span style="color:#6E6E73;">Current:</span> <b>{ex_curr}</b></div>
            <div><span style="color:#6E6E73;">Previous:</span> {ex_prev}</div>
            <div><span style="color:#6E6E73;">Variance:</span> <span style="color:{'#34C759' if not '-' in str(ex_var) and not 'N/A' in str(ex_var) else '#FF3B30'};">{ex_var}</span></div>
            <div><span style="color:#6E6E73;">Business Meaning:</span> {ex_bus}</div>
            <div><span style="color:#6E6E73;">Data Source:</span> {ex_src}</div>
            <div><span style="color:#6E6E73;">Last Refresh:</span> {datetime.now().strftime('%H:%M')}</div>
        </div>
        """
        st.markdown(ex_html.replace('\n', ''), unsafe_allow_html=True)

    # ── Executive Alert Engine ───────────────────────────────────
    st.markdown("<div style='font-size:18px; font-weight:700; margin-top:24px; margin-bottom:12px;'>Executive Alert Details</div>", unsafe_allow_html=True)
    
    def render_alert_card(alert, color_border):
        html = f'''<div style="background:#fff;border:1px solid #e5e5ea;border-left:4px solid {color_border};border-radius:8px;padding:16px;margin-bottom:12px;box-shadow:0 1px 2px rgba(0,0,0,0.02);">
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                <div style="font-weight:600;font-size:15px;color:#1d1d1f;">{alert.get('rule', alert.get('opportunity'))}</div>
                <div style="font-weight:600;font-size:14px;color:{color_border};">Impact: {alert.get('impact', alert.get('gain'))}</div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:13px;color:#48484A;margin-bottom:12px;">
                <div><span style="color:#86868B;">Current Value:</span> <b>{alert.get('current', alert.get('situation'))}</b></div>
                <div><span style="color:#86868B;">Benchmark:</span> {alert.get('benchmark', alert.get('basis'))}</div>
                <div><span style="color:#86868B;">Variance:</span> <b style="color:{color_border};">{alert.get('variance', alert.get('benefit'))}</b></div>
                <div><span style="color:#86868B;">Owner:</span> 👤 {alert['owner']}</div>
            </div>
            <div style="font-size:13px;color:#1d1d1f;margin-bottom:4px;"><span style="color:#86868B;">Reason:</span> {alert.get('reason', alert.get('situation'))}</div>
            <div style="font-size:13px;color:#1d1d1f;margin-bottom:12px;"><span style="color:#86868B;">Action:</span> ✅ {alert['action']}</div>
        </div>'''
        st.markdown(html.replace('\n', ''), unsafe_allow_html=True)
        if 'why' in alert:
            with st.expander("Why?", expanded=False):
                w = alert['why']
                st.markdown(f"""<div style="font-size:12px; color:#48484A; display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                    <div><b>Rule:</b> {w['rule']}</div>
                    <div><b>Threshold:</b> {w['threshold']}</div>
                    <div><b>Current:</b> {w['current']}</div>
                    <div><b>Calculation:</b> <code>{w['calculation']}</code></div>
                    <div><b>Rows Involved:</b> {w['rows']}</div>
                    <div><b>Rationale:</b> {w['impact_rationale']}</div>
                </div>""", unsafe_allow_html=True)

    active_tab = st.session_state.cockpit_alert_tab
    if active_tab == 'critical':
        st.markdown("<div style='font-size:15px; font-weight:600; margin-bottom:8px; color:#CF222E;'>🔴 Critical Alerts Details</div>", unsafe_allow_html=True)
        if structured_alerts["critical"]:
            for a in structured_alerts["critical"]:
                render_alert_card(a, "#FF3B30")
        else:
            st.markdown("<div style='font-size:13px; color:#6E6E73; margin-bottom:16px;'>✓ No critical rules triggered.</div>", unsafe_allow_html=True)
            
    elif active_tab == 'warning':
        st.markdown("<div style='font-size:15px; font-weight:600; margin-bottom:8px; color:#E65100;'>🟡 Warning Alerts Details</div>", unsafe_allow_html=True)
        if structured_alerts["warning"]:
            for a in structured_alerts["warning"]:
                render_alert_card(a, "#FF9F0A")
        else:
            st.markdown("<div style='font-size:13px; color:#6E6E73; margin-bottom:16px;'>✓ No warning rules triggered.</div>", unsafe_allow_html=True)
            
    elif active_tab == 'opportunities':
        st.markdown("<div style='font-size:15px; font-weight:600; margin-bottom:8px; color:#185FA5;'>🔵 Opportunities Details</div>", unsafe_allow_html=True)
        if structured_alerts["opportunities"]:
            for a in structured_alerts["opportunities"]:
                render_alert_card(a, "#007AFF")
        else:
            st.markdown("<div style='font-size:13px; color:#6E6E73; margin-bottom:16px;'>No major opportunities identified for this period.</div>", unsafe_allow_html=True)
    # ── Revenue Trend ─────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        trend_data = monthly_summary(cp, as_index=False).agg(
            Labour=("Net_Labour", "sum"), Parts=("Net_Parts", "sum")
        ).sort_values("Month_Sort")
        trend_data["Revenue"] = trend_data["Labour"] + trend_data["Parts"]
        if not trend_data.empty:
            fig = px.line(trend_data, x="Month Name", y="Revenue", markers=True)
            ChartCard("📈 Revenue Trend", fig, height=280)

    # ── WS vs BS Split ───────────────────────────────────────────
    with c2:
        wbs_data = cp.groupby("MP_PB", as_index=False, dropna=False).agg(
            Labour=("Net_Labour", "sum"), Parts=("Net_Parts", "sum")
        ).rename(columns={"MP_PB": "Type"})
        wbs_data["Revenue"] = wbs_data["Labour"] + wbs_data["Parts"]
        if not wbs_data.empty:
            fig = px.pie(wbs_data, values="Revenue", names="Type", hole=0.6,
                         color="Type", color_discrete_map=MP_COLORS)
            fig.update_traces(texttemplate="%{label}<br><b>%{percent}</b>",
                              hovertemplate="<b>%{label}</b><br>Revenue: ₹%{value:,.0f}<br>Share: %{percent}<extra></extra>")
            fig.update_layout(legend=dict(orientation="v", x=1.05, y=0.5))
            ChartCard("⚖️ WS vs BS Split", fig, height=280)

    # ── Advisor Rankings ───────────────────────────────────────────
    st.markdown('<div style="margin-top:24px;"></div>', unsafe_allow_html=True)
    
    aa = advisor_summary(cp, adv_col=ADV_COL, as_index=False).agg(
        JCs=("JC_Nos.","sum"),
        NL=("Net_Labour","sum"),
        NP=("Net_Parts","sum"),
        OQ=("Oil_Sale_Qty","sum"),
        AS=("Accessory_Sale","sum"),
        DL=("Labour Discount","sum"),
        PL=("Pre-GST Labour","sum")
    )
    aa = aa[aa["JCs"] >= 20]
    if not aa.empty:
        aa["Avg_Lab_JC"] = np.where(aa["JCs"]>0, aa["NL"]/aa["JCs"], 0)
        aa["Avg_Parts_JC"] = np.where(aa["JCs"]>0, aa["NP"]/aa["JCs"], 0)
        aa["Avg_Oil_JC"] = np.where(aa["JCs"]>0, aa["OQ"]/aa["JCs"], 0)
        aa["Avg_Acc_JC"] = np.where(aa["JCs"]>0, aa["AS"]/aa["JCs"], 0)
        aa["Lab_Disc_Pct"] = np.where(aa["PL"]>0, aa["DL"]/aa["PL"]*100, 0)
        metrics = ["JCs", "Avg_Lab_JC", "Avg_Parts_JC", "Avg_Oil_JC", "Avg_Acc_JC"]
        for metric in metrics:
            aa[f"{metric}_score"] = np.ceil(aa[metric].rank(pct=True) * 5).clip(1, 5)
        aa["Lab_Disc_Pct_score"] = np.ceil((1 - aa["Lab_Disc_Pct"].rank(pct=True)) * 5).clip(1, 5)
        score_cols = [f"{m}_score" for m in metrics] + ["Lab_Disc_Pct_score"]
        aa["Composite_Score"] = aa[score_cols].mean(axis=1).round(1)
        aa_sorted = aa.sort_values("Composite_Score", ascending=False)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Top 5 Advisors**")
            top5 = aa_sorted.head(5)[[ADV_COL, "Composite_Score", "JCs", "Avg_Lab_JC"]]
            top5 = top5.rename(columns={ADV_COL: "Advisor"})
            top5["JCs"] = top5["JCs"].apply(fmt_num)
            top5["Avg_Lab_JC"] = top5["Avg_Lab_JC"].apply(fmt_inr)
            from ui.components.tables import TableCard
            TableCard(top5, height=250, index=False)
        with c2:
            st.markdown("**Bottom 5 Advisors**")
            bot5 = aa_sorted.tail(5)[[ADV_COL, "Composite_Score", "JCs", "Avg_Lab_JC"]].iloc[::-1]
            bot5 = bot5.rename(columns={ADV_COL: "Advisor"})
            bot5["JCs"] = bot5["JCs"].apply(fmt_num)
            bot5["Avg_Lab_JC"] = bot5["Avg_Lab_JC"].apply(fmt_inr)
            TableCard(bot5, height=250, index=False)
    else:
        st.info("Not enough advisor data (minimum 20 JCs required)")

    # ── Location Rankings ───────────────────────────────────────────
    st.markdown('<div style="margin-top:24px;"></div>', unsafe_allow_html=True)
    
    loc_cp = location_summary(cp, as_index=True).agg(
        JCs=("JC_Nos.","sum"),
        NL=("Net_Labour","sum"),
        M=("Total Margin","sum"),
        DL=("Labour Discount","sum"),
        PL=("Pre-GST Labour","sum"),
        Grp=("Location Group", "first")
    ).reset_index()
    loc_pp = location_summary(pp, as_index=True)["Net_Labour"].sum().reset_index()
    loc_pp.columns = ["Location Name", "PP_NL"]
    loc_data = loc_cp.merge(loc_pp, on="Location Name", how="left")
    loc_data["PP_NL"] = loc_data["PP_NL"].fillna(0)
    loc_data["Disc_Pct"] = np.where(loc_data["PL"]>0, loc_data["DL"]/loc_data["PL"]*100, 0)
    loc_data["YoY_Pct"] = np.where(loc_data["PP_NL"]>0, (loc_data["NL"]-loc_data["PP_NL"])/loc_data["PP_NL"]*100, 0)
    loc_data = loc_data.sort_values("NL", ascending=False)

    if not loc_data.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Top 5 Locations**")
            top5_loc = loc_data.head(5)[["Location Name", "Grp", "JCs", "NL", "M", "YoY_Pct"]]
            top5_loc = top5_loc.rename(columns={"NL": "Net Labour", "M": "Margin"})
            top5_loc["JCs"] = top5_loc["JCs"].apply(fmt_num)
            top5_loc["Net Labour"] = top5_loc["Net Labour"].apply(fmt_inr)
            top5_loc["Margin"] = top5_loc["Margin"].apply(fmt_inr)
            top5_loc["YoY_Pct"] = top5_loc["YoY_Pct"].apply(lambda x: f"{x:.1f}%")
            TableCard(top5_loc, height=250, index=False)
        with c2:
            st.markdown("**Bottom 5 Locations**")
            bot5_loc = loc_data.tail(5)[["Location Name", "Grp", "JCs", "NL", "M", "YoY_Pct"]].iloc[::-1]
            bot5_loc = bot5_loc.rename(columns={"NL": "Net Labour", "M": "Margin"})
            bot5_loc["JCs"] = bot5_loc["JCs"].apply(fmt_num)
            bot5_loc["Net Labour"] = bot5_loc["Net Labour"].apply(fmt_inr)
            bot5_loc["Margin"] = bot5_loc["Margin"].apply(fmt_inr)
            bot5_loc["YoY_Pct"] = bot5_loc["YoY_Pct"].apply(lambda x: f"{x:.1f}%")
            TableCard(bot5_loc, height=250, index=False)
    else:
        st.info("No location data available")

