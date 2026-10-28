#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from gui.core.state_manager import StateManager
from gui.core.optimization_engine import OptimizationEngine
from gui.app import create_app
from gui.layouts.problem_definition import create_problem_definition_layout
from gui.layouts.algorithm_config import create_algorithm_config_layout
from gui.layouts.visualization import create_visualization_layout
from gui.layouts.results import create_results_layout


class TestGUIComponents(unittest.TestCase):
    """Test GUI component creation and optimization engine setup."""

    def test_app_creation(self):
        app = create_app()
        self.assertIsNotNone(app)
        self.assertIsNotNone(app.server)

    def test_layouts(self):
        self.assertIsNotNone(create_problem_definition_layout())
        self.assertIsNotNone(create_algorithm_config_layout())
        self.assertIsNotNone(create_visualization_layout())
        self.assertIsNotNone(create_results_layout())

    def test_algorithm_setup(self):
        exp = StateManager().create_new_experiment("Test_nsga2")
        self.assertIsNotNone(OptimizationEngine().setup_algorithm(exp))


if __name__ == "__main__":
    unittest.main()
