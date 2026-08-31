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

from dash import Input, Output, State, callback_context, no_update, ALL
from ..core.state_manager import (
    StateManager, Variable, Objective, Constraint,
    ProblemDefinition, AlgorithmConfig
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
        print(f"[OPT] control_optimization triggered: {[t['prop_id'] for t in ctx.triggered]}, run={run_clicks}, stop={stop_clicks}")
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "btn-run-optimization":
            print(f"[OPT] RUN CLICKED — engine_running={app.optimization_engine.is_running}")
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
            })
            start_optimization_process(app, merged)
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

        # Sync state from control store if needed
        if control_store:
            cmd = control_store.get("cmd")
            if cmd == "start" and engine_running:
                if not current_state or not current_state.get("optimization_running"):
                    current_state = control_store.get("state", current_state or {})
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
    #    Also captures problem_type, cec2018_id, taut, nt
    # ------------------------------------------------------------------
    @app.callback(
        Output("algo-config", "data"),
        Input("population-size",  "value"),
        Input("max-generations",  "value"),
        Input("random-seed",      "value"),
        Input("algorithm-select", "value"),
        Input("problem-type",     "value"),
        Input("dynamic-taut",     "value"),
        Input("dynamic-nt",       "value"),
        State("algo-config",      "data"),
        prevent_initial_call=True,
    )
    def update_algorithm_state(pop_size, max_gen, seed, algorithm,
                               problem_type, taut, nt, current):
        cfg = current.copy() if current else {}
        cfg.update({
            "population_size": pop_size  or 100,
            "max_generations": max_gen   or 250,
            "random_seed":     seed      or 42,
            "algorithm":       algorithm or "nsga2",
            "problem_type":    problem_type or "static",
            "cec2018_id":      1,
            "taut":            int(taut) if taut else 10,
            "nt":              int(nt)   if nt   else 10,
        })
        return cfg


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def start_optimization_process(app, state):
    try:
        problem_type = state.get("problem_type", "static")
        if problem_type == "dynamic":
            _start_dynamic_optimization(app, state)
        else:
            experiment = create_experiment_from_state(state)
            if experiment is None:
                print("[OPT] No problem defined — aborting")
                return
            print(f"[OPT] Running: {len(experiment.problem.variables)} vars, "
                  f"{len(experiment.problem.objectives)} objs, "
                  f"pop={experiment.algorithm.population_size}, "
                  f"gen={experiment.algorithm.max_generations}")
            app.optimization_engine.run_optimization(experiment, lambda result: None)
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"Error starting optimization: {e}")


def _start_dynamic_optimization(app, state):
    """Run CEC2018 dynamic problem using NSGA-II with tau incremented per generation."""
    import threading
    import numpy as np
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.operators.crossover.sbx import SBX
    from pymoo.operators.mutation.pm import PM
    from pymoo.operators.sampling.rnd import FloatRandomSampling
    from pymoo.optimize import minimize
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from cec2018_dmop import CEC2018Problem
    from ..core.optimization_engine import OptimizationResult

    problem_id  = state.get("cec2018_id", 1)
    taut        = state.get("taut", 10)
    nt          = state.get("nt", 10)
    pop_size    = state.get("population_size", 100)
    max_gen     = state.get("max_generations", 250)
    seed        = state.get("random_seed", 42)

    problem = CEC2018Problem(problem_id=problem_id, taut=taut, nt=nt, n_var=10)

    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=FloatRandomSampling(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(prob=0.1, eta=20),
        eliminate_duplicates=True,
    )

    engine = app.optimization_engine
    engine.is_running = True
    engine.stop_requested = False
    engine.convergence_history = []
    engine.diversity_history = []

    def callback(algo):
        if engine.stop_requested:
            algo.termination.force_termination = True
            return
        # Advance time parameter
        problem.set_tau(algo.n_gen)

        pf = algo.opt.get("F")
        pop_F = algo.pop.get("F")
        pop_X = algo.pop.get("X")

        metrics = {"n_solutions": len(pf), "hypervolume": 0.0, "spread": 0.0, "spacing": 0.0}
        try:
            from pymoo.indicators.hv import HV
            ref = np.max(pf, axis=0) + 1.0
            metrics["hypervolume"] = float(HV(ref_point=ref)(pf))
        except Exception:
            pass

        engine.convergence_history.append({
            "generation": algo.n_gen,
            "hypervolume": metrics["hypervolume"],
            "n_solutions": metrics["n_solutions"],
        })

        engine.current_result = OptimizationResult(
            generation=algo.n_gen,
            population=pop_X,
            objectives=pop_F,
            constraints=None,
            pareto_front=pf,
            metrics=metrics,
            algorithm_info={
                "algorithm": "nsga2",
                "population_size": pop_size,
                "n_gen": algo.n_gen,
                "problem": f"DF{problem_id}",
                "taut": taut,
                "nt": nt,
            },
        )

    def worker():
        try:
            minimize(
                problem, algorithm,
                ("n_gen", max_gen),
                callback=callback,
                verbose=False,
                seed=seed,
            )
        except Exception as e:
            print(f"Dynamic optimization error: {e}")
        finally:
            engine.is_running = False

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    engine.optimization_thread = t


def _build_results_data(current_result, app):
    """Serialize an OptimizationResult into a JSON-safe dict."""
    results_data = {
        "generation":            current_result.generation,
        "pareto_front":          current_result.pareto_front.tolist(),
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
    from ..core.state_manager import ExperimentState

    var_names        = state.get("var_names") or []
    var_types        = state.get("var_types") or []
    var_lowers       = state.get("var_lowers") or []
    var_uppers       = state.get("var_uppers") or []
    obj_names        = state.get("obj_names") or []
    obj_directions   = state.get("obj_directions") or []
    obj_expressions  = state.get("obj_expressions") or []
    constraint_names = state.get("constraint_names") or []
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
                type="ineq",
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
        random_seed=int(state.get("random_seed") or 42),
        parameters={
            "crossover_prob": 0.9, "crossover_eta": 15,
            "mutation_eta": 20,
        },
        many_objective_options=[], dynamic_options=[],
    )

    return ExperimentState(
        name=state.get("experiment_name", "experiment"),
        description="",
        problem=problem, algorithm=algorithm,
        created_at="", modified_at="",
    )
