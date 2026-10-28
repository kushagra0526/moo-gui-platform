"""
Optimization engine integrating with pymoo
"""

import numpy as np
from typing import Dict, Any, Optional, Callable
import threading
from dataclasses import dataclass

from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.core.repair import Repair
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.operators.sampling.lhs import LHS
from pymoo.optimize import minimize
from pymoo.indicators.hv import HV

from expression_parser import ExpressionParser
from .state_manager import ExperimentState

# Tolerance used to turn an equality constraint h(x) = 0 into |h(x)| - EQ_TOL <= 0
EQ_TOL = 1e-4


@dataclass
class OptimizationResult:
    """Results from optimization run."""
    generation: int
    population: np.ndarray
    objectives: np.ndarray
    constraints: Optional[np.ndarray]
    pareto_front: np.ndarray
    pareto_set: np.ndarray
    metrics: Dict[str, float]
    algorithm_info: Dict[str, Any]


class RoundIntegers(Repair):
    """Round integer and binary variables so they are evaluated and reported as whole numbers."""

    def __init__(self, idx):
        super().__init__()
        self.idx = idx

    def _do(self, problem, X, **kwargs):
        X[:, self.idx] = np.round(X[:, self.idx])
        return X


class CustomProblem(Problem):
    """Custom problem class for user-defined optimization problems."""

    def __init__(self, experiment: ExperimentState):
        self.variables = experiment.problem.variables
        self.objectives_def = experiment.problem.objectives
        self.constraints_def = experiment.problem.constraints

        # Binary variables are always 0/1, whatever bounds were typed
        xl = np.array([0.0 if v.type == 'binary' else v.lower_bound for v in self.variables])
        xu = np.array([1.0 if v.type == 'binary' else v.upper_bound for v in self.variables])
        self.integer_idx = [i for i, v in enumerate(self.variables) if v.type in ('integer', 'binary')]
        # pymoo minimizes, so maximized objectives are negated; multiply by sign to report real values
        self.sign = np.array([-1.0 if o.direction == 'maximize' else 1.0 for o in self.objectives_def])

        super().__init__(
            n_var=len(self.variables),
            n_obj=len(self.objectives_def),
            n_constr=len(self.constraints_def),
            xl=xl,
            xu=xu,
        )

        # Validate (only safe math is allowed) and compile once
        self.parser = ExpressionParser()
        self.objective_funcs = [(self._compile(o.expression, o.name), o.direction) for o in self.objectives_def]
        self.constraint_funcs = [(self._compile(c.expression, c.name), c.type) for c in self.constraints_def]

    def _compile(self, expression, name):
        try:
            return self.parser.compile(expression)
        except ValueError as e:
            raise ValueError(f"'{name}': {e}")

    def _evaluate(self, X, out, *args, **kwargs):
        """Evaluate objectives and constraints."""
        n_samples = X.shape[0]
        namespace = self.parser.namespace()

        F = np.zeros((n_samples, self.n_obj))
        G = np.zeros((n_samples, self.n_constr))
        for i in range(n_samples):
            namespace["x"] = X[i]
            for j, (code, direction) in enumerate(self.objective_funcs):
                try:
                    value = eval(code, namespace)
                    F[i, j] = -value if direction == 'maximize' else value
                except Exception:
                    F[i, j] = np.inf
            for j, (code, ctype) in enumerate(self.constraint_funcs):
                try:
                    value = eval(code, namespace)
                    G[i, j] = abs(value) - EQ_TOL if ctype == 'eq' else value
                except Exception:
                    G[i, j] = np.inf

        # Replace any inf/NaN with a large finite penalty so NSGA2 doesn't crash
        out["F"] = np.where(np.isfinite(F), F, 1e9)
        if self.n_constr > 0:
            out["G"] = G


class OptimizationEngine:
    """Main optimization engine managing algorithm execution."""

    # shortcut: one engine per server process, shared by every signed-in user; give each session its own engine before multi-user use
    def __init__(self):
        self.is_running = False
        self.current_result: Optional[OptimizationResult] = None
        self.optimization_thread: Optional[threading.Thread] = None
        self.callback_func: Optional[Callable] = None
        self.stop_requested = False
        # Track metrics history
        self.convergence_history = []
        self.diversity_history = []
        self._hv_ref = None

    def setup_algorithm(self, experiment: ExperimentState, problem: Optional[CustomProblem] = None):
        """Setup NSGA-II from the experiment configuration."""
        config = experiment.algorithm
        if config.algorithm != "nsga2":
            raise ValueError(f"Unsupported algorithm: {config.algorithm}")

        sampling = LHS() if config.parameters.get("sampling") == "lhs" else FloatRandomSampling()
        crossover = SBX(
            prob=config.parameters.get("crossover_prob", 0.9),
            eta=config.parameters.get("crossover_eta", 15)
        )
        # Mutation — 1/n_var is the standard default
        n_var = len(experiment.problem.variables) or 1
        mutation = PM(
            prob=config.parameters.get("mutation_prob", 1.0 / n_var),
            eta=config.parameters.get("mutation_eta", 20)
        )
        extra = {"repair": RoundIntegers(problem.integer_idx)} if problem is not None and problem.integer_idx else {}

        return NSGA2(
            pop_size=int(config.population_size) if config.population_size else 100,
            sampling=sampling,
            crossover=crossover,
            mutation=mutation,
            eliminate_duplicates=True,
            **extra,
        )

    def run_optimization(self, experiment: ExperimentState, callback: Optional[Callable] = None):
        """Run optimization in a separate thread."""
        if self.is_running:
            raise RuntimeError("Optimization is already running")

        # Build the problem here so invalid formulas fail in the caller, not silently in the thread
        problem = CustomProblem(experiment)
        self.callback_func = callback
        self.stop_requested = False
        self.is_running = True
        self.optimization_thread = threading.Thread(
            target=self._optimization_worker,
            args=(experiment, problem),
            daemon=True,
        )
        self.optimization_thread.start()

    def stop_optimization(self):
        """Request optimization to stop."""
        self.is_running = False  # Mark stopped immediately so UI reflects it at once
        self.stop_requested = True
        if self.optimization_thread and self.optimization_thread.is_alive():
            self.optimization_thread.join(timeout=5.0)

    def _make_result(self, experiment, problem, algorithm, pop, opt):
        """Build an OptimizationResult from pymoo's population and optimum, dropping non-finite points."""
        pf, ps = opt.get("F"), opt.get("X")
        mask = np.all(np.isfinite(pf), axis=1)
        pf, ps = pf[mask], ps[mask]
        if len(pf) == 0:
            return None
        metrics = self._calculate_metrics_safe(pf)
        return OptimizationResult(
            generation=algorithm.n_gen,
            population=pop.get("X"),
            objectives=pop.get("F") * problem.sign,
            constraints=pop.get("G") if problem.n_constr > 0 else None,
            pareto_front=pf * problem.sign,
            pareto_set=ps,
            metrics=metrics,
            algorithm_info={
                "algorithm": experiment.algorithm.algorithm,
                "population_size": experiment.algorithm.population_size,
                "n_gen": algorithm.n_gen,
            },
        )

    def _optimization_worker(self, experiment: ExperimentState, problem: CustomProblem):
        """Worker function for optimization thread."""
        try:
            self.convergence_history = []
            self.diversity_history = []
            self._hv_ref = None
            algorithm = self.setup_algorithm(experiment, problem)

            def optimization_callback(algorithm):
                if self.stop_requested:
                    algorithm.termination.force_termination = True
                    return
                result = self._make_result(experiment, problem, algorithm, algorithm.pop, algorithm.opt)
                if result is None:
                    return
                self.convergence_history.append({
                    "generation":  algorithm.n_gen,
                    "hypervolume": result.metrics["hypervolume"],
                    "n_solutions": result.metrics["n_solutions"],
                    "best_f":      float(np.min(result.pareto_front[:, 0])),
                })
                self.diversity_history.append({
                    "generation": algorithm.n_gen,
                    "spread":     result.metrics["spread"],
                    "spacing":    result.metrics["spacing"],
                })
                self.current_result = result
                if self.callback_func:
                    self.callback_func(result)

            # The callback also runs after the last generation, so current_result ends as the final front
            minimize(
                problem, algorithm,
                ('n_gen', experiment.algorithm.max_generations),
                callback=optimization_callback,
                verbose=False,
                seed=experiment.algorithm.random_seed,
            )

        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"Optimization error: {e}")
        finally:
            # A run stopped and replaced by a new one must not mark the new run as finished
            if self.optimization_thread is threading.current_thread():
                self.is_running = False

    def _calculate_metrics_safe(self, pf_clean: np.ndarray) -> Dict[str, float]:
        """Calculate metrics on a clean (finite) Pareto front."""
        metrics = {"hypervolume": 0.0, "n_solutions": len(pf_clean),
                   "spread": 0.0, "spacing": 0.0}
        # Fix the reference point on first use so hypervolume is comparable across generations
        if self._hv_ref is None or len(self._hv_ref) != pf_clean.shape[1]:
            self._hv_ref = np.max(pf_clean, axis=0) + 1.0
        try:
            metrics["hypervolume"] = float(HV(ref_point=self._hv_ref)(pf_clean))
        except Exception:
            pass
        if len(pf_clean) > 1:
            d = np.linalg.norm(pf_clean[:, None, :] - pf_clean[None, :, :], axis=2)
            np.fill_diagonal(d, np.inf)
            dists = d.min(axis=1)
            metrics["spread"]  = float(np.std(dists))
            metrics["spacing"] = float(np.mean(dists))
        return metrics
