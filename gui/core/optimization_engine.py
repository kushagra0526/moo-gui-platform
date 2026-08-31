"""
Optimization engine integrating with pymoo
"""

import numpy as np
from typing import Dict, Any, List, Optional, Callable
import threading
import time
from dataclasses import dataclass

from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.algorithms.moo.moead import MOEAD
from pymoo.algorithms.moo.rnsga2 import RNSGA2
from pymoo.algorithms.soo.nonconvex.pso import PSO

from pymoo.core.problem import Problem
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.operators.sampling.lhs import LHS
from pymoo.operators.selection.tournament import TournamentSelection

from pymoo.optimize import minimize
from pymoo.indicators.hv import HV
from pymoo.indicators.igd import IGD

from .state_manager import ExperimentState, Variable, Objective, Constraint

@dataclass
class OptimizationResult:
    """Results from optimization run."""
    generation: int
    population: np.ndarray
    objectives: np.ndarray
    constraints: Optional[np.ndarray]
    pareto_front: np.ndarray
    metrics: Dict[str, float]
    algorithm_info: Dict[str, Any]

class CustomProblem(Problem):
    """Custom problem class for user-defined optimization problems."""
    
    def __init__(self, experiment: ExperimentState):
        self.experiment = experiment
        self.variables = experiment.problem.variables
        self.objectives_def = experiment.problem.objectives
        self.constraints_def = experiment.problem.constraints
        
        # Determine variable bounds and types
        xl = np.array([var.lower_bound for var in self.variables])
        xu = np.array([var.upper_bound for var in self.variables])
        
        # Handle variable types
        vtype = []
        for var in self.variables:
            if var.type == 'continuous':
                vtype.append(float)
            elif var.type == 'integer':
                vtype.append(int)
            elif var.type == 'binary':
                vtype.append(bool)
        
        super().__init__(
            n_var=len(self.variables),
            n_obj=len(self.objectives_def),
            n_constr=len(self.constraints_def),
            xl=xl,
            xu=xu,
        )
        
        # Compile expressions for performance
        self._compile_expressions()
    
    def _compile_expressions(self):
        """Compile objective and constraint expressions."""
        self.objective_funcs = []
        self.constraint_funcs = []
        
        # Compile objectives
        for obj in self.objectives_def:
            try:
                # Create a safe evaluation environment
                func_code = compile(obj.expression, '<objective>', 'eval')
                self.objective_funcs.append((func_code, obj.direction))
            except SyntaxError as e:
                raise ValueError(f"Invalid objective expression '{obj.name}': {e}")
        
        # Compile constraints
        for con in self.constraints_def:
            try:
                func_code = compile(con.expression, '<constraint>', 'eval')
                self.constraint_funcs.append(func_code)
            except SyntaxError as e:
                raise ValueError(f"Invalid constraint expression '{con.name}': {e}")
    
    def _evaluate(self, X, out, *args, **kwargs):
        """Evaluate objectives and constraints."""
        n_samples = X.shape[0]
        
        # Evaluate objectives
        F = np.zeros((n_samples, self.n_obj))
        for i in range(n_samples):
            x = X[i]
            for j, (func_code, direction) in enumerate(self.objective_funcs):
                try:
                    # Safe evaluation with limited scope
                    safe_globals = {
                        "__builtins__": {},
                        "x": x, 
                        "np": np, 
                        "sin": np.sin, 
                        "cos": np.cos, 
                        "exp": np.exp, 
                        "log": np.log, 
                        "sqrt": np.sqrt,
                        "abs": np.abs, 
                        "sum": np.sum, 
                        "max": np.max, 
                        "min": np.min,
                        "len": len,
                        "range": range,
                        "pi": np.pi,
                        "e": np.e
                    }
                    value = eval(func_code, safe_globals, {})
                    # Handle maximize objectives
                    F[i, j] = -value if direction == 'maximize' else value
                except Exception as e:
                    # Handle evaluation errors gracefully
                    F[i, j] = np.inf
        
        out["F"] = F
        # Replace any inf/NaN with a large finite penalty so NSGA2 doesn't crash
        out["F"] = np.where(np.isfinite(F), F, 1e9)
        
        # Evaluate constraints if any
        if self.n_constr > 0:
            G = np.zeros((n_samples, self.n_constr))
            for i in range(n_samples):
                x = X[i]
                for j, func_code in enumerate(self.constraint_funcs):
                    try:
                        safe_globals = {
                            "__builtins__": {},
                            "x": x, 
                            "np": np, 
                            "sin": np.sin, 
                            "cos": np.cos,
                            "exp": np.exp, 
                            "log": np.log, 
                            "sqrt": np.sqrt,
                            "abs": np.abs, 
                            "sum": np.sum, 
                            "max": np.max, 
                            "min": np.min,
                            "len": len,
                            "range": range,
                            "pi": np.pi,
                            "e": np.e
                        }
                        value = eval(func_code, safe_globals, {})
                        G[i, j] = value
                    except Exception as e:
                        G[i, j] = np.inf
            
            out["G"] = G

class OptimizationEngine:
    """Main optimization engine managing algorithm execution."""
    
    def __init__(self):
        self.is_running = False
        self.current_result: Optional[OptimizationResult] = None
        self.optimization_thread: Optional[threading.Thread] = None
        self.callback_func: Optional[Callable] = None
        self.stop_requested = False
        # Track metrics history
        self.convergence_history = []
        self.diversity_history = []
        
    def setup_algorithm(self, experiment: ExperimentState):
        """Setup the optimization algorithm based on experiment configuration."""
        config = experiment.algorithm

        # Setup sampling
        sampling = LHS() if config.parameters.get("sampling") == "lhs" else FloatRandomSampling()

        # Setup crossover
        crossover = SBX(
            prob=config.parameters.get("crossover_prob", 0.9),
            eta=config.parameters.get("crossover_eta", 15)
        )

        # Setup mutation — 1/n_var is the standard default
        n_var = len(experiment.problem.variables) if experiment.problem.variables else 10
        default_mut_prob = 1.0 / max(n_var, 1)
        mutation = PM(
            prob=config.parameters.get("mutation_prob", default_mut_prob),
            eta=config.parameters.get("mutation_eta", 20)
        )

        pop_size = int(config.population_size) if config.population_size else 100

        if config.algorithm == "nsga2":
            algorithm = NSGA2(
                pop_size=pop_size,
                sampling=sampling,
                crossover=crossover,
                mutation=mutation,
                eliminate_duplicates=True
            )
        elif config.algorithm == "nsga3":
            from pymoo.util.ref_dirs import get_reference_directions
            ref_dirs = get_reference_directions("das-dennis", 2, n_partitions=12)
            algorithm = NSGA3(
                ref_dirs=ref_dirs,
                pop_size=pop_size,
                sampling=sampling,
                crossover=crossover,
                mutation=mutation,
                eliminate_duplicates=True
            )
        elif config.algorithm == "moead":
            from pymoo.util.ref_dirs import get_reference_directions
            ref_dirs = get_reference_directions("uniform", 2, n_partitions=pop_size - 1)
            algorithm = MOEAD(
                ref_dirs=ref_dirs,
                n_neighbors=20,
                decomposition="tchebicheff",
                prob_neighbor_mating=0.9,
                sampling=sampling,
                crossover=crossover,
                mutation=mutation
            )
        else:
            raise ValueError(f"Unsupported algorithm: {config.algorithm}")

        return algorithm
    
    def run_optimization(self, experiment: ExperimentState, callback: Optional[Callable] = None):
        """Run optimization in a separate thread."""
        if self.is_running:
            raise RuntimeError("Optimization is already running")
        
        self.callback_func = callback
        self.stop_requested = False
        self.optimization_thread = threading.Thread(
            target=self._optimization_worker,
            args=(experiment,)
        )
        self.optimization_thread.start()
    
    def stop_optimization(self):
        """Request optimization to stop."""
        self.is_running = False  # Mark stopped immediately so UI reflects it at once
        self.stop_requested = True
        if self.optimization_thread and self.optimization_thread.is_alive():
            self.optimization_thread.join(timeout=5.0)
    
    def _optimization_worker(self, experiment: ExperimentState):
        """Worker function for optimization thread."""
        try:
            self.is_running = True
            self.convergence_history = []
            self.diversity_history = []

            problem   = CustomProblem(experiment)
            algorithm = self.setup_algorithm(experiment)

            def optimization_callback(algorithm):
                if self.stop_requested:
                    algorithm.termination.force_termination = True
                    return

                pf   = algorithm.opt.get("F")
                popF = algorithm.pop.get("F")
                popX = algorithm.pop.get("X")

                # Skip if any NaN/inf in Pareto front
                if pf is None or len(pf) == 0:
                    return
                pf_clean = pf[np.all(np.isfinite(pf), axis=1)]
                if len(pf_clean) == 0:
                    return

                metrics = self._calculate_metrics_safe(pf_clean)

                self.convergence_history.append({
                    "generation":  algorithm.n_gen,
                    "hypervolume": metrics.get("hypervolume", 0.0),
                    "n_solutions": metrics.get("n_solutions", 0),
                    "best_f":      float(np.nanmin(pf_clean[:, 0])),
                })
                self.diversity_history.append({
                    "generation": algorithm.n_gen,
                    "spread":     metrics.get("spread", 0.0),
                    "spacing":    metrics.get("spacing", 0.0),
                })

                self.current_result = OptimizationResult(
                    generation=algorithm.n_gen,
                    population=popX,
                    objectives=popF,
                    constraints=algorithm.pop.get("G") if problem.n_constr > 0 else None,
                    pareto_front=pf_clean,
                    metrics=metrics,
                    algorithm_info={
                        "algorithm":      experiment.algorithm.algorithm,
                        "population_size":experiment.algorithm.population_size,
                        "n_gen":          algorithm.n_gen,
                    }
                )
                if self.callback_func:
                    self.callback_func(self.current_result)

            res = minimize(
                problem, algorithm,
                ('n_gen', experiment.algorithm.max_generations),
                callback=optimization_callback,
                verbose=False,
                seed=experiment.algorithm.random_seed,
            )

            # Final result
            if not self.stop_requested and res.F is not None:
                pf_final = res.F[np.all(np.isfinite(res.F), axis=1)]
                if len(pf_final) > 0:
                    final_metrics = self._calculate_metrics_safe(pf_final)
                    self.current_result = OptimizationResult(
                        generation=res.algorithm.n_gen,
                        population=res.pop.get("X"),
                        objectives=res.pop.get("F"),
                        constraints=res.pop.get("G") if problem.n_constr > 0 else None,
                        pareto_front=pf_final,
                        metrics=final_metrics,
                        algorithm_info={
                            "algorithm":        experiment.algorithm.algorithm,
                            "population_size":  experiment.algorithm.population_size,
                            "n_gen":            res.algorithm.n_gen,
                            "convergence_history": self.convergence_history,
                            "diversity_history":   self.diversity_history,
                        }
                    )
                    if self.callback_func:
                        self.callback_func(self.current_result)

        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"Optimization error: {e}")
        finally:
            self.is_running = False
    
    def _calculate_metrics_safe(self, pf_clean: np.ndarray) -> Dict[str, float]:
        """Calculate metrics on a clean (finite) Pareto front."""
        metrics = {"hypervolume": 0.0, "n_solutions": len(pf_clean),
                   "spread": 0.0, "spacing": 0.0}
        try:
            ref = np.max(pf_clean, axis=0) + 1.0
            metrics["hypervolume"] = float(HV(ref_point=ref)(pf_clean))
        except Exception:
            pass
        if len(pf_clean) > 1:
            try:
                dists = [min(np.linalg.norm(pf_clean[i] - pf_clean[j])
                             for j in range(len(pf_clean)) if i != j)
                         for i in range(len(pf_clean))]
                metrics["spread"]  = float(np.std(dists))
                metrics["spacing"] = float(np.mean(dists))
            except Exception:
                pass
        return metrics