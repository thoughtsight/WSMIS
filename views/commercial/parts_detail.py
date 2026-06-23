from views.shared import *
from views.components.chart_engine import ChartEngine
from views.dashboard_common import style_table_bold_total, style_margin_color, get_drill_params, clear_drill_params, inject_responsive_css
from utils.constants import CATEGORY_COLORS

"""
Parts Revenue — Detail Dashboard
Multi-Location Mar Dealership  ·  Apple Light-Theme  ·  v2.0
"""


CAT_MAP = {
    "Standard Parts": "Parts_Sale",
    "Oil": "Oil_Sale",
    "Accessories": "Accessory_Sale",
    "Tyres": "Tyre_Sale",
    "Battery": "Battery_Sale",
    "Other": "Other_Sale",
}


def _apply_detail_filters(df):
    """Render page-level inline filters and return filtered DataFrame."""
    # Get drill-through parameters
    drill_params = get_drill_params()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # If drill-through location is set, use it as default
        location_options = ["All"] + sorted(df["Location Name"].unique())
        if drill_params["location"] and drill_params["location"] in location_options:
            sel_location = st.selectbox("Location", location_options, key="parts_detail_location", index=location_options.index(drill_params["location"]))
        else:
            sel_location = st.selectbox("Location", location_options, key="parts_detail_location")
    with col2:
        sel_month = st.selectbox("Month", ["All"] + sorted(df["Month Name"].unique(), reverse=True), key="parts_detail_month")
    with col3:
        sel_svc = st.selectbox("Service Type", ["All"] + sorted(df["Service Type"].dropna().unique()), key="parts_detail_svc")
    with col4:
        # If drill-through category is set, use it as default
        category_options = ["All", "Standard Parts", "Oil", "Accessories", "Tyres", "Battery", "Other"]
        if drill_params["category"] and drill_params["category"] in category_options:
            sel_cat = st.selectbox("Category", category_options, key="parts_detail_cat", index=category_options.index(drill_params["category"]))
        else:
            sel_cat = st.selectbox("Category", category_options, key="parts_detail_cat")
    
    fdf = df.copy()
    if sel_location != "All":
        fdf = fdf[fdf["Location Name"] == sel_location]
    if sel_month != "All":
        fdf = fdf[fdf["Month Name"] == sel_month]
    if sel_svc != "All":
        fdf = fdf[fdf["Service Type"] == sel_svc]
    
    # Apply category filter if selected
    if sel_cat != "All" and sel_cat in CAT_MAP:
        cat_col = CAT_MAP[sel_cat]
        if cat_col in fdf.columns:
            fdf = fdf[fdf[cat_col] > 0]
    
    # Show drill-through context if navigating from another page
    if drill_params["from_page"]:
        st.info(f"🔍 Drilled from {drill_params['from_page']}")
        if st.button("Clear drill-through filters", key="clear_drill"):
            clear_drill_params()
            st.rerun()
    
    return fdf, sel_cat


def _render_category_table(fdf, sel_cat):
    section_title("📦 Parts Category Revenue by Location")
    
    CAT_COLS_LIST = list(CAT_MAP.values())
    numeric_cols = CAT_COLS_LIST + ["Pre-GST Parts", "Parts Profit", "Parts Discount"]
    for c in numeric_cols:
        if c in fdf.columns:
            fdf = fdf.copy()
            fdf[c] = pd.to_numeric(fdf[c], errors="coerce").fillna(0).astype(float)
    cat_sum = category_summary(fdf, CAT_COLS_LIST)
    has_cat = cat_sum.sum() > 0
    
    if not has_cat:
        st.info("Category breakdown available from Jan-26 onwards. Showing total parts only.")
        agg_dict = {"Pre-GST Parts": "sum", "Parts Profit": "sum", "Parts Discount": "sum"}
        for col in CAT_MAP.values():
            agg_dict[col] = "sum"
        loc_sum = location_summary(fdf, as_index=True).agg(agg_dict)
        loc_total = loc_sum["Pre-GST Parts"] if "Pre-GST Parts" in loc_sum.columns else pd.Series(dtype=float)
        loc_total = loc_total.sort_values(ascending=False)
        st.dataframe(loc_total.apply(fmt_inr_full).rename("Parts Revenue"), use_container_width=True)
        return
    
    # Use cached location_summary for efficiency
    agg_dict = {"Pre-GST Parts": "sum", "Parts Profit": "sum", "Parts Discount": "sum"}
    for col in CAT_MAP.values():
        agg_dict[col] = "sum"
    loc_sum = location_summary(fdf, as_index=True).agg(agg_dict)
    
    rows = []
    for loc in loc_sum.index:
        row = {"Location": loc}
        row_total = 0
        for label, col in CAT_MAP.items():
            v = loc_sum.loc[loc, col] if col in loc_sum.columns else 0
            row[label] = v
            row_total += v
        row["Total"] = loc_sum.loc[loc, "Pre-GST Parts"] if "Pre-GST Parts" in loc_sum.columns else 0
        row["Margin %"] = calc_ratio(loc_sum.loc[loc, "Parts Profit"], row_total, multiplier=100, fill_value=0) if row_total > 0 else 0.0
        rows.append(row)
    
    # TOTAL row - use canonical helpers
    total_row = {"Location": "TOTAL"}
    for label, col in CAT_MAP.items():
        total_row[label] = cat_sum[col] if col in cat_sum.index else 0
    total_row["Total"] = get_parts_sales(fdf, aggregate=True)
    total_row["Margin %"] = calc_ratio(get_parts_profit(fdf, aggregate=True), total_row["Total"], multiplier=100, fill_value=0) if total_row["Total"] > 0 else 0.0
    rows.append(total_row)
    
    # If a specific category is selected, filter to show only that category
    if sel_cat != "All" and sel_cat in CAT_MAP:
        cat_df = pd.DataFrame(rows)
        cat_df = cat_df[["Location", sel_cat, "Total", "Margin %"]].copy()
        cat_df.columns = ["Location", "Revenue", "Total", "Margin %"]
        money_cols = ["Revenue", "Total"]
        fmt_dict = {c: fmt_inr_full for c in money_cols}
        fmt_dict["Margin %"] = lambda v: f"{v:.1f}%"
        
        styled = cat_df.style.apply(style_table_bold_total, axis=1)
        styled = styled.map(style_margin_color, subset=["Margin %"])
        styled = styled.format(fmt_dict)
        
        st.dataframe(styled, use_container_width=True, hide_index=True)
        
        from services.export_service import ExportMeta
        meta = ExportMeta(
            report_title=f"Parts Category - {sel_cat}",
            location="All Locations",
            date_range="",
        )
        render_export_buttons(cat_df, meta, key_prefix="parts_category")
        return
    
    cat_df = pd.DataFrame(rows)
    
    loc_rows = cat_df[cat_df["Location"] != "TOTAL"].sort_values("Total", ascending=False)
    total_row_df = cat_df[cat_df["Location"] == "TOTAL"]
    cat_df = pd.concat([loc_rows, total_row_df], ignore_index=True)
    
    
    money_cols = list(CAT_MAP.keys()) + ["Total"]
    fmt_dict = {c: fmt_inr_full for c in money_cols}
    fmt_dict["Margin %"] = lambda v: f"{v:.1f}%"
    
    styled = cat_df.style.apply(style_table_bold_total, axis=1)
    styled = styled.map(style_margin_color, subset=["Margin %"])
    styled = styled.format(fmt_dict)
    
    st.dataframe(styled, use_container_width=True, hide_index=True)
    
    from services.export_service import ExportMeta
    meta = ExportMeta(
        report_title="Parts Category",
        location="All Locations",
        date_range="",
    )
    render_export_buttons(cat_df, meta, key_prefix="parts_category")


def _render_category_mix_chart(fdf, mode_str):
    section_title("📊 Category Mix — CP vs PP")
    
    has_cat = fdf[list(CAT_MAP.values())].sum().sum() > 0
    if not has_cat:
        st.info("Category breakdown available from Jan-26 onwards.")
        return
    
    cp_df = fdf[fdf["year"] == "This FY"]
    pp_df = fdf[fdf["year"] == "Last FY"]
    
    categories = list(CAT_MAP.keys())
    cp_vals = [cp_df[CAT_MAP[c]].sum() if CAT_MAP[c] in cp_df.columns else 0 for c in categories]
    pp_vals = [pp_df[CAT_MAP[c]].sum() if CAT_MAP[c] in pp_df.columns else 0 for c in categories]
    
    fig = go.Figure()
    for i, cat in enumerate(categories):
        color = CATEGORY_COLORS.get(cat, T.COLOR_PRIMARY)
        fig.add_trace(go.Bar(
            name=f"CP — {cat}", x=["CP (This FY)"], y=[cp_vals[i]],
            marker_color=color, opacity=0.9,
            text=[fmt_inr_short(cp_vals[i])], textposition="inside",
            textfont=dict(size=11, color="white", weight=700)))
        fig.add_trace(go.Bar(
            name=f"PP — {cat}", x=["PP (Last FY)"], y=[pp_vals[i]],
            marker_color=color, opacity=0.5,
            text=[fmt_inr_short(pp_vals[i])], textposition="inside",
            textfont=dict(size=11, color="white")))
    
    fig = ChartEngine.apply_chart(fig, title=f"Parts Category Mix — CP vs PP ({mode_str})",
                      height=400, barmode="stack", size="full")
    st.plotly_chart(fig, use_container_width=True)


def _render_service_contribution(fdf):
    section_title("🔧 Parts Revenue by Service Type")

    # Use cached service_summary for efficiency
    svc_gb = service_summary(fdf, as_index=True)
    svc_sum = svc_gb.agg({"Pre-GST Parts": "sum", "JC_Nos.": "sum", "Parts Profit": "sum"})

    svc_df = pd.DataFrame({
        "Revenue": svc_sum["Pre-GST Parts"] if "Pre-GST Parts" in svc_sum.columns else 0,
        "Job_Cards": svc_sum["JC_Nos."] if "JC_Nos." in svc_sum.columns else 0,
        "Profit": svc_sum["Parts Profit"] if "Parts Profit" in svc_sum.columns else 0
    }, index=svc_sum.index)
    svc_df = svc_df.sort_values("Revenue", ascending=False)

    svc_df["Parts/JC"] = calc_ratio(svc_df["Revenue"], svc_df["Job_Cards"], fill_value=0)
    svc_df["Margin %"] = calc_ratio(svc_df["Profit"], svc_df["Revenue"], multiplier=100, fill_value=0).round(1)
    svc_df["% of Total"] = calc_ratio(svc_df["Revenue"], svc_df["Revenue"].sum(), multiplier=100, fill_value=0).round(1)

    # Discount Rate per service type
    if "Parts Discount" in fdf.columns:
        svc_discount = fdf.groupby("Service Type")["Parts Discount"].sum()
        svc_df["Discount %"] = calc_ratio(svc_discount, svc_df["Revenue"], multiplier=100, fill_value=0).reindex(svc_df.index, fill_value=0).round(2)
    else:
        svc_df["Discount %"] = 0.0

    # Oil Penetration Rate per service type
    if "Oil_Sale" in fdf.columns:
        oil_jcs_by_svc = fdf[fdf["Oil_Sale"] > 0].groupby("Service Type").size()
        svc_df["Oil Pen %"] = calc_ratio(oil_jcs_by_svc, svc_df["Job_Cards"], multiplier=100, fill_value=0).reindex(svc_df.index, fill_value=0).round(1)
    else:
        svc_df["Oil Pen %"] = 0.0

    svc_df.insert(0, "Rank", range(1, len(svc_df) + 1))

    fmt_dict = {
        "Revenue": fmt_inr_full,
        "Job_Cards": fmt_num,
        "Parts/JC": lambda v: f"{v:.1f}",
        "Discount %": lambda v: f"{v:.2f}%",
        "Oil Pen %": lambda v: f"{v:.1f}%",
        "Margin %": lambda v: f"{v:.1f}%",
        "% of Total": lambda v: f"{v:.1f}%",
    }

    styled = svc_df.reset_index().style.format(fmt_dict)
    styled = styled.map(style_margin_color, subset=["Margin %"])

    # Conditional formatting for Discount % (lower is better)
    def _discount_color(val):
        if val > 2.5: return f"color:{T.COLOR_DANGER};font-weight:700"
        if val > 2.0: return f"color:{T.COLOR_WARNING};font-weight:700"
        return ""

    # Conditional formatting for Oil Pen %
    def _oil_pen_color(val):
        if val < 60: return f"color:{T.COLOR_DANGER};font-weight:700"
        if val < 70: return f"color:{T.COLOR_WARNING};font-weight:700"
        return ""

    styled = styled.map(_discount_color, subset=["Discount %"])
    styled = styled.map(_oil_pen_color, subset=["Oil Pen %"])

    st.dataframe(styled, use_container_width=True, hide_index=True)
    
    from services.export_service import ExportMeta
    meta = ExportMeta(
        report_title="Parts Service Contribution",
        location="All Locations",
        date_range="",
    )
    render_export_buttons(svc_df.reset_index(), meta, key_prefix="parts_service")


def _render_service_mix_donut(fdf):
    """Render Service Type Mix Analysis as a donut chart."""
    section_title("🍩 Service Type Mix Analysis")

    # Use cached service_summary for efficiency
    svc_gb = service_summary(fdf, as_index=True)
    svc_sum = svc_gb.agg({"Pre-GST Parts": "sum"})

    if svc_sum.empty or "Pre-GST Parts" not in svc_sum.columns:
        st.info("No service type data available.")
        return

    svc_sum = svc_sum.sort_values("Pre-GST Parts", ascending=False)

    fig = go.Figure(data=[go.Pie(
        labels=svc_sum.index,
        values=svc_sum["Pre-GST Parts"],
        hole=0.4,
        textinfo="label+percent",
        textposition="outside",
        marker=dict(
            colors=[CATEGORY_COLORS.get(svc, T.COLOR_PRIMARY) for svc in svc_sum.index],
            line=dict(color="white", width=2)
        ),
        hovertemplate="<b>%{label}</b><br>Revenue: %{value}<br>%{percent}<extra></extra>",
    )])

    fig.update_layout(
        title="Revenue Distribution by Service Type",
        height=400,
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02
        )
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_monthly_trend_table(fdf):
    """Render Monthly Trend Table showing last 6 months of data."""
    section_title("📈 Monthly Trend (Last 6 Months)")

    # Use cached monthly_summary for efficiency
    month_gb = monthly_summary(fdf, as_index=True)
    month_sum = month_gb.agg({"Pre-GST Parts": "sum", "JC_Nos.": "sum", "Parts Profit": "sum"})

    if month_sum.empty or "Pre-GST Parts" not in month_sum.columns:
        st.info("No monthly trend data available.")
        return

    # Reset index to get Month Name as column
    month_df = month_sum.reset_index()

    # Sort by Month_Sort if available, otherwise by Month Name
    if "Month_Sort" in month_df.columns:
        month_df = month_df.sort_values("Month_Sort", ascending=True)
    else:
        month_df = month_df.sort_values("Month Name", ascending=True)

    # Get last 6 months
    month_df = month_df.tail(6)

    month_df["Margin %"] = calc_ratio(month_df["Parts Profit"], month_df["Pre-GST Parts"], multiplier=100, fill_value=0).round(1)
    month_df["Parts/JC"] = calc_ratio(month_df["Pre-GST Parts"], month_df["JC_Nos."], fill_value=0).round(1)

    # Select and rename columns
    trend_df = month_df[["Month Name", "Pre-GST Parts", "JC_Nos.", "Margin %", "Parts/JC"]]
    trend_df.columns = ["Month", "Revenue", "Job Cards", "Margin %", "Parts/JC"]

    fmt_dict = {
        "Revenue": fmt_inr_full,
        "Job Cards": fmt_num,
        "Margin %": lambda v: f"{v:.1f}%",
        "Parts/JC": lambda v: f"{v:.1f}",
    }

    styled = trend_df.style.format(fmt_dict)
    styled = styled.map(style_margin_color, subset=["Margin %"])

    st.dataframe(styled, use_container_width=True, hide_index=True)

    from services.export_service import ExportMeta
    meta = ExportMeta(
        report_title="Monthly Trend",
        location="All Locations",
        date_range="",
    )
    render_export_buttons(trend_df, meta, key_prefix="monthly_trend")


def _render_discount_table(fdf):
    section_title("🏷 Parts Discount by Location")
    
    for c in ["Pre-GST Parts", "Parts Profit", "Parts Discount"] + list(CAT_MAP.values()):
        if c in fdf.columns:
            fdf[c] = pd.to_numeric(fdf[c], errors="coerce").fillna(0)
    agg_dict = {"Pre-GST Parts": "sum", "Parts Profit": "sum", "Parts Discount": "sum"}
    for col in CAT_MAP.values():
        agg_dict[col] = "sum"
    loc_sum = location_summary(fdf, as_index=True).agg(agg_dict)
    
    disc_df = pd.DataFrame({
        "Revenue": loc_sum["Pre-GST Parts"] if "Pre-GST Parts" in loc_sum.columns else 0,
        "Discount": loc_sum["Parts Discount"] if "Parts Discount" in loc_sum.columns else 0
    }, index=loc_sum.index)
    disc_df["Discount %"] = calc_ratio(disc_df["Discount"], disc_df["Revenue"], multiplier=100, fill_value=0).round(2)
    disc_df = disc_df.sort_values("Discount %", ascending=False)
    
    def _disc_color(val):
        if val > 2.0: return f"color:{T.COLOR_DANGER};font-weight:700"
        if val > 1.0: return f"color:{T.COLOR_WARNING};font-weight:700"
        return ""
    
    styled = disc_df.reset_index().style.format({
        "Revenue": fmt_inr_full,
        "Discount": fmt_inr_full,
        "Discount %": lambda v: f"{v:.2f}%"
    }).map(_disc_color, subset=["Discount %"])
    
    st.dataframe(styled, use_container_width=True, hide_index=True)
    
    from services.export_service import ExportMeta
    meta = ExportMeta(
        report_title="Parts Discount",
        location="All Locations",
        date_range="",
    )
    render_export_buttons(disc_df.reset_index(), meta, key_prefix="parts_discount")


def render(df, pairs, comparison_mode=True, selected_months=None):
    inject_responsive_css()
    PageBreadcrumb(["Commercial", "Parts Executive", "Parts Detail"])
    if df.empty:
        EmptyState("No parts data for the selected period.")
        return
    
    mode_str = "YoY" if comparison_mode else "MoM"
    
    fdf, sel_cat = _apply_detail_filters(df)
    
    if fdf.empty:
        EmptyState("No data for selected filters.")
        return
    
    _render_category_table(fdf, sel_cat)
    st.markdown("---")
    _render_category_mix_chart(fdf, mode_str)
    st.markdown("---")
    _render_service_contribution(fdf)
    st.markdown("---")
    _render_service_mix_donut(fdf)
    st.markdown("---")
    _render_monthly_trend_table(fdf)
    st.markdown("---")
    _render_discount_table(fdf)
    UniversalFooter()
