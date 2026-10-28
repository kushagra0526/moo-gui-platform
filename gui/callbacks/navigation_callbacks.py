"""
Navigation callbacks — status bar and progress only.
Quick-action navigation is handled via dcc.Link href (no callback needed).
url.pathname has a single writer in auth_callbacks.py.
"""

from dash import Input, Output, State, no_update


def register_navigation_callbacks(app):

    # ------------------------------------------------------------------
    # Reset stale optimization_running flag on every page navigation
    # This prevents stale localStorage from keeping Run button disabled
    # ------------------------------------------------------------------
    # Run/Stop buttons need no reset here: the router re-renders them from engine state on every navigation
    @app.callback(
        Output("app-state",             "data", allow_duplicate=True),
        Output("optimization-interval", "disabled", allow_duplicate=True),
        Input("url", "pathname"),
        State("app-state", "data"),
        prevent_initial_call=True,
    )
    def reset_running_flag_on_nav(pathname, app_state):
        """Clear stale optimization_running on navigation so Run button is always enabled."""
        if app.optimization_engine.is_running:
            # Engine actually running — don't touch anything
            return no_update, no_update
        if pathname in ("/logout", "/login", "/"):
            return {}, True
        # Engine not running — clear any stale running flags
        if app_state and app_state.get("optimization_running"):
            state = app_state.copy()
            state["optimization_running"] = False
            return state, True
        # Interval may be enabled from stale state — disable it
        return no_update, True

    # ------------------------------------------------------------------
    # status-text.children — SOLE writer
    # ------------------------------------------------------------------
    @app.callback(
        Output("status-text", "children"),
        Input("app-state", "data"),
        prevent_initial_call=True,
    )
    def update_status(app_state):
        if not app_state:
            return "Idle — Ready"
        if app_state.get("optimization_running"):
            gen = app_state.get("current_generation", 0)
            return f"Running optimization… Generation {gen}"
        if app_state.get("optimization_completed"):
            return "Optimization completed"
        return "Idle — Ready"

    # ------------------------------------------------------------------
    # progress-bar — sole writer
    # ------------------------------------------------------------------
    @app.callback(
        Output("progress-bar", "value"),
        Input("app-state", "data"),
        prevent_initial_call=True,
    )
    def update_progress(app_state):
        if not app_state:
            return 0
        if app_state.get("optimization_running"):
            cur = app_state.get("current_generation", 0)
            mx  = app_state.get("max_generations") or 250  # engine default when Algorithm page was never opened
            return min(100, (cur / mx) * 100)
        return 100 if app_state.get("optimization_completed") else 0

    # ------------------------------------------------------------------
    # Dashboard stat cards — filled from this session's stores
    # ------------------------------------------------------------------
    @app.callback(
        Output("total-projects",  "children"),
        Output("completed-runs",  "children"),
        Output("active-runs",     "children"),
        Output("total-solutions", "children"),
        Input("app-state",            "data"),
        Input("optimization-results", "data"),
    )
    def update_dashboard_stats(app_state, results_data):
        app_state = app_state or {}
        n_objectives = sum(1 for e in app_state.get("obj_expressions") or [] if e and e.strip())
        n_solutions = ((results_data or {}).get("metrics") or {}).get("n_solutions", 0)
        return (str(n_objectives), str(app_state.get("runs_completed", 0)),
                "1" if app.optimization_engine.is_running else "0", str(n_solutions))
