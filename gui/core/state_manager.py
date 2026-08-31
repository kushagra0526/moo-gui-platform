"""
State management for the MOO GUI application
"""

import json
import yaml
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class Variable:
    """Decision variable definition."""
    name: str
    type: str  # 'continuous', 'integer', 'binary'
    lower_bound: float
    upper_bound: float
    initial_value: Optional[float] = None

@dataclass
class Objective:
    """Objective function definition."""
    name: str
    direction: str  # 'minimize', 'maximize'
    expression: str
    is_dynamic: bool = False

@dataclass
class Constraint:
    """Constraint definition."""
    name: str
    type: str  # 'ineq', 'eq'
    expression: str
    is_dynamic: bool = False

@dataclass
class ProblemDefinition:
    """Complete problem definition."""
    variables: List[Variable]
    objectives: List[Objective]
    constraints: List[Constraint]
    problem_type: str  # 'static', 'dynamic', 'many'

@dataclass
class AlgorithmConfig:
    """Algorithm configuration."""
    algorithm: str
    population_size: int
    max_generations: int
    random_seed: int
    parameters: Dict[str, Any]
    many_objective_options: List[str]
    dynamic_options: List[str]

@dataclass
class ExperimentState:
    """Complete experiment state."""
    name: str
    description: str
    problem: ProblemDefinition
    algorithm: AlgorithmConfig
    created_at: str
    modified_at: str
    results: Optional[Dict[str, Any]] = None

class StateManager:
    """Manages application state and experiment persistence."""
    
    def __init__(self):
        self.current_experiment: Optional[ExperimentState] = None
        self.experiments_history: List[ExperimentState] = []
        
    def create_new_experiment(self, name: str, description: str = "") -> ExperimentState:
        """Create a new experiment with default settings."""
        now = datetime.now().isoformat()
        
        # Default problem definition
        default_problem = ProblemDefinition(
            variables=[
                Variable("x0", "continuous", 0.0, 1.0),
                Variable("x1", "continuous", 0.0, 1.0)
            ],
            objectives=[
                Objective("objective_0", "minimize", "x[0]**2 + x[1]**2"),
                Objective("objective_1", "minimize", "(x[0]-1)**2 + (x[1]-1)**2")
            ],
            constraints=[],
            problem_type="static"
        )
        
        # Default algorithm configuration
        default_algorithm = AlgorithmConfig(
            algorithm="nsga2",
            population_size=100,
            max_generations=250,
            random_seed=42,
            parameters={
                "sampling": "random",
                "tournament_size": 2,
                "tournament_pressure": 1.0,
                "crossover_prob": 0.9,
                "crossover_eta": 15,
                "mutation_prob": 0.1,
                "mutation_eta": 20
            },
            many_objective_options=[],
            dynamic_options=[]
        )
        
        experiment = ExperimentState(
            name=name,
            description=description,
            problem=default_problem,
            algorithm=default_algorithm,
            created_at=now,
            modified_at=now
        )
        
        self.current_experiment = experiment
        return experiment
    
    def update_problem_definition(self, problem: ProblemDefinition):
        """Update the current experiment's problem definition."""
        if self.current_experiment:
            self.current_experiment.problem = problem
            self.current_experiment.modified_at = datetime.now().isoformat()
    
    def update_algorithm_config(self, algorithm: AlgorithmConfig):
        """Update the current experiment's algorithm configuration."""
        if self.current_experiment:
            self.current_experiment.algorithm = algorithm
            self.current_experiment.modified_at = datetime.now().isoformat()
    
    def save_experiment(self, filepath: str):
        """Save the current experiment to file."""
        if not self.current_experiment:
            raise ValueError("No current experiment to save")
        
        experiment_dict = asdict(self.current_experiment)
        
        if filepath.endswith('.json'):
            with open(filepath, 'w') as f:
                json.dump(experiment_dict, f, indent=2)
        elif filepath.endswith('.yaml') or filepath.endswith('.yml'):
            with open(filepath, 'w') as f:
                yaml.dump(experiment_dict, f, default_flow_style=False)
        else:
            raise ValueError("Unsupported file format. Use .json or .yaml")
    
    def load_experiment(self, filepath: str) -> ExperimentState:
        """Load an experiment from file."""
        if filepath.endswith('.json'):
            with open(filepath, 'r') as f:
                experiment_dict = json.load(f)
        elif filepath.endswith('.yaml') or filepath.endswith('.yml'):
            with open(filepath, 'r') as f:
                experiment_dict = yaml.safe_load(f)
        else:
            raise ValueError("Unsupported file format. Use .json or .yaml")
        
        # Reconstruct dataclass objects
        experiment = self._dict_to_experiment(experiment_dict)
        self.current_experiment = experiment
        
        # Add to history if not already present
        if experiment not in self.experiments_history:
            self.experiments_history.append(experiment)
        
        return experiment
    
    def _dict_to_experiment(self, data: Dict[str, Any]) -> ExperimentState:
        """Convert dictionary to ExperimentState object."""
        # Reconstruct nested objects
        variables = [Variable(**var) for var in data['problem']['variables']]
        objectives = [Objective(**obj) for obj in data['problem']['objectives']]
        constraints = [Constraint(**con) for con in data['problem']['constraints']]
        
        problem = ProblemDefinition(
            variables=variables,
            objectives=objectives,
            constraints=constraints,
            problem_type=data['problem']['problem_type']
        )
        
        algorithm = AlgorithmConfig(**data['algorithm'])
        
        return ExperimentState(
            name=data['name'],
            description=data['description'],
            problem=problem,
            algorithm=algorithm,
            created_at=data['created_at'],
            modified_at=data['modified_at'],
            results=data.get('results')
        )
    
    def validate_problem_definition(self, problem: ProblemDefinition) -> List[str]:
        """Validate problem definition and return list of issues."""
        issues = []
        
        # Check variables
        if not problem.variables:
            issues.append("At least one decision variable is required")
        
        for i, var in enumerate(problem.variables):
            if var.lower_bound >= var.upper_bound:
                issues.append(f"Variable {var.name}: lower bound must be less than upper bound")
            
            if var.type == 'binary' and (var.lower_bound != 0 or var.upper_bound != 1):
                issues.append(f"Binary variable {var.name}: bounds must be [0, 1]")
        
        # Check objectives
        if len(problem.objectives) < 2:
            issues.append("At least two objectives are required for multi-objective optimization")
        
        for obj in problem.objectives:
            if not obj.expression.strip():
                issues.append(f"Objective {obj.name}: expression cannot be empty")
        
        # Check constraints
        for con in problem.constraints:
            if not con.expression.strip():
                issues.append(f"Constraint {con.name}: expression cannot be empty")
        
        return issues
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current application state as dictionary."""
        if not self.current_experiment:
            return {}
        
        return asdict(self.current_experiment)