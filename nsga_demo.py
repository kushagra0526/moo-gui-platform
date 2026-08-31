#!/usr/bin/env python3
"""
NSGA-II Standalone Demo
Demonstrates running NSGA-II optimization using the project's problem framework.
"""

import numpy as np
from generic_problem import GenericProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.optimize import minimize


def run_nsga2_demo():
    print("=" * 60)
    print("Running NSGA-II on ZDT1 Bi-Objective Problem")
    print("=" * 60)

    # 1. Define problem using GenericProblem
    n_var = 5
    problem = GenericProblem(
        n_var=n_var,
        n_obj=2,
        n_constr=0,
        xl=np.zeros(n_var),
        xu=np.ones(n_var),
        objective_expressions=[
            "x[0]",
            "(1 + 9*sum(x[1:])/4) * (1 - sqrt(x[0]/(1 + 9*sum(x[1:])/4)))"
        ],
        objective_directions=["minimize", "minimize"]
    )

    # 2. Configure algorithm
    algorithm = NSGA2(
        pop_size=50,
        sampling=FloatRandomSampling(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(prob=0.1, eta=20),
        eliminate_duplicates=True
    )

    # 3. Execute optimization
    res = minimize(
        problem,
        algorithm,
        ("n_gen", 50),
        seed=42,
        verbose=False
    )

    print(f"\nOptimization completed!")
    print(f"Total evaluated solutions: {len(res.pop)}")
    print(f"Non-dominated Pareto solutions found: {len(res.F)}")
    print(f"Best f1 found: {res.F[:, 0].min():.4f}")
    print(f"Best f2 found: {res.F[:, 1].min():.4f}")
    print("=" * 60)
    return res


if __name__ == '__main__':
    run_nsga2_demo()
