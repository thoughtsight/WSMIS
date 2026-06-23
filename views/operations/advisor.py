from views.shared import *
from views.components.kpi_engine import KPIEngine
from views.components.chart_engine import ChartEngine





# Import new Phase B UI Components
from ui.design_tokens import T

def render(df, pairs, comparison_mode=True, selected_months=None):
    with st.spinner("Computing Advisor Scorecard..."):
        if df.empty:
            EmptyState('No data available for the selected period. Adjust your filters or check data freshness.')
            return
    # df is already filtered by selected_months at main level, use it directly for current period
    cp = df
    
    # Get previous period data for MoM comparison
    pp_months = [p[1] for p in pairs] if pairs else []
    pp = apply_month_filter(df, "Month Name", pp_months) if pp_months else pd.DataFrame()
    
    # Min JC threshold
    min_jc = st.slider("Minimum JCs for ranking", 5, 100, 20, key="scorecard_min_jc")
    
    # Aggregate advisor metrics for current period
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
    
    # Aggregate advisor metrics for previous period (for MoM trends)
    if not pp.empty:
        aa_pp = advisor_summary(pp, adv_col=ADV_COL, as_index=False).agg(
            JCs_pp=("JC_Nos.","sum"),
            NL_pp=("Net_Labour","sum"),
            NP_pp=("Net_Parts","sum")
        )
        aa_pp = aa_pp.rename(columns={ADV_COL: "Advisor_PP_Name"})
    else:
        aa_pp = pd.DataFrame()
    
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
    
    # Compute MoM trends if previous period data exists
    if not aa_pp.empty:
        aa = aa.merge(aa_pp, left_on=ADV_COL, right_on="Advisor_PP_Name", how="left")
        aa["JC_MoM"] = calc_growth_pct(aa["JCs"], aa["JCs_pp"], fill_value=0)
        aa["NL_MoM"] = calc_growth_pct(aa["NL"], aa["NL_pp"], fill_value=0)
        aa["NP_MoM"] = calc_growth_pct(aa["NP"], aa["NP_pp"], fill_value=0)
    else:
        aa["JC_MoM"] = 0
        aa["NL_MoM"] = 0
        aa["NP_MoM"] = 0
    
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
    ChartEngine.render_card("📊 Performance Scatter", fig, height=400)
    
    # Full table with trend indicators
    st.markdown(f'<div style="margin-top:{T.SPACE_6}px;"></div>', unsafe_allow_html=True)
    
    aa_sorted = aa.sort_values("Composite_Score", ascending=False).reset_index(drop=True)
    aa_sorted["Rank"] = range(1, len(aa_sorted) + 1)
    
    # Rename column for display
    aa_sorted = aa_sorted.rename(columns={ADV_COL: "Advisor Name"})
    
    display_cols = ["Rank", "Advisor Name", "Loc", "Loc_Count", "JCs", "JC_MoM", "Avg_Lab_JC", "NL_MoM", "Avg_Parts_JC", "NP_MoM",
                     "Avg_Oil_JC", "Avg_Acc_JC", "Lab_Disc_Pct", "Composite_Score"]
    dt = aa_sorted[display_cols].copy()
    # Format Loc column: show "Multi (N)" if Loc_Count > 1
    dt["Loc"] = dt.apply(lambda r: f"Multi ({r['Loc_Count']})" if r['Loc_Count'] > 1 else r['Loc'], axis=1)
    dt = dt.drop(columns=["Loc_Count"])
    dt["JCs"] = dt["JCs"].apply(fmt_num)
    
    # Format MoM trends with arrows
    def format_mom_trend(val):
        if val > 0: return f'📈 {val:.1f}%'
        if val < 0: return f'📉 {val:.1f}%'
        return '—'
    
    dt["JC_MoM"] = dt["JC_MoM"].apply(format_mom_trend)
    dt["NL_MoM"] = dt["NL_MoM"].apply(format_mom_trend)
    dt["NP_MoM"] = dt["NP_MoM"].apply(format_mom_trend)
    
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
    
    # Enhanced Advisor drill-down with MoM analysis
    st.markdown(f'<div style="margin-top:{T.SPACE_6}px;"></div>', unsafe_allow_html=True)
    
    selected_advs = st.session_state.get("filter_advisor", [])
    if len(selected_advs) == 1:
        sel_adv = selected_advs[0]
        adv_data = cp[cp[ADV_COL] == sel_adv]
        
        # Section: Advisor MoM Analysis
        st.markdown(f"### 🔍 Advisor MoM Analysis: {sel_adv}")
        st.markdown("---")
        
        # KPI cards for selected advisor
        adv_monthly = monthly_summary(adv_data, as_index=False)[["Net_Labour", "Net_Parts", "JC_Nos."]].sum()
        if not adv_monthly.empty:
            latest_val = adv_monthly["Net_Labour"].iloc[0] if len(adv_monthly) > 0 else 0
            prior_val = adv_monthly["Net_Labour"].iloc[-1] if len(adv_monthly) > 1 else 0
            mom_delta = latest_val - prior_val if len(adv_monthly) > 1 else 0
            
            # Get location average for comparison
            loc_monthly = monthly_summary(cp, as_index=False)[["Net_Labour", "Net_Parts", "JC_Nos."]].sum()
            n_advs = cp[ADV_COL].nunique()
            loc_avg = loc_monthly["Net_Labour"].iloc[0] / max(n_advs, 1) if not loc_monthly.empty else 0
            
            # Determine rank
            adv_totals = cp.groupby(ADV_COL, dropna=False)["Net_Labour"].sum().sort_values(ascending=False)
            rank = adv_totals.index.get_loc(sel_adv) + 1 if sel_adv in adv_totals.index else "N/A"
            
            KPIGrid([
                {"label": "This Month Labour", "value": fmt_inr_short(latest_val)},
                {"label": "Last Month Labour", "value": fmt_inr_short(prior_val)},
                {"label": "MoM Delta", "value": f"{fmt_inr_short(mom_delta)} ({calc_growth_pct(latest_val, prior_val, fill_value=0):.1f}%)"},
                {"label": "Location Avg", "value": fmt_inr_short(loc_avg)},
                {"label": "Rank", "value": f"#{rank}"}
            ])
        
        # MoM sparkline
        st.markdown(f'<div style="margin-top:{T.SPACE_6}px;"></div>', unsafe_allow_html=True)
        adv_monthly_full = monthly_summary(adv_data, as_index=False).agg(
            NL=("Net_Labour","sum"),
            NP=("Net_Parts","sum")
        ).reset_index().sort_values("Month_Sort")
        
        if not adv_monthly_full.empty:
            last_6 = adv_monthly_full.tail(6) if len(adv_monthly_full) >= 6 else adv_monthly_full
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=last_6["Month Name"], y=last_6["NL"], mode='lines+markers', name=sel_adv, line=dict(color=C["primary"])))
            loc_monthly_full = monthly_summary(cp, as_index=False).agg(NL=("Net_Labour","sum")).reset_index().sort_values("Month_Sort")
            loc_6 = loc_monthly_full[loc_monthly_full["Month Name"].isin(last_6["Month Name"].tolist())]
            n_adv = cp[ADV_COL].nunique()
            if not loc_6.empty and n_adv > 0:
                loc_6["Avg"] = loc_6["NL"] / n_adv
                fig.add_trace(go.Scatter(x=loc_6["Month Name"], y=loc_6["Avg"], mode='lines', name="Location Avg", line=dict(color=C["gray"], dash='dash')))
            ChartEngine.render_card(f"📈 {sel_adv} — Labour Trend (Last 6M)", fig, height=350)
        
        # Coaching notes
        st.markdown(f'<div style="margin-top:{T.SPACE_6}px;"></div>', unsafe_allow_html=True)
        notes = []
        adv_disc = calc_ratio(get_labour_discount(adv_data), get_labour_sales(adv_data), multiplier=100, fill_value=0)
        adv_parts_jc = get_net_parts(adv_data) / get_jobcard_count(adv_data) if get_jobcard_count(adv_data) > 0 else 0
        loc_parts_jc = get_net_parts(cp) / get_jobcard_count(cp) if get_jobcard_count(cp) > 0 else 0
        adv_oil_jc = adv_data["Oil_Sale_Qty"].sum() / get_jobcard_count(adv_data) if get_jobcard_count(adv_data) > 0 else 0
        
        if adv_disc > 20:
            notes.append(f"Discount control needed: {adv_disc:.1f}% labour discount is above the 20% threshold.")
        if adv_parts_jc < loc_parts_jc * 0.8:
            notes.append(f"Parts upsell opportunity: Parts/JC is below location average. Focus on recommending genuine parts.")
        if adv_oil_jc < 1:
            notes.append(f"Oil penetration low: {adv_oil_jc:.1f} litres/JC. Target oil sale on every service visit.")
        
        if notes:
            note_text = "<br>".join(notes)
            st.markdown(f'<div style="background:#FFF3CD;border-radius:8px;padding:12px;border-left:4px solid #FFC107;">'
                       f'<strong>📋 Coaching Notes:</strong><br>{note_text}</div>', unsafe_allow_html=True)
        else:
            st.success("✅ No specific coaching notes for this advisor.")
        
    else:
        st.info("Select exactly **one Advisor** from the Page Filters above to view the MoM analysis and coaching notes.")
