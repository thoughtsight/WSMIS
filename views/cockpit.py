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
from ui.kpi_cards import kpi
from ui.tables import html_table
from ui.traffic import yoy_badge, traffic_light, tgt_badge
from ui.helpers import apply_chart, clean_hover, _render_finding, render_neg_labour_alert
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num
from config.settings import LABOUR_DISC_BENCH, HIGH_DISC_ALERT, YOY_DECLINE_ALERT, VOR_ALERT_THRESHOLD

def render(df, pairs, alerts, comparison_mode=True, selected_months=None):
    with st.spinner("Loading Cockpit..."):
        if df.empty: return

    cp_months = [p[0] for p in pairs]
    pp_months = [p[1] for p in pairs]
    cp = apply_month_filter(df, "Month Name", cp_months)
    pp = apply_month_filter(df, "Month Name", pp_months)
    
    render_neg_labour_alert(cp)

    def s(d, c): return d[c].sum() if not d.empty else 0

    # ── KPI Cards ────────────────────────────────────────────────
    st.markdown('<div class="section-card"><div class="section-title">📊 Executive Summary</div>', unsafe_allow_html=True)
    c = st.columns(5)
    cp_rev = calculate_net_revenue(cp)
    pp_rev = calculate_net_revenue(pp)
    cp_mar = calculate_total_margin(cp)
    pp_mar = calculate_total_margin(pp)
    cp_jc = s(cp, "JC_Nos.")
    pp_jc = s(pp, "JC_Nos.")
    cp_disc = calculate_labour_discount(cp)
    cp_pre_lab = s(cp, "Pre-GST Labour")
    avg_disc = calculate_labour_discount_pct(cp)

    with c[0]: kpi("Total Revenue", fmt_inr(cp_rev), f"PP: {fmt_inr(pp_rev)}", cp_rev, pp_rev)
    with c[1]: kpi("Total Margin", fmt_inr(cp_mar), f"PP: {fmt_inr(pp_mar)}", cp_mar, pp_mar)
    with c[2]: kpi("Total JCs", fmt_num(cp_jc), f"PP: {fmt_num(pp_jc)}", cp_jc, pp_jc)
    with c[3]: kpi("Avg Discount %", f"{avg_disc:.1f}%", benchmark=f"{LABOUR_DISC_BENCH}%")
    with c[4]: kpi("YoY Growth %", fmt_pct(calc_growth_pct(cp_rev, pp_rev, fill_value=0), True), cp=cp_rev, pp=pp_rev)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Business Health Score ────────────────────────────────────
    rev_growth_pct = calc_growth_pct(cp_rev, pp_rev, fill_value=0) if pp_rev > 0 else 0
    jc_growth_pct  = calc_growth_pct(cp_jc, pp_jc, fill_value=0) if pp_jc > 0 else 0
    red_count_bhs  = sum(1 for sv, _ in alerts if sv == "red") if alerts else 0

    rev_score  = 35 if rev_growth_pct > 5 else (25 if rev_growth_pct >= 0 else (15 if rev_growth_pct >= -5 else 0))
    disc_score = 35 if avg_disc <= LABOUR_DISC_BENCH else (22 if avg_disc <= 20 else (10 if avg_disc <= HIGH_DISC_ALERT else 0))
    jc_score   = 20 if jc_growth_pct >= 0 else (12 if jc_growth_pct >= -5 else 0)
    alert_score = max(0, 10 - red_count_bhs * 5)
    bhs = rev_score + disc_score + jc_score + alert_score

    if bhs >= 75:   bhs_label, bhs_color, bhs_icon = "Excellent", "#34C759", "🟢"
    elif bhs >= 55: bhs_label, bhs_color, bhs_icon = "Good",      "#30B0C7", "🟦"
    elif bhs >= 35: bhs_label, bhs_color, bhs_icon = "Fair",      "#FF9F0A", "🟡"
    else:           bhs_label, bhs_color, bhs_icon = "Poor",      "#FF3B30", "🔴"

    st.markdown('<div class="section-card"><div class="section-title">🏆 Business Health Score</div>', unsafe_allow_html=True)
    bhs_c = st.columns([1, 2])
    with bhs_c[0]:
        st.markdown(f"""
        <div style="text-align:center;padding:16px;">
            <div style="font-size:52px;font-weight:700;color:{bhs_color};">{bhs}</div>
            <div style="font-size:16px;font-weight:600;color:{bhs_color};">{bhs_icon} {bhs_label}</div>
            <div style="font-size:12px;color:#6E6E73;margin-top:4px;">out of 100</div>
        </div>""", unsafe_allow_html=True)
    with bhs_c[1]:
        breakdown = [
            ("Revenue Growth",   rev_score,   35, "📈"),
            ("Discount Control", disc_score,  35, "🏷️"),
            ("Volume (JC)",      jc_score,    20, "🔧"),
            ("Alert Penalty",    alert_score, 10, "⚠️"),
        ]
        for name, score, max_score, icon in breakdown:
            fill_pct = int(score / max_score * 100) if max_score > 0 else 0
            bar_color = bhs_color if score >= max_score * 0.7 else ("#FF9F0A" if score >= max_score * 0.4 else "#FF3B30")
            st.markdown(f"""
            <div style="margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;font-size:13px;">
                    <span>{icon} {name}</span><span style="color:{bar_color};font-weight:600;">{score}/{max_score}</span>
                </div>
                <div style="background:#F2F2F7;border-radius:4px;height:8px;margin-top:4px;">
                    <div style="background:{bar_color};width:{fill_pct}%;height:8px;border-radius:4px;"></div>
                </div>
            </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Alert Summary ────────────────────────────────────────────
    st.markdown('<div class="section-card"><div class="section-title">🚨 Alert Summary</div>', unsafe_allow_html=True)
    if alerts:
        red_count = sum(1 for s, _ in alerts if s == "red")
        yellow_count = sum(1 for s, _ in alerts if s == "yellow")
        blue_count = sum(1 for s, _ in alerts if s == "blue")
        c = st.columns(3)
        with c[0]: st.metric("Critical Alerts", red_count, delta_color="inverse")
        with c[1]: st.metric("Warning Alerts", yellow_count)
        with c[2]: st.metric("Opportunity Alerts", blue_count)
    else:
        st.info("No alerts for this period")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Top 3 Problems ───────────────────────────────────────────
    st.markdown('<div class="section-card"><div class="section-title">🔥 Top 3 Problems</div>', unsafe_allow_html=True)
    problems = []

    # Problem 1: High discount locations
    loc_disc = location_summary(cp, as_index=True).agg(L=("Pre-GST Labour","sum"), D=("Labour Discount","sum"))
    loc_disc['D%'] = calc_ratio(loc_disc['D'], loc_disc['L'], multiplier=100, fill_value=np.nan)
    high_disc = loc_disc[loc_disc['D%'] > HIGH_DISC_ALERT].nlargest(1, 'D%')
    if not high_disc.empty:
        loc = high_disc.index[0]
        disc_pct = high_disc.iloc[0]['D%']
        leak_amt = (disc_pct - LABOUR_DISC_BENCH) / 100 * high_disc.iloc[0]['L'] if disc_pct > LABOUR_DISC_BENCH else 0
        problems.append(("High Labour Discount", loc, f"₹{leak_amt:,.0f} leakage vs {LABOUR_DISC_BENCH}% benchmark", "Review advisor discounts"))

    # Problem 2: YoY decline locations
    loc_cp = location_summary(cp, as_index=True)['Net_Labour'].sum()
    loc_pp = location_summary(pp, as_index=True)['Net_Labour'].sum()
    yoy_declines = []
    for loc in loc_cp.index:
        if loc in loc_pp.index and loc_pp[loc] > 50000:
            yoy = calc_growth_pct(loc_cp[loc], loc_pp[loc], fill_value=np.nan) if loc_pp[loc] and not np.isnan(loc_pp[loc]) else np.nan
            if not np.isnan(yoy) and yoy < -YOY_DECLINE_ALERT:
                yoy_declines.append((loc, yoy, loc_cp[loc]))
    if yoy_declines:
        worst_yoy = min(yoy_declines, key=lambda x: x[1])
        revenue_lost = loc_pp[worst_yoy[0]] - loc_cp[worst_yoy[0]]
        problems.append(("YoY Revenue Decline", worst_yoy[0], f"{abs(worst_yoy[1]):.1f}% decline | ₹{revenue_lost:,.0f} lost vs PP", "Investigate location performance"))

    # Problem 3: VOR charges
    vor = get_vor_charges(cp)
    if vor < -VOR_ALERT_THRESHOLD:
        problems.append(("Elevated VOR Charges", "Group", f"₹{abs(vor):,.0f} excess stock", "Review parts inventory"))

    if problems:
        for i, (title, loc, impact, action) in enumerate(problems[:3]):
            st.markdown(f"""
            <div style="background:#FFEBE9;border-left:4px solid #CF222E;border-radius:8px;padding:12px;margin-bottom:8px;">
                <div style="font-weight:600;color:#CF222E;font-size:14px;">{title}</div>
                <div style="color:#6E6E73;font-size:13px;margin-top:4px;">📍 {loc} | 💰 {impact}</div>
                <div style="color:#185FA5;font-size:12px;margin-top:4px;">✅ {action}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No critical problems detected")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Top 3 Opportunities ───────────────────────────────────────
    st.markdown('<div class="section-card"><div class="section-title">💎 Top 3 Opportunities</div>', unsafe_allow_html=True)
    opportunities = []

    # A. Discount Recovery Opportunity
    disc_rec = loc_disc[loc_disc['D%'] > LABOUR_DISC_BENCH].copy()
    if not disc_rec.empty:
        total_recovery = ((disc_rec['D%'] - LABOUR_DISC_BENCH) / 100 * disc_rec['L']).sum()
        if total_recovery > 0:
            opportunities.append(("Discount Recovery", f"₹{total_recovery:,.0f}", "Group Service Head"))

    # B. Labour/JC Opportunity (below median)
    loc_lab_jc = location_summary(cp, as_index=True).agg(JCs=("JC_Nos.","sum"), NL=("Net_Labour","sum"))
    loc_lab_jc['Avg_Lab_JC'] = loc_lab_jc['NL'] / loc_lab_jc['JCs'].replace(0,np.nan)
    median_lab_jc = loc_lab_jc['Avg_Lab_JC'].median()
    low_lab_jc = loc_lab_jc[loc_lab_jc['Avg_Lab_JC'] < median_lab_jc]
    if not low_lab_jc.empty:
        potential = (median_lab_jc - low_lab_jc['Avg_Lab_JC']) * low_lab_jc['JCs']
        if potential.sum() > 0:
            opportunities.append(("Labour/JC Uplift", f"₹{potential.sum():,.0f}", "Location Managers"))

    # C. Oil Attach Opportunity
    loc_oil = location_summary(cp, as_index=True).agg(JCs=("JC_Nos.","sum"), OQ=("Oil_Sale_Qty","sum"))
    loc_oil['Oil_Attach'] = loc_oil['OQ'] / loc_oil['JCs'].replace(0,np.nan)
    median_oil = loc_oil['Oil_Attach'].median()
    low_oil = loc_oil[loc_oil['Oil_Attach'] < median_oil]
    if not low_oil.empty:
        potential_qty = (median_oil - low_oil['Oil_Attach']) * low_oil['JCs']
        if potential_qty.sum() > 0:
            avg_oil_price = get_oil_sales(cp) / cp['Oil_Sale_Qty'].replace(0, np.nan).sum() if cp['Oil_Sale_Qty'].sum() > 0 else 0
            oil_opp_value = potential_qty.sum() * avg_oil_price
            opportunities.append(("Oil Attach Uplift", f"₹{oil_opp_value:,.0f}", "Service Advisors"))

    if opportunities:
        for i, (name, impact, owner) in enumerate(opportunities[:3]):
            st.markdown(f"""
            <div style="background:#E8F0FE;border-left:4px solid #185FA5;border-radius:8px;padding:12px;margin-bottom:8px;">
                <div style="font-weight:600;color:#185FA5;font-size:14px;">{name}</div>
                <div style="color:#6E6E73;font-size:13px;margin-top:4px;">💰 {impact}</div>
                <div style="color:#34C759;font-size:12px;margin-top:4px;">👤 Owner: {owner}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No significant opportunities identified")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Revenue Trend ─────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-card"><div class="section-title">📈 Revenue Trend</div>', unsafe_allow_html=True)
        trend_data = monthly_summary(cp, as_index=False).agg(
            Labour=("Net_Labour", "sum"), Parts=("Net_Parts", "sum")
        ).sort_values("Month_Sort")
        trend_data["Revenue"] = trend_data["Labour"] + trend_data["Parts"]
        if not trend_data.empty:
            fig = px.line(trend_data, x="Month Name", y="Revenue", markers=True)
            apply_chart(fig, "Monthly Revenue", 280)
            st.plotly_chart(fig, width='stretch', key="cockpit_trend",
                            config={"displayModeBar": True, "displaylogo": False,
                                    "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                    "toImageButtonOptions": {"format":"png","scale":2}})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── WS vs BS Split ───────────────────────────────────────────
    with c2:
        st.markdown('<div class="section-card"><div class="section-title">⚖️ WS vs BS Split</div>', unsafe_allow_html=True)
        wbs_data = cp.groupby("MP_PB", as_index=False, dropna=False).agg(
            Labour=("Net_Labour", "sum"), Parts=("Net_Parts", "sum")
        ).rename(columns={"MP_PB": "Type"})
        wbs_data["Revenue"] = wbs_data["Labour"] + wbs_data["Parts"]
        if not wbs_data.empty:
            fig = px.pie(wbs_data, values="Revenue", names="Type", hole=0.6,
                         color="Type", color_discrete_map=MP_COLORS)
            fig.update_traces(texttemplate="%{label}<br><b>%{percent}</b>",
                              hovertemplate="<b>%{label}</b><br>Revenue: ₹%{value:,.0f}<br>Share: %{percent}<extra></extra>")
            apply_chart(fig, "Revenue Split", 280)
            fig.update_layout(margin=dict(t=52,b=20,l=0,r=0), legend=dict(orientation="v",x=1.05,y=0.5))
            st.plotly_chart(fig, width='stretch', key="cockpit_wsbs",
                            config={"displayModeBar": True, "displaylogo": False,
                                    "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                    "toImageButtonOptions": {"format":"png","scale":2}})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Advisor Rankings ───────────────────────────────────────────
    st.markdown('<div class="section-card"><div class="section-title">🎯 Advisor Rankings</div>', unsafe_allow_html=True)
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
            html_table(top5, height="250px")
        with c2:
            st.markdown("**Bottom 5 Advisors**")
            bot5 = aa_sorted.tail(5)[[ADV_COL, "Composite_Score", "JCs", "Avg_Lab_JC"]].iloc[::-1]
            bot5 = bot5.rename(columns={ADV_COL: "Advisor"})
            bot5["JCs"] = bot5["JCs"].apply(fmt_num)
            bot5["Avg_Lab_JC"] = bot5["Avg_Lab_JC"].apply(fmt_inr)
            html_table(bot5, height="250px")
    else:
        st.info("Not enough advisor data (minimum 20 JCs required)")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Location Rankings ───────────────────────────────────────────
    st.markdown('<div class="section-card"><div class="section-title">🏢 Location Rankings</div>', unsafe_allow_html=True)
    loc_cp = location_summary(cp, as_index=True).agg(
        JCs=("JC_Nos.","sum"),
        NL=("Net_Labour","sum"),
        M=("Total Margin","sum"),
        DL=("Labour Discount","sum"),
        PL=("Pre-GST Labour","sum"),
        Grp=("Model Group", "first")
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
            html_table(top5_loc, height="250px")
        with c2:
            st.markdown("**Bottom 5 Locations**")
            bot5_loc = loc_data.tail(5)[["Location Name", "Grp", "JCs", "NL", "M", "YoY_Pct"]].iloc[::-1]
            bot5_loc = bot5_loc.rename(columns={"NL": "Net Labour", "M": "Margin"})
            bot5_loc["JCs"] = bot5_loc["JCs"].apply(fmt_num)
            bot5_loc["Net Labour"] = bot5_loc["Net Labour"].apply(fmt_inr)
            bot5_loc["Margin"] = bot5_loc["Margin"].apply(fmt_inr)
            bot5_loc["YoY_Pct"] = bot5_loc["YoY_Pct"].apply(lambda x: f"{x:.1f}%")
            html_table(bot5_loc, height="250px")
    else:
        st.info("No location data available")
    st.markdown('</div>', unsafe_allow_html=True)

