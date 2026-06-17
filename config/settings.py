import os

# Application Settings
APP_NAME = "WSMIS Analytics"
VERSION = "1.0.0-RC"

# ── Discount Benchmarks ───────────────────────────────────────────────────────
LABOUR_DISC_BENCH = 15      # % — max acceptable labour discount
PARTS_DISC_BENCH  = 10      # % — max acceptable parts discount
HIGH_DISC_ALERT   = 25      # % — critical labour discount threshold (exception)
DISC_CONCERN_PCT  = 20      # % — discount level that triggers concern (not critical)

# ── Performance Alert Thresholds ─────────────────────────────────────────────
YOY_DECLINE_ALERT    = 15   # % magnitude — YoY decline to trigger red alert
VOR_ALERT_THRESHOLD  = 200000  # ₹ — VOR charges above this trigger warning

# ── Traffic-Light Thresholds (YoY growth %) ──────────────────────────────────
TRAFFIC_GREEN_PCT = 10      # % growth for green light
TRAFFIC_RED_PCT   = 10      # % decline magnitude for red light
