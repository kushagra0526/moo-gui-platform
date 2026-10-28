"""
Results and export layout for solution analysis and data export
"""

from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go


def _empty_fig(title):
    fig = go.Figure()
    fig.update_layout(
        title=title, template="plotly_white",
        xaxis_title="", yaxis_title=""
    )
    fig.add_annotation(
        text="Run optimization to see results",
        xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False, font=dict(size=14, color="gray")
    )
    return fig

def create_results_layout():
    """Create the results and export interface."""
    
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("Results & Export", className="section-title"),
                html.P("Analyze solutions, compare experiments, and export results.", 
                       className="section-description")
            ])
        ], className="mb-4"),
        
        # Results Summary Charts
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Pareto Front", className="mb-0"),
                    ]),
                    dbc.CardBody([
                        dcc.Graph(
                            id="results-pareto-plot",
                            figure=_empty_fig("Pareto Front"),
                            style={"height": "350px"}
                        )
                    ])
                ])
            ], width=6, className="mb-4"),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Convergence History", className="mb-0"),
                    ]),
                    dbc.CardBody([
                        dcc.Graph(
                            id="results-convergence-plot",
                            figure=_empty_fig("Convergence History"),
                            style={"height": "350px"}
                        )
                    ])
                ])
            ], width=6, className="mb-4"),
        ]),

        # Performance Metrics Summary
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.H4("0", id="results-metric-generation", className="text-primary mb-0"),
                                    html.Small("Generations", className="text-muted"),
                                ], className="text-center")
                            ], width=3),
                            dbc.Col([
                                html.Div([
                                    html.H4("0", id="results-metric-solutions", className="text-success mb-0"),
                                    html.Small("Pareto Solutions", className="text-muted"),
                                ], className="text-center")
                            ], width=3),
                            dbc.Col([
                                html.Div([
                                    html.H4("0.000", id="results-metric-hypervolume", className="text-info mb-0"),
                                    html.Small("Hypervolume", className="text-muted"),
                                ], className="text-center")
                            ], width=3),
                            dbc.Col([
                                html.Div([
                                    html.H4("—", id="results-metric-status", className="text-warning mb-0"),
                                    html.Small("Status", className="text-muted"),
                                ], className="text-center")
                            ], width=3),
                        ])
                    ])
                ])
            ], width=12)
        ], className="mb-4"),

        # Experiment Management
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Experiment", className="mb-0")),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Experiment Name:", className="form-label"),
                                dbc.Input(
                                    id="experiment-name",
                                    placeholder="Enter experiment name",
                                    value="experiment_1"
                                )
                            ], width=4),
                            dbc.Col([
                                html.Label("Description:", className="form-label"),
                                dbc.Textarea(
                                    id="experiment-description",
                                    placeholder="Optional description",
                                    rows=2
                                )
                            ], width=8)
                        ])
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Solution Analysis
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Pareto-Optimal Solutions", className="mb-0")),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id="solutions-table",
                            columns=[],  # Columns will be set dynamically by callback
                            data=[],
                            sort_action="native",
                            filter_action="native",
                            row_selectable="single",
                            selected_rows=[],
                            page_size=10,
                            style_cell={'textAlign': 'center'},
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': 'rgb(248, 248, 248)'
                                }
                            ],
                            style_header={
                                'backgroundColor': 'rgb(230, 230, 230)',
                                'fontWeight': 'bold'
                            }
                        )
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Decision Making Tools
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Decision Making & Trade-off Analysis"),
                    dbc.CardBody([
                        dbc.Tabs([
                            dbc.Tab(label="Preference Articulation", tab_id="preferences"),
                            dbc.Tab(label="Solution Ranking", tab_id="ranking"),
                            dbc.Tab(label="Trade-off Analysis", tab_id="tradeoff")
                        ], id="decision-tabs", active_tab="preferences"),
                        html.Div(id="decision-content", className="mt-3")
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Export Options
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Export Results"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Export Format:", className="form-label"),
                                dbc.RadioItems(
                                    id="export-format",
                                    options=[
                                        {"label": "CSV (Pareto solutions)", "value": "csv"},
                                        {"label": "JSON (problem, settings and results)", "value": "json"},
                                    ],
                                    value="csv"
                                )
                            ], width=8),
                            dbc.Col([
                                html.Label("Actions:", className="form-label"),
                                html.Div([
                                    dbc.Button(
                                        [html.I(className="fas fa-download me-1"), "Export"],
                                        id="btn-export-results",
                                        color="success",
                                        className="mb-2 d-block"
                                    ),
                                    dbc.Button(
                                        [html.I(className="fas fa-code me-1"), "Generate Code"],
                                        id="btn-generate-code",
                                        color="primary",
                                        className="d-block"
                                    )
                                ])
                            ], width=4)
                        ])
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Generated Code Display
        dbc.Row([
            dbc.Col([
                dbc.Collapse([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("Generated Python Code", className="mb-0"),
                            dcc.Clipboard(target_id="generated-code", title="Copy code",
                                          className="float-end", style={"cursor": "pointer"})
                        ], className="d-flex justify-content-between align-items-center"),
                        dbc.CardBody([
                            dcc.Textarea(
                                id="generated-code",
                                style={"width": "100%", "height": "400px", "fontFamily": "monospace"},
                                readOnly=True
                            )
                        ])
                    ])
                ], id="code-collapse", is_open=False)
            ], width=12)
        ])
        
    ], fluid=True)

def create_preference_content():
    """Create preference articulation interface."""
    return dbc.Row([
        dbc.Col([
            html.H6("Objective Weights"),
            html.Div(id="objective-weights-container")
        ], width=4),
        dbc.Col([
            html.H6("Aspiration Levels"),
            html.Div(id="aspiration-levels-container")
        ], width=4),
        dbc.Col([
            html.H6("Reference Points"),
            html.Div(id="reference-points-container")
        ], width=4)
    ])

def create_ranking_content():
    """Create solution ranking interface."""
    return dbc.Row([
        dbc.Col([
            html.Label("Ranking Method:", className="form-label"),
            dbc.Select(
                id="ranking-method",
                options=[
                    {"label": "TOPSIS", "value": "topsis"},
                    {"label": "Weighted Sum", "value": "weighted_sum"},
                    {"label": "Compromise Programming", "value": "compromise"},
                    {"label": "ELECTRE", "value": "electre"}
                ],
                value="topsis"
            )
        ], width=6),
        dbc.Col([
            dbc.Button(
                "Apply Ranking",
                id="btn-apply-ranking",
                color="primary"
            )
        ], width=6)
    ])

def create_tradeoff_content():
    """Create trade-off analysis interface."""
    return dbc.Row([
        dbc.Col([
            html.P("Select two solutions to analyze trade-offs:"),
            dbc.Select(
                id="solution-a-select",
                placeholder="Select Solution A"
            )
        ], width=4),
        dbc.Col([
            dbc.Select(
                id="solution-b-select",
                placeholder="Select Solution B"
            )
        ], width=4),
        dbc.Col([
            dbc.Button(
                "Analyze Trade-offs",
                id="btn-analyze-tradeoffs",
                color="primary"
            )
        ], width=4)
    ])