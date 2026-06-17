import pandas as pd
import numpy as np
from services.aggregation_cache import _get_df_hash

def test_cache_hashing():
    print("Testing deterministic DataFrame hashing...")
    
    # 1. Create identical dataframes
    df1 = pd.DataFrame({
        "A": [1, 2, 3],
        "B": ["X", "Y", "Z"]
    })
    
    df2 = pd.DataFrame({
        "A": [1, 2, 3],
        "B": ["X", "Y", "Z"]
    })
    
    hash1 = _get_df_hash(df1)
    hash2 = _get_df_hash(df2)
    
    assert hash1 == hash2, "Identical DataFrames should have identical hashes"
    print("SUCCESS: Identical DataFrames produce identical hashes.")
    assert id(df1) != id(df2), "Addresses must be different"
    print("SUCCESS: Different object addresses successfully bypassed.")
    
    # 2. Mutate dataframe
    df3 = df1.copy()
    df3.loc[0, "A"] = 999
    hash3 = _get_df_hash(df3)
    assert hash1 != hash3, "Mutated DataFrame must have a different hash"
    print("SUCCESS: Mutated DataFrame produces a different hash.")
    
    print("All hash tests passed!")

if __name__ == "__main__":
    test_cache_hashing()
