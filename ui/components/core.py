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
    html = f'''<div class="empty-state" style="text-align:center; padding:48px 24px; background:#fff; border-radius:12px; border:1px dashed #d2d2d7; margin:16px 0;">
    <div style="font-size:32px; margin-bottom:12px;">{icon}</div>
    <div style="color:#1d1d1f; font-weight:500; font-size:16px; margin-bottom:4px;">No Data Found</div>
    <div style="color:#86868b; font-size:14px;">{message}</div>
</div>'''
    st.markdown(html, unsafe_allow_html=True)

def AlertBanner(message: str, type: str = "warning"):
    """
    Standardized Alert Banner (e.g. High Discount Warnings).
    types: warning, error, info, success
    """
    bg_colors = {
        "warning": "#FFF8E6",
        "error": "#FEECEB",
        "info": "#E5F4FB",
        "success": "#E8F5E9"
    }
    border_colors = {
        "warning": "#FFCC00",
        "error": "#FF3B30",
        "info": "#007AFF",
        "success": "#34C759"
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

    html = f'''<div style="background:{bg}; border-left:4px solid {border}; padding:12px 16px; border-radius:4px; margin-bottom:16px; display:flex; align-items:center; gap:12px;">
    <span style="font-size:18px;">{icon}</span>
    <span style="color:#1d1d1f; font-size:14px; font-weight:500;">{message}</span>
</div>'''
    st.markdown(html, unsafe_allow_html=True)
