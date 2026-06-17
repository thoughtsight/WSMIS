import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num
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
from utils.constants import (
    ADV_COL, CLIENTS, EXCLUDE_SERVICE_TYPES, ARENA_LOCATIONS,
    NEXA_LOCATIONS, BS_SERVICE_TYPES, MONTH_SORT_ORDER, FY_MONTHS, SERVICE_ACCOUNT,
    WS_COLORS
)
from utils.filters import (
    apply_month_filter, apply_location_filter, apply_location_group_filter,
    apply_service_type_filter, apply_advisor_filter, apply_ws_bs_filter, split_cp_pp
)

def apply_chart(fig, title, height=320, text_col=None, bar_text_pos="outside"):
    """
    Apply standard styling to a Plotly figure:
    - Embeds title INSIDE the figure (survives fullscreen)
    - Cleans up hover labels
    - Optionally formats bar text annotations as ₹X.XXCr
    """
    layout_updates = dict(
        height=height,
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(size=15, color="#1D1D1F", family="Inter"),
            x=0.01,
            xanchor="left",
            pad=dict(t=8, b=4),
        ),
        margin=dict(l=52, r=28, t=58, b=44),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            font_size=13,
            font_family="Inter",
            bordercolor="#E5E5EA",
            namelength=-1,
        ),
        xaxis=dict(
            tickfont=dict(size=12, family="Inter"),
            title_font=dict(size=13, family="Inter"),
            gridcolor="#F0F0F5",
            linecolor="#E5E5EA",
        ),
        yaxis=dict(
            tickfont=dict(size=12, family="Inter"),
            title_font=dict(size=13, family="Inter"),
            gridcolor="#F0F0F5",
            linecolor="#E5E5EA",
        ),
        font=dict(family="Inter, -apple-system, sans-serif", size=12, color="#1D1D1F"),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        legend=dict(
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#E5E5EA",
            borderwidth=1,
            font=dict(size=12, family="Inter"),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )
    fig.update_layout(**layout_updates)
    if text_col:
        fig.update_traces(
            textposition=bar_text_pos,
            textfont=dict(size=11, color="#1D1D1F", family="Inter"),
            cliponaxis=False,
        )
    return fig


def clean_hover(fig, x_label, y_label, color_label=None, y_fmt="inr"):
    """
    Replace raw column names in hover with clean business labels.
    y_fmt: 'inr' = ₹format, 'pct' = %, 'num' = comma number
    """
    if y_fmt == "inr":
        yt = "%{y:,.0f}"  # will be overridden by customdata below
    elif y_fmt == "pct":
        yt = "%{y:.2f}%"
    else:
        yt = "%{y:,.0f}"
    color_part = f"<br><b>{color_label}:</b> %{{fullData.name}}" if color_label else ""
    hover = (f"<b>{x_label}:</b> %{{x}}<br>"
             f"<b>{y_label}:</b> %{{y:,.0f}}{color_part}"
             "<extra></extra>")
    fig.update_traces(hovertemplate=hover)
    return fig


def csv_btn(df, name, key):
    st.download_button("📥 Export CSV", df.to_csv(index=False).encode("utf-8"), file_name=name, mime="text/csv", key=key)


def render_neg_labour_alert(df_cp):
    """Show a sticky red banner listing advisors with negative net labour."""
    neg = df_cp.groupby([ADV_COL,"Location Name"], dropna=False)[
        "Net_Labour"].sum().reset_index()
    neg = neg[neg["Net_Labour"] < 0].sort_values("Net_Labour")
    if neg.empty:
        return
    parts = []
    for _, r in neg.head(6).iterrows():
        parts.append(f"<b>{r[ADV_COL]}</b> ({r['Location Name']}) "
                     f"{fmt_inr(r['Net_Labour'])}")
    msg = " &nbsp;|&nbsp; ".join(parts)
    if len(neg) > 6:
        msg += f" &nbsp;+{len(neg)-6} more"
    st.markdown(
        f'<div class="neg-lab-alert">'
        f'🚨 <b>NEGATIVE NET LABOUR DETECTED</b> — Immediate review required:<br>{msg}'
        f'</div>',
        unsafe_allow_html=True
    )


def render_alerts(alerts):
    for severity, msg in alerts:
        color_map = {'red':'#FFEBE9','yellow':'#FFF3E0','blue':'#E8F0FE'}
        text_map = {'red':'#CF222E','yellow':'#E65100','blue':'#185FA5'}
        st.markdown(f"""<div style="background:{color_map[severity]};border-radius:10px;
            padding:10px 14px;margin-bottom:8px;color:{text_map[severity]};
            font-size:13px;font-weight:600;">{msg}</div>""", unsafe_allow_html=True)


def render_discount_heatmap(df, view="By Location", key_suffix="lc"):
    if df.empty:
        st.info("No data for heatmap")
        return
    if view == "By Location":
        hd = df.groupby(["Location Name", "Month Name", "Month_Sort"], as_index=False, dropna=False).agg(
            L=("Pre-GST Labour", "sum"), D=("Labour Discount", "sum")
        )
        hd["Recoverable"] = np.maximum(0, (calc_ratio(hd["D"], hd["L"], multiplier=100, fill_value=0) - 15) / 100 * hd["L"])
        hd = hd.sort_values("Month_Sort")
        hp = hd.pivot_table(index="Location Name", columns="Month Name", values="Recoverable", aggfunc="sum").fillna(0)
    else:
        top20 = advisor_summary(df, adv_col=ADV_COL, as_index=True)["Pre-GST Labour"].sum().nlargest(20).index.tolist()
        ha = df[df[ADV_COL].isin(top20)].groupby([ADV_COL, "Month Name", "Month_Sort"], as_index=False, dropna=False).agg(
            L=("Pre-GST Labour", "sum"), D=("Labour Discount", "sum")
        )
        ha["Recoverable"] = np.maximum(0, (calc_ratio(ha["D"], ha["L"], multiplier=100, fill_value=0) - 15) / 100 * ha["L"])
        ha = ha.sort_values("Month_Sort")
        hp = ha.pivot_table(index=ADV_COL, columns="Month Name", values="Recoverable", aggfunc="sum").fillna(0)
    if hp.empty:
        st.info("No heatmap data available")
        return
    fig = px.imshow(
        hp.values, x=hp.columns.tolist(), y=hp.index.tolist(),
        color_continuous_scale=["#E8F9EE", "#FFF3E0", "#FFEBE9"],
        aspect="auto", labels={"color": "Recoverable ₹"}
    )
    apply_chart(fig, f"Recoverable Leakage ₹ — {view} × Month", 400)
    st.plotly_chart(fig, width='stretch', key=f"lc_heat_{key_suffix}",
                    config={"displayModeBar": True, "displaylogo": False,
                            "modeBarButtonsToRemove": ["select2d", "lasso2d"],
                            "toImageButtonOptions": {"format": "png", "scale": 2}})


def _render_finding(finding, cause, impact, recommendation, owner, priority):
    """Renders a structured audit finding card with mandatory 6-field format."""
    colors = {
        "Critical": ("#CF222E", "#FFEBE9", "🔴"),
        "High":     ("#E65100", "#FFF3E0", "🟠"),
        "Medium":   ("#185FA5", "#E8F0FE", "🔵"),
        "Low":      ("#6E6E73", "#F5F5F7", "⚪"),
    }
    tc, bg, icon = colors.get(priority, ("#6E6E73", "#F5F5F7", "⚪"))
    st.markdown(f"""
    <div style="background:{bg};border-left:4px solid {tc};border-radius:8px;padding:14px 16px;margin-bottom:10px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
            <div style="font-weight:700;color:{tc};font-size:14px;">{icon} {finding}</div>
            <span style="background:{tc};color:#fff;font-size:10px;font-weight:600;padding:2px 10px;border-radius:20px;white-space:nowrap;margin-left:8px;">{priority}</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
            <div><div style="color:#8E8E93;font-size:10px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;">Cause</div><div style="color:#1D1D1F;font-size:12px;">{cause}</div></div>
            <div><div style="color:#8E8E93;font-size:10px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;">Impact ₹</div><div style="color:{tc};font-size:12px;font-weight:600;">{impact}</div></div>
            <div><div style="color:#8E8E93;font-size:10px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;">Recommendation</div><div style="color:#1D1D1F;font-size:12px;">{recommendation}</div></div>
            <div><div style="color:#8E8E93;font-size:10px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;">Owner</div><div style="color:#185FA5;font-size:12px;font-weight:500;">{owner}</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


