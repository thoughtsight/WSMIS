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
from utils.constants import ADV_COL, MP_COLORS, C

# Import new Phase B UI Components
from ui.components import PageHeader, KPIGrid, ChartCard, TableCard

def render(df, pairs, comparison_mode=True, selected_months=None):
    with st.spinner("Loading Discount..."): pass
    if df.empty:
        from ui.components.core import EmptyState
        EmptyState('No data available for the selected period. Adjust your filters or check data freshness.')
        return

    # Use global period selection for consistency
    cp_months = [p[0] for p in pairs]
    pp_months = [p[1] for p in pairs]

    # If no pairs available, use selected_months for CP only
    if not cp_months and selected_months:
        disc_cp_months = selected_months
        disc_pp_months = []
    else:
        disc_cp_months = cp_months
        disc_pp_months = pp_months

    disc_cp = apply_month_filter(df, "Month Name", disc_cp_months)
    disc_pp = apply_month_filter(df, "Month Name", disc_pp_months)
    if disc_cp.empty:
        st.warning("No data for the selected discount period.")
        return

    cl = get_labour_discount(disc_cp)
    pl = get_labour_discount(disc_pp) if not disc_pp.empty else 0
    clp = calc_contribution_pct(cl, get_labour_sales(disc_cp), fill_value=0)
    plp = calc_contribution_pct(pl, get_labour_sales(disc_pp), fill_value=0)
    cpd = calculate_parts_discount(disc_cp)
    ppd = calculate_parts_discount(disc_pp) if not disc_pp.empty else 0
    cpp = calc_contribution_pct(cpd, get_parts_sales(disc_cp), fill_value=0)
    ppp = calc_contribution_pct(ppd, get_parts_sales(disc_pp), fill_value=0)

    PageHeader("Discount Analysis", icon="🏷️")
    KPIGrid([
        {"label": "Labour Disc Rs", "value": fmt_inr(cl), "cp": cl, "pp": pl, "invert_trend": True},
        {"label": "Labour Disc %", "value": f"{clp:.2f}%", "cp": clp, "pp": plp, "invert_trend": True},
        {"label": "Parts Disc Rs", "value": fmt_inr(cpd), "cp": cpd, "pp": ppd, "invert_trend": True},
        {"label": "Parts Disc %", "value": f"{cpp:.2f}%", "cp": cpp, "pp": ppp, "invert_trend": True}
    ])

    # Rolling trend
    st.markdown('<div style="margin-top:24px;"></div>', unsafe_allow_html=True)
    disc_trend = monthly_summary(disc_cp, as_index=False).agg(L=("Pre-GST Labour","sum"), D=("Labour Discount","sum")).sort_values("Month_Sort")
    disc_trend["D%"] = np.where(disc_trend["L"]>0, disc_trend["D"]/disc_trend["L"]*100, 0)
    disc_trend["Rolling3M"] = disc_trend["D%"].rolling(3, min_periods=1).mean()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=disc_trend["Month Name"], y=disc_trend["D%"], name="Monthly D%", marker_color=C["primary"]))
    fig.add_trace(go.Scatter(x=disc_trend["Month Name"], y=disc_trend["Rolling3M"], name="3M Rolling Avg", mode='lines+markers', line=dict(color=C["orange"])))
    fig.add_hline(y=15, line_dash="dash", line_color=C["red"], annotation_text="15% Benchmark")
    ChartCard("📉 Labour Discount % Trend", fig, height=350)

    # Heatmap toggle
    st.markdown('<div style="margin-top:24px;"></div>', unsafe_allow_html=True)
    heat_view = st.radio("Heatmap View", ["By Location", "By Advisor"], horizontal=True, key="heat_view")
    if heat_view == "By Location":
        hd = disc_cp.groupby(["Location Name","Month Name","Month_Sort"], as_index=False, dropna=False).agg(L=("Pre-GST Labour","sum"), D=("Labour Discount","sum"))
        hd["D%"] = np.where(hd["L"]>0, hd["D"]/hd["L"]*100, 0)
        hd = hd.sort_values("Month_Sort")
        hp = hd.pivot_table(index="Location Name", columns="Month Name", values="D%", aggfunc="mean").fillna(0)
        fig = px.imshow(hp.values, x=hp.columns.tolist(), y=hp.index.tolist(), color_continuous_scale=["#E8F9EE","#FFF3E0","#FFEBE9"], aspect="auto")
    else:
        top20 = advisor_summary(disc_cp, adv_col=ADV_COL, as_index=True)["Pre-GST Labour"].sum().nlargest(20).index.tolist()
        ha = disc_cp[disc_cp[ADV_COL].isin(top20)].groupby([ADV_COL,"Month Name","Month_Sort"], as_index=False, dropna=False).agg(L=("Pre-GST Labour","sum"), D=("Labour Discount","sum"))
        ha["D%"] = np.where(ha["L"]>0, ha["D"]/ha["L"]*100, 0)
        ha = ha.sort_values("Month_Sort")
        hp = ha.pivot_table(index=ADV_COL, columns="Month Name", values="D%", aggfunc="mean").fillna(0)
        fig = px.imshow(hp.values, x=hp.columns.tolist(), y=hp.index.tolist(), color_continuous_scale=["#E8F9EE","#FFF3E0","#FFEBE9"], aspect="auto")
    ChartCard("🗺️ Discount% Heatmap", fig, height=350)

    # Delta table
    st.markdown('<div style="margin-top:24px;"></div>', unsafe_allow_html=True)
    PageHeader("Discount Leakage Delta Table", icon="⚠️")
    cp_adv = advisor_summary(disc_cp, adv_col=ADV_COL, as_index=True).agg(L=("Pre-GST Labour","sum"), D=("Labour Discount","sum")).reset_index()
    cp_adv["D%"] = np.where(cp_adv["L"]>0, cp_adv["D"]/cp_adv["L"]*100, 0)
    cp_adv["Leakage"] = np.maximum(0, (cp_adv["D%"] - 15) / 100 * cp_adv["L"])
    if not disc_pp.empty:
        pp_adv = advisor_summary(disc_pp, adv_col=ADV_COL, as_index=True).agg(L=("Pre-GST Labour","sum"), D=("Labour Discount","sum")).reset_index()
        pp_adv["D%"] = np.where(pp_adv["L"]>0, pp_adv["D"]/pp_adv["L"]*100, 0)
        pp_adv["Leakage"] = np.maximum(0, (pp_adv["D%"] - 15) / 100 * pp_adv["L"])
        merged = cp_adv.merge(pp_adv, on=ADV_COL, suffixes=("_CP","_PP"), how="outer").fillna(0)
        merged["Delta"] = merged["D%_CP"] - merged["D%_PP"]
        merged["Leakage_Delta"] = merged["Leakage_CP"] - merged["Leakage_PP"]
        merged = merged.sort_values("Leakage_Delta", ascending=False)
        dt = pd.DataFrame({
            "Advisor": merged[ADV_COL],
            "CP Disc%": merged["D%_CP"].round(2),
            "PP Disc%": merged["D%_PP"].round(2),
            "Delta": merged["Delta"].round(2),
            "CP Leakage": merged["Leakage_CP"].apply(fmt_inr),
            "PP Leakage": merged["Leakage_PP"].apply(fmt_inr),
            "Leakage Δ": merged["Leakage_Delta"].apply(fmt_inr),
        })
    else:
        cp_adv["Delta"] = 0
        cp_adv["Leakage_Delta"] = 0
        dt = pd.DataFrame({
            "Advisor": cp_adv[ADV_COL],
            "CP Disc%": cp_adv["D%"].round(2),
            "PP Disc%": "N/A",
            "Delta": "N/A",
            "CP Leakage": cp_adv["Leakage"].apply(fmt_inr),
            "PP Leakage": "N/A",
            "Leakage Δ": "N/A",
        })
    TableCard(dt, height=400, index=False)
