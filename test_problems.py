#!/usr/bin/env python3
"""
Test Problems for the Multi-Objective Optimization GUI
Validates problem definitions and provides standard test cases.
"""

import unittest
import numpy as np
from expression_parser import ExpressionParser
from generic_problem import GenericProblem
from engineering_problem import EngineeringProblems
from gui.core.state_manager import StateManager, Variable, Objective, Constraint, ProblemDefinition


class TestProblemDefinitions(unittest.TestCase):
    """Test suite for optimization problem formulations and evaluations."""

    def setUp(self):
        self.parser = ExpressionParser()
        self.state_manager = StateManager()

    def test_basic_biobjective(self):
        """Test basic bi-objective problem."""
        variables = [
            Variable("x1", "continuous", 0.0, 1.0),
            Variable("x2", "continuous", 0.0, 1.0),
        ]
        objectives = [
            Objective("f1", "minimize", "x[0]**2 + x[1]**2"),
            Objective("f2", "minimize", "(x[0]-1)**2 + (x[1]-1)**2"),
        ]
        problem_def = ProblemDefinition(variables, objectives, [], "static")
        issues = self.state_manager.validate_problem_definition(problem_def)
        self.assertEqual(len(issues), 0, f"Validation issues: {issues}")

        # Test evaluation
        prob = GenericProblem(
            n_var=2,
            n_obj=2,
            n_constr=0,
            xl=np.array([0.0, 0.0]),
            xu=np.array([1.0, 1.0]),
            objective_expressions=["x[0]**2 + x[1]**2", "(x[0]-1)**2 + (x[1]-1)**2"],
        )
        out = {}
        X = np.array([[0.5, 0.5]])
        prob._evaluate(X, out)
        self.assertEqual(out["F"].shape, (1, 2))
        self.assertAlmostEqual(out["F"][0, 0], 0.5)
        self.assertAlmostEqual(out["F"][0, 1], 0.5)

    def test_zdt1_benchmark(self):
        """Test ZDT1 benchmark problem."""
        variables = [Variable(f"x{i}", "continuous", 0.0, 1.0) for i in range(5)]
        objectives = [
            Objective("f1", "minimize", "x[0]"),
            Objective("f2", "minimize", "(1 + 9*sum(x[1:])/4) * (1 - sqrt(x[0]/(1 + 9*sum(x[1:])/4)))"),
        ]
        problem_def = ProblemDefinition(variables, objectives, [], "static")
        issues = self.state_manager.validate_problem_definition(problem_def)
        self.assertEqual(len(issues), 0)

    def test_constrained_problem(self):
        """Test constrained problem."""
        variables = [
            Variable("x1", "continuous", -5.0, 5.0),
            Variable("x2", "continuous", -5.0, 5.0),
        ]
        objectives = [
            Objective("f1", "minimize", "x[0]**2 + x[1]**2"),
            Objective("f2", "minimize", "(x[0]-2)**2 + (x[1]-1)**2"),
        ]
        constraints = [
            Constraint("g1", "ineq", "x[0]**2 + x[1]**2 - 1"),
        ]
        problem_def = ProblemDefinition(variables, objectives, constraints, "static")
        issues = self.state_manager.validate_problem_definition(problem_def)
        self.assertEqual(len(issues), 0)

    def test_engineering_problems(self):
        """Test engineering problem templates."""
        wb = EngineeringProblems.welded_beam_design()
        self.assertEqual(len(wb["variables"]), 4)
        self.assertEqual(len(wb["objectives"]), 2)
        self.assertEqual(len(wb["constraints"]), 4)

        pv = EngineeringProblems.pressure_vessel_design()
        self.assertEqual(len(pv["variables"]), 4)
        self.assertEqual(len(pv["objectives"]), 2)
        self.assertEqual(len(pv["constraints"]), 4)

    def test_many_objective_dtlz2(self):
        """Test many-objective DTLZ2 formulation."""
        variables = [Variable(f"x{i}", "continuous", 0.0, 1.0) for i in range(6)]
        objectives = [
            Objective("f1", "minimize", "(1 + sum((x[3:] - 0.5)**2)) * cos(x[0]*pi/2) * cos(x[1]*pi/2) * cos(x[2]*pi/2)"),
            Objective("f2", "minimize", "(1 + sum((x[3:] - 0.5)**2)) * cos(x[0]*pi/2) * cos(x[1]*pi/2) * sin(x[2]*pi/2)"),
            Objective("f3", "minimize", "(1 + sum((x[3:] - 0.5)**2)) * cos(x[0]*pi/2) * sin(x[1]*pi/2)"),
            Objective("f4", "minimize", "(1 + sum((x[3:] - 0.5)**2)) * sin(x[0]*pi/2)"),
        ]
        problem_def = ProblemDefinition(variables, objectives, [], "many")
        issues = self.state_manager.validate_problem_definition(problem_def)
        self.assertEqual(len(issues), 0)


def print_reference_problems():
    """Print problem definitions reference sheet for manual GUI testing."""
    print("TEST PROBLEMS REFERENCE SHEET FOR MOO GUI")
    print("=" * 50)
    print("\n1. BASIC BI-OBJECTIVE PROBLEM")
    print("  f1: x[0]**2 + x[1]**2")
    print("  f2: (x[0]-1)**2 + (x[1]-1)**2")
    print("\n2. ZDT1 BENCHMARK PROBLEM")
    print("  f1: x[0]")
    print("  f2: (1 + 9*sum(x[1:])/4) * (1 - sqrt(x[0]/(1 + 9*sum(x[1:])/4)))")
    print("\n3. CONSTRAINED PROBLEM")
    print("  f1: x[0]**2 + x[1]**2")
    print("  f2: (x[0]-2)**2 + (x[1]-1)**2")
    print("  g1 (<= 0): x[0]**2 + x[1]**2 - 1")
    print("=" * 50)


if __name__ == "__main__":
    print_reference_problems()
    unittest.main()