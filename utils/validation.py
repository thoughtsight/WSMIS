import pandas as pd

def is_valid_df(df, required_columns=None):
    """
    Checks if a DataFrame is valid (not None and not empty).
    Optionally checks for required columns.
    """
    if df is None or df.empty:
        return False
    if required_columns:
        for col in required_columns:
            if col not in df.columns:
                return False
    return True

def validate_schema(df, schema=None):
    """
    Validates a DataFrame against a given schema (dictionary of column: dtype).
    """
    if not is_valid_df(df, required_columns=schema.keys() if schema else None):
        return False
    # Additional schema logic can be added here
    return True
