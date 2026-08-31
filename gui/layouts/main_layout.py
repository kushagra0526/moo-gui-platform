"""
Main application layout — shell with URL-driven inner page rendering.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

from .dashboard_layout      import create_dashboard_layout
from .problem_definition    import create_problem_definition_layout
from .algorithm_config      import create_algorithm_config_layout
from .visualization         import create_visualization_layout
from .results               import create_results_layout
from .cec2018_layout        import create_cec2018_layout

# Map URL pathnames → page factory functions
PAGE_MAP = {
    "/dashboard":    create_dashboard_layout,
    "/problem":      create_problem_definition_layout,
    "/algorithm":    create_algorithm_config_layout,
    "/visualization": create_visualization_layout,
    "/results":      create_results_layout,
    "/cec2018":      create_cec2018_layout,
}

def _nav_link(icon_cls, label, href, active_path):
    """Render a single sidebar navigation link."""
    is_active = active_path == href
    return dcc.Link(
        html.Div(
            [html.I(className=f"{icon_cls} me-2"), html.Span(label)],
            className=f"nav-button-inner {'nav-active' if is_active else ''}",
        ),
        href=href,
        className="nav-link-item",
        style={"textDecoration": "none", "display": "block"},
    )


def create_main_layout(user_data=None, pathname="/dashboard", engine_running=False, saved_state=None):
    """Create the authenticated shell layout."""

    full_name = (user_data or {}).get("full_name", "User")
    email     = (user_data or {}).get("email", "")

    # Resolve inner page — pass saved_state to problem page for restoration
    page_factory = PAGE_MAP.get(pathname, create_dashboard_layout)
    if pathname == "/problem" and saved_state:
        inner_page = page_factory(saved_state=saved_state)
    else:
        inner_page = page_factory()

    sidebar = html.Div([
        # User profile
        html.Div([
            html.I(className="fas fa-user-circle fa-3x text-primary d-block text-center mb-2"),
            html.H6(full_name, className="text-center mb-0 fw-bold"),
            html.P(email, className="text-center text-muted small mb-0",
                   style={"fontSize": "0.75rem"}),
        ], className="user-profile-card p-3 mb-3"),

        # Navigation links (href-based — reliable re-render every click)
        html.Div([
            _nav_link("fas fa-home",       "Dashboard",         "/dashboard",    pathname),
            _nav_link("fas fa-cog",        "Problem Definition","/problem",       pathname),
            _nav_link("fas fa-sliders-h",  "Algorithm Config",  "/algorithm",    pathname),
            _nav_link("fas fa-chart-line", "Visualization",     "/visualization",pathname),
            _nav_link("fas fa-table",      "Results & Export",  "/results",      pathname),
            html.Hr(className="my-1", style={"borderColor": "rgba(0,212,255,0.15)"}),
            _nav_link("fas fa-atom",       "CEC2018 DMOP",      "/cec2018",      pathname),
        ], className="mb-3"),

        html.Hr(className="my-2"),

        # Logout — updates URL to /logout which auth callback handles
        dcc.Link(
            html.Div(
                [html.I(className="fas fa-sign-out-alt me-2"), html.Span("Logout")],
                className="nav-button-inner text-danger",
                id="nav-logout",
            ),
            href="/logout",
            className="nav-link-item",
            style={"textDecoration": "none", "display": "block"},
        ),
    ], className="sidebar-container")

    header = dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.I(className="fas fa-chart-scatter me-2",
                               style={"fontSize": "1.1rem", "color": "#388bfd"}),
                        html.Div([
                            html.Span("Multi-Objective Optimization",
                                    className="navbar-title"),
                            html.Span(" — Research Platform",
                                       className="navbar-subtitle"),
                        ], style={"display": "inline-block",
                                  "verticalAlign": "middle"}),
                    ], style={"display": "flex", "alignItems": "center"}),
                ], width=6),
                dbc.Col([
                    html.Div([
                        dbc.ButtonGroup([
                            dbc.Button(
                                [html.I(className="fas fa-play me-1"), "Run"],
                                id="btn-run-optimization",
                                color="success", size="sm",
                                className="btn-modern",
                                disabled=engine_running,
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-stop me-1"), "Stop"],
                                id="btn-stop-optimization",
                                color="danger", size="sm",
                                disabled=not engine_running,
                                className="btn-modern",
                            ),
                        ], className="me-2"),
                        dbc.Button(
                            [html.I(className="fas fa-save me-1"), "Save"],
                            id="btn-save-experiment",
                            color="secondary", size="sm",
                            className="btn-modern me-2",
                        ),
                        dbc.Button(
                            html.I(className="fas fa-moon", id="theme-icon"),
                            id="btn-theme-toggle",
                            color="secondary", size="sm",
                            className="btn-modern",
                            title="Toggle light/dark mode",
                        ),
                    ], style={"display": "flex", "justifyContent": "flex-end",
                              "alignItems": "center"}),
                ], width=6),
            ], align="center", className="w-100"),
        ], fluid=True),
        color="dark", dark=True,
        className="navbar-modern mb-0", sticky="top",
    )

    return html.Div([
        header,
        dbc.Container([
            dbc.Row([
                dbc.Col(sidebar, width=2, className="sidebar",
                        style={"height": "calc(100vh - 52px)", "overflowY": "auto",
                               "position": "sticky", "top": "52px"}),
                dbc.Col(
                    html.Div(inner_page, id="page-content", className="content-area"),
                    width=10,
                    style={"overflowY": "auto", "height": "calc(100vh - 52px)"},
                ),
            ], style={"flexWrap": "nowrap"})
        ], fluid=True),
        # Status bar
        html.Div([
            html.Span(id="status-text", children="Ready"),
            html.Div(
                dbc.Progress(id="progress-bar", value=0, style={"height": "4px"}),
                className="progress-container",
            ),
        ], className="status-bar"),
    ], className="app-container")
