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
from utils.constants import ADV_COL, MP_COLORS, C, LOC_COLORS, PLY

# Import shared UI helpers from app
from ui.kpi_cards import kpi
from ui.tables import html_table
from ui.traffic import yoy_badge, traffic_light, tgt_badge
from ui.helpers import apply_chart, clean_hover, _render_finding
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num

def render(df, pairs, comparison_mode=True, selected_months=None):
    if df.empty:
        from ui.components.core import EmptyState
        EmptyState('No data available for the selected period. Adjust your filters or check data freshness.')
        return
    pp_months = [p[1] for p in pairs]
    # df is already filtered by selected_months at main level, use it directly for current period
    cp = df.copy()
    pp = apply_month_filter(df, "Month Name", pp_months)
    
    # Location aggregates
    loc_cp = location_summary(cp, as_index=True).agg(
        JCs=("JC_Nos.","sum"),
        NL=("Net_Labour","sum"),
        M=("Total Margin","sum"),
        DL=("Labour Discount","sum"),
        PL=("Pre-GST Labour","sum"),
        Grp=("Location Group", "first")
    ).reset_index()
    
    loc_pp = location_summary(pp, as_index=True)["Net_Labour"].sum().reset_index()
    loc_pp.columns = ["Location Name", "PP_NL"]
    
    loc_data = loc_cp.merge(loc_pp, on="Location Name", how="left")
    loc_data["PP_NL"] = loc_data["PP_NL"].fillna(0)
    loc_data["Disc_Pct"] = np.where(loc_data["PL"]>0, loc_data["DL"]/loc_data["PL"]*100, 0)
    loc_data["YoY_Pct"] = np.where(loc_data["PP_NL"]>0, (loc_data["NL"]-loc_data["PP_NL"])/loc_data["PP_NL"]*100, 0)
    
    # Top advisor per location
    top_advs = cp.groupby(["Location Name", ADV_COL], dropna=False)["JC_Nos."].sum().reset_index()
    top_advs = top_advs.sort_values(["Location Name", "JC_Nos."], ascending=[True, False]).groupby("Location Name", dropna=False).first().reset_index()
    top_advs.columns = ["Location Name", "Top_Advisor", "Top_Adv_JCs"]
    
    loc_data = loc_data.merge(top_advs, on="Location Name", how="left")
    
    # Health indicator
    def health_status(row):
        yoy_ok = row["YoY_Pct"] > 0
        disc_ok = row["Disc_Pct"] < 25
        if yoy_ok and disc_ok: return ("🟢", "green")
        if (row["YoY_Pct"] >= -10 and row["YoY_Pct"] <= 0) or (row["Disc_Pct"] >= 25 and row["Disc_Pct"] <= 35): return ("🟡", "yellow")
        return ("🔴", "red")
    
    health_results = loc_data.apply(lambda row: pd.Series(health_status(row)), axis=1, result_type='expand')
    if not health_results.empty:
        loc_data[["Health_Icon", "Health_Color"]] = health_results
    else:
        loc_data["Health_Icon"] = "🔴"
        loc_data["Health_Color"] = "red"
    
    # Sort control
    sort_by = st.radio("Sort by", ["Net Labour", "YoY%", "Discount%", "Health Status"], horizontal=True, key="loc_health_sort")
    
    if sort_by == "Net Labour":
        loc_data = loc_data.sort_values("NL", ascending=False)
    elif sort_by == "YoY%":
        loc_data = loc_data.sort_values("YoY_Pct", ascending=False)
    elif sort_by == "Discount%":
        loc_data = loc_data.sort_values("Disc_Pct", ascending=True)
    else:
        loc_data = loc_data.sort_values("Health_Color")
    
    # Render cards
    st.markdown('<div style="margin-bottom:16px;">', unsafe_allow_html=True)
    for i in range(0, len(loc_data), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(loc_data):
                loc = loc_data.iloc[i + j]
                with cols[j]:
                    card_html = f"""
                    <div class="loc-card">
                        <div class="loc-card-title">{loc['Location Name']} <span style="font-size:12px;font-weight:500;color:#6E6E73;">({loc['Grp']})</span></div>
                        <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                            <div>
                                <div class="loc-metric">JCs</div>
                                <div class="loc-metric-val">{fmt_num(loc['JCs'])}</div>
                            </div>
                            <div>
                                <div class="loc-metric">Net Labour</div>
                                <div class="loc-metric-val">{fmt_inr(loc['NL'])}</div>
                            </div>
                            <div>
                                <div class="loc-metric">Margin</div>
                                <div class="loc-metric-val">{fmt_inr(loc['M'])}</div>
                            </div>
                        </div>
                        <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                            <div>
                                <div class="loc-metric">Disc%</div>
                                <div class="loc-metric-val">{loc['Disc_Pct']:.1f}%</div>
                            </div>
                            <div>
                                <div class="loc-metric">Top Advisor</div>
                                <div class="loc-metric-val">{loc['Top_Advisor'][:12] if pd.notna(loc['Top_Advisor']) else 'N/A'}</div>
                            </div>
                        </div>
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div>
                                <div class="loc-metric">YoY Labour</div>
                                <div class="loc-metric-val" style="color:{C['green'] if loc['YoY_Pct']>=0 else C['red']}">
                                    {'▲' if loc['YoY_Pct']>=0 else '▼'} {abs(loc['YoY_Pct']):.1f}%
                                </div>
                            </div>
                            <div style="font-size:20px;">{loc['Health_Icon']}</div>
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
                    if st.button(f"View {loc['Location Name']}", key=f"loc_btn_{loc['Location Name']}", width='stretch'):
                        st.session_state.filter_location = [loc['Location Name']]
                        st.session_state.filter_loc_group = []
                        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Location ranking chart
    st.markdown('<div class="section-card"><div class="section-title">📊 Location Ranking by Net Labour</div>', unsafe_allow_html=True)
    fig = px.bar(loc_data, x="NL", y="Location Name", orientation="h", color="Grp", color_discrete_map=LOC_COLORS)
    fig.update_layout(**PLY, height=400, xaxis_title="", yaxis_title="")
    st.plotly_chart(fig, width='stretch', key="loc_health_rank",
                    config={"displayModeBar": True, "displaylogo": False,
                            "modeBarButtonsToRemove": ["select2d","lasso2d"],
                            "toImageButtonOptions": {"format":"png","scale":2}})
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Arena vs Nexa comparison
    st.markdown('<div class="section-card"><div class="section-title">⚖️ Arena vs Nexa Comparison</div>', unsafe_allow_html=True)
    group_comp = loc_data.groupby("Grp", dropna=False).agg(
        JCs=("JCs","sum"),
        NL=("NL","sum"),
        M=("M","sum")
    ).reset_index()
    
    c1, c2, c3 = st.columns(3)
    with c1:
        fig = px.bar(group_comp, x="Grp", y="JCs", color="Grp", color_discrete_map=LOC_COLORS)
        fig.update_layout(**PLY, height=250, xaxis_title="", yaxis_title="JCs", showlegend=False)
        st.plotly_chart(fig, width='stretch', key="loc_health_comp_jc",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
    with c2:
        fig = px.bar(group_comp, x="Grp", y="NL", color="Grp", color_discrete_map=LOC_COLORS)
        fig.update_layout(**PLY, height=250, xaxis_title="", yaxis_title="Net Labour", showlegend=False)
        st.plotly_chart(fig, width='stretch', key="loc_health_comp_lab",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
    with c3:
        fig = px.bar(group_comp, x="Grp", y="M", color="Grp", color_discrete_map=LOC_COLORS)
        fig.update_layout(**PLY, height=250, xaxis_title="", yaxis_title="Margin", showlegend=False)
        st.plotly_chart(fig, width='stretch', key="loc_health_comp_mar",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
    
    st.markdown('</div>', unsafe_allow_html=True)
