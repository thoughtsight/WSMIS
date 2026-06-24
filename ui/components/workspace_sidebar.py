import streamlit as st
from services.route_service import set_business_unit, set_client, set_location, get_workspace

def _on_bu_change():
    """Callback triggered when Business Unit widget changes."""
    # Read from the widget key
    new_val = st.session_state.get("workspace_bu_widget")
    # Call the stateless setter to update stored value and handle cascade
    set_business_unit(new_val)

def _on_client_change():
    """Callback triggered when Client widget changes."""
    new_val = st.session_state.get("workspace_client_widget")
    set_client(new_val)
    if new_val:
        st.session_state["client_sel"] = new_val

def _on_location_change():
    """Callback triggered when Location widget changes."""
    new_val = st.session_state.get("workspace_location_widget")
    set_location(new_val)

def render_workspace_sidebar():
    """Renders the workspace filters in the sidebar."""
    st.sidebar.markdown("### 🏢 Workspace")
    
    # 1. Fetch user access tree and options
    access_tree = st.session_state.get("user_access_tree", {})
    bu_options = list(access_tree.keys())
    
    # Get current stored values
    current_bu, current_client, current_loc = get_workspace()
    
    # Compute BU index
    bu_index = bu_options.index(current_bu) if current_bu in bu_options else 0 if current_bu is None and len(bu_options) == 1 else None
    if bu_index is None and current_bu is None and bu_options:
        bu_options_display = ["-- Select BU --"] + bu_options
        bu_index = 0
    elif current_bu is None:
        bu_options_display = []
        bu_index = 0
    else:
        bu_options_display = bu_options
        bu_index = bu_options.index(current_bu)

    selected_bu_display = st.sidebar.selectbox(
        "Business Unit",
        options=bu_options_display,
        index=bu_index,
        key="workspace_bu_widget",
        on_change=_on_bu_change
    )
    
    # Re-evaluate current_bu based on selection for dependent dropdowns
    # Note: st.selectbox actually updates session state immediately on click, but
    # to be safe, the callback handles setting the REAL stored value.
    # We use current_bu from get_workspace() to compute dependent options during normal render.
    
    client_options = []
    if current_bu and current_bu in access_tree:
        client_options = list(access_tree[current_bu].keys())
        
    client_options_display = ["-- Select Client --"] + client_options if current_client is None else client_options
    client_index = 0 if current_client is None else client_options.index(current_client) if current_client in client_options else 0

    st.sidebar.selectbox(
        "Client",
        options=client_options_display,
        index=client_index,
        key="workspace_client_widget",
        on_change=_on_client_change,
        disabled=not bool(current_bu)
    )
    
    loc_options = []
    if current_bu and current_client and current_bu in access_tree and current_client in access_tree[current_bu]:
        loc_options = access_tree[current_bu][current_client]
        
    loc_options_display = ["-- Select Location --"] + loc_options if current_loc is None else loc_options
    loc_index = 0 if current_loc is None else loc_options.index(current_loc) if current_loc in loc_options else 0

    st.sidebar.selectbox(
        "Location",
        options=loc_options_display,
        index=loc_index,
        key="workspace_location_widget",
        on_change=_on_location_change,
        disabled=not bool(current_client)
    )
    st.sidebar.markdown("---")

def render_scope_indicator():
    """Renders a badge showing the active workspace scope."""
    bu, client, loc = get_workspace()
    
    parts = []
    parts.append(bu if bu else "[Select BU]")
    parts.append(client if client else "[Select Client]")
    parts.append(loc if loc else "[Select Location]")
    
    path_str = " › ".join(parts)
    
    st.markdown(
        f'''
        <div style="padding: 0.5rem 1rem; background-color: #f8f9fa; border-radius: 4px; border-left: 4px solid #0066cc; margin-bottom: 1rem;">
            <span style="color: #6c757d; font-size: 0.9rem; font-weight: 500;">WORKSPACE:</span> 
            <span style="color: #212529; font-weight: 600; margin-left: 8px;">{path_str}</span>
        </div>
        ''',
        unsafe_allow_html=True
    )
