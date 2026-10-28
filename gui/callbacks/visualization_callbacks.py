"""
Visualization callbacks for real-time plotting and monitoring
"""

from dash import Input, Output, State, html
import plotly.graph_objects as go
import numpy as np

from ..layouts.visualization import (
    create_empty_plot, create_empty_convergence_plot, create_empty_diversity_plot
)


def register_visualization_callbacks(app):
    """Register visualization callbacks."""

    @app.callback(
        Output("main-visualization", "figure"),
        [Input("optimization-results", "data"),
         Input("plot-type-select", "value"),
         Input("x-axis-objective", "value"),
         Input("y-axis-objective", "value")],
    )
    def update_main_visualization(results_data, plot_type, x_axis, y_axis):
        """Update the main visualization plot."""
        if not results_data or not results_data.get("pareto_front"):
            return create_empty_plot()

        pareto_front = np.array(results_data["pareto_front"])
        population   = np.array(results_data.get("population_objectives", []))

        if plot_type == "pareto_3d":
            return create_3d_pareto_plot(pareto_front, population)
        if plot_type == "parallel":
            return create_parallel_coordinates_plot(pareto_front)
        if plot_type == "convergence":
            return create_convergence_plot(results_data.get("convergence_history", []))
        # dbc.Select returns strings once the user picks a value
        return create_2d_pareto_plot(pareto_front, population, int(x_axis or 0), int(y_axis or 1))

    @app.callback(
        Output("convergence-plot", "figure"),
        [Input("optimization-results", "data")],
    )
    def update_convergence_plot(results_data):
        """Update convergence metrics plot."""
        if not results_data or not results_data.get("convergence_history"):
            return create_empty_convergence_plot()

        history = results_data["convergence_history"]
        generations = [h["generation"] for h in history]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=generations, y=[h["hypervolume"] for h in history],
            mode='lines+markers', name='Hypervolume',
            line=dict(color='blue', width=2), marker=dict(size=6)
        ))
        fig.add_trace(go.Scatter(
            x=generations, y=[h.get("best_f", 0.0) for h in history],
            mode='lines+markers', name='Best Objective 1', yaxis='y2',
            line=dict(color='red', width=2), marker=dict(size=6)
        ))
        fig.update_layout(
            title="Convergence Metrics",
            xaxis_title="Generation",
            yaxis_title="Hypervolume",
            yaxis2=dict(title="Best Objective 1 Value", overlaying='y', side='right'),
            template="plotly_white",
            showlegend=True,
            hovermode='x unified'
        )
        return fig

    @app.callback(
        Output("diversity-plot", "figure"),
        [Input("optimization-results", "data")],
    )
    def update_diversity_plot(results_data):
        """Update diversity metrics plot."""
        if not results_data or not results_data.get("diversity_history"):
            return create_empty_diversity_plot()

        history = results_data["diversity_history"]
        generations = [h["generation"] for h in history]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=generations, y=[h["spread"] for h in history],
            mode='lines+markers', name='Spread',
            line=dict(color='green', width=2), marker=dict(size=6)
        ))
        fig.add_trace(go.Scatter(
            x=generations, y=[h["spacing"] for h in history],
            mode='lines+markers', name='Spacing',
            line=dict(color='orange', width=2), marker=dict(size=6)
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
         Output("metric-solutions", "children")],
        [Input("optimization-results", "data")],
    )
    def update_metrics_display(results_data):
        """Update the metrics display cards."""
        if not results_data:
            return "0", "0.000", "0"
        metrics = results_data.get("metrics", {})
        return (
            str(results_data.get("generation", 0)),
            f"{metrics.get('hypervolume', 0.0):.3f}",
            str(metrics.get("n_solutions", 0)),
        )

    @app.callback(
        Output("solution-inspector", "children"),
        [Input("main-visualization", "clickData")],
        [State("optimization-results", "data")],
        prevent_initial_call=True
    )
    def update_solution_inspector(click_data, results_data):
        """Show objectives and decision variables of a clicked Pareto point."""
        point = (click_data or {}).get("points", [{}])[0]
        # Only Pareto-front markers carry their row index in customdata
        index = point.get("customdata")
        if isinstance(index, list):
            index = index[0] if index else None
        if index is None or not results_data or index >= len(results_data.get("pareto_front", [])):
            return html.P("Click a red Pareto-front point in the plot to inspect it.",
                          className="text-muted")

        content = [
            html.H6(f"Solution {index}", className="mb-2"),
            html.Hr(),
            html.H6("Objective Values:", className="mb-1"),
        ]
        content += [html.P(f"f{i}: {v:.6f}", className="mb-1")
                    for i, v in enumerate(results_data["pareto_front"][index])]

        pareto_set = results_data.get("pareto_set") or []
        if index < len(pareto_set):
            content += [html.Hr(), html.H6("Decision Variables:", className="mb-1")]
            content += [html.P(f"x{i}: {v:.6f}", className="mb-1")
                        for i, v in enumerate(pareto_set[index])]
        return content


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
            customdata=list(range(len(pareto_front))),  # plain list: dcc.Graph can't index packed numpy arrays
            mode='markers',
            name='Pareto Front',
            marker=dict(color='red', size=8, symbol='diamond'),
            hovertemplate=f'f{x_axis}: %{{x:.4f}}<br>f{y_axis}: %{{y:.4f}}<extra></extra>',
        ))

    fig.update_layout(
        title="2D Pareto Front",
        xaxis_title=f"Objective {x_axis + 1}",
        yaxis_title=f"Objective {y_axis + 1}",
        template="plotly_white",
        showlegend=True,
        uirevision="pareto-2d",   # prevents zoom reset on data update
    )
    return fig


def create_3d_pareto_plot(pareto_front, population):
    """Create 3D Pareto front plot."""
    fig = go.Figure()

    if len(pareto_front) > 0 and pareto_front.shape[1] >= 3:
        if len(population) > 0 and population.shape[1] >= 3:
            fig.add_trace(go.Scatter3d(
                x=population[:, 0], y=population[:, 1], z=population[:, 2],
                mode='markers', name='Population',
                marker=dict(color='lightblue', size=4, opacity=0.6)
            ))
        fig.add_trace(go.Scatter3d(
            x=pareto_front[:, 0], y=pareto_front[:, 1], z=pareto_front[:, 2],
            customdata=list(range(len(pareto_front))),  # plain list: dcc.Graph can't index packed numpy arrays
            mode='markers', name='Pareto Front',
            marker=dict(color='red', size=6, symbol='diamond')
        ))
    else:
        fig.add_annotation(text="3D view needs at least 3 objectives", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="gray"))

    fig.update_layout(
        title="3D Pareto Front",
        scene=dict(xaxis_title="Objective 1", yaxis_title="Objective 2", zaxis_title="Objective 3"),
        template="plotly_white"
    )
    return fig


def create_parallel_coordinates_plot(pareto_front):
    """Create parallel coordinates plot for high-dimensional objectives."""
    if len(pareto_front) == 0:
        return create_empty_plot()

    fig = go.Figure(data=go.Parcoords(
        line=dict(color=np.arange(len(pareto_front)), colorscale='Viridis', showscale=True),
        dimensions=[dict(label=f"Objective {i}", values=pareto_front[:, i])
                    for i in range(pareto_front.shape[1])]
    ))
    fig.update_layout(title="Parallel Coordinates Plot", template="plotly_white")
    return fig


def create_convergence_plot(convergence_history):
    """Hypervolume per generation."""
    fig = go.Figure()
    if convergence_history:
        fig.add_trace(go.Scatter(
            x=[h["generation"] for h in convergence_history],
            y=[h["hypervolume"] for h in convergence_history],
            mode='lines+markers',
            name='Hypervolume',
            line=dict(color='blue')
        ))
    fig.update_layout(
        title="Convergence History",
        xaxis_title="Generation",
        yaxis_title="Hypervolume",
        template="plotly_white"
    )
    return fig
