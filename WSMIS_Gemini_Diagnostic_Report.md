# WSMIS Gemini Initialization — Diagnostic Report

## EXECUTIVE SUMMARY

**Root Cause:** `GEMINI_API_KEY` environment variable is not set. No `.env` file exists. No `.streamlit/secrets.toml` file exists. The code resolves to `"offline"` deterministically at `_resolve_provider()` before any model initialization is attempted.

**The offline fallback is NOT a bug.** It is the designed behavior when no API key is detected.

---

## COMPLETE EXECUTION TRACE

### Step 1: Page Load

```
app.py:622          main()
app.py:641          sidebar_navigation()
app.py:671          df, exp_df = load_data(CLIENTS[sel_client])
app.py:699          selected_months, pairs, comparison_mode = render_month_picker(df)
app.py:700          df_filtered, active_filter_count = render_global_filters(df)
app.py:758          render_page_router(...)
```

**Audit Intelligence is NOT in the page router.** The page router in `app.py:569-621` lists 18 pages. `audit_intelligence.py` is not among them. It exists as a standalone page module that is either imported elsewhere or not yet wired in.

### Step 2: Generate Button Click

```
audit_intelligence.py:171    generate_btn = st.button("Generate Audit Intelligence Report")
audit_intelligence.py:174    provider = st.selectbox("AI Provider", AVAILABLE_PROVIDERS, index=0)
                              → AVAILABLE_PROVIDERS = ("auto", "gemini", "anthropic", "offline")
                              → index=0 means default is "auto"
```

### Step 3: Report Generation Entry

```
audit_intelligence.py:185    report = generate_report(
                                  cp=cp, pp=pp,
                                  client_name="Rukmani Motors",
                                  period_label=period_label,
                                  comparison_label=comparison_label,
                                  adv_col=ADV_COL,
                                  provider=provider,      ← "auto"
                              )
```

### Step 4: Provider Resolution (THE DECISION POINT)

```
report_generator.py:248      resolved = _resolve_provider(provider)
                              → provider = "auto"

report_generator.py:42-50    def _resolve_provider(provider: str) -> str:
                                  if provider != "auto":
                                      return provider                    # NOT TAKEN
                                  if (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")) \
                                         and _has_module("google.generativeai"):
                                      return "gemini"                   # ← THIS CONDITION
                                  if os.getenv("ANTHROPIC_API_KEY") and _has_module("anthropic"):
                                      return "anthropic"
                                  return "offline"
```

### Step 5: Environment Variable Check

```
os.getenv("GEMINI_API_KEY")  → None     ← NO ENV VAR SET
os.getenv("GOOGLE_API_KEY")  → None     ← NO ENV VAR SET
```

**Condition evaluation:**
```python
(None or None) and _has_module("google.generativeai")
→ None and True
→ None (falsy)
→ Condition is FALSE
→ "gemini" is NOT selected
```

### Step 6: Anthropic Check (also fails)

```
os.getenv("ANTHROPIC_API_KEY")  → None   ← NO ENV VAR SET
```

### Step 7: Fallback to Offline

```
report_generator.py:50       return "offline"
```

### Step 8: Offline Report Rendering

```
report_generator.py:255      if resolved == "offline":
report_generator.py:256          markdown = _render_offline(context)
                              → Generates deterministic Markdown from context dict
                              → No network call, no LLM, no API key needed
```

### Step 9: Report Object Created

```
report_generator.py:271      return GeneratedReport(
                                  markdown=markdown,
                                  provider="offline",              ← THIS VALUE
                                  model="offline-deterministic",
                                  context=context,
                                  prompt=prompt,
                                  generated_at=datetime.now().isoformat(),
                              )
```

### Step 10: UI Displays Fallback Message

```
audit_intelligence.py:201    if st.session_state.ai_report:
audit_intelligence.py:208        report.provider       → "offline"
audit_intelligence.py:213        if "offline" in report.provider.lower():   ← TRUE
audit_intelligence.py:214            st.info("🔄 AI provider unavailable — showing offline deterministic report.")
```

**This is the message the user sees.**

---

## EVIDENCE INVENTORY

### File: `.env.example`
```
Line 14: # GEMINI_API_KEY=AIza...
```
**Status:** COMMENTED OUT. This is a template, not an active configuration.

### File: `.env`
**Status:** DOES NOT EXIST. Only `.env.example` is present.

### File: `.streamlit/secrets.toml`
**Status:** DOES NOT EXIST. Only `.streamlit/config.toml` exists (theme config only).

### File: `run.bat`
```
streamlit run app.py
```
**Status:** No environment variable injection. No `set GEMINI_API_KEY=...` command.

### File: `config/environment.py`
**Status:** Validates Google Sheets credentials only. Does NOT validate or require `GEMINI_API_KEY`.

### File: `services/ai/gemini_provider.py`
```python
Line 17: key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
Line 19: logger.error("GEMINI_API_KEY / GOOGLE_API_KEY not set. Falling back to offline.")
```
**Status:** This code is NEVER REACHED because `_resolve_provider()` returns "offline" before `_call_gemini()` is invoked.

### File: `services/ai/report_generator.py`
```python
Line 46: if (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")) and _has_module("google.generativeai"):
```
**Status:** The `os.getenv()` calls return `None`, so the entire condition is `False`.

---

## DIAGNOSTIC CHECKLIST

| Check | Result | Evidence |
|---|---|---|
| API key detected? | **NO** | `os.getenv("GEMINI_API_KEY")` → `None` |
| `GOOGLE_API_KEY` fallback? | **NO** | `os.getenv("GOOGLE_API_KEY")` → `None` |
| `ANTHROPIC_API_KEY` fallback? | **NO** | `os.getenv("ANTHROPIC_API_KEY")` → `None` |
| `.env` file exists? | **NO** | Only `.env.example` found |
| `.streamlit/secrets.toml` exists? | **NO** | Only `config.toml` found |
| `google.generativeai` installed? | **YES** | `requirements.txt:15` lists `google-generativeai==0.8.3` |
| Model selected? | **N/A** | Never reaches model selection — resolved to `"offline"` before that |
| Exception swallowed? | **N/A** | No exception occurs — offline is the designed path |
| Fallback intentionally triggered? | **YES** | `_resolve_provider()` returns `"offline"` by design when no key found |

---

## EXACT FILE AND LINE NUMBERS

| Event | File | Line | Code |
|---|---|---|---|
| Provider requested | `audit_intelligence.py` | 174 | `provider = st.selectbox("AI Provider", AVAILABLE_PROVIDERS, index=0)` |
| Provider passed | `audit_intelligence.py` | 192 | `provider=provider,` |
| Resolution entry | `report_generator.py` | 248 | `resolved = _resolve_provider(provider)` |
| Gemini key check | `report_generator.py` | 46 | `if (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))...` |
| Key = None | `report_generator.py` | 46 | `os.getenv("GEMINI_API_KEY")` returns `None` |
| Condition false | `report_generator.py` | 46 | Entire `if` block skipped |
| Offline returned | `report_generator.py` | 50 | `return "offline"` |
| Offline rendered | `report_generator.py` | 256 | `markdown = _render_offline(context)` |
| Provider set | `report_generator.py` | 268 | `used_provider = "offline (fallback)"` |
| Message displayed | `audit_intelligence.py` | 214 | `st.info("🔄 AI provider unavailable — showing offline deterministic report.")` |

---

## ROOT CAUSE

**Single root cause: No `GEMINI_API_KEY` environment variable is set in the runtime environment.**

The application has no mechanism to load this key from:
1. A `.env` file (none exists)
2. `.streamlit/secrets.toml` (none exists)
3. OS environment variable (not set in `run.bat`)
4. Any other configuration source

The `_resolve_provider()` function at `report_generator.py:42-50` is the decision point. It checks `os.getenv("GEMINI_API_KEY")` which returns `None`, causing the condition at line 46 to evaluate to `False`, which causes the function to return `"offline"` at line 50.

The offline renderer at `report_generator.py:89-207` then generates a fully deterministic Markdown report from the context dict. No network call is made. No model is loaded. No API key is needed.

The message "AI provider unavailable — showing offline deterministic report." is **informational, not an error**. It is displayed at `audit_intelligence.py:213-214` whenever the report's provider field contains "offline".

---

## WHAT WOULD NEED TO HAPPEN FOR GEMINI TO WORK

For Gemini to initialise successfully, ALL of these conditions must be true:

1. `GEMINI_API_KEY` or `GOOGLE_API_KEY` environment variable must be set to a valid key
2. `google.generativeai` package must be installed (it is — version 0.8.3)
3. The key must be valid (not expired, not revoked, with billing enabled)
4. The model `gemini-1.5-flash` must be available for the key's project

If any of conditions 1-3 fail, the code falls back to offline. Condition 4 would cause a runtime exception in `gemini_provider.py:39-46` which would be caught and also fall back to offline.

---

## ADDITIONAL FINDING

**The `audit_intelligence.py` page is not wired into the main page router in `app.py`.** The page router at `app.py:569-621` lists 18 pages (Cockpit, Overview, Labour, Parts, Margin, Discounts, Leakage Center, Sales Mix, Advisors, Advisor MoM, Locations, Trends, Targets, Reports, Executive, Expense Analysis, Profit & Loss, Internal Audit, System Health). Audit Intelligence is not among them. This means the page may be inaccessible through normal navigation, even if the Gemini key were set.
