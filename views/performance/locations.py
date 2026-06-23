from views.shared import *
from views.components.kpi_engine import KPIEngine
from views.components.chart_engine import ChartEngine
from views.dashboard_common import inject_responsive_css





# Import shared UI helpers from app
from ui.traffic import yoy_badge, traffic_light, tgt_badge
from ui.design_tokens import T

def render(df, pairs, comparison_mode=True, selected_months=None):
    inject_responsive_css()
    PageBreadcrumb(["Operations", "Locations"])
    if df.empty:
        EmptyState('No data available for the selected period. Adjust your filters or check data freshness.')
        return
    pp_months = [p[1] for p in pairs]
    # df is already filtered by selected_months at main level, use it directly for current period
    cp = df
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
    top_advs = filter_valid_advisors(cp, ADV_COL).groupby(["Location Name", ADV_COL], dropna=False)["JC_Nos."].sum().reset_index()
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
    for i in range(0, len(loc_data), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(loc_data):
                loc = loc_data.iloc[i + j]
                with cols[j]:
                    card_html = f"""
                    <div class="loc-card">
                        <div class="loc-card-title">{loc['Location Name']} <span style="font-size:{T.TYPE_XS}px;font-weight:500;color:var(--color-text-secondary);">({loc['Grp']})</span></div>
                        <div style="display:flex;justify-content:space-between;margin-bottom:{T.SPACE_2}px;">
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
                        <div style="display:flex;justify-content:space-between;margin-bottom:{T.SPACE_2}px;">
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
                            <div style="font-size:{T.TYPE_LG}px;">{loc['Health_Icon']}</div>
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
                    if st.button(f"View {loc['Location Name']}", key=f"loc_btn_{loc['Location Name']}", use_container_width=True):
                        st.session_state.filter_location = [loc['Location Name']]
                        st.session_state.filter_loc_group = []
                        st.rerun()
    
    section_title("📊 Location Ranking by Net Labour")
    fig = px.bar(loc_data, x="NL", y="Location Name", orientation="h", color="Grp", color_discrete_map=LOC_COLORS)
    fig.update_layout(**get_ply_layout(height=400, xaxis_title="", yaxis_title=""))
    st.plotly_chart(fig, width='stretch', key="loc_health_rank",
                    config={"displayModeBar": True, "displaylogo": False,
                            "modeBarButtonsToRemove": ["select2d","lasso2d"],
                            "toImageButtonOptions": {"format":"png","scale":2}})
    section_title("⚖️ Arena vs Nexa Comparison")
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
    
    UniversalFooter()

