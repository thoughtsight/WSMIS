"""
Commercial Dashboard Module
V2 Architecture - Labour, Parts Executive, Parts Detail, Margin, Sales Mix, Discounts dashboards
Version: 1.0.0
"""

from .labour import render as render_labour
from .parts_executive import render as render_parts_executive
from .parts_detail import render as render_parts_detail
from .margin import render as render_margin
from .sales_mix import render as render_sales_mix
from .discount import render as render_discount

__all__ = ['render_labour', 'render_parts_executive', 'render_parts_detail', 'render_margin', 'render_sales_mix', 'render_discount']
