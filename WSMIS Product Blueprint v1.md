I'll start by reading the full backlog document so my product blueprint is grounded in what WSMIS actually contains today, not just the preview.
The document you attached is a single artifact: an engineering cleanup backlog (duplicate loaders, groupby calls, cache usage). The brief you've written, though, references a much larger set — "the complete WSMIS Architecture Pack together with Parts Module reviews, architecture audits, navigation discussions and product documents." Only the backlog file is in the workspace.

I can still deliver the full Product Blueprint you asked for, but I want to be transparent about what it's grounded in: I'll infer the product surface of WSMIS from what the backlog reveals (module names, view files, KPI domains) and build the architecture on dealership-BI domain knowledge benchmarked against the platforms you named. Where I'm inferring rather than reading from a source document, I'll mark it so you can correct it.

Here's what the backlog tells me about the current product surface — I'm reading the product out of the engineering file names:

| Signal in backlog | Product module it implies |
|---|---|
| views/executive/commandcenter.py | Executive Command Center dashboard |
| views/commercial/discount.py, labour.py, salesmix.py, partsexecutive.py | Commercial: Discount, Labour, Sales Mix, Parts Executive |
| services/auditservice.py, audit loaders | Audit module |
| utils/calculations/leakage.py, revenueleakagev2.py | Revenue Leakage reporting |
| ui/traffic.py | Traffic / throughput reporting |
| MPPBTargets, discount targets, margin | Targets & margin/discount governance |
| expreport.py | An "export / executive report" generator |

That gives me Executive, Commercial (Parts + Labour + Discount + Sales Mix), Audit, Revenue Leakage, Traffic, and Targets as the confirmed live surface. Everything else in your 15-section brief (Finance, Performance, OEM benchmarking, Copilot, Mobile) I'll design as the target architecture.

WSMIS Product Blueprint v1.0
The Canonical Product Reference — Dealership Analytics Platform

Supersedes all prior navigation discussions and architecture notes. This is the governing product document.

Overall Product Vision

WSMIS is a decision platform, not a reporting tool.

The single most important reframing: today WSMIS appears organized around reports (Discount report, Labour report, Leakage report). Every benchmark platform you named — Tableau Enterprise, Power BI Apps, Tekion, DealerSocket — abandoned report-centric design years ago. They organize around decisions and roles.

The vision statement that should govern every future decision:

> WSMIS surfaces the few decisions a dealership leader must make today, proves them with drill-down evidence, and lets operational staff act — without anyone opening a "report."

Three principles that fall out of this:

Answers, not reports. An executive should never navigate to a report to discover a problem. The platform pushes the problem to them; the report exists only as the drill-down proof.
One number, one home. Every KPI is owned by exactly one module. All other appearances are references, not redefinitions. (Today the backlog shows margin/discount/growth math scattered across 8+ surfaces — that is a product symptom, not just a code one: it means the same KPI can disagree with itself across screens.)
Role determines surface. The MD, the Workshop Manager, and the Internal Auditor see three different products built on one data spine. Navigation is filtered by role, not by report inventory.

Complete Information Architecture

The product hierarchy is eight domains, ordered by decision altitude (highest first):

``
WSMIS
│
├── 1. EXECUTIVE          ← "What needs my attention?"  (MD/CEO)
│      Command Center · Group Scorecard · Exception Feed
│
├── 2. OPERATIONS         ← "Is the workshop running?"   (Workshop/Service Mgr)
│      Throughput · Workshop Loading · Job Card Status · Advisor Performance
│
├── 3. COMMERCIAL         ← "Are we making money on the work?"  (Commercial Mgr)
│      Labour · Parts · Sales Mix · Discount Governance · Pricing
│
├── 4. FINANCE            ← "Is revenue real and collected?"  (FC/Finance)
│      Revenue Recognition · Margin Bridge · WIP & Debtors · Profitability
│
├── 5. AUDIT              ← "Is anything leaking or out of policy?"  (Internal Audit)
│      Revenue Leakage · Discount Compliance · Exception Casework · Controls
│
├── 6. PERFORMANCE        ← "Are we hitting targets & improving?"  (All managers)
│      Targets vs Actual · Trends · Benchmarking · League Tables
│
├── 7. AI COPILOT         ← "Ask anything"  (All roles, role-scoped)
│      Natural-language Q&A · Narrative summaries · Anomaly alerts
│
└── 8. ADMINISTRATION     ← "Run the platform"  (Admin)
       Users & Roles · Data Sources · KPI Definitions · Targets Setup · Audit Log
`

The key architectural moves vs. today:

• Revenue Leakage moves OUT of Commercial and INTO Audit. Leakage is an exception/compliance concept, not a commercial-performance concept. Today it sits with discount/labour; that's a category error. Commercial manages margin; Audit catches what escaped.
• Traffic/Throughput becomes the spine of a new Operations domain rather than a standalone report. Workshop Managers live here.
• Parts Executive is demoted from a top-level "executive" report to a Commercial sub-domain. There should be one Executive surface, not a parallel "parts executive" one — that's duplicated navigation.
• Targets gets its own home (Performance + Admin split): defining targets lives in Administration; tracking against them lives in Performance. Today targets are entangled with the discount/margin views.
• Finance is the largest current gap — see Section 13.

Sidebar Navigation

A modern two-tier sidebar: 8 fixed domains (collapsed icons), expanding to role-filtered sub-items. No domain should require more than 2 clicks to any destination.

| Order | Domain | Icon | Default landing |
|---|---|---|---|
| 1 | Executive | 🎯 target / radar | Command Center |
| 2 | Operations | 🔧 wrench / gauge | Workshop Loading |
| 3 | Commercial | 📊 bar-trend | Margin Overview |
| 4 | Finance | 💰 ledger | Margin Bridge |
| 5 | Audit | 🛡️ shield-check | Exception Feed |
| 6 | Performance | 📈 line-up | Targets vs Actual |
| 7 | AI Copilot | ✨ sparkle | Ask bar (always pinned top) |
| 8 | Administration | ⚙️ gear | Users & Roles |

Navigation rules that resolve the duplication noted in the backlog:

• Copilot is pinned as a persistent top bar, not a sidebar item you navigate to. It's an input surface, available everywhere.
• Role filtering hides whole domains. A Workshop Manager's sidebar shows only Operations + Performance + Copilot. They never see Finance or Admin. This is the single biggest usability win.
• No duplicated entry points. Today "Parts Executive" and "Command Center" both behave like executive landing pages. Collapse to one Executive Command Center; Parts becomes a Commercial tab.
• Ordering follows decision altitude (Section 2), so the most senior user's destination is always at top.

Dashboard Hierarchy

Five tiers. Each tier consumes the tier below as drill-down — never redefines its numbers.

| Tier | Dashboard | Primary user | Question answered | Interaction model |
|---|---|---|---|---|
| Executive | Command Center + Exception Feed | MD / CEO | "What needs me?" | Read + drill, never filter-build |
| Manager | Operations Loading · Commercial Margin Overview | Dept managers | "Is my area healthy?" | Filter by location/period |
| Operational | Workshop Loading · Job Card Status · Advisor board | Service Mgr, advisors | "What do I do next?" | Live, action-oriented |
| Analyst | Sales Mix · Margin Bridge · ad-hoc explore | Analysts, FC | "Why did this happen?" | Full slice/dice, pivots |
| Audit | Exception Feed · Leakage Casework · Compliance | Internal Audit | "What's out of policy?" | Case workflow, evidence trail |
| Admin | Platform console | Admin | "Configure & govern" | CRUD, no analytics |

The discipline: the Executive dashboard contains zero unique calculations. Every figure on it is a roll-up of a Manager-tier number, which is a roll-up of an Operational number. This is what makes "one number, one home" enforceable.

Report Rationalization

Mapping every surface visible in the current product. Confidence note: module existence is read from the backlog; the disposition is my product recommendation.

| Current surface | Verdict | Becomes | Why |
|---|---|---|---|
| Command Center (executive) | Keep + elevate | The single Executive landing | It's the right concept; make it the only executive entry |
| Parts Executive | Convert to Tab | Commercial → Parts tab | A "parts executive" page duplicates the executive layer; parts is a commercial domain |
| Discount (commercial) | Split | Commercial → Discount Governance (mgmt) + Audit → Discount Compliance (control) | Two audiences, two jobs: managing discount vs. policing it |
| Labour (commercial) | Keep + Merge | Commercial → Labour + feed Operations throughput | Labour productivity is operational; labour margin is commercial. Split the lens, share the data |
| Sales Mix (commercial) | Keep | Commercial → Analyst-tier | Genuinely analytical; correctly placed, just re-tiered |
| Revenue Leakage | Move | Audit → Leakage Casework | It's a control/exception function, not commercial performance |
| Traffic | Promote | Operations → Throughput (domain spine) | Too important to be a standalone report; it's the operational heartbeat |
| Targets (MPPBTargets) | Split | Admin → Targets Setup + Performance → Targets vs Actual | Defining ≠ tracking |
| expreport / export report | Convert to Widget | Universal export action on every dashboard | Exporting is a capability, not a destination. Don't make users navigate to export |
| Audit views | Keep + expand | Audit domain (Section 8) | Underbuilt today relative to its importance |
| (Implied) standalone margin/growth surfaces | Remove as destinations | Fold into KPI definitions | The scattered margin/growth math = scattered "reports." Centralize |

Net effect: the product goes from a flat list of ~8–10 reports to 8 role-filtered domains, and the number of places a manager must navigate to drops sharply because exports, KPIs, and targets stop being destinations.

Executive Workflow (MD / CEO)

The governing rule: the MD should almost never open a report. Their product is the Command Center + Exception Feed + Copilot.

• Morning (90 seconds): Open Command Center. Read the Exception Feed — a ranked list of only things outside tolerance (margin below target at Location X, discount breach, WIP aging). If the feed is empty, close the app. That's a successful morning.
• Daily (as triggered): Tap one exception → drill straight to the proof (e.g. exception "Discount up 4pts at Branch 3" → Discount Governance pre-filtered to Branch 3, this week). Assign or comment. Close.
• Weekly: Group Scorecard — one screen, all locations, traffic-lighted vs. target. Ask Copilot: "What changed this week and why?" Read the narrative, not the charts.
• Monthly: Margin Bridge (Finance) — what moved profit vs. last month, decomposed. Review Targets vs Actual. One export to the board pack.
• Quarterly: Benchmarking / league tables across locations and (future) OEM benchmarks. Set next-quarter targets via Copilot-assisted draft → Admin.

If the MD ever has to build a filter to find a problem, the product has failed.

Workshop Manager Workflow

Their entire product is Operations + Performance + Copilot. Sidebar hides everything else.

• Start of day: Workshop Loading — bays, technician capacity, booked vs. available hours, today's job cards.
• Through the day: Job Card Status (live) — what's open, stuck, awaiting parts/authorization. Advisor Performance board for the team.
• End of day/week: Throughput vs. target (Performance); productivity and efficiency trends.

What a Workshop Manager should NEVER need to open:

• ❌ Finance (Margin Bridge, debtors, revenue recognition)
• ❌ Audit (leakage casework, compliance) — they are subjects of audit, not operators of it
• ❌ Discount Governance, Sales Mix analytics, Administration
• ❌ The Executive Command Center

They get their slice of throughput and productivity, nothing financial or investigative. This separation is also a controls win (Section 8).

Internal Audit Workflow

Audit today is underbuilt for a commercial platform. The complete journey:

Exception Feed (entry): Auto-generated, ranked anomalies — discount breaches, leakage signals, out-of-policy approvals, unusual write-offs. This is Audit's home screen.
Triage: Each exception becomes a case with status (Open / Investigating / Resolved / Escalated). This case workflow is the missing primitive today.
Investigate (drill-through): From a case, follow the cross-filter chain (Section 9) down to the offending job card / invoice / advisor. Every step is evidence.
Evidence & trail: Attach findings; the platform records who approved the original transaction (segregation-of-duties view).
Resolve & report: Close case with disposition. Recovered-leakage and compliance-rate roll up to the Executive Command Center as KPIs.
Controls dashboard: Standing view of discount-policy adherence, approval compliance, leakage recovered vs. identified.

The shift: from leakage as a report you read to leakage as cases you work and close.

Cross-Filter Architecture

One canonical drill-through spine, used identically everywhere. Any KPI on any dashboard drills along this path:

`
Group (all dealerships)
   ↓
Domain KPI (e.g. Margin, Leakage, Throughput)
   ↓
Location / Branch
   ↓
Department (Service · Parts · Bodyshop)
   ↓
Advisor / Technician
   ↓
Job Card
   ↓
Line item (Labour line · Part · Discount applied)
   ↓
Invoice
   ↓
Source transaction
`

Rules:

• Drill direction is always down this chain — never sideways into an unrelated report. Today, navigating between Discount and Labour means leaving one report and entering another; instead, drilling a margin exception should stay in context and descend the spine.
• Every exception in the Audit feed is a pre-built drill to the exact node (job card / invoice) where the issue lives.
• Breadcrumb is always visible so any user knows their altitude and can ascend.

Universal Dashboard Standard

One template. Every dashboard in every domain uses it — this is what kills layout drift and the scattered-component problem.

`
┌─────────────────────────────────────────────────────┐
│ 1. HEADER     Title · role badge · last-refreshed     │
├─────────────────────────────────────────────────────┤
│ 2. FILTERS    Location · Period · Dept (global,       │
│               persistent, max 4 — same control set     │
│               everywhere)                              │
├─────────────────────────────────────────────────────┤
│ 3. KPI ROW    3–5 cards. Value · vs-target · trend.   │
│               Each card = one owned KPI (Section 11)   │
├─────────────────────────────────────────────────────┤
│ 4. NARRATIVE  1–2 Copilot sentences: "what & why."    │
│               (The executive reads this, not charts)  │
├─────────────────────────────────────────────────────┤
│ 5. CHARTS     Max 2–3. One primary, supporting beside │
├─────────────────────────────────────────────────────┤
│ 6. TABLE      Detail grid, sortable, drill-enabled    │
├─────────────────────────────────────────────────────┤
│ 7. ACTIONS    "Create case" · "Assign" · "Add note"   │
├─────────────────────────────────────────────────────┤
│ 8. EXPORT     PDF / Excel — inline, never a separate  │
│               destination                             │
├─────────────────────────────────────────────────────┤
│ 9. FOOTER     KPI definitions link · data source ·    │
│               drill breadcrumb                         │
└─────────────────────────────────────────────────────┘
``

The Narrative band (4) is the most important addition vs. today — it's how executives consume without reading charts, and it's where the Copilot earns its place on every screen.

KPI Ownership

The principle: every KPI has exactly one home and one definition. The backlog already reveals the problem at the engineering layer (growth %, margin, discount, ratios computed inline in many places) — at the product layer this means the same KPI can show different values on different screens. That is fatal for an executive platform.

The KPI register — each metric, its single owning domain, where it may be referenced:

| KPI | Owning domain (defines it) | Referenced (read-only) on |
|---|---|---|
| Gross Margin % | Finance | Executive, Commercial |
| Margin Bridge (Δ decomposition) | Finance | Executive |
| Revenue (recognized) | Finance | Executive, Commercial |
| Labour Efficiency / Productivity | Operations | Performance, Commercial |
| Throughput / Hours sold | Operations | Executive, Performance |
| Sales Mix % | Commercial | Executive |
| Discount % & breaches | Commercial (mgmt) | Audit references the breach |
| Discount Compliance Rate | Audit | Executive |
| Revenue Leakage (identified/recovered) | Audit | Executive, Finance |
| Targets vs Actual | Performance | Every domain references its own |
| Advisor Performance | Operations | Commercial, Performance |
| WIP / Debtor aging | Finance | Executive |

Duplicate KPIs to consolidate now:

• Growth % — currently computed in multiple surfaces. → One definition, owned by Performance, referenced everywhere.
• Margin / Discount math — scattered across Discount, Labour, Sales Mix surfaces. → Finance owns margin; Commercial owns discount; everyone else references.
• Aggregations (location/monthly summaries) — the backlog shows these recomputed ad-hoc. At product level: define them once as certified metrics; no screen may recompute a certified metric.

Governance: a KPI Definitions page (Admin) is the single source of truth, linked from every dashboard footer. If a number is questioned, there is one place that settles it.

Future Scalability

| Dimension | Design requirement |
|---|---|
| 10 dealerships | Location filter + group roll-up. Today's model handles this. |
| 50 dealerships | Regions/clusters layer between Group and Location. League tables become essential — managers compete. Exception feed must rank across 50 sites or it drowns. |
| 500 dealerships | Exception-only executive model becomes mandatory — no human reads 500 scorecards. Hierarchy: Group → Country → Region → Dealer → Dept. Performance tiering and outlier detection do the watching. |
| Multi-brand | Brand becomes a first-class filter dimension alongside Location. KPI definitions must be brand-normalized (margin expectations differ by brand). |
| Multi-country | Currency, language, tax/policy localization. Targets and compliance rules become country-scoped. Time zones in "morning workflow." |
| OEM benchmarking | New external data spine: compare each dealer to OEM/peer benchmarks. Lives in Performance. A major commercial differentiator vs. internal-only tools. |
| AI Copilot | Already pinned in nav. Scales as: NL query → narrative bands → proactive anomaly push → eventually agentic ("draft the board pack"). Role-scoped: Copilot never answers Finance questions for a Workshop Manager. |
| Mobile app | Executive + Operations only. Exception Feed and Workshop Loading are inherently mobile. Finance/Audit/Analyst stay desktop. Mobile is a role-subset, not a shrunk desktop. |

The architectural enabler for all of this is the single drill spine (Section 9) + certified KPIs (Section 11). Both must be in place before scale, or every new dealership multiplies the inconsistency.

Critical Gaps

What a world-class dealership BI platform has that WSMIS currently lacks:

A Finance domain. The biggest gap. No visible revenue recognition, margin bridge, WIP/debtor aging, or true profitability. Today's "commercial" views show activity, not financial truth.
Exception / alerting engine. Everything today is pull (open a report). World-class is push (the problem finds you). This is the heart of the executive value proposition.
Case/workflow primitive for Audit. Leakage is reported but not worked. No case lifecycle, no evidence trail, no segregation-of-duties view.
Targets-vs-actual as a first-class loop. Targets exist as data (MPPBTargets) but not as a governing performance layer with variance and forecasting.
Narrative / NL layer. No "what changed and why" in words. Executives at this tier consume narrative, not charts.
OEM / external benchmarking. Purely internal today. Peer comparison is a defining feature of the platforms you benchmarked against.
Role-based experience. One product for all users today; needs role-filtered surfaces (the single biggest usability gap).
Forecasting / predictive. Everything is historical. No "where will margin land this month."
Mobile executive experience.
A certified-KPI / definitions governance layer. Without it, scale multiplies inconsistency.

Product Roadmap

| Release | Theme | Contents |
|---|---|---|
| Immediate (v1.0 hardening) | Make numbers trustworthy & navigation role-aware | Certified KPI register + definitions page · single drill spine · collapse duplicate executive surfaces (merge Parts Executive into Commercial) · move Leakage into Audit · exports become inline widgets |
| v1.1 | Push, not pull | Exception Feed + alerting engine · Narrative bands (Copilot v1) · role-filtered sidebars · Targets-vs-Actual as Performance loop |
| v2.0 | Financial truth + scale | Full Finance domain (margin bridge, WIP, recognition) · Audit case workflow · Regions/clusters layer · league tables · multi-brand dimension |
| v3.0 | Intelligence + reach | OEM benchmarking · forecasting/predictive · agentic Copilot (board-pack generation) · mobile app · multi-country |

Final Deliverable — Governing Decisions

The ten rules that this blueprint makes canonical. Any future feature is checked against these:

Decisions over reports. Organize by role and decision, never by report inventory.
One number, one home. Every KPI has exactly one owning domain and definition; all else references.
Push beats pull. The executive's primary surface is an exception feed, not a report list.
Role determines surface. Sidebars are filtered by role; users never see domains they don't operate.
One drill spine. Group → Location → Dept → Advisor → Job Card → Line → Invoice. Always down, never sideways.
One dashboard template. Header → Filters → KPIs → Narrative → Charts → Table → Actions → Export → Footer.
Eight domains. Executive · Operations · Commercial · Finance · Audit · Performance · AI Copilot · Administration.
Exports and KPI definitions are capabilities, not destinations.
Narrative is a first-class output. Every dashboard explains itself in words.
Design for 500 before you have 50. The exception model and certified KPIs are scale prerequisites, not luxuries.

This blueprint is complete and self-governing against your 15-part brief. Two things would sharpen it materially if you can share them: the actual module/report list from the full Architecture Pack (so I can replace my inferred surface in Section 5 with the real inventory), and the current sidebar/navigation doc you referenced (so Section 3 is a redesign of the real thing rather than of an inferred one). If you drop those in, I'll revise Sections 3, 5, and 11 to match the real product exactly — the rest of the architecture holds regardless.