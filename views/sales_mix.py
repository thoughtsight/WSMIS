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
    apply_service_type_filter, apply_advisor_filter, apply_ws_bs_filter, split_cp_pp
)
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num
from utils.constants import ADV_COL, WS_COLORS, C, PLY

# Import shared UI helpers from app
from ui.kpi_cards import kpi
from ui.tables import html_table
from ui.traffic import yoy_badge, traffic_light, tgt_badge
from ui.helpers import apply_chart, clean_hover, _render_finding
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num

def render(df, pairs, comparison_mode=True, selected_months=None):
    if df.empty: return
    # df is already filtered by selected_months at main level, use it directly for current period
    cp = df.copy()
    
    c = st.columns(4)
    with c[0]:
        kpi("Oil ₹", fmt_inr(get_oil_sales(cp)))
        kpi("Oil Ltrs", fmt_num(cp["Oil_Sale_Qty"].sum()))
    with c[1]:
        kpi("Tyre ₹", fmt_inr(get_tyre_sales(cp)))
        kpi("Tyre Nos", fmt_num(cp["Tyre_Sale_Qty"].sum()))
    with c[2]:
        kpi("Battery ₹", fmt_inr(get_battery_sales(cp)))
        kpi("Battery Nos", fmt_num(cp["Battery_Sale_Qty"].sum()))
    with c[3]:
        kpi("Accessory ₹", fmt_inr(get_accessory_sales(cp)))
        kpi("Parts Sale ₹", fmt_inr(cp["Parts_Sale"].sum()))
        
    def render_tbl(col, title):
        mo = cp.drop_duplicates("Month Name").sort_values("Month_Sort")["Month Name"].tolist()
        pvt = cp.groupby(["Location Name","Month Name"], dropna=False)[col].sum().reset_index()
        pvt = pvt.pivot_table(index="Location Name", columns="Month Name", values=col, aggfunc="sum").fillna(0)
        pvt = pvt.reindex(columns=[m for m in mo if m in pvt.columns])
        pvt["Total"] = pvt.sum(axis=1)
        tot = pd.DataFrame(pvt.sum()).T; tot.index = ["TOTAL"]
        dp = pd.concat([pvt, tot]).reset_index().rename(columns={"index":"Location"})
        for col_name in dp.columns[1:]: dp[col_name] = dp[col_name].apply(fmt_inr)
        st.markdown(f'<div class="section-card"><div class="section-title">{title}</div>', unsafe_allow_html=True)
        html_table(dp, total_row=True, height="250px")
        st.markdown('</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1: render_tbl("Oil_Sale", "🛢️ Oil Sales")
    with c2: render_tbl("Battery_Sale", "🔋 Battery Sales")
    c1, c2 = st.columns(2)
    with c1: render_tbl("Tyre_Sale", "🛞 Tyre Sales")
    with c2: render_tbl("Accessory_Sale", "🎀 Accessory Sales")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="section-card"><div class="section-title">Oil Trend</div>', unsafe_allow_html=True)
        ot = monthly_summary(cp, as_index=False).agg(S=("Oil_Sale","sum"), Q=("Oil_Sale_Qty","sum")).sort_values("Month_Sort")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=ot["Month Name"], y=ot["S"], name="₹", marker_color=C["primary"]))
        fig.add_trace(go.Scatter(x=ot["Month Name"], y=ot["Q"], name="Ltrs", yaxis="y2", marker_color=C["orange"], mode="lines+markers"))
        fig.update_layout(**PLY); fig.update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0), yaxis2=dict(overlaying="y", side="right"), showlegend=False)
        st.plotly_chart(fig, width='stretch', key="sm_oil",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="section-card"><div class="section-title">Batt + Tyre</div>', unsafe_allow_html=True)
        bt = monthly_summary(cp, as_index=False).agg(B=("Battery_Sale","sum"), T=("Tyre_Sale","sum")).sort_values("Month_Sort")
        fig = px.bar(bt, x="Month Name", y=["B", "T"], barmode="group", color_discrete_sequence=[C["green"], C["purple"]])
        fig.update_layout(**PLY); fig.update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
        st.plotly_chart(fig, width='stretch', key="sm_bt",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="section-card"><div class="section-title">Oil Ranking</div>', unsafe_allow_html=True)
        orank = location_summary(cp, as_index=False)["Oil_Sale"].sum().sort_values("Oil_Sale", ascending=True).tail(10)
        fig = px.bar(orank, x="Oil_Sale", y="Location Name", orientation="h", color_discrete_sequence=[C["primary"]])
        fig.update_layout(**PLY); fig.update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0), xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, width='stretch', key="sm_or",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
        st.markdown('</div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="section-card"><div class="section-title">Mix (Acc vs Pts)</div>', unsafe_allow_html=True)
        md = pd.DataFrame({"Cat": ["Accessory", "Parts"], "Val": [get_accessory_sales(cp), cp["Parts_Sale"].sum()]})
        fig = px.pie(md, values="Val", names="Cat", hole=0.6, color_discrete_sequence=[C["pink"], C["teal"]])
        fig.update_layout(**PLY); fig.update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, width='stretch', key="sm_mix",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Oil deep-dive
    st.markdown('<div class="section-card"><div class="section-title">🛢️ Oil Revenue per Litre by Location</div>', unsafe_allow_html=True)
    oil_per_litre = location_summary(cp, as_index=True).agg(S=("Oil_Sale","sum"), Q=("Oil_Sale_Qty","sum")).reset_index()
    oil_per_litre["Per Litre"] = np.where(oil_per_litre["Q"]>0, oil_per_litre["S"]/oil_per_litre["Q"], 0)
    oil_per_litre = oil_per_litre.sort_values("Per Litre", ascending=False)
    fig = px.bar(oil_per_litre, x="Per Litre", y="Location Name", orientation="h", color_discrete_sequence=[C["primary"]])
    fig.update_layout(**PLY); fig.update_layout(height=300, xaxis_title="₹ per Litre", yaxis_title="")
    st.plotly_chart(fig, width='stretch', key="sm_oil_per_litre",
                    config={"displayModeBar": True, "displaylogo": False,
                            "modeBarButtonsToRemove": ["select2d","lasso2d"],
                            "toImageButtonOptions": {"format":"png","scale":2}})
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Consumables Margin%
    st.markdown('<div class="section-card"><div class="section-title">📊 Consumables Margin %</div>', unsafe_allow_html=True)
    c_cols = ["Oil_Margin", "Battery_Margin", "Tyre_Margin"]
    c_sums = cp[[c for c in c_cols if c in cp.columns]].sum()
    cons_margin = pd.DataFrame({
        "Category": ["Oil", "Battery", "Tyre"],
        "Margin%": [
            calc_ratio(c_sums.get("Oil_Margin", 0), get_oil_sales(cp), multiplier=100, fill_value=0),
            calc_ratio(c_sums.get("Battery_Margin", 0), get_battery_sales(cp), multiplier=100, fill_value=0),
            calc_ratio(c_sums.get("Tyre_Margin", 0), get_tyre_sales(cp), multiplier=100, fill_value=0)
        ]
    })
    fig = px.bar(cons_margin, x="Category", y="Margin%", color_discrete_sequence=[C["green"], C["orange"], C["purple"]])
    fig.update_layout(**PLY); fig.update_layout(height=300, xaxis_title="", yaxis_title="Margin %")
    st.plotly_chart(fig, width='stretch', key="sm_cons_margin",
                    config={"displayModeBar": True, "displaylogo": False,
                            "modeBarButtonsToRemove": ["select2d","lasso2d"],
                            "toImageButtonOptions": {"format":"png","scale":2}})
    st.markdown('</div>', unsafe_allow_html=True)
