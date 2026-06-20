import streamlit as st

def UniversalHeader(client_name: str, report_title: str, selected_months: list, synced_at: str):
    """
    Universal Report Header matching the approved enterprise design.
    """
    
    # Official display names mapping
    DISPLAY_TITLES = {
        "Cockpit": "Cockpit",
        "Overview": "Workshop Overview",
        "Executive": "Executive Dashboard",
        "Labour": "Labour Revenue",
        "Parts": "Parts Revenue",
        "Margin": "Margin Analysis",
        "Sales Mix": "Sales Mix",
        "Discounts": "Discount Analysis",
        "Leakage Center": "Leakage Center",
        "Advisors": "Advisor Performance",
        "Advisor MoM": "Advisor MoM Performance",
        "Locations": "Location Performance",
        "Trends": "Performance Trends",
        "Targets": "Target vs Actual",
        "Reports": "Automated Reports",
        "Expense Analysis": "Expense Analysis",
        "Profit & Loss": "Profit & Loss",
        "Internal Audit": "Internal Audit",
        "Audit Intelligence": "Audit Intelligence",
        "System Health": "System Health"
    }
    official_title = DISPLAY_TITLES.get(report_title, report_title)

    # Format period
    if not selected_months:
        period_str = "All Periods"
    elif len(selected_months) == 1:
        period_str = selected_months[0]
    elif len(selected_months) == 2:
        period_str = f"{selected_months[0]} & {selected_months[1]}"
    else:
        period_str = f"{selected_months[0]} to {selected_months[-1]}"

    st.markdown(f'''
    <div class="report-header">
        <div class="rh-left">
            <div class="rh-client">{client_name}</div>
            <div class="rh-title">{official_title}</div>
            <div class="rh-period">{period_str}</div>
        </div>
        <div class="rh-right-container">
            <div class="rh-divider"></div>
            <div class="rh-right">
                <div class="rh-firm">Saurabh A Jain & Co.</div>
                <div class="rh-sub">Chartered Accountants • Internal Audit</div>
                <div class="rh-confidential-container"><span class="rh-confidential">CONFIDENTIAL</span></div>
                <div class="rh-bottom">
                    <span>🗓 Synced: {synced_at}</span>
                    <span class="rh-pipe">|</span>
                    <span>v1.0.0-rc1</span>
                </div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

def UniversalFooter():
    """
    Universal Report Footer for all pages.
    """
    st.markdown(f'''
    <div class="report-footer">
        <div class="rf-top">Strictly Confidential · For Internal Use Only · Unauthorised reproduction is strictly prohibited.</div>
        <div class="rf-bottom">
            <div>Saurabh A Jain & Co. (Chartered Accountants)</div>
            <div><a href="mailto:support@autollp.in" style="color:inherit; text-decoration:none;">support@autollp.in</a></div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

def EmptyState(message: str = "No data available for the selected filters.", icon: str = "📭"):
    """
    Standardized Empty State visualization.
    """
    from ui.design_tokens import T
    html = f'''<div class="empty-state" style="text-align:center; padding:{T.SPACE_12}px {T.SPACE_6}px; background:var(--color-surface); border-radius:{T.RADIUS_LG}px; border:1px dashed var(--color-border); margin:{T.SPACE_4}px 0;">
    <div style="font-size:32px; margin-bottom:{T.SPACE_3}px;">{icon}</div>
    <div style="color:var(--color-text-primary); font-weight:500; font-size:{T.TYPE_MD}px; margin-bottom:{T.SPACE_1}px;">No Data Found</div>
    <div style="color:var(--color-text-secondary); font-size:{T.TYPE_BASE}px;">{message}</div>
</div>'''
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)

def AlertBanner(message: str, type: str = "warning"):
    """
    Standardized Alert Banner (e.g. High Discount Warnings).
    types: warning, error, info, success
    """
    from ui.design_tokens import T
    bg_colors = {
        "warning": T.COLOR_WARNING_BG,
        "error": T.COLOR_DANGER_BG,
        "info": T.COLOR_INFO_BG,
        "success": T.COLOR_SUCCESS_BG
    }
    border_colors = {
        "warning": T.COLOR_WARNING,
        "error": T.COLOR_DANGER,
        "info": T.COLOR_PRIMARY,
        "success": T.COLOR_SUCCESS
    }
    icons = {
        "warning": "⚠️",
        "error": "🚨",
        "info": "ℹ️",
        "success": "✅"
    }
    
    bg = bg_colors.get(type, bg_colors["info"])
    border = border_colors.get(type, border_colors["info"])
    icon = icons.get(type, icons["info"])

    html = f'''<div style="background:{bg}; border-left:4px solid {border}; padding:{T.SPACE_3}px {T.SPACE_4}px; border-radius:{T.RADIUS_SM}px; margin-bottom:{T.SPACE_4}px; display:flex; align-items:center; gap:{T.SPACE_3}px;">
    <span style="font-size:18px;">{icon}</span>
    <span style="color:var(--color-text-primary); font-size:{T.TYPE_BASE}px; font-weight:500;">{message}</span>
</div>'''
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)
