import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from views.shared import *
from views.components.kpi_engine import KPIEngine
from views.components.chart_engine import ChartEngine
from services.state_manager import StateManager
from ui.traffic import yoy_badge, traffic_light, tgt_badge
from ui.design_tokens import T
from config.settings import LABOUR_DISC_BENCH, HIGH_DISC_ALERT, YOY_DECLINE_ALERT, VOR_ALERT_THRESHOLD
from utils.constants import LOC_COLORS, MP_COLORS, CLIENTS
from utils.loaders import load_targets

from services.benchmark_provider import DefaultBenchmarkProvider
from services.executive_alert_engine import ExecutiveAlertEngine
from services.ai.provider import get_ai_client, get_default_model
from views.dashboard_common import inject_responsive_css, navigate_to_page

def generate_executive_narrative(cp, pp, cp_months, pp_months):
    """Generate rule-based executive narrative sections."""
    sections = {}
    cp_lab = get_net_labour(cp); pp_lab = get_net_labour(pp)
    yoy_lab = calc_growth_pct(cp_lab, pp_lab, fill_value=0)
    direction = "grew" if yoy_lab >= 0 else "declined"
    cp_period_str = f"{cp_months[0]} to {cp_months[-1]}" if cp_months else "selected period"
    pp_period_str = f"{pp_months[0]} to {pp_months[-1]}" if pp_months else "prior period"
    sections["period"] = (
        f"For the period {cp_period_str}, the group reported net labour revenue of "
        f"{fmt_inr(cp_lab)}, which {direction} {abs(yoy_lab):.1f}% compared to the prior period "
        f"({fmt_inr(pp_lab)}). Total job cards processed: {int(get_jobcard_count(cp)):,} "
        f"across {cp['Location Name'].nunique()} active locations."
    )
    
    loc_cp = location_summary(cp, as_index=True)["Net_Labour"].sum()
    loc_pp = location_summary(pp, as_index=True)["Net_Labour"].sum()
    loc_yoy = calc_growth_pct(loc_cp, loc_pp, fill_value=np.nan).dropna()
    top3 = loc_yoy.nlargest(3) if not loc_yoy.empty else pd.Series()
    bot3 = loc_yoy.nsmallest(3) if not loc_yoy.empty else pd.Series()
    top_str = "; ".join([f"{l} (+{v:.1f}%)" for l, v in top3.items()]) if not top3.empty else "N/A"
    bot_str = "; ".join([f"{l} ({v:+.1f}%)" for l, v in bot3.items()]) if not bot3.empty else "N/A"
    sections["locations"] = (
        f"Top performing locations by YoY labour growth: {top_str}. "
        f"Locations requiring management attention: {bot_str}."
    )
    
    adv_lab = advisor_summary(cp, adv_col=ADV_COL, as_index=True)["Net_Labour"].sum()
    adv_disc = advisor_summary(cp, adv_col=ADV_COL, as_index=True).apply(
        lambda x: calc_ratio(get_labour_discount(x), get_labour_sales(x), multiplier=100, fill_value=0)
        if get_labour_sales(x) > 0 else 0
    )
    star = adv_lab.idxmax() if not getattr(locals().get('cp', None), 'empty', True) else "N/A" if not adv_lab.empty else "N/A"
    risk = adv_disc[adv_disc > 25].index.tolist() if not adv_disc.empty else []
    sections["advisors"] = (
        f"Star advisor this period: {star} with {fmt_inr(adv_lab.get(star, 0))} net labour. "
        f"{'High discount risk advisors (>25%): ' + ', '.join(risk[:5]) + '.' if risk else 'No advisors exceeded the 25% discount threshold.'}"
    )
    
    total_gross = get_labour_sales(cp)
    total_disc = get_labour_discount(cp)
    disc_pct = calc_ratio(total_disc, total_gross, multiplier=100, fill_value=0)
    pp_disc_pct = calc_ratio(get_labour_discount(pp), get_labour_sales(pp), multiplier=100, fill_value=0)
    disc_dir = "improved" if disc_pct < pp_disc_pct else "worsened"
    leakage = max(0, (disc_pct - LABOUR_DISC_BENCH) / 100 * total_gross)
    sections["discount"] = (
        f"Group labour discount stands at {disc_pct:.1f}% (vs {pp_disc_pct:.1f}% prior period — {disc_dir}). "
        f"Estimated revenue leakage vs {LABOUR_DISC_BENCH}% benchmark: {fmt_inr(leakage)}. "
        f"{'Immediate discount audit recommended.' if disc_pct > HIGH_DISC_ALERT else 'Discount levels are within acceptable range.'}"
    )
    
    oil_jcs = cp[cp["Oil_Sale_Qty"] > 0]["JC_Nos."].count()
    total_jcs = len(cp[cp["JC_Nos."] > 0])
    oil_pen = calc_ratio(oil_jcs, total_jcs, multiplier=100, fill_value=0)
    sections["sales_mix"] = (
        f"Oil penetration: {oil_pen:.1f}% of job cards. "
        f"Total oil revenue: {fmt_inr(get_oil_sales(cp))}. "
        f"Battery: {fmt_inr(get_battery_sales(cp))}, Tyre: {fmt_inr(get_tyre_sales(cp))}, "
        f"Accessories: {fmt_inr(get_accessory_sales(cp))}."
    )
    
    recent = cp.groupby("Month_Sort", dropna=False)["Net_Labour"].sum().reset_index().sort_values("Month_Sort").tail(6)
    if len(recent) >= 3:
        slope = np.polyfit(recent["Month_Sort"], recent["Net_Labour"], 1)[0]
        signal = "Strong Momentum 🟢" if slope > 50000 else ("At Risk 🔴" if slope < -50000 else "Stable 🟡")
    else:
        signal = "Insufficient Data"
    sections["forecast"] = f"Trend signal based on last 6 months: {signal}."
    
    actions = []
    if disc_pct > 20:
        actions.append("1. Conduct immediate discount audit for advisors exceeding 20% — Group Level")
    if not loc_yoy.empty and loc_yoy.min() < -15:
        worst = loc_yoy.idxmin()
        actions.append(f"2. Initiate turnaround review for {worst} — Location Manager")
    if oil_pen < 60:
        actions.append("3. Launch oil penetration drive — target 70% by next quarter — Advisor Level")
    if not actions:
        actions.append("1. Maintain current performance standards and focus on margin improvement.")
    sections["actions"] = "\n".join(actions)
    return sections

def render(df, pairs, alerts=None, comparison_mode=True, selected_months=None):
    inject_responsive_css()
    with st.spinner("Loading Executive Command Center..."):
        if df.empty:
            EmptyState('No data available for the selected period.')
            return

    cp_months = selected_months if selected_months else []
    pp_months = [p[1] for p in pairs]
    cp = apply_month_filter(df, "Month Name", cp_months)
    pp = apply_month_filter(df, "Month Name", pp_months)

    def s(d, c): return d[c].sum() if not d.empty else 0

    client_name = st.session_state.get("client_sel")
    if client_name and client_name in CLIENTS:
        sheet_id = CLIENTS[client_name].get("sheet_id")
        targets_df = load_targets(sheet_id) if sheet_id else pd.DataFrame()
    else:
        targets_df = pd.DataFrame()
    
    tgt_cp = targets_df[targets_df["Month Name"].isin(cp["Month Name"].unique())] if not targets_df.empty else pd.DataFrame()
    
    # ── ZONE A: Identity & Health Strip ─────────────────────────────
    # Identity Strip is generally handled by app.py layout (UniversalHeader)

    cp_rev = calculate_net_revenue(cp)
    pp_rev = calculate_net_revenue(pp)
    cp_mar = calculate_total_margin(cp)
    pp_mar = calculate_total_margin(pp)
    cp_jc = s(cp, "JC_Nos.")
    pp_jc = s(pp, "JC_Nos.")
    
    cp_avg_lab_jc = s(cp, "Net_Labour") / cp_jc if cp_jc > 0 else 0
    pp_avg_lab_jc = s(pp, "Net_Labour") / pp_jc if pp_jc > 0 else 0
    
    avg_disc = calculate_labour_discount_pct(cp)
    pp_avg_disc = calculate_labour_discount_pct(pp)
    
    tgt_rev = tgt_cp["WS_Labour_Target"].sum() + tgt_cp["BS_Labour_Target"].sum() + tgt_cp["WS_Parts_Target"].sum() + tgt_cp["BS_Parts_Target"].sum() if not tgt_cp.empty else 0
    rev_tgt_pct = (cp_rev / tgt_rev * 100) if tgt_rev > 0 else np.nan

    KPIGrid([
        {"label": "Total Revenue", "value": fmt_inr(cp_rev), "cp": cp_rev, "pp": pp_rev, "pp_label": f"PP {fmt_inr(pp_rev)}"},
        {"label": "Margin %", "value": f"{(cp_mar/cp_rev*100 if cp_rev>0 else 0):.1f}%", "cp": (cp_mar/cp_rev*100 if cp_rev>0 else 0), "pp": (pp_mar/pp_rev*100 if pp_rev>0 else 0), "pp_label": f"PP {(pp_mar/pp_rev*100 if pp_rev>0 else 0):.1f}%"},
        {"label": "Total JCs", "value": fmt_num(cp_jc), "cp": cp_jc, "pp": pp_jc, "pp_label": f"PP {fmt_num(pp_jc)}"},
        {"label": "Avg Labour / JC", "value": fmt_inr(cp_avg_lab_jc), "cp": cp_avg_lab_jc, "pp": pp_avg_lab_jc, "pp_label": f"PP {fmt_inr(pp_avg_lab_jc)}"},
        {"label": "Avg Discount %", "value": f"{avg_disc:.1f}%", "target": f"{LABOUR_DISC_BENCH}%", "benchmark": f"Critical {HIGH_DISC_ALERT}%", "invert_trend": True, "pp_label": f"PP {pp_avg_disc:.1f}%"},
        {"label": "Revenue vs Target", "value": f"{rev_tgt_pct:.1f}%" if not np.isnan(rev_tgt_pct) else "N/A", "cp": rev_tgt_pct if not np.isnan(rev_tgt_pct) else None, "pp": 100 if not np.isnan(rev_tgt_pct) else None, "pp_label": "Target 100%"}
    ], cols=6)

    st.markdown('<hr class="zone-separator" />', unsafe_allow_html=True)

    # ── ZONE B: Alert & Opportunity Rail ──────────────────────────────
    engine = ExecutiveAlertEngine(DefaultBenchmarkProvider())
    structured_alerts = engine.evaluate(cp, pp)
    
    section_title("Alert & Opportunity Rail")
    
    col1, col2, col3 = st.columns(3)
    
    def render_rail_cards(alert_list, modifier_class):
        if not alert_list:
            st.markdown('<div class="insight-stat">✓ No alerts in this category.</div>', unsafe_allow_html=True)
            return
        for i, a in enumerate(alert_list[:3]):
            rule = a.get('rule') or a.get('opportunity') or 'N/A'
            impact = a.get('impact') or a.get('gain') or 'N/A'
            owner = a.get('owner') or 'N/A'
            card_html = f"""
            <div class="insight-card {modifier_class}">
                <div class="insight-title">{rule}</div>
                <div class="insight-stat">Impact: {impact}</div>
                <div class="insight-stat">Owner: 👤 {owner}</div>
            </div>
            """
            st.markdown(card_html.replace('\n', ''), unsafe_allow_html=True)
        if len(alert_list) > 3:
            st.markdown(f'<div class="insight-stat">+ {len(alert_list) - 3} More...</div>', unsafe_allow_html=True)

    with col1:
        st.markdown(f"**🔴 Critical ({len(structured_alerts['critical'])})**")
        render_rail_cards(structured_alerts['critical'], "neg")
    with col2:
        st.markdown(f"**🟡 Warning ({len(structured_alerts['warning'])})**")
        render_rail_cards(structured_alerts['warning'], "warn")
    with col3:
        st.markdown(f"**🔵 Opportunity ({len(structured_alerts['opportunities'])})**")
        render_rail_cards(structured_alerts['opportunities'], "pos")
        
    with st.expander("View Alert Details", expanded=False):
        def render_alert_detail(alert, modifier_class):
            rule = alert.get('rule') or alert.get('opportunity') or 'N/A'
            impact = alert.get('impact') or alert.get('gain') or 'N/A'
            current = alert.get('current') or alert.get('situation') or 'N/A'
            benchmark = alert.get('benchmark') or alert.get('basis') or 'N/A'
            variance = alert.get('variance') or alert.get('benefit') or 'N/A'
            owner = alert.get('owner') or 'N/A'
            reason = alert.get('reason') or alert.get('situation') or 'N/A'
            action = alert.get('action') or 'N/A'
            
            html = f'''<div class="insight-card {modifier_class}">
                <div style="display:flex;justify-content:space-between;margin-bottom:{T.SPACE_2}px;">
                    <div class="insight-title" style="font-size:{T.TYPE_LG}px;">{rule}</div>
                    <div class="insight-title" style="font-size:{T.TYPE_BASE}px;">Impact: {impact}</div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:{T.SPACE_2}px;font-size:{T.TYPE_SM}px;color:var(--color-text-secondary);margin-bottom:{T.SPACE_3}px;">
                    <div><span style="color:var(--color-text-tertiary);">Current Value:</span> <b>{current}</b></div>
                    <div><span style="color:var(--color-text-tertiary);">Benchmark:</span> {benchmark}</div>
                    <div><span style="color:var(--color-text-tertiary);">Variance:</span> <b>{variance}</b></div>
                    <div><span style="color:var(--color-text-tertiary);">Owner:</span> 👤 {owner}</div>
                </div>
                <div class="insight-stat"><span style="color:var(--color-text-tertiary);">Reason:</span> {reason}</div>
            </div>'''
            st.markdown(html.replace('\n', ''), unsafe_allow_html=True)
            
        st.markdown('<div class="insight-title" style="color:var(--color-danger);">Critical Alerts</div>', unsafe_allow_html=True)
        if not structured_alerts["critical"]: st.markdown("No critical alerts.")
        for a in structured_alerts["critical"]: render_alert_detail(a, "neg")
        
        st.markdown('<div class="insight-title" style="color:var(--color-warning); margin-top:16px;">Warning Alerts</div>', unsafe_allow_html=True)
        if not structured_alerts["warning"]: st.markdown("No warning alerts.")
        for a in structured_alerts["warning"]: render_alert_detail(a, "warn")
        
        st.markdown('<div class="insight-title" style="color:var(--color-primary); margin-top:16px;">Opportunities</div>', unsafe_allow_html=True)
        if not structured_alerts["opportunities"]: st.markdown("No opportunities.")
        for a in structured_alerts["opportunities"]: render_alert_detail(a, "pos")

    st.markdown('<hr class="zone-separator" />', unsafe_allow_html=True)

    # ── Executive Brief (AI with Fallback) ──────────────────────────
    section_title("Executive Brief")
    st.markdown('<p class="ai-band-label">Executive Brief</p>', unsafe_allow_html=True)
    
    cp_months_list = sorted(cp["Month Name"].unique(), key=lambda x: MONTH_SORT_ORDER.get(x, 99))
    pp_months_list = sorted(pp["Month Name"].unique(), key=lambda x: MONTH_SORT_ORDER.get(x, 99)) if not pp.empty else []
    sections = generate_executive_narrative(cp, pp, cp_months_list, pp_months_list)
    
    ai_success = False
    try:
        client_ai = get_ai_client()
        model_name = get_default_model()
        base_text = "\n\n".join(sections.values())
        message = client_ai.messages.create(
            model=model_name,
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": (
                    "You are a senior automotive dealership analyst. Rewrite this management brief "
                    "in polished professional English for a dealership group MD. Format it clearly using bullet points and short paragraphs. "
                    "Keep all numbers exactly as given. Output only the rewritten text, no preamble:\n\n" + base_text
                )
            }]
        )
        enhanced_text = message.content[0].text
        st.markdown(enhanced_text)
        ai_success = True
    except Exception as e:
        ai_success = False
    
    if not ai_success:
        for title, text in [("Period Overview", sections["period"]), ("Location Intelligence", sections["locations"]),
                             ("Advisor Spotlight", sections["advisors"]), ("Discount Health", sections["discount"]),
                             ("Sales Mix", sections["sales_mix"]), ("Forecast Signal", sections["forecast"]),
                             ("Recommended Actions", sections["actions"])]:
            note = f'<div style="margin-bottom:var(--space-2);"><b style="color:var(--color-text-primary);font-size:var(--type-base);">{title}</b></div><div style="color:var(--color-text-primary);font-size:var(--type-base);line-height:1.6;">{text}</div>'
            st.markdown(f'<div class="ai-band">{note}</div>', unsafe_allow_html=True)

    st.markdown('<hr class="zone-separator" />', unsafe_allow_html=True)

    # ── ZONE C: Workshop Intelligence ────────────────────────────────
    section_title("Workshop Intelligence")
    
    # Row 1: Trend and Location
    c1, c2 = st.columns(2)
    with c1:
        # Single-month safe trend: use original `df` to get trailing 6 months relative to the max month in `cp`
        max_sort = cp["Month_Sort"].max() if not cp.empty else 0
        trend_df = df[(df["Month_Sort"] <= max_sort) & (df["Month_Sort"] > max_sort - 6)]
        trend_data = trend_df.groupby(["Month_Sort", "Month Name"], as_index=False, dropna=False)["Net_Labour"].sum().sort_values("Month_Sort")
        if not trend_data.empty:
            fig = px.line(trend_data, x="Month Name", y="Net_Labour", markers=True, title="Monthly Net Labour Trend")
            fig.update_traces(line=dict(color="#0071E3"))
            ChartEngine.render_card("📈 Net Labour Trend (6M)", fig, height=320)
            
    with c2:
        loc_ranking = location_summary(cp, as_index=False).agg(Revenue=("Net_Labour", "sum")).sort_values("Revenue", ascending=True).tail(10)
        if not loc_ranking.empty:
            fig = px.bar(loc_ranking, x="Revenue", y="Location Name", orientation="h", color="Revenue", color_continuous_scale="Blues")
            fig.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
            ChartEngine.render_card("🏆 Revenue by Location (Top 10)", fig, height=320)
            
    # Row 2: WS vs BS and Service Mix
    c1, c2 = st.columns(2)
    with c1:
        wd = cp.groupby("Service_Type_Group", as_index=False, dropna=False)["Net_Labour"].sum().rename(columns={"Service_Type_Group":"Type","Net_Labour":"Net Labour (₹)"})
        fig = px.pie(wd, values="Net Labour (₹)", names="Type", hole=0.6, color="Type", color_discrete_map=MP_COLORS)
        fig.update_traces(texttemplate="%{label}<br><b>%{percent}</b>")
        fig.update_layout(legend=dict(orientation="v", x=1.05, y=0.5))
        total_val = wd["Net Labour (₹)"].sum()
        fig.add_annotation(
            x=0.5, y=0.5,
            text=f"₹{fmt_inr_short(total_val)}",
            showarrow=False,
            font=dict(size=15, family="Inter, -apple-system, sans-serif", color="#1D1D1F"),
            xref="paper", yref="paper"
        )
        ChartEngine.render_card("⚖️ WS vs BS Split", fig, height=300)
    with c2:
        sd = cp[cp["Service Type"] != "Wash"].groupby("Service Type", as_index=False, dropna=False)["JC_Nos."].sum()
        fig = px.pie(sd, values="JC_Nos.", names="Service Type", hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_traces(texttemplate="%{label}<br><b>%{percent}</b>")
        fig.update_layout(legend=dict(orientation="v", x=1.05, y=0.5))
        total_val = sd["JC_Nos."].sum()
        fig.add_annotation(
            x=0.5, y=0.5,
            text=f"{fmt_num(total_val)}",
            showarrow=False,
            font=dict(size=15, family="Inter, -apple-system, sans-serif", color="#1D1D1F"),
            xref="paper", yref="paper"
        )
        ChartEngine.render_card("🔧 Service Type Mix", fig, height=300)
        
    # Row 3: Advisors
    st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
    aa = advisor_summary(cp, adv_col=ADV_COL, as_index=False).agg(JCs=("JC_Nos.","sum"), NL=("Net_Labour","sum"))
    aa = aa[(aa["JCs"] >= 20) & (aa[ADV_COL] != "Unassigned")].copy()
    if not aa.empty:
        aa["Avg_Lab_JC"] = np.where(aa["JCs"]>0, aa["NL"]/aa["JCs"], 0)
        aa_sorted = aa.sort_values("Avg_Lab_JC", ascending=False)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Top 5 Advisors (by Avg Labour/JC)**")
            top5 = aa_sorted.head(5)[[ADV_COL, "JCs", "Avg_Lab_JC"]].rename(columns={ADV_COL: "Advisor"})
            top5["Avg_Lab_JC"] = top5["Avg_Lab_JC"].apply(fmt_inr)
            TableCard(top5, height=250, index=False)
        with c2:
            st.markdown("**Bottom 5 Advisors (by Avg Labour/JC)**")
            bot5 = aa_sorted.tail(5)[[ADV_COL, "JCs", "Avg_Lab_JC"]].iloc[::-1].rename(columns={ADV_COL: "Advisor"})
            bot5["Avg_Lab_JC"] = bot5["Avg_Lab_JC"].apply(fmt_inr)
            TableCard(bot5, height=250, index=False)

    # Row 4: Locations
    st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
    loc_cp = location_summary(cp, as_index=True).agg(JCs=("JC_Nos.","sum"), NL=("Net_Labour","sum")).reset_index()
    if not loc_cp.empty:
        loc_cp = loc_cp.sort_values("NL", ascending=False)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Top 5 Locations (by Net Labour)**")
            top5_loc = loc_cp.head(5)[["Location Name", "JCs", "NL"]].rename(columns={"NL": "Net Labour"})
            top5_loc["Net Labour"] = top5_loc["Net Labour"].apply(fmt_inr)
            TableCard(top5_loc, height=250, index=False)
        with c2:
            st.markdown("**Bottom 5 Locations (by Net Labour)**")
            bot5_loc = loc_cp.tail(5)[["Location Name", "JCs", "NL"]].iloc[::-1].rename(columns={"NL": "Net Labour"})
            bot5_loc["Net Labour"] = bot5_loc["Net Labour"].apply(fmt_inr)
            TableCard(bot5_loc, height=250, index=False)

    st.markdown('<hr class="zone-separator" />', unsafe_allow_html=True)

    # ── ZONE D: Deep Drill Navigation Rail ───────────────────────────
    section_title("Deep Drill Navigation")
    st.markdown('<div class="zone-intro">Select a functional area below to leave the Executive Command Center and drill into operational specifics.</div>', unsafe_allow_html=True)
    
    NAV_ITEMS = [
        ("Labour",         "Labour"),
        ("Parts Detail",   "Parts Detail"),
        ("Margin",         "Margin"),
        ("Discounts",      "Discounts"),
        ("Leakage",        "Leakage Center"),
        ("Sales Mix",      "Sales Mix"),
        ("Advisors",       "Advisors"),
        ("Locations",      "Locations"),
        ("Targets",        "Targets"),
        ("Profit & Loss",  "Profit & Loss"),
        ("Internal Audit", "Internal Audit"),
    ]
    
    # Render in wrapping rows of 6 columns to prevent extreme squishing
    for i in range(0, len(NAV_ITEMS), 6):
        row_items = NAV_ITEMS[i:i+6]
        cols = st.columns(6)
        for col, (label, page_key) in zip(cols, row_items):
            with col:
                if st.button(label, key=f"nav_drill_{page_key}", use_container_width=True):
                    navigate_to_page(page_key)
