"""
Results and export callbacks
"""

import csv
import io
import json

from dash import Input, Output, State, dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np

from ..layouts.results import (
    create_preference_content, create_ranking_content, create_tradeoff_content
)


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
    )
    def update_results_summary(results_data):
        """Populate the results-page charts and metric pills."""
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
            conv_fig.add_trace(go.Scatter(
                x=[h["generation"] for h in history], y=[h["hypervolume"] for h in history],
                mode="lines+markers", name="Hypervolume", line=dict(color="blue", width=2)
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
    )
    def update_solutions_table(results_data):
        """One row per Pareto-optimal solution: objective values, then decision variables."""
        header, rows = _pareto_rows(results_data)
        columns = [{"name": "Solution ID", "id": "id"}] + [
            {"name": h, "id": h, "type": "numeric", "format": {"specifier": ".4f"}} for h in header[1:]
        ]
        return [dict(zip(header, r)) for r in rows], columns

    @app.callback(
        Output("decision-content", "children"),
        [Input("decision-tabs", "active_tab")],
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
        [State("app-state", "data"), State("algo-config", "data")],
        prevent_initial_call=True
    )
    def generate_python_code(n_clicks, app_state, algo_config):
        """Generate Python code for the current experiment."""
        return generate_pymoo_code(app_state, algo_config), True

    # Header "Save" — available on every page
    @app.callback(
        Output("download", "data"),
        Input("btn-save-experiment", "n_clicks"),
        State("app-state", "data"),
        State("algo-config", "data"),
        State("optimization-results", "data"),
        prevent_initial_call=True,
    )
    def save_experiment(_n, app_state, algo_config, results_data):
        """Download the problem, algorithm settings and latest results as JSON."""
        return _experiment_download("experiment", "", app_state, algo_config, results_data, "json")

    # Results page "Export"
    @app.callback(
        Output("download", "data", allow_duplicate=True),
        Input("btn-export-results", "n_clicks"),
        State("export-format", "value"),
        State("experiment-name", "value"),
        State("experiment-description", "value"),
        State("app-state", "data"),
        State("algo-config", "data"),
        State("optimization-results", "data"),
        prevent_initial_call=True,
    )
    def export_results(_n, fmt, name, description, app_state, algo_config, results_data):
        """Download the Pareto set as CSV or the whole experiment as JSON."""
        return _experiment_download(name or "experiment", description or "",
                                    app_state, algo_config, results_data, fmt)

    @app.callback(
        Output("objective-weights-container", "children"),
        [Input("optimization-results", "data")],
    )
    def create_objective_weights(results_data):
        """Create objective weight controls for preference articulation."""
        if not results_data or not results_data.get("pareto_front"):
            return html.P("No objectives available", className="text-muted")

        n_objectives = np.array(results_data["pareto_front"]).shape[1]
        return [
            dbc.Row([
                dbc.Col([html.Label(f"Objective {i}:", className="form-label")], width=6),
                dbc.Col([dbc.Input(id=f"weight-obj-{i}", type="number", value=1.0 / n_objectives,
                                   min=0.0, max=1.0, step=0.1)], width=6)
            ], className="mb-2")
            for i in range(n_objectives)
        ]

    @app.callback(
        Output("aspiration-levels-container", "children"),
        [Input("optimization-results", "data")],
    )
    def create_aspiration_levels(results_data):
        """Create aspiration level controls."""
        if not results_data or not results_data.get("pareto_front"):
            return html.P("No objectives available", className="text-muted")

        pareto_front = np.array(results_data["pareto_front"])
        min_vals = np.min(pareto_front, axis=0)
        max_vals = np.max(pareto_front, axis=0)
        return [
            dbc.Row([
                dbc.Col([html.Label(f"Objective {i}:", className="form-label")], width=6),
                dbc.Col([dbc.Input(id=f"aspiration-obj-{i}", type="number", value=float(min_vals[i]),
                                   min=float(min_vals[i]), max=float(max_vals[i]),
                                   step=(max_vals[i] - min_vals[i]) / 100 or None)], width=6)
            ], className="mb-2")
            for i in range(pareto_front.shape[1])
        ]


def _pareto_rows(results_data):
    """Header and rows of the Pareto set: id, f0..fm, x0..xn."""
    pf = (results_data or {}).get("pareto_front") or []
    ps = (results_data or {}).get("pareto_set") or []
    n_obj = len(pf[0]) if pf else 2
    n_var = len(ps[0]) if ps else 0
    header = ["id"] + [f"f{j}" for j in range(n_obj)] + [f"x{j}" for j in range(n_var)]
    rows = [[i] + list(f) + (list(ps[i]) if i < len(ps) else []) for i, f in enumerate(pf)]
    return header, rows


def _experiment_download(name, description, app_state, algo_config, results_data, fmt):
    """dcc.Download payload: Pareto set as CSV, or everything as JSON."""
    safe_name = "".join(c for c in name if c.isalnum() or c in "-_") or "experiment"
    if fmt == "csv":
        header, rows = _pareto_rows(results_data)
        buf = io.StringIO()
        csv.writer(buf).writerows([header] + rows)
        return dcc.send_string(buf.getvalue(), f"{safe_name}_pareto.csv")
    payload = {
        "name": name,
        "description": description,
        "problem": {k: v for k, v in (app_state or {}).items() if not k.startswith(("optimization_", "current_"))},
        "algorithm": algo_config or {},
        "results": results_data or {},
    }
    return dcc.send_string(json.dumps(payload, indent=2), f"{safe_name}.json")


def generate_pymoo_code(app_state, algo_config=None):
    """Generate a standalone pymoo script that reproduces the current experiment."""
    state = app_state or {}
    cfg = algo_config or {}
    objectives = [(e.strip(), d) for e, d in zip(state.get("obj_expressions") or [],
                                                  (state.get("obj_directions") or []) + ["minimize"] * 99)
                  if e and e.strip()]
    if len(objectives) < 2 or not state.get("var_names"):
        return "# Define at least one variable and two objectives on the Problem page first."

    n_var = len(state["var_names"])
    types = (state.get("var_types") or []) + ["continuous"] * n_var
    lowers = [0.0 if types[i] == "binary" else float((state.get("var_lowers") or [0] * n_var)[i] or 0)
              for i in range(n_var)]
    uppers = [1.0 if types[i] == "binary" else float((state.get("var_uppers") or [1] * n_var)[i] or 0)
              for i in range(n_var)]
    int_idx = [i for i in range(n_var) if types[i] in ("integer", "binary")]
    constraints = [(e.strip(), t or "ineq") for e, t in zip(state.get("constraint_expressions") or [],
                                                           (state.get("constraint_types") or []) + ["ineq"] * 99)
                   if e and e.strip()]

    f_lines = [f"            -({e}),  # maximize" if d == "maximize" else f"            {e},"
               for e, d in objectives]
    g_lines = [f"            abs({e}) - 1e-4,  # equality" if t == "eq" else f"            {e},"
               for e, t in constraints]
    mut = cfg.get("mutation_prob")

    code = [
        "#!/usr/bin/env python3",
        f'"""Generated pymoo script for experiment: {state.get("experiment_name", "experiment")}"""',
        "",
        "import numpy as np",
        "from numpy import (sin, cos, tan, arcsin, arccos, arctan, sinh, cosh, tanh, exp, log, log10, log2,",
        "                   sqrt, abs, floor, ceil, round, sign, sum, mean, max, min, std, var, square, pi, e)",
        "from numpy import power as pow",
        "from pymoo.algorithms.moo.nsga2 import NSGA2",
        "from pymoo.core.problem import ElementwiseProblem",
        *(["from pymoo.core.repair import Repair"] if int_idx else []),
        "from pymoo.operators.crossover.sbx import SBX",
        "from pymoo.operators.mutation.pm import PM",
        "from pymoo.optimize import minimize",
        "",
        "",
        "class UserProblem(ElementwiseProblem):",
        "    def __init__(self):",
        f"        super().__init__(n_var={n_var}, n_obj={len(objectives)}, n_ieq_constr={len(constraints)},",
        f"                         xl=np.array({lowers}), xu=np.array({uppers}))",
        "",
        "    def _evaluate(self, x, out, *args, **kwargs):",
        "        out['F'] = [",
        *f_lines,
        "        ]",
    ]
    if constraints:
        code += ["        out['G'] = [  # feasible when <= 0", *g_lines, "        ]"]
    if int_idx:
        code += [
            "",
            "",
            "class RoundIntegers(Repair):",
            "    def _do(self, problem, X, **kwargs):",
            f"        X[:, {int_idx}] = np.round(X[:, {int_idx}])",
            "        return X",
        ]
    code += [
        "",
        "",
        "algorithm = NSGA2(",
        f"    pop_size={int(cfg.get('population_size') or 100)},",
        f"    crossover=SBX(prob={cfg.get('crossover_prob', 0.9)}, eta=15),",
        f"    mutation=PM({'prob=' + str(mut) + ', ' if mut is not None else ''}eta=20),",
        "    eliminate_duplicates=True,",
        *(["    repair=RoundIntegers(),"] if int_idx else []),
        ")",
        "",
        "res = minimize(UserProblem(), algorithm,",
        f"               ('n_gen', {int(cfg.get('max_generations') or 250)}),",
        f"               seed={cfg.get('random_seed', 42)}, verbose=True)",
        "",
        "print(f'Pareto solutions: {len(res.F)}')",
        "print(res.F)  # maximized objectives appear negated",
    ]
    return "\n".join(code)
