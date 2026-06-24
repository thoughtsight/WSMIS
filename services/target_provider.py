import pandas as pd
import streamlit as st

class TargetProvider:
    """
    Encapsulates all logic related to fetching, formatting, and aggregating target 
    and benchmark thresholds. 
    Provides a canonical single source of truth across all modules.
    """
    
    def __init__(self, targets_df: pd.DataFrame):
        self._raw_df = targets_df.copy()
        
        # 1. Normalize the month format to ensure matching
        if not self._raw_df.empty and "Month Name" in self._raw_df.columns:
            # Map Apr-26 -> Apr-2026 safely
            normalized = pd.to_datetime(
                self._raw_df["Month Name"], format="%b-%y", errors="coerce"
            ).dt.strftime("%b-%Y")
            
            # Fill any NaN resulting from parsing errors with the original string
            self._raw_df["Month Name"] = normalized.fillna(self._raw_df["Month Name"])
        
        # 2. Trim whitespace from Location Name for robust matching
        if not self._raw_df.empty and "Location Name" in self._raw_df.columns:
            self._raw_df["Location Name"] = self._raw_df["Location Name"].str.strip()
            
    def get_location_targets(self, locations: list, months: list, debug: bool = False) -> pd.DataFrame:
        """
        Returns the raw target dataframe filtered for the requested locations and months.
        Useful for detailed breakdown pages like Targets or Discounts that merge row-by-row.
        """
        if self._raw_df.empty:
            if debug:
                st.warning(f"TargetProvider: Empty targets DataFrame")
            return pd.DataFrame()
        
        # Normalize inputs for matching
        locations_normalized = [str(loc).strip() for loc in locations]
        months_normalized = [str(m).strip() for m in months]
        
        if debug:
            st.write(f"**TargetProvider Lookup Diagnostics**")
            st.write(f"- Requested Locations: {locations_normalized}")
            st.write(f"- Requested Months: {months_normalized}")
            st.write(f"- Available Locations in targets: {self._raw_df['Location Name'].unique().tolist()}")
            st.write(f"- Available Months in targets: {self._raw_df['Month Name'].unique().tolist()}")
            
        mask = (self._raw_df["Month Name"].isin(months_normalized)) & (self._raw_df["Location Name"].isin(locations_normalized))
        result = self._raw_df[mask]
        
        if debug:
            st.write(f"- Matching rows: {len(result)}")
            if not result.empty:
                st.dataframe(result, use_container_width=True)
            else:
                st.warning(f"No matching rows found for the requested scope")
        
        return result

    def get_revenue_target(self, locations: list, months: list, debug: bool = False) -> float:
        """
        Returns the scalar sum of all WS/BS Labour and Parts targets for the specified scope.
        Used by Executive Command Center and summary KPIs.
        Returns 0.0 if no target configured (graceful fallback).
        """
        tgt = self.get_location_targets(locations, months, debug=debug)
        if tgt.empty:
            if debug:
                st.warning("Revenue Target: No matching rows - returning 0.0")
            return 0.0
            
        cols = ["WS_Labour_Target", "BS_Labour_Target", "WS_Parts_Target", "BS_Parts_Target"]
        # Ensure columns exist before summing
        valid_cols = [c for c in cols if c in tgt.columns]
        if not valid_cols:
            if debug:
                st.warning("Revenue Target: No target columns found - returning 0.0")
            return 0.0
            
        result = float(tgt[valid_cols].apply(pd.to_numeric, errors='coerce').sum().sum())
        if debug:
            st.write(f"Revenue Target: {result:,.2f}")
        return result

    def get_parts_target(self, locations: list, months: list, debug: bool = False) -> float:
        """
        Returns the scalar sum of all WS/BS Parts targets for the specified scope.
        Used by Parts Executive.
        Returns 0.0 if no target configured (graceful fallback).
        """
        tgt = self.get_location_targets(locations, months, debug=debug)
        if tgt.empty:
            if debug:
                st.warning("Parts Target: No matching rows - returning 0.0")
            return 0.0
            
        cols = ["WS_Parts_Target", "BS_Parts_Target"]
        valid_cols = [c for c in cols if c in tgt.columns]
        if not valid_cols:
            if debug:
                st.warning("Parts Target: No target columns found - returning 0.0")
            return 0.0
            
        result = float(tgt[valid_cols].apply(pd.to_numeric, errors='coerce').sum().sum())
        if debug:
            st.write(f"Parts Target: {result:,.2f}")
        return result
        
    def get_discount_target(self, locations: list, months: list, revenue_df: pd.DataFrame = None, debug: bool = False) -> float:
        """
        Calculates the average approved discount for the specified scope.
        If revenue_df is provided (DataFrame with Location Name and Net_Labour columns),
        computes a revenue-weighted average using Net_Labour as the canonical weighting metric.
        Otherwise, a simple average.
        Returns default 15.0% if no target configured (graceful fallback).
        """
        DEFAULT_DISC = 15.0
        tgt = self.get_location_targets(locations, months, debug=debug)
        
        if tgt.empty or "Appr_Lab_Disc" not in tgt.columns:
            if debug:
                st.warning(f"Discount Target: No matching rows or column missing - using default {DEFAULT_DISC}%")
            return DEFAULT_DISC
            
        if revenue_df is not None and not revenue_df.empty:
            # Compute revenue weights using canonical Net_Labour metric
            revenue_weights = revenue_df.groupby("Location Name")["Net_Labour"].sum().to_dict()
            
            total_weight = 0.0
            weighted_sum = 0.0
            
            # Since multiple months could be passed, group by location and average the target
            loc_tgt = tgt.groupby("Location Name")["Appr_Lab_Disc"].apply(
                lambda x: pd.to_numeric(x, errors="coerce").mean()
            ).reset_index()
            
            for _, row in loc_tgt.iterrows():
                loc = row["Location Name"]
                val = row["Appr_Lab_Disc"]
                if pd.isna(val): continue
                
                weight = revenue_weights.get(loc, 0.0)
                weighted_sum += val * weight
                total_weight += weight
                
            if total_weight > 0:
                result = float(weighted_sum / total_weight)
                if debug:
                    st.write(f"Discount Target (Weighted): {result:.2f}%")
                return result
                
        # Simple average fallback if no revenue_df provided or total weight is zero
        result = float(pd.to_numeric(tgt["Appr_Lab_Disc"], errors="coerce").mean())
        if debug:
            st.write(f"Discount Target (Simple Average): {result:.2f}%")
        return result
