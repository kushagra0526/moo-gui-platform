"""
Optimization execution callbacks — no duplicate outputs.

app-state.data            → merged into update_optimization_progress
                            (control_optimization writes it too, so we
                             split: control writes opt-control-state store,
                             progress merges both into app-state)

Strategy:
  opt-control-store  (session) — written ONLY by control_optimization
  app-state.data               — written ONLY by update_optimization_progress
  optimization-results.data    — written ONLY by update_optimization_progress
  optimization-interval.disabled — written ONLY by control_optimization
  btn-run/stop disabled        — written ONLY by control_optimization
  algo-config store            — written ONLY by update_algorithm_state
"""

import time

from dash import Input, Output, State, callback_context, no_update
from ..core.state_manager import (
    Variable, Objective, Constraint, ProblemDefinition, AlgorithmConfig, ExperimentState
)


def register_optimization_callbacks(app):

    # ------------------------------------------------------------------
    # 1. control_optimization
    #    Outputs: btn states, interval disabled, opt-control-store
    #    Does NOT touch app-state or optimization-results
    # ------------------------------------------------------------------
    @app.callback(
        Output("btn-run-optimization",  "disabled"),
        Output("btn-stop-optimization", "disabled"),
        Output("optimization-interval", "disabled"),
        Output("opt-control-store",     "data"),
        Input("btn-run-optimization",  "n_clicks"),
        Input("btn-stop-optimization", "n_clicks"),
        State("app-state",             "data"),
        State("algo-config",           "data"),
        prevent_initial_call=True,
    )
    def control_optimization(run_clicks, stop_clicks, current_state, algo_config):
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "btn-run-optimization":
            if app.optimization_engine.is_running:
                return True, False, False, no_update

            merged = {}
            if current_state:
                merged.update(current_state)
            if algo_config:
                merged.update(algo_config)

            merged.update({
                "optimization_running":   True,
                "optimization_completed": False,
                "current_generation":     0,
                "run_id":                 time.time(),
            })
            # Stay idle when the problem is incomplete or a formula is rejected (the Problem page shows why)
            if not start_optimization_process(app, merged):
                return False, True, True, {"cmd": "idle"}
            return True, False, False, {"cmd": "start", "state": merged}

        if button_id == "btn-stop-optimization":
            app.optimization_engine.stop_optimization()
            return False, True, True, {"cmd": "stop"}

        return no_update, no_update, no_update, no_update

    # ------------------------------------------------------------------
    # 2. update_optimization_progress
    #    Outputs: optimization-results, app-state  (SOLE writers)
    #    Reads opt-control-store to know what control_optimization did
    # ------------------------------------------------------------------
    @app.callback(
        Output("optimization-results", "data"),
        Output("app-state",            "data"),
        Output("optimization-interval","disabled", allow_duplicate=True),
        Output("btn-run-optimization", "disabled", allow_duplicate=True),
        Output("btn-stop-optimization","disabled", allow_duplicate=True),
        Input("optimization-interval", "n_intervals"),
        State("app-state",             "data"),
        State("opt-control-store",     "data"),
        prevent_initial_call=True,
    )
    def update_optimization_progress(n_intervals, current_state, control_store):
        engine_running = app.optimization_engine.is_running
        NO = (no_update, no_update, no_update, no_update, no_update)

        # Adopt the run control_optimization started, once — even if it already finished before this first tick
        if control_store:
            cmd = control_store.get("cmd")
            started = control_store.get("state") or {}
            if cmd == "start" and (current_state or {}).get("run_id") != started.get("run_id"):
                current_state = started
            elif cmd == "stop":
                new_state = (current_state or {}).copy()
                new_state.update({"optimization_running": False, "optimization_completed": False})
                # disable interval, re-enable Run
                return no_update, new_state, True, False, True

        if not current_state or not current_state.get("optimization_running"):
            # Stale state — disable interval and re-enable Run
            if not engine_running:
                return no_update, no_update, True, False, True
            return NO

        current_result = app.optimization_engine.current_result

        # Engine finished
        if not engine_running:
            new_state = current_state.copy()
            new_state["optimization_running"] = False
            if not app.optimization_engine.stop_requested:
                new_state["optimization_completed"] = True
                new_state["runs_completed"] = new_state.get("runs_completed", 0) + 1
            if current_result is not None:
                return _build_results_data(current_result, app), new_state, True, False, True
            return no_update, new_state, True, False, True

        # Engine still running
        if current_result is None:
            return NO

        results_data = _build_results_data(current_result, app)
        new_state = current_state.copy()
        new_state["current_generation"] = current_result.generation
        return results_data, new_state, no_update, no_update, no_update

    # ------------------------------------------------------------------
    # 3. update_algorithm_state
    #    Writes ONLY algo-config store (not app-state)
    # ------------------------------------------------------------------
    @app.callback(
        Output("algo-config", "data"),
        Input("population-size",      "value"),
        Input("max-generations",      "value"),
        Input("random-seed",          "value"),
        Input("nsga2-crossover-prob", "value"),
        Input("nsga2-mutation-prob",  "value"),
        State("algo-config",          "data"),
    )
    def update_algorithm_state(pop_size, max_gen, seed, cx_prob, mut_prob, current):
        cfg = current.copy() if current else {}
        cfg.update({
            "algorithm":       "nsga2",
            "population_size": pop_size or 100,
            "max_generations": max_gen  or 250,
            "random_seed":     seed if seed is not None else 42,
            "crossover_prob":  cx_prob if cx_prob is not None else 0.9,
            "mutation_prob":   mut_prob,  # None → engine uses 1/n_var
        })
        return cfg


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def start_optimization_process(app, state):
    """Start a run; returns False when the problem is incomplete or a formula is rejected."""
    experiment = create_experiment_from_state(state)
    if experiment is None:
        return False
    try:
        app.optimization_engine.run_optimization(experiment)
    except (ValueError, RuntimeError) as e:
        print(f"Optimization not started: {e}")
        return False
    return True


def _build_results_data(current_result, app):
    """Serialize an OptimizationResult into a JSON-safe dict."""
    results_data = {
        "generation":            current_result.generation,
        "pareto_front":          current_result.pareto_front.tolist(),
        "pareto_set":            current_result.pareto_set.tolist(),
        "population_objectives": current_result.objectives.tolist(),
        "population":            current_result.population.tolist(),
        "metrics":               current_result.metrics,
        "algorithm_info":        current_result.algorithm_info,
        "convergence_history":   app.optimization_engine.convergence_history,
        "diversity_history":     app.optimization_engine.diversity_history,
    }
    if current_result.constraints is not None:
        results_data["constraints"] = current_result.constraints.tolist()
    return results_data


def create_experiment_from_state(state):
    """Build ExperimentState from app-state. Returns None if problem not defined."""
    var_names        = state.get("var_names") or []
    var_types        = state.get("var_types") or []
    var_lowers       = state.get("var_lowers") or []
    var_uppers       = state.get("var_uppers") or []
    obj_names        = state.get("obj_names") or []
    obj_directions   = state.get("obj_directions") or []
    obj_expressions  = state.get("obj_expressions") or []
    constraint_names = state.get("constraint_names") or []
    constraint_types = state.get("constraint_types") or []
    constraint_exprs = state.get("constraint_expressions") or []

    # Require at least 1 variable and 2 objectives — no silent fallback
    if not var_names or len(var_names) == 0:
        return None
    if not obj_expressions or len(obj_expressions) < 2:
        return None

    variables = []
    for i in range(len(var_names)):
        variables.append(Variable(
            name=var_names[i] or f"x{i}",
            type=var_types[i] if i < len(var_types) else "continuous",
            lower_bound=float(var_lowers[i]) if i < len(var_lowers) and var_lowers[i] is not None else 0.0,
            upper_bound=float(var_uppers[i]) if i < len(var_uppers) and var_uppers[i] is not None else 1.0,
        ))

    objectives = []
    for i in range(len(obj_expressions)):
        expr = obj_expressions[i]
        if not expr or not str(expr).strip():
            continue
        objectives.append(Objective(
            name=obj_names[i] if i < len(obj_names) and obj_names[i] else f"objective_{i}",
            direction=obj_directions[i] if i < len(obj_directions) else "minimize",
            expression=str(expr).strip(),
        ))

    if len(objectives) < 2:
        return None

    constraints = []
    for i, expr in enumerate(constraint_exprs):
        if expr and str(expr).strip():
            constraints.append(Constraint(
                name=constraint_names[i] if i < len(constraint_names) and constraint_names[i] else f"g{i}",
                type=constraint_types[i] if i < len(constraint_types) and constraint_types[i] else "ineq",
                expression=str(expr).strip(),
            ))

    problem = ProblemDefinition(
        variables=variables,
        objectives=objectives,
        constraints=constraints,
        problem_type=state.get("problem_type", "static"),
    )

    algorithm = AlgorithmConfig(
        algorithm=state.get("algorithm", "nsga2"),
        population_size=int(state.get("population_size") or 100),
        max_generations=int(state.get("max_generations") or 250),
        random_seed=int(state["random_seed"]) if state.get("random_seed") is not None else 42,
        parameters={
            "crossover_prob": state.get("crossover_prob", 0.9), "crossover_eta": 15,
            "mutation_eta": 20,
            # Leave mutation_prob out when unset so the engine uses 1/n_var
            **({"mutation_prob": state["mutation_prob"]} if state.get("mutation_prob") is not None else {}),
        },
        many_objective_options=[], dynamic_options=[],
    )

    return ExperimentState(
        name=state.get("experiment_name", "experiment"),
        description="",
        problem=problem, algorithm=algorithm,
        created_at="", modified_at="",
    )
