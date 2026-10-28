#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
import numpy as np
from expression_parser import ExpressionParser
from gui.app import create_app
from gui.core.optimization_engine import CustomProblem, OptimizationEngine, RoundIntegers
from gui.core.state_manager import StateManager, Variable, Objective, Constraint, ProblemDefinition


def _experiment(variables, objectives, constraints=()):
    exp = StateManager().create_new_experiment("t")
    exp.problem = ProblemDefinition(list(variables), list(objectives), list(constraints), "static")
    return exp


class TestFormulaSafety(unittest.TestCase):

    def test_math_formulas_are_accepted(self):
        parser = ExpressionParser()
        for expr in ["x[0]**2 + x[1]**2", "sqrt(x[0]) * sum(x[1:]) / len(x[1:])",
                     "-cos(pi * x[0]) if x[0] > 0.5 else exp(-x[1])"]:
            self.assertEqual(parser.validate(expr), (True, None), expr)

    def test_code_is_rejected(self):
        parser = ExpressionParser()
        for expr in ["x.__class__", "np.ones(3)", "(lambda: 1)()", "[i for i in x]",
                     "open('f')", "'text'", "sin(x=1)"]:
            ok, _ = parser.validate(expr)
            self.assertFalse(ok, expr)

    def test_engine_refuses_rejected_formula(self):
        exp = _experiment([Variable("x0", "continuous", 0, 1)],
                          [Objective("a", "minimize", "x[0]"), Objective("b", "minimize", "x.T")])
        with self.assertRaises(ValueError):
            OptimizationEngine().run_optimization(exp)


class TestProblemSettings(unittest.TestCase):

    def test_integer_rounding_and_equality_constraint(self):
        exp = _experiment(
            [Variable("x0", "integer", 0, 10), Variable("x1", "continuous", 0, 1)],
            [Objective("a", "minimize", "x[0]"), Objective("b", "maximize", "x[1]")],
            [Constraint("h", "eq", "x[0] - 3")],
        )
        problem = CustomProblem(exp)
        X = RoundIntegers(problem.integer_idx)._do(problem, np.array([[3.4, 0.5], [5.6, 0.5]]))
        self.assertEqual(X[:, 0].tolist(), [3.0, 6.0])
        out = {}
        problem._evaluate(X, out)
        self.assertLessEqual(out["G"][0, 0], 0)    # x0 = 3 satisfies x0 - 3 = 0
        self.assertGreater(out["G"][1, 0], 0)      # x0 = 6 does not
        self.assertEqual(out["F"][0, 1], -0.5)     # maximized objective is negated for pymoo


class TestLoginGuard(unittest.TestCase):

    def setUp(self):
        self.client = create_app().server.test_client()

    def test_app_callbacks_need_a_session(self):
        r = self.client.post("/_dash-update-component", json={
            "output": "..btn-run-optimization.disabled...opt-control-store.data..", "inputs": [], "state": []})
        self.assertEqual(r.status_code, 204)

    def test_forged_browser_state_does_not_log_in(self):
        r = self.client.post("/_dash-update-component", json={
            "output": "..login-page-wrapper.style...app-shell.children..",
            "outputs": [{"id": "login-page-wrapper", "property": "style"},
                        {"id": "app-shell", "property": "children"}],
            "inputs": [{"id": "auth-state", "property": "data", "value": {"authenticated": True}},
                       {"id": "url", "property": "pathname", "value": "/results"}],
            "state": [{"id": "app-state", "property": "data", "value": None},
                      {"id": "algo-config", "property": "data", "value": None}],
            "changedPropIds": ["auth-state.data"]})
        self.assertEqual(r.json["response"]["login-page-wrapper"]["style"], {"display": "block"})


if __name__ == "__main__":
    unittest.main()
