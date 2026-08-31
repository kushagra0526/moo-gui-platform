from .main_layout import create_main_layout
from .problem_definition import create_problem_definition_layout
from .algorithm_config import create_algorithm_config_layout
from .visualization import create_visualization_layout
from .results import create_results_layout
from .login_layout import create_login_layout
from .dashboard_layout import create_dashboard_layout

__all__ = [
    'create_main_layout',
    'create_problem_definition_layout', 
    'create_algorithm_config_layout',
    'create_visualization_layout',
    'create_results_layout',
    'create_login_layout',
    'create_dashboard_layout'
]