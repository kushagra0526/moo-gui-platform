"""
Main Dash application.
Login form always in DOM. Router toggles a single 'authenticated' class.
"""
import dash
from dash import dcc, html, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import os

from .layouts import create_main_layout
from .layouts.login_layout import build_login_card
from .callbacks import register_callbacks
from .callbacks.auth_callbacks import register_auth_callbacks
from .core.state_manager import StateManager
from .core.optimization_engine import OptimizationEngine


def create_app():
    current_dir  = os.path.dirname(os.path.abspath(__file__))
    assets_path  = os.path.join(os.path.dirname(current_dir), 'assets')

    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.icons.FONT_AWESOME],
        suppress_callback_exceptions=True,
        title="Multi-Objective Optimization Platform",
        assets_folder=assets_path,
    )

    app.state_manager       = StateManager()
    app.optimization_engine = OptimizationEngine()

    app.layout = html.Div([
        dcc.Location(id="url", refresh=False),

        dcc.Store(id="auth-state",           storage_type="session"),
        dcc.Store(id="app-state",            storage_type="session"),
        dcc.Store(id="optimization-results", storage_type="session"),
        dcc.Store(id="opt-control-store",    storage_type="session",
                  data={"cmd": "idle"}),
        dcc.Store(id="algo-config",          storage_type="session"),
        dcc.Interval(id="optimization-interval", interval=2000, disabled=True),

        # Login — always in DOM
        html.Div(build_login_card(), id="login-page-wrapper"),

        # App shell — rendered by router
        html.Div(id="app-shell"),
    ])

    @app.callback(
        Output("login-page-wrapper", "style"),
        Output("app-shell",          "children"),
        Input("auth-state", "data"),
        Input("url",        "pathname"),
        State("app-state",  "data"),
    )
    def router(auth_state, pathname, app_state):
        if isinstance(auth_state, str):
            try:
                import json as _j; auth_state = _j.loads(auth_state)
            except Exception:
                auth_state = None

        authenticated = bool(
            isinstance(auth_state, dict) and auth_state.get("authenticated") is True
        )

        HIDE = {"display": "none"}
        SHOW = {"display": "block"}

        if pathname == "/logout":
            return SHOW, None

        if not authenticated:
            return SHOW, None

        user_data = auth_state.get("user", {}) if isinstance(auth_state, dict) else {}
        valid_paths = ("/dashboard", "/problem", "/algorithm", "/visualization", "/results", "/cec2018")
        safe = pathname if pathname in valid_paths else "/dashboard"

        return HIDE, create_main_layout(
            user_data=user_data,
            pathname=safe,
            engine_running=app.optimization_engine.is_running,
            saved_state=app_state or {},
        )
    register_auth_callbacks(app)
    register_callbacks(app)

    # ── Theme toggle — clientside, no server round-trip ───────────────
    app.clientside_callback(
        """
        function(n_clicks) {
            var body = document.body;
            var isLight = body.classList.contains('light-mode');
            if (isLight) {
                body.classList.remove('light-mode');
                localStorage.setItem('moo-theme', 'dark');
                return 'fas fa-moon';
            } else {
                body.classList.add('light-mode');
                localStorage.setItem('moo-theme', 'light');
                return 'fas fa-sun';
            }
        }
        """,
        Output("theme-icon", "className"),
        Input("btn-theme-toggle", "n_clicks"),
        prevent_initial_call=True,
    )

    # ── Restore saved theme on page load ─────────────────────────────
    app.clientside_callback(
        """
        function(pathname) {
            var saved = localStorage.getItem('moo-theme') || 'dark';
            if (saved === 'light') {
                document.body.classList.add('light-mode');
                return 'fas fa-sun';
            } else {
                document.body.classList.remove('light-mode');
                return 'fas fa-moon';
            }
        }
        """,
        Output("theme-icon", "className", allow_duplicate=True),
        Input("url", "pathname"),
        prevent_initial_call='initial_duplicate',
    )

    return app
