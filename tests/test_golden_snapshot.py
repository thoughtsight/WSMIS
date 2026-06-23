import os
import json
import pytest
import pandas as pd
import pandas as pd
from utils.constants import CLIENTS
from utils.loaders import load_raw_worksheet
from services.financial_service import FinancialService
from utils.calculations import fact_metrics

def get_snapshot_data():
    client_config = list(CLIENTS.values())[0]
    sheet_id = client_config["sheet_id"]
    sheet_tab = client_config["sheet_tab"]
    df = load_raw_worksheet(sheet_id, sheet_tab)
    
    # Coerce to numeric to avoid sum() errors on strings
    for col in df.columns:
        if col not in ["Location", "Service Type", "Bill Date", "Job Card No", "Advisor Name", "Model"]:
            try:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            except Exception:
                pass
    return df


SNAPSHOT_FILE = os.path.join(os.path.dirname(__file__), "golden_snapshots.json")

def compute_all_kpis(df: pd.DataFrame) -> dict:
    """Extracts all KPIs from the frozen calculation layer."""
    if df.empty:
        return {}
        
    kpis = {}
    
    # Extract from FinancialService
    rev_metrics = FinancialService.get_revenue_metrics(df)
    mar_metrics = FinancialService.get_margin_metrics(df)
    disc_metrics = FinancialService.get_discount_metrics(df)
    
    kpis.update(rev_metrics)
    kpis.update(mar_metrics)
    kpis.update(disc_metrics)
    
    # Extract Fact Metrics
    rev_comps = fact_metrics.get_revenue_components(df)
    mar_comps = fact_metrics.get_margin_components(df)
    
    kpis.update(rev_comps)
    kpis.update(mar_comps)
    
    # Additional static KPIs or fallback for missing ones (to ensure we capture what's available)
    # We round everything to 2 decimal places as requested
    
    rounded_kpis = {}
    for key, value in kpis.items():
        if isinstance(value, (int, float)):
            rounded_kpis[key] = round(float(value), 2)
        elif pd.isna(value):
            rounded_kpis[key] = 0.0
            
    return rounded_kpis

def generate_snapshot():
    """Generates the golden snapshot file."""
    print("Loading data for golden snapshot...")
    df = get_snapshot_data()
    print(f"Data loaded. Shape: {df.shape}")
    
    kpis = compute_all_kpis(df)
    
    # Also compute by location to ensure branch-level granularity
    if "Location" in df.columns:
        locations = df["Location"].dropna().unique()
        for loc in locations:
            loc_df = df[df["Location"] == loc]
            loc_kpis = compute_all_kpis(loc_df)
            kpis[f"Location_{loc}"] = loc_kpis
            
    # Also compute by Service Type if available
    if "Service Type" in df.columns:
        svc_types = df["Service Type"].dropna().unique()
        for svc in svc_types:
            svc_df = df[df["Service Type"] == svc]
            svc_kpis = compute_all_kpis(svc_df)
            kpis[f"Service_{svc}"] = svc_kpis
            
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(kpis, f, indent=4)
        
    print(f"Golden snapshot saved to {SNAPSHOT_FILE}")
    print(f"Captured {len(kpis.keys())} root-level KPI categories/locations.")

@pytest.fixture(scope="session")
def snapshot_data():
    if not os.path.exists(SNAPSHOT_FILE):
        pytest.skip(f"Snapshot file {SNAPSHOT_FILE} not found. Run 'python test_golden_snapshot.py' to generate it.")
    with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="session")
def current_data():
    return get_snapshot_data()

def test_golden_regression_overall(snapshot_data, current_data):
    """Verifies overall KPIs against the golden snapshot."""
    current_kpis = compute_all_kpis(current_data)
    
    missing_kpis = []
    failed_kpis = []
    
    # Only compare top-level keys that are floats (overall KPIs)
    for key, expected_val in snapshot_data.items():
        if isinstance(expected_val, (int, float)):
            if key not in current_kpis:
                missing_kpis.append(key)
                continue
                
            actual_val = current_kpis[key]
            delta = abs(expected_val - actual_val)
            
            if delta > 0.01:
                failed_kpis.append(f"{key}: Expected {expected_val}, got {actual_val} (Delta: {delta:.4f})")
                
    assert not missing_kpis, f"Missing KPIs in current calculation: {missing_kpis}"
    assert not failed_kpis, f"Regression detected in KPIs:\n" + "\n".join(failed_kpis)

if __name__ == "__main__":
    generate_snapshot()
