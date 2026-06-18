import streamlit as st

def PageHeader(title: str, description: str = None, icon: str = None):
    """
    Standardized Page Header for all WSMIS reports.
    """
    icon_html = f'<span style="margin-right:8px;">{icon}</span>' if icon else ''
    st.markdown(f'''
    <div class="page-header">
        <h1 style="margin-bottom: 4px; display: flex; align-items: center;">{icon_html}{title}</h1>
        {"<p style='color:#6E6E73; margin-top:0; font-size:14px;'>" + description + "</p>" if description else ""}
    </div>
    ''', unsafe_allow_html=True)

def EmptyState(message: str = "No data available for the selected filters.", icon: str = "📭"):
    """
    Standardized Empty State visualization.
    """
    st.markdown(f'''
    <div class="empty-state" style="text-align:center; padding:48px 24px; background:#fff; border-radius:12px; border:1px dashed #d2d2d7; margin:16px 0;">
        <div style="font-size:32px; margin-bottom:12px;">{icon}</div>
        <div style="color:#1d1d1f; font-weight:500; font-size:16px; margin-bottom:4px;">No Data Found</div>
        <div style="color:#86868b; font-size:14px;">{message}</div>
    </div>
    ''', unsafe_allow_html=True)

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

    st.markdown(f'''
    <div style="background:{bg}; border-left:4px solid {border}; padding:12px 16px; border-radius:4px; margin-bottom:16px; display:flex; align-items:center; gap:12px;">
        <span style="font-size:18px;">{icon}</span>
        <span style="color:#1d1d1f; font-size:14px; font-weight:500;">{message}</span>
    </div>
    ''', unsafe_allow_html=True)
