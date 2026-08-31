"""
Algorithm configuration layout for MOEA selection and parameter tuning
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

def create_algorithm_config_layout():
    """Create the algorithm configuration interface."""
    
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("Algorithm Configuration", className="section-title"),
                html.P("Configure NSGA-II algorithm parameters for optimization.", 
                       className="section-description")
            ])
        ], className="mb-4"),
        
        # Algorithm Selection (Fixed to NSGA-II)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Algorithm Selection"),
                    dbc.CardBody([
                        dbc.Select(
                            id="algorithm-select",
                            options=[
                                {"label": "NSGA-II", "value": "nsga2"}
                            ],
                            value="nsga2",
                            disabled=True
                        ),
                        html.Div([
                            html.P("NSGA-II (Non-dominated Sorting Genetic Algorithm II)", 
                                  className="fw-bold mt-3 mb-2"),
                            html.Ul([
                                html.Li("Fast non-dominated sorting"),
                                html.Li("Crowding distance for diversity preservation"),
                                html.Li("Suitable for multi-objective optimization")
                            ], className="mb-0")
                        ], id="algorithm-description")
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # General Parameters
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("General Parameters"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Population Size:", className="form-label"),
                                dbc.Input(
                                    id="population-size",
                                    type="number",
                                    value=100,
                                    min=10,
                                    max=1000,
                                    step=10
                                )
                            ], width=4),
                            dbc.Col([
                                html.Label("Max Generations:", className="form-label"),
                                dbc.Input(
                                    id="max-generations",
                                    type="number",
                                    value=250,
                                    min=10,
                                    max=10000,
                                    step=10
                                )
                            ], width=4),
                            dbc.Col([
                                html.Label("Random Seed:", className="form-label"),
                                dbc.Input(
                                    id="random-seed",
                                    type="number",
                                    value=42,
                                    min=0,
                                    max=99999,
                                    step=1
                                )
                            ], width=4),
                        ])
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Algorithm-Specific Parameters
        html.Div(id="algorithm-specific-params"),

        # Dynamic problem parameters — shown only when problem-type is dynamic
        html.Div([
            dbc.Card([
                dbc.CardHeader("Dynamic Problem Parameters (CEC2018)"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Change Frequency (taut):", className="form-label"),
                            dbc.Input(
                                id="dynamic-taut",
                                type="number",
                                value=10,
                                min=1,
                                max=500,
                                step=1,
                            ),
                            html.Small("Generations between environment changes", className="text-muted"),
                        ], width=6),
                        dbc.Col([
                            html.Label("Change Severity (nt):", className="form-label"),
                            dbc.Input(
                                id="dynamic-nt",
                                type="number",
                                value=10,
                                min=1,
                                max=100,
                                step=1,
                            ),
                            html.Small("Controls how much the Pareto front shifts", className="text-muted"),
                        ], width=6),
                    ]),
                ]),
            ], className="mb-4"),
        ], id="dynamic-params-div", style={"display": "none"}),

    ], fluid=True)

def create_nsga2_params():
    """Create simplified NSGA-II parameter controls."""
    return dbc.Card([
        dbc.CardHeader("NSGA-II Parameters"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Crossover Probability:", className="form-label"),
                    dbc.Input(
                        id="nsga2-crossover-prob",
                        type="number",
                        value=0.9,
                        min=0.0,
                        max=1.0,
                        step=0.1
                    )
                ], width=6),
                dbc.Col([
                    html.Label("Mutation Probability:", className="form-label"),
                    dbc.Input(
                        id="nsga2-mutation-prob",
                        type="number",
                        value=0.1,
                        min=0.0,
                        max=1.0,
                        step=0.1
                    )
                ], width=6)
            ])
        ])
    ], className="mb-4")