# Dashboard Framework Migration Guide (Final)

## Prerequisites
Ensure core.framework and core.registry are accessible.

## Step 1: Define Strong Types
Create your dashboard-specific Models inheriting from the Framework:
`python
from dataclasses import dataclass
from core.framework import DashboardMetrics, DashboardFilters

@dataclass
class LabourMetrics(DashboardMetrics):
    total_sales: float
    loc_breakdown: pd.DataFrame
`

## Step 2: Subclass DashboardController
Create your Controller and implement _apply_filters and _build_context.
`python
class LabourController(DashboardController):
    def _apply_filters(self, df, **kwargs):
        # Subset cp and pp
        return cp, pp
        
    def _build_context(self, cp, pp, **kwargs) -> DashboardContext:
        metrics = LabourMetrics(total_sales=100)
        return DashboardContext(cp=cp, pp=pp, metrics=metrics, ...)
`

## Step 3: Implement Render Hooks
Implement the _render_* hooks you need. You are NOT required to implement hooks you don't use (e.g., if you have no charts, do not override _render_charts).

## Step 4: Register Capabilities
Add your route to DashboardRegistry.ROUTES using DashboardMeta.
