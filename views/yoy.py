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
from utils.constants import ADV_COL, MP_COLORS, C, PLY

# Import shared UI helpers from app
from ui.kpi_cards import kpi
from ui.tables import html_table
from ui.traffic import yoy_badge, traffic_light, tgt_badge
from ui.helpers import apply_chart, clean_hover, _render_finding, csv_btn
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num

def render(df, pairs, val_col, tab_key, title_prefix, comparison_mode=True, selected_months=None):
    with st.spinner(f"Computing {title_prefix}..."):
        if df.empty:
            from ui.components.core import EmptyState
            EmptyState('No data available for the selected period. Adjust your filters or check data freshness.')
            return
    cp_months = [p[0] for p in pairs]
    pp_months = [p[1] for p in pairs]
    # df contains both CP and PP months, filter appropriately
    cp = apply_month_filter(df, "Month Name", cp_months)
    pp = apply_month_filter(df, "Month Name", pp_months)

    mode_str = "YoY" if comparison_mode else "MoM"

    cp_val = cp[val_col].sum(); pp_val = pp[val_col].sum()
    cp_locs = location_summary(cp, as_index=True)[val_col].sum()
    pp_locs = location_summary(pp, as_index=True)[val_col].sum()
    _df = pd.DataFrame({"CP": cp_locs, "PP": pp_locs}).fillna(0)
    _df["Growth"] = calc_growth_pct(_df["CP"], _df["PP"], fill_value=np.nan)
    valid_locs = _df[_df["PP"] > 10000]["Growth"].dropna()
    best_loc = valid_locs.idxmax() if not valid_locs.empty else "N/A"
    best_val = valid_locs.max() if not valid_locs.empty else 0

    cp_growth_pct = calc_growth_pct(cp_val, pp_val, fill_value=np.nan)
    growth_label = fmt_pct(cp_growth_pct, True) if not np.isnan(cp_growth_pct) else "New ✦"

    c = st.columns(6)
    with c[0]: kpi(f"CP {title_prefix}", fmt_inr(cp_val))
    with c[1]: kpi(f"PP {title_prefix}", fmt_inr(pp_val))
    with c[2]: kpi(f"Overall {mode_str}", growth_label, cp=cp_val, pp=pp_val)
    mp_pb_sums = cp.groupby("MP_PB")[val_col].sum()
    with c[3]: kpi("WS CP", fmt_inr(mp_pb_sums.get("MP", 0)))
    with c[4]: kpi("BS CP", fmt_inr(mp_pb_sums.get("PB", 0)))
    with c[5]: kpi(f"Best: {best_loc[:13]}", fmt_pct(best_val, True) if best_val else "—")

    st.markdown(f'<div class="section-card"><div class="section-title">📊 Location × Month — {title_prefix} {mode_str}</div>', unsafe_allow_html=True)
    all_locs = sorted(set(cp["Location Name"].unique()) | set(pp["Location Name"].unique()))
    c_piv = cp.groupby(["Location Name","Month Name"], dropna=False)[val_col].sum().reset_index()
    p_piv = pp.groupby(["Location Name","Month Name"], dropna=False)[val_col].sum().reset_index()
    c_idx = c_piv.set_index(["Location Name", "Month Name"])[val_col] if not c_piv.empty else pd.Series(dtype=float)
    p_idx = p_piv.set_index(["Location Name", "Month Name"])[val_col] if not p_piv.empty else pd.Series(dtype=float)
    c_m_idx = c_piv.groupby("Month Name")[val_col].sum() if not c_piv.empty else pd.Series(dtype=float)
    p_m_idx = p_piv.groupby("Month Name")[val_col].sum() if not p_piv.empty else pd.Series(dtype=float)
    
    rows = []
    for loc in all_locs:
        r = {"🚦": "", "Location Name": loc}
        ct = 0; pt = 0
        for cm, pm, _ in pairs:
            cv = c_idx.get((loc, cm), 0)
            pv = p_idx.get((loc, pm), 0)
            r[cm] = fmt_inr(cv); r[pm] = fmt_inr(pv)
            r[f"{cm} {mode_str}%"] = yoy_badge(cv, pv)
            ct+=cv; pt+=pv
        r["Total CP"] = fmt_inr(ct); r["Total PP"] = fmt_inr(pt); r[f"Total {mode_str}%"] = yoy_badge(ct, pt)
        r["🚦"] = f'<span class="traffic-light">{traffic_light(ct, pt)}</span>'
        rows.append(r)

    tr = {"🚦": "", "Location Name": "TOTAL"}
    cgt = 0; pgt = 0
    for cm, pm, _ in pairs:
        cv = c_m_idx.get(cm, 0)
        pv = p_m_idx.get(pm, 0)
        tr[cm] = fmt_inr(cv); tr[pm] = fmt_inr(pv); tr[f"{cm} {mode_str}%"] = yoy_badge(cv, pv)
        cgt+=cv; pgt+=pv
    tr["Total CP"] = fmt_inr(cgt); tr["Total PP"] = fmt_inr(pgt); tr[f"Total {mode_str}%"] = yoy_badge(cgt, pgt)
    rows.append(tr)
    
    html_table(pd.DataFrame(rows), total_row=True, height="400px")
    csv_btn(pd.DataFrame(rows), f"{title_prefix}_yoy.csv", f"yoy_{tab_key}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="section-card"><div class="section-title">📊 Grouped Bar (CP vs PP)</div>', unsafe_allow_html=True)
        gb = pd.DataFrame({"Location Name": all_locs})
        gb["CP"] = gb["Location Name"].map(cp_locs).fillna(0)
        gb["PP"] = gb["Location Name"].map(pp_locs).fillna(0)
        gb_m = gb.melt(id_vars="Location Name", value_vars=["CP", "PP"], var_name="Period", value_name="Val")
        fig = px.bar(gb_m, x="Location Name", y="Val", color="Period", barmode="group", color_discrete_map={"CP":C["primary"], "PP":C["gold"]})
        fig.update_layout(**PLY); fig.update_layout(height=320, xaxis_title="", yaxis_title="Amount (₹)")
        st.plotly_chart(fig, width='stretch', key=f"bar_{tab_key}",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="section-card"><div class="section-title">📈 YoY% Trend Lines</div>', unsafe_allow_html=True)
        t_rows = []
        for loc in all_locs:
            for cm, pm, ms in pairs:
                cv = c_idx.get((loc, cm), 0)
                pv = p_idx.get((loc, pm), 0)
                if pv > 0:
                    t_rows.append({"Location Name": loc, "Month": cm, "Sort": ms, "YoY%": (cv-pv)/pv*100})
        if t_rows:
            tdf = pd.DataFrame(t_rows).sort_values("Sort")
            fig = px.line(tdf, x="Month", y="YoY%", color="Location Name", markers=True)
            fig.add_hline(y=0, line_dash="dash", line_color=C["gray"])
            fig.update_layout(**PLY); fig.update_layout(height=320, xaxis_title="")
            st.plotly_chart(fig, width='stretch', key=f"line_{tab_key}",
                            config={"displayModeBar": True, "displaylogo": False,
                                    "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                    "toImageButtonOptions": {"format":"png","scale":2}})
        st.markdown('</div>', unsafe_allow_html=True)
        
    c1, c2 = st.columns(2)
    with c1:
        wbs = cp.groupby(["Month_Sort","Month Name","MP_PB"], as_index=False, dropna=False)[val_col].sum()\
                 .sort_values("Month_Sort")\
                 .rename(columns={"MP_PB":"Type","Month Name":"Month",val_col:"Amount (₹)"})
        wbs["Label"] = wbs["Amount (₹)"].apply(fmt_inr_short)
        fig = px.bar(wbs, x="Month", y="Amount (₹)", color="Type",
                     color_discrete_map={"MP":C["primary"],"PB":C["orange"]},
                     text="Label", barmode="stack")
        apply_chart(fig, f"🏢 {title_prefix} by Type & Month — CP", 340, text_col="Label", bar_text_pos="inside")
        fig.update_traces(
            hovertemplate="<b>%{fullData.name} {title_prefix}</b><br>Month: %{x}<br>Amount: %{{customdata[0]}}<extra></extra>".replace("{title_prefix}", title_prefix),
            insidetextanchor="middle",
            textfont=dict(size=10, color="#FFFFFF")
        )
        st.plotly_chart(fig, width='stretch', key=f"wsbs_{tab_key}",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
    with c2:
        if title_prefix == "Labour":
            st.markdown(f'<div class="section-card"><div class="section-title">🔧 Service Type — Like-for-Like YoY</div>', unsafe_allow_html=True)
            # Like-for-like: compare each Service Type CP vs same Service Type PP
            svc_cp = cp.groupby("Service Type", as_index=False, dropna=False)[val_col].sum()
            svc_pp = pp.groupby("Service Type", as_index=False, dropna=False)[val_col].sum()
            svc_cp.columns = ["Service Type", "CP"]
            svc_pp.columns = ["Service Type", "PP"]
            svc_lfl = pd.merge(svc_cp, svc_pp, on="Service Type", how="outer").fillna(0)
            svc_lfl = svc_lfl[svc_lfl["CP"] > 0].sort_values("CP", ascending=False)
            svc_lfl["YoY%"] = np.where(
                svc_lfl["PP"] > 0,
                calc_growth_pct(svc_lfl["CP"], svc_lfl["PP"], fill_value=np.nan),
                np.nan
            )
            svc_m = svc_lfl.melt(id_vars="Service Type", value_vars=["CP", "PP"], var_name="Period", value_name="Val")
            fig = px.bar(svc_m, x="Service Type", y="Val", color="Period", barmode="group",
                         color_discrete_map={"CP": C["primary"], "PP": C["gold"]},
                         text_auto=".2s")
            fig.update_layout(**PLY); fig.update_layout(height=320, xaxis_title="", yaxis_title="₹")
            st.plotly_chart(fig, width='stretch', key=f"svc_{tab_key}",
                            config={"displayModeBar": True, "displaylogo": False,
                                    "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                    "toImageButtonOptions": {"format":"png","scale":2}})
            # Show YoY% table below the chart
            tbl = svc_lfl[["Service Type","CP","PP","YoY%"]].copy()
            tbl["CP"] = tbl["CP"].apply(fmt_inr)
            tbl["PP"] = tbl["PP"].apply(fmt_inr)
            tbl["YoY%"] = tbl["YoY%"].apply(lambda x: fmt_pct(x, True) if not np.isnan(x) else "New ✦")
            html_table(tbl, height="200px")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="section-card"><div class="section-title">🧰 Parts Margin % by Location</div>', unsafe_allow_html=True)
            pm = location_summary(cp, as_index=False).agg(P=("Net_Parts","sum"), M=("Parts_Margin","sum"))
            pm["M%"] = np.where(pm["P"]>0, pm["M"]/pm["P"]*100, 0)
            pm = pm.sort_values("M%", ascending=False)
            fig = px.bar(pm, x="Location Name", y="M%", color_discrete_sequence=[C["green"]])
            fig.update_layout(**PLY); fig.update_layout(height=320, xaxis_title="", yaxis_title="Margin %")
            st.plotly_chart(fig, width='stretch', key=f"pm_{tab_key}",
                            config={"displayModeBar": True, "displaylogo": False,
                                    "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                    "toImageButtonOptions": {"format":"png","scale":2}})
            st.markdown('</div>', unsafe_allow_html=True)
