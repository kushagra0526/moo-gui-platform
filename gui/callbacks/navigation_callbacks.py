"""
Navigation callbacks — status bar and progress only.
Quick-action navigation is handled via dcc.Link href (no callback needed).
url.pathname has a single writer in auth_callbacks.py.
"""

from dash import Input, Output, State, callback_context, no_update


def register_navigation_callbacks(app):

    # ------------------------------------------------------------------
    # Reset stale optimization_running flag on every page navigation
    # This prevents stale localStorage from keeping Run button disabled
    # ------------------------------------------------------------------
    @app.callback(
        Output("app-state",             "data", allow_duplicate=True),
        Output("optimization-interval", "disabled", allow_duplicate=True),
        Output("btn-run-optimization",  "disabled", allow_duplicate=True),
        Output("btn-stop-optimization", "disabled", allow_duplicate=True),
        Input("url", "pathname"),
        State("app-state", "data"),
        prevent_initial_call=True,
    )
    def reset_running_flag_on_nav(pathname, app_state):
        """Clear stale optimization_running on navigation so Run button is always enabled."""
        if app.optimization_engine.is_running:
            # Engine actually running — don't touch anything
            return no_update, no_update, no_update, no_update
        if pathname in ("/logout", "/login", "/"):
            return {}, True, False, True
        # Engine not running — clear any stale running flags and re-enable Run
        if app_state and app_state.get("optimization_running"):
            state = app_state.copy()
            state["optimization_running"] = False
            return state, True, False, True
        # Interval may be enabled from stale state — disable it
        return no_update, True, False, True

    # ------------------------------------------------------------------
    # status-text.children — SOLE writer
    # Merges: optimization status + save experiment feedback
    # ------------------------------------------------------------------
    @app.callback(
        Output("status-text", "children"),
        Input("app-state",                    "data"),
        Input("btn-save-experiment-results",  "n_clicks"),
        Input("quick-action-export",          "n_clicks"),
        State("experiment-name",              "value"),
        State("optimization-results",         "data"),
        prevent_initial_call=True,
    )
    def update_status(app_state, save_clicks, export_clicks,
                      experiment_name, results_data):
        ctx = callback_context
        if not ctx.triggered:
            return no_update

        trigger = ctx.triggered[0]["prop_id"].split(".")[0]

        if trigger in ("btn-save-experiment-results", "quick-action-export"):
            if not experiment_name:
                return "Please enter an experiment name"
            if not results_data:
                return "No results to save"
            return f"Experiment '{experiment_name}' saved successfully"

        # Default: reflect optimization state
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
            mx  = app_state.get("max_generations", 1)
            return min(100, (cur / mx) * 100)
        return 100 if app_state.get("optimization_completed") else 0
