import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from io import BytesIO
from datetime import datetime
import time

# Services
from services.financial_service import FinancialService
from services.audit_service import calc_penetration, get_month

# Calculations
from utils.calculations.fact_metrics import *
from utils.calculations.revenue import *
from utils.calculations.margin import *
from utils.calculations.discount import *
from utils.calculations.leakage import *
from utils.calculations.common import *

# Utils & Aggregations
from utils.aggregations import *
from utils.filters import *
from utils.constants import *

# UI & Formats
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num
from ui.design_tokens import T

# UI Components
from ui.components import KPIGrid, MetricCard, TableCard
from ui.components.core import UniversalHeader, UniversalFooter, EmptyState, AlertBanner, spacer, section_card, section_title, badge, divider, PageBreadcrumb
from ui.tables import html_table, searchable_table
# Helpers
from views.components.chart_engine import ChartEngine
from views.components.kpi_engine import KPIEngine
from ui.helpers import *

from ui.export_buttons import render_export_buttons
