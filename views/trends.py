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
from ui.helpers import apply_chart, clean_hover, _render_finding
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num

def render(df, pairs, comparison_mode=True, selected_months=None):
    if df.empty: return
    
    # Auto Insights
    c1, c2 = st.columns([3, 7])
    with c1:
        st.markdown('<div class="section-card" style="height:100%"><div class="section-title">🤖 Auto Insights</div>', unsafe_allow_html=True)
        pp_months = [p[1] for p in pairs]
        # df is already filtered by selected_months at main level, use it directly for current period
        cp = df.copy()
        pp = apply_month_filter(df, "Month Name", pp_months)
        
        cpl = location_summary(cp, as_index=True)["Net_Labour"].sum()
        ppl = location_summary(pp, as_index=True)["Net_Labour"].sum()
        _df = pd.DataFrame({"CP": cpl, "PP": ppl}).fillna(0)
        _df["YoY"] = calc_growth_pct(_df["CP"], _df["PP"], fill_value=np.nan)
        yoy_valid = _df[_df["PP"] > 10000]["YoY"].dropna()
        
        if not yoy_valid.empty:
            b = yoy_valid.idxmax() if not getattr(locals().get('cp', None), 'empty', True) else "N/A" if not yoy_valid.empty else "N/A"
            if b != "N/A":
                st.markdown(f'<div class="insight-card pos"><div class="insight-title">🏆 Best Performer</div><div class="insight-stat">{b} leads with +{yoy_valid[b]:.1f}% YoY labour growth</div></div>', unsafe_allow_html=True)
            w = yoy_valid.idxmin() if not yoy_valid.empty else "N/A"
            if w != "N/A" and yoy_valid[w] < 0:
                st.markdown(f'<div class="insight-card neg"><div class="insight-title">⚠️ Needs Attention</div><div class="insight-stat">{w} declined {abs(yoy_valid[w]):.1f}% YoY</div></div>', unsafe_allow_html=True)
        
        adv = advisor_summary(cp, adv_col=ADV_COL, as_index=False).agg(L=("Pre-GST Labour","sum"), D=("Labour Discount","sum"))
        adv["D%"] = np.where(adv["L"]>0, adv["D"]/adv["L"]*100, 0)
        if not adv.empty:
            wa = adv.sort_values("D%", ascending=False).iloc[0]
            st.markdown(f'<div class="insight-card warn"><div class="insight-title">💰 High Discount</div><div class="insight-stat">{wa[ADV_COL]} at {wa["D%"]:.1f}% labour discount</div></div>', unsafe_allow_html=True)
            
        la = location_summary(cp, as_index=False).agg(J=("JC_Nos.","sum"), L=("Net_Labour","sum"))
        la["A"] = np.where(la["J"]>0, la["L"]/la["J"], 0)
        if not la.empty:
            ba = la.sort_values("A", ascending=False).iloc[0]
            st.markdown(f'<div class="insight-card pos"><div class="insight-title">⭐ Top Avg/JC</div><div class="insight-stat">{ba["Location Name"]} achieves {fmt_inr(ba["A"])} avg labour/JC</div></div>', unsafe_allow_html=True)
            
        mt = monthly_summary(cp, as_index=True)["Net_Labour"].sum().reset_index()
        if not mt.empty:
            bm = mt.sort_values("Net_Labour", ascending=False).iloc[0]
            st.markdown(f'<div class="insight-card"><div class="insight-title">📈 Peak Month</div><div class="insight-stat">{bm["Month Name"]} was strongest at {fmt_inr(bm["Net_Labour"])}</div></div>', unsafe_allow_html=True)
            
        new_locs = ppl[ppl == 0].index.tolist()
        if new_locs:
            st.markdown(f'<div class="insight-card"><div class="insight-title">🆕 New Locations</div><div class="insight-stat">{len(new_locs)} added this FY: {", ".join(new_locs[:3])}{"..." if len(new_locs)>3 else ""}</div></div>', unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c2:
        st.markdown('<div class="section-card"><div class="section-title">📊 YoY Comparison Area</div>', unsafe_allow_html=True)
        both = pd.concat([cp.assign(P="This FY"), pp.assign(P="Last FY")])
        tr = both.groupby(["Month_Sort", "Month Name", "P"], as_index=False, dropna=False)["Net_Labour"].sum().sort_values("Month_Sort")
        fig = px.area(tr, x="Month Name", y="Net_Labour", color="P", color_discrete_map={"This FY":C["primary"], "Last FY":C["gold"]})
        fig.update_layout(**PLY); fig.update_layout(height=450, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, width='stretch', key="tr_area",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
        st.markdown('</div>', unsafe_allow_html=True)
        
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-card"><div class="section-title">📈 MoM Labour Growth %</div>', unsafe_allow_html=True)
        mom = both.groupby(["P", "Month_Sort", "Month Name"], as_index=False, dropna=False)["Net_Labour"].sum()
        mom = mom.sort_values(["P", "Month_Sort"])
        mom["MoM"] = mom.groupby("P", dropna=False)["Net_Labour"].pct_change() * 100
        fig = px.bar(mom, x="Month Name", y="MoM", color="P", barmode="group", color_discrete_map={"This FY":C["green"], "Last FY":C["gray"]})
        fig.update_layout(**PLY); fig.update_layout(height=300, xaxis_title="", yaxis_title="% Growth")
        st.plotly_chart(fig, width='stretch', key="tr_mom",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="section-card"><div class="section-title">⚖️ L100P Location × Month</div>', unsafe_allow_html=True)
        l1 = cp.groupby(["Location Name", "Month_Sort", "Month Name"], as_index=False, dropna=False).agg(NL=("Net_Labour","sum"), NP=("Net_Parts","sum")).sort_values("Month_Sort")
        l1["L100P"] = np.where(l1["NP"]>0, l1["NL"]/l1["NP"]*100, 0)
        fig = px.line(l1, x="Month Name", y="L100P", color="Location Name", markers=True)
        fig.add_hline(y=100, line_dash="dash", line_color=C["red"])
        fig.update_layout(**PLY); fig.update_layout(height=300, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, width='stretch', key="tr_l100p",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown('<div class="section-card"><div class="section-title">🏢 WS vs BS Trend (Stacked Area)</div>', unsafe_allow_html=True)
    wbs = cp.groupby(["Month_Sort", "Month Name", "MP_PB"], as_index=False, dropna=False)["Net_Labour"].sum().sort_values("Month_Sort")
    fig = px.area(wbs, x="Month Name", y="Net_Labour", color="MP_PB", color_discrete_map=MP_COLORS)
    fig.update_layout(**PLY); fig.update_layout(height=350, xaxis_title="", yaxis_title="")
    st.plotly_chart(fig, width='stretch', key="tr_wsbs",
                    config={"displayModeBar": True, "displaylogo": False,
                            "modeBarButtonsToRemove": ["select2d","lasso2d"],
                            "toImageButtonOptions": {"format":"png","scale":2}})
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Forecasting Section
    st.markdown('<div class="forecast-card"><div class="section-title">📈 3-Month Forecast (Linear Trend)</div>', unsafe_allow_html=True)

    def forecast_metric(df, metric_col, n_forecast=3):
        hist = df.groupby('Month_Sort', dropna=False)[metric_col].sum().reset_index().sort_values('Month_Sort')
        hist = hist.tail(12)
        if len(hist) < 6:
            return None, None
        X = hist['Month_Sort'].values.reshape(-1, 1)
        y = hist[metric_col].values
        model = LinearRegression().fit(X, y)
        last_sort = hist['Month_Sort'].max()
        future_sorts = np.array([[last_sort + i] for i in range(1, n_forecast + 1)])
        predictions = model.predict(future_sorts)
        sort_to_month = {v: k for k, v in MONTH_SORT_ORDER.items()}
        future_months = [sort_to_month.get(int(s[0]), f"M+{i+1}") for i, s in enumerate(future_sorts)]
        return future_months, predictions.clip(min=0)
    
    metrics_to_forecast = ["JC_Nos.", "Net_Labour", "Total Margin"]
    forecast_data = []
    
    for metric in metrics_to_forecast:
        # Pass full df to forecast, not just cp slice
        future_months, predictions = forecast_metric(df, metric)
        if future_months:
            for m, p in zip(future_months, predictions):
                forecast_data.append({"Month": m, "Metric": metric, "Value": p})
    
    if forecast_data:
        forecast_df = pd.DataFrame(forecast_data)
        
        # Combined chart
        st.markdown('<div style="margin-bottom:16px;">', unsafe_allow_html=True)
        fig = go.Figure()
        
        for metric in metrics_to_forecast:
            hist = cp.groupby('Month_Sort', dropna=False)[metric].sum().reset_index().sort_values('Month_Sort').tail(12)
            fig.add_trace(go.Scatter(
                x=hist['Month_Sort'],
                y=hist[metric],
                name=f"{metric} (Actual)",
                mode='lines+markers',
                line=dict(width=2)
            ))
            
            forecast_subset = forecast_df[forecast_df['Metric'] == metric]
            if not forecast_subset.empty:
                last_hist_sort = hist['Month_Sort'].max()
                last_hist_val = hist[metric].iloc[-1]
                forecast_x = [last_hist_sort] + list(range(last_hist_sort + 1, last_hist_sort + 4))
                forecast_y = [last_hist_val] + forecast_subset['Value'].tolist()
                fig.add_trace(go.Scatter(
                    x=forecast_x,
                    y=forecast_y,
                    name=f"{metric} (Forecast)",
                    mode='lines+markers',
                    line=dict(width=2, dash='dash'),
                    opacity=0.7
                ))
        
        fig.update_layout(**PLY, height=350, xaxis_title="", yaxis_title="Value", hovermode="x unified")
        st.plotly_chart(fig, width='stretch', key="tr_forecast",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Forecast KPI cards
        st.markdown('<p class="forecast-note">Simple linear projection. Actual results may vary based on seasonality.</p>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        for i, metric in enumerate(metrics_to_forecast):
            with [c1, c2, c3][i]:
                forecast_subset = forecast_df[forecast_df['Metric'] == metric]
                if not forecast_subset.empty:
                    st.markdown(f"**{metric.replace('_', ' ')} Forecast**", unsafe_allow_html=True)
                    for _, row in forecast_subset.iterrows():
                        st.markdown(f"<div style='font-size:14px;font-weight:600;'>{row['Month']}: {fmt_inr(row['Value'])}</div>", unsafe_allow_html=True)
    else:
        st.info("Insufficient data for forecasting (need at least 6 months of data)")
    
    st.markdown('</div>', unsafe_allow_html=True)
