import pandas as pd
import streamlit as st

data = {
    "Month Name": ["Jan-24", "Feb-24", "Jan-24"],
    "Month_Sort": [1, 2, 1],
    "Location Name": ["Loc1", "Loc2", "Loc1"],
    "Service Type": ["Svc1", "Svc2", "Svc1"],
    "Pre-GST Parts": [1000, 2000, 1500],
    "Parts Profit": [100, 200, 150],
    "Parts Discount": [10, 20, 15],
    "JC_Nos.": [10, 20, 15],
    "Oil_Sale": [50, 100, 75],
    "year": ["This FY", "Last FY", "This FY"],
    "Parts_Sale": [500, 1000, 700],
    "Accessory_Sale": [100, 200, 150],
    "Tyre_Sale": [50, 100, 75],
    "Battery_Sale": [50, 100, 75],
    "Other_Sale": [250, 500, 350]
}
df = pd.DataFrame(data)

st.session_state = {"parts_cross_month": None}

import sys
import traceback

try:
    from views.commercial.parts_executive import _compute_metrics, _render_waterfall, _render_category_heatmap
    print("Running _compute_metrics for Parts Executive...")
    d = _compute_metrics(df, df, df)
    print("Parts Executive metrics computed successfully.")
except Exception as e:
    print("Error in Parts Executive compute metrics:")
    traceback.print_exc()

try:
    print("Testing waterfall chart...")
    _render_waterfall(d, "YoY")
    print("Waterfall tested.")
except Exception as e:
    print("Error in waterfall:")
    traceback.print_exc()

try:
    print("Testing heatmap chart...")
    _render_category_heatmap(d, "YoY")
    print("Heatmap tested.")
except Exception as e:
    print("Error in heatmap:")
    traceback.print_exc()

try:
    from views.commercial.parts_detail import render as render_parts_detail
    print("Testing Parts Detail render...")
    render_parts_detail(df, [], True, None)
    print("Parts Detail rendered.")
except Exception as e:
    print("Error in Parts Detail:")
    traceback.print_exc()

try:
    from views.commercial.sales_mix import render as render_sales_mix
    print("Testing Sales Mix render...")
    render_sales_mix(df, [], True, None)
    print("Sales Mix rendered.")
except Exception as e:
    print("Error in Sales Mix:")
    traceback.print_exc()
