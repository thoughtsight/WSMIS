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
    apply_service_type_filter, apply_advisor_filter, apply_mp_pb_filter, split_cp_pp
)
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num
from utils.constants import ADV_COL, MP_COLORS, MONTH_SORT_ORDER

# Import shared UI helpers from app
from ui.kpi_cards import kpi
from ui.tables import html_table
from ui.traffic import yoy_badge, traffic_light, tgt_badge
from ui.helpers import apply_chart, clean_hover, _render_finding
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num

def render(df, pairs, comparison_mode=True, selected_months=None):
    if df.empty: return
    pp_months = [p[1] for p in pairs]
    # df is already filtered by selected_months at main level, use it directly for current period
    cp = df.copy()
    pp = apply_month_filter(df, "Month Name", pp_months)
    if cp.empty:
        st.warning("No data for the selected period. Please adjust the month picker.")
        return

    st.markdown('<div class="section-card"><div class="section-title">🧠 Executive Summary</div>', unsafe_allow_html=True)

    # 5.1 — Page layout
    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        if st.button("🧠 Generate Summary", key="exec_gen"):
            st.session_state["exec_generated"] = True
    with c2:
        cp_months_list = sorted(cp["Month Name"].unique(), key=lambda x: MONTH_SORT_ORDER.get(x, 99))
        pp_months_list = sorted(pp["Month Name"].unique(), key=lambda x: MONTH_SORT_ORDER.get(x, 99)) if not pp.empty else []
        period_text = f"{cp_months_list[0]} → {cp_months_list[-1]}" if cp_months_list else "No data"
        if pp_months_list:
            period_text += f" vs {pp_months_list[0]} → {pp_months_list[-1]}"
        st.markdown(f"**Period:** {period_text}")
    with c3:
        use_ai = st.toggle("✨ AI-Enhanced Prose", value=False, key="exec_ai")

    if not st.session_state.get("exec_generated", False):
        st.info("Click 'Generate Summary' to produce the executive brief.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # 5.1a — Auto-generated Top Insights
    st.markdown('<div class="section-title" style="margin-top:20px">✨ Top Insights</div>', unsafe_allow_html=True)
    i1, i2, i3 = st.columns(3)
    
    # Best location
    loc_lab = location_summary(cp, as_index=True)["Net_Labour"].sum()
    best_loc = loc_lab.idxmax() if not loc_lab.empty and loc_lab.max() > 0 else "N/A"
    best_loc_val = loc_lab.max() if best_loc != "N/A" else 0
    with i1:
        st.markdown(f'''<div class="insight-card pos">
            <div class="insight-title">🏆 Best Location</div>
            <div class="insight-stat">{best_loc} <span style="font-size:12px;color:#8E8E93">({fmt_inr(best_loc_val)})</span></div>
        </div>''', unsafe_allow_html=True)
        
    # Highest discount advisor
    adv_disc = advisor_summary(cp, adv_col=ADV_COL, as_index=True).agg(L=('Pre-GST Labour','sum'), D=('Labour Discount','sum'))
    adv_disc['D%'] = calc_ratio(adv_disc['D'], adv_disc['L'], multiplier=100, fill_value=np.nan)
    high_adv = adv_disc['D%'].idxmax() if not adv_disc.empty and not adv_disc['D%'].isna().all() else "N/A"
    high_adv_val = adv_disc.loc[high_adv, 'D%'] if high_adv != "N/A" else 0
    with i2:
        st.markdown(f'''<div class="insight-card warn">
            <div class="insight-title">⚠️ Highest Discount Advisor</div>
            <div class="insight-stat">{high_adv} <span style="color:#CF222E;font-weight:600;font-size:12px">({high_adv_val:.1f}%)</span></div>
        </div>''', unsafe_allow_html=True)
        
    # Strongest Growth
    loc_cp = location_summary(cp, as_index=True)["Net_Labour"].sum()
    loc_pp = location_summary(pp, as_index=True)["Net_Labour"].sum()
    loc_yoy = calc_growth_pct(loc_cp, loc_pp, fill_value=np.nan).dropna()
    best_growth = loc_yoy.idxmax() if not loc_yoy.empty else "N/A"
    best_growth_val = loc_yoy.max() if best_growth != "N/A" else 0
    with i3:
        st.markdown(f'''<div class="insight-card pos">
            <div class="insight-title">📈 Strongest Growth</div>
            <div class="insight-stat">{best_growth} <span style="color:#1A7F37;font-weight:600;font-size:12px">(+{best_growth_val:.1f}%)</span></div>
        </div>''', unsafe_allow_html=True)

    # 5.2 — KPI snapshot (8 metric cards)
    st.markdown('<div class="section-title" style="margin-top:20px">📊 KPI Snapshot</div>', unsafe_allow_html=True)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi5, kpi6, kpi7, kpi8 = st.columns(4)

    jc_cp = get_jobcard_count(cp); jc_pp = get_jobcard_count(pp)
    lab_cp = get_net_labour(cp); lab_pp = get_net_labour(pp)
    parts_cp = get_net_parts(cp); parts_pp = get_net_parts(pp)
    margin_cp = calculate_total_margin(cp); margin_pp = calculate_total_margin(pp)
    avg_lab_jc_cp = lab_cp / jc_cp if jc_cp > 0 else 0
    avg_lab_jc_pp = lab_pp / jc_pp if jc_pp > 0 else 0
    disc_cp = calc_ratio(calculate_labour_discount(cp), get_labour_sales(cp), multiplier=100, fill_value=0)
    disc_pp = calc_ratio(calculate_labour_discount(pp), get_labour_sales(pp), multiplier=100, fill_value=0)
    oil_jcs = cp[cp["Oil_Sale_Qty"] > 0]["JC_Nos."].count()
    total_jcs = len(cp[cp["JC_Nos."] > 0])
    oil_pen = calc_ratio(oil_jcs, total_jcs, multiplier=100, fill_value=0)
    ws_jcs = cp[cp["MP_PB"] == "MP"]["JC_Nos."].sum()
    bs_jcs = cp[cp["MP_PB"] == "PB"]["JC_Nos."].sum()
    ws_ratio = calc_ratio(ws_jcs, ws_jcs + bs_jcs, multiplier=100, fill_value=0)

    with kpi1:
        st.metric("Total JCs", f"{jc_cp:,.0f}", f"{((jc_cp-jc_pp)/jc_pp*100 if jc_pp>0 else 0):+.1f}%", help="Total number of Job Cards closed in this period")
    with kpi2:
        st.metric("Net Labour", fmt_inr(lab_cp), f"{((lab_cp-lab_pp)/lab_pp*100 if lab_pp>0 else 0):+.1f}%", help="Pre-GST Labour Revenue minus Labour Discounts")
    with kpi3:
        st.metric("Net Parts", fmt_inr(parts_cp), f"{((parts_cp-parts_pp)/parts_pp*100 if parts_pp>0 else 0):+.1f}%", help="Pre-GST Parts Revenue minus Parts Discounts")
    with kpi4:
        st.metric("Total Margin", fmt_inr(margin_cp), f"{((margin_cp-margin_pp)/margin_pp*100 if margin_pp>0 else 0):+.1f}%")
    with kpi5:
        st.metric("Avg Labour/JC", fmt_inr(avg_lab_jc_cp), f"{((avg_lab_jc_cp-avg_lab_jc_pp)/avg_lab_jc_pp*100 if avg_lab_jc_pp>0 else 0):+.1f}%")
    with kpi6:
        st.metric("Disc %", f"{disc_cp:.2f}%", f"{disc_cp-disc_pp:+.2f}%", delta_color="inverse")
    with kpi7:
        st.metric("Oil Penetration", f"{oil_pen:.1f}%")
    with kpi8:
        st.metric("WS/BS Split", f"{ws_ratio:.0f}% / {100-ws_ratio:.0f}%")

    # 5.3 — Rule-based NLG narrative
    st.markdown('<div class="section-title" style="margin-top:20px">📄 Management Brief</div>', unsafe_allow_html=True)

    def generate_executive_narrative(cp, pp, cp_months, pp_months):
        sections = {}
        # 1. Period Overview
        cp_lab = get_net_labour(cp); pp_lab = get_net_labour(pp)
        yoy_lab = calc_growth_pct(cp_lab, pp_lab, fill_value=0)
        direction = "grew" if yoy_lab >= 0 else "declined"
        cp_months_list = sorted(cp["Month Name"].unique(), key=lambda x: MONTH_SORT_ORDER.get(x, 99))
        pp_months_list = sorted(pp["Month Name"].unique(), key=lambda x: MONTH_SORT_ORDER.get(x, 99)) if not pp.empty else []
        cp_period_str = f"{cp_months_list[0]} to {cp_months_list[-1]}" if cp_months_list else "selected period"
        pp_period_str = f"{pp_months_list[0]} to {pp_months_list[-1]}" if pp_months_list else "prior period"
        sections["period"] = (
            f"For the period {cp_period_str}, the group reported net labour revenue of "
            f"{fmt_inr(cp_lab)}, which {direction} {abs(yoy_lab):.1f}% compared to the prior period "
            f"({fmt_inr(pp_lab)}). Total job cards processed: {int(get_jobcard_count(cp)):,} "
            f"across {cp['Location Name'].nunique()} active locations."
        )
        # 2. Location Intelligence
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
        # 3. Advisor Spotlight
        adv_jc = advisor_summary(cp, adv_col=ADV_COL, as_index=True)["JC_Nos."].sum()
        adv_lab = advisor_summary(cp, adv_col=ADV_COL, as_index=True)["Net_Labour"].sum()
        adv_disc = advisor_summary(cp, adv_col=ADV_COL, as_index=True).apply(
            lambda x: calc_ratio(calculate_labour_discount(x), get_labour_sales(x), multiplier=100, fill_value=0)
            if get_labour_sales(x) > 0 else 0
        )
        star = adv_lab.idxmax() if not getattr(locals().get('cp', None), 'empty', True) else "N/A" if not adv_lab.empty else "N/A"
        risk = adv_disc[adv_disc > 25].index.tolist() if not adv_disc.empty else []
        sections["advisors"] = (
            f"Star advisor this period: {star} with {fmt_inr(adv_lab.get(star, 0))} net labour. "
            f"{'High discount risk advisors (>25%): ' + ', '.join(risk[:5]) + '.' if risk else 'No advisors exceeded the 25% discount threshold.'}"
        )
        # 4. Discount Health
        total_gross = get_labour_sales(cp)
        total_disc = calculate_labour_discount(cp)
        disc_pct = calc_ratio(total_disc, total_gross, multiplier=100, fill_value=0)
        pp_disc_pct = calc_ratio(calculate_labour_discount(pp), get_labour_sales(pp), multiplier=100, fill_value=0)
        disc_dir = "improved" if disc_pct < pp_disc_pct else "worsened"
        leakage = max(0, (disc_pct - 15) / 100 * total_gross)
        sections["discount"] = (
            f"Group labour discount stands at {disc_pct:.1f}% (vs {pp_disc_pct:.1f}% prior period — {disc_dir}). "
            f"Estimated revenue leakage vs 15% benchmark: {fmt_inr(leakage)}. "
            f"{'Immediate discount audit recommended.' if disc_pct > 25 else 'Discount levels are within acceptable range.'}"
        )
        # 5. Sales Mix
        oil_jcs = cp[cp["Oil_Sale_Qty"] > 0]["JC_Nos."].count()
        total_jcs = len(cp[cp["JC_Nos."] > 0])
        oil_pen = calc_ratio(oil_jcs, total_jcs, multiplier=100, fill_value=0)
        sections["sales_mix"] = (
            f"Oil penetration: {oil_pen:.1f}% of job cards. "
            f"Total oil revenue: {fmt_inr(get_oil_sales(cp))}. "
            f"Battery: {fmt_inr(get_battery_sales(cp))}, Tyre: {fmt_inr(get_tyre_sales(cp))}, "
            f"Accessories: {fmt_inr(get_accessory_sales(cp))}."
        )
        # 6. Forecast Signal
        recent = cp.groupby("Month_Sort", dropna=False)["Net_Labour"].sum().reset_index().sort_values("Month_Sort").tail(6)
        if len(recent) >= 3:
            slope = np.polyfit(recent["Month_Sort"], recent["Net_Labour"], 1)[0]
            signal = "Strong Momentum 🟢" if slope > 50000 else ("At Risk 🔴" if slope < -50000 else "Stable 🟡")
        else:
            signal = "Insufficient Data"
        sections["forecast"] = f"Trend signal based on last 6 months: {signal}."
        # 7. Recommended Actions
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

    cp_months_list = sorted(cp["Month Name"].unique(), key=lambda x: MONTH_SORT_ORDER.get(x, 99))
    pp_months_list = sorted(pp["Month Name"].unique(), key=lambda x: MONTH_SORT_ORDER.get(x, 99)) if not pp.empty else []
    sections = generate_executive_narrative(cp, pp, cp_months_list, pp_months_list)

    # 5.4 — Render the narrative
    full_text = ""
    for title, text in [("Period Overview", sections["period"]), ("Location Intelligence", sections["locations"]),
                         ("Advisor Spotlight", sections["advisors"]), ("Discount Health", sections["discount"]),
                         ("Sales Mix", sections["sales_mix"]), ("Forecast Signal", sections["forecast"]),
                         ("Recommended Actions", sections["actions"])]:
        st.markdown(f'<div style="background:#F5F5F7;border-radius:8px;padding:12px;margin-bottom:8px;"><b>{title}</b><br>{text}</div>', unsafe_allow_html=True)
        full_text += f"{title}:\n{text}\n\n"

    # Copy & Download buttons
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📋 Copy All", key="exec_copy"):
            st.write("Text copied to clipboard (simulated)")
    with c2:
        cp_months_list = sorted(cp["Month Name"].unique(), key=lambda x: MONTH_SORT_ORDER.get(x, 99))
        filename_start = cp_months_list[0] if cp_months_list else "start"
        filename_end = cp_months_list[-1] if cp_months_list else "end"
        st.download_button("📥 Download .txt", full_text, file_name=f"Executive_Summary_{filename_start}_{filename_end}.txt", key="exec_download")

    # 5.5 — Optional Anthropic API enhancement
    if use_ai:
        st.markdown('<div class="section-title" style="margin-top:20px">✨ AI-Enhanced Prose</div>', unsafe_allow_html=True)
        try:
            import anthropic
            client_ai = anthropic.Anthropic()
            base_text = "\n\n".join(sections.values())
            message = client_ai.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": (
                        "You are a senior automotive dealership analyst. Rewrite this management brief "
                        "in polished professional English for a dealership group MD. Keep all numbers "
                        "exactly as given. Output only the rewritten text, no preamble:\n\n" + base_text
                    )
                }]
            )
            enhanced_text = message.content[0].text
            st.markdown(enhanced_text)
        except Exception as e:
            st.warning(f"AI enhancement unavailable: {e}. Showing rule-based summary.")

    st.markdown('</div>', unsafe_allow_html=True)
