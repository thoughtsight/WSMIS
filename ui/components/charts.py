import streamlit as st
import plotly.graph_objects as go
from typing import Optional

def ChartCard(title: str, fig: go.Figure, description: Optional[str] = None, height: int = 400):
    """
    Standardized Chart Card wrapper.
    Ensures charts are displayed in a clean, consistent enterprise card.
    """
    from ui.design_tokens import T
    # Enforce standard responsive layout configurations without overwriting the chart's core data
    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        height=height,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family=T.FONT_FAMILY, color=T.COLOR_TEXT_PRIMARY),
        hoverlabel=dict(bgcolor=T.COLOR_SURFACE, font_size=T.TYPE_BASE, font_family=T.FONT_FAMILY)
    )
    
    html = f'''<div class="chart-card" style="background:var(--color-surface); border-radius:{T.RADIUS_LG}px; padding:{T.SPACE_4}px; border:1px solid var(--color-border); box-shadow:var(--shadow-sm); margin-bottom:{T.SPACE_4}px;">
    <div style="font-size:{T.TYPE_MD}px; font-weight:600; color:var(--color-text-primary); margin-bottom:{T.SPACE_1}px;">{title}</div>
    {f"<div style='font-size:{T.TYPE_BASE}px; color:var(--color-text-secondary); margin-bottom:{T.SPACE_4}px;'>{description}</div>" if description else ""}
</div>'''
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)
    
    # We render the figure directly below the header because Streamlit's st.plotly_chart cannot be easily embedded inside pure HTML string containers without complex components.
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
