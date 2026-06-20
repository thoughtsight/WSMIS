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
    NEXA_LOCATIONS, PB_SERVICE_TYPES, MONTH_SORT_ORDER, FY_MONTHS, SERVICE_ACCOUNT,
    MP_COLORS
)
from utils.filters import (
    apply_month_filter, apply_location_filter, apply_location_group_filter,
    apply_service_type_filter, apply_advisor_filter, apply_mp_pb_filter, split_cp_pp
)

def apply_chart(fig, title, height=360, text_col=None, bar_text_pos="outside", size="medium"):
    """
    Apply Executive Light styling to a Plotly figure.

    Args:
        fig:          Plotly Figure
        title:        Chart title string
        height:       Chart height in pixels (default 360 — token medium)
        text_col:     If set, formats bar text annotations
        bar_text_pos: Text position for bar annotations
        size:         Token size hint — "small"|"medium"|"large"|"full"
    """
    # Token-aligned sizes per chart size
    from ui.design_tokens import T
    SIZES = {
        "small":  {"title": 14, "tick": 11, "label": 11, "legend": 11, "margin": dict(l=48, r=20, t=40, b=40)},
        "medium": {"title": 16, "tick": 12, "label": 12, "legend": 12, "margin": dict(l=52, r=24, t=52, b=44)},
        "large":  {"title": 18, "tick": 13, "label": 13, "legend": 13, "margin": dict(l=60, r=32, t=60, b=52)},
        "full":   {"title": 22, "tick": 14, "label": 14, "legend": 14, "margin": dict(l=72, r=40, t=72, b=60)},
    }
    s = SIZES.get(size, SIZES["medium"])
    font_stack = T.FONT_FAMILY

    layout_updates = dict(
        height=height,
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(size=s["title"], color=T.COLOR_TEXT_PRIMARY, family=font_stack, weight=700),
            x=0.01,
            xanchor="left",
            pad=dict(t=8, b=4),
        ),
        margin=s["margin"],
        hoverlabel=dict(
            bgcolor=T.COLOR_SURFACE,
            font_size=13,
            font_family=font_stack,
            bordercolor=T.COLOR_BORDER,
            namelength=-1,
        ),
        xaxis=dict(
            tickfont=dict(size=s["tick"], family=font_stack),
            title_font=dict(size=s["tick"] + 1, family=font_stack),
            gridcolor=T.COLOR_SURFACE2,
            linecolor=T.COLOR_BORDER,
        ),
        yaxis=dict(
            tickfont=dict(size=s["tick"], family=font_stack),
            title_font=dict(size=s["tick"] + 1, family=font_stack),
            gridcolor=T.COLOR_SURFACE2,
            linecolor=T.COLOR_BORDER,
        ),
        font=dict(family=font_stack, size=s["tick"], color=T.COLOR_TEXT_PRIMARY),
        paper_bgcolor=T.COLOR_SURFACE,
        plot_bgcolor=T.COLOR_SURFACE,
        legend=dict(
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor=T.COLOR_BORDER,
            borderwidth=1,
            font=dict(size=s["legend"], family=font_stack),
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
            textfont=dict(size=s["label"], color=T.COLOR_TEXT_PRIMARY, family=font_stack),
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
    from ui.export_buttons import render_export_buttons
    from services.export_service import ExportMeta
    title = name.replace(".csv", "").replace("_", " ").title()
    meta = ExportMeta(report_title=title)
    render_export_buttons(df, meta, formats=["csv"], key_prefix=key, collapsed=True)

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
    from ui.design_tokens import T
    for severity, msg in alerts:
        color_map = {'red':T.COLOR_DANGER_BG,'yellow':T.COLOR_WARNING_BG,'blue':T.COLOR_INFO_BG}
        text_map = {'red':T.COLOR_DANGER,'yellow':T.COLOR_WARNING,'blue':T.COLOR_PRIMARY}
        st.markdown(f"""<div style="background:{color_map[severity]};border-radius:{T.RADIUS_LG}px;
            padding:{T.SPACE_2}px {T.SPACE_3}px;margin-bottom:{T.SPACE_2}px;color:{text_map[severity]};
            font-size:{T.TYPE_BASE}px;font-weight:600;">{msg}</div>""", unsafe_allow_html=True)


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
    from ui.design_tokens import T
    fig = px.imshow(
        hp.values, x=hp.columns.tolist(), y=hp.index.tolist(),
        color_continuous_scale=[T.COLOR_SUCCESS_BG, T.COLOR_WARNING_BG, T.COLOR_DANGER_BG],
        aspect="auto", labels={"color": "Recoverable ₹"}
    )
    apply_chart(fig, f"Recoverable Leakage ₹ — {view} × Month", 400)
    st.plotly_chart(fig, width='stretch', key=f"lc_heat_{key_suffix}",
                    config={"displayModeBar": True, "displaylogo": False,
                            "modeBarButtonsToRemove": ["select2d", "lasso2d"],
                            "toImageButtonOptions": {"format": "png", "scale": 2}})


def _render_finding(finding, cause, impact, recommendation, owner, priority):
    """Renders a structured audit finding card with mandatory 6-field format."""
    from ui.design_tokens import T
    colors = {
        "Critical": (T.COLOR_DANGER, T.COLOR_DANGER_BG, "🔴"),
        "High":     (T.COLOR_WARNING, T.COLOR_WARNING_BG, "🟠"),
        "Medium":   (T.COLOR_PRIMARY, T.COLOR_INFO_BG, "🔵"),
        "Low":      (T.COLOR_TEXT_SECONDARY, T.COLOR_SURFACE2, "⚪"),
    }
    tc, bg, icon = colors.get(priority, (T.COLOR_TEXT_SECONDARY, T.COLOR_SURFACE2, "⚪"))
    st.markdown(f"""
    <div style="background:{bg};border-left:4px solid {tc};border-radius:{T.RADIUS_MD}px;padding:{T.SPACE_3}px {T.SPACE_4}px;margin-bottom:{T.SPACE_2}px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:{T.SPACE_2}px;">
            <div style="font-weight:700;color:{tc};font-size:{T.TYPE_BASE}px;">{icon} {finding}</div>
            <span style="background:{tc};color:var(--color-surface);font-size:{T.TYPE_XS}px;font-weight:600;padding:2px 10px;border-radius:20px;white-space:nowrap;margin-left:{T.SPACE_2}px;">{priority}</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:{T.SPACE_2}px;">
            <div><div style="color:var(--color-text-tertiary);font-size:{T.TYPE_XS}px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;">Cause</div><div style="color:var(--color-text-primary);font-size:{T.TYPE_SM}px;">{cause}</div></div>
            <div><div style="color:var(--color-text-tertiary);font-size:{T.TYPE_XS}px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;">Impact ₹</div><div style="color:{tc};font-size:{T.TYPE_SM}px;font-weight:600;">{impact}</div></div>
            <div><div style="color:var(--color-text-tertiary);font-size:{T.TYPE_XS}px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;">Recommendation</div><div style="color:var(--color-text-primary);font-size:{T.TYPE_SM}px;">{recommendation}</div></div>
            <div><div style="color:var(--color-text-tertiary);font-size:{T.TYPE_XS}px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;">Owner</div><div style="color:var(--color-primary);font-size:{T.TYPE_SM}px;font-weight:500;">{owner}</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


