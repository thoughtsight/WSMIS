# WSMIS Audit Intelligence Report — Framework Design

**Version:** 1.0
**Role:** Chief Product Strategist — Internal Audit & MIS
**Audience:** Managing Director, CEO, CFO, GM, Dealer Principal
**Presentation:** Monthly Board Meeting

---

## I. DESIGN PRINCIPLES

This is NOT a dashboard. This is a **formal audit intelligence document** that a Senior Audit Partner presents in a board meeting. The principles that govern its design:

1. **Inverted Pyramid** — Conclusion first, evidence second. The MD should know the answer before seeing the analysis.
2. **Financial Quantification** — Every finding is expressed in ₹. Not "discount is high" but "₹2.3Cr recoverable revenue leakage."
3. **Root Cause, Not Symptom** — "Labour discount is 18%" is a symptom. "3 advisors in Indore are authorised at 30% without Service Head approval" is a root cause.
4. **Actionable Ownership** — Every recommendation has an owner, a deadline, and a measurable outcome.
5. **RAG Priority** — Red means act this week. Amber means act this month. Green means monitor.
6. **5-Minute Read** — Page 1 alone should give the MD 80% of what they need.

---

## II. REPORT STRUCTURE — COMPLETE SECTION ORDER

The report is structured as a **12-section document** presented in a fixed order. The order is designed to follow the natural flow of a board conversation:

```
SECTION                              PAGE    TIME TO READ
─────────────────────────────────────────────────────────
1.  Executive Summary (1-Page Brief)  1       5 minutes
2.  Business Health Scorecard         2       2 minutes
3.  Profit & Loss Commentary          3-4     5 minutes
4.  Revenue Analysis                  5-6     5 minutes
5.  Margin & Leakage Analysis         7-8     5 minutes
6.  Expense Intelligence              9-10    5 minutes
7.  Operational Risk Register         11-12   3 minutes
8.  Advisor Performance Intelligence  13-14   5 minutes
9.  Location Benchmarking             15-16   5 minutes
10. Opportunities & Recovery          17-18   3 minutes
11. Priority Action Plan              19-20   3 minutes
12. 30-60-90 Day Roadmap              21-22   3 minutes
─────────────────────────────────────────────────────────
TOTAL                                 ~22     ~50 minutes
```

**Board Meeting Flow:**
- Pre-read: Section 1 (Executive Summary) — sent 24 hours before the meeting
- Presentation: Sections 2-10 — discussed in the meeting
- Decisions: Sections 11-12 — action items approved in the meeting

---

## III. SECTION-BY-SECTION DESIGN

---

### SECTION 1: EXECUTIVE SUMMARY (1-Page Brief)

**Objective:** Give the MD a complete picture in 5 minutes. This is the only section some directors will read.

**Questions Answered:**
- Are we profitable this period?
- How do we compare to last year?
- Where is money being lost?
- What is the single biggest action required?
- What is the estimated financial recovery if all recommendations are implemented?

**KPIs Required (Top 10):**

| # | KPI | Value | Display | Comparison |
|---|---|---|---|---|
| 1 | **Business Health Score** | 0-100 | Large gauge/number | vs Last Month |
| 2 | Net Revenue | ₹ Cr | Large number | vs PP (YoY %) |
| 3 | Total Margin | ₹ Cr | Large number | vs PP (YoY %) |
| 4 | Gross Profit % | % | Large number | vs PP |
| 5 | Job Cards Processed | Number | Large number | vs PP |
| 6 | Revenue per Job Card | ₹ | Medium number | vs PP |
| 7 | Labour Discount % | % | Amber/Red indicator | vs Benchmark (15%) |
| 8 | Revenue Leakage Identified | ₹ | Red number | Cumulative |
| 9 | Operational Exceptions | Count | Red/Amber indicator | vs Last Month |
| 10 | Estimated Profit Recovery | ₹ | Green number | If all actions implemented |

**Charts Required:**
- None on Page 1. Numbers only. Charts belong on subsequent pages.

**Audit Insights:**
- "Group net revenue of ₹X.XX Cr represents [X%] growth over prior period. However, revenue leakage of ₹XX Lakhs from uncontrolled discounting has reduced effective margin by [X] basis points."
- "Estimated recoverable revenue: ₹XX Lakhs through discount policy enforcement and advisor accountability."

**Recommendations:**
- Display as a single sentence: "Immediate discount audit recommended for [X] locations exceeding 15% threshold."

**Financial Impact:**
- Show as: "Potential recovery: ₹XX Lakhs | Risk if unaddressed: ₹XX Lakhs additional leakage"

---

### SECTION 2: BUSINESS HEALTH SCORECARD

**Objective:** A single composite score (0-100) that quantifies overall business health, decomposed into sub-dimensions.

**Questions Answered:**
- Is the business healthy overall?
- Which dimension is dragging the score down?
- How does each location contribute to (or detract from) the score?

**Score Composition (Weighted):**

| Dimension | Weight | Metrics | RAG Thresholds |
|---|---|---|---|
| **Revenue Health** | 25% | YoY revenue growth, Revenue per JC | Green: >5%, Amber: 0-5%, Red: <0% |
| **Margin Health** | 25% | Gross margin %, Margin per JC | Green: >35%, Amber: 25-35%, Red: <25% |
| **Discount Control** | 20% | Labour disc %, Parts disc % | Green: <12%, Amber: 12-18%, Red: >18% |
| **Operational Efficiency** | 15% | JCs per advisor, TAT, FCR | Green: above median, Amber: median, Red: below median |
| **Growth Trajectory** | 15% | MoM trend, Forecast signal | Green: upward, Amber: flat, Red: downward |

**KPIs Required:**

| # | KPI | Formula | Display |
|---|---|---|---|
| 1 | Business Health Score | Weighted average of 5 dimensions | Large number (0-100) with color |
| 2 | Revenue Health | YoY growth % + Rev/JC vs benchmark | RAG indicator |
| 3 | Margin Health | Gross margin % vs benchmark | RAG indicator |
| 4 | Discount Control | Labour disc % vs 15% benchmark | RAG indicator |
| 5 | Operational Efficiency | Composite of JC/advisor, TAT | RAG indicator |
| 6 | Growth Trajectory | 3-month trend direction | RAG indicator |

**Charts Required:**
1. **Radar Chart** — 5 dimensions plotted on a pentagonal radar, with current period vs target outline
2. **Score Trend Line** — Last 12 months of Business Health Score as a line chart
3. **Location Health Grid** — Heatmap of each location's score across 5 dimensions

**Audit Insights:**
- "Overall Business Health Score: [X/100]. Primary drag: Discount Control at [X/100] due to [X] locations exceeding 15% benchmark."
- "Best performing location: [Name] ([X/100]). Worst performing: [Name] ([X/100])."
- "3-month trend: [Improving/Stable/Declining] — driven by [factor]."

**Recommendations:**
- "Discount Control dimension requires immediate attention. Focus on locations with score <50/100."

**Financial Impact:**
- "If all locations achieve benchmark discount control (15%), estimated margin improvement: ₹XX Lakhs per month."

---

### SECTION 3: PROFIT & LOSS COMMENTARY

**Objective:** Explain what happened to the P&L this month — not just the numbers, but WHY they moved.

**Questions Answered:**
- What is the gross profit vs last year?
- Which line items moved the most?
- What drove the change — volume, mix, or margin?
- Are expenses in line with revenue growth?
- What is the operating profit trend?

**KPIs Required:**

| # | KPI | Value | vs PP | Variance Driver |
|---|---|---|---|---|
| 1 | Gross Revenue | ₹ | YoY % | Volume + Price |
| 2 | Less: Labour Discount | ₹ | YoY % | Policy + Approval |
| 3 | Less: Parts Discount | ₹ | YoY % | Policy + Approval |
| 4 | Net Revenue | ₹ | YoY % | |
| 5 | Cost of Services (COGS) | ₹ | YoY % | |
| 6 | Gross Profit | ₹ | YoY % | |
| 7 | Gross Profit % | % | bps change | |
| 8 | Operating Expenses | ₹ | YoY % | |
| 9 | Operating Profit | ₹ | YoY % | |
| 10 | Operating Profit % | % | bps change | |

**Charts Required:**
1. **P&L Waterfall** — Gross Revenue → Discounts → Net Revenue → COGS → Gross Profit → Expenses → Operating Profit (stacked waterfall showing each deduction)
2. **Monthly Operating Profit Trend** — Line chart with 12-month history, shaded area for target
3. **Variance Bridge** — Horizontal waterfall showing what drove the change from PP to CP (Volume effect, Mix effect, Discount effect, Cost effect)

**Audit Insights:**
- "Operating profit declined ₹XX Lakhs vs prior period. The primary driver was a ₹XX Lakh increase in labour discounts, partially offset by ₹XX Lakh volume growth."
- "Discount as % of gross revenue increased from X% to Y% — a [X] basis point deterioration. If maintained, annual impact: ₹XX Cr."
- "Expense growth of X% outpaced revenue growth of Y%, creating a [X] bps margin compression."

**Recommendations:**
- "Implement discount approval matrix: >15% requires Service Head, >20% requires GM approval."
- "Expense review recommended for [specific category] which grew [X%] vs revenue growth of [Y%]."

**Financial Impact:**
- "Discount policy enforcement: ₹XX Lakhs monthly savings potential"
- "Expense optimization: ₹XX Lakhs identified in [category]"

---

### SECTION 4: REVENUE ANALYSIS

**Objective:** Deep-dive into revenue composition, growth drivers, and volume/mix analysis.

**Questions Answered:**
- What is the revenue by service type (PMS, Repairs, etc.)?
- Which service types are growing, which are declining?
- What is the WS vs BS revenue mix?
- Which locations are driving growth?
- Which locations are declining?
- What is the revenue per advisor trend?

**KPIs Required:**

| # | KPI | Value | Trend | Benchmark |
|---|---|---|---|---|
| 1 | Total Revenue | ₹ | YoY % | |
| 2 | WS Revenue | ₹ | YoY % | |
| 3 | BS Revenue | ₹ | YoY % | |
| 4 | Revenue per JC | ₹ | YoY % | Group median |
| 5 | Revenue per Advisor | ₹ | YoY % | Group median |
| 6 | WS/BS Ratio | % | Trend | Target WS% |
| 7 | Service Type Revenue Mix | % | Trend | |
| 8 | Top 3 Location Contribution | % | Trend | >50% is concentration risk |

**Charts Required:**
1. **Revenue Mix Donut** — WS vs BS, with inner ring showing service type breakdown
2. **Revenue by Service Type (Stacked Bar)** — Monthly trend, stacked by PMS/Repair/Other
3. **Location Revenue Ranking** — Horizontal bar chart, top to bottom, with YoY% annotation
4. **Revenue per Advisor Box Plot** — Distribution of advisor revenue, showing median, quartiles, outliers
5. **Revenue Concentration Chart** — Cumulative contribution of top 3, top 5, top 10 locations

**Audit Insights:**
- "BS revenue represents [X%] of total — [above/below] industry benchmark of [Y%]. BS typically carries lower margin; monitor if WS/BS ratio is deteriorating."
- "Revenue concentration: Top 3 locations contribute [X%] of total revenue. If any top location declines, group impact is significant."
- "[X] advisors have revenue below [threshold] — potential underperformance or training gap."
- "PMS revenue as % of total is [X%] — [above/below] target. PMS is typically higher margin; low PMS penetration indicates missed service revenue."

**Recommendations:**
- "Increase PMS penetration through advisor training and customer follow-up automation."
- "Review WS/BS mix — if BS is growing faster than WS, investigate pricing policy."
- "Focus on bottom-quartile advisors: potential [₹XX Lakhs] revenue uplift if brought to median."

**Financial Impact:**
- "PMS penetration increase from [X%] to [Y%]: ₹XX Lakhs additional revenue"
- "Bottom-quartile advisor improvement to median: ₹XX Lakhs revenue uplift"

---

### SECTION 5: MARGIN & LEAKAGE ANALYSIS

**Objective:** Quantify exactly how much revenue is being lost to discounting, and identify where the leakage originates.

**Questions Answered:**
- What is the total revenue leakage?
- Which locations have the highest leakage?
- Which advisors are the biggest leakers?
- What is the root cause of high discounts?
- What is the leakage trend over time?
- What is recoverable vs unrecoverable?

**KPIs Required:**

| # | KPI | Value | vs Benchmark | Trend |
|---|---|---|---|---|
| 1 | Labour Discount % | % | vs 15% benchmark | Monthly trend |
| 2 | Parts Discount % | % | vs 10% benchmark | Monthly trend |
| 3 | Total Leakage (Labour) | ₹ | Above benchmark | |
| 4 | Total Leakage (Parts) | ₹ | Above benchmark | |
| 5 | Total Recoverable Leakage | ₹ | | |
| 6 | Locations Above Benchmark | Count | | |
| 7 | Advisors Above Benchmark | Count | | |
| 8 | Leakage as % of Margin | % | | |
| 9 | Leakage per JC | ₹ | vs group average | |
| 10 | Leakage Recovery Rate | % | | |

**Charts Required:**
1. **Leakage Waterfall** — Gross Labour → Labour Discount → Net Labour, showing benchmark line at 15%
2. **Location Leakage Heatmap** — Location × Month, colour-coded by severity
3. **Advisor Leakage Ranking** — Top 10 advisors by leakage amount, with severity badge
4. **Discount Trend with Benchmark** — Monthly labour disc % with 15% dashed benchmark line and 3-month rolling average
5. **Leakage vs Margin Scatter** — Each location plotted: X-axis = Discount %, Y-axis = Total Margin. Shows locations in the "danger quadrant" (high discount, low margin)
6. **Cumulative Leakage Trend** — Running total of leakage over the fiscal year

**Audit Insights:**
- "Total recoverable leakage this period: ₹XX Lakhs. This represents [X%] of total margin earned."
- "Leakage is concentrated: [X] locations ([X%] of total) account for [Y%] of total leakage."
- "Root cause analysis: [X]% of high-discount advisors have discount authority above 15% without documented approval. [Y]% of leakage occurs on job cards below ₹5,000 value — indicating potential customer-facing discount abuse."
- "Labour leakage is trending [up/down] over the last 3 months. If trend continues, annual impact: ₹XX Cr."
- "Parts leakage at [X%] is [above/below] the 10% benchmark. [X] locations exceed threshold."

**Recommendations:**
- "Immediate: Cap advisor discount authority at 15%. Any discount above 15% requires Service Head digital approval."
- "Audit all job cards below ₹5,000 labour value with discount >10% — potential abuse."
- "Implement monthly discount review meeting with location heads — review top 5 leakers."
- "Parts discount policy review: enforce 10% ceiling with parts manager sign-off."

**Financial Impact:**
- "Discount cap enforcement (15%): ₹XX Lakhs monthly recovery"
- "Parts discount policy (10% ceiling): ₹XX Lakhs monthly recovery"
- "Total annualised recovery potential: ₹XX Cr"

---

### SECTION 6: EXPENSE INTELLIGENCE

**Objective:** Analyse expenses not just as totals, but as ratios to revenue, with trend analysis and anomaly detection.

**Questions Answered:**
- What is the expense-to-revenue ratio?
- Which expense categories are growing faster than revenue?
- Are there any anomalous expense spikes?
- What is the cost per job card?
- How do locations compare on expense efficiency?

**KPIs Required:**

| # | KPI | Value | vs PP | Benchmark |
|---|---|---|---|---|
| 1 | Total Operating Expenses | ₹ | YoY % | |
| 2 | Expense-to-Revenue Ratio | % | bps change | <X% target |
| 3 | Cost per Job Card | ₹ | YoY % | Group median |
| 4 | Staff Cost as % of Revenue | % | bps change | |
| 5 | Consumables Cost as % of Revenue | % | bps change | |
| 6 | Overhead Cost as % of Revenue | % | bps change | |
| 7 | Expense Growth vs Revenue Growth | bps | Trend | 0 (equal) |
| 8 | Top 3 Expense Categories | ₹ each | Trend | |

**Charts Required:**
1. **Expense Waterfall** — Revenue → COGS → Gross Profit → Expenses → Operating Profit
2. **Expense-to-Revenue Ratio Trend** — 12-month line chart with benchmark
3. **Expense Category Breakdown** — Donut chart with top categories
4. **Location Expense Efficiency** — Bar chart showing cost per JC by location, ranked
5. **Expense Growth vs Revenue Growth** — Scatter plot: X = Revenue growth %, Y = Expense growth %. Locations above the 45° line have expenses growing faster than revenue.

**Audit Insights:**
- "Expense-to-revenue ratio is [X%], [X bps] [above/below] prior period. [Location] has highest ratio at [X%]."
- "[Category] expense grew [X%] while revenue grew [Y%] — a [Z] bps deterioration. This is the fastest-growing expense line."
- "Cost per job card: ₹[X] vs group median ₹[Y]. [X] locations are above median — review staffing and overhead allocation."
- "Staff cost as % of revenue: [X%]. If above [Y%], review advisor-to-revenue productivity."

**Recommendations:**
- "Conduct expense audit for locations with expense ratio > [X%] of revenue."
- "Review [category] spending — growth of [X%] is [Y bps] above revenue growth."
- "Benchmark cost per JC: locations above ₹[X] should justify staffing levels."

**Financial Impact:**
- "Expense optimisation potential: ₹XX Lakhs per month if all locations achieve group median cost per JC."
- "Staff cost rebalancing: ₹XX Lakhs if advisor-to-revenue ratio matches top quartile."

---

### SECTION 7: OPERATIONAL RISK REGISTER

**Objective:** Identify and quantify operational risks that could impact financial performance, with severity, likelihood, and mitigation.

**Questions Answered:**
- What are the top 5 risks to profitability right now?
- Which risks are new this month?
- Which risks have increased in severity?
- What is the financial exposure of each risk?
- Who owns each risk?

**Risk Categories:**

| # | Risk Category | Example Risk | Financial Exposure |
|---|---|---|---|
| 1 | **Revenue Risk** | High discount % at key location | ₹ XX Lakhs leakage |
| 2 | **Margin Risk** | Parts margin erosion from supplier pricing | ₹ XX Lakhs margin loss |
| 3 | **Operational Risk** | High VOR charges (excess stock) | ₹ XX Lakhs in charges |
| 4 | **People Risk** | Top advisor attrition | ₹ XX Lakhs revenue at risk |
| 5 | **Compliance Risk** | Unauthorised discounting | ₹ XX Lakhs policy violation |
| 6 | **Concentration Risk** | Top 3 locations = >60% revenue | ₹ XX Cr if one location fails |
| 7 | **Growth Risk** | Declining YoY at >3 locations | ₹ XX Lakhs revenue decline |

**Required Output per Risk:**

| Field | Description |
|---|---|
| Risk ID | Unique identifier (R-001, R-002, etc.) |
| Risk Title | Short description |
| Category | Revenue / Margin / Operational / People / Compliance / Concentration |
| Severity | Critical / High / Medium / Low |
| Financial Exposure | ₹ value |
| Likelihood | High / Medium / Low |
| Risk Score | Severity × Likelihood |
| Trend | Worsening / Stable / Improving |
| Mitigation | Specific action to reduce risk |
| Owner | Named individual |
| Deadline | Target resolution date |

**Charts Required:**
1. **Risk Heat Matrix** — 3×3 grid: Severity (Y) × Likelihood (X), with risks plotted as bubbles
2. **Risk Trend Over Time** — Line chart showing total risk count by severity over 6 months
3. **Risk by Category** — Bar chart of financial exposure by risk category

**Audit Insights:**
- "Total financial exposure from active risks: ₹XX Cr."
- "Risk severity has [increased/decreased] by [X%] vs last month."
- "New risk identified: [description]. Financial exposure: ₹XX Lakhs."
- "[X] risks are Critical and require board attention this month."

**Recommendations:**
- "Immediate escalation required for [X] Critical risks."
- "Board approval needed for [risk mitigation action] with estimated cost of ₹XX Lakhs."

**Financial Impact:**
- "Risk mitigation investment: ₹XX Lakhs"
- "Risk avoidance savings: ₹XX Cr annually"

---

### SECTION 8: ADVISOR PERFORMANCE INTELLIGENCE

**Objective:** Individual advisor analysis from an audit perspective — who is driving value, who is leaking value, and what action is required.

**Questions Answered:**
- Who are the top 5 value-creating advisors?
- Who are the top 5 value-leaking advisors?
- Which advisors have the highest discount rates?
- Which advisors are trending downward?
- What is the revenue impact of underperformance?
- Which advisors need coaching vs which need intervention?

**KPIs Required:**

| # | KPI | Value | Rank | Trend |
|---|---|---|---|---|
| 1 | Net Labour per JC | ₹ | Rank | 6-month trend |
| 2 | Labour Discount % | % | Rank | 6-month trend |
| 3 | Revenue per JC | ₹ | Rank | 6-month trend |
| 4 | Oil Penetration % | % | Rank | 6-month trend |
| 5 | Parts per JC | ₹ | Rank | 6-month trend |
| 6 | Composite Score | /5 | Rank | 6-month trend |
| 7 | Total Revenue Generated | ₹ | Rank | vs period target |
| 8 | Total Leakage Caused | ₹ | Rank | |

**Advisor Segmentation (4-Box Matrix):**

| Quadrant | Description | Action |
|---|---|---|
| **Stars** (High Revenue, Low Discount) | Value creators | Retain, reward, replicate |
| **Cash Cows** (High Revenue, High Discount) | Revenue but margin leak | Coach on discount discipline |
| **Question Marks** (Low Revenue, Low Discount) | Potential but not performing | Train, mentor, set targets |
| **Underperformers** (Low Revenue, High Discount) | Double negative | Intervention, performance plan |

**Charts Required:**
1. **Advisor Performance Scatter** — X = Revenue per JC, Y = Discount %, Bubble size = Total JCs, Colour = Location. Four quadrants labelled.
2. **Discount Distribution Histogram** — Distribution of advisor discount rates, showing the 15% benchmark line and outliers
3. **Top 5 / Bottom 5 Bar Charts** — Side by side, showing composite score ranking
4. **Advisor Trend Lines** — 6-month composite score trend for each advisor (filtered by location)
5. **Advisor Leakage Pareto** — Bar chart showing cumulative leakage by advisor (Pareto: top 20% of advisors cause 80% of leakage)

**Audit Insights:**
- "Top 20% of advisors (by leakage) cause [X%] of total revenue leakage. Focused intervention on [X] advisors could recover ₹XX Lakhs."
- "[Advisor Name] has consistently high discount ([X%]) across [Y] months. This is a systemic pattern, not a one-time issue."
- "[X] advisors have declining composite scores for 3+ consecutive months. Early intervention recommended."
- "Oil penetration below [X%] at [Y] locations suggests missed revenue opportunity of ₹XX Lakhs per month."

**Recommendations:**
- "Performance improvement plan for bottom 10 advisors: 60-day target to reach group median discount %."
- "Reward top 5 advisors: retention risk if stars are not recognised."
- "Oil penetration drive: target 70% penetration across all locations."
- "Coaching programme for high-revenue, high-discount advisors (Cash Cows) — they have the skill but lack discount discipline."

**Financial Impact:**
- "Bottom 10 advisor improvement to median: ₹XX Lakhs revenue uplift + ₹XX Lakhs leakage reduction"
- "Oil penetration increase to 70%: ₹XX Lakhs additional revenue"
- "Total advisor optimisation potential: ₹XX Lakhs per month"

---

### SECTION 9: LOCATION BENCHMARKING

**Objective:** Compare locations against each other and against benchmarks to identify outliers and best practices.

**Questions Answered:**
- Which location is performing best overall?
- Which location is the biggest concern?
- How does each location compare to the group average?
- Are there best practices from top locations that can be replicated?
- What is the Arena vs Nexa performance gap?
- Which locations are declining?

**KPIs Required:**

| # | KPI | Location Avg | Best | Worst | Benchmark |
|---|---|---|---|---|---|
| 1 | Net Labour | ₹ | ₹ | ₹ | |
| 2 | Labour/JC | ₹ | ₹ | ₹ | Group median |
| 3 | Labour Discount % | % | % | % | 15% |
| 4 | Total Margin | ₹ | ₹ | ₹ | |
| 5 | Margin per JC | ₹ | ₹ | ₹ | Group median |
| 6 | JCs per Advisor | # | # | # | |
| 7 | YoY Revenue Growth | % | % | % | 0% |
| 8 | Arena vs Nexa Gap | % | | | |

**Charts Required:**
1. **Location Scorecard Grid** — Heatmap: Location × KPI, colour-coded green/yellow/red
2. **Location Ranking Bar Chart** — Horizontal bars ranked by composite score, with RAG badge
3. **Arena vs Nexa Comparison** — Side-by-side grouped bars: JCs, Labour, Margin, Discount%
4. **Location Trend Lines** — 12-month revenue trend for each location (small multiples or overlaid lines)
5. **Location vs Group Median** — Bullet charts showing each location's performance against group median
6. **Location Correlation Matrix** — Scatter: Discount % vs Margin % (each dot = location)

**Audit Insights:**
- "Location [Name] has the highest discount ([X%]) and lowest margin ([Y%]) — urgent review needed."
- "Arena locations outperform Nexa locations by [X%] in margin per JC. Best practices should be documented and replicated."
- "[X] locations show declining YoY revenue for 3+ consecutive months — turnaround plan required."
- "Best-performing location [Name] achieves [X%] lower discount than worst-performing [Name] with similar revenue — proof that discount control is achievable."

**Recommendations:**
- "Adopt best practices from top-performing location [Name] — schedule cross-location knowledge sharing."
- "Turnaround plan for declining locations: 90-day intensive review with weekly KPI tracking."
- "Arena vs Nexa gap analysis: identify specific operational differences driving the gap."
- "Monthly location ranking review at management meeting — create healthy competition."

**Financial Impact:**
- "If worst location achieves group median performance: ₹XX Lakhs additional margin"
- "Arena best practice replication to Nexa: ₹XX Lakhs margin improvement potential"

---

### SECTION 10: OPPORTUNITIES & RECOVERY

**Objective:** Quantify specific, actionable profit improvement opportunities with clear owners and timelines.

**Questions Answered:**
- How much additional profit can we realistically recover?
- What are the top 5 opportunities ranked by financial impact?
- What is the quick-win vs long-term gain split?
- Who should own each opportunity?
- What is the investment required vs expected return?

**Opportunity Categories:**

| # | Opportunity | Source | Recovery Potential | Effort |
|---|---|---|---|---|
| 1 | **Discount Policy Enforcement** | Leakage analysis | ₹ XX Lakhs/month | Low |
| 2 | **Oil Penetration Improvement** | Sales mix analysis | ₹ XX Lakhs/month | Medium |
| 3 | **Advisor Performance Uplift** | Advisor analysis | ₹ XX Lakhs/month | Medium |
| 4 | **Parts Margin Optimisation** | Margin analysis | ₹ XX Lakhs/month | Medium |
| 5 | **Expense Rationalisation** | Expense analysis | ₹ XX Lakhs/month | High |
| 6 | **BS-to-WS Conversion** | Revenue analysis | ₹ XX Lakhs/month | High |
| 7 | **New Service Revenue** | Market analysis | ₹ XX Lakhs/month | High |

**Required Output per Opportunity:**

| Field | Description |
|---|---|
| Opportunity ID | Unique identifier (O-001, O-002, etc.) |
| Title | Short description |
| Category | Leakage / Revenue / Cost / Process |
| Monthly Recovery Potential | ₹ value |
| Annualised Impact | ₹ value |
| Investment Required | ₹ value |
| ROI | Return on investment ratio |
| Timeline | Quick-win (<30 days), Medium (30-90 days), Long-term (90+ days) |
| Owner | Named individual |
| Dependencies | What needs to happen first |
| Confidence Level | High / Medium / Low |

**Charts Required:**
1. **Opportunity Waterfall** — Current Profit → + Quick Wins → + Medium Gains → + Long-term → Target Profit
2. **Opportunity Priority Matrix** — 2×2 grid: Impact (Y) × Effort (X), with opportunities plotted as bubbles
3. **Recovery Timeline** — Gantt-style chart showing when each opportunity's impact is realised
4. **ROI Comparison** — Bar chart showing ROI for each opportunity (sorted highest to lowest)

**Audit Insights:**
- "Total identified recovery potential: ₹XX Lakhs per month (₹XX Cr annualised)."
- "Quick wins (<30 days): ₹XX Lakhs/month — requires policy enforcement only."
- "Top opportunity: Discount policy enforcement with [X:1] ROI — minimal investment, high return."
- "Opportunities ranked by confidence: [X] at High confidence, [Y] at Medium, [Z] at Low."

**Recommendations:**
- "Approve quick-win actions immediately — no capital investment required."
- "Allocate project team for medium-term opportunities — estimated 90-day implementation."
- "Commission feasibility study for long-term opportunities."

**Financial Impact:**
- "If all opportunities realised: ₹XX Cr additional annual profit"
- "Conservative estimate (50% realisation): ₹XX Cr"
- "Minimum guaranteed (quick wins only): ₹XX Lakhs per month"

---

### SECTION 11: PRIORITY ACTION PLAN

**Objective:** Translate all findings into a clear, owned, time-bound action list.

**Questions Answered:**
- What exactly needs to happen?
- Who is responsible?
- By when?
- What is the expected outcome?
- What happens if we don't act?

**Action Plan Table:**

| Priority | Action | Owner | Deadline | Expected Outcome | Risk of Delay | Status |
|---|---|---|---|---|---|---|
| 🔴 Critical | Cap discount at 15% — all locations | Group Service Head | Week 1 | ₹XX L/month recovery | ₹XX L additional leakage | |
| 🔴 Critical | Audit top 5 leakage advisors | Location Manager | Week 2 | Identify root cause | Continued revenue loss | |
| 🟡 High | Implement discount approval matrix | IT + Operations | Week 3 | Policy enforcement | Policy remains unenforced | |
| 🟡 High | Oil penetration drive | Marketing + Advisors | Month 1 | 70% penetration target | ₹XX L missed revenue | |
| 🟡 High | Advisor performance improvement plan | HR + Location Manager | Month 2 | Bottom 10 to median | Continued underperformance | |
| 🟢 Medium | Expense audit for high-ratio locations | CFO | Month 2 | ₹XX L cost savings | Expenses continue above benchmark | |
| 🟢 Medium | Arena-to-Nexa best practice transfer | GM | Month 3 | ₹XX L margin improvement | Performance gap persists | |
| 🔵 Low | PMS penetration increase programme | Service Head | Quarter 2 | ₹XX L revenue | Missed service revenue | |

**Charts Required:**
1. **Action Timeline** — Gantt chart showing all actions across 90 days
2. **Action Status Dashboard** — Count of actions by status (Not Started / In Progress / Completed)
3. **Priority Distribution** — Pie chart of actions by priority level

**Audit Insights:**
- "[X] actions are Critical and require immediate board attention."
- "Total actions: [X]. [Y] are overdue from last month."
- "If all actions completed on time, estimated financial recovery: ₹XX Cr."

**Recommendations:**
- "Approve all Critical actions at this board meeting."
- "Assign dedicated owners for High-priority actions — no shared ownership."
- "Monthly review of action plan at management meeting."

**Financial Impact:**
- "Action plan completion value: ₹XX Cr annually"
- "Cost of inaction: ₹XX Cr annually"

---

### SECTION 12: 30-60-90 DAY ROADMAP

**Objective:** Provide a phased implementation plan that management can approve and track.

**Questions Answered:**
- What happens in the first 30 days?
- What happens in days 31-60?
- What happens in days 61-90?
- What are the milestones and checkpoints?
- What does "done" look like?

**30-60-90 Structure:**

**Days 1-30: Quick Wins (Stabilise)**
| Week | Action | Owner | Milestone |
|---|---|---|---|
| 1 | Discount cap communication to all locations | Service Head | Policy issued |
| 1 | Top 5 leakage advisor investigation | Location Manager | Root cause identified |
| 2 | Discount approval matrix implementation | IT | System live |
| 2 | Negative labour alert review | Operations | All alerts addressed |
| 3 | Parts discount policy review | Parts Manager | New policy drafted |
| 4 | First monthly discount review meeting | GM | Meeting conducted |
| 4 | Quick-win recovery tracking | CFO | First ₹ measured |

**Days 31-60: Process Embedding (Improve)**
| Week | Action | Owner | Milestone |
|---|---|---|---|
| 5 | Advisor performance improvement plans (bottom 10) | HR | PIPs initiated |
| 5 | Oil penetration drive launch | Marketing | Campaign live |
| 6 | Expense audit completion for 3 highest-ratio locations | CFO | Audit report issued |
| 7 | Arena best practice documentation | GM | Best practice guide published |
| 8 | Second monthly discount review | GM | Trend improvement visible |
| 8 | Mid-point recovery assessment | CFO | ₹XX L recovery confirmed |

**Days 61-90: Strategic Positioning (Scale)**
| Week | Action | Owner | Milestone |
|---|---|---|---|
| 9 | Nexa operational improvement programme | GM | Programme launched |
| 9 | PMS penetration programme | Service Head | Pilot in 3 locations |
| 10 | Advisor coaching programme at scale | HR | 50% of advisors enrolled |
| 11 | Third monthly review — all metrics | GM | Improvement confirmed |
| 12 | Board progress report | CFO | Full progress report |
| 12 | Next quarter planning | MD + CFO | Q2 targets set |

**Charts Required:**
1. **90-Day Gantt Chart** — All actions plotted on a 12-week timeline with milestones
2. **Progress Tracker** — % completion at each checkpoint (30, 60, 90 days)
3. **Expected Recovery Curve** — Cumulative ₹ recovery over 90 days

**Audit Insights:**
- "30-day checkpoint: Expected recovery ₹XX Lakhs from discount policy enforcement alone."
- "60-day checkpoint: Process improvements embedded, recovery trending to ₹XX Lakhs/month."
- "90-day checkpoint: Strategic improvements showing initial results. Full impact expected by Month 6."

**Recommendations:**
- "Board to approve 30-day quick-win actions immediately."
- "Monthly progress review at board meeting — CFO to report against milestones."
- "If 30-day milestones are not met, escalate to MD for intervention."

**Financial Impact:**
- "30-day recovery: ₹XX Lakhs"
- "60-day cumulative recovery: ₹XX Lakhs"
- "90-day cumulative recovery: ₹XX Lakhs"
- "12-month projected recovery: ₹XX Cr"

---

## IV. PAGE 1 — WHAT SHOULD APPEAR

Page 1 is the **entire report for a busy director**. It must contain:

```
┌─────────────────────────────────────────────────────────┐
│  WSMIS AUDIT INTELLIGENCE REPORT                       │
│  Period: [Month Year] | Prepared by: [CA Firm Name]    │
│  Confidential — Board Meeting Use Only                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  BUSINESS HEALTH SCORE: [78]/100  🟡                   │
│  (vs 82 last month — declining)                        │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  HEADLINE NUMBERS                                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Net Rev  │ │ Margin   │ │ Disc %   │ │ Leakage  │  │
│  │ ₹X.XX Cr │ │ ₹X.XX Cr │ │ X.X%    │ │ ₹XX L    │  │
│  │ +X% YoY  │ │ -X% YoY  │ │ vs 15%  │ │ Recoverable│
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🔴 CRITICAL ACTIONS (Board Decision Required)          │
│  1. Discount cap enforcement — ₹XX L recovery          │
│  2. Top 5 advisor investigation — ₹XX L at risk        │
│                                                         │
│  🟡 HIGH PRIORITY (Management Action)                   │
│  3. Oil penetration drive — ₹XX L opportunity          │
│  4. Expense audit — 3 locations above benchmark         │
│                                                         │
│  🟢 MONITORING (Normal Course)                          │
│  5. Arena-Nexa gap — best practice transfer             │
│  6. PMS penetration — long-term revenue growth          │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  FINANCIAL RECOVERY SUMMARY                             │
│  Quick Wins (<30 days):    ₹XX Lakhs/month             │
│  Medium Term (30-90 days): ₹XX Lakhs/month             │
│  Long Term (90+ days):     ₹XX Lakhs/month             │
│  ─────────────────────────────────────────               │
│  TOTAL ANNUALISED:         ₹XX Cr                       │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  TOP 3 RISKS THIS PERIOD                               │
│  R-001: [Risk description] — ₹XX L exposure            │
│  R-002: [Risk description] — ₹XX L exposure            │
│  R-003: [Risk description] — ₹XX L exposure            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## V. WHAT MANAGEMENT SHOULD READ IN UNDER 5 MINUTES

The 5-minute read is Page 1 only. It answers these questions in this order:

| Question | Where on Page 1 | Time |
|---|---|---|
| **Are we healthy?** | Business Health Score (top) | 10 seconds |
| **How much did we make?** | Headline Numbers (4 boxes) | 30 seconds |
| **What's wrong?** | Critical Actions (Red) | 1 minute |
| **What should we do?** | High Priority (Amber) | 1 minute |
| **How much can we recover?** | Financial Recovery Summary | 1 minute |
| **What are we worried about?** | Top 3 Risks | 1 minute |
| | **Total** | **~5 minutes** |

---

## VI. RAG PRIORITY SYSTEM

### Red (Critical) — Board Decision Required
- **Criteria:** Financial impact > ₹10 Lakhs per month OR compliance violation OR revenue at risk
- **Display:** Red border, red icon, first in list
- **Decision:** Must be approved at this board meeting
- **Follow-up:** Next board meeting — status report

### Amber (High) — Management Action Required
- **Criteria:** Financial impact ₹5-10 Lakhs per month OR operational risk OR performance below benchmark
- **Display:** Amber border, amber icon, second in list
- **Decision:** Management to implement within 30 days
- **Follow-up:** Monthly review at management meeting

### Green (Medium) — Monitor and Improve
- **Criteria:** Financial impact < ₹5 Lakhs per month OR best-practice improvement OR long-term opportunity
- **Display:** Green border, green icon, third in list
- **Decision:** Include in regular operations review
- **Follow-up:** Quarterly review

### Blue (Informational) — For Awareness
- **Criteria:** No immediate financial impact OR market intelligence OR benchmarking data
- **Display:** Blue border, blue icon, last in list
- **Decision:** No immediate action required
- **Follow-up:** Next quarterly review

---

## VII. RECOMMENDATIONS THAT SHOULD ALWAYS BE GENERATED

These are **system-generated recommendations** that should appear in every report automatically based on data thresholds:

### Automatic Red Recommendations (appear if condition is met):
1. "Labour discount exceeds 25% at [Location] — immediate investigation required."
2. "Net labour is negative for [Advisor] at [Location] — review job card reversals."
3. "VOR charges exceed ₹2,00,000 — excess stock review needed."
4. "Revenue decline >15% YoY at [Location] — turnaround plan required."
5. "Parts discount exceeds 10% benchmark at [X] locations — policy review needed."

### Automatic Amber Recommendations (appear if condition is met):
1. "Labour discount between 15-25% at [Location] — monitor and enforce policy."
2. "Advisor composite score <2/5 for 3+ consecutive months — coaching programme."
3. "Oil penetration below 50% at [Location] — missed revenue opportunity."
4. "Expense-to-revenue ratio above group average at [Location] — cost review."
5. "Top 3 locations contribute >60% of revenue — concentration risk."

### Automatic Green Recommendations (appear if condition is met):
1. "Best-performing location [Name] — document and replicate best practices."
2. "Advisor [Name] has highest composite score — potential for team lead role."
3. "Margin per JC trending upward — positive trajectory, maintain course."
4. "Oil penetration above 70% at [Location] — benchmark for other locations."

---

## VIII. DATA FLOW FROM WSMIS TO REPORT

The report pulls data from WSMIS through these mappings:

| Report Section | WSMIS Source | Data Points |
|---|---|---|
| Executive Summary | `cockpit.py` + `executive.py` | KPI cards, alert summary |
| Business Health | `cockpit.py` + calculated | Health score computation |
| P&L Commentary | `pnl.py` + `margin.py` | P&L waterfall, margin components |
| Revenue Analysis | `yoy.py` + `sales_mix.py` | Revenue by type, by location, WS/BS |
| Margin & Leakage | `leakage.py` + `margin.py` | Discount %, leakage Rs, benchmarks |
| Expense Intelligence | `expense.py` | Expense categories, ratios |
| Operational Risks | `internal_audit.py` | Exception audit findings |
| Advisor Intelligence | `advisor.py` + `advisor_mom.py` | Scorecard, trends, rankings |
| Location Benchmarking | `locations.py` + `yoy.py` | Location health cards, comparisons |
| Opportunities | `cockpit.py` (Top 3 Opportunities) + calculated | Recovery potential |
| Action Plan | Generated from all findings | Prioritised actions |
| 30-60-90 Roadmap | Generated from action plan | Phased timeline |

---

## IX. REPORT CADENCE

| Report | Frequency | Audience | Duration |
|---|---|---|---|
| **Full Audit Intelligence Report** | Monthly | Board | 22 pages, 50 min |
| **Executive Brief (Page 1 only)** | Monthly | MD (pre-read) | 1 page, 5 min |
| **Flash Report (Key Metrics Only)** | Weekly | CEO + CFO | 1 page, 2 min |
| **Deep-Dive: Leakage** | Quarterly | Audit Committee | 10 pages, 30 min |
| **Deep-Dive: Advisor Performance** | Quarterly | HR + Operations | 8 pages, 20 min |
| **Annual Audit Summary** | Annually | Board + Auditors | 30 pages, 60 min |

---

*End of Audit Intelligence Framework Design*
