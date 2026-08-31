"""
Auth callbacks — strictly ONE callback per output.

auth-state.data  → handle_auth_state  (signin-button click only)
url.pathname     → handle_url         (auth-state change → redirect)
                   handle_quick_nav   (quick-action buttons → navigate)
auth-alert       → handle_auth_alert  (signin, signup, forgot — read-only DB peek)
signin/signup form toggle → toggle_tab
"""
from dash import Input, Output, State, html, callback_context, no_update
import dash_bootstrap_components as dbc
from ..auth.user_manager import UserManager

user_manager = UserManager()


def register_auth_callbacks(app):

    # ── 1. auth-state.data — SOLE writer ────────────────────────────
    # Triggered ONLY by signin-button click or logout pathname.
    @app.callback(
        Output("auth-state", "data"),
        Input("signin-button", "n_clicks"),
        Input("url",           "pathname"),
        State("signin-email",    "value"),
        State("signin-password", "value"),
        State("signin-remember", "value"),
        prevent_initial_call=True,
    )
    def handle_auth_state(n, pathname, email, password, remember):
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        t = ctx.triggered[0]["prop_id"].split(".")[0]

        # Clear auth on logout
        if t == "url" and pathname == "/logout":
            return {"authenticated": False, "user": None}

        # Authenticate on button click
        if t == "signin-button":
            if not email or not password:
                return no_update
            ok, _msg, user_data = user_manager.authenticate_user(email, password)
            if ok:
                return {
                    "authenticated": True,
                    "user": user_data,
                    "remember": bool(remember),
                }
        return no_update

    # ── 2. url.pathname — SOLE writer (auth redirects only) ─────────
    # Watches auth-state changes only. Quick-action nav uses dcc.Link.
    @app.callback(
        Output("url", "pathname"),
        Input("auth-state", "data"),
        prevent_initial_call=True,
    )
    def handle_url(auth_state):
        if not isinstance(auth_state, dict):
            return no_update

        if auth_state.get("authenticated"):
            # Always go to dashboard on login
            return "/dashboard"
        else:
            # Always go to root on logout (clears /logout from URL)
            return "/"

    # ── 3. auth-alert — SOLE writer ─────────────────────────────────
    @app.callback(
        Output("auth-alert", "children"),
        Input("signin-button",        "n_clicks"),
        Input("signup-button",        "n_clicks"),
        Input("forgot-password-link", "n_clicks"),
        State("signin-email",            "value"),
        State("signin-password",         "value"),
        State("signup-fullname",         "value"),
        State("signup-email",            "value"),
        State("signup-password",         "value"),
        State("signup-password-confirm", "value"),
        State("signup-terms",            "value"),
        prevent_initial_call=True,
    )
    def handle_auth_alert(sc, supc, fc, s_email, s_pass,
                          su_name, su_email, su_pass, su_confirm, su_terms):
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        t = ctx.triggered[0]["prop_id"].split(".")[0]

        if t == "forgot-password-link":
            return dbc.Alert(
                "Contact your administrator to reset your password.",
                color="info", dismissable=True, duration=8000,
            )

        if t == "signup-button":
            if not all([su_name, su_email, su_pass, su_confirm]):
                return dbc.Alert("Please fill in all fields.", color="warning",
                                 dismissable=True, duration=4000)
            if not su_terms:
                return dbc.Alert("You must agree to the Terms of Service.",
                                 color="warning", dismissable=True, duration=4000)
            if su_pass != su_confirm:
                return dbc.Alert("Passwords do not match.", color="danger",
                                 dismissable=True, duration=4000)
            ok, msg = user_manager.register_user(su_email, su_name, su_pass)
            return dbc.Alert(
                "Account created! You can now sign in." if ok else msg,
                color="success" if ok else "danger",
                dismissable=True, duration=5000,
            )

        if t == "signin-button":
            if not s_email or not s_pass:
                return dbc.Alert("Please enter your email and password.",
                                 color="warning", dismissable=True, duration=4000)
            # Read-only DB peek — no attempt counter side effects
            db = user_manager._load_db()
            em = s_email.lower().strip()
            if em not in db:
                return dbc.Alert("Invalid email or password.", color="danger",
                                 dismissable=True, duration=5000)
            u = db[em]
            if u.get("account_locked"):
                return dbc.Alert("Account locked. Try again later.", color="danger",
                                 dismissable=True, duration=5000)
            h, _ = user_manager._hash_password(s_pass, u["salt"])
            if h != u["password_hash"]:
                rem = max(0, 4 - u.get("login_attempts", 0))
                return dbc.Alert(
                    f"Invalid email or password. {rem} attempts remaining.",
                    color="danger", dismissable=True, duration=5000,
                )
            return dbc.Alert(
                f"Welcome back, {u['full_name']}!",
                color="success", dismissable=True, duration=3000,
            )
        return no_update

    # ── 4. Tab toggle ────────────────────────────────────────────────
    @app.callback(
        Output("signin-form-div", "style"),
        Output("signup-form-div", "style"),
        Output("tab-btn-signin",  "outline"),
        Output("tab-btn-signup",  "outline"),
        Input("tab-btn-signin", "n_clicks"),
        Input("tab-btn-signup", "n_clicks"),
        prevent_initial_call=True,
    )
    def toggle_tab(a, b):
        ctx = callback_context
        if not ctx.triggered:
            return {"display": "block"}, {"display": "none"}, False, True
        if ctx.triggered[0]["prop_id"].split(".")[0] == "tab-btn-signup":
            return {"display": "none"}, {"display": "block"}, True, False
        return {"display": "block"}, {"display": "none"}, False, True
