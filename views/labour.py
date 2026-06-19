"""
Labour Revenue — Executive Comparative Dashboard
Multi-Location Mar Dealership  ·  Apple Light-Theme  ·  v2.0
"""
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import re

from utils.calculations.fact_metrics import get_jobcard_count
from utils.filters import filter_valid_advisors
from utils.calculations.common import calc_growth_pct, calc_ratio
from ui.formatters import fmt_inr, fmt_inr_short, fmt_inr_full, fmt_pct, fmt_num
from ui.components.theme import EXECUTIVE_THEME_CSS
from utils.constants import ADV_COL, C, PLY, PLY_TITLE, MONTH_SORT_ORDER, get_ply_layout
from services.ai_service import get_narrative, get_actions
from ui.components.core import EmptyState


DEFAULTS = {
    "lab_business_view": "All",
    "lab_service_types": [],
    "lab_cross_month": None,
    "lab_ai_hash": None,
    "lab_ai_narrative": None,
    "lab_ai_opps": None,
    "lab_ai_opps_hash": None,
}


def _init_state():
    for k, v in DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v


@st.cache_data
def _get_master_lists(client):
    from app import load_data
    from utils.constants import CLIENTS, MONTH_SORT_ORDER
    full_df, _ = load_data(CLIENTS[client])
    return (
        sorted(full_df["Location Name"].dropna().unique().tolist()),
        sorted(full_df["Service Type"].dropna().unique().tolist()),
        sorted(full_df["Month Name"].dropna().unique().tolist(), key=lambda x: MONTH_SORT_ORDER.get(x, 99))
    )


_CSS_INJECTED = False

def _inject_responsive_css():
    global _CSS_INJECTED
    if _CSS_INJECTED:
        return
    _CSS_INJECTED = True
    st.markdown("""<style>
@media (max-width: 1024px) {
    [data-testid="stHorizontalBlock"] > div { min-width: 100% !important; }
}
@media (min-width: 1800px) {
    .kpi-value { font-size: 28px !important; }
    .kpi-label { font-size: 13px !important; }
}
.kpi-card { height: 140px; display: flex; flex-direction: column; justify-content: space-between; }
.lab-summary { font-size: 12px; color: #6E6E73; padding: 2px 0 8px 0; }
</style>""", unsafe_allow_html=True)


def _apply_filters(df, active_pairs):
    filtered = df.copy()
    
    biz = st.session_state.get("lab_business_view", "All")
    if biz == "Workshop":
        filtered = filtered[filtered["Service Type"] != "BR"]
    elif biz == "Bodyshop":
        filtered = filtered[filtered["Service Type"] == "BR"]

    svc_types = st.session_state.get("lab_service_types", [])
    if svc_types:
        filtered = filtered[filtered["Service Type"].isin(svc_types)]


    cp_months_active = [p[0] for p in active_pairs]
    pp_months_active = [p[1] for p in active_pairs]
    click_month = st.session_state.get("lab_cross_month")
    if click_month:
        # Cross filter restricts the data to just that month and its paired prior month
        paired_pm = next((p[1] for p in active_pairs if p[0] == click_month), None)
        cp_months_active = [click_month]
        pp_months_active = [paired_pm] if paired_pm else []

    cp = filtered[filtered["Month Name"].isin(cp_months_active)]
    pp = filtered[filtered["Month Name"].isin(pp_months_active)]
    return cp, pp


def _compute_metrics(cp, pp, df, val_col="Pre-GST Labour"):
    # Business rule: Use Pre-GST Labour as canonical revenue (no discount subtraction)
    cp_loc = cp.groupby("Location Name")[val_col].sum()
    pp_loc = pp.groupby("Location Name")[val_col].sum()
    cp_svc = cp.groupby("Service Type")[val_col].sum()
    pp_svc = pp.groupby("Service Type")[val_col].sum()
    loc_svc_cp = cp.groupby(["Location Name", "Service Type"])[val_col].sum()
    loc_svc_pp = pp.groupby(["Location Name", "Service Type"])[val_col].sum()

    cp_val = cp[val_col].sum()
    pp_val = pp[val_col].sum()
    growth_pct = calc_growth_pct(cp_val, pp_val, fill_value=0)

    cp_jc = get_jobcard_count(cp) if "JC_Nos." in cp.columns else cp[val_col].count()
    pp_jc = get_jobcard_count(pp) if "JC_Nos." in pp.columns else pp[val_col].count()
    
    # Business rule: Avg Labour = Pre-GST Labour / Job Cards (never blank)
    cp_rpc = calc_ratio(cp_val, cp_jc, fill_value=0) if cp_jc > 0 else 0
    pp_rpc = calc_ratio(pp_val, pp_jc, fill_value=0) if pp_jc > 0 else 0
    rpc_growth = calc_growth_pct(cp_rpc, pp_rpc, fill_value=0)

    loc_df = pd.DataFrame({"CP": cp_loc, "PP": pp_loc}).fillna(0)
    loc_df["Growth"] = calc_growth_pct(loc_df["CP"], loc_df["PP"], fill_value=np.nan)
    loc_df["Delta"] = loc_df["CP"] - loc_df["PP"]
    valid_locs = loc_df[loc_df["PP"] > 10000]

    best_loc = valid_locs["Growth"].idxmax() if not valid_locs.empty else "\u2014"
    best_growth = valid_locs["Growth"].max() if not valid_locs.empty else 0
    worst_loc = valid_locs["Growth"].idxmin() if not valid_locs.empty else "\u2014"
    worst_growth = valid_locs["Growth"].min() if not valid_locs.empty else 0
    n_growing = int((valid_locs["Growth"] > 0).sum())
    n_total = len(valid_locs)
    
    declining_locs = []
    if not valid_locs.empty:
        dec_df = valid_locs[valid_locs["Delta"] < 0].sort_values("Delta")
        for loc in dec_df.index:
            declining_locs.append({
                "location": loc,
                "gap_inr": fmt_inr(abs(dec_df.loc[loc, "Delta"]))
            })

    svc_df = pd.DataFrame({"CP": cp_svc, "PP": pp_svc}).fillna(0)
    svc_df["Delta"] = svc_df["CP"] - svc_df["PP"]
    top_svc_driver = svc_df["Delta"].idxmax() if not svc_df.empty else "\u2014"

    def _driver(loc):
        if loc == "\u2014" or loc not in loc_svc_cp.index.get_level_values("Location Name"):
            return "\u2014"
        c = loc_svc_cp.xs(loc, level="Location Name")
        p = (loc_svc_pp.xs(loc, level="Location Name")
             if loc in loc_svc_pp.index.get_level_values("Location Name")
             else pd.Series(dtype=float))
        sdf = pd.DataFrame({"CP": c, "PP": p}).fillna(0)
        sdf["Delta"] = sdf["CP"] - sdf["PP"]
        return sdf["Delta"].idxmax() if not sdf.empty else "volume"

    adv_cp = filter_valid_advisors(cp, ADV_COL).groupby([ADV_COL, "Location Name", "Service Type"],
                        as_index=False)[val_col].sum()
    adv_pp = filter_valid_advisors(pp, ADV_COL).groupby([ADV_COL, "Location Name", "Service Type"],
                        as_index=False)[val_col].sum()
    neg_advs = adv_cp[adv_cp[val_col] < 0].copy()
    neg_count = len(neg_advs)

    cp_loc_piv = cp.pivot_table(index="Location Name", columns="Month Name",
                                values=val_col, aggfunc="sum", fill_value=0)
    pp_loc_piv = pp.pivot_table(index="Location Name", columns="Month Name",
                                values=val_col, aggfunc="sum", fill_value=0)
    cp_month_sum = cp.groupby("Month Name")[val_col].sum()
    pp_month_sum = pp.groupby("Month Name")[val_col].sum()
    loc_6m_avg = df.groupby("Location Name")[val_col].sum() / max(df["Month Name"].nunique(), 1)
    
    # Aggregate actual Job Cards by Location
    cp_loc_jc = cp.groupby("Location Name")["JC_Nos."].sum() if "JC_Nos." in cp.columns else pd.Series(dtype=float)
    pp_loc_jc = pp.groupby("Location Name")["JC_Nos."].sum() if "JC_Nos." in pp.columns else pd.Series(dtype=float)

    active_svc_count = len(cp["Service Type"].dropna().unique())

    is_pms_cp = cp["Service Type"] == "PMS"
    is_pms_pp = pp["Service Type"] == "PMS"
    pms_jobs_cp = get_jobcard_count(cp[is_pms_cp]) if "JC_Nos." in cp.columns else is_pms_cp.sum()
    pms_jobs_pp = get_jobcard_count(pp[is_pms_pp]) if "JC_Nos." in pp.columns else is_pms_pp.sum()
    pms_rev_cp = cp.loc[is_pms_cp, val_col].sum()
    pms_rev_pp = pp.loc[is_pms_pp, val_col].sum()

    is_br_cp = cp["Service Type"] == "BR"
    is_br_pp = pp["Service Type"] == "BR"
    br_jobs_cp = get_jobcard_count(cp[is_br_cp]) if "JC_Nos." in cp.columns else is_br_cp.sum()
    br_jobs_pp = get_jobcard_count(pp[is_br_pp]) if "JC_Nos." in pp.columns else is_br_pp.sum()
    br_rev_cp = cp.loc[is_br_cp, val_col].sum()
    br_rev_pp = pp.loc[is_br_pp, val_col].sum()

    # Business rule: Avg Labour = Pre-GST Labour / Job Cards (never blank)
    pms_stats = {
        "cp_jobs": pms_jobs_cp, "pp_jobs": pms_jobs_pp,
        "cp_rev": pms_rev_cp, "pp_rev": pms_rev_pp,
        "cp_rpc": calc_ratio(pms_rev_cp, pms_jobs_cp) if pms_jobs_cp > 0 else 0,
        "pp_rpc": calc_ratio(pms_rev_pp, pms_jobs_pp) if pms_jobs_pp > 0 else 0,
    }
    br_stats = {
        "cp_jobs": br_jobs_cp, "pp_jobs": br_jobs_pp,
        "cp_rev": br_rev_cp, "pp_rev": br_rev_pp,
        "cp_rpc": calc_ratio(br_rev_cp, br_jobs_cp) if br_jobs_cp > 0 else 0,
        "pp_rpc": calc_ratio(br_rev_pp, br_jobs_pp) if br_jobs_pp > 0 else 0,
    }

    return {
        "cp_val": cp_val, "pp_val": pp_val, "growth_pct": growth_pct,
        "cp_rpc": cp_rpc, "pp_rpc": pp_rpc, "rpc_growth": rpc_growth,
        "cp_jc": cp_jc, "pp_jc": pp_jc,
        "loc_df": loc_df, "valid_locs": valid_locs,
        "best_loc": best_loc, "best_growth": best_growth, "best_driver": _driver(best_loc),
        "worst_loc": worst_loc, "worst_growth": worst_growth, "worst_driver": _driver(worst_loc),
        "n_growing": n_growing, "n_total": n_total,
        "svc_df": svc_df, "top_svc_driver": top_svc_driver,
        "neg_advs": neg_advs, "neg_count": neg_count, "adv_pp": adv_pp,
        "loc_6m_avg": loc_6m_avg,
        "loc_svc_cp": loc_svc_cp, "loc_svc_pp": loc_svc_pp,
        "cp_loc_month_piv": cp_loc_piv, "pp_loc_month_piv": pp_loc_piv,
        "cp_month_sum": cp_month_sum, "pp_month_sum": pp_month_sum,
        "cp_loc_jc": cp_loc_jc, "pp_loc_jc": pp_loc_jc,
        "active_svc_count": active_svc_count,
        "pms_stats": pms_stats, "br_stats": br_stats,
        "declining_locs": declining_locs,
    }


def _prepare_datasets(cp, pp, df):
    biz = st.session_state.get("lab_business_view", "All")

    if biz == "Workshop":
        is_ws = cp["Service Type"] != "BR"
        pp_ws = pp[pp["Service Type"] != "BR"]
        metrics = _compute_metrics(cp[is_ws], pp_ws, df[df["Service Type"] != "BR"])
        return {"combined": metrics, "workshop": metrics, "bodyshop": None}

    elif biz == "Bodyshop":
        is_bs = cp["Service Type"] == "BR"
        pp_bs = pp[pp["Service Type"] == "BR"]
        metrics = _compute_metrics(cp[is_bs], pp_bs, df[df["Service Type"] == "BR"])
        return {"combined": metrics, "workshop": None, "bodyshop": metrics}

    else:
        is_ws = cp["Service Type"] != "BR"
        is_bs = cp["Service Type"] == "BR"
        pp_ws = pp[pp["Service Type"] != "BR"]
        pp_bs = pp[pp["Service Type"] == "BR"]
        return {
            "combined": _compute_metrics(cp, pp, df),
            "workshop": _compute_metrics(cp[is_ws], pp_ws, df[df["Service Type"] != "BR"]),
            "bodyshop": _compute_metrics(cp[is_bs], pp_bs, df[df["Service Type"] == "BR"]),
        }




def _render_cross_filter_bar():
    chips = []
    cross_month = st.session_state.get("lab_cross_month")
    if cross_month:
        chips.append(("\U0001f4c5 " + cross_month, "lab_cross_month"))
    if not chips:
        return
    html = '<div style="display:flex;gap:6px;align-items:center;padding:4px 0 8px 0;flex-wrap:wrap">'
    html += '<span style="font-size:12px;color:#6E6E73;font-weight:600">Filtered by:</span>'
    for label, key in chips:
        html += (f'<span style="background:#E8F0FE;color:#185FA5;border:1px solid #B5D4F4;'
                 f'border-radius:16px;padding:3px 10px;font-size:11px;font-weight:600">'
                 f'{label} \u2715</span>')
    html += (f'<span style="font-size:11px;color:#FF3B30;cursor:pointer;margin-left:4px;'
             f'font-weight:600">Clear all filters</span></div>')
    st.markdown(html, unsafe_allow_html=True)

    for label, key in chips:
        if st.button(label + " \u2715", key=f"chip_{key}", label_visibility="visible"):
            st.session_state[key] = None
            st.rerun()
    if st.button("Clear all filters", key="chip_clear_all", label_visibility="visible"):
        st.session_state.lab_cross_month = None
        st.rerun()


def _render_ai_narrative(datasets, mode_str, cp_label, pp_label):
    d = datasets["combined"]
    ws = datasets["workshop"]
    bs = datasets["bodyshop"]
    biz = st.session_state.get("lab_business_view", "All")
    cross_filters = {}
    if st.session_state.get("lab_cross_month"):
        cross_filters["month"] = st.session_state.lab_cross_month

    payload = {
        "mode": mode_str, "period": f"{cp_label} vs {pp_label}",
        "business_view": biz,
        "cp_total_inr": fmt_inr(d["cp_val"]), "pp_total_inr": fmt_inr(d["pp_val"]),
        "growth_pct": round(d["growth_pct"], 2),
        "best_loc": d["best_loc"], "best_growth_pct": round(d["best_growth"], 2),
        "best_driver": d["best_driver"],
        "worst_loc": d["worst_loc"], "worst_growth_pct": round(d["worst_growth"], 2),
        "worst_driver": d["worst_driver"],
        "n_growing": d["n_growing"], "n_total": d["n_total"],
        "neg_count": d["neg_count"],
        "neg_locations": list(d["neg_advs"]["Location Name"].unique()) if not d["neg_advs"].empty else [],
        "rpc_growth": round(d.get("rpc_g", 0), 2),
        "abs_growth_inr": fmt_inr(d["cp_val"] - d["pp_val"]),
        "top_svc_driver": d["top_svc_driver"],
        "cross_filters": cross_filters,
        "declining_locs": d.get("declining_locs", []),
    }
    if biz == "All":
        payload["workshop_cp"] = fmt_inr(ws["cp_val"])
        payload["workshop_growth"] = round(ws["growth_pct"], 2)
        payload["bodyshop_cp"] = fmt_inr(bs["cp_val"])
        payload["bodyshop_growth"] = round(bs["growth_pct"], 2)
        ws_top = ws["svc_df"]["Delta"].idxmax() if not ws["svc_df"].empty else "\u2014"
        bs_top = bs["svc_df"]["Delta"].idxmax() if not bs["svc_df"].empty else "\u2014"
        payload["workshop_top_svc"] = ws_top
        payload["bodyshop_top_svc"] = bs_top

    content_hash = str(hash(str(sorted(payload.items()))))
    if content_hash != st.session_state.get("lab_ai_hash"):
        with st.spinner("Generating executive summary..."):
            narrative = get_narrative(payload)
        st.session_state.lab_ai_hash = content_hash
        st.session_state.lab_ai_narrative = narrative
    else:
        narrative = st.session_state.lab_ai_narrative

    st.markdown(
        f'<div class="ai-band">\U0001f916 {narrative}</div>',
        unsafe_allow_html=True)


def _render_executive_panel(datasets, mode_str):
    d = datasets["combined"]
    
    rev_cp = fmt_inr_short(d["cp_val"])
    rev_pp = fmt_inr_short(d["pp_val"])
    rev_g = d["growth_pct"]
    
    # Display "—" when Job Cards = 0
    rpc_cp = "—" if d["cp_rpc"] == 0 and d["cp_jc"] == 0 else fmt_inr_short(d["cp_rpc"])
    rpc_pp = "—" if d["pp_rpc"] == 0 and d["pp_jc"] == 0 else fmt_inr_short(d["pp_rpc"])
    rpc_g = d["rpc_growth"]
    
    load_cp = f"{int(d['cp_jc']):,}"
    load_pp = f"{int(d['pp_jc']):,}"
    load_g = calc_growth_pct(d["cp_jc"], d["pp_jc"], fill_value=0)
    
    def _arrow(val):
        if val > 0: return f'<span class="g-pos">▲ {val:.1f}%</span>'
        if val < 0: return f'<span class="g-neg">▼ {abs(val):.1f}%</span>'
        return ""

    def _kpi_card(title, cp_val, pp_val, g_val):
        return f"""<div class="kpi-box">
<div class="kpi-title">{title}</div>
<div class="kpi-val">{cp_val}</div>
<div class="kpi-footer">{_arrow(g_val)} <span class="pp-val">PP {pp_val}</span></div>
</div>"""

    def _svc_row(label, cp_v, pp_v):
        return f"""<div class="svc-row">
<div class="svc-label">{label}</div>
<div class="svc-vals">
<div class="svc-cp">{cp_v} <span class="svc-cp-tag">CP</span></div>
<div class="svc-pp">{pp_v} PP</div>
</div>
</div>"""

    def _svc_panel(title, stats):
        cp_jobs = f"{int(stats['cp_jobs']):,}"
        pp_jobs = f"{int(stats['pp_jobs']):,}"
        # Display "—" when Job Cards = 0
        cp_rpc = "—" if stats["cp_rpc"] == 0 and stats["cp_jobs"] == 0 else fmt_inr_short(stats["cp_rpc"])
        pp_rpc = "—" if stats["pp_rpc"] == 0 and stats["pp_jobs"] == 0 else fmt_inr_short(stats["pp_rpc"])
        cp_rev = fmt_inr_short(stats["cp_rev"])
        pp_rev = fmt_inr_short(stats["pp_rev"])
        
        return f"""<div class="kpi-box svc-panel">
<div class="kpi-val" style="font-size: 16px; margin-bottom: 20px;">{title}</div>
{_svc_row("Jobs", cp_jobs, pp_jobs)}
{_svc_row("Avg labour", cp_rpc, pp_rpc)}
{_svc_row("Revenue", cp_rev, pp_rev)}
</div>"""

    html = f"""{EXECUTIVE_THEME_CSS}
<div class="exec-heading">EXECUTIVE SUMMARY</div>
<div class="kpi-wrapper">
{_kpi_card("LABOUR REVENUE", rev_cp, rev_pp, rev_g)}
{_kpi_card("LOAD", load_cp, load_pp, load_g)}
{_kpi_card("AVG LABOUR", rpc_cp, rpc_pp, rpc_g)}
</div>
<hr style="border:none; border-top:1px solid #36393F; margin: 20px 0 16px 0;">
<div class="exec-heading">PMS & BODYSHOP — CP VS PP</div>
<div class="kpi-wrapper">
{_svc_panel("PMS", d["pms_stats"])}
{_svc_panel("Bodyshop (BR)", d["br_stats"])}
</div>"""
    st.markdown(html, unsafe_allow_html=True)


def _render_neg_labour_audit(data):
    if data["neg_count"] == 0:
        return
    val_col = "Pre-GST Labour"
    with st.expander(
            f"\u26a0 {data['neg_count']} Negative Labour Alert(s) \u2014 Action Required",
            expanded=False):
        rows = []
        for _, row in data["neg_advs"].iterrows():
            adv = row[ADV_COL]; loc = row["Location Name"]; svc = row["Service Type"]
            cv = row[val_col]
            pv = data["adv_pp"][
                (data["adv_pp"][ADV_COL] == adv) &
                (data["adv_pp"]["Location Name"] == loc) &
                (data["adv_pp"]["Service Type"] == svc)
            ][val_col].sum()
            rows.append({
                "Advisor Name": adv, "Location": loc, "Service Type": svc,
                "Labour \u20b9": cv, "Expected \u20b9": pv,
                "Variance \u20b9": cv - pv,
                "Diagnosis": (f"Credits/discounts exceeded gross by "
                              f"{fmt_inr(abs(cv - pv))}. Review open JCs at {loc}.")
            })
        st.dataframe(pd.DataFrame(rows), column_config={
            "Labour \u20b9": st.column_config.NumberColumn(format="\u20b9%.0f"),
            "Expected \u20b9": st.column_config.NumberColumn(format="\u20b9%.0f"),
            "Variance \u20b9": st.column_config.NumberColumn(format="\u20b9%.0f"),
        }, use_container_width=True, hide_index=True)


def _render_charts(datasets, active_pairs, mode_str):
    data = datasets["combined"]
    
    # Revenue Trend - Full width, larger fonts
    months = [p[0] for p in active_pairs]
    cp_vals = [data["cp_month_sum"].get(m, 0) for m in months]
    pp_vals = [data["pp_month_sum"].get(p[1], 0) for p in active_pairs]
    growth = [calc_growth_pct(c, p, fill_value=0) for c, p in zip(cp_vals, pp_vals)]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name=f"CP ({mode_str})", x=months, y=cp_vals,
        marker_color=C["primary"],
        text=[fmt_inr_short(v) for v in cp_vals], textposition="outside",
        textfont=dict(size=14),
        customdata=list(zip(months, cp_vals, pp_vals, growth)),
        hovertemplate=("<b>%{customdata[0]}</b><br>CP: \u20b9%{customdata[1]:,.0f}"
                       "<br>PP: \u20b9%{customdata[2]:,.0f}"
                       "<br>Growth: %{customdata[3]:.1f}%<extra></extra>")))
    fig.add_trace(go.Bar(
        name="PP", x=months, y=pp_vals, marker_color=C["gray"], opacity=0.7,
        text=[fmt_inr_short(v) for v in pp_vals], textposition="outside",
        textfont=dict(size=14)))
    fig.add_trace(go.Scatter(
        name="Growth %", x=months, y=growth,
        mode="lines+markers+text", yaxis="y2",
        line=dict(color=C["orange"], width=3),
        text=[f"{g:+.1f}%" for g in growth], textposition="top center",
        textfont=dict(size=13, color=[C["green"] if g >= 0 else C["red"] for g in growth]),
        marker=dict(size=10, color=[C["green"] if g >= 0 else C["red"] for g in growth])))
    fig.update_layout(**get_ply_layout(
        barmode="group", height=400,
        title=dict(text=f"Revenue Trend \u2014 {mode_str}", font=dict(size=16)),
        yaxis=dict(**PLY["yaxis"], title="Revenue (\u20b9)", title_font=dict(size=14)),
        yaxis2=dict(title="Growth %", overlaying="y", side="right",
                    tickformat=".1f", showgrid=False, title_font=dict(size=14)),
        xaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
        legend=dict(font=dict(size=12))))

    ev = st.plotly_chart(fig, use_container_width=True,
                         on_select="rerun", selection_mode="points",
                         key="chart_trend")
    if ev and ev.selection and ev.selection.points:
        cm = ev.selection.points[0].get("x")
        if cm and cm != st.session_state.get("lab_cross_month"):
            st.session_state.lab_cross_month = cm
            st.rerun()






def _render_executive_table(datasets, active_pairs, mode_str):
    data = datasets["combined"]
    
    st.markdown(
        f'<div class="section-title">\U0001f4ca Executive Location Performance \u2014 {mode_str}</div>',
        unsafe_allow_html=True)
    
    # Build executive table with location performance
    all_locs = sorted(set(data["cp_loc_month_piv"].index) |
                      set(data["pp_loc_month_piv"].index))
    
    rows = []
    for loc in all_locs:
        lcp = data["loc_df"].loc[loc, "CP"] if loc in data["loc_df"].index else 0
        lpp = data["loc_df"].loc[loc, "PP"] if loc in data["loc_df"].index else 0
        growth = data["loc_df"].loc[loc, "Growth"] if loc in data["loc_df"].index else 0
        delta = data["loc_df"].loc[loc, "Delta"] if loc in data["loc_df"].index else 0
        
        # Use actual Job Cards from aggregation
        cp_jc = data["cp_loc_jc"].get(loc, 0) if "cp_loc_jc" in data else 0
        avg_lab = calc_ratio(lcp, cp_jc, fill_value=0) if cp_jc > 0 else 0
        
        rows.append({
            "Location": loc,
            "Labour CP": lcp,
            "Labour PP": lpp,
            "Difference ₹": delta,
            "Growth %": growth,
            "Job Cards": cp_jc,
            "Avg Labour": avg_lab
        })
    
    # Add Total row
    total_cp = data["cp_val"]
    total_pp = data["pp_val"]
    total_delta = total_cp - total_pp
    total_growth = calc_growth_pct(total_cp, total_pp, fill_value=0)
    total_jc = data["cp_jc"]
    total_avg = calc_ratio(total_cp, total_jc, fill_value=0) if total_jc > 0 else 0
    
    rows.append({
        "Location": "TOTAL",
        "Labour CP": total_cp,
        "Labour PP": total_pp,
        "Difference ₹": total_delta,
        "Growth %": total_growth,
        "Job Cards": total_jc,
        "Avg Labour": total_avg
    })
    
    tdf = pd.DataFrame(rows)
    
    # Add Rank column (excluding TOTAL)
    tdf["Rank"] = list(range(1, len(tdf) + 1))
    tdf["Rank"] = tdf["Rank"].astype(object)
    tdf.loc[tdf["Location"] == "TOTAL", "Rank"] = None
    
    # Sort by Growth % descending (excluding TOTAL which stays at bottom)
    total_row = tdf[tdf["Location"] == "TOTAL"].copy()
    loc_rows = tdf[tdf["Location"] != "TOTAL"].sort_values("Growth %", ascending=False)
    tdf = pd.concat([loc_rows, total_row], ignore_index=True)
    
    # Re-rank after sorting
    tdf.loc[tdf["Location"] != "TOTAL", "Rank"] = range(1, len(loc_rows) + 1)
    
    # Basic configuration without formatting overrides
    cc = {
        "Rank": st.column_config.NumberColumn("Rank"),
        "Location": st.column_config.TextColumn("Location"),
        "Labour CP": st.column_config.NumberColumn("Labour CP"),
        "Labour PP": st.column_config.NumberColumn("Labour PP"),
        "Difference ₹": st.column_config.NumberColumn("Difference ₹"),
        "Growth %": st.column_config.NumberColumn("Growth %"),
        "Job Cards": st.column_config.NumberColumn("Job Cards"),
        "Avg Labour": st.column_config.NumberColumn("Avg Labour"),
    }
    
    # Style with Indian formatting and color coding
    def _bold_total(row):
        if row["Location"] == "TOTAL":
            return ["font-weight: 700"] * len(row)
        return [""] * len(row)
        
    def _color_growth(val):
        if pd.isna(val) or val == 0: return ""
        return "color: #10b981;" if val > 0 else "color: #ef4444;"
    
    styled = tdf.style.apply(_bold_total, axis=1)
    
    # Map colors to growth and delta
    styled = styled.map(_color_growth, subset=["Growth %", "Difference ₹"])
    
    # Apply Indian formatting
    styled = styled.format({
        "Labour CP": fmt_inr_full,
        "Labour PP": fmt_inr_full,
        "Difference ₹": fmt_inr_full,
        "Growth %": lambda x: fmt_pct(x, sign=True),
        "Job Cards": fmt_num,
        "Avg Labour": fmt_inr_full,
    })
    
    st.dataframe(styled, column_config=cc, use_container_width=True, hide_index=True)


def _render_monthly_detail(datasets, active_pairs, mode_str):
    data = datasets["combined"]
    
    with st.expander("▶ Monthly Location Performance (Detailed View)", expanded=False):
        st.markdown(
            f'<div class="section-title">\U0001f4ca Monthly Detail \u2014 {mode_str}</div>',
            unsafe_allow_html=True)
        
        all_locs = sorted(set(data["cp_loc_month_piv"].index) |
                          set(data["pp_loc_month_piv"].index))
        t2_rows = []
        for loc in all_locs:
            row = {"Location": loc}
            for cm, pm, _ in active_pairs:
                cv = (data["cp_loc_month_piv"].loc[loc, cm]
                      if loc in data["cp_loc_month_piv"].index
                      and cm in data["cp_loc_month_piv"].columns else 0)
                pv = (data["pp_loc_month_piv"].loc[loc, pm]
                      if loc in data["pp_loc_month_piv"].index
                      and pm in data["pp_loc_month_piv"].columns else 0)
                row[f"{cm[:3]} Lab_CP"] = cv
                row[f"{cm[:3]} Lab_PP"] = pv
                row[f"{cm[:3]} YoY%"] = calc_growth_pct(cv, pv, fill_value=np.nan)
            t2_rows.append(row)

        totals = {"Location": "TOTAL"}
        for cm, pm, _ in active_pairs:
            tcv = sum(r.get(f"{cm[:3]} Lab_CP", 0) for r in t2_rows)
            tpv = sum(r.get(f"{cm[:3]} Lab_PP", 0) for r in t2_rows)
            totals[f"{cm[:3]} Lab_CP"] = tcv
            totals[f"{cm[:3]} Lab_PP"] = tpv
            totals[f"{cm[:3]} YoY%"] = calc_growth_pct(tcv, tpv, fill_value=np.nan)
        t2_rows.append(totals)

        t2df = pd.DataFrame(t2_rows)
        t2cc = {"Location": st.column_config.TextColumn("Location")}
        
        format_dict = {}
        color_subset = []
        for cm, _, _ in active_pairs:
            t2cc[f"{cm[:3]} Lab_CP"] = st.column_config.NumberColumn(f"{cm[:3]} Lab_CP")
            t2cc[f"{cm[:3]} Lab_PP"] = st.column_config.NumberColumn(f"{cm[:3]} Lab_PP")
            t2cc[f"{cm[:3]} YoY%"] = st.column_config.NumberColumn(f"{cm[:3]} YoY%")
            
            format_dict[f"{cm[:3]} Lab_CP"] = fmt_inr_full
            format_dict[f"{cm[:3]} Lab_PP"] = fmt_inr_full
            format_dict[f"{cm[:3]} YoY%"] = lambda x: fmt_pct(x, sign=True)
            color_subset.append(f"{cm[:3]} YoY%")
            
        def _bold_total_m(row):
            if row["Location"] == "TOTAL":
                return ["font-weight: 700"] * len(row)
            return [""] * len(row)
            
        def _color_growth(val):
            if pd.isna(val) or val == 0: return ""
            return "color: #10b981;" if val > 0 else "color: #ef4444;"
            
        styled2 = t2df.style.apply(_bold_total_m, axis=1)
        styled2 = styled2.map(_color_growth, subset=color_subset)
        styled2 = styled2.format(format_dict)
            
        st.dataframe(styled2, column_config=t2cc, use_container_width=True, hide_index=True)


def _render_opportunities_actions(datasets, mode_str):
    d = datasets["combined"]
    ws = datasets["workshop"]
    bs = datasets["bodyshop"]

    payload = {
        "mode": mode_str, "business_view": st.session_state.get("lab_business_view", "All"),
        "worst_loc": d["worst_loc"],
        "worst_growth": round(d["worst_growth"], 2),
        "worst_driver": d["worst_driver"],
        "best_loc": d["best_loc"],
        "best_growth": round(d["best_growth"], 2),
        "neg_count": d["neg_count"],
        "neg_locations": (d["neg_advs"]["Location Name"].unique().tolist()
                          if d["neg_count"] > 0 else []),
        "top_svc_driver": d["top_svc_driver"],
        "rpc_growth": round(d.get("rpc_g", 0), 2),
        "declining_locs": d.get("declining_locs", []),
    }
    if st.session_state.get("lab_business_view") == "All" and ws and bs:
        payload["workshop_summary"] = {
            "cp": fmt_inr(ws["cp_val"]),
            "growth": round(ws["growth_pct"], 2),
            "best_loc": ws["best_loc"],
            "worst_loc": ws["worst_loc"],
            "top_svc": ws["top_svc_driver"],
        }
        payload["bodyshop_summary"] = {
            "cp": fmt_inr(bs["cp_val"]),
            "growth": round(bs["growth_pct"], 2),
            "best_loc": bs["best_loc"],
            "worst_loc": bs["worst_loc"],
            "top_svc": bs["top_svc_driver"],
        }

    opps_hash = str(hash(str(sorted(payload.items()))))
    if opps_hash != st.session_state.get("lab_ai_opps_hash"):
        with st.spinner("Generating recommendations..."):
            text = get_actions(payload)
        st.session_state.lab_ai_opps = text
        st.session_state.lab_ai_opps_hash = opps_hash
    else:
        text = st.session_state.lab_ai_opps or ""

    opps = re.findall(r"O\d+:\s*(.+?)(?=\s*[OA]\d+:|$)", text, re.DOTALL)
    acts = re.findall(r"A\d+:\s*(.+?)(?=\s*[OA]\d+:|$)", text, re.DOTALL)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            '<div class="section-title">\U0001f4a1 Opportunities</div>',
            unsafe_allow_html=True)
        for i, o in enumerate(opps[:3], 1):
            st.markdown(
                f'<div class="insight-card pos">'
                f'<div class="insight-title">{i}. Opportunity</div>'
                f'<div class="insight-stat">{o.strip()}</div></div>',
                unsafe_allow_html=True)
    with c2:
        st.markdown(
            '<div class="section-title">\U0001f3af Actions Required</div>',
            unsafe_allow_html=True)
        for i, a in enumerate(acts[:3], 1):
            st.markdown(
                f'<div class="insight-card neg">'
                f'<div class="insight-title">{i}. Action</div>'
                f'<div class="insight-stat">{a.strip()}</div></div>',
                unsafe_allow_html=True)


def render(df, pairs, comparison_mode=True, selected_months=None):
    _inject_responsive_css()
    if df.empty:
        EmptyState("No data available for the selected period.")
        return

    _init_state()
    
    mode_str = "YoY" if comparison_mode else "MoM"
    active_pairs = pairs if pairs else []
    
    if not active_pairs:
        EmptyState("No matching prior period data for the selected comparison mode.")
        return

    cp_months = [p[0] for p in active_pairs]
    pp_months = [p[1] for p in active_pairs]
    cp_label = (f"{cp_months[0]} \u2192 {cp_months[-1]}" if len(cp_months) > 1
                else cp_months[0] if cp_months else "\u2014")
    pp_label = (f"{pp_months[0]} \u2192 {pp_months[-1]}" if len(pp_months) > 1
                else pp_months[0] if pp_months else "\u2014")

    cp, pp = _apply_filters(df, active_pairs)
    if cp.empty and pp.empty:
        EmptyState("No data matches the active filters.")
        return

    datasets = _prepare_datasets(cp, pp, df)
    d = datasets["combined"]
    n_rows = len(cp) + len(pp)
    n_locs = d["n_total"]


    _render_cross_filter_bar()
    _render_executive_panel(datasets, mode_str)
    _render_neg_labour_audit(d)
    _render_charts(datasets, active_pairs, mode_str)
    _render_executive_table(datasets, active_pairs, mode_str)
    _render_monthly_detail(datasets, active_pairs, mode_str)
    _render_opportunities_actions(datasets, mode_str)
    _render_ai_narrative(datasets, mode_str, cp_label, pp_label)

