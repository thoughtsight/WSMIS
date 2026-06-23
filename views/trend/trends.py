from views.shared import *
from views.components.kpi_engine import KPIEngine
from views.components.chart_engine import ChartEngine
from views.dashboard_common import inject_responsive_css




from sklearn.linear_model import LinearRegression

# Import shared UI helpers from app
from ui.traffic import yoy_badge, traffic_light, tgt_badge
from ui.design_tokens import T

def render(df, pairs, comparison_mode=True, selected_months=None):
    inject_responsive_css()
    PageBreadcrumb(["Performance", "Trends"])
    if df.empty:
        EmptyState('No data available for the selected period. Adjust your filters or check data freshness.')
        return
    
    # Auto Insights
    c1, c2 = st.columns([3, 7])
    with c1:
        section_title("🤖 Auto Insights")
        pp_months = [p[1] for p in pairs]
        # df is already filtered by selected_months at main level, use it directly for current period
        cp = df
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
            
        
    with c2:
        section_title("📊 YoY Comparison Area")
        both = pd.concat([cp.assign(P="This FY"), pp.assign(P="Last FY")])
        tr = both.groupby(["Month_Sort", "Month Name", "P"], as_index=False, dropna=False)["Net_Labour"].sum().sort_values("Month_Sort")
        fig = px.area(tr, x="Month Name", y="Net_Labour", color="P", color_discrete_map={"This FY":C["primary"], "Last FY":C["gold"]})
        fig.update_layout(**get_ply_layout(height=450, xaxis_title="", yaxis_title=""))
        st.plotly_chart(fig, width='stretch', key="tr_area",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
        
    c1, c2 = st.columns(2)
    with c1:
        section_title("📈 MoM Labour Growth %")
        mom = both.groupby(["P", "Month_Sort", "Month Name"], as_index=False, dropna=False)["Net_Labour"].sum()
        mom = mom.sort_values(["P", "Month_Sort"])
        mom["MoM"] = mom.groupby("P", dropna=False)["Net_Labour"].pct_change() * 100
        fig = px.bar(mom, x="Month Name", y="MoM", color="P", barmode="group", color_discrete_map={"This FY":C["green"], "Last FY":C["gray"]})
        fig.update_layout(**get_ply_layout(height=300, xaxis_title="", yaxis_title="% Growth"))
        st.plotly_chart(fig, width='stretch', key="tr_mom",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
    with c2:
        section_title("⚖️ L100P Location × Month")
        l1 = cp.groupby(["Location Name", "Month_Sort", "Month Name"], as_index=False, dropna=False).agg(NL=("Net_Labour","sum"), NP=("Net_Parts","sum")).sort_values("Month_Sort")
        l1["L100P"] = np.where(l1["NP"]>0, l1["NL"]/l1["NP"]*100, 0)
        fig = px.line(l1, x="Month Name", y="L100P", color="Location Name", markers=True)
        fig.add_hline(y=100, line_dash="dash", line_color=C["red"])
        fig.update_layout(**get_ply_layout(height=300, xaxis_title="", yaxis_title=""))
        st.plotly_chart(fig, width='stretch', key="tr_l100p",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
        
    section_title("🏢 WS vs BS Trend (Stacked Area)")
    wbs = cp.groupby(["Month_Sort", "Month Name", "Service_Type_Group"], as_index=False, dropna=False)["Net_Labour"].sum().sort_values("Month_Sort")
    fig = px.area(wbs, x="Month Name", y="Net_Labour", color="Service_Type_Group", color_discrete_map=MP_COLORS)
    fig.update_layout(**get_ply_layout(height=350, xaxis_title="", yaxis_title=""))
    st.plotly_chart(fig, width='stretch', key="tr_wsbs",
                    config={"displayModeBar": True, "displaylogo": False,
                            "modeBarButtonsToRemove": ["select2d","lasso2d"],
                            "toImageButtonOptions": {"format":"png","scale":2}})
    # Forecasting Section
    section_title("📈 3-Month Forecast (Linear Trend)")

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
        
        fig.update_layout(**get_ply_layout(height=350, xaxis_title="", yaxis_title="Value", hovermode="x unified"))
        st.plotly_chart(fig, width='stretch', key="tr_forecast",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
        
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
    UniversalFooter()
