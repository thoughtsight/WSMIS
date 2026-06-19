"""
Forensic Audit Script V3 - Trace the transformation step by step
"""
import pandas as pd
import numpy as np
from utils.loaders import load_raw_worksheet
from utils.constants import ADV_COL, MONTH_SORT_ORDER, PB_SERVICE_TYPES, CLIENTS

def main():
    print("FORENSIC AUDIT V3: Trace transformation step by step")
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
        
        # Check Feb-25 and Mar-25 specifically
        feb_25_count = len(df_raw[df_raw['Month Name'] == 'Feb-25'])
        mar_25_count = len(df_raw[df_raw['Month Name'] == 'Mar-25'])
        print(f"\nRaw counts: Feb-25={feb_25_count}, Mar-25={mar_25_count}")
        
        # Sample rows for Feb-25 and Mar-25
        print(f"\nSample Feb-25 rows:")
        print(df_raw[df_raw['Month Name'] == 'Feb-25'][['Month Name', 'Location Name']].head(3).to_string())
        
        print(f"\nSample Mar-25 rows:")
        print(df_raw[df_raw['Month Name'] == 'Mar-25'][['Month Name', 'Location Name']].head(3).to_string())
    
    # Now apply the transformation manually to see what happens
    print(f"\n{'='*80}")
    print("APPLYING TRANSFORMATION FROM clean_dataframe() LINE 58")
    print(f"{'='*80}")
    
    df_transform = df_raw.copy()
    
    # This is the exact transformation from clean_dataframe line 58
    def transform_month(x):
        if isinstance(x, str) and '-' in x:
            try:
                return __import__('datetime').datetime.strptime(x, "%b-%y").strftime("%b-%Y")
            except Exception as e:
                print(f"  Failed to transform '{x}': {e}")
                return x
        return x
    
    print(f"\nTransforming Month Name column...")
    df_transform['Month Name'] = df_transform['Month Name'].apply(transform_month)
    
    print(f"\nAfter transformation - unique Month Name values:")
    transformed_values = df_transform['Month Name'].dropna().unique()
    print(f"  Count: {len(transformed_values)}")
    print(f"  Values: {sorted(transformed_values, key=str)}")
    
    # Check Feb-2025 and Mar-2025 after transformation
    feb_2025_count = len(df_transform[df_transform['Month Name'] == 'Feb-2025'])
    mar_2025_count = len(df_transform[df_transform['Month Name'] == 'Mar-2025'])
    print(f"\nAfter transformation counts: Feb-2025={feb_2025_count}, Mar-2025={mar_2025_count}")
    
    # Now apply the categorical creation
    print(f"\n{'='*80}")
    print("APPLYING CATEGORICAL CREATION FROM clean_dataframe() LINES 60-61")
    print(f"{'='*80}")
    
    sorted_months = sorted(MONTH_SORT_ORDER.keys(), key=lambda k: MONTH_SORT_ORDER[k])
    print(f"\nSorted months from MONTH_SORT_ORDER (first 20):")
    print(f"  {sorted_months[:20]}")
    print(f"Total categories: {len(sorted_months)}")
    
    # Check if Feb-2025 and Mar-2025 are in the categories
    print(f"\nChecking if target months are in categories:")
    print(f"  'Feb-2025' in categories: {'Feb-2025' in sorted_months}")
    print(f"  'Mar-2025' in categories: {'Mar-2025' in sorted_months}")
    
    # Apply categorical
    df_transform['Month Name'] = pd.Categorical(df_transform['Month Name'], categories=sorted_months, ordered=True)
    
    # Check for NaN values after categorical
    nan_count = df_transform['Month Name'].isna().sum()
    print(f"\nNaN values in Month Name after categorical: {nan_count}")
    
    # Check Feb-2025 and Mar-2025 after categorical
    feb_2025_count_after = len(df_transform[df_transform['Month Name'] == 'Feb-2025'])
    mar_2025_count_after = len(df_transform[df_transform['Month Name'] == 'Mar-2025'])
    print(f"\nAfter categorical counts: Feb-2025={feb_2025_count_after}, Mar-2025={mar_2025_count_after}")
    
    # Check which values became NaN
    if nan_count > 0:
        print(f"\nRows with NaN Month Name after categorical:")
        nan_rows = df_transform[df_transform['Month Name'].isna()]
        print(f"  Count: {len(nan_rows)}")
        if not nan_rows.empty:
            # Get the original Month Name values that became NaN
            # We need to check what they were before categorical
            print(f"  Sample of rows that became NaN:")
            # Since we overwrote, let's check the original
            original_nan = df_raw.loc[nan_rows.index]
            if 'Month Name' in original_nan.columns:
                print(original_nan['Month Name'].value_counts().head(10).to_string())

if __name__ == "__main__":
    main()
