"""
CEC2018 DMOP dedicated page layout.
"""
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

# ── Problem metadata ────────────────────────────────────────────────
_PROBLEMS = {
    1:  ("DF1",  2, "Linear Pareto front that shifts sinusoidally over time."),
    2:  ("DF2",  2, "Concave Pareto front with time-varying position."),
    3:  ("DF3",  2, "Convex Pareto front with dynamic curvature."),
    4:  ("DF4",  2, "Mixed Pareto front with oscillating shape."),
    5:  ("DF5",  2, "Disconnected Pareto front segments, time-varying."),
    6:  ("DF6",  2, "Linear front with deceptive landscape changes."),
    7:  ("DF7",  2, "Convex front with time-dependent variable linkage."),
    8:  ("DF8",  2, "Concave front with changing variable interactions."),
    9:  ("DF9",  2, "Multi-modal dynamic landscape, 2 objectives."),
    10: ("DF10", 3, "3-objective problem with linear Pareto surface."),
    11: ("DF11", 3, "3-objective spherical Pareto surface, dynamic."),
    12: ("DF12", 3, "3-objective problem with degenerate front."),
    13: ("DF13", 3, "3-objective problem with time-varying bias."),
    14: ("DF14", 3, "3-objective problem with mixed dynamics."),
}

_OBJ_COLOR = {2: "primary", 3: "success"}


def _problem_card(pid):
    name, n_obj, desc = _PROBLEMS[pid]
    return dbc.Col(
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.Span(name,
                              style={"fontSize": "1.3rem", "fontWeight": "800",
                                     "color": "#00d4ff"}),
                    dbc.Badge(
                        f"{n_obj}-obj",
                        color=_OBJ_COLOR[n_obj],
                        className="ms-2",
                        style={"fontSize": "0.75rem"},
                    ),
                ], className="mb-2"),
                html.P(desc,
                       className="text-muted mb-3",
                       style={"fontSize": "0.82rem", "minHeight": "48px"}),
                dbc.Button(
                    [html.I(className="fas fa-play me-2"), "Select"],
                    id={"type": "cec-select-btn", "index": pid},
                    color="outline-primary",
                    size="sm",
                    className="w-100",
                    style={"borderRadius": "8px"},
                ),
            ])
        ], className="h-100",
           style={"background": "rgba(20,24,41,0.7)",
                  "border": "1px solid rgba(0,212,255,0.2)",
                  "borderRadius": "12px"}),
        md=3, sm=6, className="mb-3",
    )


def _empty_fig(title="Pareto Front"):
    fig = go.Figure()
    fig.update_layout(
        title=title,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        uirevision="static",          # prevents camera reset on data update
        margin=dict(l=40, r=20, t=40, b=40),
    )
    fig.add_annotation(
        text="Select a problem and click Run",
        xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False, font=dict(size=14, color="#6b7280"),
    )
    return fig


def _compare_panel():
    """Time comparison panel — shown below the viz panel."""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-code-branch me-2", style={"color": "#00d4ff"}),
            html.Span("Compare Across Time",
                      style={"fontWeight": "700", "color": "#00d4ff"}),
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Time t₁", className="form-label small"),
                    dbc.Select(
                        id="cec-t1-select",
                        options=[{"label": f"t = {i}", "value": i} for i in range(1, 11)],
                        value=1,
                        style={"background": "rgba(20,24,41,0.9)", "color": "#e8eaf6",
                               "border": "1px solid rgba(0,212,255,0.3)"},
                    ),
                ], width=3),
                dbc.Col([
                    html.Label("Time t₂", className="form-label small"),
                    dbc.Select(
                        id="cec-t2-select",
                        options=[{"label": f"t = {i}", "value": i} for i in range(1, 11)],
                        value=2,
                        style={"background": "rgba(20,24,41,0.9)", "color": "#e8eaf6",
                               "border": "1px solid rgba(0,212,255,0.3)"},
                    ),
                ], width=3),
                dbc.Col([
                    html.Label("\u00a0", className="form-label small d-block"),
                    dbc.Button(
                        [html.I(className="fas fa-chart-line me-2"), "Compare Pareto Fronts"],
                        id="cec-compare-btn",
                        color="info",
                        disabled=False,
                        style={"borderRadius": "8px"},
                    ),
                ], width=4),
                dbc.Col([
                    html.Label("View", className="form-label small"),
                    dbc.RadioItems(
                        id="cec-compare-view",
                        options=[
                            {"label": "Overlay", "value": "overlay"},
                            {"label": "Side-by-Side", "value": "side"},
                        ],
                        value="overlay",
                        inline=True,
                        className="small",
                    ),
                ], width=2),
            ], className="mb-3 align-items-end"),

            html.Div(id="cec-compare-status",
                     className="text-muted small mb-2",
                     children="Select a problem and run optimization first."),

            # Overlay view
            html.Div(id="cec-compare-overlay-div", children=[
                dcc.Graph(
                    id="cec-compare-plot",
                    figure=_empty_compare_fig(),
                    style={"height": "420px"},
                    config={"displayModeBar": True},
                ),
            ]),

            # Side-by-side view
            html.Div(id="cec-compare-side-div", style={"display": "none"}, children=[
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(
                            id="cec-compare-plot-t1",
                            figure=_empty_compare_fig("t₁"),
                            style={"height": "380px"},
                            config={"displayModeBar": False},
                        ),
                    ], width=6),
                    dbc.Col([
                        dcc.Graph(
                            id="cec-compare-plot-t2",
                            figure=_empty_compare_fig("t₂"),
                            style={"height": "380px"},
                            config={"displayModeBar": False},
                        ),
                    ], width=6),
                ]),
            ]),
        ]),
    ], style={"background": "rgba(20,24,41,0.7)",
              "border": "1px solid rgba(0,212,255,0.15)",
              "borderRadius": "12px"},
       className="mb-4")


def _empty_compare_fig(label=""):
    fig = go.Figure()
    fig.update_layout(
        title=f"Pareto Front Comparison {label}".strip(),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,18,30,0.8)",
        uirevision="cec-compare",
        margin=dict(l=40, r=20, t=40, b=40),
    )
    fig.add_annotation(
        text="Click 'Compare Pareto Fronts' to start",
        xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False, font=dict(size=13, color="#6b7280"),
    )
    return fig


def create_cec2018_layout():
    problem_grid = dbc.Row(
        [_problem_card(pid) for pid in range(1, 15)],
        className="mb-4",
    )

    config_panel = dbc.Card([
        dbc.CardHeader([
            html.Span(id="cec-selected-label",
                      children="No problem selected",
                      style={"fontWeight": "700", "color": "#00d4ff"}),
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Population Size", className="form-label small"),
                    dbc.Input(id="cec-pop-size",  type="number",
                              value=100, min=20, max=500, step=10),
                ], width=3),
                dbc.Col([
                    html.Label("Max Generations", className="form-label small"),
                    dbc.Input(id="cec-max-gen",   type="number",
                              value=200, min=10, max=2000, step=10),
                ], width=3),
                dbc.Col([
                    html.Label("Change Freq (taut)", className="form-label small"),
                    dbc.Input(id="cec-taut",       type="number",
                              value=10, min=1, max=200, step=1),
                ], width=2),
                dbc.Col([
                    html.Label("Severity (nt)", className="form-label small"),
                    dbc.Input(id="cec-nt",         type="number",
                              value=10, min=1, max=100, step=1),
                ], width=2),
                dbc.Col([
                    html.Label("Live Update", className="form-label small"),
                    dbc.Switch(id="cec-live-toggle", value=True,
                               label="On", className="mt-1"),
                ], width=2),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button(
                            [html.I(className="fas fa-play me-2"), "Run"],
                            id="cec-run-btn", color="success",
                            disabled=True,
                            style={"borderRadius": "8px 0 0 8px"},
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-stop me-2"), "Stop"],
                            id="cec-stop-btn", color="danger",
                            disabled=True,
                            style={"borderRadius": "0 8px 8px 0"},
                        ),
                    ]),
                    html.Span(id="cec-status-text",
                              children="",
                              className="ms-3 text-muted small",
                              style={"verticalAlign": "middle"}),
                ]),
            ]),
        ]),
    ], style={"background": "rgba(20,24,41,0.7)",
              "border": "1px solid rgba(0,212,255,0.15)",
              "borderRadius": "12px"},
       className="mb-4")

    viz_panel = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.Span("Pareto Front", style={"fontWeight": "600"}),
                    dbc.Badge(id="cec-gen-badge", children="Gen 0",
                              color="secondary", className="ms-2"),
                ]),
                dbc.CardBody([
                    dcc.Graph(
                        id="cec-pareto-plot",
                        figure=_empty_fig("Pareto Front"),
                        style={"height": "420px"},
                        config={"displayModeBar": False},
                    ),
                ], style={"padding": "0.5rem"}),
            ], style={"background": "rgba(20,24,41,0.7)",
                      "border": "1px solid rgba(0,212,255,0.15)",
                      "borderRadius": "12px"}),
        ], width=8),

        dbc.Col([
            # Metrics
            dbc.Card([
                dbc.CardHeader("Metrics"),
                dbc.CardBody([
                    _metric_row("Generation",  "cec-metric-gen",  "fas fa-clock"),
                    _metric_row("Hypervolume", "cec-metric-hv",   "fas fa-cube"),
                    _metric_row("PF Size",     "cec-metric-pf",   "fas fa-dot-circle"),
                    _metric_row("Time Step t", "cec-metric-t",    "fas fa-hourglass"),
                ]),
            ], className="mb-3",
               style={"background": "rgba(20,24,41,0.7)",
                      "border": "1px solid rgba(0,212,255,0.15)",
                      "borderRadius": "12px"}),

            # HV over time
            dbc.Card([
                dbc.CardHeader("Hypervolume over Time"),
                dbc.CardBody([
                    dcc.Graph(
                        id="cec-hv-plot",
                        figure=_empty_fig("HV"),
                        style={"height": "200px"},
                        config={"displayModeBar": False},
                    ),
                ], style={"padding": "0.25rem"}),
            ], style={"background": "rgba(20,24,41,0.7)",
                      "border": "1px solid rgba(0,212,255,0.15)",
                      "borderRadius": "12px"}),
        ], width=4),
    ], className="mb-4")

    compare_panel = _compare_panel()

    return html.Div([
        # Hidden stores
        dcc.Store(id="cec-state",          storage_type="memory"),
        dcc.Store(id="cec-results",        storage_type="memory"),
        dcc.Store(id="cec-problem-id",     storage_type="memory"),
        dcc.Interval(id="cec-interval",     interval=2000, disabled=True),

        html.Div([
            html.H4("CEC2018 Dynamic MOPs",
                    style={"color": "#00d4ff", "fontWeight": "800"}),
            html.P("DF1–DF14 benchmark functions with time-varying Pareto fronts.",
                   className="text-muted mb-4"),
        ]),

        problem_grid,
        config_panel,
        viz_panel,
        compare_panel,
    ], className="fade-in", style={"padding": "1rem"})


def _metric_row(label, elem_id, icon):
    return html.Div([
        html.I(className=f"{icon} me-2 text-primary"),
        html.Span(label + ": ",
                  style={"color": "#b8bfcc", "fontSize": "0.85rem"}),
        html.Span("—", id=elem_id,
                  style={"color": "#e8eaf6", "fontWeight": "700",
                         "fontSize": "0.9rem"}),
    ], className="mb-2")
