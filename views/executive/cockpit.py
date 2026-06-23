from views.executive.command_center import render as cc_render

def render_cockpit(df, pairs, alerts=None, comparison_mode=True, selected_months=None, ctx=None):
    return cc_render(df, pairs, alerts, comparison_mode, selected_months, ctx=ctx)

render = render_cockpit
