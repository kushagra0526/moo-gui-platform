#!/usr/bin/env python3
"""
Generic multi-objective optimization problem definition.
Provides flexible problem class for user-defined objectives and constraints.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Callable
from pymoo.core.problem import Problem
from expression_parser import ExpressionParser


class GenericProblem(Problem):
    """
    Generic multi-objective optimization problem with user-defined expressions.
    Supports continuous, integer, and binary variables with constraints.
    """
    
    def __init__(
        self,
        n_var: int,
        n_obj: int,
        n_constr: int = 0,
        xl: Optional[np.ndarray] = None,
        xu: Optional[np.ndarray] = None,
        var_types: Optional[List[str]] = None,
        objective_expressions: Optional[List[str]] = None,
        constraint_expressions: Optional[List[str]] = None,
        objective_directions: Optional[List[str]] = None,
        time_dependent: bool = False,
        **kwargs
    ):
        """
        Initialize generic optimization problem.
        
        Args:
            n_var: Number of decision variables
            n_obj: Number of objectives
            n_constr: Number of constraints
            xl: Lower bounds for variables
            xu: Upper bounds for variables
            var_types: List of variable types ('real', 'int', 'binary')
            objective_expressions: List of objective function expressions
            constraint_expressions: List of constraint expressions (g(x) <= 0)
            objective_directions: List of 'minimize' or 'maximize' for each objective
            time_dependent: Whether problem is time-dependent (dynamic)
        """
        # Set default bounds if not provided
        if xl is None:
            xl = np.zeros(n_var)
        if xu is None:
            xu = np.ones(n_var)
        
        # Initialize parent class
        super().__init__(
            n_var=n_var,
            n_obj=n_obj,
            n_constr=n_constr,
            xl=xl,
            xu=xu,
            **kwargs
        )
        
        # Store problem configuration
        self.var_types = var_types or ['real'] * n_var
        self.objective_expressions = objective_expressions or []
        self.constraint_expressions = constraint_expressions or []
        self.objective_directions = objective_directions or ['minimize'] * n_obj
        self.time_dependent = time_dependent
        self.current_time = 0.0
        
        # Initialize expression parser
        self.parser = ExpressionParser()
        
        # Compile expressions for faster evaluation
        self._compile_expressions()
        
        # Validate configuration
        self._validate()
    
    def _compile_expressions(self):
        """Compile all expressions for efficient evaluation."""
        self.compiled_objectives = []
        self.compiled_constraints = []
        
        # Compile objectives
        for i, expr in enumerate(self.objective_expressions):
            try:
                code = self.parser.compile(expr, cache_key=f"obj_{i}")
                self.compiled_objectives.append(code)
            except Exception as e:
                raise ValueError(f"Failed to compile objective {i}: {str(e)}")
        
        # Compile constraints
        for i, expr in enumerate(self.constraint_expressions):
            try:
                code = self.parser.compile(expr, cache_key=f"constr_{i}")
                self.compiled_constraints.append(code)
            except Exception as e:
                raise ValueError(f"Failed to compile constraint {i}: {str(e)}")
    
    def _validate(self):
        """Validate problem configuration."""
        if len(self.objective_expressions) != self.n_obj:
            raise ValueError(
                f"Number of objective expressions ({len(self.objective_expressions)}) "
                f"must match n_obj ({self.n_obj})"
            )
        
        if len(self.constraint_expressions) != self.n_constr:
            raise ValueError(
                f"Number of constraint expressions ({len(self.constraint_expressions)}) "
                f"must match n_constr ({self.n_constr})"
            )
        
        if len(self.objective_directions) != self.n_obj:
            raise ValueError(
                f"Number of objective directions ({len(self.objective_directions)}) "
                f"must match n_obj ({self.n_obj})"
            )
        
        if len(self.var_types) != self.n_var:
            raise ValueError(
                f"Number of variable types ({len(self.var_types)}) "
                f"must match n_var ({self.n_var})"
            )
    
    def _evaluate(self, X, out, *args, **kwargs):
        """
        Evaluate objectives and constraints for given solutions.
        
        Args:
            X: Array of shape (n_solutions, n_variables)
            out: Dictionary to store results
        """
        n_solutions = X.shape[0]
        
        # Initialize output arrays
        F = np.zeros((n_solutions, self.n_obj))
        G = np.zeros((n_solutions, self.n_constr)) if self.n_constr > 0 else None
        
        # Prepare namespace for evaluation
        namespace = {
            **self.parser.SAFE_FUNCTIONS,
            'np': np,
        }
        
        # Add time for dynamic problems
        if self.time_dependent:
            namespace['t'] = self.current_time
        
        # Evaluate for each solution
        for i, x in enumerate(X):
            namespace['x'] = x
            
            # Evaluate objectives
            for j, code in enumerate(self.compiled_objectives):
                try:
                    value = eval(code, {"__builtins__": {}}, namespace)
                    # Handle maximize objectives (convert to minimize)
                    if self.objective_directions[j] == 'maximize':
                        value = -value
                    F[i, j] = value
                except Exception as e:
                    # Assign penalty for failed evaluations
                    F[i, j] = 1e6
                    print(f"Warning: Failed to evaluate objective {j} for solution {i}: {e}")
            
            # Evaluate constraints
            if self.n_constr > 0:
                for j, code in enumerate(self.compiled_constraints):
                    try:
                        value = eval(code, {"__builtins__": {}}, namespace)
                        G[i, j] = value
                    except Exception as e:
                        # Assign large constraint violation for failed evaluations
                        G[i, j] = 1e6
                        print(f"Warning: Failed to evaluate constraint {j} for solution {i}: {e}")
        
        # Store results
        out["F"] = F
        if G is not None:
            out["G"] = G
    
    def set_time(self, time: float):
        """Set current time for dynamic problems."""
        self.current_time = time
    
    def get_bounds(self) -> tuple:
        """Get variable bounds."""
        return self.xl, self.xu
    
    def get_variable_info(self) -> List[Dict[str, Any]]:
        """Get information about decision variables."""
        info = []
        for i in range(self.n_var):
            info.append({
                'index': i,
                'type': self.var_types[i],
                'lower_bound': self.xl[i],
                'upper_bound': self.xu[i]
            })
        return info
    
    def get_objective_info(self) -> List[Dict[str, Any]]:
        """Get information about objectives."""
        info = []
        for i in range(self.n_obj):
            info.append({
                'index': i,
                'expression': self.objective_expressions[i],
                'direction': self.objective_directions[i]
            })
        return info
    
    def get_constraint_info(self) -> List[Dict[str, Any]]:
        """Get information about constraints."""
        info = []
        for i in range(self.n_constr):
            info.append({
                'index': i,
                'expression': self.constraint_expressions[i],
                'type': 'inequality'  # g(x) <= 0
            })
        return info
    
    def evaluate_single(self, x: np.ndarray) -> Dict[str, Any]:
        """
        Evaluate a single solution and return detailed results.
        
        Args:
            x: Decision variable vector
            
        Returns:
            Dictionary with objectives, constraints, and feasibility
        """
        # Prepare output
        out = {}
        X = x.reshape(1, -1)
        
        # Evaluate
        self._evaluate(X, out)
        
        # Extract results
        objectives = out["F"][0]
        constraints = out.get("G", [None])[0] if "G" in out else None
        
        # Check feasibility
        is_feasible = True
        if constraints is not None:
            is_feasible = np.all(constraints <= 0)
        
        return {
            'variables': x,
            'objectives': objectives,
            'constraints': constraints,
            'is_feasible': is_feasible
        }


def create_problem_from_config(config: Dict[str, Any]) -> GenericProblem:
    """
    Create a GenericProblem instance from configuration dictionary.
    
    Args:
        config: Problem configuration dictionary
        
    Returns:
        GenericProblem instance
    """
    # Extract variables configuration
    variables = config.get('variables', [])
    n_var = len(variables)
    xl = np.array([v['lower_bound'] for v in variables])
    xu = np.array([v['upper_bound'] for v in variables])
    var_types = [v['type'] for v in variables]
    
    # Extract objectives configuration
    objectives = config.get('objectives', [])
    n_obj = len(objectives)
    objective_expressions = [obj['expression'] for obj in objectives]
    objective_directions = [obj['direction'] for obj in objectives]
    
    # Extract constraints configuration
    constraints = config.get('constraints', [])
    n_constr = len(constraints)
    constraint_expressions = [c['expression'] for c in constraints]
    
    # Check if time-dependent
    time_dependent = config.get('time_dependent', False)
    
    # Create problem
    problem = GenericProblem(
        n_var=n_var,
        n_obj=n_obj,
        n_constr=n_constr,
        xl=xl,
        xu=xu,
        var_types=var_types,
        objective_expressions=objective_expressions,
        constraint_expressions=constraint_expressions,
        objective_directions=objective_directions,
        time_dependent=time_dependent
    )
    
    return problem
