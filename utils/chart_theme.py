import plotly.graph_objects as go
import plotly.io as pio

def apply_wsmis_theme():
    """
    Registers and applies the standard WSMIS Enterprise Plotly theme.
    """
    wsmis_template = go.layout.Template()
    
    # Base layout
    wsmis_template.layout = go.Layout(
        font=dict(family="Inter, Roboto, sans-serif", color="#1d1d1f"),
        title=dict(font=dict(size=16, color="#1d1d1f", weight="bold")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=40, b=20),
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Inter, Roboto, sans-serif",
            bordercolor="#e5e5ea"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=12, color="#6E6E73")
        ),
        colorway=[
            "#007AFF", # Blue
            "#34C759", # Green
            "#FF9F0A", # Orange
            "#FF3B30", # Red
            "#5856D6", # Purple
            "#30B0C7"  # Cyan
        ]
    )
    
    # Axes
    wsmis_template.layout.xaxis = dict(
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor="#e5e5ea",
        tickfont=dict(color="#6E6E73", size=11)
    )
    
    wsmis_template.layout.yaxis = dict(
        showgrid=True,
        gridcolor="#f5f5f7",
        zeroline=True,
        zerolinecolor="#e5e5ea",
        showline=False,
        tickfont=dict(color="#6E6E73", size=11)
    )
    
    pio.templates["wsmis"] = wsmis_template
    pio.templates.default = "wsmis"
