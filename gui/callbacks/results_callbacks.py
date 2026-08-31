"""
Results and export callbacks
"""

from dash import Input, Output, State, callback_context, no_update
import pandas as pd
import json
import numpy as np

def register_results_callbacks(app):
    """Register results and export callbacks."""

    @app.callback(
        Output("results-pareto-plot",       "figure"),
        Output("results-convergence-plot",  "figure"),
        Output("results-metric-generation", "children"),
        Output("results-metric-solutions",  "children"),
        Output("results-metric-hypervolume","children"),
        Output("results-metric-status",     "children"),
        Input("optimization-results", "data"),
        prevent_initial_call=True
    )
    def update_results_summary(results_data):
        """Populate the results-page charts and metric pills."""
        import plotly.graph_objects as go
        import numpy as np

        def empty(title):
            fig = go.Figure()
            fig.update_layout(title=title, template="plotly_white")
            fig.add_annotation(text="Run optimization to see results",
                               xref="paper", yref="paper", x=0.5, y=0.5,
                               showarrow=False, font=dict(size=14, color="gray"))
            return fig

        if not results_data or not results_data.get("pareto_front"):
            return empty("Pareto Front"), empty("Convergence History"), "0", "0", "0.000", "No data"

        # --- Pareto front plot ---
        pf = np.array(results_data["pareto_front"])
        pop_obj = np.array(results_data.get("population_objectives", []))

        pareto_fig = go.Figure()
        if pop_obj.ndim == 2 and pop_obj.shape[1] >= 2:
            pareto_fig.add_trace(go.Scatter(
                x=pop_obj[:, 0], y=pop_obj[:, 1],
                mode="markers", name="Population",
                marker=dict(color="lightblue", size=5, opacity=0.6)
            ))
        if pf.ndim == 2 and pf.shape[1] >= 2:
            pareto_fig.add_trace(go.Scatter(
                x=pf[:, 0], y=pf[:, 1],
                mode="markers", name="Pareto Front",
                marker=dict(color="red", size=8, symbol="diamond")
            ))
        pareto_fig.update_layout(
            title="Pareto Front", xaxis_title="Objective 1",
            yaxis_title="Objective 2", template="plotly_white", showlegend=True
        )

        # --- Convergence plot ---
        history = results_data.get("convergence_history", [])
        conv_fig = go.Figure()
        if history:
            gens = [h["generation"] for h in history]
            hvs  = [h["hypervolume"] for h in history]
            conv_fig.add_trace(go.Scatter(
                x=gens, y=hvs, mode="lines+markers",
                name="Hypervolume", line=dict(color="blue", width=2)
            ))
        conv_fig.update_layout(
            title="Convergence History", xaxis_title="Generation",
            yaxis_title="Hypervolume", template="plotly_white"
        )

        # --- Metrics ---
        metrics = results_data.get("metrics", {})
        generation  = str(results_data.get("generation", 0))
        n_solutions = str(metrics.get("n_solutions", len(pf)))
        hypervolume = f"{metrics.get('hypervolume', 0.0):.3f}"
        status      = "Completed" if results_data.get("generation") else "Partial"

        return pareto_fig, conv_fig, generation, n_solutions, hypervolume, status

    @app.callback(
        [Output("solutions-table", "data"),
         Output("solutions-table", "columns")],
        [Input("optimization-results", "data")],
        prevent_initial_call=True
    )
    def update_solutions_table(results_data):
        """Update the solutions table with Pareto-optimal solutions."""
        if not results_data or not results_data.get("pareto_front"):
            # Return empty with default columns
            default_columns = [
                {"name": "Solution ID", "id": "id"},
                {"name": "Objective 1", "id": "f0", "type": "numeric", "format": {"specifier": ".4f"}},
                {"name": "Objective 2", "id": "f1", "type": "numeric", "format": {"specifier": ".4f"}},
                {"name": "Dominance Rank", "id": "rank", "type": "numeric"},
                {"name": "Crowding Distance", "id": "crowding", "type": "numeric", "format": {"specifier": ".4f"}},
                {"name": "Constraint Violation", "id": "cv", "type": "numeric", "format": {"specifier": ".4f"}}
            ]
            return [], default_columns
        
        pareto_front = np.array(results_data["pareto_front"])
        n_objectives = pareto_front.shape[1]
        
        # Dynamically create columns based on number of objectives
        columns = [{"name": "Solution ID", "id": "id"}]
        
        # Add objective columns dynamically
        for j in range(n_objectives):
            columns.append({
                "name": f"Objective {j+1}",
                "id": f"f{j}",
                "type": "numeric",
                "format": {"specifier": ".4f"}
            })
        
        # Add metric columns
        columns.extend([
            {"name": "Dominance Rank", "id": "rank", "type": "numeric"},
            {"name": "Crowding Distance", "id": "crowding", "type": "numeric", "format": {"specifier": ".4f"}},
            {"name": "Constraint Violation", "id": "cv", "type": "numeric", "format": {"specifier": ".4f"}}
        ])
        
        # Create table data
        table_data = []
        for i, solution in enumerate(pareto_front):
            row = {"id": i}
            
            # Add ALL objective values dynamically
            for j, obj_val in enumerate(solution):
                row[f"f{j}"] = float(obj_val) if obj_val is not None else 0.0
            
            # Add additional metrics if available
            metrics = results_data.get("solution_metrics", {})
            if "dominance_rank" in metrics and i < len(metrics["dominance_rank"]):
                row["rank"] = int(metrics["dominance_rank"][i])
            else:
                row["rank"] = 1  # All Pareto-optimal solutions have rank 1
            
            if "crowding_distance" in metrics and i < len(metrics["crowding_distance"]):
                row["crowding"] = float(metrics["crowding_distance"][i])
            else:
                row["crowding"] = 0.0
            
            if "constraint_violation" in metrics and i < len(metrics["constraint_violation"]):
                row["cv"] = float(metrics["constraint_violation"][i])
            else:
                row["cv"] = 0.0
            
            table_data.append(row)
        
        return table_data, columns
    
    @app.callback(
        Output("decision-content", "children"),
        [Input("decision-tabs", "active_tab")],
        prevent_initial_call=True
    )
    def update_decision_content(active_tab):
        """Update decision making content based on active tab."""
        if active_tab == "preferences":
            return create_preference_content()
        elif active_tab == "ranking":
            return create_ranking_content()
        elif active_tab == "tradeoff":
            return create_tradeoff_content()
        
        return []
    
    @app.callback(
        Output("generated-code", "value"),
        Output("code-collapse", "is_open"),
        [Input("btn-generate-code", "n_clicks")],
        [State("app-state", "data")],
        prevent_initial_call=True
    )
    def generate_python_code(n_clicks, app_state):
        """Generate Python code for the current experiment."""
        if not n_clicks or not app_state:
            return "", False
        
        code = generate_pymoo_code(app_state)
        return code, True
    
    @app.callback(
        Output("experiment-name", "value"),
        [Input("btn-load-experiment", "n_clicks")],
        prevent_initial_call=True
    )
    def load_experiment(n_clicks):
        """Load an experiment from file."""
        if not n_clicks:
            return no_update
        
        # In a real implementation, this would open a file dialog
        # For now, return a placeholder
        return "loaded_experiment"
    
    @app.callback(
        Output("objective-weights-container", "children"),
        [Input("optimization-results", "data")],
        prevent_initial_call=True
    )
    def create_objective_weights(results_data):
        """Create objective weight controls for preference articulation."""
        from dash import html
        import dash_bootstrap_components as dbc
        
        if not results_data or not results_data.get("pareto_front"):
            return html.P("No objectives available", className="text-muted")
        
        pareto_front = np.array(results_data["pareto_front"])
        n_objectives = pareto_front.shape[1]
        
        weight_controls = []
        for i in range(n_objectives):
            weight_controls.append(
                dbc.Row([
                    dbc.Col([
                        html.Label(f"Objective {i}:", className="form-label")
                    ], width=6),
                    dbc.Col([
                        dbc.Input(
                            id=f"weight-obj-{i}",
                            type="number",
                            value=1.0/n_objectives,
                            min=0.0,
                            max=1.0,
                            step=0.1
                        )
                    ], width=6)
                ], className="mb-2")
            )
        
        return weight_controls
    
    @app.callback(
        Output("aspiration-levels-container", "children"),
        [Input("optimization-results", "data")],
        prevent_initial_call=True
    )
    def create_aspiration_levels(results_data):
        """Create aspiration level controls."""
        from dash import html
        import dash_bootstrap_components as dbc
        
        if not results_data or not results_data.get("pareto_front"):
            return html.P("No objectives available", className="text-muted")
        
        pareto_front = np.array(results_data["pareto_front"])
        n_objectives = pareto_front.shape[1]
        
        # Calculate reasonable aspiration levels based on Pareto front
        min_vals = np.min(pareto_front, axis=0)
        max_vals = np.max(pareto_front, axis=0)
        
        aspiration_controls = []
        for i in range(n_objectives):
            aspiration_controls.append(
                dbc.Row([
                    dbc.Col([
                        html.Label(f"Objective {i}:", className="form-label")
                    ], width=6),
                    dbc.Col([
                        dbc.Input(
                            id=f"aspiration-obj-{i}",
                            type="number",
                            value=float(min_vals[i]),
                            min=float(min_vals[i]),
                            max=float(max_vals[i]),
                            step=(max_vals[i] - min_vals[i]) / 100
                        )
                    ], width=6)
                ], className="mb-2")
            )
        
        return aspiration_controls

def create_preference_content():
    """Create preference articulation interface."""
    from dash import html
    import dash_bootstrap_components as dbc
    
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
    from dash import html
    import dash_bootstrap_components as dbc
    
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
    from dash import html
    import dash_bootstrap_components as dbc
    
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

def generate_pymoo_code(app_state):
    """Generate Python code that reproduces the current experiment."""
    if not app_state:
        return "# No experiment data available"
    
    code_lines = [
        "#!/usr/bin/env python3",
        '"""',
        "Generated code for multi-objective optimization experiment",
        f"Experiment: {app_state.get('experiment_name', 'Unnamed')}",
        '"""',
        "",
        "import numpy as np",
        "from pymoo.algorithms.moo.nsga2 import NSGA2",
        "from pymoo.core.problem import Problem",
        "from pymoo.optimize import minimize",
        "from pymoo.operators.crossover.sbx import SBX",
        "from pymoo.operators.mutation.pm import PM",
        "from pymoo.operators.sampling.rnd import FloatRandomSampling",
        "",
        "class CustomProblem(Problem):",
        "    def __init__(self):",
        "        super().__init__(",
        f"            n_var={len(app_state.get('variables', []))},",
        f"            n_obj={len(app_state.get('objectives', []))},",
        f"            n_constr={len(app_state.get('constraints', []))},",
        "            xl=np.array([0.0, 0.0]),  # Lower bounds",
        "            xu=np.array([1.0, 1.0])   # Upper bounds",
        "        )",
        "",
        "    def _evaluate(self, X, out, *args, **kwargs):",
        "        # Objective functions",
        "        f1 = X[:, 0]**2 + X[:, 1]**2",
        "        f2 = (X[:, 0] - 1)**2 + (X[:, 1] - 1)**2",
        "        ",
        "        out['F'] = np.column_stack([f1, f2])",
        "",
        "# Create problem instance",
        "problem = CustomProblem()",
        "",
        "# Configure algorithm",
        "algorithm = NSGA2(",
        f"    pop_size={app_state.get('population_size', 100)},",
        "    sampling=FloatRandomSampling(),",
        "    crossover=SBX(prob=0.9, eta=15),",
        "    mutation=PM(prob=0.1, eta=20),",
        "    eliminate_duplicates=True",
        ")",
        "",
        "# Run optimization",
        "res = minimize(",
        "    problem,",
        "    algorithm,",
        f"    ('n_gen', {app_state.get('max_generations', 250)}),",
        f"    seed={app_state.get('random_seed', 42)},",
        "    verbose=True",
        ")",
        "",
        "# Print results",
        "print(f'Number of solutions: {len(res.F)}')",
        "print(f'Objective values:')",
        "print(res.F)",
        "",
        "# Plot results (optional)",
        "import matplotlib.pyplot as plt",
        "plt.figure(figsize=(8, 6))",
        "plt.scatter(res.F[:, 0], res.F[:, 1], c='red', marker='o')",
        "plt.xlabel('Objective 1')",
        "plt.ylabel('Objective 2')",
        "plt.title('Pareto Front')",
        "plt.grid(True)",
        "plt.show()"
    ]
    
    return "\n".join(code_lines)