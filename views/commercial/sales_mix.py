from views.shared import *
from views.components.chart_engine import ChartEngine
from ui.design_tokens import T



def _apply_filters(df, pairs):
    """Apply CP/PP period filters using pairs."""
    if not pairs:
        return df, None
    
    cp_months = [p[0] for p in pairs]
    pp_months = [p[1] for p in pairs]
    
    cp = df[df["Month Name"].isin(cp_months)] if cp_months else df
    pp = df[df["Month Name"].isin(pp_months)] if pp_months else None
    
    return cp, pp

def _compute_metrics(cp, pp):
    metrics = {"cp": cp, "pp": pp}
    
    # CP values
    metrics["oil_rs_cp"] = get_oil_sales(cp)
    metrics["oil_ltrs_cp"] = cp["Oil_Sale_Qty"].sum() if "Oil_Sale_Qty" in cp.columns else 0
    metrics["tyre_rs_cp"] = get_tyre_sales(cp)
    metrics["tyre_nos_cp"] = cp["Tyre_Sale_Qty"].sum() if "Tyre_Sale_Qty" in cp.columns else 0
    metrics["batt_rs_cp"] = get_battery_sales(cp)
    metrics["batt_nos_cp"] = cp["Battery_Sale_Qty"].sum() if "Battery_Sale_Qty" in cp.columns else 0
    metrics["acc_rs_cp"] = get_accessory_sales(cp)
    metrics["parts_rs_cp"] = cp["Parts_Sale"].sum() if "Parts_Sale" in cp.columns else 0
    
    # PP values (if available)
    if pp is not None and not pp.empty:
        metrics["oil_rs_pp"] = get_oil_sales(pp)
        metrics["oil_ltrs_pp"] = pp["Oil_Sale_Qty"].sum() if "Oil_Sale_Qty" in pp.columns else 0
        metrics["tyre_rs_pp"] = get_tyre_sales(pp)
        metrics["tyre_nos_pp"] = pp["Tyre_Sale_Qty"].sum() if "Tyre_Sale_Qty" in pp.columns else 0
        metrics["batt_rs_pp"] = get_battery_sales(pp)
        metrics["batt_nos_pp"] = pp["Battery_Sale_Qty"].sum() if "Battery_Sale_Qty" in pp.columns else 0
        metrics["acc_rs_pp"] = get_accessory_sales(pp)
        metrics["parts_rs_pp"] = pp["Parts_Sale"].sum() if "Parts_Sale" in pp.columns else 0
    else:
        metrics["oil_rs_pp"] = 0
        metrics["oil_ltrs_pp"] = 0
        metrics["tyre_rs_pp"] = 0
        metrics["tyre_nos_pp"] = 0
        metrics["batt_rs_pp"] = 0
        metrics["batt_nos_pp"] = 0
        metrics["acc_rs_pp"] = 0
        metrics["parts_rs_pp"] = 0
    
    # Calculate growth percentages
    metrics["oil_growth"] = calc_growth_pct(metrics["oil_rs_cp"], metrics["oil_rs_pp"], fill_value=0)
    metrics["tyre_growth"] = calc_growth_pct(metrics["tyre_rs_cp"], metrics["tyre_rs_pp"], fill_value=0)
    metrics["batt_growth"] = calc_growth_pct(metrics["batt_rs_cp"], metrics["batt_rs_pp"], fill_value=0)
    metrics["acc_growth"] = calc_growth_pct(metrics["acc_rs_cp"], metrics["acc_rs_pp"], fill_value=0)
    metrics["parts_growth"] = calc_growth_pct(metrics["parts_rs_cp"], metrics["parts_rs_pp"], fill_value=0)
    
    # Calculate growth for quantity metrics
    metrics["oil_ltrs_growth"] = calc_growth_pct(metrics["oil_ltrs_cp"], metrics["oil_ltrs_pp"], fill_value=0)
    metrics["tyre_nos_growth"] = calc_growth_pct(metrics["tyre_nos_cp"], metrics["tyre_nos_pp"], fill_value=0)
    metrics["batt_nos_growth"] = calc_growth_pct(metrics["batt_nos_cp"], metrics["batt_nos_pp"], fill_value=0)
    
    kpi_data = [
        {"label": "Oil (INR)", "value": fmt_inr(metrics["oil_rs_cp"]), "cp": metrics["oil_rs_cp"], "pp": metrics["oil_rs_pp"]},
        {"label": "Oil (Ltrs)", "value": fmt_num(metrics["oil_ltrs_cp"]), "cp": metrics["oil_ltrs_cp"], "pp": metrics["oil_ltrs_pp"]},
        {"label": "Tyre (INR)", "value": fmt_inr(metrics["tyre_rs_cp"]), "cp": metrics["tyre_rs_cp"], "pp": metrics["tyre_rs_pp"]},
        {"label": "Tyre (Nos)", "value": fmt_num(metrics["tyre_nos_cp"]), "cp": metrics["tyre_nos_cp"], "pp": metrics["tyre_nos_pp"]},
        {"label": "Battery (INR)", "value": fmt_inr(metrics["batt_rs_cp"]), "cp": metrics["batt_rs_cp"], "pp": metrics["batt_rs_pp"]},
        {"label": "Battery (Nos)", "value": fmt_num(metrics["batt_nos_cp"]), "cp": metrics["batt_nos_cp"], "pp": metrics["batt_nos_pp"]},
        {"label": "Accessory (INR)", "value": fmt_inr(metrics["acc_rs_cp"]), "cp": metrics["acc_rs_cp"], "pp": metrics["acc_rs_pp"]},
        {"label": "Parts Sale (INR)", "value": fmt_inr(metrics["parts_rs_cp"]), "cp": metrics["parts_rs_cp"], "pp": metrics["parts_rs_pp"]}
    ]
    metrics["kpi_data"] = kpi_data
    return metrics

def _get_table_data(cp, col, pp=None, comparison_mode=True):
    mo = cp.drop_duplicates("Month Name").sort_values("Month_Sort")["Month Name"].tolist()
    pvt = cp.groupby(["Location Name","Month Name"], dropna=False)[col].sum().reset_index()
    pvt = pvt.pivot_table(index="Location Name", columns="Month Name", values=col, aggfunc="sum").fillna(0)
    pvt = pvt.reindex(columns=[m for m in mo if m in pvt.columns])
    pvt["Total"] = pvt.sum(axis=1)
    
    # Add growth column if PP data is available
    if pp is not None and not pp.empty and len(mo) >= 2:
        pp_pvt = pp.groupby(["Location Name","Month Name"], dropna=False)[col].sum().reset_index()
        pp_pvt = pp_pvt.pivot_table(index="Location Name", columns="Month Name", values=col, aggfunc="sum").fillna(0)
        pp_pvt = pp_pvt.reindex(columns=[m for m in mo if m in pp_pvt.columns])
        pp_pvt["Total"] = pp_pvt.sum(axis=1)
        
        # Calculate growth for Total column
        growth_col = []
        for loc in pvt.index:
            cp_total = pvt.loc[loc, "Total"] if loc in pvt.index else 0
            pp_total = pp_pvt.loc[loc, "Total"] if loc in pp_pvt.index else 0
            growth = calc_growth_pct(cp_total, pp_total, fill_value=0)
            growth_col.append(growth)
        growth_label = "YoY Growth %" if comparison_mode else "MoM Growth %"
        pvt[growth_label] = growth_col
    
    tot = pd.DataFrame(pvt.sum()).T; tot.index = ["TOTAL"]
    dp = pd.concat([pvt, tot]).reset_index().rename(columns={"index":"Location"})
    for col_name in dp.columns[1:]:
        if "Growth %" not in col_name:
            dp[col_name] = dp[col_name].apply(fmt_inr)
        else:
            dp[col_name] = dp[col_name].apply(lambda v: f"{v:+.1f}%" if pd.notna(v) else "—")
    return dp

def _render_kpis(metrics):
    KPIGrid(metrics["kpi_data"], cols=4)

def _render_tables(metrics, comparison_mode=True):
    cp = metrics["cp"]
    pp = metrics["pp"]
    spacer(6)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('**Oil Sales**')
        oil_df = _get_table_data(cp, "Oil_Sale", pp, comparison_mode)
        TableCard(oil_df, height=300, index=False)
        from services.export_service import ExportMeta
        meta = ExportMeta(
            report_title="Oil Sales",
            location="All Locations",
            date_range="",
        )
        render_export_buttons(oil_df, meta, key_prefix="sales_mix_oil")
    with c2:
        st.markdown('**Battery Sales**')
        batt_df = _get_table_data(cp, "Battery_Sale", pp, comparison_mode)
        TableCard(batt_df, height=300, index=False)
        meta = ExportMeta(
            report_title="Battery Sales",
            location="All Locations",
            date_range="",
        )
        render_export_buttons(batt_df, meta, key_prefix="sales_mix_battery")

    spacer(6)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('**Tyre Sales**')
        tyre_df = _get_table_data(cp, "Tyre_Sale", pp, comparison_mode)
        TableCard(tyre_df, height=300, index=False)
        meta = ExportMeta(
            report_title="Tyre Sales",
            location="All Locations",
            date_range="",
        )
        render_export_buttons(tyre_df, meta, key_prefix="sales_mix_tyre")
    with c2:
        st.markdown('**Accessory Sales**')
        acc_df = _get_table_data(cp, "Accessory_Sale", pp, comparison_mode)
        TableCard(acc_df, height=300, index=False)
        meta = ExportMeta(
            report_title="Accessory Sales",
            location="All Locations",
            date_range="",
        )
        render_export_buttons(acc_df, meta, key_prefix="sales_mix_accessory")

def _render_charts(metrics, comparison_mode=True):
    cp = metrics["cp"]
    pp = metrics["pp"]
    pp_label = "Prior Period (YoY)" if comparison_mode else "Prior Period (MoM)"
    cp_label = "Current Period"
    spacer(6)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        agg_cp = {"S": ("Oil_Sale", "sum")}
        if "Oil_Sale_Qty" in cp.columns: agg_cp["Q"] = ("Oil_Sale_Qty", "sum")
        ot = monthly_summary(cp, as_index=False).agg(**agg_cp).sort_values("Month_Sort")
        if "Q" not in ot.columns: ot["Q"] = 0

        fig = go.Figure()
        fig.add_trace(go.Bar(x=ot["Month Name"], y=ot["S"], name=f"INR ({cp_label})", marker_color=T.COLOR_PRIMARY))
        fig.add_trace(go.Scatter(x=ot["Month Name"], y=ot["Q"], name=f"Ltrs ({cp_label})", yaxis="y2", marker_color=T.COLOR_WARNING, mode="lines+markers"))
        # Add PP comparison if available
        if pp is not None and not pp.empty:
            agg_pp = {"S": ("Oil_Sale", "sum")}
            if "Oil_Sale_Qty" in pp.columns: agg_pp["Q"] = ("Oil_Sale_Qty", "sum")
            ot_pp = monthly_summary(pp, as_index=False).agg(**agg_pp).sort_values("Month_Sort")
            if "Q" not in ot_pp.columns: ot_pp["Q"] = 0
            fig.add_trace(go.Scatter(x=ot_pp["Month Name"], y=ot_pp["S"], name=f"INR ({pp_label})", line=dict(dash="dash", color=T.COLOR_PRIMARY)))
            fig.add_trace(go.Scatter(x=ot_pp["Month Name"], y=ot_pp["Q"], name=f"Ltrs ({pp_label})", yaxis="y2", line=dict(dash="dash", color=T.COLOR_WARNING), mode="lines+markers"))
        fig.update_layout(yaxis2=dict(overlaying="y", side="right"), showlegend=True, legend=dict(orientation="h", y=-0.2))
        ChartEngine.render_card("Oil Trend", fig, height=350)
    with c2:
        bt = monthly_summary(cp, as_index=False).agg(B=("Battery_Sale","sum"), T=("Tyre_Sale","sum")).sort_values("Month_Sort")
        fig = px.bar(bt, x="Month Name", y=["B", "T"], barmode="group", color_discrete_sequence=[T.COLOR_SUCCESS, T.COLOR_WARNING])
        # Add PP comparison if available
        if pp is not None and not pp.empty:
            bt_pp = monthly_summary(pp, as_index=False).agg(B=("Battery_Sale","sum"), T=("Tyre_Sale","sum")).sort_values("Month_Sort")
            fig.add_trace(go.Scatter(x=bt_pp["Month Name"], y=bt_pp["B"], name=f"Battery ({pp_label})", line=dict(dash="dash", color=T.COLOR_SUCCESS)))
            fig.add_trace(go.Scatter(x=bt_pp["Month Name"], y=bt_pp["T"], name=f"Tyre ({pp_label})", line=dict(dash="dash", color=T.COLOR_WARNING)))
        fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.2))
        ChartEngine.render_card("Batt + Tyre", fig, height=350)
    with c3:
        orank = location_summary(cp, as_index=False)["Oil_Sale"].sum().sort_values(by="Oil_Sale", ascending=True).tail(10)
        fig = px.bar(orank, x="Oil_Sale", y="Location Name", orientation="h", color_discrete_sequence=[T.COLOR_PRIMARY])
        ChartEngine.render_card("Oil Ranking", fig, height=300)
    with c4:
        md = pd.DataFrame({"Cat": ["Accessory", "Parts"], "Val": [metrics["acc_rs_cp"], metrics["parts_rs_cp"]]})
        fig = px.pie(md, values="Val", names="Cat", hole=0.6, color_discrete_sequence=[T.COLOR_DANGER, T.COLOR_SUCCESS])
        ChartEngine.render_card("Mix (Acc vs Pts)", fig, height=300)
        
    spacer(6)
    agg_oil_loc = {"S": ("Oil_Sale", "sum")}
    if "Oil_Sale_Qty" in cp.columns: agg_oil_loc["Q"] = ("Oil_Sale_Qty", "sum")
    oil_per_litre = location_summary(cp, as_index=True).agg(**agg_oil_loc).reset_index()
    if "Q" not in oil_per_litre.columns: oil_per_litre["Q"] = 0
    oil_per_litre["Per Litre"] = np.where(oil_per_litre["Q"]>0, oil_per_litre["S"]/oil_per_litre["Q"], 0)
    oil_per_litre = oil_per_litre.sort_values("Per Litre", ascending=False)
    fig = px.bar(oil_per_litre, x="Per Litre", y="Location Name", orientation="h", color_discrete_sequence=[T.COLOR_PRIMARY])
    ChartEngine.render_card("Oil Revenue per Litre by Location", fig, height=400, x_title="INR per Litre")

def render(df, pairs, comparison_mode=True, selected_months=None):
    """
    Sales Mix render function with YoY/MoM comparison support.
    
    Args:
        df: Source dataframe
        pairs: Period pairs for comparison (CP, PP)
        comparison_mode: If True, shows YoY comparison; if False, shows MoM
        selected_months: Optional month filter
    """
    if df.empty:
        EmptyState('No data available for the selected period. Adjust your filters or check data freshness.')
        return
        
    cp, pp = _apply_filters(df, pairs)
    metrics = _compute_metrics(cp, pp)
    
    _render_kpis(metrics)
    _render_tables(metrics, comparison_mode)
    _render_charts(metrics, comparison_mode)
    
    try:
        UniversalFooter()
    except Exception:
        pass
