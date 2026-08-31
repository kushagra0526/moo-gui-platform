"""
pymoo Problem wrapper for CEC2018 DMOP benchmarks.

Usage:
    problem = CEC2018Problem(problem_id=1, taut=10, nt=10, n_var=10)
    # problem_id: 1-14
    # taut: change frequency (generations between environment changes)
    # nt: change severity
"""

import numpy as np
from pymoo.core.problem import Problem
from .cec2018_DF import cec2018_DF

# DF1-9: 2 objectives, DF10-14: 3 objectives
_N_OBJ = {i: 2 for i in range(1, 10)}
_N_OBJ.update({i: 3 for i in range(10, 15)})

# Variable bounds: x[0] in [0,1], x[1:] in [-1,1]
# For 3-obj problems (DF10-14): x[0],x[1] in [0,1], x[2:] in [-1,1]
def _get_bounds(problem_id, n_var):
    if problem_id <= 9:
        xl = np.array([0.0] + [-1.0] * (n_var - 1))
        xu = np.array([1.0] + [ 1.0] * (n_var - 1))
    else:
        xl = np.array([0.0, 0.0] + [-1.0] * (n_var - 2))
        xu = np.array([1.0, 1.0] + [ 1.0] * (n_var - 2))
    return xl, xu


class CEC2018Problem(Problem):
    """
    pymoo-compatible wrapper for CEC2018 DMOP benchmark functions.

    The `tau` (generation counter) is updated externally by calling
    `set_tau(tau)` before each generation's evaluation.
    """

    def __init__(self, problem_id: int, taut: int = 10, nt: int = 10, n_var: int = 10):
        if not 1 <= problem_id <= 14:
            raise ValueError(f"problem_id must be 1–14, got {problem_id}")

        self.problem_id = problem_id
        self.taut = int(taut)
        self.nt = int(nt)
        self.tau = 0  # updated each generation

        n_obj = _N_OBJ[problem_id]
        xl, xu = _get_bounds(problem_id, n_var)

        super().__init__(
            n_var=n_var,
            n_obj=n_obj,
            n_constr=0,
            xl=xl,
            xu=xu,
        )

    def set_tau(self, tau: int):
        """Call this before each generation to advance the time parameter."""
        self.tau = tau

    def _evaluate(self, X, out, *args, **kwargs):
        n_samples = X.shape[0]
        F = np.zeros((n_samples, self.n_obj))

        for i in range(n_samples):
            result = cec2018_DF(
                self.problem_id, X[i],
                self.tau, self.taut, self.nt,
            )
            for j in range(self.n_obj):
                F[i, j] = result[j]

        out["F"] = F
