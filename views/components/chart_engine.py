import streamlit as st
import plotly.graph_objects as go
from typing import Optional

class ChartEngine:
    """
    Shared View Engine for standardizing Plotly charts across all WSMIS dashboards.
    """
    
    @staticmethod
    def apply_chart(fig: go.Figure, title: str, height: int = 360, text_col=None, bar_text_pos: str = "outside", size: str = "medium", x_title: Optional[str] = None, y_title: Optional[str] = None, barmode: Optional[str] = None):
        """
        Apply Executive Light styling to a Plotly figure.
        """
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
                text=title,
                font=dict(
                    family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                    size=14,
                    color="#1D1D1F"
                ),
                x=0,
                xanchor="left",
                pad=dict(l=4, t=4),
            ),
            margin=s["margin"],
            hoverlabel=dict(
                bgcolor=T.COLOR_SURFACE,
                font_size=13,
                font_family=font_stack,
                bordercolor=T.COLOR_BORDER,
                namelength=-1,
            ),
            xaxis=dict(title=dict(text=x_title, font=dict(size=s["tick"] + 1, family=font_stack)) if x_title else None, 
                tickfont=dict(size=s["tick"], family=font_stack),
                title_font=dict(size=s["tick"] + 1, family=font_stack),
                gridcolor="#E5E5EA",
                gridwidth=1,
                zeroline=False,
                linecolor="#E5E5EA",
            ),
            yaxis=dict(title=dict(text=y_title, font=dict(size=s["tick"] + 1, family=font_stack)) if y_title else None, 
                tickfont=dict(size=s["tick"], family=font_stack),
                title_font=dict(size=s["tick"] + 1, family=font_stack),
                gridcolor="#E5E5EA",
                gridwidth=1,
                zeroline=False,
                linecolor="#E5E5EA",
            ),
            font=dict(
                family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                color="#6E6E73",
                size=11,
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,1)", barmode=barmode,
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
            # Safely apply trace-specific formatting without raising ValueErrors
            for trace in fig.data:
                trace_type = getattr(trace, 'type', None) or 'scatter'
                updates = dict(
                    textfont=dict(size=s["label"], color=T.COLOR_TEXT_PRIMARY, family=font_stack)
                )
                
                if trace_type in ('bar', 'scatter'):
                    updates['cliponaxis'] = False

                if trace_type == 'bar':
                    if not getattr(trace, 'textposition', None):
                        updates['textposition'] = bar_text_pos
                elif trace_type == 'scatter':
                    has_text = getattr(trace, 'text', None) is not None or getattr(trace, 'texttemplate', None) is not None
                    if getattr(trace, 'textposition', None) is None and has_text:
                        updates['textposition'] = "top center"

                trace.update(updates)
        return fig

    @staticmethod
    def render_card(title: str, fig: go.Figure, description: Optional[str] = None, height: int = 400, x_title: Optional[str] = None, y_title: Optional[str] = None, barmode: Optional[str] = None):
        """
        Standardized Chart Card wrapper.
        Ensures charts are displayed in a clean, consistent enterprise card.
        """
        from ui.design_tokens import T
        # Enforce standard responsive layout configurations
        ChartEngine.apply_chart(fig, title="", height=height, x_title=x_title, y_title=y_title, barmode=barmode)
        
        html = f'''<div class="chart-card" style="background:var(--color-surface); border-radius:{T.RADIUS_LG}px; padding:{T.SPACE_4}px; border:1px solid var(--color-border); box-shadow:var(--shadow-sm); margin-bottom:{T.SPACE_4}px;">
        <div style="font-size:{T.TYPE_MD}px; font-weight:600; color:var(--color-text-primary); margin-bottom:{T.SPACE_1}px;">{title}</div>
        {f"<div style='font-size:{T.TYPE_BASE}px; color:var(--color-text-secondary); margin-bottom:{T.SPACE_4}px;'>{description}</div>" if description else ""}
    </div>'''
        st.markdown(html.replace('\n', ''), unsafe_allow_html=True)
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
