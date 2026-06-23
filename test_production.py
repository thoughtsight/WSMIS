import os
import sys
import traceback
import pandas as pd
import streamlit as st

st.session_state["parts_cross_month"] = None

print("Loading settings...")
try:
    from utils.constants import CLIENTS
    from app import load_data
except Exception as e:
    print(f"Failed to import app/constants: {e}")
    sys.exit(1)

client_name = list(CLIENTS.keys())[0]
client_config = CLIENTS[client_name]

print(f"Fetching real data for client: {client_name}...")
try:
    df, exp_df = load_data(client_config)
    print(f"Data fetched! DF shape: {df.shape}")
except Exception as e:
    print(f"Failed to load real data: {e}")
    traceback.print_exc()
    sys.exit(1)

def test_view(module_name, render_func_name, *args):
    print(f"\n--- Testing {module_name} ---")
    try:
        module = __import__(module_name, fromlist=[render_func_name])
        render_func = getattr(module, render_func_name)
        render_func(*args)
        print(f"PASS: {module_name}")
    except Exception as e:
        print(f"FAIL: {module_name} - {e}")
        traceback.print_exc()
        sys.exit(1)

from utils.filters import split_cp_pp

try:
    from views.commercial.parts_executive import _compute_metrics, _render_waterfall, _render_category_heatmap
    print("\n--- Testing parts_executive ---")
    months = list(df["Month Name"].unique()[:2])
    cp_months = [months[0]]
    pp_months = [months[1]] if len(months) > 1 else cp_months
    cp, pp = split_cp_pp(df, "Month Name", cp_months, pp_months)
    d = _compute_metrics(cp, pp, df)
    _render_waterfall(d, "YoY")
    _render_category_heatmap(d, "YoY")
    print("PASS: parts_executive components")
except Exception as e:
    print(f"FAIL: parts_executive - {e}")
    traceback.print_exc()
    sys.exit(1)

test_view("views.commercial.parts_detail", "render", df, [], True, None)
test_view("views.commercial.sales_mix", "render", df, [], True, None)

print("\nALL PRODUCTION VALIDATIONS PASSED.")
