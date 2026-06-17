# User Acceptance Testing (UAT) Guide

Welcome to the WSMIS v1.0.0-rc1 UAT phase. This guide provides detailed instructions on how to access, navigate, and validate the application functionality before production rollout.

## 1. Initial Access & Login
- Open your supported web browser (Chrome or Edge recommended).
- Navigate to the designated Streamlit Community Cloud URL or local network IP (e.g., `http://localhost:8501`).
- *(Note: User authentication is handled via the Google Service Account for data access. Direct login is not currently required unless specified by your IT admin).*

## 2. Workspace Setup
- **Selecting Client:** Use the **Client** dropdown in the left sidebar to select your target dealership group (e.g., "Rukmani Motors").
- **Selecting FY/Period:** Use the top header bar to select "Preset" periods (e.g., 3M, 6M) or use the "Custom" Month Picker to select specific combinations of months.

## 3. Global Filters
Use the **Global Filters** in the sidebar to slice the dashboard data:
- **Location Group:** Filter by Arena, Nexa, or Other.
- **Location:** Filter down to specific dealer locations (e.g., Palda, Dhar).
- **Service Type:** Select specific service types (e.g., Free, Paid, Running Repair).
- **Advisor:** Focus on one or multiple Service Advisors.
- **WS/BS:** Toggle between Workshop (WS) and Bodyshop (BS) revenue streams.

## 4. Dashboard Navigation
The application features 18 distinct dashboards categorized in the sidebar:
- **Overview:** Cockpit, Overview, Executive
- **Revenue:** Labour, Parts, Margin, Sales Mix, Discounts, Leakage Center
- **People:** Advisors, Advisor MoM
- **Performance:** Locations, Trends, Targets
- **Finance:** Expense Analysis, Profit & Loss
- **Admin:** Reports, Internal Audit

Clicking any button under these categories will immediately switch the main view. Allow the "Crunching numbers..." spinner to finish loading before scrolling.

## 5. Exporting Data
- Every data table in the dashboards features a download icon (usually at the top right of the table or via a dedicated "📥 Download Excel" button).
- Ensure that the exported Excel/CSV matches the data shown on the screen and correctly reflects any active global filters.

## 6. Reports Generation
- Navigate to the **Reports** tab under the Admin section.
- Select your desired report (MIS Summary, Advisor Performance, Discount Leakage).
- Click the download button to generate a formatted Excel spreadsheet.

## 7. Performance Expectations
- **Initial Load:** Data fetching from Google Sheets may take 3-6 seconds.
- **Cache Hits:** Once loaded, switching tabs should be near-instantaneous (< 1 second) as aggregations are heavily cached in-memory.
- **Filtering:** Applying a new global filter or month selection should take ~1-2 seconds to recompute.
