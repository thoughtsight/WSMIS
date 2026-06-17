# UAT Checklist

This checklist must be used to validate the accuracy and functionality of all dashboards in the WSMIS v1.0.0-rc1 application.

## Validation Criteria
For every item below, verify:
- **KPIs**: Values match source system (Google Sheets/DMS)
- **Charts**: Visualizations render correctly without overlap or scaling issues
- **Tables**: Values aggregate correctly, sorting works
- **Exports**: Downloaded files match the UI data
- **Filters**: Global filters accurately slice the data
- **Navigation**: Switching pages does not cause crashes
- **Loading Speed**: Loads within expected thresholds
- **Formatting**: Currency (INR), percentages (%), and alignments are visually clean
- **Totals**: Column and row totals tie out accurately

---

## 1. Dashboard: Cockpit & Overview
| Test Case | Expected Result | Actual Result | Pass/Fail | Remarks |
|-----------|-----------------|---------------|-----------|---------|
| Validate KPI totals (Labour, Parts, Margin) | Matches raw Google Sheet sum | | [ ] | |
| Verify YoY comparisons | Accurately calculates CP vs PP growth % | | [ ] | |
| Check WS/BS split | Displays correct ratio and revenue amounts | | [ ] | |
| Apply Location filter | Overview recalculates instantly | | [ ] | |

## 2. Dashboard: Revenue (Labour, Parts, Margin, Sales Mix)
| Test Case | Expected Result | Actual Result | Pass/Fail | Remarks |
|-----------|-----------------|---------------|-----------|---------|
| Validate Margin Waterfall chart | Renders cascade from Gross to Net | | [ ] | |
| Sales Mix calculations | Oil/Tyre/Battery totals match sheet | | [ ] | |
| Matrix Rendering | Location × Month matrices populate correctly | | [ ] | |
| Trend Lines | Linear regression forecast lines appear | | [ ] | |

## 3. Dashboard: Discounts & Leakage
| Test Case | Expected Result | Actual Result | Pass/Fail | Remarks |
|-----------|-----------------|---------------|-----------|---------|
| Discount % accuracy | Labour/Parts discount formulas match 15% threshold logic | | [ ] | |
| Leakage amounts | Recoverable leakage is isolated correctly | | [ ] | |
| Advisor Heatmap | High discounts correctly flagged red | | [ ] | |

## 4. Dashboard: Advisors (Advisors, Advisor MoM)
| Test Case | Expected Result | Actual Result | Pass/Fail | Remarks |
|-----------|-----------------|---------------|-----------|---------|
| Scorecard calculation | 1-5 star ratings correctly assigned based on quintiles | | [ ] | |
| Advisor totals | Revenue ties out to location totals | | [ ] | |

## 5. Dashboard: Performance (Locations, Trends, Targets)
| Test Case | Expected Result | Actual Result | Pass/Fail | Remarks |
|-----------|-----------------|---------------|-----------|---------|
| Location Health Grid | 🟢/🟡/🔴 indicators correctly evaluate thresholds | | [ ] | |
| Targets Achievement | Achievement % accurately calculates (Actual/Target) | | [ ] | |
| Trends | 3-month forecast correctly projects next month | | [ ] | |

## 6. Dashboard: Finance (Expense Analysis, P&L)
| Test Case | Expected Result | Actual Result | Pass/Fail | Remarks |
|-----------|-----------------|---------------|-----------|---------|
| Expense Mapping | Expenses correctly matched to location logic | | [ ] | |
| P&L Totals | Net profit ties out | | [ ] | |

## 7. Dashboard: Admin (Reports, Internal Audit)
| Test Case | Expected Result | Actual Result | Pass/Fail | Remarks |
|-----------|-----------------|---------------|-----------|---------|
| Download MIS Summary | Generates formatted Excel file | | [ ] | |
| Internal Audit data | Loads historical audit metrics | | [ ] | |
| AI Narrative (Optional)| Generates text summary successfully | | [ ] | |
