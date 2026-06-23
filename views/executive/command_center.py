"""
Executive Command Center -- v2 Unified Data Pipeline
RC1 Stabilization: Consumes AppContext; no local filtering, target loading, or alert generation.
"""
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
from utils.constants import LOC_COLORS, MP_COLORS, CLIENTS
from services.benchmark_provider import DefaultBenchmarkProvider
from services.executive_alert_engine import ExecutiveAlertEngine
from services.ai.provider import get_ai_client, get_default_model
from views.dashboard_common import inject_responsive_css, navigate_to_page


# ─────────────────────────────────────────────────────────────────────────────
# KPI Model: single computation, shared by all consumers
# ─────────────────────────────────────────────────────────────────────────────

def build_kpi_model(cp, pp, targets_df, benchmarks):
    """
    Compute all Executive KPIs in one place.
    All downstream components (narrative, cards, charts, alerts) read from this model.
    No calculations are permitted outside this function.
    """
    def _s(df, col):
        return float(df[col].sum()) if not df.empty and col in df.columns else 0.0

    def _div(num, den, pct=False):
        if den == 0 or (hasattr(den, '__float__') and (den != den)):  # NaN check
            return 0.0
        try:
            return float(num / den) * (100.0 if pct else 1.0)
        except Exception:
            return 0.0

    cp_jc   = _s(cp, "JC_Nos.")
    pp_jc   = _s(pp, "JC_Nos.")
    cp_rev  = calculate_net_revenue(cp)  if not cp.empty else 0.0
    pp_rev  = calculate_net_revenue(pp)  if not pp.empty else 0.0
    cp_mar  = calculate_total_margin(cp) if not cp.empty else 0.0
    pp_mar  = calculate_total_margin(pp) if not pp.empty else 0.0
    cp_lab  = _s(cp, "Net_Labour")
    pp_lab  = _s(pp, "Net_Labour")

    cp_avg_lab_jc = _div(cp_lab, cp_jc)
    pp_avg_lab_jc = _div(pp_lab, pp_jc)
    cp_mar_pct    = _div(cp_mar, cp_rev, pct=True)
    pp_mar_pct    = _div(pp_mar, pp_rev, pct=True)

    avg_disc    = calculate_labour_discount_pct(cp) if not cp.empty else 0.0
    pp_avg_disc = calculate_labour_discount_pct(pp) if not pp.empty else 0.0

    # Revenue vs Target -- uses centralized targets_df, already managed by app.py
    cp_months_set = set(cp["Month Name"].unique()) if not cp.empty else set()
    tgt_cp = targets_df[targets_df["Month Name"].isin(cp_months_set)] if not targets_df.empty else pd.DataFrame()
    tgt_rev = 0.0
    if not tgt_cp.empty:
        for col in ["WS_Labour_Target", "BS_Labour_Target", "WS_Parts_Target", "BS_Parts_Target"]:
            if col in tgt_cp.columns:
                tgt_rev += float(tgt_cp[col].sum())

    rev_tgt_pct = _div(cp_rev, tgt_rev, pct=True) if tgt_rev > 0 else None  # None = no target

    # Discount leakage
    pre_gst_labour = _s(cp, "Pre-GST Labour")
    total_disc     = float(get_labour_discount(cp)) if not cp.empty else 0.0
    pp_gst_labour  = _s(pp, "Pre-GST Labour")
    disc_pct    = _div(total_disc,                                            pre_gst_labour, pct=True)
    pp_disc_pct = _div(float(get_labour_discount(pp)) if not pp.empty else 0.0, pp_gst_labour, pct=True)
    leakage     = max(0.0, (disc_pct - benchmarks["labour_discount_target"]) / 100.0 * pre_gst_labour)

    # Oil penetration
    oil_jcs   = int(cp[cp["Oil_Sale_Qty"] > 0]["JC_Nos."].count()) if not cp.empty and "Oil_Sale_Qty" in cp.columns else 0
    valid_jcs = int(len(cp[cp["JC_Nos."] > 0]))                    if not cp.empty else 0
    oil_pen   = _div(oil_jcs, valid_jcs, pct=True)

    # Trend signal
    trend_signal = "Insufficient Data"
    if not cp.empty and "Month_Sort" in cp.columns:
        recent = (
            cp.groupby("Month_Sort", dropna=False)["Net_Labour"]
            .sum().reset_index().sort_values("Month_Sort").tail(6)
        )
        if len(recent) >= 3:
            slope = np.polyfit(recent["Month_Sort"], recent["Net_Labour"], 1)[0]
            if slope > 50000:
                trend_signal = "Strong Momentum \U0001f7e2"
            elif slope < -50000:
                trend_signal = "At Risk \U0001f534"
            else:
                trend_signal = "Stable \U0001f7e1"

    return dict(
        cp_rev=cp_rev, pp_rev=pp_rev, cp_mar=cp_mar, pp_mar=pp_mar,
        cp_mar_pct=cp_mar_pct, pp_mar_pct=pp_mar_pct,
        cp_jc=cp_jc, pp_jc=pp_jc, cp_lab=cp_lab, pp_lab=pp_lab,
        cp_avg_lab_jc=cp_avg_lab_jc, pp_avg_lab_jc=pp_avg_lab_jc,
        avg_disc=avg_disc, pp_avg_disc=pp_avg_disc,
        tgt_rev=tgt_rev, rev_tgt_pct=rev_tgt_pct,
        disc_pct=disc_pct, pp_disc_pct=pp_disc_pct, leakage=leakage,
        oil_pen=oil_pen, trend_signal=trend_signal, tgt_cp=tgt_cp,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Narrative Generator: formatting only, no calculations
# ─────────────────────────────────────────────────────────────────────────────

def generate_executive_narrative(cp, pp, cp_months, pp_months, kpi, benchmarks):
    """
    Produce rule-based narrative text.
    Receives a pre-computed KPI model -- performs NO business calculations.
    """
    sections = {}

    cp_period = (
        f"{cp_months[0]} to {cp_months[-1]}" if len(cp_months) > 1
        else (cp_months[0] if cp_months else "selected period")
    )
    pp_period = (
        f"{pp_months[0]} to {pp_months[-1]}" if len(pp_months) > 1
        else (pp_months[0] if pp_months else "prior period")
    )
    yoy_lab   = calc_growth_pct(kpi["cp_lab"], kpi["pp_lab"], fill_value=0)
    direction = "grew" if yoy_lab >= 0 else "declined"
    n_locs    = int(cp["Location Name"].nunique()) if not cp.empty else 0

    sections["period"] = (
        f"For the period {cp_period}, the group reported net labour revenue of "
        f"{fmt_inr(kpi['cp_lab'])}, which {direction} {abs(yoy_lab):.1f}% compared to the prior period "
        f"({fmt_inr(kpi['pp_lab'])}). Total job cards processed: {int(kpi['cp_jc']):,} "
        f"across {n_locs} active location(s)."
    )

    # Locations
    if not cp.empty and not pp.empty:
        loc_cp_nl = location_summary(cp, as_index=True)["Net_Labour"].sum()
        loc_pp_nl = location_summary(pp, as_index=True)["Net_Labour"].sum()
        loc_yoy   = calc_growth_pct(loc_cp_nl, loc_pp_nl, fill_value=np.nan).dropna()
        if n_locs == 1:
            sections["locations"] = f"Single-location period. YoY Net Labour growth: {yoy_lab:+.1f}%."
        elif loc_yoy.empty:
            sections["locations"] = "Insufficient comparison data for location breakdown."
        else:
            top3 = loc_yoy.nlargest(3)
            bot3 = loc_yoy.nsmallest(3)
            top_str = "; ".join([f"{l} (+{v:.1f}%)" for l, v in top3.items()]) if not top3.empty else "N/A"
            bot_str = "; ".join([f"{l} ({v:+.1f}%)" for l, v in bot3.items()]) if not bot3.empty else "N/A"
            sections["locations"] = (
                f"Top performing locations by YoY labour growth: {top_str}. "
                f"Locations requiring management attention: {bot_str}."
            )
    else:
        sections["locations"] = "Insufficient comparison data for location breakdown."

    # Advisors
    if not cp.empty:
        adv_lab  = advisor_summary(cp, adv_col=ADV_COL, as_index=True)["Net_Labour"].sum()
        adv_disc = advisor_summary(cp, adv_col=ADV_COL, as_index=True).apply(
            lambda x: calc_ratio(get_labour_discount(x), get_labour_sales(x), multiplier=100, fill_value=0)
            if get_labour_sales(x) > 0 else 0, axis=1
        )
        star = adv_lab.idxmax() if not adv_lab.empty else "N/A"
        risk = adv_disc[adv_disc > 25].index.tolist() if not adv_disc.empty else []
        sections["advisors"] = (
            f"Star advisor this period: {star} with {fmt_inr(adv_lab.get(star, 0))} net labour. "
            + (f"High discount risk advisors (>25%): {', '.join(risk[:5])}." if risk
               else "No advisors exceeded the 25% discount threshold.")
        )
    else:
        sections["advisors"] = "No advisor data available for the selected period."

    # Discount
    disc_dir = "improved" if kpi["disc_pct"] < kpi["pp_disc_pct"] else "worsened"
    sections["discount"] = (
        f"Group labour discount stands at {kpi['disc_pct']:.1f}% (vs {kpi['pp_disc_pct']:.1f}% prior period -- {disc_dir}). "
        f"Estimated revenue leakage vs {benchmarks['labour_discount_target']}% benchmark: {fmt_inr(kpi['leakage'])}. "
        + ("Immediate discount audit recommended." if kpi["disc_pct"] > benchmarks["high_discount_alert"]
           else "Discount levels are within acceptable range.")
    )

    # Sales mix
    sections["sales_mix"] = (
        f"Oil penetration: {kpi['oil_pen']:.1f}% of job cards. "
        f"Total oil revenue: {fmt_inr(get_oil_sales(cp) if not cp.empty else 0)}. "
        f"Battery: {fmt_inr(get_battery_sales(cp) if not cp.empty else 0)}, "
        f"Tyre: {fmt_inr(get_tyre_sales(cp) if not cp.empty else 0)}, "
        f"Accessories: {fmt_inr(get_accessory_sales(cp) if not cp.empty else 0)}."
    )

    sections["forecast"] = f"Trend signal based on last 6 months: {kpi['trend_signal']}."

    # Actions
    actions = []
    if kpi["disc_pct"] > 20:
        actions.append("1. Conduct immediate discount audit for advisors exceeding 20% -- Group Level")
    if not cp.empty and not pp.empty:
        loc_cp_nl2 = location_summary(cp, as_index=True)["Net_Labour"].sum()
        loc_pp_nl2 = location_summary(pp, as_index=True)["Net_Labour"].sum()
        loc_yoy2   = calc_growth_pct(loc_cp_nl2, loc_pp_nl2, fill_value=np.nan).dropna()
        if not loc_yoy2.empty and loc_yoy2.min() < -15:
            worst = loc_yoy2.idxmin()
            actions.append(f"2. Initiate turnaround review for {worst} -- Location Manager")
    if kpi["oil_pen"] < 60:
        actions.append("3. Launch oil penetration drive -- target 70% by next quarter -- Advisor Level")
    if not actions:
        actions.append("1. Maintain current performance standards and focus on margin improvement.")
    sections["actions"] = "\n".join(actions)

    return sections


# ─────────────────────────────────────────────────────────────────────────────
# Main Render -- consumes AppContext exclusively
# ─────────────────────────────────────────────────────────────────────────────

def render(df, pairs, alerts=None, comparison_mode=True, selected_months=None, ctx=None):
    """
    Executive Command Center entry point.

    Parameters
    ----------
    df              : df_filtered_full (CP + PP months, globally filtered).
    pairs           : [(cp_month, pp_month), ...]
    alerts          : pre-computed flat alert list from app.py (informational).
    comparison_mode : bool
    selected_months : CP months selected by the user.
    ctx             : AppContext -- provides df_filtered_cp, targets_df, etc.
    """
    inject_responsive_css()
    PageBreadcrumb(["Executive", "Command Center"])

    with st.spinner("Loading Executive Command Center..."):
        if df.empty:
            EmptyState("No data available for the selected period.")
            return

    # ── Resolve CP / PP dataframes ──────────────────────────────────
    cp_months = selected_months if selected_months else []
    pp_months = [p[1] for p in pairs]

    if ctx is not None:
        # Use pre-sliced CP frame -- eliminates duplicate apply_month_filter
        cp         = ctx.df_filtered_cp
        pp         = apply_month_filter(df, "Month Name", pp_months) if pp_months else pd.DataFrame()
        targets_df = ctx.targets_df
    else:
        # Compatibility fallback for callers that have not been updated yet
        cp         = apply_month_filter(df, "Month Name", cp_months)
        pp         = apply_month_filter(df, "Month Name", pp_months) if pp_months else pd.DataFrame()
        targets_df = pd.DataFrame()

    # ── Benchmarks -- centralized provider ─────────────────────────
    _bench = DefaultBenchmarkProvider()
    benchmarks = {
        "labour_discount_target": _bench.get_benchmark("labour_discount_target"),
        "high_discount_alert":    _bench.get_benchmark("high_discount_alert"),
    }

    # ── KPI Model -- computed exactly once ─────────────────────────
    kpi = build_kpi_model(cp, pp, targets_df, benchmarks)

    cp_months_list = sorted(cp["Month Name"].unique(), key=lambda x: MONTH_SORT_ORDER.get(x, 99)) if not cp.empty else []
    pp_months_list = sorted(pp["Month Name"].unique(), key=lambda x: MONTH_SORT_ORDER.get(x, 99)) if not pp.empty else []
    n_cp_months    = len(cp_months_list)
    n_locs         = int(cp["Location Name"].nunique()) if not cp.empty else 0

    # ── ZONE A: KPI Cards ──────────────────────────────────────────
    rev_tgt_display = (
        f"{kpi['rev_tgt_pct']:.1f}%" if kpi["rev_tgt_pct"] is not None
        else "Target Not Configured"
    )
    rev_tgt_cp_val = kpi["rev_tgt_pct"] if kpi["rev_tgt_pct"] is not None else None

    KPIGrid([
        {"label": "Total Revenue",    "value": fmt_inr(kpi["cp_rev"]),        "cp": kpi["cp_rev"],        "pp": kpi["pp_rev"],        "pp_label": f"PP {fmt_inr(kpi['pp_rev'])}"},
        {"label": "Margin %",         "value": f"{kpi['cp_mar_pct']:.1f}%",   "cp": kpi["cp_mar_pct"],    "pp": kpi["pp_mar_pct"],    "pp_label": f"PP {kpi['pp_mar_pct']:.1f}%"},
        {"label": "Total JCs",        "value": fmt_num(kpi["cp_jc"]),         "cp": kpi["cp_jc"],         "pp": kpi["pp_jc"],         "pp_label": f"PP {fmt_num(kpi['pp_jc'])}"},
        {"label": "Avg Labour / JC",  "value": fmt_inr(kpi["cp_avg_lab_jc"]), "cp": kpi["cp_avg_lab_jc"], "pp": kpi["pp_avg_lab_jc"], "pp_label": f"PP {fmt_inr(kpi['pp_avg_lab_jc'])}"},
        {
            "label": "Avg Discount %",
            "value": f"{kpi['avg_disc']:.1f}%",
            "target": f"{benchmarks['labour_discount_target']}%",
            "benchmark": f"Critical {benchmarks['high_discount_alert']}%",
            "invert_trend": True,
            "pp_label": f"PP {kpi['pp_avg_disc']:.1f}%",
        },
        {
            "label": "Revenue vs Target",
            "value": rev_tgt_display,
            "cp":    rev_tgt_cp_val,
            "pp":    100 if rev_tgt_cp_val is not None else None,
            "pp_label": "Target 100%",
        },
    ], cols=6)

    st.markdown('<hr class="zone-separator" />', unsafe_allow_html=True)

    # ── ZONE B: Alert & Opportunity Rail ───────────────────────────
    # Alert engine is evaluated on the same CP/PP frames as the KPI model
    _engine          = ExecutiveAlertEngine(DefaultBenchmarkProvider())
    structured_alerts = _engine.evaluate(cp, pp)

    section_title("Alert & Opportunity Rail")

    col1, col2, col3 = st.columns(3)

    def render_rail_cards(alert_list, modifier_class):
        if not alert_list:
            st.markdown('<div class="insight-stat">\u2713 No alerts in this category.</div>', unsafe_allow_html=True)
            return
        for a in alert_list[:3]:
            rule   = a.get("rule")   or a.get("opportunity") or "N/A"
            impact = a.get("impact") or a.get("gain")        or "N/A"
            owner  = a.get("owner")  or "N/A"
            st.markdown(
                f'<div class="insight-card {modifier_class}">'
                f'<div class="insight-title">{rule}</div>'
                f'<div class="insight-stat">Impact: {impact}</div>'
                f'<div class="insight-stat">Owner: \U0001f464 {owner}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
        if len(alert_list) > 3:
            st.markdown(f'<div class="insight-stat">+ {len(alert_list) - 3} More...</div>', unsafe_allow_html=True)

    with col1:
        st.markdown(f"**\U0001f534 Critical ({len(structured_alerts['critical'])})**")
        render_rail_cards(structured_alerts["critical"], "neg")
    with col2:
        st.markdown(f"**\U0001f7e1 Warning ({len(structured_alerts['warning'])})**")
        render_rail_cards(structured_alerts["warning"], "warn")
    with col3:
        st.markdown(f"**\U0001f535 Opportunity ({len(structured_alerts['opportunities'])})**")
        render_rail_cards(structured_alerts["opportunities"], "pos")

    with st.expander("View Alert Details", expanded=False):
        def render_alert_detail(alert, modifier_class):
            rule      = alert.get("rule")      or alert.get("opportunity") or "N/A"
            impact    = alert.get("impact")    or alert.get("gain")        or "N/A"
            current   = alert.get("current")   or alert.get("situation")   or "N/A"
            benchmark = alert.get("benchmark") or alert.get("basis")       or "N/A"
            variance  = alert.get("variance")  or alert.get("benefit")     or "N/A"
            owner     = alert.get("owner")     or "N/A"
            reason    = alert.get("reason")    or alert.get("situation")   or "N/A"
            html = (
                f'<div class="insight-card {modifier_class}">'
                f'<div style="display:flex;justify-content:space-between;margin-bottom:{T.SPACE_2}px;">'
                f'<div class="insight-title" style="font-size:{T.TYPE_LG}px;">{rule}</div>'
                f'<div class="insight-title" style="font-size:{T.TYPE_BASE}px;">Impact: {impact}</div>'
                f"</div>"
                f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:{T.SPACE_2}px;font-size:{T.TYPE_SM}px;color:var(--color-text-secondary);margin-bottom:{T.SPACE_3}px;">'
                f'<div><span style="color:var(--color-text-tertiary);">Current Value:</span> <b>{current}</b></div>'
                f'<div><span style="color:var(--color-text-tertiary);">Benchmark:</span> {benchmark}</div>'
                f'<div><span style="color:var(--color-text-tertiary);">Variance:</span> <b>{variance}</b></div>'
                f'<div><span style="color:var(--color-text-tertiary);">Owner:</span> \U0001f464 {owner}</div>'
                f"</div>"
                f'<div class="insight-stat"><span style="color:var(--color-text-tertiary);">Reason:</span> {reason}</div>'
                f"</div>"
            )
            st.markdown(html, unsafe_allow_html=True)

        st.markdown('<div class="insight-title" style="color:var(--color-danger);">Critical Alerts</div>', unsafe_allow_html=True)
        if not structured_alerts["critical"]:
            st.markdown("No critical alerts.")
        for a in structured_alerts["critical"]:
            render_alert_detail(a, "neg")

        st.markdown('<div class="insight-title" style="color:var(--color-warning); margin-top:16px;">Warning Alerts</div>', unsafe_allow_html=True)
        if not structured_alerts["warning"]:
            st.markdown("No warning alerts.")
        for a in structured_alerts["warning"]:
            render_alert_detail(a, "warn")

        st.markdown('<div class="insight-title" style="color:var(--color-primary); margin-top:16px;">Opportunities</div>', unsafe_allow_html=True)
        if not structured_alerts["opportunities"]:
            st.markdown("No opportunities.")
        for a in structured_alerts["opportunities"]:
            render_alert_detail(a, "pos")

    st.markdown('<hr class="zone-separator" />', unsafe_allow_html=True)

    # ── Executive Brief ─────────────────────────────────────────────
    section_title("Executive Brief")
    st.markdown('<p class="ai-band-label">Executive Brief</p>', unsafe_allow_html=True)

    # Narrative receives pre-computed KPI model -- zero calculations inside
    sections = generate_executive_narrative(cp, pp, cp_months_list, pp_months_list, kpi, benchmarks)

    ai_success = False
    try:
        client_ai  = get_ai_client()
        model_name = get_default_model()
        base_text  = "\n\n".join(sections.values())
        message    = client_ai.messages.create(
            model=model_name,
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": (
                    "You are a senior automotive dealership analyst. Rewrite this management brief "
                    "in polished professional English for a dealership group MD. "
                    "Format it clearly using bullet points and short paragraphs. "
                    "Keep all numbers exactly as given. Output only the rewritten text, no preamble:\n\n"
                    + base_text
                ),
            }],
        )
        st.markdown(message.content[0].text)
        ai_success = True
    except Exception:
        ai_success = False

    if not ai_success:
        for title, text in [
            ("Period Overview",       sections["period"]),
            ("Location Intelligence", sections["locations"]),
            ("Advisor Spotlight",     sections["advisors"]),
            ("Discount Health",       sections["discount"]),
            ("Sales Mix",             sections["sales_mix"]),
            ("Forecast Signal",       sections["forecast"]),
            ("Recommended Actions",   sections["actions"]),
        ]:
            note = (
                f'<div style="margin-bottom:var(--space-2);">'
                f'<b style="color:var(--color-text-primary);font-size:var(--type-base);">{title}</b>'
                f"</div>"
                f'<div style="color:var(--color-text-primary);font-size:var(--type-base);line-height:1.6;">{text}</div>'
            )
            st.markdown(f'<div class="ai-band">{note}</div>', unsafe_allow_html=True)

    st.markdown('<hr class="zone-separator" />', unsafe_allow_html=True)

    # ── ZONE C: Workshop Intelligence ──────────────────────────────
    section_title("Workshop Intelligence")

    # Row 1: Trend and Location
    c1, c2 = st.columns(2)
    with c1:
        if n_cp_months < 2:
            st.info("Select at least 2 months to view the Net Labour trend.")
        elif not cp.empty and "Month_Sort" in cp.columns:
            max_sort   = cp["Month_Sort"].max()
            trend_df   = df[(df["Month_Sort"] <= max_sort) & (df["Month_Sort"] > max_sort - 6)]
            trend_data = (
                trend_df.groupby(["Month_Sort", "Month Name"], as_index=False, dropna=False)["Net_Labour"]
                .sum().sort_values("Month_Sort")
            )
            if not trend_data.empty:
                fig = px.line(trend_data, x="Month Name", y="Net_Labour", markers=True, title="Monthly Net Labour Trend")
                fig.update_traces(line=dict(color="#0071E3"))
                ChartEngine.render_card("\U0001f4c8 Net Labour Trend (6M)", fig, height=320)
            else:
                st.info("No trend data available.")

    with c2:
        if cp.empty:
            st.info("No location data available.")
        else:
            loc_ranking = (
                location_summary(cp, as_index=False)
                .agg(Revenue=("Net_Labour", "sum"))
                .sort_values("Revenue", ascending=True)
                .tail(10)
            )
            if not loc_ranking.empty:
                fig = px.bar(
                    loc_ranking, x="Revenue", y="Location Name",
                    orientation="h", color="Revenue", color_continuous_scale="Blues",
                )
                fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
                ChartEngine.render_card("\U0001f3c6 Revenue by Location (Top 10)", fig, height=320)

    # Row 2: WS vs BS and Service Mix
    c1, c2 = st.columns(2)
    with c1:
        if not cp.empty and "Service_Type_Group" in cp.columns:
            wd = (
                cp.groupby("Service_Type_Group", as_index=False, dropna=False)["Net_Labour"]
                .sum()
                .rename(columns={"Service_Type_Group": "Type", "Net_Labour": "Net Labour (\u20b9)"})
            )
            if not wd.empty:
                fig = px.pie(wd, values="Net Labour (\u20b9)", names="Type", hole=0.6, color="Type", color_discrete_map=MP_COLORS)
                fig.update_traces(texttemplate="%{label}<br><b>%{percent}</b>")
                fig.update_layout(legend=dict(orientation="v", x=1.05, y=0.5))
                total_val = wd["Net Labour (\u20b9)"].sum()
                fig.add_annotation(
                    x=0.5, y=0.5,
                    text=f"\u20b9{fmt_inr_short(total_val)}",
                    showarrow=False,
                    font=dict(size=15, family="Inter, -apple-system, sans-serif", color="#1D1D1F"),
                    xref="paper", yref="paper",
                )
                ChartEngine.render_card("\u2696\ufe0f WS vs BS Split", fig, height=300)

    with c2:
        if not cp.empty and "Service Type" in cp.columns:
            sd = (
                cp[cp["Service Type"] != "Wash"]
                .groupby("Service Type", as_index=False, dropna=False)["JC_Nos."]
                .sum()
            )
            if not sd.empty:
                fig = px.pie(sd, values="JC_Nos.", names="Service Type", hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_traces(texttemplate="%{label}<br><b>%{percent}</b>")
                fig.update_layout(legend=dict(orientation="v", x=1.05, y=0.5))
                total_val = sd["JC_Nos."].sum()
                fig.add_annotation(
                    x=0.5, y=0.5,
                    text=f"{fmt_num(total_val)}",
                    showarrow=False,
                    font=dict(size=15, family="Inter, -apple-system, sans-serif", color="#1D1D1F"),
                    xref="paper", yref="paper",
                )
                ChartEngine.render_card("\U0001f527 Service Type Mix", fig, height=300)

    # Row 3: Advisor Performance
    st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
    if not cp.empty:
        aa = advisor_summary(cp, adv_col=ADV_COL, as_index=False).agg(JCs=("JC_Nos.", "sum"), NL=("Net_Labour", "sum"))
        aa = aa[(aa["JCs"] >= 20) & (aa[ADV_COL] != "Unassigned")].copy()
        if not aa.empty:
            aa["Avg_Lab_JC"] = np.where(aa["JCs"] > 0, aa["NL"] / aa["JCs"], 0)
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

    # Row 4: Location Performance
    st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
    if not cp.empty:
        loc_cp = location_summary(cp, as_index=True).agg(JCs=("JC_Nos.", "sum"), NL=("Net_Labour", "sum")).reset_index()
        if not loc_cp.empty:
            loc_cp = loc_cp.sort_values("NL", ascending=False)
            if n_locs == 1:
                single = loc_cp[["Location Name", "JCs", "NL"]].rename(columns={"NL": "Net Labour"})
                single["Net Labour"] = single["Net Labour"].apply(fmt_inr)
                st.markdown("**Location Performance** *(Single Location)*")
                TableCard(single, height=150, index=False)
            else:
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

    # ── ZONE D: Deep Drill Navigation Rail ─────────────────────────
    section_title("Deep Drill Navigation")
    st.markdown(
        '<div class="zone-intro">Select a functional area below to leave the Executive Command Center and drill into operational specifics.</div>',
        unsafe_allow_html=True,
    )

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

    for i in range(0, len(NAV_ITEMS), 6):
        row_items = NAV_ITEMS[i : i + 6]
        cols = st.columns(6)
        for col, (label, page_key) in zip(cols, row_items):
            with col:
                if st.button(label, key=f"nav_drill_{page_key}", use_container_width=True):
                    navigate_to_page(page_key)

    UniversalFooter()
