"""
Main callback registration for the MOO GUI
"""

from .navigation_callbacks import register_navigation_callbacks
from .problem_callbacks import register_problem_callbacks
from .visualization_callbacks import register_visualization_callbacks
from .results_callbacks import register_results_callbacks
from .optimization_callbacks import register_optimization_callbacks
from .equation_callbacks import register_equation_callbacks
from .cec2018_callbacks import register_cec2018_callbacks
from .prediction_callbacks import register_prediction_callbacks

def register_callbacks(app):
    """Register all application callbacks."""
    register_navigation_callbacks(app)
    register_problem_callbacks(app)
    register_visualization_callbacks(app)
    register_results_callbacks(app)
    register_optimization_callbacks(app)
    register_equation_callbacks(app)
    register_cec2018_callbacks(app)
    register_prediction_callbacks(app)