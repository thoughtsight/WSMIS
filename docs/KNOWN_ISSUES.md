# Known Issues & Limitations
*Version: v1.0.0-RC1*

This document tracks known issues, technical limitations, and deferred improvements in the current release candidate of WSMIS. These are documented to prevent redundant bug reporting during the pilot phase.

## Technical Limitations
1. **Initial Cache Warm-up Delays**: 
   - **Impact**: The very first user to access the application after a server reboot or deployment may experience a ~5-8 second delay as data is fetched from Google Sheets and the DataFrame cache is built. Subsequent loads are near-instantaneous.
2. **Concurrent Gspread API Limits**:
   - **Impact**: Refreshing the Google Sheet backend manually too many times in a short timeframe may trigger a `429 Too Many Requests` error from the Google Sheets API.
3. **No PDF Export Formatting**:
   - **Impact**: The application only supports `.csv` exports natively. Printing dashboards directly via the browser (Ctrl+P) will work but depends heavily on individual browser margin settings.
4. **Historical Month Constraints**:
   - **Impact**: The application statically models months based on `utils/constants.py` mapping logic. Dynamically loading data from unmapped years will result in them being bucketed into the lowest-priority sort order.

## Known Minor Bugs (Deferred)
1. **Plotly Hover Out-of-Bounds on Mobile**:
   - **Description**: On screens less than 400px wide, long hover tooltips on bar charts may partially overflow off the right side of the screen.
2. **Streamlit File Uploader Theme Conflict**:
   - **Description**: If the user's OS forces a dark theme while the app's config forces light, certain input elements may temporarily render dark-on-dark before the app takes precedence.

## Won't Fix (By Design)
1. **Live Synchronous Updates**: WSMIS relies on a caching engine optimized for read-heavy analytical dashboards. Changes made in the Google Sheet will NOT appear in WSMIS until the 1-hour automatic TTL expires, or a manual reload is triggered. This is by design to ensure system stability.
