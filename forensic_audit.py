"""
Forensic Audit Script - Trace Feb-2025 and Mar-2025 through data pipeline
"""
import pandas as pd
import numpy as np
from utils.loaders import load_raw_worksheet
from utils.cleaning import clean_dataframe
from utils.constants import ADV_COL, MONTH_SORT_ORDER, PB_SERVICE_TYPES, CLIENTS

def audit_month_columns(df, stage_name):
    """Audit month-related columns at each stage"""
    print(f"\n{'='*80}")
    print(f"STAGE: {stage_name}")
    print(f"{'='*80}")
    print(f"Total rows: {len(df)}")
    
    if df.empty:
        print("DataFrame is empty")
        return
    
    # Identify all month-related columns
    month_cols = [col for col in df.columns if 'month' in col.lower() or 'date' in col.lower() or col == 'Bill Date']
    print(f"\nMonth-related columns: {month_cols}")
    
    # For each month column, show unique values
    for col in month_cols:
        if col in df.columns:
            print(f"\n{col}:")
            unique_vals = df[col].dropna().unique()
            print(f"  Unique values: {sorted(unique_vals, key=str)}")
            print(f"  Count: {len(unique_vals)}")
    
    # Check Month Name specifically
    if 'Month Name' in df.columns:
        print(f"\nMonth Name distribution:")
        month_counts = df['Month Name'].value_counts().sort_index()
        for month, count in month_counts.items():
            print(f"  {month}: {count} rows")
        
        # Check specific months
        target_months = ['Feb-2025', 'Mar-2025', 'Apr-2025']
        print(f"\nTarget months row counts:")
        for month in target_months:
            count = len(df[df['Month Name'] == month])
            print(f"  {month}: {count} rows")
    
    # Show sample rows for target months
    if 'Month Name' in df.columns:
        target_months = ['Feb-2025', 'Mar-2025', 'Apr-2025']
        for month in target_months:
            month_df = df[df['Month Name'] == month]
            if not month_df.empty:
                print(f"\nSample rows for {month}:")
                print(month_df.head(3).to_string())
            else:
                print(f"\nNo rows found for {month}")

def main():
    print("FORENSIC AUDIT: Tracing Feb-2025 and Mar-2025 through data pipeline")
    print("="*80)
    
    # Get client config
    client_config = list(CLIENTS.values())[0]
    sheet_id = client_config["sheet_id"]
    sheet_tab = client_config["sheet_tab"]
    
    print(f"\nSheet ID: {sheet_id}")
    print(f"Sheet Tab: {sheet_tab}")
    
    # Stage 1: Raw worksheet load
    print("\n" + "="*80)
    print("STAGE 1: load_raw_worksheet()")
    print("="*80)
    df_raw = load_raw_worksheet(sheet_id, sheet_tab)
    audit_month_columns(df_raw, "After load_raw_worksheet()")
    
    # Stage 2: After clean_dataframe
    print("\n" + "="*80)
    print("STAGE 2: clean_dataframe()")
    print("="*80)
    df_clean = clean_dataframe(df_raw.copy(), ADV_COL, MONTH_SORT_ORDER, PB_SERVICE_TYPES)
    audit_month_columns(df_clean, "After clean_dataframe()")
    
    # Stage 3: After load_data (exclusions)
    print("\n" + "="*80)
    print("STAGE 3: load_data() - Exclusions")
    print("="*80)
    from utils.constants import EXCLUDE_SERVICE_TYPES
    df_exclusions = df_clean.copy()
    df_exclusions = df_exclusions[~df_exclusions['Service Type'].isin(EXCLUDE_SERVICE_TYPES)]
    audit_month_columns(df_exclusions, "After Service Type exclusions")
    
    # Stage 4: After location classification
    print("\n" + "="*80)
    print("STAGE 4: Location Classification")
    print("="*80)
    df_final = df_exclusions.copy()
    df_final['Location Group'] = df_final['Location Name'].apply(lambda x: classify_location(x, client_config))
    audit_month_columns(df_final, "After location classification")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Raw worksheet rows: {len(df_raw)}")
    print(f"After clean_dataframe: {len(df_clean)}")
    print(f"After exclusions: {len(df_exclusions)}")
    print(f"Final: {len(df_final)}")
    
    for stage_name, df in [
        ("Raw", df_raw),
        ("Cleaned", df_clean),
        ("Exclusions", df_exclusions),
        ("Final", df_final)
    ]:
        if 'Month Name' in df.columns:
            feb_count = len(df[df['Month Name'] == 'Feb-2025'])
            mar_count = len(df[df['Month Name'] == 'Mar-2025'])
            apr_count = len(df[df['Month Name'] == 'Apr-2025'])
            print(f"\n{stage_name}: Feb-2025={feb_count}, Mar-2025={mar_count}, Apr-2025={apr_count}")

def classify_location(name, client_config):
    if name in client_config["arena_locations"]: return "Arena"
    if name in client_config["nexa_locations"]: return "Nexa"
    return "Other"

if __name__ == "__main__":
    main()
