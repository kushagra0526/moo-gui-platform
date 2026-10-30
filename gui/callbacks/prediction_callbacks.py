"""
Dynamic Prediction page callbacks.

Random restart, ISVM-SMOTE and ISVM-LoRAS run one after another on the same problem and seed, through
dmoea.run like the benchmark. pred_control is the only writer of the page's outputs: Run, Stop, polling
and coming back to the page all go through it, so a comparison keeps showing after navigating away.
"""

import threading
import time

import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback_context, html, no_update

from dmoea import run

STRATEGIES = [("random",     "Random restart",     "#9ca3af"),
              ("isvm-smote", "ISVM-SMOTE (paper)", "#3b82f6"),
              ("isvm-loras", "ISVM-LoRAS",         "#ef4444")]
_LABEL = {key: label for key, label, _ in STRATEGIES}


def register_prediction_callbacks(app):

    @app.callback(
        Output("pred-igd-plot",  "figure"),
        Output("pred-table",     "children"),
        Output("pred-status",    "children"),
        Output("pred-interval",  "disabled"),
        Output("pred-run-btn",   "disabled"),
        Output("pred-stop-btn",  "disabled"),
        Input("pred-run-btn",    "n_clicks"),
        Input("pred-stop-btn",   "n_clicks"),
        Input("pred-interval",   "n_intervals"),
        State("pred-problem",    "value"),
        State("pred-changes",    "value"),
        State("pred-taut",       "value"),
        State("pred-nt",         "value"),
    )
    def pred_control(_run, _stop, _tick, problem, changes, taut, nt):
        trigger = callback_context.triggered_id
        progress = getattr(app, "_pred", None)
        if trigger == "pred-run-btn":
            progress = app._pred = new_progress({
                "problem": _clamp(problem, 5, 1, 14), "changes": _clamp(changes, 10, 1, 30),
                "taut": _clamp(taut, 10, 1, 50), "nt": _clamp(nt, 10, 1, 20),
            })
            threading.Thread(target=compare, args=(app, progress), daemon=True).start()
        elif trigger == "pred-stop-btn" and progress:
            progress["stop"] = True
        if progress is None:  # nothing run yet since the server started
            return no_update, no_update, no_update, True, False, True
        busy = progress["running"] and not progress["stop"]
        return (*render(progress), not busy, busy, not busy)


def new_progress(settings):
    return {"settings": settings, "curves": {}, "summary": {}, "current": None, "env": 0,
            "running": True, "stop": False, "error": None}


def compare(app, progress):
    """Run the three strategies in order, writing into `progress`. Stops when Stop is pressed or a
    newer comparison replaces this one."""
    # shortcut: one comparison at a time for the whole server, like the CEC2018 page; per-user runs need a job store
    s = progress["settings"]
    try:
        for key, _, _ in STRATEGIES:
            progress["current"], progress["env"] = key, 0

            def report(info):
                progress["curves"][key] = list(info["igd"])
                progress["env"] = info["env"]
                return progress["stop"] or app._pred is not progress

            start = time.time()
            strategy, _, oversampling = key.partition("-")
            r = run(s["problem"], nt=s["nt"], taut=s["taut"], n_changes=s["changes"], strategy=strategy,
                    oversampling=oversampling or "loras", pop_size=s.get("pop_size"), seed=42,
                    on_environment=report)
            if progress["stop"] or app._pred is not progress:
                return
            progress["summary"][key] = {"migd": r["migd"], "mhv": r["mhv"], "seconds": time.time() - start}
    except Exception as e:
        progress["error"] = str(e)
    finally:
        progress["running"] = False


def render(progress):
    """(IGD figure, summary table, status line) for a comparison in any state."""
    s, summary = progress["settings"], progress["summary"]

    fig = go.Figure()
    for key, label, color in STRATEGIES:
        y = progress["curves"].get(key)
        if y:
            fig.add_trace(go.Scatter(x=list(range(len(y))), y=y, name=label, mode="lines+markers",
                                     line=dict(color=color, width=2), marker=dict(size=5)))
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,18,30,0.8)",
                      uirevision="pred-igd", margin=dict(l=50, r=20, t=30, b=40),
                      title=f"DF{s['problem']}, (nt, taut) = ({s['nt']}, {s['taut']})",
                      legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.2))
    fig.update_xaxes(title_text="Environment", gridcolor="rgba(255,255,255,0.05)")
    fig.update_yaxes(title_text="IGD (log scale)", type="log", gridcolor="rgba(255,255,255,0.05)")

    base = summary.get("random", {}).get("migd")
    rows = []
    for key, label, color in STRATEGIES:
        r = summary.get(key)
        if r:
            gain = f"{(1 - r['migd'] / base) * 100:.1f}%" if base and key != "random" else "—"
            cells = [f"{r['migd']:.4f}", f"{r['mhv']:.4f}", gain, f"{r['seconds']:.0f} s"]
        elif progress["running"] and progress["current"] == key and not progress["stop"]:
            cells = [f"env {progress['env']}/{s['changes']}", "", "", ""]
        else:
            cells = ["—"] * 4
        rows.append(html.Tr([html.Td(label, style={"color": color, "fontWeight": "600"})]
                            + [html.Td(c) for c in cells]))
    table = dbc.Table([html.Thead(html.Tr([html.Th(h) for h in ("Strategy", "MIGD", "MHV", "vs random", "Time")])),
                       html.Tbody(rows)], color="dark", size="sm", hover=True, className="mb-0")

    if progress["error"]:
        status = html.Span(f"Error: {progress['error']}", style={"color": "#f87171"})
    elif progress["stop"]:
        status = "Stopped."
    elif progress["running"]:
        status = f"Running {_LABEL[progress['current']]}… environment {progress['env']}/{s['changes']}"
    else:
        status = html.Span("Done. Same seed for all three, so the difference comes from the change response.",
                           style={"color": "#4ade80"})
    return fig, table, status


def _clamp(value, default, lo, hi):
    try:
        return min(max(int(value), lo), hi)
    except (TypeError, ValueError):
        return default
