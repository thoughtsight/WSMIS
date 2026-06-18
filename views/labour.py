import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from services.financial_service import FinancialService
from utils.calculations.fact_metrics import get_net_labour
from utils.calculations.common import calc_growth_pct, calc_ratio
from utils.aggregations import location_summary
from utils.filters import apply_month_filter, apply_mp_pb_filter
from ui.formatters import fmt_inr, fmt_pct
from utils.constants import ADV_COL, C, PLY

def render(df, pairs, comparison_mode=True, selected_months=None):
    with st.spinner(f"Computing Labour Comparative Analysis..."):
        if df.empty:
            from ui.components.core import EmptyState
            EmptyState('No data available for the selected period. Adjust your filters or check data freshness.')
            return

    # 1. Workshop / Bodyshop Segmented Control
    st.markdown('<div class="section-title">🏭 Business Unit Filter</div>', unsafe_allow_html=True)
    if hasattr(st, "segmented_control"):
        ws_bs_filter = st.segmented_control("Business Unit Filter", ["All", "Workshop", "Bodyshop"], default="All", label_visibility="collapsed")
    else:
        ws_bs_filter = st.radio("Business Unit Filter", ["All", "Workshop", "Bodyshop"], horizontal=True, label_visibility="collapsed")
    
    if ws_bs_filter == "Workshop":
        df = apply_mp_pb_filter(df, "MP_PB", "MP")
    elif ws_bs_filter == "Bodyshop":
        df = apply_mp_pb_filter(df, "MP_PB", "PB")

    val_col = "Net_Labour"
    cp_months = selected_months if selected_months else []
    pp_months = [p[1] for p in pairs]
    
    cp = apply_month_filter(df, "Month Name", cp_months)
    pp = apply_month_filter(df, "Month Name", pp_months)

    mode_str = "YoY" if comparison_mode else "MoM"
    
    cp_val = cp[val_col].sum()
    pp_val = pp[val_col].sum()

    # Executive Explainability KPIs
    c1, c2, c3, c4 = st.columns(4)
    
    def kpi_with_explanation(col, label, value, current, previous, definition, formula, action=""):
        with col:
            st.metric(label, value, delta=fmt_pct(calc_growth_pct(current, previous, fill_value=0), True) if previous else None)
            if hasattr(st, "popover"):
                with st.popover("ⓘ Explanation"):
                    st.markdown(f"**Definition:** {definition}")
                    st.markdown(f"**Formula:** {formula}")
                    st.markdown(f"**Current:** {fmt_inr(current)} | **Previous:** {fmt_inr(previous)}")
                    if action: st.markdown(f"**Action:** {action}")
            else:
                with st.expander("ⓘ Explanation"):
                    st.markdown(f"**Definition:** {definition}")
                    st.markdown(f"**Formula:** {formula}")
                    st.markdown(f"**Current:** {fmt_inr(current)} | **Previous:** {fmt_inr(previous)}")

    kpi_with_explanation(c1, "CP Labour Revenue", fmt_inr(cp_val), cp_val, pp_val, "Total net labour revenue for the current selected period.", "Sum(Net_Labour)", "Monitor if below benchmark.")
    kpi_with_explanation(c2, "PP Labour Revenue", fmt_inr(pp_val), pp_val, 0, "Total net labour revenue for the prior matched period.", "Sum(Net_Labour PP)")
    
    # Highest Growth Component
    cp_locs = location_summary(cp, as_index=True)[val_col].sum()
    pp_locs = location_summary(pp, as_index=True)[val_col].sum()
    _df = pd.DataFrame({"CP": cp_locs, "PP": pp_locs}).fillna(0)
    _df["Growth"] = calc_growth_pct(_df["CP"], _df["PP"], fill_value=np.nan)
    valid_locs = _df[_df["PP"] > 10000]["Growth"].dropna()
    
    if not valid_locs.empty:
        best_loc = valid_locs.idxmax()
        best_growth = valid_locs.max()
        b_cp = _df.loc[best_loc, "CP"]
        b_pp = _df.loc[best_loc, "PP"]
        
        # Heuristic for business explanation
        loc_cp_svc = cp[cp["Location Name"] == best_loc].groupby("Service Type")[val_col].sum()
        loc_pp_svc = pp[pp["Location Name"] == best_loc].groupby("Service Type")[val_col].sum()
        svc_df = pd.DataFrame({"CP": loc_cp_svc, "PP": loc_pp_svc}).fillna(0)
        svc_df["Delta"] = svc_df["CP"] - svc_df["PP"]
        driver = svc_df["Delta"].idxmax() if not svc_df.empty else "general volume"
        
        with c3:
            st.metric(f"Highest Growth: {best_loc}", fmt_pct(best_growth, True))
            if hasattr(st, "popover"):
                with st.popover("ⓘ Details"):
                    st.markdown(f"**Current:** {fmt_inr(b_cp)} | **Previous:** {fmt_inr(b_pp)}")
                    st.markdown(f"**Business Explanation:** Growth primarily driven by higher `{driver}` billing.")
            else:
                with st.expander("ⓘ Details"):
                    st.markdown(f"**Current:** {fmt_inr(b_cp)} | **Previous:** {fmt_inr(b_pp)}")
                    st.markdown(f"**Business Explanation:** Growth primarily driven by higher `{driver}` billing.")

    st.markdown("---")
    
    # DYNAMIC COMPARISON TABLE WITH SPARKLINES
    st.markdown(f'<div class="section-title">📊 Executive Comparison Table — {mode_str}</div>', unsafe_allow_html=True)
    all_locs = sorted(set(cp["Location Name"].unique()) | set(pp["Location Name"].unique()))
    
    table_data = []
    
    for loc in all_locs:
        row = {"Location": loc}
        sparkline_data = []
        loc_cp_total = cp_locs.get(loc, 0)
        loc_pp_total = pp_locs.get(loc, 0)
        
        for cm, pm, _ in pairs:
            cv = cp[(cp["Location Name"] == loc) & (cp["Month Name"] == cm)][val_col].sum()
            pv = pp[(pp["Location Name"] == loc) & (pp["Month Name"] == pm)][val_col].sum()
            row[cm] = cv
            row[pm] = pv
            row[f"{cm[:3]} {mode_str}%"] = calc_growth_pct(cv, pv, fill_value=np.nan)
            sparkline_data.append(cv)
            
        row["CP Total"] = loc_cp_total
        row["PP Total"] = loc_pp_total
        row[f"Total {mode_str}%"] = calc_growth_pct(loc_cp_total, loc_pp_total, fill_value=np.nan)
        row["Contribution %"] = calc_ratio(loc_cp_total, cp_val, multiplier=100, fill_value=0)
        row["Trend"] = sparkline_data
        table_data.append(row)
        
    tdf = pd.DataFrame(table_data)
    
    # Configure Columns
    col_config = {
        "Location": st.column_config.TextColumn("Location"),
        "CP Total": st.column_config.NumberColumn("CP Total", format="₹%.0f"),
        "PP Total": st.column_config.NumberColumn("PP Total", format="₹%.0f"),
        f"Total {mode_str}%": st.column_config.NumberColumn(f"Total {mode_str}%", format="%.1f%%"),
        "Contribution %": st.column_config.ProgressColumn("Contribution %", format="%.1f%%", min_value=0, max_value=100),
        "Trend": st.column_config.LineChartColumn("Trend (CP)"),
    }
    
    for cm, pm, _ in pairs:
        col_config[cm] = st.column_config.NumberColumn(cm, format="₹%.0f")
        col_config[pm] = st.column_config.NumberColumn(pm, format="₹%.0f")
        col_config[f"{cm[:3]} {mode_str}%"] = st.column_config.NumberColumn(f"{cm[:3]} {mode_str}%", format="%.1f%%")
        
    st.dataframe(tdf, column_config=col_config, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # NEGATIVE LABOUR ALERT
    st.markdown(f'<div class="section-title">🔴 Negative Labour Alerts</div>', unsafe_allow_html=True)
    
    adv_cp = cp.groupby([ADV_COL, "Location Name", "Service Type"], as_index=False)[val_col].sum()
    adv_pp = pp.groupby([ADV_COL, "Location Name", "Service Type"], as_index=False)[val_col].sum()
    
    neg_advs = adv_cp[adv_cp[val_col] < 0].copy()
    if not neg_advs.empty:
        alert_rows = []
        for _, row in neg_advs.iterrows():
            adv = row[ADV_COL]
            loc = row["Location Name"]
            svc = row["Service Type"]
            cv = row[val_col]
            pv = adv_pp[(adv_pp[ADV_COL] == adv) & (adv_pp["Location Name"] == loc) & (adv_pp["Service Type"] == svc)][val_col].sum()
            variance = cv - pv
            alert_rows.append({
                "Advisor": adv,
                "Location": loc,
                "Service Type": svc,
                "Current Labour": cv,
                "Expected Labour": pv,
                "Variance": variance,
                "Reason": "Credits/Discounts exceeded gross generation",
                "Action": "Review open jobcards and applied discounts immediately"
            })
            
        alert_df = pd.DataFrame(alert_rows)
        ac_config = {
            "Current Labour": st.column_config.NumberColumn("Current", format="₹%.0f"),
            "Expected Labour": st.column_config.NumberColumn("Expected", format="₹%.0f"),
            "Variance": st.column_config.NumberColumn("Variance", format="₹%.0f")
        }
        st.dataframe(alert_df, column_config=ac_config, use_container_width=True, hide_index=True)
    else:
        st.success("No negative labour detected for the selected period.")

