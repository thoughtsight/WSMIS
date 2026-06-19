"""
Forensic Audit Script V2 - Check raw Month Name values before transformation
"""
import pandas as pd
import numpy as np
from utils.loaders import load_raw_worksheet
from utils.cleaning import clean_dataframe
from utils.constants import ADV_COL, MONTH_SORT_ORDER, PB_SERVICE_TYPES, CLIENTS

def main():
    print("FORENSIC AUDIT V2: Check raw Month Name values")
    print("="*80)
    
    # Get client config
    client_config = list(CLIENTS.values())[0]
    sheet_id = client_config["sheet_id"]
    sheet_tab = client_config["sheet_tab"]
    
    print(f"\nSheet ID: {sheet_id}")
    print(f"Sheet Tab: {sheet_tab}")
    
    # Load raw data
    df_raw = load_raw_worksheet(sheet_id, sheet_tab)
    
    print(f"\nTotal rows in raw worksheet: {len(df_raw)}")
    
    # Check raw Month Name values
    if 'Month Name' in df_raw.columns:
        print(f"\nRaw Month Name unique values:")
        raw_month_values = df_raw['Month Name'].dropna().unique()
        print(f"  Count: {len(raw_month_values)}")
        print(f"  Values: {sorted(raw_month_values, key=str)}")
        
        # Check for Feb/Mar 2025 in various formats
        target_patterns = ['Feb-25', 'Mar-25', 'Feb-2025', 'Mar-2025', 'Feb-25', 'Mar-25']
        print(f"\nSearching for target patterns in raw Month Name:")
        for pattern in target_patterns:
            count = len(df_raw[df_raw['Month Name'].astype(str).str.contains(pattern, case=False, na=False)])
            print(f"  Pattern '{pattern}': {count} rows")
        
        # Show sample rows with Month Name containing 'Feb' or 'Mar'
        feb_mar_rows = df_raw[df_raw['Month Name'].astype(str).str.contains('Feb|Mar', case=False, na=False)]
        print(f"\nRows with Feb/Mar in Month Name: {len(feb_mar_rows)}")
        if not feb_mar_rows.empty:
            print(f"Sample rows:")
            print(feb_mar_rows[['Month Name', 'Location Name', 'Service Type']].head(10).to_string())
        
        # Check all unique Month Name values
        print(f"\nAll unique Month Name values with row counts:")
        month_counts = df_raw['Month Name'].value_counts().sort_index()
        for month, count in month_counts.items():
            print(f"  {month}: {count} rows")
    
    # Check if there's a different column name for month
    print(f"\nAll columns in raw data:")
    print(df_raw.columns.tolist())

if __name__ == "__main__":
    main()
