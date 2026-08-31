"""
Visualization layout for real-time monitoring and Pareto front display
"""

from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

def create_visualization_layout():
    """Create the visualization interface."""
    
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("Real-time Visualization", className="section-title"),
                html.P("Monitor optimization progress and explore Pareto fronts.", 
                       className="section-description")
            ])
        ], className="mb-4"),
        
        # Visualization Controls
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Visualization Controls"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Plot Type:", className="form-label"),
                                dbc.Select(
                                    id="plot-type-select",
                                    options=[
                                        {"label": "2D Pareto Front", "value": "pareto_2d"},
                                        {"label": "3D Pareto Front", "value": "pareto_3d"},
                                        {"label": "Parallel Coordinates", "value": "parallel"},
                                        {"label": "Convergence Metrics", "value": "convergence"},
                                        {"label": "Population Evolution", "value": "evolution"}
                                    ],
                                    value="pareto_2d"
                                )
                            ], width=3),
                            dbc.Col([
                                html.Label("X-Axis Objective:", className="form-label"),
                                dbc.Select(
                                    id="x-axis-objective",
                                    options=[
                                        {"label": "Objective 1", "value": 0},
                                        {"label": "Objective 2", "value": 1}
                                    ],
                                    value=0
                                )
                            ], width=3),
                            dbc.Col([
                                html.Label("Y-Axis Objective:", className="form-label"),
                                dbc.Select(
                                    id="y-axis-objective",
                                    options=[
                                        {"label": "Objective 1", "value": 0},
                                        {"label": "Objective 2", "value": 1}
                                    ],
                                    value=1
                                )
                            ], width=3),
                            dbc.Col([
                                html.Label("Update Frequency:", className="form-label"),
                                dbc.Select(
                                    id="update-frequency",
                                    options=[
                                        {"label": "Real-time", "value": 1},
                                        {"label": "Every 5 gen", "value": 5},
                                        {"label": "Every 10 gen", "value": 10}
                                    ],
                                    value=5
                                )
                            ], width=3)
                        ])
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Main Visualization Area
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Optimization Progress", className="mb-0"),
                        dbc.ButtonGroup([
                            dbc.Button(
                                html.I(className="fas fa-play"),
                                id="btn-play-animation",
                                color="success",
                                size="sm",
                                outline=True
                            ),
                            dbc.Button(
                                html.I(className="fas fa-pause"),
                                id="btn-pause-animation",
                                color="warning",
                                size="sm",
                                outline=True
                            ),
                            dbc.Button(
                                html.I(className="fas fa-download"),
                                id="btn-download-plot",
                                color="primary",
                                size="sm",
                                outline=True
                            )
                        ], size="sm", className="float-end")
                    ], className="d-flex justify-content-between align-items-center"),
                    dbc.CardBody([
                        dcc.Graph(
                            id="main-visualization",
                            figure=create_empty_plot(),
                            style={"height": "500px"}
                        )
                    ])
                ])
            ], width=8),
            dbc.Col([
                # Metrics Panel
                dbc.Card([
                    dbc.CardHeader("Performance Metrics"),
                    dbc.CardBody([
                        html.Div(id="metrics-display", children=[
                            create_metric_card("Generation", "0", "fas fa-clock"),
                            create_metric_card("Hypervolume", "0.000", "fas fa-cube"),
                            create_metric_card("IGD", "0.000", "fas fa-ruler"),
                            create_metric_card("Solutions", "0", "fas fa-dot-circle")
                        ])
                    ])
                ], className="mb-3"),
                
                # Solution Inspector
                dbc.Card([
                    dbc.CardHeader("Solution Inspector"),
                    dbc.CardBody([
                        html.Div(id="solution-inspector", children=[
                            html.P("Click on a solution in the plot to inspect its details.", 
                                   className="text-muted")
                        ])
                    ])
                ])
            ], width=4)
        ], className="mb-4"),
        
        # Secondary Visualizations
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Convergence History"),
                    dbc.CardBody([
                        dcc.Graph(
                            id="convergence-plot",
                            figure=create_empty_convergence_plot(),
                            style={"height": "300px"}
                        )
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Diversity Metrics"),
                    dbc.CardBody([
                        dcc.Graph(
                            id="diversity-plot",
                            figure=create_empty_diversity_plot(),
                            style={"height": "300px"}
                        )
                    ])
                ])
            ], width=6)
        ])
        
    ], fluid=True)

def create_empty_plot():
    """Create an empty plot placeholder."""
    fig = go.Figure()
    fig.update_layout(
        title="Pareto Front Visualization",
        xaxis_title="Objective 1",
        yaxis_title="Objective 2",
        template="plotly_white",
        showlegend=True
    )
    fig.add_annotation(
        text="Run optimization to see results",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="gray")
    )
    return fig

def create_empty_convergence_plot():
    """Create an empty convergence plot."""
    fig = go.Figure()
    fig.update_layout(
        title="Convergence Metrics",
        xaxis_title="Generation",
        yaxis_title="Metric Value",
        template="plotly_white"
    )
    return fig

def create_empty_diversity_plot():
    """Create an empty diversity plot."""
    fig = go.Figure()
    fig.update_layout(
        title="Population Diversity",
        xaxis_title="Generation",
        yaxis_title="Diversity Measure",
        template="plotly_white"
    )
    return fig

def create_metric_card(title, value, icon):
    """Create a metric display card."""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.I(className=f"{icon} fa-2x text-primary")
                ], width=4),
                dbc.Col([
                    html.H4(value, className="mb-0", id=f"metric-{title.lower()}"),
                    html.P(title, className="text-muted mb-0")
                ], width=8)
            ])
        ])
    ], className="mb-2")