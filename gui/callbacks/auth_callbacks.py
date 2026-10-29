"""
Auth callbacks — strictly ONE callback per output.

auth-state.data  → handle_auth_state  (signin-button click; also sets the server session)
url.pathname     → handle_url         (auth-state change → redirect)
auth-alert       → handle_auth_state  (signin result), handle_auth_alert (signup, forgot)
signin/signup form toggle → toggle_tab

The signed Flask session is what proves a login; auth-state only tells the browser to re-route.
"""
from dash import Input, Output, State, callback_context, no_update
import dash_bootstrap_components as dbc
from flask import session
from ..auth.user_manager import UserManager

user_manager = UserManager()


def register_auth_callbacks(app):

    # ── 1. auth-state.data — SOLE writer ────────────────────────────
    # Triggered ONLY by signin-button click. Logout is handled by the router
    # (listening to url here too would make a url → auth-state → url cycle).
    @app.callback(
        Output("auth-state", "data"),
        Output("auth-alert", "children", allow_duplicate=True),
        Input("signin-button", "n_clicks"),
        State("signin-email",    "value"),
        State("signin-password", "value"),
        State("signin-remember", "value"),
        prevent_initial_call=True,
    )
    def handle_auth_state(n, email, password, remember):
        if n:
            if not email or not password:
                return no_update, dbc.Alert("Please enter your email and password.",
                                            color="warning", dismissable=True, duration=4000)
            ok, msg, user_data = user_manager.authenticate_user(email, password)
            if not ok:
                return no_update, dbc.Alert(msg, color="danger", dismissable=True, duration=5000)
            session["user"] = user_data
            return (
                {"authenticated": True, "user": user_data, "remember": bool(remember)},
                dbc.Alert(f"Welcome back, {user_data['full_name']}!",
                          color="success", dismissable=True, duration=3000),
            )
        return no_update, no_update

    # ── 2. url.pathname — SOLE writer (auth redirects only) ─────────
    # Watches auth-state changes only. Quick-action nav uses dcc.Link.
    @app.callback(
        Output("url", "pathname"),
        Input("auth-state", "data"),
        State("url", "pathname"),
        prevent_initial_call=True,
    )
    def handle_url(auth_state, pathname):
        # auth-state also fires when the browser restores it on reload; only leave the root/logout URL,
        # so reloading or bookmarking an app page stays on that page
        if isinstance(auth_state, dict) and auth_state.get("authenticated") and pathname in (None, "/", "/logout"):
            return "/dashboard"
        return no_update

    # ── 3. auth-alert — SOLE writer ─────────────────────────────────
    @app.callback(
        Output("auth-alert", "children"),
        Input("signup-button",        "n_clicks"),
        Input("forgot-password-link", "n_clicks"),
        State("signup-fullname",         "value"),
        State("signup-email",            "value"),
        State("signup-password",         "value"),
        State("signup-password-confirm", "value"),
        State("signup-terms",            "value"),
        prevent_initial_call=True,
    )
    def handle_auth_alert(supc, fc, su_name, su_email, su_pass, su_confirm, su_terms):
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
