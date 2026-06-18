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
from utils.constants import ADV_COL, MP_COLORS, C, MONTH_SORT_ORDER
from utils.loaders import TARGET_TAB

# Import shared UI helpers from app
from ui.kpi_cards import kpi
from ui.tables import html_table
from ui.traffic import yoy_badge, traffic_light, tgt_badge
from ui.helpers import apply_chart, clean_hover, _render_finding, csv_btn
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num

def render(df_act, targets_df, pairs):
    with st.spinner("Loading Targets..."): pass
    if df_act.empty:
        from ui.components.core import EmptyState
        EmptyState("No data available.")
        return
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    if targets_df.empty:
        st.info(
            f'📊 No targets loaded. Create a Google Sheet tab named exactly '
            f'**`{TARGET_TAB}`** in the same spreadsheet.\n\n'
            f'Format: `Month Name | Location Name | WS_Labour_Target | '
            f'BS_Labour_Target | WS_Parts_Target | BS_Parts_Target`'
        )
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # df_act is already filtered by selected_months at main level, use it directly
    act = df_act.copy()
    tgt = targets_df[targets_df["Month Name"].isin(act["Month Name"].unique())]

    if tgt.empty:
        tgt_months = sorted(act["Month Name"].unique(), key=lambda x: MONTH_SORT_ORDER.get(x, 99))
        st.warning(f"No targets found for periods: {', '.join(tgt_months)}")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # aggregate actuals by location + ws/bs
    ws_act = act[act["MP_PB"]=="MP"].groupby("Location Name", dropna=False).agg(
        WS_Lab=("Net_Labour","sum"), WS_Pts=("Net_Parts","sum")).reset_index()
    bs_act = act[act["MP_PB"]=="PB"].groupby("Location Name", dropna=False).agg(
        BS_Lab=("Net_Labour","sum"), BS_Pts=("Net_Parts","sum")).reset_index()

    # aggregate targets
    tgt_g = location_summary(tgt, as_index=True).agg(
        WS_Labour_Target=("WS_Labour_Target","sum"),
        BS_Labour_Target=("BS_Labour_Target","sum"),
        WS_Parts_Target=("WS_Parts_Target","sum"),
        BS_Parts_Target=("BS_Parts_Target","sum"),
    ).reset_index()

    merged = tgt_g.merge(ws_act, on="Location Name", how="left")\
                  .merge(bs_act, on="Location Name", how="left").fillna(0)

    if merged.empty:
        st.info("No target data found for the selected period. Please check the MP_PB_Targets sheet.")
        return

    def ach(act_v, tgt_v):
        return calc_achievement_pct(act_v, tgt_v, fill_value=np.nan)

    merged["WS_Lab_Ach"] = merged.apply(lambda r: ach(r["WS_Lab"],r["WS_Labour_Target"]), axis=1)
    merged["BS_Lab_Ach"] = merged.apply(lambda r: ach(r["BS_Lab"],r["BS_Labour_Target"]), axis=1)
    merged["WS_Pts_Ach"] = merged.apply(lambda r: ach(r["WS_Pts"],r["WS_Parts_Target"]), axis=1)
    merged["BS_Pts_Ach"] = merged.apply(lambda r: ach(r["BS_Pts"],r["BS_Parts_Target"]), axis=1)

    # Summary KPIs
    c = st.columns(4)
    def kpi_tgt(col, lab, act_col, tgt_col):
        t = merged[tgt_col].sum(); a = merged[act_col].sum()
        p = a/t*100 if t > 0 else 0
        with col: kpi(lab, f"{p:.1f}%", f"Act: {fmt_inr(a)} / Tgt: {fmt_inr(t)}",
                       cp=a, pp=t)
    kpi_tgt(c[0], "WS Labour Ach%", "WS_Lab", "WS_Labour_Target")
    kpi_tgt(c[1], "BS Labour Ach%", "BS_Lab", "BS_Labour_Target")
    kpi_tgt(c[2], "WS Parts Ach%",  "WS_Pts", "WS_Parts_Target")
    kpi_tgt(c[3], "BS Parts Ach%",  "BS_Pts", "BS_Parts_Target")

    st.markdown('<div class="section-title" style="margin-top:16px">'
                '🎯 Location-wise Target Achievement</div>', unsafe_allow_html=True)

    rows = []
    for _, r in merged.sort_values("WS_Lab_Ach", ascending=False).iterrows():
        rows.append({
            "Location": r["Location Name"],
            "WS Lab Target": fmt_inr(r["WS_Labour_Target"]),
            "WS Lab Actual": fmt_inr(r["WS_Lab"]),
            "WS Lab Ach": tgt_badge(r["WS_Lab_Ach"]) if not np.isnan(r["WS_Lab_Ach"]) else "—",
            "WS Lab Gap": fmt_inr(r["WS_Lab"]-r["WS_Labour_Target"]),
            "BS Lab Target": fmt_inr(r["BS_Labour_Target"]),
            "BS Lab Actual": fmt_inr(r["BS_Lab"]),
            "BS Lab Ach": tgt_badge(r["BS_Lab_Ach"]) if not np.isnan(r["BS_Lab_Ach"]) else "—",
            "WS Pts Ach": tgt_badge(r["WS_Pts_Ach"]) if not np.isnan(r["WS_Pts_Ach"]) else "—",
            "BS Pts Ach": tgt_badge(r["BS_Pts_Ach"]) if not np.isnan(r["BS_Pts_Ach"]) else "—",
        })

    # Total row
    t_cols = ["WS_Labour_Target", "WS_Lab", "BS_Labour_Target", "BS_Lab", "WS_Parts_Target", "WS_Pts", "BS_Parts_Target", "BS_Pts"]
    t_sums = merged[[c for c in t_cols if c in merged.columns]].sum()
    ws_lt = t_sums.get("WS_Labour_Target", 0)
    ws_la = t_sums.get("WS_Lab", 0)
    bs_lt = t_sums.get("BS_Labour_Target", 0)
    bs_la = t_sums.get("BS_Lab", 0)
    ws_pt = t_sums.get("WS_Parts_Target", 0)
    ws_pa = t_sums.get("WS_Pts", 0)
    bs_pt = t_sums.get("BS_Parts_Target", 0)
    bs_pa = t_sums.get("BS_Pts", 0)

    rows.append({
        "Location": "TOTAL",
        "WS Lab Target": fmt_inr(ws_lt),
        "WS Lab Actual": fmt_inr(ws_la),
        "WS Lab Ach": tgt_badge(ws_la/ws_lt*100 if ws_lt > 0 else 0),
        "WS Lab Gap": fmt_inr(ws_la - ws_lt),
        "BS Lab Target": fmt_inr(bs_lt),
        "BS Lab Actual": fmt_inr(bs_la),
        "BS Lab Ach": tgt_badge(bs_la/bs_lt*100 if bs_lt > 0 else 0),
        "WS Pts Ach": tgt_badge(ws_pa/ws_pt*100 if ws_pt > 0 else 0),
        "BS Pts Ach": tgt_badge(bs_pa/bs_pt*100 if bs_pt > 0 else 0),
    })
    html_table(pd.DataFrame(rows), total_row=True, height="500px")
    csv_btn(merged, "target_vs_actual.csv", "tgt_csv")

    # Chart: Grouped Bar — WS Labour Target vs Actual
    bar_d = merged[["Location Name","WS_Labour_Target","WS_Lab","BS_Labour_Target","BS_Lab"]]
    bar_m = pd.melt(bar_d, id_vars="Location Name",
                    value_vars=["WS_Labour_Target","WS_Lab","BS_Labour_Target","BS_Lab"],
                    var_name="Series", value_name="Amount")
    bar_m["Label"] = bar_m["Amount"].apply(fmt_inr_short)
    fig = px.bar(bar_m, x="Location Name", y="Amount", color="Series", barmode="group",
                 text="Label",
                 color_discrete_map={"WS_Labour_Target":C["gray"],"WS_Lab":C["primary"],
                                     "BS_Labour_Target":"#FFD6A5","BS_Lab":C["orange"]})
    apply_chart(fig, "🎯 WS & BS Labour — Target vs Actual by Location", 400, text_col="Label")
    fig.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>Location: %{x}<br>Amount: %{customdata[0]}<extra></extra>",
        customdata=bar_m[["Label"]].values
    )
    st.plotly_chart(fig, width='stretch', key="tgt_bar",
                    config={"displayModeBar": True, "displaylogo": False,
                            "modeBarButtonsToRemove": ["select2d","lasso2d"],
                            "toImageButtonOptions": {"format":"png","scale":2}})
    st.markdown('</div>', unsafe_allow_html=True)
