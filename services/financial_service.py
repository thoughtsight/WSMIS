"""
Financial Service Layer
Orchestrates business engines (Revenue, Margin, Discount, Leakage, Fact Metrics) 
for consumption by dashboards.
"""

import pandas as pd
from typing import Dict, Union, Tuple, Optional, Any

from utils.calculations import fact_metrics, revenue, margin, discount, leakage, common
from utils import aggregations

class FinancialService:
    
    @staticmethod
    def get_revenue_metrics(df: pd.DataFrame) -> Dict[str, Any]:
        """Unified revenue metrics."""
        return {
            "Total Revenue": revenue.calculate_total_revenue(df),
            "Labour Revenue": fact_metrics.get_labour_sales(df),
            "Parts Revenue": fact_metrics.get_parts_sales(df),
            "Net Labour": fact_metrics.get_net_labour(df),
            "Net Parts": fact_metrics.get_net_parts(df),
            "Revenue Per JC": revenue.calculate_revenue_per_jobcard(df)
        }
        
    @staticmethod
    def get_margin_metrics(df: pd.DataFrame) -> Dict[str, Any]:
        """Unified margin metrics."""
        return {
            "Total Margin": margin.calculate_total_margin(df),
            "Parts Margin": margin.calculate_parts_margin(df),
            "Margin Per JC": margin.calculate_margin_per_jobcard(df)
        }
        
    @staticmethod
    def get_discount_metrics(df: pd.DataFrame) -> Dict[str, Any]:
        """Unified discount metrics."""
        return {
            "Total Discount": discount.calculate_total_discount(df),
            "Labour Discount": discount.calculate_labour_discount(df),
            "Parts Discount": discount.calculate_parts_discount(df),
            "Labour Discount %": discount.calculate_labour_discount_pct(df),
            "Parts Discount %": discount.calculate_parts_discount_pct(df),
            "Overall Discount %": discount.calculate_overall_discount_pct(df),
            "Discount Per JC": discount.calculate_discount_per_jobcard(df)
        }
        
    @staticmethod
    def get_leakage_metrics(df: pd.DataFrame, group_col: str, benchmark: float = 15.0) -> pd.DataFrame:
        """Unified leakage aggregates."""
        return leakage.compute_discount_aggregates(df, group_col, benchmark)
        
    @staticmethod
    def get_dashboard_kpis(cp: pd.DataFrame, pp: pd.DataFrame) -> Dict[str, Any]:
        """Consolidates KPIs for CP/PP comparison."""
        rev_kpis = revenue.calculate_revenue_growth(cp, pp)
        mar_kpis = margin.calculate_margin_kpis(cp, pp)
        disc_kpis = discount.calculate_discount_kpis(cp, pp)
        return {
            "Revenue Growth %": rev_kpis,
            "Margin KPIs": mar_kpis,
            "Discount KPIs": disc_kpis
        }

# ==========================================
# No longer exporting raw calculations or aggregations.
# Pages must import directly from utils.calculations and utils.aggregations
# or use the FinancialService API.
# ==========================================
