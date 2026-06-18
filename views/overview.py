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
from utils.constants import ADV_COL, MP_COLORS, C, LOC_COLORS
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num

# Import new Phase B UI Components
from ui.components import KPIGrid, ChartCard, TableCard

def render(df, pairs, alerts, comparison_mode=True, selected_months=None):
    with st.spinner("Computing Overview..."):
        if df.empty:
            return

    if alerts:
        render_alerts(alerts)

    cp_months = [p[0] for p in pairs]
    pp_months = [p[1] for p in pairs]
    cp = apply_month_filter(df, "Month Name", cp_months)
    pp = apply_month_filter(df, "Month Name", pp_months)
    
    # Top insight cards
    if not cp.empty:
        c1, c2, c3 = st.columns(3)
        
        # Best location by Net Labour
        with c1:
            _s = location_summary(cp, as_index=True)["Net_Labour"].sum()
            best_loc = _s.idxmax() if not getattr(locals().get('cp', None), 'empty', True) else "N/A" if not _s.empty and _s.max() > 0 else "N/A"
            best_loc_val = _s.max() if not _s.empty else 0
            if best_loc != "N/A":
                st.markdown(f"""
                <div class="insight-card pos">
                    <div class="insight-title">🏆 Best Location</div>
                    <div class="insight-stat">{best_loc} with {fmt_inr(best_loc_val)} Net Labour</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">🏆 Best Location</div>
                    <div class="insight-stat">No data available</div>
                </div>""", unsafe_allow_html=True)
        
        # Highest discount advisor
        with c2:
            adv_disc = advisor_summary(cp, adv_col=ADV_COL, as_index=True).agg(L=("Pre-GST Labour","sum"), D=("Labour Discount","sum"))
            adv_disc["D%"] = calc_ratio(adv_disc["D"], adv_disc["L"], multiplier=100, fill_value=np.nan)
            if not adv_disc.empty and adv_disc["L"].sum() > 0:
                _high_disc = adv_disc[adv_disc["L"] > 10000]["D%"] if len(adv_disc[adv_disc["L"] > 10000]) > 0 else adv_disc["D%"]
                worst_adv = _high_disc.idxmax() if not getattr(locals().get('cp', None), 'empty', True) else "N/A" if not _high_disc.empty else "N/A"
                worst_adv_pct = adv_disc.loc[worst_adv, "D%"] if worst_adv != "N/A" and worst_adv in adv_disc.index else 0
                if worst_adv != "N/A":
                    st.markdown(f"""
                    <div class="insight-card warn">
                        <div class="insight-title">⚠️ Highest Discount</div>
                        <div class="insight-stat">{worst_adv[:15]} at {worst_adv_pct:.1f}% labour discount</div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">⚠️ Highest Discount</div>
                    <div class="insight-stat">No data available</div>
                </div>""", unsafe_allow_html=True)
        
        # Strongest MoM growth
        with c3:
            cp_unique_months = cp["Month Name"].nunique()
            if cp_unique_months >= 2:
                cp_sorted = cp.sort_values("Month_Sort")
                first_month = cp_sorted["Month Name"].iloc[0]
                last_month = cp_sorted["Month Name"].iloc[-1]
                first_data = cp_sorted[cp_sorted["Month Name"] == first_month].groupby("Location Name", dropna=False)["Net_Labour"].sum()
                last_data = cp_sorted[cp_sorted["Month Name"] == last_month].groupby("Location Name", dropna=False)["Net_Labour"].sum()
                mom_growth = {}
                for loc in set(first_data.index) | set(last_data.index):
                    fv = first_data.get(loc, 0)
                    lv = last_data.get(loc, 0)
                    if fv > 0:
                        mom_growth[loc] = calc_growth_pct(lv, fv, fill_value=0)
                if mom_growth:
                    best_mom = max(mom_growth, key=mom_growth.get)
                    best_mom_val = mom_growth[best_mom]
                    st.markdown(f"""
                    <div class="insight-card pos">
                        <div class="insight-title">📈 Strongest Growth</div>
                        <div class="insight-stat">{best_mom} grew {best_mom_val:.1f}% MoM</div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="insight-card">
                        <div class="insight-title">📈 Strongest Growth</div>
                        <div class="insight-stat">Need 2+ months for MoM</div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">📈 Strongest Growth</div>
                    <div class="insight-stat">Need 2+ months for MoM</div>
                </div>""", unsafe_allow_html=True)
    
    def s(d, c): return d[c].sum() if not d.empty else 0
    cp_jc, pp_jc = s(cp,"JC_Nos."), s(pp,"JC_Nos.")
    cp_lab, pp_lab = s(cp,"Net_Labour"), s(pp,"Net_Labour")
    cp_pts, pp_pts = s(cp,"Net_Parts"), s(pp,"Net_Parts")
    cp_mar, pp_mar = calculate_total_margin(cp), calculate_total_margin(pp)
    cp_avg = cp_lab/cp_jc if cp_jc else 0; pp_avg = pp_lab/pp_jc if pp_jc else 0

    
    KPIGrid([
        {"label": "Total JCs", "value": fmt_num(cp_jc), "cp": cp_jc, "pp": pp_jc},
        {"label": "Net Labour", "value": fmt_inr(cp_lab), "cp": cp_lab, "pp": pp_lab},
        {"label": "Net Parts", "value": fmt_inr(cp_pts), "cp": cp_pts, "pp": pp_pts},
        {"label": "Total Margin", "value": fmt_inr(cp_mar), "cp": cp_mar, "pp": pp_mar},
        {"label": "Avg Labour/JC", "value": fmt_inr(cp_avg), "cp": cp_avg, "pp": pp_avg}
    ])
    
    st.markdown('<div style="margin-top:24px;"></div>', unsafe_allow_html=True)
    
    cp_ws = cp[cp["MP_PB"]=="MP"]; pp_ws = pp[pp["MP_PB"]=="MP"]
    cp_bs = cp[cp["MP_PB"]=="PB"]; pp_bs = pp[pp["MP_PB"]=="PB"]
    
    KPIGrid([
        {"label": "WS JCs", "value": fmt_num(s(cp_ws,"JC_Nos.")), "cp": s(cp_ws,"JC_Nos."), "pp": s(pp_ws,"JC_Nos.")},
        {"label": "WS Net Labour", "value": fmt_inr(s(cp_ws,"Net_Labour")), "cp": s(cp_ws,"Net_Labour"), "pp": s(pp_ws,"Net_Labour")},
        {"label": "WS Margin", "value": fmt_inr(calculate_total_margin(cp_ws)), "cp": calculate_total_margin(cp_ws), "pp": calculate_total_margin(pp_ws)},
        {"label": "BS JCs", "value": fmt_num(s(cp_bs,"JC_Nos.")), "cp": s(cp_bs,"JC_Nos."), "pp": s(pp_bs,"JC_Nos.")},
        {"label": "BS Net Labour", "value": fmt_inr(s(cp_bs,"Net_Labour")), "cp": s(cp_bs,"Net_Labour"), "pp": s(pp_bs,"Net_Labour")},
        {"label": "BS Margin", "value": fmt_inr(calculate_total_margin(cp_bs)), "cp": calculate_total_margin(cp_bs), "pp": calculate_total_margin(pp_bs)}
    ])
    
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        wbs_data = cp.groupby(["Month_Sort","Month Name","MP_PB"], as_index=False, dropna=False)["Net_Labour"].sum().sort_values("Month_Sort")
        wbs_data = wbs_data.rename(columns={"MP_PB":"Type","Month Name":"Month","Net_Labour":"Net Labour"})
        wbs_data["Label"] = wbs_data["Net Labour"].apply(fmt_inr_short)
        fig = px.line(
            cp.groupby(["Month_Sort","Month Name","MP_PB"], as_index=False, dropna=False)["Net_Labour"].sum()
               .sort_values("Month_Sort")
               .rename(columns={"MP_PB":"Type","Month Name":"Month","Net_Labour":"Net Labour (₹)"}),
            x="Month", y="Net Labour (₹)", color="Type", markers=True,
            color_discrete_map={"MP":C["primary"],"PB":C["orange"]},
        )
        fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Month: %{x}<br>Net Labour: ₹%{y:,.0f}<extra></extra>")
        ChartCard("📈 Monthly Net Labour Trend", fig, height=320)
        
    with c2:
        lr = cp.groupby(["Location Name","Location Group"], as_index=False, dropna=False)["Net_Labour"].sum()\
               .sort_values("Net_Labour",ascending=True)\
               .rename(columns={"Net_Labour":"Net Labour (₹)","Location Name":"Location","Location Group":"Group"})
        lr["Label"] = lr["Net Labour (₹)"].apply(fmt_inr_short)
        fig = px.bar(lr, x="Net Labour (₹)", y="Location", color="Group", orientation="h",
                     color_discrete_map=LOC_COLORS, text="Label")
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Net Labour: %{customdata[0]}<br>Group: %{fullData.name}<extra></extra>",
                          customdata=lr[["Label"]].values, textposition="outside")
        ChartCard("🏢 Location Ranking — Net Labour CP", fig, height=340)
        
    c1, c2 = st.columns(2)
    with c1:
        sd = cp[cp["Service Type"] != "Wash"].groupby("Service Type", as_index=False, dropna=False)["JC_Nos."].sum()
        fig = px.pie(sd, values="JC_Nos.", names="Service Type", hole=0.6,
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_traces(texttemplate="%{label}<br><b>%{value:,}</b>",
                          hovertemplate="<b>%{label}</b><br>JCs: %{value:,}<br>Share: %{percent}<extra></extra>")
        fig.update_layout(legend=dict(orientation="v", x=1.05, y=0.5))
        ChartCard("🔧 Service Type Mix — CP JCs", fig, height=300)
        
    with c2:
        wd = cp.groupby("MP_PB", as_index=False, dropna=False)["Net_Labour"].sum()\
               .rename(columns={"MP_PB":"Type","Net_Labour":"Net Labour (₹)"})
        fig = px.pie(wd, values="Net Labour (₹)", names="Type", hole=0.6,
                     color="Type", color_discrete_map=MP_COLORS)
        fig.update_traces(
            texttemplate="%{label}<br><b>%{percent}</b>",
            hovertemplate="<b>%{label} Labour</b><br>Amount: ₹%{value:,.0f}<br>Share: %{percent}<extra></extra>"
        )
        fig.update_layout(legend=dict(orientation="v", x=1.05, y=0.5))
        ChartCard("⚖️ WS vs BS Labour Split — CP", fig, height=300)

    
    summ = monthly_summary(cp, as_index=False).agg(
        JCs=("JC_Nos.","sum"), L=("Net_Labour","sum"), P=("Net_Parts","sum"), M=("Total Margin","sum"),
        GL=("Pre-GST Labour","sum"), DL=("Labour Discount","sum"), GP=("Pre-GST Parts","sum"), DP=("Parts Discount","sum")
    ).sort_values("Month_Sort")
    summ["Lab Disc%"] = np.where(summ["GL"]>0, summ["DL"]/summ["GL"]*100, 0)
    summ["Parts Disc%"] = np.where(summ["GP"]>0, summ["DP"]/summ["GP"]*100, 0)
    summ["Avg Lab/JC"] = np.where(summ["JCs"]>0, summ["L"]/summ["JCs"], 0)
    
    dt = pd.DataFrame()
    dt["Month"] = summ["Month Name"]
    dt["JCs"] = summ["JCs"].apply(fmt_num)
    dt["Net Labour"] = summ["L"].apply(fmt_inr)
    dt["Net Parts"] = summ["P"].apply(fmt_inr)
    dt["Total Margin"] = summ["M"].apply(fmt_inr)
    dt["Lab Disc%"] = summ["Lab Disc%"].apply(lambda x: f"{x:.2f}%")
    dt["Parts Disc%"] = summ["Parts Disc%"].apply(lambda x: f"{x:.2f}%")
    dt["Avg Lab/JC"] = summ["Avg Lab/JC"].apply(fmt_inr)
    
    tr = {"Month": "TOTAL", "JCs": fmt_num(summ["JCs"].sum()), "Net Labour": fmt_inr(summ["L"].sum()),
          "Net Parts": fmt_inr(summ["P"].sum()), "Total Margin": fmt_inr(summ["M"].sum()),
          "Lab Disc%": f"{(summ['DL'].sum()/summ['GL'].sum()*100 if summ['GL'].sum()>0 else 0):.2f}%",
          "Parts Disc%": f"{(summ['DP'].sum()/summ['GP'].sum()*100 if summ['GP'].sum()>0 else 0):.2f}%",
          "Avg Lab/JC": fmt_inr(summ["L"].sum()/summ["JCs"].sum() if summ["JCs"].sum()>0 else 0)}
    dt = pd.concat([dt, pd.DataFrame([tr])])
    
    # Render with TableCard
    TableCard(dt, height=400)
    
    # Use standardized export buttons
    from services.export_service import ExportMeta
    from ui.export_buttons import render_export_buttons
    meta = ExportMeta(report_title="Monthly Summary", location="All", date_range="")
    render_export_buttons(summ, meta, formats=["csv", "excel"], key_prefix="ov", collapsed=False)
