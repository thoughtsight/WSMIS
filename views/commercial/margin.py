from views.shared import *
from views.components.kpi_engine import KPIEngine
from views.components.chart_engine import ChartEngine
from utils.calculations.fact_metrics import _get_metric
from views.dashboard_common import inject_responsive_css





# Import new Phase B UI Components
from ui.design_tokens import T


def _render_margin_narrative(kpi_values: dict):
    """Conditional narrative banner summarising margin health signals."""
    total_m = kpi_values.get("Total Margin", 0)
    net_lab = kpi_values.get("Net Labour", 0)
    parts_m = kpi_values.get("Parts_Margin", 0)

    msgs = []
    if total_m <= 0:
        msgs.append(f"⚠ Total margin is negative ({fmt_inr_short(total_m)}) — immediate review required.")
        severity = "error"
    else:
        severity = "info"
        msgs.append(f"Total margin this period: {fmt_inr_short(total_m)}.")

    if parts_m < 0:
        severity = "warning" if severity == "info" else severity
        msgs.append(f"Parts margin is negative ({fmt_inr_short(parts_m)}) — check cost and discount structure.")

    if net_lab > 0 and total_m > 0:
        lab_share = net_lab / total_m * 100
        if lab_share > 70:
            msgs.append(f"Labour drives {lab_share:.0f}% of total margin — diversify revenue streams.")
        elif lab_share > 50:
            msgs.append(f"Labour contributes {lab_share:.0f}% of total margin.")

    if not msgs:
        return

    colors  = {"error": "#FEE2E2", "warning": "#FEF9C3", "info": "#EFF6FF"}
    borders = {"error": "#EF4444", "warning": "#EAB308", "info": "#3B82F6"}
    banner  = "  ·  ".join(msgs)
    st.markdown(
        f'<div style="background:{colors[severity]};border-left:4px solid {borders[severity]};'
        f'padding:12px 16px;border-radius:6px;margin-bottom:16px;'
        f'font-size:var(--type-sm);font-weight:600;line-height:1.6;">{banner}</div>',
        unsafe_allow_html=True
    )


def render(df, pairs, comparison_mode=True, selected_months=None):
    inject_responsive_css()
    PageBreadcrumb(["Commercial", "Margin"])
    if df.empty:
        EmptyState('No data available for the selected period. Adjust your filters or check data freshness.')
        return
    # df is already filtered by selected_months at main level, use it directly for current period
    cp = df.copy()
    
    
    kpis = ["Total Margin", "Net Labour", "Parts_Margin", "Oil_Margin", "OTC Income", "FSC Income"]
    kpi_data = []
    kpi_values = {}
    for k in kpis:
        if k == "Net Labour":
            v = get_net_labour(cp)  # Use canonical frozen calculation
        else:
            v = _get_metric(cp, k, aggregate=True)  # Safe metric extraction
        kpi_data.append({"label": k.replace("_", " "), "value": fmt_inr(v)})
        kpi_values[k] = v
    KPIGrid(kpi_data)
    _render_margin_narrative(kpi_values)
    
    # Waterfall chart
    st.markdown(f'<div style="margin-top:{T.SPACE_6}px;"></div>', unsafe_allow_html=True)
    gross_lab = get_labour_sales(cp)
    lab_disc = -get_labour_discount(cp)  # Use canonical frozen calculation
    net_lab = get_net_labour(cp)  # Use canonical Net Labour definition
    parts_margin = calculate_parts_margin(cp)
    oil_margin = _get_metric(cp, "Oil_Margin", aggregate=True)  # Safe metric extraction
    battery_margin = _get_metric(cp, "Battery_Margin", aggregate=True)  # Safe metric extraction
    tyre_margin = _get_metric(cp, "Tyre_Margin", aggregate=True)  # Safe metric extraction
    other_margin = _get_metric(cp, "Other_Margin", aggregate=True)  # Safe metric extraction
    fsc_income = get_fsc_income(cp)
    otc_income = get_otc_income(cp)
    vor_charges = -get_vor_charges(cp)
    dealer_foc = -get_dealer_foc(cp)
    internal_cons = -get_internal_consumption(cp)
    total_margin = calculate_total_margin(cp)
    
    labels = ["Gross Labour", "Labour Disc", "Net Labour", "Parts Margin", "Oil Margin", 
              "Battery+Tyre+Other", "FSC Income", "OTC Income", "VOR Charges", "Dealer FOC", 
              "Internal Cons", "Total Margin"]
    values = [gross_lab, lab_disc, net_lab, parts_margin, oil_margin, 
              battery_margin + tyre_margin + other_margin, fsc_income, otc_income, 
              vor_charges, dealer_foc, internal_cons, total_margin]
    
    fig = go.Figure(go.Waterfall(
        name="Margin Flow",
        orientation="v",
        measure=["relative"] * 11 + ["total"],
        x=labels,
        y=values,
        textposition="outside",
        text=[fmt_inr(v) for v in values],
        connector={"line":{"color":"rgb(63, 63, 63)"}},
    ))
    ChartEngine.render_card("💰 Margin Waterfall", fig, height=400)
        
    st.markdown(f'<div style="margin-top:{T.SPACE_6}px;"></div>', unsafe_allow_html=True)
    
    cats = ["Parts_Margin", "Accessory_Margin", "Oil_Margin", "Tyre_Margin", "Battery_Margin", "Other_Margin", "VOR Charges",
            "Total Parts Margin", "Net Labour", "OTC Income", "MSIL Labour Claim", "FSC Income", "Dealer FOC", "Internal Consumption", "Total Margin"]
    
    mo = cp.drop_duplicates("Month Name").sort_values("Month_Sort")["Month Name"].tolist()
    m_data = cp.groupby(["Month Name", "Month_Sort"], dropna=False).sum(numeric_only=True).reset_index().sort_values("Month_Sort")
    # Use safe column access for Total Parts Margin calculation
    margin_cols = ["Parts_Margin", "Accessory_Margin", "Oil_Margin", "Tyre_Margin", "Battery_Margin", "Other_Margin", "VOR Charges"]
    m_data["Total Parts Margin"] = m_data.reindex(columns=margin_cols, fill_value=0).sum(axis=1)
    m_data["Total Margin"] = m_data["Total Margin"]
    
    rows = []
    prev_tm = 0
    for cat in cats:
        r = {"Category": f"{cat}"}
        ct = 0
        for m in mo:
            if cat == "Net Labour":
                # Use canonical Net Labour calculation (Pre-GST Labour)
                month_cp = cp[cp["Month Name"] == m]
                v = get_net_labour(month_cp)
            else:
                lookup_cat = cat
                # Use safe metric access for optional columns
                month_m_data = m_data[m_data["Month Name"]==m]
                v = _get_metric(month_m_data, lookup_cat, aggregate=True) if not month_m_data.empty else 0
            r[m] = fmt_inr(v)
            ct += v
        r["Total CP"] = fmt_inr(ct)
        rows.append(r)
        
    # MoM
    r = {"Category": "MoM Growth %"}
    for m in mo:
        month_m_data = m_data[m_data["Month Name"]==m]
        v = _get_metric(month_m_data, "Total Margin", aggregate=True) if not month_m_data.empty else 0
        if prev_tm > 0: r[m] = fmt_pct((v-prev_tm)/prev_tm*100, True)
        else: r[m] = "—"
        prev_tm = v
    r["Total CP"] = "—"
    rows.append(r)
    
    TableCard(pd.DataFrame(rows), height=600, index=False)
    
    c1, c2 = st.columns(2)
    with c1:
        fig = px.area(m_data, x="Month Name", y="Total Margin", markers=True, color_discrete_sequence=[C["primary"]])
        fig.update_layout(**get_ply_layout(height=320, xaxis_title="", yaxis_title="Total Margin (₹)"))
        ChartEngine.render_card("📈 Total Margin Trend", fig, height=320)
    with c2:
        pie_cols = ["Parts_Margin", "Oil_Margin", "Net_Labour", "OTC Income", "FSC Income"]
        md = m_data.reindex(columns=pie_cols, fill_value=0).sum().reset_index()
        md.columns = ["Cat", "Val"]
        md.loc[md["Cat"] == "Net_Labour", "Cat"] = "Net Labour"
        md = md[md["Val"] > 0]
        fig = px.pie(md, values="Val", names="Cat", hole=0.5, color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(**get_ply_layout(height=320, margin=dict(t=0,b=0,l=0,r=0)))
        ChartEngine.render_card("🍰 Margin Mix", fig, height=320)
        
    c1, c2 = st.columns(2)
    with c1:
        lm = location_summary(cp, as_index=False)["Total Margin"].sum().sort_values("Total Margin", ascending=True)
        fig = px.bar(lm, x="Total Margin", y="Location Name", orientation="h", color_discrete_sequence=[C["green"]])
        fig.update_layout(**get_ply_layout(height=320, xaxis_title="", yaxis_title=""))
        ChartEngine.render_card("🏢 Location Margin", fig, height=320)
    with c2:
        wbs = cp.groupby(["Month_Sort", "Month Name", "Service_Type_Group"], as_index=False, dropna=False)["Total Margin"].sum().sort_values("Month_Sort")
        fig = px.bar(wbs, x="Month Name", y="Total Margin", color="Service_Type_Group", color_discrete_map=MP_COLORS)
        fig.update_layout(**get_ply_layout(height=320, xaxis_title="", yaxis_title=""))
        ChartEngine.render_card("⚖️ WS vs BS Margin", fig, height=320)
    UniversalFooter()
