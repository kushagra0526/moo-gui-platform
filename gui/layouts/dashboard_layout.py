"""
Dashboard layout - Overview and quick stats
"""

from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

def create_dashboard_layout():
    """Create a modern dashboard with overview statistics."""
    
    return html.Div([
        # Welcome section
        html.Div([
            html.H2("Dashboard", className="section-title"),
            html.P("Welcome to your optimization workspace", className="section-description"),
        ], className="mb-4"),
        
        # Quick stats cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-project-diagram fa-2x text-primary mb-3"),
                            html.H3("0", className="metric-value", id="total-projects"),
                            html.P("Total Projects", className="metric-label"),
                        ], className="text-center")
                    ])
                ], className="metric-card shadow")
            ], width=12, md=3, className="mb-3"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-chart-line fa-2x text-success mb-3"),
                            html.H3("0", className="metric-value", id="completed-runs"),
                            html.P("Completed Runs", className="metric-label"),
                        ], className="text-center")
                    ])
                ], className="metric-card shadow")
            ], width=12, md=3, className="mb-3"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-clock fa-2x text-warning mb-3"),
                            html.H3("0", className="metric-value", id="active-runs"),
                            html.P("Active Runs", className="metric-label"),
                        ], className="text-center")
                    ])
                ], className="metric-card shadow")
            ], width=12, md=3, className="mb-3"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-database fa-2x text-info mb-3"),
                            html.H3("0", className="metric-value", id="total-solutions"),
                            html.P("Total Solutions", className="metric-label"),
                        ], className="text-center")
                    ])
                ], className="metric-card shadow")
            ], width=12, md=3, className="mb-3"),
        ], className="mb-4"),
        
        # Recent activity and quick actions
        dbc.Row([
            # Recent activity
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-history me-2"),
                        "Recent Activity"
                    ]),
                    dbc.CardBody([
                        html.Div([
                            html.P("No recent activity", className="text-muted text-center py-4")
                        ], id="recent-activity-list")
                    ])
                ], className="shadow")
            ], width=12, md=6, className="mb-3"),
            
            # Quick actions
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-bolt me-2"),
                        "Quick Actions"
                    ]),
                    dbc.CardBody([
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                html.I(className="fas fa-plus-circle me-2 text-primary"),
                                "Create New Problem"
                            ], href="/problem", action=True, className="border-0 mb-2"),
                            dbc.ListGroupItem([
                                html.I(className="fas fa-cog me-2 text-success"),
                                "Configure Algorithm"
                            ], href="/algorithm", action=True, className="border-0 mb-2"),
                            dbc.ListGroupItem([
                                html.I(className="fas fa-chart-bar me-2 text-info"),
                                "View Results"
                            ], href="/results", action=True, className="border-0 mb-2"),
                            dbc.ListGroupItem([
                                html.I(className="fas fa-file-export me-2 text-warning"),
                                "Export Data"
                            ], id="quick-action-export", action=True, n_clicks=0, className="border-0"),
                        ], flush=True)
                    ])
                ], className="shadow")
            ], width=12, md=6, className="mb-3"),
        ]),
        
        # Getting started guide
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-rocket me-2"),
                        "Getting Started"
                    ]),
                    dbc.CardBody([
                        html.Ol([
                            html.Li([
                                html.Strong("Define Your Problem: "),
                                "Navigate to Problem Definition to set up variables, objectives, and constraints"
                            ], className="mb-2"),
                            html.Li([
                                html.Strong("Configure Algorithm: "),
                                "Choose and configure your optimization algorithm (NSGA-II, NSGA-III, etc.)"
                            ], className="mb-2"),
                            html.Li([
                                html.Strong("Run Optimization: "),
                                "Click the Run button to start the optimization process"
                            ], className="mb-2"),
                            html.Li([
                                html.Strong("Analyze Results: "),
                                "View visualizations and export your results"
                            ]),
                        ], className="mb-0")
                    ])
                ], className="shadow")
            ], width=12),
        ]),
        
    ], className="fade-in")
