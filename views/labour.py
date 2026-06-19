"""
Labour Revenue — Executive Comparative Dashboard
Multi-Location Mar Dealership  ·  Apple Light-Theme  ·  v2.0
"""
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import re

from utils.calculations.fact_metrics import get_net_labour, get_jobcard_count
from utils.calculations.common import calc_growth_pct, calc_ratio
from ui.formatters import fmt_inr, fmt_pct, fmt_inr_short
from utils.constants import ADV_COL, C, PLY, PLY_TITLE, MONTH_SORT_ORDER, get_ply_layout
from services.ai_service import get_narrative, get_actions
from ui.components.core import EmptyState

_SVC_COLORS = {"PMP": C["primary"], "RR": C["green"], "Accessories": C["orange"],
               "BR": C["purple"], "Bodyshop Repair": C["purple"]}

DEFAULTS = {
    "lab_business_view": "All",
    "lab_service_types": [],
    "lab_cross_loc": None,
    "lab_cross_month": None,
    "lab_cross_svc": None,
    "lab_drill_open": False,
    "lab_drill_type": None,
    "lab_drill_value": None,
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
.lab-drill { border: 2px dashed #E5E5EA; border-radius: 12px; padding: 16px; margin: 8px 0; }
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

    cross_loc = st.session_state.get("lab_cross_loc")
    if cross_loc:
        filtered = filtered[filtered["Location Name"] == cross_loc]

    cross_svc = st.session_state.get("lab_cross_svc")
    if cross_svc:
        filtered = filtered[filtered["Service Type"] == cross_svc]

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


def _compute_metrics(cp, pp, df, val_col="Net_Labour"):
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
    cp_rpc = calc_ratio(cp_val, cp_jc, fill_value=0)
    pp_rpc = calc_ratio(pp_val, pp_jc, fill_value=0)
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

    adv_cp = cp.groupby([ADV_COL, "Location Name", "Service Type"],
                        as_index=False)[val_col].sum()
    adv_pp = pp.groupby([ADV_COL, "Location Name", "Service Type"],
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

    active_svc_count = len(cp["Service Type"].dropna().unique())

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
        "active_svc_count": active_svc_count,
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


def _render_control_bar(df, n_rows, n_locs):
    from utils.constants import FY_MONTHS
    
    client = st.session_state.get("sel_client", "Rukmani Motors")
    all_locs, all_svc, all_months = _get_master_lists(client)

    preset_options = ["Custom", "1M", "3M", "6M"]
    for fy_label, fy_month_list in FY_MONTHS.items():
        if any(m in fy_month_list for m in all_months):
            preset_options.append(fy_label)

    st.markdown('<div class="filter-toolbar" style="background:#f9f9fb; padding:12px 16px; border-radius:8px; border:1px solid #e5e5ea; margin-bottom:16px;">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 3, 3, 3, 1])

    with c1:
        cur_preset = st.session_state.get("month_preset", "3M")
        new_preset = st.selectbox("Period", preset_options, index=preset_options.index(cur_preset) if cur_preset in preset_options else 1, key="lab_month_preset_ui", label_visibility="visible")
        if new_preset != cur_preset:
            st.session_state.month_preset = new_preset
            st.session_state.last_preset = new_preset
            if new_preset == "1M":
                st.session_state.selected_months_custom = [all_months[-1]] if all_months else []
            elif new_preset == "3M":
                st.session_state.selected_months_custom = all_months[-3:] if len(all_months) >= 3 else all_months
            elif new_preset == "6M":
                st.session_state.selected_months_custom = all_months[-6:] if len(all_months) >= 6 else all_months
            elif new_preset != "Custom":
                st.session_state.selected_months_custom = [m for m in all_months if m in FY_MONTHS.get(new_preset, [])]
            st.rerun()

    with c2:
        cur_comp = st.session_state.get("comparison_mode_radio", "YoY")
        if hasattr(st, "segmented_control"):
            new_comp = st.segmented_control("Comparison", ["YoY", "MoM"], default=cur_comp, key="lab_comp_ui")
        else:
            new_comp = st.radio("Comparison", ["YoY", "MoM"], horizontal=True, key="lab_comp_ui")
        if new_comp and new_comp != cur_comp:
            st.session_state.comparison_mode_radio = new_comp
            st.rerun()

    with c3:
        cur_locs = st.session_state.get("filter_location", [])
        new_locs = st.multiselect("Location", all_locs, default=cur_locs, placeholder=f"All Locations ({len(all_locs)})", key="lab_loc_ui", label_visibility="visible")
        if set(new_locs) != set(cur_locs):
            st.session_state.filter_location = new_locs
            st.rerun()

    with c4:
        cur_svc = st.session_state.get("filter_svc_type", [])
        new_svc = st.multiselect("Service Type", all_svc, default=cur_svc, placeholder=f"All Service Types ({len(all_svc)})", key="lab_svc_ui", label_visibility="visible")
        if set(new_svc) != set(cur_svc):
            st.session_state.filter_svc_type = new_svc
            st.rerun()

    with c5:
        cur_biz = st.session_state.get("lab_business_view", "All")
        st.markdown('<div style="margin-bottom:8px;font-size:14px;color:#1D1D1F;">Business View</div>', unsafe_allow_html=True)
        if hasattr(st, "segmented_control"):
            new_b = st.segmented_control("Business View", ["All", "Workshop", "Bodyshop"], default=cur_biz, key="lab_biz_ui", label_visibility="collapsed")
        else:
            new_b = st.radio("Business View", ["All", "Workshop", "Bodyshop"], index=["All", "Workshop", "Bodyshop"].index(cur_biz), horizontal=True, key="lab_biz_ui", label_visibility="collapsed")
        if new_b and new_b != cur_biz:
            st.session_state.lab_business_view = new_b
            st.rerun()

    with c6:
        st.markdown('<div style="margin-top:28px;"></div>', unsafe_allow_html=True)
        if st.button("🔄 Reset Page", key="lab_reset_ui"):
            st.session_state.month_preset = "3M"
            st.session_state.last_preset = "3M"
            st.session_state.comparison_mode_radio = "YoY"
            st.session_state.selected_months_custom = all_months[-3:] if len(all_months) >= 3 else all_months
            st.session_state.lab_business_view = "All"
            
            keys_to_clear = ["filter_location", "filter_svc_type", "lab_cross_loc", "lab_cross_month", "lab_cross_svc"]
            for k in keys_to_clear:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    cur_preset = st.session_state.get("month_preset", "3M")
    if cur_preset == "Custom":
        cur_sel = st.session_state.get("selected_months_custom", [])
        new_sel = st.multiselect("Custom Months", all_months, default=cur_sel, key="lab_custom_months_ui")
        if set(new_sel) != set(cur_sel):
            st.session_state.selected_months_custom = new_sel
            st.rerun()



def _render_cross_filter_bar():
    chips = []
    cross_loc = st.session_state.get("lab_cross_loc")
    cross_month = st.session_state.get("lab_cross_month")
    cross_svc = st.session_state.get("lab_cross_svc")
    if cross_loc:
        chips.append(("\U0001f4cd " + cross_loc, "lab_cross_loc"))
    if cross_month:
        chips.append(("\U0001f4c5 " + cross_month, "lab_cross_month"))
    if cross_svc:
        chips.append(("\U0001f527 " + cross_svc, "lab_cross_svc"))
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
        st.session_state.lab_cross_loc = None
        st.session_state.lab_cross_month = None
        st.session_state.lab_cross_svc = None
        st.rerun()


def _render_ai_narrative(datasets, mode_str, cp_label, pp_label):
    d = datasets["combined"]
    ws = datasets["workshop"]
    bs = datasets["bodyshop"]
    biz = st.session_state.get("lab_business_view", "All")
    cross_filters = {}
    if st.session_state.get("lab_cross_loc"):
        cross_filters["location"] = st.session_state.lab_cross_loc
    if st.session_state.get("lab_cross_month"):
        cross_filters["month"] = st.session_state.lab_cross_month
    if st.session_state.get("lab_cross_svc"):
        cross_filters["service_type"] = st.session_state.lab_cross_svc

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
        "top_svc_driver": d["top_svc_driver"],
        "cross_filters": cross_filters,
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


def _render_kpi_tier_1(datasets, mode_str):
    d = datasets["combined"]
    c1, c2, c3 = st.columns(3)

    def _card(col, label, value, delta_pct, delta_pos, what, why, so_what):
        dc = "kpi-delta-pos" if delta_pos else "kpi-delta-neg"
        ds = (f"(+{delta_pct:.2f}%)" if delta_pos and delta_pct > 0
              else f"({delta_pct:.2f}%)" if delta_pct != 0 else "")
        with col:
            st.markdown(
                f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">{value}</div>'
                f'<div class="{dc}">{ds}</div></div>',
                unsafe_allow_html=True)
            if hasattr(st, "popover"):
                with st.popover("What \u00b7 Why \u00b7 So What"):
                    st.markdown(f"**What:** {what}")
                    st.markdown(f"**Why:** {why}")
                    st.markdown(f"**So What:** {so_what}")

    abs_growth = d["cp_val"] - d["pp_val"]
    _card(c1, f"CP Labour Revenue ({mode_str})", fmt_inr(d["cp_val"]),
          d["growth_pct"], d["growth_pct"] >= 0,
          what=f"Total net labour billed: {fmt_inr(d['cp_val'])}.",
          why=f"Top contributor: {d['best_loc']} ({fmt_pct(d['best_growth'], True)}). "
              f"Driver: {d['best_driver']}.",
          so_what=f"{'Above' if d['growth_pct'] > 0 else 'Below'} prior by "
                  f"{fmt_inr(abs(abs_growth))}. "
                  f"{'Sustain momentum.' if d['growth_pct'] > 0 else 'Immediate review.'}")

    _card(c2, f"PP Labour Revenue ({mode_str})", fmt_inr(d["pp_val"]),
          0, True,
          what=f"Prior period labour: {fmt_inr(d['pp_val'])}.",
          why=f"{'Same months prior year' if mode_str == 'YoY' else 'Preceding months'}.",
          so_what=f"Gap: {fmt_inr(abs(abs_growth))}.")

    _card(c3, "Revenue per Jobcard", fmt_inr(d["cp_rpc"]),
          d["rpc_growth"], d["rpc_growth"] >= 0,
          what=f"Average realised per jobcard: {fmt_inr(d['cp_rpc'])}.",
          why=f"{'Higher-value mix (' + d['top_svc_driver'] + ').' if d['rpc_growth'] >= 0 else 'Lower-value mix. ' + d['top_svc_driver'] + ' volume up.'}",
          so_what=f"{'Realisation improving.' if d['rpc_growth'] >= 0 else 'Push attach rates.'}")


def _render_kpi_tier_2(datasets):
    d = datasets["combined"]
    loc_count = len(d["loc_df"])
    global_locations = st.session_state.get("filter_location", [])
    single_loc = len(global_locations) == 1

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if single_loc:
            st.markdown(
                '<div class="kpi-card"><div class="kpi-label">Best Location</div>'
                '<div class="kpi-meta" style="padding:12px 0">Only 1 location in view \u2014 widen filters</div></div>',
                unsafe_allow_html=True)
        else:
            badge = "badge-pos" if d["best_growth"] > 0 else "badge-neg"
            st.markdown(
                f'<div class="kpi-card"><div class="kpi-label">Best Location</div>'
                f'<div class="kpi-value">{d["best_loc"]}</div>'
                f'<div class="{badge}">({fmt_pct(d["best_growth"], True)})</div>'
                f'<div class="kpi-meta">{d["best_driver"]}</div></div>',
                unsafe_allow_html=True)

    with c2:
        if single_loc:
            st.markdown(
                '<div class="kpi-card"><div class="kpi-label">Worst Location</div>'
                '<div class="kpi-meta" style="padding:12px 0">Only 1 location in view \u2014 widen filters</div></div>',
                unsafe_allow_html=True)
        else:
            badge = "badge-neg" if d["worst_growth"] < 0 else "badge-pos"
            st.markdown(
                f'<div class="kpi-card"><div class="kpi-label">Worst Location</div>'
                f'<div class="kpi-value">{d["worst_loc"]}</div>'
                f'<div class="{badge}">({fmt_pct(d["worst_growth"], True)})</div>'
                f'<div class="kpi-meta">{d["worst_driver"]}</div></div>',
                unsafe_allow_html=True)

    with c3:
        hp = calc_ratio(d["n_growing"], d["n_total"], multiplier=100, fill_value=0)
        hb = ("badge-pos" if hp >= 70 else "badge-warn" if hp >= 50 else "badge-neg")
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-label">Locations Growing</div>'
            f'<div class="kpi-value">{d["n_growing"]} / {d["n_total"]}</div>'
            f'<div class="{hb}">{hp:.0f}% healthy</div></div>',
            unsafe_allow_html=True)

    with c4:
        svc_names = d["svc_df"].sort_values("CP", ascending=False).head(2).index.tolist()
        top2 = ", ".join(svc_names) if svc_names else "\u2014"
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-label">Active Service Types</div>'
            f'<div class="kpi-value">{d["active_svc_count"]}</div>'
            f'<div class="kpi-meta">Top 2: {top2}</div></div>',
            unsafe_allow_html=True)


def _render_neg_labour_audit(data):
    if data["neg_count"] == 0:
        return
    val_col = "Net_Labour"
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
    c1, c2 = st.columns([3, 2])

    with c1:
        months = [p[0] for p in active_pairs]
        cp_vals = [data["cp_month_sum"].get(m, 0) for m in months]
        pp_vals = [data["pp_month_sum"].get(p[1], 0) for p in active_pairs]
        growth = [calc_growth_pct(c, p, fill_value=0) for c, p in zip(cp_vals, pp_vals)]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name=f"CP ({mode_str})", x=months, y=cp_vals,
            marker_color=C["primary"],
            text=[fmt_inr_short(v) for v in cp_vals], textposition="outside",
            customdata=list(zip(months, cp_vals, pp_vals, growth)),
            hovertemplate=("<b>%{customdata[0]}</b><br>CP: \u20b9%{customdata[1]:,.0f}"
                           "<br>PP: \u20b9%{customdata[2]:,.0f}"
                           "<br>Growth: %{customdata[3]:.1f}%<extra></extra>")))
        fig.add_trace(go.Bar(
            name="PP", x=months, y=pp_vals, marker_color=C["gray"], opacity=0.7,
            text=[fmt_inr_short(v) for v in pp_vals], textposition="outside"))
        fig.add_trace(go.Scatter(
            name="Growth %", x=months, y=growth,
            mode="lines+markers+text", yaxis="y2",
            line=dict(color=C["orange"], width=2),
            text=[f"{g:+.1f}%" for g in growth], textposition="top center",
            marker=dict(size=8, color=[C["green"] if g >= 0 else C["red"] for g in growth])))
        fig.update_layout(**get_ply_layout(
            barmode="group", height=300,
            title=dict(text=f"Revenue Trend \u2014 {mode_str}", **PLY_TITLE),
            yaxis=dict(**PLY["yaxis"], title="Revenue (\u20b9)"),
            yaxis2=dict(title="Growth %", overlaying="y", side="right",
                        tickformat=".1f", showgrid=False)))

        ev = st.plotly_chart(fig, use_container_width=True,
                             on_select="rerun", selection_mode="points",
                             key="chart_trend")
        if ev and ev.selection and ev.selection.points:
            cm = ev.selection.points[0].get("x")
            if cm and cm != st.session_state.get("lab_cross_month"):
                st.session_state.lab_cross_month = cm
                st.rerun()

    with c2:
        all_svc = sorted(data["svc_df"].index)
        fig2 = go.Figure()
        for svc in all_svc:
            cv = data["svc_df"].loc[svc, "CP"]
            pv = data["svc_df"].loc[svc, "PP"]
            fig2.add_trace(go.Bar(
                name=svc, x=["CP", "PP"], y=[cv, pv],
                marker_color=_SVC_COLORS.get(svc, C["gray"]),
                text=[fmt_inr_short(cv), fmt_inr_short(pv)], textposition="inside",
                customdata=[[svc, cv, pv, calc_growth_pct(cv, pv, 0)]] * 2,
                hovertemplate=("<b>%{customdata[0]}</b><br>%{x}: \u20b9%{y:,.0f}"
                               "<br>Growth: %{customdata[3]:.1f}%<extra></extra>")))
        fig2.update_layout(**get_ply_layout(
            barmode="stack", height=300,
            title=dict(text=f"Service Type Mix \u2014 {mode_str}", **PLY_TITLE)))

        ev2 = st.plotly_chart(fig2, use_container_width=True,
                              on_select="rerun", selection_mode="points",
                              key="chart_svc")
        if ev2 and ev2.selection and ev2.selection.points:
            idx = ev2.selection.points[0].get("curve_number", 0)
            if idx < len(all_svc):
                clicked = all_svc[idx]
                if clicked != st.session_state.get("lab_cross_svc"):
                    st.session_state.lab_cross_svc = clicked
                    st.rerun()


def _render_heatmap(datasets, active_pairs, mode_str):
    data = datasets["combined"]
    months = [p[0] for p in active_pairs]
    locs = sorted(set(data["cp_loc_month_piv"].index) |
                  set(data["pp_loc_month_piv"].index))
    z, txt = [], []
    for loc in locs:
        rz, rt = [], []
        for cm, pm, _ in active_pairs:
            cv = (data["cp_loc_month_piv"].loc[loc, cm]
                  if loc in data["cp_loc_month_piv"].index
                  and cm in data["cp_loc_month_piv"].columns else 0)
            pv = (data["pp_loc_month_piv"].loc[loc, pm]
                  if loc in data["pp_loc_month_piv"].index
                  and pm in data["pp_loc_month_piv"].columns else 0)
            g = calc_growth_pct(cv, pv, fill_value=np.nan)
            rz.append(g)
            rt.append(f"{g:+.1f}" if not np.isnan(g) else "\u2014")
        z.append(rz); txt.append(rt)

    h = max(320, len(locs) * 28 + 60)
    fig = go.Figure(go.Heatmap(
        z=z, x=months, y=locs,
        colorscale=[[0, "#FF3B30"], [0.5, "#FFFFFF"], [1, "#34C759"]],
        zmid=0, zmin=-30, zmax=30,
        text=txt, texttemplate="%{text}%", textfont=dict(size=10),
        hovertemplate="<b>%{y}</b> \u2014 %{x}<br>Growth: %{text}%<extra></extra>"))
    fig.update_layout(**get_ply_layout(
        height=h,
        title=dict(text=f"Location Growth Heatmap \u2014 {mode_str}", **PLY_TITLE),
        xaxis=dict(**PLY["xaxis"], side="top")))

    ev = st.plotly_chart(fig, use_container_width=True,
                         on_select="rerun", selection_mode="points",
                         key="chart_heat")
    if ev and ev.selection and ev.selection.points:
        pt = ev.selection.points[0]
        cl = pt.get("y"); cm = pt.get("x")
        changed = False
        if cl and cl != st.session_state.get("lab_cross_loc"):
            st.session_state.lab_cross_loc = cl; changed = True
        if cm and cm != st.session_state.get("lab_cross_month"):
            st.session_state.lab_cross_month = cm; changed = True
        if changed:
            st.rerun()


def _render_waterfalls(datasets, mode_str):
    data = datasets["combined"]
    g1, g2 = st.columns(2)

    with g1:
        sl = sorted(data["loc_df"].index,
                    key=lambda l: data["loc_df"].loc[l, "Delta"], reverse=True)
        wf_x = ["PP Total"] + sl + ["CP Total"]
        wf_y = ([data["pp_val"]] +
                [data["loc_df"].loc[l, "Delta"] for l in sl] +
                [data["cp_val"]])
        wf_m = ["absolute"] + ["relative"] * len(sl) + ["total"]
        wf_t = ([fmt_inr_short(data["pp_val"])] +
                [f"{'+' if v >= 0 else ''}{fmt_inr_short(v)}"
                 for v in [data["loc_df"].loc[l, "Delta"] for l in sl]] +
                [fmt_inr_short(data["cp_val"])])
        fig = go.Figure(go.Waterfall(
            name="Location Bridge", orientation="v",
            measure=wf_m, x=wf_x, y=wf_y, text=wf_t,
            textposition="outside",
            increasing={"marker": {"color": C["green"]}},
            decreasing={"marker": {"color": C["red"]}},
            totals={"marker": {"color": C["primary"]}},
            connector={"line": {"color": "#E5E5EA", "width": 1}}))
        fig.update_layout(**get_ply_layout(
            height=360,
            title=dict(text=f"Location Bridge \u2014 {mode_str}", **PLY_TITLE)))
        ev = st.plotly_chart(fig, use_container_width=True,
                             on_select="rerun", selection_mode="points",
                             key="chart_wf_loc")
        if ev and ev.selection and ev.selection.points:
            loc = ev.selection.points[0].get("x")
            if loc and loc not in ("PP Total", "CP Total"):
                st.session_state.lab_cross_loc = loc
                st.session_state.lab_drill_open = True
                st.session_state.lab_drill_type = "location"
                st.session_state.lab_drill_value = loc
                st.rerun()

    with g2:
        ss = sorted(data["svc_df"].index,
                    key=lambda s: data["svc_df"].loc[s, "Delta"], reverse=True)
        wf2_x = ["PP Total"] + ss + ["CP Total"]
        wf2_y = ([data["pp_val"]] +
                 [data["svc_df"].loc[s, "Delta"] for s in ss] +
                 [data["cp_val"]])
        wf2_m = ["absolute"] + ["relative"] * len(ss) + ["total"]
        wf2_t = ([fmt_inr_short(data["pp_val"])] +
                 [f"{'+' if v >= 0 else ''}{fmt_inr_short(v)}"
                  for v in [data["svc_df"].loc[s, "Delta"] for s in ss]] +
                 [fmt_inr_short(data["cp_val"])])
        fig2 = go.Figure(go.Waterfall(
            name="Service Bridge", orientation="v",
            measure=wf2_m, x=wf2_x, y=wf2_y, text=wf2_t,
            textposition="outside",
            increasing={"marker": {"color": C["green"]}},
            decreasing={"marker": {"color": C["red"]}},
            totals={"marker": {"color": C["primary"]}},
            connector={"line": {"color": "#E5E5EA", "width": 1}}))
        fig2.update_layout(**get_ply_layout(
            height=360,
            title=dict(text=f"Service Type Bridge \u2014 {mode_str}", **PLY_TITLE)))
        ev2 = st.plotly_chart(fig2, use_container_width=True,
                              on_select="rerun", selection_mode="points",
                              key="chart_wf_svc")
        if ev2 and ev2.selection and ev2.selection.points:
            svc = ev2.selection.points[0].get("x")
            if svc and svc not in ("PP Total", "CP Total"):
                st.session_state.lab_cross_svc = svc
                st.session_state.lab_drill_open = True
                st.session_state.lab_drill_type = "service"
                st.session_state.lab_drill_value = svc
                st.rerun()


def _render_drill_down(datasets):
    if not st.session_state.get("lab_drill_open"):
        return
    dtype = st.session_state.get("lab_drill_type")
    dval = st.session_state.get("lab_drill_value")
    if not dtype or not dval:
        return
    data = datasets["combined"]

    st.markdown('<div class="lab-drill">', unsafe_allow_html=True)
    if dtype == "location":
        st.markdown(f"**{dval} \u2014 Service Type Breakdown**")
        cp_s = (data["loc_svc_cp"].xs(dval, level="Location Name")
                if dval in data["loc_svc_cp"].index.get_level_values("Location Name")
                else pd.Series(dtype=float))
        pp_s = (data["loc_svc_pp"].xs(dval, level="Location Name")
                if dval in data["loc_svc_pp"].index.get_level_values("Location Name")
                else pd.Series(dtype=float))
        sdf = pd.DataFrame({"CP": cp_s, "PP": pp_s}).fillna(0)
        fig = go.Figure()
        for svc in sdf.index:
            fig.add_trace(go.Bar(
                name=svc, x=["CP", "PP"],
                y=[sdf.loc[svc, "CP"], sdf.loc[svc, "PP"]],
                marker_color=_SVC_COLORS.get(svc, C["gray"])))
        fig.update_layout(**get_ply_layout(
            barmode="stack", height=240,
            title=dict(text=f"{dval} Service Breakdown", **PLY_TITLE)))
        st.plotly_chart(fig, use_container_width=True, key="drill_loc_chart")

    elif dtype == "service":
        st.markdown(f"**{dval} \u2014 Location Breakdown**")
        cp_l = (data["loc_svc_cp"].xs(dval, level="Service Type")
                if dval in data["loc_svc_cp"].index.get_level_values("Service Type")
                else data["loc_df"]["CP"])
        pp_l = (data["loc_svc_pp"].xs(dval, level="Service Type")
                if dval in data["loc_svc_pp"].index.get_level_values("Service Type")
                else data["loc_df"]["PP"])
        ldf = pd.DataFrame({"CP": cp_l, "PP": pp_l}).fillna(0).sort_values("CP", ascending=False)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="CP", x=ldf.index.tolist(),
                              y=ldf["CP"].tolist(), marker_color=C["primary"]))
        fig2.add_trace(go.Bar(name="PP", x=ldf.index.tolist(),
                              y=ldf["PP"].tolist(), marker_color=C["gray"], opacity=0.7))
        fig2.update_layout(**get_ply_layout(
            barmode="group", height=240,
            title=dict(text=f"{dval} by Location", **PLY_TITLE)))
        st.plotly_chart(fig2, use_container_width=True, key="drill_svc_chart")

    if st.button("\u2715 Close drill-down", key="close_drill"):
        st.session_state.lab_drill_open = False
        st.session_state.lab_drill_type = None
        st.session_state.lab_drill_value = None
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def _render_executive_table(datasets, active_pairs, mode_str):
    data = datasets["combined"]
    st.markdown("---")
    tab1, tab2 = st.tabs(["Performance Table", "YoY Comparison"])

    with tab1:
        st.markdown(
            f'<div class="section-title">\U0001f4ca Performance Table \u2014 {mode_str}</div>',
            unsafe_allow_html=True)
        all_locs = sorted(set(data["cp_loc_month_piv"].index) |
                          set(data["pp_loc_month_piv"].index))
        rows = []
        for loc in all_locs:
            row = {"Location": loc}
            sp = []
            lcp = data["loc_df"].loc[loc, "CP"] if loc in data["loc_df"].index else 0
            lpp = data["loc_df"].loc[loc, "PP"] if loc in data["loc_df"].index else 0
            for cm, pm, _ in active_pairs:
                cv = (data["cp_loc_month_piv"].loc[loc, cm]
                      if loc in data["cp_loc_month_piv"].index
                      and cm in data["cp_loc_month_piv"].columns else 0)
                pv = (data["pp_loc_month_piv"].loc[loc, pm]
                      if loc in data["pp_loc_month_piv"].index
                      and pm in data["pp_loc_month_piv"].columns else 0)
                row[f"{cm[:3]} \u0394%"] = calc_growth_pct(cv, pv, fill_value=np.nan)
                sp.append(cv)
            row["CP Total"] = lcp
            row["PP Total"] = lpp
            row["Total \u0394%"] = calc_growth_pct(lcp, lpp, fill_value=np.nan)
            row["Share%"] = calc_ratio(lcp, data["cp_val"], multiplier=100, fill_value=0)
            row["Trend"] = sp
            rows.append(row)

        tdf = pd.DataFrame(rows).sort_values("CP Total", ascending=False)

        def _rs(row):
            d = row.get("Total \u0394%", 0)
            if pd.isna(d):
                return [""] * len(row)
            if d < -5:
                return ["background-color:#FFEBE9"] * len(row)
            if d > 15:
                return ["background-color:#E8F9EE"] * len(row)
            return [""] * len(row)

        styled = tdf.style.apply(_rs, axis=1)
        cc = {
            "Location": st.column_config.TextColumn("Location"),
            "CP Total": st.column_config.NumberColumn("CP Total", format="\u20b9%.0f"),
            "PP Total": st.column_config.NumberColumn("PP Total", format="\u20b9%.0f"),
            "Total \u0394%": st.column_config.NumberColumn(
                f"Total {mode_str}%", format="%.1f%%"),
            "Share%": st.column_config.ProgressColumn(
                "Share %", format="%.1f%%", min_value=0, max_value=100),
            "Trend": st.column_config.LineChartColumn("Trend (CP)"),
        }
        for cm, _, _ in active_pairs:
            cc[f"{cm[:3]} \u0394%"] = st.column_config.NumberColumn(
                f"{cm[:3]} {mode_str}%", format="%.1f%%")
        st.dataframe(styled, column_config=cc, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown(
            f'<div class="section-title">\U0001f4ca YoY Comparison \u2014 {mode_str}</div>',
            unsafe_allow_html=True)
        all_locs2 = sorted(set(data["cp_loc_month_piv"].index) |
                           set(data["pp_loc_month_piv"].index))
        t2_rows = []
        for loc in all_locs2:
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
        for cm, _, _ in active_pairs:
            t2cc[f"{cm[:3]} Lab_CP"] = st.column_config.NumberColumn(
                f"{cm[:3]} Lab_CP", format="\u20b9%.0f")
            t2cc[f"{cm[:3]} Lab_PP"] = st.column_config.NumberColumn(
                f"{cm[:3]} Lab_PP", format="\u20b9%.0f")
            t2cc[f"{cm[:3]} YoY%"] = st.column_config.NumberColumn(
                f"{cm[:3]} YoY%", format="%.1f%%")
        st.dataframe(t2df, column_config=t2cc, use_container_width=True, hide_index=True)


def _render_opportunities_actions(datasets, mode_str):
    d = datasets["combined"]
    ws = datasets["workshop"]
    bs = datasets["bodyshop"]

    declining = d["valid_locs"][d["valid_locs"]["Growth"] < 0].sort_values("Growth").head(3)
    opps_data = []
    for loc in declining.index:
        avg = d["loc_6m_avg"].get(loc, d["loc_df"].loc[loc, "CP"]
                                  if loc in d["loc_df"].index else 0)
        gap = avg - (d["loc_df"].loc[loc, "CP"]
                     if loc in d["loc_df"].index else 0)
        opps_data.append({"location": loc, "gap_inr": fmt_inr(max(gap, 0)),
                          "current_growth": round(
                              d["loc_df"].loc[loc, "Growth"], 2)
                          if loc in d["loc_df"].index else 0})

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
        "rpc_growth": round(d["rpc_growth"], 2),
        "declining_locs": opps_data,
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


    _render_control_bar(df, n_rows, n_locs)
    _render_cross_filter_bar()
    _render_ai_narrative(datasets, mode_str, cp_label, pp_label)
    _render_kpi_tier_1(datasets, mode_str)
    _render_kpi_tier_2(datasets)
    _render_neg_labour_audit(d)
    _render_charts(datasets, active_pairs, mode_str)
    _render_heatmap(datasets, active_pairs, mode_str)
    _render_waterfalls(datasets, mode_str)
    _render_drill_down(datasets)
    _render_executive_table(datasets, active_pairs, mode_str)
    _render_opportunities_actions(datasets, mode_str)

