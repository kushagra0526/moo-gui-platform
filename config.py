#!/usr/bin/env python3
"""
Configuration settings for the Multi-Objective Optimization GUI
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class AppConfig:
    """Application configuration settings."""
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8050
    debug: bool = True
    
    # Application settings
    app_title: str = "Multi-Objective Optimization GUI"
    app_description: str = "Research-grade interface for pymoo-based optimization"
    
    # File paths
    assets_folder: str = "assets"
    experiments_folder: str = "experiments"
    exports_folder: str = "exports"
    
    # Optimization settings
    default_population_size: int = 100
    default_max_generations: int = 250
    default_random_seed: int = 42
    max_population_size: int = 1000
    max_generations: int = 10000
    
    # Visualization settings
    default_plot_width: int = 800
    default_plot_height: int = 600
    max_plot_points: int = 10000
    update_interval_ms: int = 1000
    
    # Performance settings
    max_concurrent_optimizations: int = 1
    optimization_timeout_minutes: int = 60
    memory_limit_mb: int = 2048
    
    # UI settings
    sidebar_width: int = 250
    content_padding: int = 20
    card_border_radius: int = 8
    
    # Export settings
    export_formats: list = None
    max_export_size_mb: int = 100
    
    def __post_init__(self):
        """Initialize default values that depend on other settings."""
        if self.export_formats is None:
            self.export_formats = ["csv", "json", "png", "pdf", "python"]
        
        # Create directories if they don't exist
        for folder in [self.experiments_folder, self.exports_folder]:
            os.makedirs(folder, exist_ok=True)

@dataclass
class AlgorithmDefaults:
    """Default algorithm parameters."""
    
    # NSGA-II defaults
    nsga2_params: Dict[str, Any] = None
    
    # NSGA-III defaults
    nsga3_params: Dict[str, Any] = None
    
    # MOEA/D defaults
    moead_params: Dict[str, Any] = None
    
    # RM-MEDA defaults
    rmmeda_params: Dict[str, Any] = None
    
    # MOPSO defaults
    mopso_params: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default algorithm parameters."""
        if self.nsga2_params is None:
            self.nsga2_params = {
                "sampling": "random",
                "tournament_size": 2,
                "tournament_pressure": 1.0,
                "crossover_prob": 0.9,
                "crossover_eta": 15,
                "mutation_prob": 0.1,
                "mutation_eta": 20
            }
        
        if self.nsga3_params is None:
            self.nsga3_params = {
                "ref_dirs": "das_dennis",
                "partitions": 12,
                "crossover_prob": 0.9,
                "crossover_eta": 30,
                "mutation_prob": 0.1,
                "mutation_eta": 20
            }
        
        if self.moead_params is None:
            self.moead_params = {
                "decomposition": "tchebi",
                "neighborhood_size": 20,
                "prob_delta": 0.9,
                "crossover_prob": 1.0,
                "crossover_eta": 20,
                "mutation_prob": 0.1,
                "mutation_eta": 20
            }
        
        if self.rmmeda_params is None:
            self.rmmeda_params = {
                "n_clusters": 3,
                "alpha": 0.25
            }
        
        if self.mopso_params is None:
            self.mopso_params = {
                "w": 0.4,
                "c1": 2.0,
                "c2": 2.0,
                "adaptive": True
            }

@dataclass
class ValidationRules:
    """Validation rules for problem definition."""
    
    min_variables: int = 1
    max_variables: int = 100
    min_objectives: int = 2
    max_objectives: int = 20
    max_constraints: int = 50
    
    # Variable bounds
    min_bound_value: float = -1e6
    max_bound_value: float = 1e6
    
    # Expression validation
    allowed_functions: list = None
    forbidden_keywords: list = None
    
    def __post_init__(self):
        """Initialize validation lists."""
        if self.allowed_functions is None:
            self.allowed_functions = [
                "sin", "cos", "tan", "exp", "log", "sqrt", "abs",
                "sum", "max", "min", "pow", "pi", "e"
            ]
        
        if self.forbidden_keywords is None:
            self.forbidden_keywords = [
                "import", "exec", "eval", "open", "file", "__",
                "globals", "locals", "vars", "dir"
            ]

class ConfigManager:
    """Configuration manager for the application."""
    
    def __init__(self):
        self.app_config = AppConfig()
        self.algorithm_defaults = AlgorithmDefaults()
        self.validation_rules = ValidationRules()
        
        # Load from environment variables if available
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Server settings
        if os.getenv("MOO_GUI_HOST"):
            self.app_config.host = os.getenv("MOO_GUI_HOST")
        
        if os.getenv("MOO_GUI_PORT"):
            try:
                self.app_config.port = int(os.getenv("MOO_GUI_PORT"))
            except ValueError:
                pass
        
        if os.getenv("MOO_GUI_DEBUG"):
            self.app_config.debug = os.getenv("MOO_GUI_DEBUG").lower() == "true"
        
        # Performance settings
        if os.getenv("MOO_GUI_MEMORY_LIMIT"):
            try:
                self.app_config.memory_limit_mb = int(os.getenv("MOO_GUI_MEMORY_LIMIT"))
            except ValueError:
                pass
        
        if os.getenv("MOO_GUI_TIMEOUT"):
            try:
                self.app_config.optimization_timeout_minutes = int(os.getenv("MOO_GUI_TIMEOUT"))
            except ValueError:
                pass
    
    def get_algorithm_params(self, algorithm: str) -> Dict[str, Any]:
        """Get default parameters for a specific algorithm."""
        param_map = {
            "nsga2": self.algorithm_defaults.nsga2_params,
            "nsga3": self.algorithm_defaults.nsga3_params,
            "moead": self.algorithm_defaults.moead_params,
            "rmmeda": self.algorithm_defaults.rmmeda_params,
            "mopso": self.algorithm_defaults.mopso_params
        }
        
        return param_map.get(algorithm, {})
    
    def validate_expression(self, expression: str) -> list:
        """Validate a mathematical expression."""
        issues = []
        
        # Check for forbidden keywords
        for keyword in self.validation_rules.forbidden_keywords:
            if keyword in expression:
                issues.append(f"Forbidden keyword '{keyword}' found in expression")
        
        # Check for basic syntax
        if not expression.strip():
            issues.append("Expression cannot be empty")
        
        # Try to compile the expression
        try:
            compile(expression, '<expression>', 'eval')
        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")
        
        return issues
    
    def get_export_path(self, filename: str) -> str:
        """Get full path for export file."""
        return os.path.join(self.app_config.exports_folder, filename)
    
    def get_experiment_path(self, filename: str) -> str:
        """Get full path for experiment file."""
        return os.path.join(self.app_config.experiments_folder, filename)

# Global configuration instance
config = ConfigManager()

# Convenience functions
def get_app_config() -> AppConfig:
    """Get application configuration."""
    return config.app_config

def get_algorithm_defaults() -> AlgorithmDefaults:
    """Get algorithm default parameters."""
    return config.algorithm_defaults

def get_validation_rules() -> ValidationRules:
    """Get validation rules."""
    return config.validation_rules

def get_algorithm_params(algorithm: str) -> Dict[str, Any]:
    """Get default parameters for an algorithm."""
    return config.get_algorithm_params(algorithm)

def validate_expression(expression: str) -> list:
    """Validate a mathematical expression."""
    return config.validate_expression(expression)