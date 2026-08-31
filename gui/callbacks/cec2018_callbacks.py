"""
CEC2018 page callbacks.

Stores
------
cec-state   (memory) — problem config + running flag
cec-results (memory) — latest pareto front + hv history

Outputs (each has exactly ONE writer)
--------------------------------------
cec-state.data          → handle_cec_select, cec_control
cec-results.data        → cec_progress_update
cec-run-btn.disabled    → cec_control
cec-stop-btn.disabled   → cec_control
cec-interval.disabled   → cec_control
cec-selected-label      → handle_cec_select
cec-pareto-plot.figure  → cec_update_plots
cec-hv-plot.figure      → cec_update_plots
cec-gen-badge.children  → cec_update_metrics
cec-metric-gen.children → cec_update_metrics
cec-metric-hv.children  → cec_update_metrics
cec-metric-pf.children  → cec_update_metrics
cec-metric-t.children   → cec_update_metrics
cec-status-text.children→ cec_update_metrics
"""

import threading
import numpy as np
import plotly.graph_objects as go

from dash import Input, Output, State, callback_context, no_update, ALL, html
import dash_bootstrap_components as dbc

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

        _NAMES = {
            1:"DF1",2:"DF2",3:"DF3",4:"DF4",5:"DF5",6:"DF6",7:"DF7",
            8:"DF8",9:"DF9",10:"DF10",11:"DF11",12:"DF12",13:"DF13",14:"DF14",
        }
        _NOBJ = {i: 2 for i in range(1,10)}
        _NOBJ.update({i: 3 for i in range(10,15)})

        if (current_state or {}).get("running"):
            return no_update, no_update   # don't switch while running

        label = f"{_NAMES[pid]}  ({_NOBJ[pid]}-objective)  — ready to run"
        return pid, label

    # ── 1b. Enable Run button when a problem is selected ─────────────
    # SOLE writer of cec-run-btn.disabled (shared with cec_control below,
    # but cec_control is the authoritative writer during run/stop).
    # We use a separate callback so there's no conflict.
    # NOTE: cec_control is the SOLE writer — this callback is removed;
    # the Run button starts disabled and cec_control enables it after stop.
    # Instead we rely on cec_control reading cec-problem-id.

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
        State("cec-pop-size",   "value"),
        State("cec-max-gen",    "value"),
        State("cec-taut",       "value"),
        State("cec-nt",         "value"),
        State("cec-state",      "data"),
        prevent_initial_call=True,
    )
    def cec_control(run_clicks, stop_clicks, pid,
                    pop_size, max_gen, taut, nt, current_state):
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
                "pop_size":    pop_size or 100,
                "max_gen":     max_gen  or 200,
                "taut":        taut     or 10,
                "nt":          nt       or 10,
                "current_gen": 0,
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
        Output("cec-hv-plot",     "figure"),
        Input("cec-results", "data"),
        State("cec-state",   "data"),
        prevent_initial_call=True,
    )
    def cec_update_plots(results, state):
        if not results:
            return no_update, no_update

        pf  = np.array(results.get("pareto_front", []))
        pop = np.array(results.get("population_objectives", []))
        hv_hist = results.get("hv_history", [])
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

        # ── HV over time plot ──
        hv_fig = go.Figure()
        hv_fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,18,30,0.8)",
            uirevision="cec-hv",
            margin=dict(l=40, r=10, t=20, b=30),
            showlegend=False,
        )
        if hv_hist:
            gens = [h["gen"] for h in hv_hist]
            hvs  = [h["hv"]  for h in hv_hist]
            hv_fig.add_trace(go.Scattergl(
                x=gens, y=hvs,
                mode="lines",
                line=dict(color="#00d4ff", width=2),
                fill="tozeroy",
                fillcolor="rgba(0,212,255,0.08)",
            ))
            hv_fig.update_xaxes(title_text="Generation",
                                 gridcolor="rgba(255,255,255,0.05)")
            hv_fig.update_yaxes(title_text="HV",
                                 gridcolor="rgba(255,255,255,0.05)")

        return pareto_fig, hv_fig

    # ── 5. Metrics update ────────────────────────────────────────────
    @app.callback(
        Output("cec-gen-badge",    "children"),
        Output("cec-metric-gen",   "children"),
        Output("cec-metric-hv",    "children"),
        Output("cec-metric-pf",    "children"),
        Output("cec-metric-t",     "children"),
        Output("cec-status-text",  "children"),
        Input("cec-results", "data"),
        State("cec-state",   "data"),
        prevent_initial_call=True,
    )
    def cec_update_metrics(results, state):
        if not results:
            return no_update, no_update, no_update, no_update, no_update, no_update

        gen    = results.get("generation", 0)
        hv     = results.get("hypervolume", 0.0)
        pf_sz  = results.get("pf_size", 0)
        t_val  = results.get("t_value", 0.0)
        done   = results.get("done", False)

        status = "Completed" if done else f"Running… gen {gen}"
        return (
            f"Gen {gen}",
            str(gen),
            f"{hv:.4f}",
            str(pf_sz),
            f"{t_val:.4f}",
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
        State("cec-taut",         "value"),
        State("cec-nt",           "value"),
        prevent_initial_call=True,
    )
    def do_compare(n_clicks, pid, cec_state, t1, t2, taut, nt):
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
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
            from cec2018_dmop.cec2018_DF import cec2018_DF

            pid_int = int(pid)
            t1      = int(t1)   if t1   is not None else 1
            t2      = int(t2)   if t2   is not None else 2
            taut    = int(taut) if taut is not None else 10
            nt      = int(nt)   if nt   is not None else 10
            n_obj   = 2 if pid_int <= 9 else 3

            def _true_front(t_target):
                T0    = 50
                tau   = T0 + int(taut * (t_target * nt))
                t_val = (1.0 / nt) * np.floor(max(tau + taut - T0 - 1, 0) / taut)
                G     = np.sin(0.5 * np.pi * t_val)
                N     = 400
                pts   = []
                if n_obj == 2:
                    for x0 in np.linspace(0.0, 1.0, N):
                        x = np.array([x0] + [G] * 9)
                        f = cec2018_DF(pid_int, x, tau, taut, nt)
                        pts.append([f[0], f[1]])
                else:
                    ns = int(np.sqrt(N))
                    for x0 in np.linspace(0.0, 1.0, ns):
                        for x1 in np.linspace(0.0, 1.0 - x0, ns):
                            x = np.array([x0, x1] + [G] * 8)
                            f = cec2018_DF(pid_int, x, tau, taut, nt)
                            pts.append([f[0], f[1], f[2]])
                return np.array(pts)

            pf1 = _true_front(t1)
            pf2 = _true_front(t2)

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

    t = threading.Thread(target=_cec_worker, args=(app, state), daemon=True)
    t.start()


def _cec_worker(app, state):
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from cec2018_dmop import CEC2018Problem
        from pymoo.algorithms.moo.nsga2 import NSGA2
        from pymoo.operators.crossover.sbx import SBX
        from pymoo.operators.mutation.pm import PM
        from pymoo.operators.sampling.rnd import FloatRandomSampling
        from pymoo.optimize import minimize
        from pymoo.indicators.hv import HV

        pid     = state["problem_id"]
        pop_sz  = state.get("pop_size",  100)
        max_gen = state.get("max_gen",   200)
        taut    = state.get("taut",       10)
        nt      = state.get("nt",         10)

        problem = CEC2018Problem(problem_id=pid, taut=taut, nt=nt, n_var=10)
        hv_history = []

        algo = NSGA2(
            pop_size=pop_sz,
            sampling=FloatRandomSampling(),
            crossover=SBX(prob=0.9, eta=15),
            mutation=PM(prob=0.1, eta=20),
            eliminate_duplicates=True,
        )

        def callback(a):
            if app._cec_stop_flag:
                a.termination.force_termination = True
                return

            problem.set_tau(a.n_gen)
            pf   = a.opt.get("F")
            popF = a.pop.get("F")
            popX = a.pop.get("X")

            # Compute HV
            hv_val = 0.0
            try:
                ref = np.max(pf, axis=0) + 1.0
                hv_val = float(HV(ref_point=ref)(pf))
            except Exception:
                pass

            # Compute t value
            T0 = 50
            t_val = (1.0 / nt) * np.floor(
                max(a.n_gen + taut - T0 - 1, 0) / taut
            )

            hv_history.append({"gen": a.n_gen, "hv": hv_val})

            app._cec_latest_result = {
                "generation":            a.n_gen,
                "pareto_front":          pf.tolist(),
                "population_objectives": _downsample_list(popF, 200),
                "hypervolume":           hv_val,
                "pf_size":               len(pf),
                "t_value":               float(t_val),
                "hv_history":            hv_history[-200:],  # keep last 200 pts
                "done":                  False,
            }

        minimize(
            problem, algo,
            ("n_gen", max_gen),
            callback=callback,
            verbose=False,
            seed=42,
        )

        # Mark done
        if app._cec_latest_result:
            app._cec_latest_result["done"] = True

    except Exception as e:
        print(f"CEC worker error: {e}")
    finally:
        app._cec_running = False


def _downsample(arr: np.ndarray, n: int) -> np.ndarray:
    """Return at most n rows, evenly sampled."""
    if len(arr) <= n:
        return arr
    idx = np.linspace(0, len(arr) - 1, n, dtype=int)
    return arr[idx]


def _downsample_list(arr: np.ndarray, n: int) -> list:
    return _downsample(arr, n).tolist()
