from views.shared import *
from views.components.kpi_engine import KPIEngine
from views.components.chart_engine import ChartEngine
from views.dashboard_common import inject_responsive_css




from utils.loaders import TARGET_TAB

# Import shared UI helpers from app
from ui.traffic import yoy_badge, traffic_light, tgt_badge
from ui.design_tokens import T

def render(df_act, targets_df, pairs):
    inject_responsive_css()
    PageBreadcrumb(["Performance", "Targets"])
    if df_act.empty:
        EmptyState("No data available.")
        return
    if targets_df.empty:
        st.info(
            f'📊 No targets loaded. Create a Google Sheet tab named exactly '
            f'**`{TARGET_TAB}`** in the same spreadsheet.\n\n'
            f'Format: `Month Name | Location Name | WS_Labour_Target | '
            f'BS_Labour_Target | WS_Parts_Target | BS_Parts_Target`'
        )
        return

    # df_act is already filtered by selected_months at main level, use it directly
    act = df_act
    tgt = targets_df[targets_df["Month Name"].isin(act["Month Name"].unique())]

    if tgt.empty:
        tgt_months = sorted(act["Month Name"].unique(), key=lambda x: MONTH_SORT_ORDER.get(x, 99))
        st.warning(f"No targets found for periods: {', '.join(tgt_months)}")
        return

    # aggregate actuals by location + ws/bs
    ws_act = act[act["Service_Type_Group"]=="WS"].groupby("Location Name", dropna=False).agg(
        WS_Lab=("Net_Labour","sum"), WS_Pts=("Net_Parts","sum")).reset_index()
    bs_act = act[act["Service_Type_Group"]=="BS"].groupby("Location Name", dropna=False).agg(
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
    ws_lab_a = merged["WS_Lab"].sum(); ws_lab_t = merged["WS_Labour_Target"].sum()
    bs_lab_a = merged["BS_Lab"].sum(); bs_lab_t = merged["BS_Labour_Target"].sum()
    ws_pts_a = merged["WS_Pts"].sum(); ws_pts_t = merged["WS_Parts_Target"].sum()
    bs_pts_a = merged["BS_Pts"].sum(); bs_pts_t = merged["BS_Parts_Target"].sum()
    KPIEngine.render_grid([
        {"label": "WS Labour Ach%", "value": f"{ws_lab_a/ws_lab_t*100 if ws_lab_t > 0 else 0:.1f}%",
         "sub": f"Act: {fmt_inr(ws_lab_a)} / Tgt: {fmt_inr(ws_lab_t)}", "cp": ws_lab_a, "pp": ws_lab_t},
        {"label": "BS Labour Ach%", "value": f"{bs_lab_a/bs_lab_t*100 if bs_lab_t > 0 else 0:.1f}%",
         "sub": f"Act: {fmt_inr(bs_lab_a)} / Tgt: {fmt_inr(bs_lab_t)}", "cp": bs_lab_a, "pp": bs_lab_t},
        {"label": "WS Parts Ach%",  "value": f"{ws_pts_a/ws_pts_t*100 if ws_pts_t > 0 else 0:.1f}%",
         "sub": f"Act: {fmt_inr(ws_pts_a)} / Tgt: {fmt_inr(ws_pts_t)}", "cp": ws_pts_a, "pp": ws_pts_t},
        {"label": "BS Parts Ach%",  "value": f"{bs_pts_a/bs_pts_t*100 if bs_pts_t > 0 else 0:.1f}%",
         "sub": f"Act: {fmt_inr(bs_pts_a)} / Tgt: {fmt_inr(bs_pts_t)}", "cp": bs_pts_a, "pp": bs_pts_t},
    ], cols=4)

    section_title("🎯 Location-wise Target Achievement")

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
                                     "BS_Labour_Target":T.COLOR_WARNING_BG,"BS_Lab":C["orange"]})
    ChartEngine.apply_chart(fig, "🎯 WS & BS Labour — Target vs Actual by Location", 400, text_col="Label")
    fig.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>Location: %{x}<br>Amount: %{customdata[0]}<extra></extra>",
        customdata=bar_m[["Label"]].values
    )
    st.plotly_chart(fig, width='stretch', key="tgt_bar",
                    config={"displayModeBar": True, "displaylogo": False,
                            "modeBarButtonsToRemove": ["select2d","lasso2d"],
                            "toImageButtonOptions": {"format":"png","scale":2}})
    UniversalFooter()

