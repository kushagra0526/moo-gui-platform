"""
Algorithm configuration callbacks
"""

from dash import Input, Output, State, callback_context, no_update
from ..layouts.algorithm_config import create_nsga2_params

def register_algorithm_callbacks(app):
    """Register algorithm configuration callbacks."""
    
    @app.callback(
        Output("algorithm-description", "children"),
        [Input("algorithm-select", "value")],
        prevent_initial_call=True
    )
    def update_algorithm_description(algorithm):
        """Update algorithm description based on selection."""
        from dash import html
        
        return html.Div([
            html.P("NSGA-II (Non-dominated Sorting Genetic Algorithm II)", className="fw-bold mt-3 mb-2"),
            html.Ul([
                html.Li("Fast non-dominated sorting"),
                html.Li("Crowding distance for diversity preservation"),
                html.Li("Suitable for multi-objective optimization")
            ], className="mb-0")
        ])
    
    @app.callback(
        Output("algorithm-specific-params", "children"),
        [Input("algorithm-select", "value")],
        prevent_initial_call=True
    )
    def update_algorithm_params(algorithm):
        """Update algorithm-specific parameter controls."""
        return create_nsga2_params()

    # Show/hide dynamic params panel based on problem-type store
    @app.callback(
        Output("dynamic-params-div", "style"),
        Input("app-state", "data"),
        Input("algo-config", "data"),
        prevent_initial_call=True,
    )
    def toggle_dynamic_params(app_state, algo_config):
        is_dynamic = False
        if algo_config and algo_config.get("problem_type") == "dynamic":
            is_dynamic = True
        elif app_state and app_state.get("problem_type") == "dynamic":
            is_dynamic = True
        return {"display": "block"} if is_dynamic else {"display": "none"}