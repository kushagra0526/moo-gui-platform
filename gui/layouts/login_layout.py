"""
Login layout — clean research-grade design. All form IDs always in DOM.
"""
from dash import html
import dash_bootstrap_components as dbc

# Shared inline style tokens (minimal overrides — CSS handles the rest)
_C = {
    "bg":      "#161b22",
    "surface": "#1c2128",
    "border":  "#30363d",
    "text":    "#e6edf3",
    "muted":   "#8b949e",
    "accent":  "#388bfd",
    "success": "#3fb950",
}


def build_login_card():
    left_panel = html.Div([
        html.Div([
            html.I(className="fas fa-chart-scatter",
                   style={"fontSize": "1.8rem", "color": _C["accent"],
                          "marginBottom": "0.75rem"}),
            html.H2("Multi-Objective\nOptimization",
                    style={"fontSize": "1.35rem", "fontWeight": "700",
                           "lineHeight": "1.4", "whiteSpace": "pre-line",
                           "color": _C["text"], "marginBottom": "0.4rem"}),
            html.P("Research Platform",
                   style={"color": _C["muted"], "fontSize": "0.8rem",
                          "marginBottom": "2rem"}),
        ]),
        html.Hr(style={"borderColor": _C["border"], "marginBottom": "1.5rem"}),
        *[html.Div([
            html.I(className=f"{ic} me-2",
                   style={"color": _C["accent"], "fontSize": "0.85rem",
                          "width": "16px", "opacity": "0.8"}),
            html.Span(tx, style={"color": _C["muted"], "fontSize": "0.8rem"}),
          ], style={"display": "flex", "alignItems": "center",
                    "marginBottom": "0.65rem"})
          for ic, tx in [
            ("fas fa-dna",         "NSGA-II / NSGA-III algorithms"),
            ("fas fa-chart-line",  "Real-time Pareto visualization"),
            ("fas fa-sliders-h",   "Configurable problem definitions"),
            ("fas fa-file-export", "Export results & generate code"),
          ]],
    ], style={
        "display": "flex", "flexDirection": "column",
        "justifyContent": "center", "height": "100%",
        "padding": "2.5rem 2rem",
        "background": _C["surface"],
        "borderRight": f"1px solid {_C['border']}",
    })

    tab_btns = html.Div([
        dbc.Button("Sign In", id="tab-btn-signin", color="primary",
                   outline=False, size="sm", className="me-2"),
        dbc.Button("Sign Up", id="tab-btn-signup", color="secondary",
                   outline=True, size="sm"),
    ], style={"marginBottom": "1.25rem"})

    _inp_style = {
        "background": _C["surface"],
        "border": f"1px solid {_C['border']}",
        "color": _C["text"],
        "borderRadius": "6px",
        "fontSize": "0.82rem",
    }
    _lbl_style = {
        "color": _C["muted"],
        "fontSize": "0.75rem",
        "fontWeight": "500",
        "marginBottom": "0.3rem",
    }

    signin_form = html.Div([
        dbc.Label("Email", style=_lbl_style),
        dbc.Input(type="email", id="signin-email",
                  placeholder="you@example.com",
                  className="mb-3", style=_inp_style),
        dbc.Label("Password", style=_lbl_style),
        dbc.Input(type="password", id="signin-password",
                  placeholder="••••••••",
                  className="mb-3", style=_inp_style),
        html.Div([
            dbc.Checkbox(id="signin-remember", label="Remember me",
                         style={"color": _C["muted"], "fontSize": "0.78rem"}),
            html.A("Forgot password?", href="#", id="forgot-password-link",
                   style={"color": _C["accent"], "fontSize": "0.78rem",
                          "textDecoration": "none"}),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "alignItems": "center", "marginBottom": "1.25rem"}),
        dbc.Button([html.I(className="fas fa-sign-in-alt me-2"), "Sign In"],
                   id="signin-button", color="primary",
                   size="md", className="w-100"),
    ], id="signin-form-div")

    signup_form = html.Div([
        dbc.Label("Full Name", style=_lbl_style),
        dbc.Input(type="text", id="signup-fullname",
                  placeholder="Your full name",
                  className="mb-2", style=_inp_style),
        dbc.Label("Email", style=_lbl_style),
        dbc.Input(type="email", id="signup-email",
                  placeholder="you@example.com",
                  className="mb-2", style=_inp_style),
        dbc.Label("Password", style=_lbl_style),
        dbc.Input(type="password", id="signup-password",
                  placeholder="Min 8 characters",
                  className="mb-2", style=_inp_style),
        dbc.Label("Confirm Password", style=_lbl_style),
        dbc.Input(type="password", id="signup-password-confirm",
                  placeholder="Repeat password",
                  className="mb-3", style=_inp_style),
        dbc.Checkbox(id="signup-terms", className="mb-3",
                     label=html.Span([
                         "I agree to the ",
                         html.A("Terms of Service", href="#",
                                style={"color": _C["accent"]}),
                         " and ",
                         html.A("Privacy Policy", href="#",
                                style={"color": _C["accent"]}),
                     ], style={"fontSize": "0.78rem", "color": _C["muted"]})),
        dbc.Button([html.I(className="fas fa-user-plus me-2"), "Create Account"],
                   id="signup-button", color="success",
                   size="md", className="w-100"),
    ], id="signup-form-div", style={"display": "none"})

    right_panel = html.Div([
        html.H5("Welcome back",
                style={"color": _C["text"], "fontWeight": "600",
                       "marginBottom": "0.2rem", "fontSize": "1rem"}),
        html.P("Sign in to continue",
               style={"color": _C["muted"], "fontSize": "0.78rem",
                      "marginBottom": "1.25rem"}),
        tab_btns,
        signin_form,
        signup_form,
        html.Div(id="auth-alert", style={"marginTop": "0.75rem"}),
        html.Hr(style={"borderColor": _C["border"], "margin": "1.25rem 0"}),
        html.P([
            html.I(className="fas fa-lock me-2",
                   style={"color": _C["success"], "fontSize": "0.75rem"}),
            html.Span("Encrypted & secure",
                      style={"color": _C["muted"], "fontSize": "0.75rem"}),
        ], style={"textAlign": "center", "marginBottom": "0"}),
    ], style={"padding": "2rem 2rem"})

    card = html.Div([
        dbc.Row([
            dbc.Col(left_panel,  md=5, style={"padding": "0"}),
            dbc.Col(right_panel, md=7, style={"padding": "0"}),
        ], style={"margin": "0", "minHeight": "480px"}),
    ], style={
        "background": _C["bg"],
        "border": f"1px solid {_C['border']}",
        "borderRadius": "8px",
        "boxShadow": "0 8px 24px rgba(0,0,0,0.4)",
        "overflow": "hidden",
        "width": "100%",
        "maxWidth": "820px",
        "margin": "0 auto",
    })

    return html.Div([
        html.Div([card], style={
            "minHeight": "100vh",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "padding": "2rem 1rem",
            "background": "#0d1117",
        }),
    ], className="login-page")


def create_login_layout():
    return build_login_card()
