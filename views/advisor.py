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
from utils.constants import ADV_COL, MP_COLORS, LOC_COLORS, PLY, get_ply_layout

# Import new Phase B UI Components
from ui.components import KPIGrid, ChartCard, TableCard
from ui.tables import html_table
from ui.helpers import apply_chart, clean_hover
from ui.design_tokens import T

def render(df, pairs, comparison_mode=True, selected_months=None):
    with st.spinner("Computing Advisor Scorecard..."):
        if df.empty:
            from ui.components.core import EmptyState
            EmptyState('No data available for the selected period. Adjust your filters or check data freshness.')
            return
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
    
    # Filter by min JCs and exclude Unassigned
    aa = aa[(aa["JCs"] >= min_jc) & (aa[ADV_COL] != "Unassigned")]
    
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
    
    top = aa.nlargest(1, "Composite_Score").iloc[0] if not aa.empty else None
    KPIGrid([
        {"label": "Total Advisors", "value": str(len(aa))},
        {"label": "Avg Composite Score", "value": f"{aa['Composite_Score'].mean():.1f}/5"},
        {"label": "Top Performer", "value": f"{top[ADV_COL][:15]} ({top['Composite_Score']})" if top is not None else "N/A"},
        {"label": "Ranked Advisors", "value": f"{min_jc}+ JCs"}
    ])
    
    # Scatter plot
    st.markdown(f'<div style="margin-top:{T.SPACE_6}px;"></div>', unsafe_allow_html=True)
    fig = px.scatter(
        aa, x="JCs", y="Avg_Lab_JC",
        size="Composite_Score", color="Grp",
        hover_name=ADV_COL,
        hover_data=["Composite_Score", "Lab_Disc_Pct"],
        color_discrete_map=LOC_COLORS,
        size_max=30
    )
    fig.update_layout(**get_ply_layout(height=400, xaxis_title="Total JCs", yaxis_title="Avg Labour / JC"))
    ChartCard("📊 Performance Scatter", fig, height=400)
    
    # Full table
    st.markdown(f'<div style="margin-top:{T.SPACE_6}px;"></div>', unsafe_allow_html=True)
    
    
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
        if v >= 4: return f'🟢 {v}'
        if v >= 3: return f'🟡 {v}'
        return f'🔴 {v}'
    
    dt["Composite_Score"] = dt["Composite_Score"].apply(score_cell)
    
    TableCard(dt, height=500, index=False)
    
    # Advisor drill-down
    st.markdown(f'<div style="margin-top:{T.SPACE_6}px;"></div>', unsafe_allow_html=True)
    
    selected_advs = st.session_state.get("filter_advisor", [])
    if len(selected_advs) == 1:
        sel_adv = selected_advs[0]
        adv_data = cp[cp[ADV_COL] == sel_adv]
    else:
        st.info("Select exactly **one Advisor** from the Page Filters above to view the drill-down chart.")
        adv_data = pd.DataFrame()
        
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
        ChartCard(f"🔍 Drill-Down: {sel_adv}", fig, height=300)
