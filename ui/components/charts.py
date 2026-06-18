import streamlit as st
import plotly.graph_objects as go
from typing import Optional

def ChartCard(title: str, fig: go.Figure, description: Optional[str] = None, height: int = 400):
    """
    Standardized Chart Card wrapper.
    Ensures charts are displayed in a clean, consistent enterprise card.
    """
    # Enforce standard responsive layout configurations without overwriting the chart's core data
    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        height=height,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, Roboto, sans-serif", color="#1d1d1f"),
        hoverlabel=dict(bgcolor="white", font_size=13, font_family="Inter, Roboto, sans-serif")
    )
    
    html = f'''<div class="chart-card" style="background:#fff; border-radius:12px; padding:16px; border:1px solid #e5e5ea; box-shadow:0 1px 2px rgba(0,0,0,0.02); margin-bottom:16px;">
    <div style="font-size:16px; font-weight:600; color:#1d1d1f; margin-bottom:4px;">{title}</div>
    {"<div style='font-size:13px; color:#6E6E73; margin-bottom:16px;'>" + description + "</div>" if description else ""}
</div>'''
    st.markdown(html, unsafe_allow_html=True)
    
    # We render the figure directly below the header because Streamlit's st.plotly_chart cannot be easily embedded inside pure HTML string containers without complex components.
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
