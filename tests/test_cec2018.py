#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
import numpy as np
from cec2018_dmop import CEC2018Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.optimize import minimize


class TestCEC2018(unittest.TestCase):
    """Test dynamic benchmark problems from CEC 2018."""

    def test_all_14_benchmarks_evaluation(self):
        for pid in range(1, 15):
            p = CEC2018Problem(problem_id=pid, taut=10, nt=10, n_var=10)
            p.set_tau(0)
            X = np.random.rand(3, 10)
            X[:, 1:] = X[:, 1:] * 2 - 1
            if pid >= 10:
                X[:, 1] = np.random.rand(3)
            out = {}
            p._evaluate(X, out)
            expected_n_obj = 2 if pid < 10 else 3
            self.assertEqual(out["F"].shape, (3, expected_n_obj))

    def test_nsga2_on_df1(self):
        problem = CEC2018Problem(problem_id=1, taut=10, nt=10, n_var=10)
        algo = NSGA2(
            pop_size=30,
            sampling=FloatRandomSampling(),
            crossover=SBX(prob=0.9, eta=15),
            mutation=PM(prob=0.1, eta=20),
            eliminate_duplicates=True,
        )
        res = minimize(problem, algo, ("n_gen", 10), seed=42, verbose=False)
        self.assertGreater(len(res.F), 0)

    def test_environment_change(self):
        p = CEC2018Problem(problem_id=1, taut=5, nt=10, n_var=10)
        X_test = np.array([[0.5] + [0.0]*9])
        p.set_tau(0)
        out1 = {}
        p._evaluate(X_test, out1)
        self.assertEqual(out1["F"].shape, (1, 2))


if __name__ == "__main__":
    unittest.main()
