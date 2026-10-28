"""
Main Dash application.
Login form always in DOM. Router shows it or the app shell, based on the signed server session.
"""
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import os
import secrets
from flask import request, session

from .layouts import create_main_layout
from .layouts.login_layout import build_login_card
from .callbacks import register_callbacks
from .callbacks.auth_callbacks import register_auth_callbacks
from .core.optimization_engine import OptimizationEngine

# Callback outputs an anonymous visitor may update: the login form and the router (which checks the session itself)
PUBLIC_OUTPUTS = ("auth-state.", "auth-alert.", "signin-form-div.", "signup-form-div.", "tab-btn-",
                  "login-page-wrapper.", "app-shell.", "url.")


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

    # Signs the session cookie. Random per start (logs everyone out on restart) unless MOO_GUI_SECRET_KEY is set.
    app.server.secret_key = os.environ.get("MOO_GUI_SECRET_KEY") or secrets.token_hex(32)
    app.optimization_engine = OptimizationEngine()

    @app.server.before_request
    def require_login():
        """Answer app callbacks from visitors without a session with 204 (Dash's "no update")."""
        if request.path.endswith("/_dash-update-component") and not session.get("user"):
            outputs = (request.get_json(silent=True) or {}).get("output", "").strip(".").split("...")
            if not all(o.startswith(PUBLIC_OUTPUTS) for o in outputs):
                return "", 204

    app.layout = html.Div([
        dcc.Location(id="url", refresh=False),

        dcc.Store(id="auth-state",           storage_type="session"),
        dcc.Store(id="app-state",            storage_type="session"),
        dcc.Store(id="optimization-results", storage_type="session"),
        dcc.Store(id="opt-control-store",    storage_type="session",
                  data={"cmd": "idle"}),
        dcc.Store(id="algo-config",          storage_type="session"),
        dcc.Interval(id="optimization-interval", interval=2000, disabled=True),
        dcc.Download(id="download"),

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
        State("algo-config", "data"),
    )
    def router(_auth_state, pathname, app_state, algo_config):
        # auth-state is only a trigger; the browser can forge it, the signed session it cannot
        if pathname == "/logout":
            session.pop("user", None)
        user_data = session.get("user")

        HIDE = {"display": "none"}
        SHOW = {"display": "block"}

        if not user_data:
            return SHOW, None

        valid_paths = ("/dashboard", "/problem", "/algorithm", "/visualization", "/results", "/cec2018")
        safe = pathname if pathname in valid_paths else "/dashboard"

        return HIDE, create_main_layout(
            user_data=user_data,
            pathname=safe,
            engine_running=app.optimization_engine.is_running,
            saved_state=app_state or {},
            algo_config=algo_config or {},
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
