from typing import List, Dict, Any, Optional
from ui.components.metrics import KPIGrid

class KPIEngine:
    """
    Shared View Engine for standardizing KPI rendering across all WSMIS dashboards.
    """
    
    @staticmethod
    def render_grid(metrics: List[Dict[str, Any]], cols: Optional[int] = None):
        """
        Renders a responsive grid of MetricCards.
        
        Args:
            metrics: List of dicts where each dict contains kwargs for MetricCard:
                     (label, value, sub, cp, pp, pp_label, benchmark, target, invert_trend)
            cols:    Column count override. Defaults to len(metrics).
        """
        KPIGrid(metrics, cols)
