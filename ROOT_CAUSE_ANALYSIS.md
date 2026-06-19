# Root Cause Analysis: Plotly Duplicate `title` Keyword Argument Error

## Error

```
TypeError: plotly.graph_objs._figure.Figure.update_layout() got multiple values for keyword argument 'title'
```

**Traceback:**
```
File "/mount/src/wsmis/services/error_handler.py", line 55, in safe_render
    render_func(*args, **kwargs)
File "/mount/src/wsmis/views/labour.py", line 730, in render
    _render_charts(data, pairs, mode_str)
File "/mount/src/wsmis/views/labour.py", line 396, in _render_charts
    fig_trend.update_layout(**PLY, barmode="group", height=300,
```

---

## Root Cause

The original `PLY` dict in `utils/constants.py` contained a `title` key:

```python
PLY = dict(
    template="simple_white",
    font=dict(family="Inter, -apple-system, sans-serif", color="#1D1D1F", size=12),
    paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
    xaxis=dict(gridcolor="#F0F0F5", linecolor="#E5E5EA", tickfont=dict(size=11)),
    yaxis=dict(gridcolor="#F0F0F5", linecolor="#E5E5EA", tickfont=dict(size=11)),
    margin=dict(l=48, r=24, t=52, b=40),
    hoverlabel=dict(bgcolor="#FFFFFF", font_size=13, font_family="Inter", bordercolor="#E5E5EA"),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#E5E5EA", borderwidth=1,
                font=dict(size=11), orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1),
    title=dict(font=dict(size=14, color="#1D1D1F", family="Inter"), x=0.01, xanchor="left", pad=dict(t=4)),  # <-- THIS
)
```

Every `update_layout` call in `labour.py` used this pattern:

```python
fig_trend.update_layout(**PLY, barmode="group", height=300,
    title=dict(text=f"Revenue Trend — {mode_str}", **PLY["title"]),
    yaxis=dict(**PLY["yaxis"], title="Revenue (₹)"),
    ...)
```

When Python evaluates this:

1. `**PLY` expands **all** keys from PLY — **including `title`** (a dict of styling properties)
2. The explicit `title=dict(text=..., **PLY["title"])` provides a **second** `title` keyword argument
3. Python sees two values for the same keyword argument and raises `TypeError`

This affected **7 call sites** in `labour.py`:

| Line (original) | Chart |
|---|---|
| 396 | Revenue Trend |
| ~435 | Location Growth Heatmap |
| ~469 | Service Type Mix |
| ~509 | Location Bridge (waterfall) |
| ~542 | Service Type Bridge (waterfall) |
| ~585 | Drill-Down: Location Service Breakdown |
| ~603 | Drill-Down: Service by Location |

---

## Fix (Already Applied)

Two commits fixed the issue:

### Commit `e1865e3` — Remove `title` from PLY

- Removed `title` from the `PLY` dict in `utils/constants.py`
- Created a separate `PLY_TITLE` constant for title styling
- Updated `labour.py` to use `PLY_TITLE` instead of `PLY["title"]`

### Commit `c78b6d6` — Create `get_ply_layout()` helper

- Created `get_ply_layout(**kwargs)` in `utils/constants.py` as a safe wrapper
- The helper copies PLY, removes any conflicting keys, then merges in kwargs
- Updated all 7 `update_layout` calls in `labour.py` to use `**get_ply_layout(...)` instead of `**PLY`

**Current `utils/constants.py`:**

```python
PLY = dict(
    template="simple_white",
    font=dict(family="Inter, -apple-system, sans-serif", color="#1D1D1F", size=12),
    paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
    xaxis=dict(gridcolor="#F0F0F5", linecolor="#E5E5EA", tickfont=dict(size=11)),
    yaxis=dict(gridcolor="#F0F0F5", linecolor="#E5E5EA", tickfont=dict(size=11)),
    margin=dict(l=48, r=24, t=52, b=40),
    hoverlabel=dict(bgcolor="#FFFFFF", font_size=13, font_family="Inter", bordercolor="#E5E5EA"),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#E5E5EA", borderwidth=1,
                font=dict(size=11), orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1),
)  # No title key

PLY_TITLE = dict(font=dict(size=14, color="#1D1D1F", family="Inter"), x=0.01, xanchor="left", pad=dict(t=4))

def get_ply_layout(**kwargs):
    layout_cfg = dict(PLY)
    layout_cfg.pop("title", None)
    layout_cfg.pop("title_text", None)
    layout_cfg.update(kwargs)
    return layout_cfg
```

**Current `labour.py` pattern:**

```python
fig_trend.update_layout(**get_ply_layout(
    barmode="group", height=300,
    title=dict(text=f"Revenue Trend — {mode_str}", **PLY_TITLE),
    yaxis=dict(**PLY["yaxis"], title="Revenue (₹)"),
    yaxis2=dict(title="Growth %", overlaying="y", side="right",
        tickformat=".1f", showgrid=False)
))
```

---

## Verification

All 7 chart `update_layout` patterns were tested in isolation and **all succeed without error**:

```
SUCCESS: fig_trend.update_layout rendered without error
SUCCESS: fig_heat.update_layout rendered without error
SUCCESS: fig_svc.update_layout rendered without error
SUCCESS: fig_wf_loc.update_layout rendered without error
SUCCESS: fig_wf_svc.update_layout rendered without error
SUCCESS: fig_drill_loc.update_layout rendered without error
SUCCESS: fig_drill_svc.update_layout rendered without error
```

---

## Why the Error May Still Appear in Deployment

The traceback provided shows **old code** (`**PLY` at line 396) while the current codebase has `**get_ply_layout(` at that line. Both fix commits are already pushed to the remote (`origin/feature/parts-dashboard-v2`).

If the error persists, the **Streamlit deployment** (Docker container or cloud service at `/mount/src/wsmis/`) is running a stale version. The deployment must be **rebuilt and restarted** to pick up the committed changes.

---

## Files Modified

| File | Change |
|---|---|
| `utils/constants.py` | Removed `title` from `PLY`, added `PLY_TITLE`, added `get_ply_layout()` |
| `views/labour.py` | All 7 `update_layout` calls changed from `**PLY` to `**get_ply_layout(...)` |

---

## Other Files Using `**PLY`

These files still use `**PLY` directly but **do not pass `title=` alongside it**, so they are not affected:

| File | Line | Call |
|---|---|---|
| `views/advisor.py` | 185 | `fig.update_layout(**PLY, height=300, xaxis_title="", yaxis_title="Amount (₹)")` |
| `views/locations.py` | 195, 202, 209 | `fig.update_layout(**PLY, height=250, xaxis_title="", yaxis_title="...", showlegend=False)` |
| `views/yoy.py` | 204, 222 | `fig.update_layout(**PLY); fig.update_layout(height=320, ...)` |
