import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

from utils.calculations.fact_metrics import get_net_labour
from utils.calculations.common import calc_growth_pct, calc_ratio
from utils.filters import apply_month_filter, apply_mp_pb_filter, apply_service_type_filter
from ui.formatters import fmt_inr, fmt_pct, fmt_inr_short
from utils.constants import ADV_COL, C, PLY, PLY_TITLE, MONTH_SORT_ORDER, get_ply_layout
from services.ai_service import get_narrative, get_actions

def _inject_responsive_css():
    """Inject responsive CSS for the dashboard."""
    RESPONSIVE_CSS = """
<style>
@media (max-width: 1400px) {
    [data-testid="stHorizontalBlock"] > div:nth-child(n+3) { min-width: 48% !important; }
}
@media (min-width: 1800px) {
    .kpi-value { font-size: 28px !important; }
    .kpi-label { font-size: 13px !important; }
    .section-title { font-size: 18px !important; }
}
</style>
"""
    st.markdown(RESPONSIVE_CSS, unsafe_allow_html=True)


def _initialize_cross_filter_state():
    """Initialize cross-filter state specific to this page."""
    if "labour_click_loc" not in st.session_state:
        st.session_state["labour_click_loc"] = None
    if "labour_click_month" not in st.session_state:
        st.session_state["labour_click_month"] = None


def _apply_filters(df, active_pairs, comparison_mode, selected_months):
    """Apply all global and cross-filters and return CP/PP DataFrames."""
    # Get filters from global state (app.py)
    ws_bs = st.session_state.get("filter_mp_pb", "All")
    svc_filter = st.session_state.get("filter_svc_type", [])
    click_loc = st.session_state.get("labour_click_loc")
    click_month = st.session_state.get("labour_click_month")
    
    # Apply WS/BS filter (map All/MP/PB to filter function)
    df_filtered = df
    if ws_bs == "MP":
        df_filtered = apply_mp_pb_filter(df_filtered, "MP_PB", "MP")
    elif ws_bs == "PB":
        df_filtered = apply_mp_pb_filter(df_filtered, "MP_PB", "PB")
        
    # Apply service type filter
    if svc_filter:
        df_filtered = apply_service_type_filter(df_filtered, "Service Type", svc_filter)
        
    # Apply cross-filters to make them consistent across the whole dashboard
    if click_loc:
        df_filtered = df_filtered[df_filtered["Location Name"] == click_loc]
    
    # Get active pairs and months directly from router
    cp_months_active = [p[0] for p in active_pairs]
    pp_months_active = [p[1] for p in active_pairs]
    
    if click_month:
        # Cross filter restricts the data to just that month and its paired prior month
        paired_pm = next((p[1] for p in active_pairs if p[0] == click_month), None)
        cp_months_active = [click_month]
        if paired_pm:
            pp_months_active = [paired_pm]
    
    # Split CP and PP
    cp = apply_month_filter(df_filtered, "Month Name", cp_months_active)
    pp = apply_month_filter(df_filtered, "Month Name", pp_months_active)
    
    return cp, pp


def _prepare_view_data(cp, pp, df):
    """Compute all master aggregations and KPIs needed for the dashboard once."""
    val_col = "Net_Labour"
    
    # Pre-compute master DataFrames
    cp_loc_series = cp.groupby("Location Name")[val_col].sum()
    pp_loc_series = pp.groupby("Location Name")[val_col].sum()
    
    cp_svc_series = cp.groupby("Service Type")[val_col].sum()
    pp_svc_series = pp.groupby("Service Type")[val_col].sum()
    
    # Also need Location x Service Type for drill-downs and drivers
    loc_svc_cp = cp.groupby(["Location Name", "Service Type"])[val_col].sum()
    loc_svc_pp = pp.groupby(["Location Name", "Service Type"])[val_col].sum()
    
    # Basic revenue metrics
    cp_val = cp[val_col].sum()
    pp_val = pp[val_col].sum()
    growth_pct = calc_growth_pct(cp_val, pp_val, fill_value=0)
    abs_growth = cp_val - pp_val
    
    # Revenue per jobcard
    cp_rpc = calc_ratio(cp_val, cp["JC_Nos."].sum(), fill_value=0) if "JC_Nos." in cp.columns else 0
    pp_rpc = calc_ratio(pp_val, pp["JC_Nos."].sum(), fill_value=0) if "JC_Nos." in pp.columns else 0
    rpc_growth = calc_growth_pct(cp_rpc, pp_rpc, fill_value=0)
    
    # Location analysis
    loc_df = pd.DataFrame({"CP": cp_loc_series, "PP": pp_loc_series}).fillna(0)
    loc_df["Growth"] = calc_growth_pct(loc_df["CP"], loc_df["PP"], fill_value=np.nan)
    loc_df["Delta"] = loc_df["CP"] - loc_df["PP"]
    valid_locs = loc_df[loc_df["PP"] > 10000]
    
    best_loc = valid_locs["Growth"].idxmax() if not valid_locs.empty else "—"
    best_growth = valid_locs["Growth"].max() if not valid_locs.empty else 0
    worst_loc = valid_locs["Growth"].idxmin() if not valid_locs.empty else "—"
    worst_growth = valid_locs["Growth"].min() if not valid_locs.empty else 0
    n_growing = int((valid_locs["Growth"] > 0).sum())
    n_total = len(valid_locs)
    
    # Service type analysis
    svc_df = pd.DataFrame({"CP": cp_svc_series, "PP": pp_svc_series}).fillna(0)
    svc_df["Delta"] = svc_df["CP"] - svc_df["PP"]
    top_svc_driver = svc_df["Delta"].idxmax() if not svc_df.empty else "—"
    
    # Negative labour alerts
    adv_cp = cp.groupby([ADV_COL, "Location Name", "Service Type"], as_index=False)[val_col].sum()
    adv_pp = pp.groupby([ADV_COL, "Location Name", "Service Type"], as_index=False)[val_col].sum()
    neg_advs = adv_cp[adv_cp[val_col] < 0].copy()
    neg_count = len(neg_advs)
    
    # Service driver helper (uses O(1) multi-index lookup)
    def get_svc_driver(loc):
        if loc == "—": return "—"
        if loc in loc_svc_cp.index.get_level_values("Location Name"):
            c = loc_svc_cp.xs(loc, level="Location Name")
            p = loc_svc_pp.xs(loc, level="Location Name") if loc in loc_svc_pp.index.get_level_values("Location Name") else pd.Series(dtype=float)
            sdf = pd.DataFrame({"CP": c, "PP": p}).fillna(0)
            sdf["Delta"] = sdf["CP"] - sdf["PP"]
            return sdf["Delta"].idxmax() if not sdf.empty else "volume"
        return "volume"
    
    best_driver = get_svc_driver(best_loc)
    worst_driver = get_svc_driver(worst_loc)
    
    # Pivot tables for performance in charts and tables
    # Location x Month Pivot
    cp_loc_month_piv = cp.pivot_table(index="Location Name", columns="Month Name", values=val_col, aggfunc="sum", fill_value=0)
    pp_loc_month_piv = pp.pivot_table(index="Location Name", columns="Month Name", values=val_col, aggfunc="sum", fill_value=0)
    
    # Month sum pivot
    cp_month_sum = cp.groupby("Month Name")[val_col].sum()
    pp_month_sum = pp.groupby("Month Name")[val_col].sum()
    
    # 6-month average for opportunity quantification
    loc_6m_avg = df.groupby("Location Name")[val_col].sum() / max(df["Month Name"].nunique(), 1)
    
    return {
        "cp_val": cp_val, "pp_val": pp_val, "growth_pct": growth_pct, "abs_growth": abs_growth,
        "cp_rpc": cp_rpc, "pp_rpc": pp_rpc, "rpc_growth": rpc_growth,
        "loc_df": loc_df, "valid_locs": valid_locs,
        "best_loc": best_loc, "best_growth": best_growth, "best_driver": best_driver,
        "worst_loc": worst_loc, "worst_growth": worst_growth, "worst_driver": worst_driver,
        "n_growing": n_growing, "n_total": n_total,
        "svc_df": svc_df, "top_svc_driver": top_svc_driver,
        "neg_advs": neg_advs, "neg_count": neg_count,
        "adv_pp": adv_pp, "loc_6m_avg": loc_6m_avg,
        "loc_svc_cp": loc_svc_cp, "loc_svc_pp": loc_svc_pp,
        "cp_loc_month_piv": cp_loc_month_piv, "pp_loc_month_piv": pp_loc_month_piv,
        "cp_month_sum": cp_month_sum, "pp_month_sum": pp_month_sum
    }


def _render_control_bar(df, active_pairs, comparison_mode):
    """Render Section A - Control Bar."""
    mode_str = "YoY" if comparison_mode else "MoM"
    cp_months_active = [p[0] for p in active_pairs]
    pp_months_active = [p[1] for p in active_pairs]
    
    if comparison_mode:
        cp_label = f"{cp_months_active[0]} to {cp_months_active[-1]}" if len(cp_months_active) > 1 else (cp_months_active[0] if cp_months_active else "—")
        pp_label = f"{pp_months_active[0]} to {pp_months_active[-1]}" if len(pp_months_active) > 1 else (pp_months_active[0] if pp_months_active else "—")
        period_text = f"{cp_label} vs {pp_label} (YoY)"
    else:
        period_text = f"{cp_months_active[0] if cp_months_active else '—'} to {cp_months_active[-1] if cp_months_active else '—'} vs prior months (MoM)"
    
    col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([2, 2, 4, 2])
    
    with col_ctrl1:
        st.markdown(f'<div class="period-badge">{period_text}</div>', unsafe_allow_html=True)
    
    with col_ctrl2:
        ws_bs_options = ["All", "MP", "PB"]
        current_ws_bs = st.session_state.get("filter_mp_pb", "All")
        if hasattr(st, "segmented_control"):
            new_ws_bs = st.segmented_control("Unit", ws_bs_options,
                default=current_ws_bs, label_visibility="collapsed",
                key="ctrl_ws_bs")
        else:
            new_ws_bs = st.radio("Unit", ws_bs_options, horizontal=True,
                index=ws_bs_options.index(current_ws_bs),
                label_visibility="collapsed", key="ctrl_ws_bs")
        if new_ws_bs != current_ws_bs:
            st.session_state["filter_mp_pb"] = new_ws_bs
            st.rerun()
    
    with col_ctrl3:
        all_svc_types = sorted(df["Service Type"].dropna().unique().tolist())
        current_svc = st.session_state.get("filter_svc_type", [])
        new_svc = st.multiselect("Service Types", all_svc_types,
            default=current_svc if current_svc else all_svc_types,
            label_visibility="collapsed", key="ctrl_svc",
            placeholder="All service types")
        active_svc = [] if set(new_svc) == set(all_svc_types) else new_svc
        if active_svc != current_svc:
            st.session_state["filter_svc_type"] = active_svc
            st.rerun()
    
    with col_ctrl4:
        # Mode toggle - read-only display since it's controlled by app.py
        mode_display = "YoY" if comparison_mode else "MoM"
        st.markdown(f'<div class="period-badge" style="background:#F5F5F7;color:#6E6E73;border-color:#E5E5EA">{mode_display}</div>', unsafe_allow_html=True)


def _render_ai_narrative(data, mode_str):
    """Render Section B - AI Narrative Band."""
    narrative_payload = {
        "mode": mode_str,
        "cp_total_inr": fmt_inr(data["cp_val"]),
        "growth_pct": round(data["growth_pct"], 2),
        "best_loc": data["best_loc"],
        "best_growth_pct": round(data["best_growth"], 2),
        "best_driver": data["best_driver"],
        "worst_loc": data["worst_loc"],
        "worst_growth_pct": round(data["worst_growth"], 2),
        "worst_driver": data["worst_driver"],
        "n_growing": data["n_growing"],
        "n_total": data["n_total"],
        "neg_count": data["neg_count"],
        "top_svc_driver": data["top_svc_driver"],
        "abs_growth_inr": fmt_inr(data["abs_growth"])
    }
    
    with st.spinner("Generating executive summary..."):
        narrative_text = get_narrative(narrative_payload)
    
    st.markdown(f'<div class="ai-band">🤖 {narrative_text}</div>', unsafe_allow_html=True)


def _render_kpi_tier_1(data, mode_str):
    """Render Section C - KPI Tier 1."""
    c1, c2, c3, c4 = st.columns(4)
    
    def kpi_card(col, label, value_str, delta_pct, what, why, so_what, delta_is_positive=True):
        delta_class = "kpi-delta-pos" if delta_is_positive else "kpi-delta-neg"
        delta_sign = "+" if delta_is_positive and delta_pct > 0 else ""
        delta_str = f"{delta_sign}{delta_pct:.2f}%" if delta_pct != 0 else ""
        with col:
            st.markdown(f'''<div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value_str}</div>
                <div class="{delta_class}">{delta_str}</div>
            </div>''', unsafe_allow_html=True)
            if hasattr(st, "popover"):
                with st.popover("What · Why · So What"):
                    st.markdown(f"**What:** {what}")
                    st.markdown(f"**Why:** {why}")
                    st.markdown(f"**So What:** {so_what}")
    
    kpi_card(c1, f"CP Labour Revenue ({mode_str})",
        fmt_inr(data["cp_val"]), data["growth_pct"],
        what=f"Total net labour billed in the selected period: {fmt_inr(data['cp_val'])}.",
        why=f"Top contributor: {data['best_loc']} ({fmt_pct(data['best_growth'], True)}). Service driver: {data['best_driver']}.",
        so_what=f"{'Above' if data['growth_pct'] > 0 else 'Below'} prior period by {fmt_inr(abs(data['abs_growth']))}. {'Sustain momentum.' if data['growth_pct'] > 0 else 'Immediate review required.'}",
        delta_is_positive=data["growth_pct"] >= 0)
    
    kpi_card(c2, f"PP Labour Revenue ({mode_str})",
        fmt_inr(data["pp_val"]), 0,
        what=f"Net labour revenue for the matched prior period: {fmt_inr(data['pp_val'])}.",
        why=f"Comparison basis: {'same months prior year' if mode_str == 'YoY' else 'immediately preceding months'}.",
        so_what=f"Gap to close: {fmt_inr(abs(data['abs_growth']))} {'advantage' if data['abs_growth'] > 0 else 'deficit'}.",
        delta_is_positive=True)
    
    kpi_card(c3, "Absolute Growth",
        (f"+{fmt_inr(data['abs_growth'])}" if data['abs_growth'] >= 0 else f"–{fmt_inr(abs(data['abs_growth']))}"),
        data["growth_pct"],
        what=f"Net change in labour revenue: {fmt_inr(data['abs_growth'])} {'increase' if data['abs_growth'] >= 0 else 'decline'}.",
        why=f"Top 2 location drivers: {data['best_loc']} (+{fmt_inr(data['loc_df'].loc[data['best_loc'],'Delta'] if data['best_loc'] in data['loc_df'].index else 0)}) and {data['worst_loc']} ({fmt_inr(data['loc_df'].loc[data['worst_loc'],'Delta'] if data['worst_loc'] in data['loc_df'].index else 0)}).",
        so_what=f"{'Portfolio is net positive. Monitor declining outliers.' if data['abs_growth'] >= 0 else 'Portfolio is net negative. Escalate to GM Service.'}",
        delta_is_positive=data["abs_growth"] >= 0)
    
    kpi_card(c4, "Revenue per Jobcard",
        fmt_inr(data["cp_rpc"]), data["rpc_growth"],
        what=f"Average labour realised per jobcard: {fmt_inr(data['cp_rpc'])}.",
        why=f"{'Mix shift toward higher-value services ('+data['top_svc_driver']+').' if data['rpc_growth'] >= 0 else 'Mix shift toward lower-value services. '+data['top_svc_driver']+' volume increased.'}",
        so_what=f"{'Realisation quality improving.' if data['rpc_growth'] >= 0 else 'Push PMP and BR attach rates to improve realisation.'}",
        delta_is_positive=data["rpc_growth"] >= 0)


def _render_kpi_tier_2(data):
    """Render Section D - KPI Tier 2."""
    d1, d2, d3, d4 = st.columns(4)
    
    with d1:
        badge = "badge-pos" if data["best_growth"] > 0 else "badge-neg"
        st.markdown(f'''<div class="kpi-card">
            <div class="kpi-label">Best Location</div>
            <div class="kpi-value">{data["best_loc"]}</div>
            <div class="{badge}">{fmt_pct(data["best_growth"], True)}</div>
            <div class="kpi-meta">{data["best_driver"]}</div>
        </div>''', unsafe_allow_html=True)
        if st.button(f"Filter to {data['best_loc']}", key="btn_best_loc", use_container_width=True):
            st.session_state["labour_click_loc"] = data["best_loc"]
            st.rerun()
    
    with d2:
        badge = "badge-neg" if data["worst_growth"] < 0 else "badge-pos"
        st.markdown(f'''<div class="kpi-card">
            <div class="kpi-label">Worst Location</div>
            <div class="kpi-value">{data["worst_loc"]}</div>
            <div class="{badge}">{fmt_pct(data["worst_growth"], True)}</div>
            <div class="kpi-meta">{data["worst_driver"]}</div>
        </div>''', unsafe_allow_html=True)
        if st.button(f"Filter to {data['worst_loc']}", key="btn_worst_loc", use_container_width=True):
            st.session_state["labour_click_loc"] = data["worst_loc"]
            st.rerun()
    
    with d3:
        health_pct = calc_ratio(data["n_growing"], data["n_total"], multiplier=100, fill_value=0)
        h_badge = "badge-pos" if health_pct >= 60 else ("badge-warn" if health_pct >= 40 else "badge-neg")
        st.markdown(f'''<div class="kpi-card">
            <div class="kpi-label">Locations Growing</div>
            <div class="kpi-value">{data["n_growing"]} / {data["n_total"]}</div>
            <div class="{h_badge}">{health_pct:.0f}% healthy</div>
        </div>''', unsafe_allow_html=True)
    
    with d4:
        n_badge = "badge-neg" if data["neg_count"] > 0 else "badge-pos"
        n_text = f"{data['neg_count']} advisors" if data["neg_count"] > 0 else "None"
        st.markdown(f'''<div class="kpi-card" style="{'border-left: 3px solid #FF3B30;' if data['neg_count'] > 0 else ''}">
            <div class="kpi-label">⚠ Neg Labour Alerts</div>
            <div class="kpi-value">{n_text}</div>
            <div class="{n_badge}">{'Action required' if data['neg_count'] > 0 else 'All clear'}</div>
        </div>''', unsafe_allow_html=True)


def _render_alert_banner(data):
    """Render Section E - Alert Banner."""
    val_col = "Net_Labour"
    neg_advs = data["neg_advs"]
    adv_pp = data["adv_pp"]
    neg_count = data["neg_count"]
    
    if neg_count > 0:
        with st.expander(f"⚠ {neg_count} Negative Labour Alert(s) — Action Required", expanded=False):
            alert_rows = []
            for _, row in neg_advs.iterrows():
                adv = row[ADV_COL]; loc = row["Location Name"]; svc = row["Service Type"]
                cv = row[val_col]
                # lookup in precomputed adv_pp
                pv = adv_pp[(adv_pp[ADV_COL]==adv) & (adv_pp["Location Name"]==loc) & (adv_pp["Service Type"]==svc)][val_col].sum()
                alert_rows.append({
                    "Advisor": adv, "Location": loc, "Service Type": svc,
                    "Current Labour": cv, "Expected Labour": pv, "Variance": cv - pv,
                    "Diagnosis": f"Credits/discounts exceeded gross generation by {fmt_inr(abs(cv - pv))}. Review open jobcards at {loc}."
                })
            alert_df = pd.DataFrame(alert_rows)
            st.dataframe(alert_df, column_config={
                "Current Labour": st.column_config.NumberColumn("Current", format="₹%.0f"),
                "Expected Labour": st.column_config.NumberColumn("Expected", format="₹%.0f"),
                "Variance": st.column_config.NumberColumn("Variance", format="₹%.0f"),
            }, use_container_width=True, hide_index=True)
    else:
        st.success("No negative labour detected for the selected period and filters.")


def _render_charts(data, active_pairs, mode_str):
    """Render Section F - Charts (F1, F2, F3)."""
    # F1: Revenue Trend Chart
    f1_months = [p[0] for p in active_pairs]
    f1_cp_vals = [data["cp_month_sum"].get(m, 0) for m in f1_months]
    f1_pp_vals = [data["pp_month_sum"].get(p[1], 0) for p in active_pairs]
    f1_growth = [calc_growth_pct(c, p, fill_value=0) for c, p in zip(f1_cp_vals, f1_pp_vals)]
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(name=f"CP ({mode_str})", x=f1_months, y=f1_cp_vals,
        marker_color=C["primary"], text=[fmt_inr_short(v) for v in f1_cp_vals],
        textposition="outside", customdata=list(zip(f1_months, f1_cp_vals, f1_pp_vals, f1_growth)),
        hovertemplate="<b>%{customdata[0]}</b><br>CP: ₹%{customdata[1]:,.0f}<br>PP: ₹%{customdata[2]:,.0f}<br>Growth: %{customdata[3]:.1f}%<extra></extra>"))
    fig_trend.add_trace(go.Bar(name="PP", x=f1_months, y=f1_pp_vals,
        marker_color=C["gray"], opacity=0.7, text=[fmt_inr_short(v) for v in f1_pp_vals],
        textposition="outside"))
    fig_trend.add_trace(go.Scatter(name="Growth %", x=f1_months, y=f1_growth,
        mode="lines+markers+text", yaxis="y2", line=dict(color=C["orange"], width=2),
        text=[f"{g:+.1f}%" for g in f1_growth], textposition="top center",
        marker=dict(size=8, color=[C["green"] if g >= 0 else C["red"] for g in f1_growth])))
    fig_trend.update_layout(**get_ply_layout(
        barmode="group", height=300,
        title=dict(text=f"Revenue Trend — {mode_str}", **PLY_TITLE),
        yaxis=dict(**PLY["yaxis"], title="Revenue (₹)"),
        yaxis2=dict(title="Growth %", overlaying="y", side="right",
            tickformat=".1f", showgrid=False)
    ))
    
    event_trend = st.plotly_chart(fig_trend, use_container_width=True,
        on_select="rerun", selection_mode="points", key="chart_trend")
    if event_trend and event_trend.selection and event_trend.selection.points:
        clicked_month = event_trend.selection.points[0].get("x")
        if clicked_month and clicked_month != st.session_state.get("labour_click_month"):
            st.session_state["labour_click_month"] = clicked_month
            st.rerun()
    
    # F2: Location Heatmap
    heat_months = [p[0] for p in active_pairs]
    heat_locs = sorted(set(data["cp_loc_month_piv"].index) | set(data["pp_loc_month_piv"].index))
    heat_z = []
    heat_text = []
    for loc in heat_locs:
        row_z = []; row_t = []
        for cm, pm, _ in active_pairs:
            cv = data["cp_loc_month_piv"].loc[loc, cm] if loc in data["cp_loc_month_piv"].index and cm in data["cp_loc_month_piv"].columns else 0
            pv = data["pp_loc_month_piv"].loc[loc, pm] if loc in data["pp_loc_month_piv"].index and pm in data["pp_loc_month_piv"].columns else 0
            g = calc_growth_pct(cv, pv, fill_value=np.nan)
            row_z.append(g)
            row_t.append(f"{g:+.1f}" if not np.isnan(g) else "—")
        heat_z.append(row_z); heat_text.append(row_t)
    
    heatmap_height = max(320, len(heat_locs) * 28 + 60)
    fig_heat = go.Figure(go.Heatmap(
        z=heat_z, x=heat_months, y=heat_locs,
        colorscale=[[0, "#FF3B30"], [0.5, "#FFFFFF"], [1, "#34C759"]],
        zmid=0, zmin=-30, zmax=30,
        text=heat_text, texttemplate="%{text}%", textfont=dict(size=10),
        hovertemplate="<b>%{y}</b> — %{x}<br>Growth: %{text}%<extra></extra>"
    ))
    fig_heat.update_layout(**get_ply_layout(
        height=heatmap_height,
        title=dict(text=f"Location Growth Heatmap — {mode_str}", **PLY_TITLE),
        xaxis=dict(**PLY["xaxis"], side="top")
    ))
    
    event_heat = st.plotly_chart(fig_heat, use_container_width=True,
        on_select="rerun", selection_mode="points", key="chart_heat")
    if event_heat and event_heat.selection and event_heat.selection.points:
        pt = event_heat.selection.points[0]
        clicked_loc = pt.get("y"); clicked_m = pt.get("x")
        changed = False
        if clicked_loc and clicked_loc != st.session_state.get("labour_click_loc"):
            st.session_state["labour_click_loc"] = clicked_loc; changed = True
        if clicked_m and clicked_m != st.session_state.get("labour_click_month"):
            st.session_state["labour_click_month"] = clicked_m; changed = True
        if changed: st.rerun()
    
    # F3: Service Type Mix
    all_svc = sorted(data["svc_df"].index)
    svc_colors = {"PMP": C["primary"], "RR": C["green"], "Accessories": C["orange"],
                  "BR": C["purple"], "Bodyshop Repair": C["purple"]}
    
    fig_svc = go.Figure()
    for svc in all_svc:
        cp_svc_val = data["svc_df"].loc[svc, "CP"]
        pp_svc_val = data["svc_df"].loc[svc, "PP"]
        clr = svc_colors.get(svc, C["gray"])
        fig_svc.add_trace(go.Bar(name=svc, x=["CP", "PP"], y=[cp_svc_val, pp_svc_val],
            marker_color=clr, text=[fmt_inr_short(cp_svc_val), fmt_inr_short(pp_svc_val)],
            textposition="inside",
            customdata=[[svc, cp_svc_val, pp_svc_val, calc_growth_pct(cp_svc_val, pp_svc_val, 0)],
                        [svc, cp_svc_val, pp_svc_val, calc_growth_pct(cp_svc_val, pp_svc_val, 0)]],
            hovertemplate="<b>%{customdata[0]}</b><br>%{x}: ₹%{y:,.0f}<br>Growth: %{customdata[3]:.1f}%<extra></extra>"))
    fig_svc.update_layout(**get_ply_layout(
        barmode="stack", height=300,
        title=dict(text=f"Service Type Mix — {mode_str}", **PLY_TITLE)
    ))
    
    event_svc = st.plotly_chart(fig_svc, use_container_width=True,
        on_select="rerun", selection_mode="points", key="chart_svc")
    if event_svc and event_svc.selection and event_svc.selection.points:
        pt = event_svc.selection.points[0]
        svc_idx = pt.get("curve_number", 0)
        if svc_idx < len(all_svc):
            clicked_svc = all_svc[svc_idx]
            new_svc_filter = [clicked_svc]
            if new_svc_filter != st.session_state.get("filter_svc_type", []):
                st.session_state["filter_svc_type"] = new_svc_filter
                st.rerun()


def _render_waterfall_charts(data, mode_str):
    """Render Section G - Waterfall Charts."""
    g1, g2 = st.columns(2)
    
    with g1:
        sorted_locs_wf = sorted(data["loc_df"].index, key=lambda l: data["loc_df"].loc[l, "Delta"], reverse=True)
        wf_x = ["PP Total"] + sorted_locs_wf + ["CP Total"]
        wf_y = [data["pp_val"]] + [data["loc_df"].loc[l, "Delta"] for l in sorted_locs_wf] + [data["cp_val"]]
        wf_measures = ["absolute"] + ["relative"] * len(sorted_locs_wf) + ["total"]
        wf_text = [fmt_inr_short(data["pp_val"])] + \
                  [f"{'+' if v >= 0 else ''}{fmt_inr_short(v)}" for v in [data["loc_df"].loc[l,'Delta'] for l in sorted_locs_wf]] + \
                  [fmt_inr_short(data["cp_val"])]
        
        fig_wf_loc = go.Figure(go.Waterfall(
            name="Location Bridge", orientation="v",
            measure=wf_measures, x=wf_x, y=wf_y, text=wf_text,
            textposition="outside",
            increasing={"marker": {"color": C["green"]}},
            decreasing={"marker": {"color": C["red"]}},
            totals={"marker": {"color": C["primary"]}},
            connector={"line": {"color": "#E5E5EA", "width": 1}}
        ))
        fig_wf_loc.update_layout(**get_ply_layout(
            height=360,
            title=dict(text=f"Location Bridge — {mode_str}", **PLY_TITLE)
        ))
        
        event_wf_loc = st.plotly_chart(fig_wf_loc, use_container_width=True,
            on_select="rerun", selection_mode="points", key="chart_wf_loc")
        if event_wf_loc and event_wf_loc.selection and event_wf_loc.selection.points:
            pt = event_wf_loc.selection.points[0]
            loc_clicked = pt.get("x")
            if loc_clicked and loc_clicked not in ["PP Total", "CP Total"]:
                if loc_clicked != st.session_state.get("labour_click_loc"):
                    st.session_state["labour_click_loc"] = loc_clicked
                    st.rerun()
    
    with g2:
        sorted_svc_wf = sorted(data["svc_df"].index, key=lambda s: data["svc_df"].loc[s, "Delta"], reverse=True)
        wf2_x = ["PP Total"] + sorted_svc_wf + ["CP Total"]
        wf2_y = [data["pp_val"]] + [data["svc_df"].loc[s, "Delta"] for s in sorted_svc_wf] + [data["cp_val"]]
        wf2_measures = ["absolute"] + ["relative"] * len(sorted_svc_wf) + ["total"]
        wf2_text = [fmt_inr_short(data["pp_val"])] + \
                   [f"{'+' if v >= 0 else ''}{fmt_inr_short(v)}" for v in [data["svc_df"].loc[s,'Delta'] for s in sorted_svc_wf]] + \
                   [fmt_inr_short(data["cp_val"])]
        
        fig_wf_svc = go.Figure(go.Waterfall(
            name="Service Bridge", orientation="v",
            measure=wf2_measures, x=wf2_x, y=wf2_y, text=wf2_text,
            textposition="outside",
            increasing={"marker": {"color": C["green"]}},
            decreasing={"marker": {"color": C["red"]}},
            totals={"marker": {"color": C["primary"]}},
            connector={"line": {"color": "#E5E5EA", "width": 1}}
        ))
        fig_wf_svc.update_layout(**get_ply_layout(
            height=360,
            title=dict(text=f"Service Type Bridge — {mode_str}", **PLY_TITLE)
        ))
        
        event_wf_svc = st.plotly_chart(fig_wf_svc, use_container_width=True,
            on_select="rerun", selection_mode="points", key="chart_wf_svc")
        if event_wf_svc and event_wf_svc.selection and event_wf_svc.selection.points:
            pt = event_wf_svc.selection.points[0]
            svc_clicked = pt.get("x")
            if svc_clicked and svc_clicked not in ["PP Total", "CP Total"]:
                new_svc = [svc_clicked]
                if new_svc != st.session_state.get("filter_svc_type", []):
                    st.session_state["filter_svc_type"] = new_svc
                    st.rerun()


def _render_drill_down_panel(data):
    """Render Section H - Drill-Down Panel."""
    val_col = "Net_Labour"
    drill_loc = st.session_state.get("labour_click_loc")
    drill_svc = st.session_state.get("filter_svc_type", [])
    
    svc_colors = {"PMP": C["primary"], "RR": C["green"], "Accessories": C["orange"],
                  "BR": C["purple"], "Bodyshop Repair": C["purple"]}
    
    if drill_loc or drill_svc:
        st.markdown("---")
        st.markdown(f'<div class="section-title">🔍 Drill-Down Analysis</div>', unsafe_allow_html=True)
        h1, h2 = st.columns(2)
        
        if drill_loc:
            with h1:
                st.markdown(f"**{drill_loc} — by Service Type**")
                loc_cp_svc = data["loc_svc_cp"].xs(drill_loc, level="Location Name") if drill_loc in data["loc_svc_cp"].index.get_level_values("Location Name") else pd.Series(dtype=float)
                loc_pp_svc = data["loc_svc_pp"].xs(drill_loc, level="Location Name") if drill_loc in data["loc_svc_pp"].index.get_level_values("Location Name") else pd.Series(dtype=float)
                drill_svc_df = pd.DataFrame({"CP": loc_cp_svc, "PP": loc_pp_svc}).fillna(0)
                fig_drill_loc = go.Figure()
                for svc_type in drill_svc_df.index:
                    fig_drill_loc.add_trace(go.Bar(
                        name=svc_type, x=["CP", "PP"],
                        y=[drill_svc_df.loc[svc_type,"CP"], drill_svc_df.loc[svc_type,"PP"]],
                        marker_color=svc_colors.get(svc_type, C["gray"])))
                fig_drill_loc.update_layout(**get_ply_layout(
                    barmode="stack", height=240,
                    title=dict(text=f"{drill_loc} Service Breakdown", **PLY_TITLE)
                ))
                st.plotly_chart(fig_drill_loc, use_container_width=True, key="drill_loc_chart")
        
        if drill_svc:
            with h2:
                active_svc_name = drill_svc[0] if len(drill_svc) == 1 else ", ".join(drill_svc)
                st.markdown(f"**{active_svc_name} — by Location**")
                svc_cp_loc = data["loc_svc_cp"].xs(drill_svc[0], level="Service Type") if len(drill_svc) == 1 and drill_svc[0] in data["loc_svc_cp"].index.get_level_values("Service Type") else data["loc_df"]["CP"]
                svc_pp_loc = data["loc_svc_pp"].xs(drill_svc[0], level="Service Type") if len(drill_svc) == 1 and drill_svc[0] in data["loc_svc_pp"].index.get_level_values("Service Type") else data["loc_df"]["PP"]
                drill_loc_df = pd.DataFrame({"CP": svc_cp_loc, "PP": svc_pp_loc}).fillna(0).sort_values("CP", ascending=False)
                fig_drill_svc = go.Figure()
                fig_drill_svc.add_trace(go.Bar(name="CP", x=drill_loc_df.index.tolist(),
                    y=drill_loc_df["CP"].tolist(), marker_color=C["primary"]))
                fig_drill_svc.add_trace(go.Bar(name="PP", x=drill_loc_df.index.tolist(),
                    y=drill_loc_df["PP"].tolist(), marker_color=C["gray"], opacity=0.7))
                fig_drill_svc.update_layout(**get_ply_layout(
                    barmode="group", height=240,
                    title=dict(text=f"{active_svc_name} by Location", **PLY_TITLE)
                ))
                st.plotly_chart(fig_drill_svc, use_container_width=True, key="drill_svc_chart")
        
        if st.button("✕ Clear drill-down filters", key="clear_drill"):
            st.session_state["labour_click_loc"] = None
            st.session_state["labour_click_month"] = None
            st.session_state["filter_svc_type"] = []
            st.rerun()


def _render_executive_table(data, active_pairs, mode_str):
    """Render Section I - Executive Comparison Table."""
    click_loc = st.session_state.get("labour_click_loc")
    click_month = st.session_state.get("labour_click_month")
    
    st.markdown("---")
    st.markdown(f'<div class="section-title">📊 Executive Comparison Table — {mode_str}</div>', unsafe_allow_html=True)
    
    active_filter_parts = []
    if click_loc: active_filter_parts.append(f"📍 {click_loc}")
    if click_month: active_filter_parts.append(f"📅 {click_month}")
    if st.session_state.get("filter_svc_type", []): active_filter_parts.append(f"🔧 {', '.join(st.session_state['filter_svc_type'])}")
    
    if active_filter_parts:
        chips_html = " ".join([f'<span class="filter-chip">{p}</span>' for p in active_filter_parts])
        st.markdown(f'<div class="filter-chips-bar">{chips_html} <a href="#" onclick="return false;" style="font-size:11px;margin-left:8px;color:#FF3B30">✕ Clear</a></div>', unsafe_allow_html=True)
    
    table_locs = sorted(set(data["cp_loc_month_piv"].index) | set(data["pp_loc_month_piv"].index))
    table_data = []
    for loc in table_locs:
        row = {"Location": loc}
        sparkline_data = []
        loc_cp_total = data["loc_df"].loc[loc, "CP"] if loc in data["loc_df"].index else 0
        loc_pp_total = data["loc_df"].loc[loc, "PP"] if loc in data["loc_df"].index else 0
        
        for cm, pm, _ in active_pairs:
            cv = data["cp_loc_month_piv"].loc[loc, cm] if loc in data["cp_loc_month_piv"].index and cm in data["cp_loc_month_piv"].columns else 0
            pv = data["pp_loc_month_piv"].loc[loc, pm] if loc in data["pp_loc_month_piv"].index and pm in data["pp_loc_month_piv"].columns else 0
            row[f"{cm[:3]} Δ%"] = calc_growth_pct(cv, pv, fill_value=np.nan)
            sparkline_data.append(cv)
            
        row["CP Total"] = loc_cp_total
        row["PP Total"] = loc_pp_total
        row[f"Total Δ%"] = calc_growth_pct(loc_cp_total, loc_pp_total, fill_value=np.nan)
        row["Contribution %"] = calc_ratio(loc_cp_total, data["cp_val"], multiplier=100, fill_value=0)
        row["Trend"] = sparkline_data
        table_data.append(row)
    
    tdf = pd.DataFrame(table_data).sort_values("CP Total", ascending=False)
    
    def row_style(row):
        delta = row.get(f"Total Δ%", 0)
        if pd.isna(delta): return [""] * len(row)
        if delta < -5: return ["background-color:#FFEBE9"] * len(row)
        if delta > 15: return ["background-color:#E8F9EE"] * len(row)
        return [""] * len(row)
    
    styled_tdf = tdf.style.apply(row_style, axis=1)
    
    col_config = {
        "Location": st.column_config.TextColumn("Location"),
        "CP Total": st.column_config.NumberColumn("CP Total", format="₹%.0f"),
        "PP Total": st.column_config.NumberColumn("PP Total", format="₹%.0f"),
        "Total Δ%": st.column_config.NumberColumn(f"Total {mode_str}%", format="%.1f%%"),
        "Contribution %": st.column_config.ProgressColumn("Share %", format="%.1f%%", min_value=0, max_value=100),
        "Trend": st.column_config.LineChartColumn("Trend (CP)"),
    }
    for cm, _, _ in active_pairs:
        col_config[f"{cm[:3]} Δ%"] = st.column_config.NumberColumn(f"{cm[:3]} {mode_str}%", format="%.1f%%")
    
    st.dataframe(styled_tdf, column_config=col_config, use_container_width=True, hide_index=True)


def _render_opportunity_actions(data, mode_str):
    """Render Section J - Opportunity & Action Panel."""
    declining_locs = data["valid_locs"][data["valid_locs"]["Growth"] < 0].sort_values("Growth").head(3)
    opportunities_data = []
    for loc in declining_locs.index:
        avg_6m = data["loc_6m_avg"].get(loc, data["loc_df"].loc[loc, "CP"] if loc in data["loc_df"].index else 0)
        gap = avg_6m - data["loc_df"].loc[loc, "CP"] if loc in data["loc_df"].index else 0
        opportunities_data.append({"location": loc, "gap_inr": fmt_inr(max(gap, 0)),
            "current_growth": round(data["loc_df"].loc[loc, "Growth"], 2) if loc in data["loc_df"].index else 0})
    
    actions_payload = {
        "mode": mode_str,
        "worst_loc": data["worst_loc"], "worst_growth": round(data["worst_growth"], 2),
        "worst_driver": data["worst_driver"],
        "best_loc": data["best_loc"], "best_growth": round(data["best_growth"], 2),
        "neg_count": data["neg_count"],
        "neg_locations": data["neg_advs"]["Location Name"].unique().tolist() if data["neg_count"] > 0 else [],
        "top_svc_driver": data["top_svc_driver"],
        "rpc_growth": round(data["rpc_growth"], 2),
        "declining_locs": opportunities_data,
    }
    
    with st.spinner("Generating recommendations..."):
        actions_text = get_actions(actions_payload)
    
    opps = re.findall(r'O\d+:\s*(.+?)(?=\s*[OA]\d+:|$)', actions_text, re.DOTALL)
    acts = re.findall(r'A\d+:\s*(.+?)(?=\s*[OA]\d+:|$)', actions_text, re.DOTALL)
    
    j1, j2 = st.columns(2)
    with j1:
        st.markdown(f'<div class="section-title">💡 Opportunities</div>', unsafe_allow_html=True)
        for i, opp in enumerate(opps[:3], 1):
            st.markdown(f'<div class="insight-card pos"><div class="insight-title">{i}. Opportunity</div><div class="insight-stat">{opp.strip()}</div></div>', unsafe_allow_html=True)
    with j2:
        st.markdown(f'<div class="section-title">🎯 Actions Required</div>', unsafe_allow_html=True)
        for i, act in enumerate(acts[:3], 1):
            st.markdown(f'<div class="insight-card neg"><div class="insight-title">{i}. Action</div><div class="insight-stat">{act.strip()}</div></div>', unsafe_allow_html=True)


def render(df, pairs, comparison_mode=True, selected_months=None):
    """Main render function for Labour Revenue dashboard."""
    _inject_responsive_css()
    
    # Empty state check
    if df.empty:
        from ui.components.core import EmptyState
        EmptyState('No data available for the selected period. Adjust your filters or check data freshness.')
        return
    
    _initialize_cross_filter_state()
    
    # Apply filters globally across ALL components to ensure absolute consistency
    cp, pp = _apply_filters(df, pairs, comparison_mode, selected_months)
    mode_str = "YoY" if comparison_mode else "MoM"
    
    # Pre-compute all grouped and aggregated data in one master step
    # All render functions must consume from this dictionary!
    data = _prepare_view_data(cp, pp, df)
    
    # Render all sections
    _render_control_bar(df, pairs, comparison_mode)
    _render_ai_narrative(data, mode_str)
    _render_kpi_tier_1(data, mode_str)
    _render_kpi_tier_2(data)
    _render_alert_banner(data)
    _render_charts(data, pairs, mode_str)
    _render_waterfall_charts(data, mode_str)
    _render_drill_down_panel(data)
    _render_executive_table(data, pairs, mode_str)
    _render_opportunity_actions(data, mode_str)

