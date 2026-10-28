"""
CEC2018 DMOP benchmarks (DF1-DF14), using pymoo's reference implementation.

Usage:
    problem = CEC2018Problem(problem_id=1, taut=10, nt=10, n_var=10)
    # problem_id: 1-14
    # taut: change frequency (generations between environment changes)
    # nt: change severity
    problem.set_tau(generation)   # advance time before each generation
"""

import numpy as np
import pymoo.problems.dynamic.df as df

# CEC2018 competition setting: the first environment change happens after T0 generations
T0 = 50

# DF1-9: 2 objectives, DF10-14: 3 objectives
N_OBJ = {i: 2 if i <= 9 else 3 for i in range(1, 15)}


class _CompetitionTime:
    """Maps the generation counter to pymoo's tau with the competition's T0 offset:
    t = 1/nt * floor(max(gen + taut - T0 - 1, 0) / taut)."""

    def set_tau(self, tau: int):
        self.tau = max(int(tau) + self.taut - T0 - 1, 0)


_CLASSES = {k: type(f"DF{k}", (_CompetitionTime, getattr(df, f"DF{k}")), {}) for k in range(1, 15)}


def CEC2018Problem(problem_id: int, taut: int = 10, nt: int = 10, n_var: int = 10):
    """pymoo problem for DF<problem_id>; its `time` property is the current t."""
    if problem_id not in _CLASSES:
        raise ValueError(f"problem_id must be 1–14, got {problem_id}")
    problem = _CLASSES[problem_id](n_var=n_var, taut=int(taut), nt=int(nt))
    problem.set_tau(0)
    return problem


def true_front(problem_id: int, t: float, n_points: int = 400) -> np.ndarray:
    """Analytical Pareto front of DF<problem_id> at time t, sorted by f1."""
    problem = _CLASSES[problem_id]()
    problem.time = t
    pf = np.asarray(problem._calc_pareto_front(n_pareto_points=n_points))
    return pf[np.argsort(pf[:, 0])]
