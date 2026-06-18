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
from utils.constants import ADV_COL, WS_COLORS, LOC_COLORS, PLY

# Import shared UI helpers from app
from ui.kpi_cards import kpi
from ui.tables import html_table
from ui.traffic import yoy_badge, traffic_light, tgt_badge
from ui.helpers import apply_chart, clean_hover, _render_finding
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num

def render(df, pairs, comparison_mode=True, selected_months=None):
    with st.spinner("Computing Advisor Scorecard..."):
        if df.empty: return
    # df is already filtered by selected_months at main level, use it directly for current period
    cp = df.copy()
    
    # Min JC threshold
    min_jc = st.slider("Minimum JCs for ranking", 5, 100, 20, key="scorecard_min_jc")
    
    # Aggregate advisor metrics
    aa = advisor_summary(cp, adv_col=ADV_COL, as_index=False).agg(
        JCs=("JC_Nos.","sum"),
        NL=("Net_Labour","sum"),
        NP=("Net_Parts","sum"),
        OQ=("Oil_Sale_Qty","sum"),
        AS=("Accessory_Sale","sum"),
        DL=("Labour Discount","sum"),
        PL=("Pre-GST Labour","sum"),
        Loc=("Location Name", lambda x: ", ".join(sorted(x.unique())) if len(x.unique()) > 1 else x.iloc[0]),
        Loc_Count=("Location Name", "nunique"),
        Grp=("Location Group", "first")
    )
    
    # Filter by min JCs
    aa = aa[aa["JCs"] >= min_jc]
    
    if aa.empty:
        st.warning(f"No advisors with {min_jc}+ JCs in selected period")
        return
    
    # Compute metrics
    aa["Avg_Lab_JC"] = np.where(aa["JCs"]>0, aa["NL"]/aa["JCs"], 0)
    aa["Avg_Parts_JC"] = np.where(aa["JCs"]>0, aa["NP"]/aa["JCs"], 0)
    aa["Avg_Oil_JC"] = np.where(aa["JCs"]>0, aa["OQ"]/aa["JCs"], 0)
    aa["Avg_Acc_JC"] = np.where(aa["JCs"]>0, aa["AS"]/aa["JCs"], 0)
    aa["Lab_Disc_Pct"] = np.where(aa["PL"]>0, aa["DL"]/aa["PL"]*100, 0)
    
    # Score each metric (1-5 stars based on percentile)
    metrics = ["JCs", "Avg_Lab_JC", "Avg_Parts_JC", "Avg_Oil_JC", "Avg_Acc_JC"]
    for metric in metrics:
        aa[f"{metric}_score"] = np.ceil(aa[metric].rank(pct=True) * 5).clip(1, 5)
    
    # For discount, lower is better
    aa["Lab_Disc_Pct_score"] = np.ceil((1 - aa["Lab_Disc_Pct"].rank(pct=True)) * 5).clip(1, 5)
    
    # Composite score
    score_cols = [f"{m}_score" for m in metrics] + ["Lab_Disc_Pct_score"]
    aa["Composite_Score"] = aa[score_cols].mean(axis=1).round(1)
    
    # KPI cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Advisors", len(aa))
    with c2:
        st.metric("Avg Composite Score", f"{aa['Composite_Score'].mean():.1f}/5")
    with c3:
        top = aa.nlargest(1, "Composite_Score").iloc[0] if not aa.empty else None
        st.metric("Top Performer", f"{top[ADV_COL][:15]} ({top['Composite_Score']})" if top is not None else "N/A")
    with c4:
        st.metric("Ranked Advisors", f"{min_jc}+ JCs")
    
    # Scatter plot
    st.markdown('<div class="section-card"><div class="section-title">📊 Performance Scatter</div>', unsafe_allow_html=True)
    fig = px.scatter(
        aa, x="JCs", y="Avg_Lab_JC",
        size="Composite_Score", color="Grp",
        hover_name=ADV_COL,
        hover_data=["Composite_Score", "Lab_Disc_Pct"],
        color_discrete_map=LOC_COLORS,
        size_max=30
    )
    fig.update_layout(**PLY, height=400, xaxis_title="Total JCs", yaxis_title="Avg Labour / JC")
    st.plotly_chart(fig, width='stretch', key="scorecard_scatter",
                    config={"displayModeBar": True, "displaylogo": False,
                            "modeBarButtonsToRemove": ["select2d","lasso2d"],
                            "toImageButtonOptions": {"format":"png","scale":2}})
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Full table
    st.markdown('<div class="section-card"><div class="section-title">📋 Complete Scorecard</div>', unsafe_allow_html=True)
    
    aa_sorted = aa.sort_values("Composite_Score", ascending=False).reset_index(drop=True)
    aa_sorted["Rank"] = range(1, len(aa_sorted) + 1)
    
    # Rename column for display
    aa_sorted = aa_sorted.rename(columns={ADV_COL: "Advisor Name"})
    
    display_cols = ["Rank", "Advisor Name", "Loc", "Loc_Count", "JCs", "Avg_Lab_JC", "Avg_Parts_JC",
                     "Avg_Oil_JC", "Avg_Acc_JC", "Lab_Disc_Pct", "Composite_Score"]
    dt = aa_sorted[display_cols].copy()
    # Format Loc column: show "Multi (N)" if Loc_Count > 1
    dt["Loc"] = dt.apply(lambda r: f"Multi ({r['Loc_Count']})" if r['Loc_Count'] > 1 else r['Loc'], axis=1)
    dt = dt.drop(columns=["Loc_Count"])
    dt["JCs"] = dt["JCs"].apply(fmt_num)
    dt["Avg_Lab_JC"] = dt["Avg_Lab_JC"].apply(fmt_inr)
    dt["Avg_Parts_JC"] = dt["Avg_Parts_JC"].apply(fmt_inr)
    dt["Avg_Oil_JC"] = dt["Avg_Oil_JC"].apply(lambda x: f"{x:.1f}")
    dt["Avg_Acc_JC"] = dt["Avg_Acc_JC"].apply(fmt_inr)
    dt["Lab_Disc_Pct"] = dt["Lab_Disc_Pct"].apply(lambda x: f"{x:.1f}%")
    
    def score_cell(v):
        if v >= 4: return f'<span class="score-green">{v}</span>'
        if v >= 3: return f'<span class="score-yellow">{v}</span>'
        return f'<span class="score-red">{v}</span>'
    
    dt["Composite_Score"] = dt["Composite_Score"].apply(score_cell)
    
    html_table(dt, height="500px")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Advisor drill-down
    st.markdown('<div class="section-card"><div class="section-title">🔍 Advisor Drill-Down</div>', unsafe_allow_html=True)
    sel_adv = st.selectbox("Select Advisor", sorted(aa[ADV_COL].unique()), key="scorecard_drill")
    
    adv_data = cp[cp[ADV_COL] == sel_adv]
    if not adv_data.empty:
        adv_monthly = monthly_summary(adv_data, as_index=True).agg(
            JCs=("JC_Nos.","sum"),
            NL=("Net_Labour","sum"),
            NP=("Net_Parts","sum"),
            DL=("Labour Discount","sum"),
            PL=("Pre-GST Labour","sum")
        ).reset_index().sort_values("Month_Sort")
        adv_monthly["Lab_Disc_Pct"] = np.where(adv_monthly["PL"]>0, adv_monthly["DL"]/adv_monthly["PL"]*100, 0)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=adv_monthly["Month Name"], y=adv_monthly["NL"], name="Net Labour", mode='lines+markers'))
        fig.add_trace(go.Scatter(x=adv_monthly["Month Name"], y=adv_monthly["NP"], name="Net Parts", mode='lines+markers'))
        fig.update_layout(**PLY, height=300, xaxis_title="", yaxis_title="Amount (₹)")
        st.plotly_chart(fig, width='stretch', key="scorecard_drill_chart",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
    
    st.markdown('</div>', unsafe_allow_html=True)
