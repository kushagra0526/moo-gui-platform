"""
Visualization callbacks for real-time plotting and monitoring
"""

from dash import Input, Output, State, callback_context, no_update
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

def register_visualization_callbacks(app):
    """Register visualization callbacks."""
    
    @app.callback(
        Output("main-visualization", "figure"),
        [Input("optimization-results", "data"),
         Input("plot-type-select", "value"),
         Input("x-axis-objective", "value"),
         Input("y-axis-objective", "value")],
        prevent_initial_call=True
    )
    def update_main_visualization(results_data, plot_type, x_axis, y_axis):
        """Update the main visualization plot."""
        if not results_data or not results_data.get("pareto_front"):
            return create_empty_plot()

        pareto_front = np.array(results_data["pareto_front"])
        population   = np.array(results_data.get("population_objectives", []))

        if plot_type == "pareto_2d":
            return create_2d_pareto_plot(pareto_front, population, x_axis, y_axis)
        elif plot_type == "pareto_3d":
            return create_3d_pareto_plot(pareto_front, population)
        elif plot_type == "parallel":
            return create_parallel_coordinates_plot(pareto_front)
        elif plot_type == "convergence":
            return create_convergence_plot(results_data.get("convergence_history", []))
        elif plot_type == "evolution":
            return create_evolution_plot(results_data.get("evolution_history", []))

        return create_empty_plot()
    
    @app.callback(
        Output("convergence-plot", "figure"),
        [Input("optimization-results", "data")],
        prevent_initial_call=True
    )
    def update_convergence_plot(results_data):
        """Update convergence metrics plot."""
        if not results_data or not results_data.get("convergence_history"):
            return create_empty_convergence_plot()
        
        history = results_data["convergence_history"]
        
        # Extract data from history list of dicts
        generations = [h["generation"] for h in history]
        hypervolumes = [h["hypervolume"] for h in history]
        best_f = [h.get("best_f", 0.0) for h in history]
        
        fig = go.Figure()
        
        # Add hypervolume trace
        fig.add_trace(go.Scatter(
            x=generations,
            y=hypervolumes,
            mode='lines+markers',
            name='Hypervolume',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))
        
        # Add best objective value trace
        fig.add_trace(go.Scatter(
            x=generations,
            y=best_f,
            mode='lines+markers',
            name='Best Objective',
            yaxis='y2',
            line=dict(color='red', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title="Convergence Metrics",
            xaxis_title="Generation",
            yaxis_title="Hypervolume",
            yaxis2=dict(
                title="Best Objective Value",
                overlaying='y',
                side='right'
            ),
            template="plotly_white",
            showlegend=True,
            hovermode='x unified'
        )
        
        return fig
    
    @app.callback(
        Output("diversity-plot", "figure"),
        [Input("optimization-results", "data")],
        prevent_initial_call=True
    )
    def update_diversity_plot(results_data):
        """Update diversity metrics plot."""
        if not results_data or not results_data.get("diversity_history"):
            return create_empty_diversity_plot()
        
        history = results_data["diversity_history"]
        
        # Extract data from history list of dicts
        generations = [h["generation"] for h in history]
        spreads = [h["spread"] for h in history]
        spacings = [h["spacing"] for h in history]
        
        fig = go.Figure()
        
        # Add spread trace
        fig.add_trace(go.Scatter(
            x=generations,
            y=spreads,
            mode='lines+markers',
            name='Spread',
            line=dict(color='green', width=2),
            marker=dict(size=6)
        ))
        
        # Add spacing trace
        fig.add_trace(go.Scatter(
            x=generations,
            y=spacings,
            mode='lines+markers',
            name='Spacing',
            line=dict(color='orange', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title="Population Diversity",
            xaxis_title="Generation",
            yaxis_title="Diversity Measure",
            template="plotly_white",
            showlegend=True,
            hovermode='x unified'
        )
        
        return fig
    
    @app.callback(
        [Output("metric-generation", "children"),
         Output("metric-hypervolume", "children"),
         Output("metric-igd", "children"),
         Output("metric-solutions", "children")],
        [Input("optimization-results", "data")],
        prevent_initial_call=True
    )
    def update_metrics_display(results_data):
        """Update the metrics display cards."""
        if not results_data:
            return "0", "0.000", "0.000", "0"
        
        generation = results_data.get("generation", 0)
        metrics = results_data.get("metrics", {})
        
        hypervolume = metrics.get("hypervolume", 0.0)
        igd = metrics.get("igd", 0.0)
        n_solutions = metrics.get("n_solutions", 0)
        
        return (
            str(generation),
            f"{hypervolume:.3f}",
            f"{igd:.3f}",
            str(n_solutions)
        )
    
    @app.callback(
        Output("solution-inspector", "children"),
        [Input("main-visualization", "clickData")],
        [State("optimization-results", "data")],
        prevent_initial_call=True
    )
    def update_solution_inspector(click_data, results_data):
        """Update solution inspector when a point is clicked."""
        from dash import html
        import dash_bootstrap_components as dbc
        
        if not click_data or not results_data:
            return html.P("Click on a solution in the plot to inspect its details.", 
                         className="text-muted")
        
        point_index = click_data["points"][0]["pointIndex"]
        pareto_front = np.array(results_data["pareto_front"])
        
        if point_index >= len(pareto_front):
            return html.P("Invalid solution selected.", className="text-muted")
        
        solution = pareto_front[point_index]
        
        # Get additional solution info if available
        population = results_data.get("population", [])
        constraints = results_data.get("constraints", [])
        
        inspector_content = [
            html.H6(f"Solution {point_index}", className="mb-2"),
            html.Hr(),
            html.H6("Objective Values:", className="mb-1")
        ]
        
        # Add objective values
        for i, obj_val in enumerate(solution):
            inspector_content.append(
                html.P(f"f{i}: {obj_val:.6f}", className="mb-1")
            )
        
        # Add constraint violations if available
        if constraints and point_index < len(constraints):
            constraint_vals = constraints[point_index]
            if np.any(constraint_vals > 0):
                inspector_content.extend([
                    html.Hr(),
                    html.H6("Constraint Violations:", className="mb-1 text-warning")
                ])
                for i, cv in enumerate(constraint_vals):
                    if cv > 0:
                        inspector_content.append(
                            html.P(f"g{i}: {cv:.6f}", className="mb-1 text-warning")
                        )
            else:
                inspector_content.extend([
                    html.Hr(),
                    html.P("No constraint violations", className="text-success")
                ])
        
        # Add decision variables if available
        if population and point_index < len(population):
            variables = population[point_index]
            inspector_content.extend([
                html.Hr(),
                html.H6("Decision Variables:", className="mb-1")
            ])
            for i, var_val in enumerate(variables):
                inspector_content.append(
                    html.P(f"x{i}: {var_val:.6f}", className="mb-1")
                )
        
        return inspector_content

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

def create_2d_pareto_plot(pareto_front, population, x_axis=0, y_axis=1):
    """Create 2D Pareto front plot using WebGL (Scattergl) for performance."""
    fig = go.Figure()

    # Downsample population to max 300 points
    if len(population) > 0 and population.shape[1] > max(x_axis, y_axis):
        pop_ds = population[np.linspace(0, len(population)-1, min(300, len(population)), dtype=int)]
        fig.add_trace(go.Scattergl(
            x=pop_ds[:, x_axis],
            y=pop_ds[:, y_axis],
            mode='markers',
            name='Population',
            marker=dict(color='rgba(100,160,255,0.4)', size=5),
            hoverinfo='skip',
        ))

    if len(pareto_front) > 0 and pareto_front.shape[1] > max(x_axis, y_axis):
        fig.add_trace(go.Scattergl(
            x=pareto_front[:, x_axis],
            y=pareto_front[:, y_axis],
            mode='markers',
            name='Pareto Front',
            marker=dict(color='red', size=8, symbol='diamond'),
            hovertemplate=f'f{x_axis}: %{{x:.4f}}<br>f{y_axis}: %{{y:.4f}}<extra></extra>',
        ))

    fig.update_layout(
        title="2D Pareto Front",
        xaxis_title=f"Objective {x_axis}",
        yaxis_title=f"Objective {y_axis}",
        template="plotly_white",
        showlegend=True,
        uirevision="pareto-2d",   # prevents zoom reset on data update
    )
    return fig

def create_3d_pareto_plot(pareto_front, population):
    """Create 3D Pareto front plot."""
    fig = go.Figure()
    
    if len(pareto_front) > 0 and pareto_front.shape[1] >= 3:
        # Add population points
        if len(population) > 0 and population.shape[1] >= 3:
            fig.add_trace(go.Scatter3d(
                x=population[:, 0],
                y=population[:, 1],
                z=population[:, 2],
                mode='markers',
                name='Population',
                marker=dict(
                    color='lightblue',
                    size=4,
                    opacity=0.6
                )
            ))
        
        # Add Pareto front
        fig.add_trace(go.Scatter3d(
            x=pareto_front[:, 0],
            y=pareto_front[:, 1],
            z=pareto_front[:, 2],
            mode='markers',
            name='Pareto Front',
            marker=dict(
                color='red',
                size=6,
                symbol='diamond'
            )
        ))
    
    fig.update_layout(
        title="3D Pareto Front",
        scene=dict(
            xaxis_title="Objective 1",
            yaxis_title="Objective 2",
            zaxis_title="Objective 3"
        ),
        template="plotly_white"
    )
    
    return fig

def create_parallel_coordinates_plot(pareto_front):
    """Create parallel coordinates plot for high-dimensional objectives."""
    if len(pareto_front) == 0:
        return create_empty_plot()
    
    n_objectives = pareto_front.shape[1]
    
    dimensions = []
    for i in range(n_objectives):
        dimensions.append(dict(
            label=f"Objective {i}",
            values=pareto_front[:, i]
        ))
    
    fig = go.Figure(data=go.Parcoords(
        line=dict(color=np.arange(len(pareto_front)),
                  colorscale='Viridis',
                  showscale=True),
        dimensions=dimensions
    ))
    
    fig.update_layout(
        title="Parallel Coordinates Plot",
        template="plotly_white"
    )
    
    return fig

def create_convergence_plot(convergence_history):
    """Create convergence plot."""
    fig = go.Figure()
    
    if convergence_history:
        generations = list(range(len(convergence_history)))
        fig.add_trace(go.Scatter(
            x=generations,
            y=convergence_history,
            mode='lines+markers',
            name='Convergence',
            line=dict(color='blue')
        ))
    
    fig.update_layout(
        title="Convergence History",
        xaxis_title="Generation",
        yaxis_title="Convergence Metric",
        template="plotly_white"
    )
    
    return fig

def create_evolution_plot(evolution_history):
    """Create population evolution animation plot."""
    # This would create an animated plot showing how the population evolves
    # For now, return a simple plot
    return create_empty_plot()

def create_empty_convergence_plot():
    """Create empty convergence plot."""
    fig = go.Figure()
    fig.update_layout(
        title="Convergence Metrics",
        xaxis_title="Generation",
        yaxis_title="Metric Value",
        template="plotly_white"
    )
    return fig

def create_empty_diversity_plot():
    """Create empty diversity plot."""
    fig = go.Figure()
    fig.update_layout(
        title="Population Diversity",
        xaxis_title="Generation",
        yaxis_title="Diversity Measure",
        template="plotly_white"
    )
    return fig