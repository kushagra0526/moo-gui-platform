"""
CEC2018 page callbacks.

Stores
------
cec-state   (memory) — problem config + running flag
cec-results (memory) — latest pareto front + IGD per environment

Outputs (each has exactly ONE writer)
--------------------------------------
cec-state.data          → handle_cec_select, cec_control
cec-results.data        → cec_progress_update
cec-run-btn.disabled    → cec_control
cec-stop-btn.disabled   → cec_control
cec-interval.disabled   → cec_control
cec-selected-label      → handle_cec_select
cec-pareto-plot.figure  → cec_update_plots
cec-igd-plot.figure     → cec_update_plots
cec-gen-badge.children  → cec_update_metrics
cec-metric-env/igd/migd/mhv/t.children → cec_update_metrics
cec-status-text.children→ cec_update_metrics

Runs go through dmoea.run, the same loop the benchmark uses, so the page and the experiments match.
"""

import threading
import numpy as np
import plotly.graph_objects as go

from dash import Input, Output, State, callback_context, no_update, ALL, html

from cec2018_dmop import N_OBJ, true_front
from dmoea import run

# Max population points to render (downsampling for performance)
_MAX_POP_RENDER = 200
_MAX_PF_RENDER  = 300


def register_cec2018_callbacks(app):

    # ── 1. Problem selection ─────────────────────────────────────────
    @app.callback(
        Output("cec-problem-id",     "data"),
        Output("cec-selected-label", "children"),
        Input({"type": "cec-select-btn", "index": ALL}, "n_clicks"),
        State("cec-state", "data"),
        prevent_initial_call=True,
    )
    def handle_cec_select(n_clicks_list, current_state):
        ctx = callback_context
        if not ctx.triggered or not any(n for n in n_clicks_list if n):
            return no_update, no_update

        triggered = ctx.triggered[0]["prop_id"]
        import json as _j
        pid = _j.loads(triggered.split(".")[0])["index"]

        if (current_state or {}).get("running"):
            return no_update, no_update   # don't switch while running

        label = f"DF{pid}  ({N_OBJ[pid]}-objective)  — ready to run"
        return pid, label

    # ── 2. Run / Stop control — SOLE writer of cec-run-btn.disabled,
    #       cec-stop-btn.disabled, cec-interval.disabled, cec-state ──
    @app.callback(
        Output("cec-run-btn",      "disabled"),
        Output("cec-stop-btn",     "disabled"),
        Output("cec-interval",     "disabled"),
        Output("cec-state",        "data"),
        Input("cec-run-btn",    "n_clicks"),
        Input("cec-stop-btn",   "n_clicks"),
        Input("cec-problem-id", "data"),
        State("cec-strategy",   "value"),
        State("cec-pop-size",   "value"),
        State("cec-changes",    "value"),
        State("cec-taut",       "value"),
        State("cec-nt",         "value"),
        State("cec-state",      "data"),
        prevent_initial_call=True,
    )
    def cec_control(run_clicks, stop_clicks, pid,
                    strategy, pop_size, changes, taut, nt, current_state):
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update

        trigger = ctx.triggered[0]["prop_id"].split(".")[0]

        # Problem selected → enable Run, keep Stop disabled
        if trigger == "cec-problem-id":
            if pid and not (current_state or {}).get("running"):
                return False, True, True, no_update
            return no_update, no_update, no_update, no_update

        if trigger == "cec-run-btn":
            if not pid:
                return no_update, no_update, no_update, no_update
            state = {
                "problem_id":  pid,
                "running":     True,
                "strategy":    strategy or "isvm-loras",
                "pop_size":    int(pop_size or 100),
                "changes":     int(changes or 30),
                "taut":        int(taut or 10),
                "nt":          int(nt or 10),
            }
            _launch_cec_thread(app, state)
            return True, False, False, state

        if trigger == "cec-stop-btn":
            app._cec_stop_flag = True
            state = {"running": False, "problem_id": pid}
            return False, True, True, state

        return no_update, no_update, no_update, no_update

    # ── 3. Progress polling ──────────────────────────────────────────
    @app.callback(
        Output("cec-results",  "data"),
        Output("cec-interval", "disabled", allow_duplicate=True),
        Output("cec-run-btn",  "disabled", allow_duplicate=True),
        Output("cec-stop-btn", "disabled", allow_duplicate=True),
        Input("cec-interval", "n_intervals"),
        State("cec-state",    "data"),
        State("cec-live-toggle", "value"),
        prevent_initial_call=True,
    )
    def cec_progress_update(n_intervals, state, live):
        no_change = (no_update, no_update, no_update, no_update)

        if not state or not state.get("running"):
            return no_change

        result = getattr(app, "_cec_latest_result", None)
        if result is None:
            return no_change

        # Optimization finished — push final result, stop interval, re-enable Run
        if not getattr(app, "_cec_running", False):
            final = dict(result)
            final["done"] = True
            return final, True, False, True

        # Still running — respect live toggle
        if not live:
            return no_change

        # Add a unique tick key so Dash sees a change every interval
        result = dict(result)
        result["_tick"] = n_intervals
        return result, no_update, no_update, no_update

    # ── 4. Plot update ───────────────────────────────────────────────
    @app.callback(
        Output("cec-pareto-plot", "figure"),
        Output("cec-igd-plot",    "figure"),
        Input("cec-results", "data"),
        State("cec-state",   "data"),
        prevent_initial_call=True,
    )
    def cec_update_plots(results, state):
        if not results:
            return no_update, no_update

        pf  = np.array(results.get("pareto_front", []))
        pop = np.array(results.get("population_objectives", []))
        igd_hist = results.get("igd_history", [])
        pid = (state or {}).get("problem_id", 1)
        n_obj = pf.shape[1] if len(pf) > 0 else 2

        # ── Pareto front plot ──
        pareto_fig = go.Figure()
        pareto_fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,18,30,0.8)",
            uirevision="cec-pareto",   # keeps zoom/pan on update
            margin=dict(l=40, r=20, t=30, b=40),
            showlegend=True,
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )

        if len(pf) > 0:
            if n_obj == 2:
                # Downsample population
                pop_ds = _downsample(pop, _MAX_POP_RENDER)
                pf_ds  = _downsample(pf,  _MAX_PF_RENDER)

                if len(pop_ds) > 0:
                    pareto_fig.add_trace(go.Scattergl(
                        x=pop_ds[:, 0], y=pop_ds[:, 1],
                        mode="markers",
                        name="Population",
                        marker=dict(color="rgba(100,160,255,0.4)", size=5),
                        hoverinfo="skip",
                    ))
                pareto_fig.add_trace(go.Scattergl(
                    x=pf_ds[:, 0], y=pf_ds[:, 1],
                    mode="markers",
                    name="Pareto Front",
                    marker=dict(
                        color=pf_ds[:, 0],
                        colorscale="Plasma",
                        size=8, symbol="diamond",
                        showscale=False,
                    ),
                    hovertemplate="f1: %{x:.4f}<br>f2: %{y:.4f}<extra></extra>",
                ))
                pareto_fig.update_xaxes(title_text="f1", gridcolor="rgba(255,255,255,0.05)")
                pareto_fig.update_yaxes(title_text="f2", gridcolor="rgba(255,255,255,0.05)")

            else:  # 3-obj
                pf_ds = _downsample(pf, _MAX_PF_RENDER)
                pareto_fig.add_trace(go.Scatter3d(
                    x=pf_ds[:, 0], y=pf_ds[:, 1], z=pf_ds[:, 2],
                    mode="markers",
                    name="Pareto Front",
                    marker=dict(
                        color=pf_ds[:, 0],
                        colorscale="Plasma",
                        size=4,
                    ),
                ))
                pareto_fig.update_layout(
                    scene=dict(
                        xaxis_title="f1", yaxis_title="f2", zaxis_title="f3",
                        bgcolor="rgba(15,18,30,0.8)",
                    )
                )

        pareto_fig.update_layout(title=f"DF{pid} — Pareto Front")

        # ── IGD per environment (log scale, like the paper's Fig. 4) ──
        igd_fig = go.Figure()
        igd_fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,18,30,0.8)",
            uirevision="cec-igd",
            margin=dict(l=40, r=10, t=20, b=30),
            showlegend=False,
        )
        if igd_hist:
            igd_fig.add_trace(go.Scatter(
                x=list(range(len(igd_hist))), y=igd_hist,
                mode="lines+markers",
                line=dict(color="#00d4ff", width=2),
            ))
            igd_fig.update_xaxes(title_text="Environment", gridcolor="rgba(255,255,255,0.05)")
            igd_fig.update_yaxes(title_text="IGD", type="log", gridcolor="rgba(255,255,255,0.05)")

        return pareto_fig, igd_fig

    # ── 5. Metrics update ────────────────────────────────────────────
    @app.callback(
        Output("cec-gen-badge",    "children"),
        Output("cec-metric-env",   "children"),
        Output("cec-metric-igd",   "children"),
        Output("cec-metric-migd",  "children"),
        Output("cec-metric-mhv",   "children"),
        Output("cec-metric-t",     "children"),
        Output("cec-status-text",  "children"),
        Input("cec-results", "data"),
        State("cec-state",   "data"),
        prevent_initial_call=True,
    )
    def cec_update_metrics(results, state):
        if not results:
            return (no_update,) * 7

        env, total = results["environment"], results["n_changes"]
        fmt = lambda v: "—" if v is None else f"{v:.4f}"  # MIGD/MHV need at least one change
        status = "Completed" if results.get("done") else f"Running… environment {env}/{total}"
        return (
            f"Env {env}",
            f"{env}/{total}",
            fmt(results["igd"]),
            fmt(results["migd"]),
            fmt(results["mhv"]),
            f"{results['t_value']:.4f}",
            status,
        )


    # ── 7. Toggle overlay / side-by-side view ────────────────────────
    @app.callback(
        Output("cec-compare-overlay-div", "style"),
        Output("cec-compare-side-div",    "style"),
        Input("cec-compare-view", "value"),
    )
    def toggle_compare_view(view):
        if view == "side":
            return {"display": "none"}, {"display": "block"}
        return {"display": "block"}, {"display": "none"}

    # ── 8. Compare — single callback, no thread, no interval ─────────
    @app.callback(
        Output("cec-compare-plot",    "figure"),
        Output("cec-compare-plot-t1", "figure"),
        Output("cec-compare-plot-t2", "figure"),
        Output("cec-compare-status",  "children"),
        Input("cec-compare-btn",  "n_clicks"),
        State("cec-problem-id",   "data"),
        State("cec-state",        "data"),
        State("cec-t1-select",    "value"),
        State("cec-t2-select",    "value"),
        prevent_initial_call=True,
    )
    def do_compare(n_clicks, pid, cec_state, t1, t2):
        from ..layouts.cec2018_layout import _empty_compare_fig
        empty = _empty_compare_fig()

        if not n_clicks:
            return no_update, no_update, no_update, no_update

        # pid may be None if store not yet written — fall back to cec-state
        if not pid and cec_state:
            pid = cec_state.get("problem_id")

        if not pid:
            return (empty, empty, empty,
                    html.Span("⚠ Select a problem first (click a DF card above).",
                              style={"color": "#f87171"}))

        try:
            pid_int = int(pid)
            t1      = int(t1)   if t1   is not None else 1
            t2      = int(t2)   if t2   is not None else 2
            n_obj   = N_OBJ[pid_int]

            pf1 = true_front(pid_int, t1)
            pf2 = true_front(pid_int, t2)

            overlay = _build_overlay_fig(pf1, pf2, t1, t2, pid_int, n_obj)
            fig_t1  = _build_single_fig(pf1, t1, pid_int, n_obj, "#3b82f6")
            fig_t2  = _build_single_fig(pf2, t2, pid_int, n_obj, "#ef4444")
            status  = html.Span(
                f"DF{pid_int} — t={t1} (blue) vs t={t2} (red)  ✓",
                style={"color": "#4ade80", "fontWeight": "600"},
            )
            return overlay, fig_t1, fig_t2, status

        except Exception as e:
            import traceback; traceback.print_exc()
            return (empty, empty, empty,
                    html.Span(f"Error: {e}", style={"color": "#f87171"}))


# ── Comparison plot builders ─────────────────────────────────────────

def _build_overlay_fig(pf1, pf2, t1, t2, pid, n_obj):
    fig = go.Figure()
    fig.update_layout(
        title=f"DF{pid} — True Pareto Front: t={t1} vs t={t2}",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,18,30,0.8)",
        uirevision="cec-compare-overlay",
        margin=dict(l=40, r=20, t=40, b=40),
        showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=13)),
    )

    if n_obj == 2:
        if len(pf1) > 0:
            fig.add_trace(go.Scattergl(
                x=pf1[:, 0], y=pf1[:, 1],
                mode="lines+markers",
                name=f"t = {t1}",
                line=dict(color="#3b82f6", width=2),
                marker=dict(color="#3b82f6", size=4),
                hovertemplate=f"t={t1}  f1: %{{x:.4f}}<br>f2: %{{y:.4f}}<extra></extra>",
            ))
        if len(pf2) > 0:
            fig.add_trace(go.Scattergl(
                x=pf2[:, 0], y=pf2[:, 1],
                mode="lines+markers",
                name=f"t = {t2}",
                line=dict(color="#ef4444", width=2),
                marker=dict(color="#ef4444", size=4),
                hovertemplate=f"t={t2}  f1: %{{x:.4f}}<br>f2: %{{y:.4f}}<extra></extra>",
            ))
        fig.update_xaxes(title_text="f1", gridcolor="rgba(255,255,255,0.05)")
        fig.update_yaxes(title_text="f2", gridcolor="rgba(255,255,255,0.05)")

    else:  # 3-obj
        if len(pf1) > 0:
            ds = _downsample(pf1, _MAX_PF_RENDER)
            fig.add_trace(go.Scatter3d(
                x=ds[:, 0], y=ds[:, 1], z=ds[:, 2],
                mode="markers",
                name=f"t = {t1}",
                marker=dict(color="#3b82f6", size=3, opacity=0.85),
            ))
        if len(pf2) > 0:
            ds = _downsample(pf2, _MAX_PF_RENDER)
            fig.add_trace(go.Scatter3d(
                x=ds[:, 0], y=ds[:, 1], z=ds[:, 2],
                mode="markers",
                name=f"t = {t2}",
                marker=dict(color="#ef4444", size=3, opacity=0.85),
            ))
        fig.update_layout(scene=dict(
            xaxis_title="f1", yaxis_title="f2", zaxis_title="f3",
            bgcolor="rgba(15,18,30,0.8)",
        ))

    return fig


def _build_single_fig(pf, t_val, pid, n_obj, color):
    from ..layouts.cec2018_layout import _empty_compare_fig
    if len(pf) == 0:
        return _empty_compare_fig(f"t={t_val}")

    fig = go.Figure()
    fig.update_layout(
        title=f"DF{pid} — True Pareto Front at t = {t_val}",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,18,30,0.8)",
        uirevision=f"cec-side-{t_val}",
        margin=dict(l=40, r=20, t=40, b=40),
        showlegend=False,
    )
    if n_obj == 2:
        fig.add_trace(go.Scattergl(
            x=pf[:, 0], y=pf[:, 1],
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(color=color, size=4),
            hovertemplate="f1: %{x:.4f}<br>f2: %{y:.4f}<extra></extra>",
        ))
        fig.update_xaxes(title_text="f1", gridcolor="rgba(255,255,255,0.05)")
        fig.update_yaxes(title_text="f2", gridcolor="rgba(255,255,255,0.05)")
    else:
        ds = _downsample(pf, _MAX_PF_RENDER)
        fig.add_trace(go.Scatter3d(
            x=ds[:, 0], y=ds[:, 1], z=ds[:, 2],
            mode="markers",
            marker=dict(color=color, size=3, opacity=0.85),
        ))
        fig.update_layout(scene=dict(
            xaxis_title="f1", yaxis_title="f2", zaxis_title="f3",
            bgcolor="rgba(15,18,30,0.8)",
        ))
    return fig




def _launch_cec_thread(app, state):
    """Start CEC2018 optimization in a daemon thread."""
    app._cec_stop_flag  = False
    app._cec_running    = True
    app._cec_latest_result = None
    app._cec_run_id = run_id = object()

    threading.Thread(target=_cec_worker, args=(app, state, run_id), daemon=True).start()


def _cec_worker(app, state, run_id):
    def report(info):
        if app._cec_run_id is not run_id:  # a newer run replaced this one: stop without writing
            return True
        igds, hvs = info["igd"], info["hv"]
        app._cec_latest_result = {
            "environment":           info["env"],
            "n_changes":             state["changes"],
            "pareto_front":          info["front"].tolist(),
            "population_objectives": _downsample_list(info["population"], _MAX_POP_RENDER),
            "igd":                   igds[-1],
            "migd":                  float(np.mean(igds[1:])) if len(igds) > 1 else None,
            "mhv":                   float(np.mean(hvs[1:])) if len(hvs) > 1 else None,
            "t_value":               float(info["time"]),
            "igd_history":           list(igds),
            "done":                  False,
        }
        return app._cec_stop_flag

    try:
        # "isvm-loras" -> strategy "isvm" with LoRAS oversampling; "none" / "random" need no oversampler
        strategy, _, oversampling = state["strategy"].partition("-")
        run(state["problem_id"], nt=state["nt"], taut=state["taut"], n_changes=state["changes"],
            strategy=strategy, oversampling=oversampling or "loras", pop_size=state["pop_size"],
            seed=42, on_environment=report)
    except Exception as e:
        print(f"CEC worker error: {e}")
    finally:
        if app._cec_run_id is run_id:
            app._cec_running = False


def _downsample(arr: np.ndarray, n: int) -> np.ndarray:
    """Return at most n rows, evenly sampled."""
    if len(arr) <= n:
        return arr
    idx = np.linspace(0, len(arr) - 1, n, dtype=int)
    return arr[idx]


def _downsample_list(arr: np.ndarray, n: int) -> list:
    return _downsample(arr, n).tolist()
