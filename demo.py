#!/usr/bin/env python3
"""
Quick demo of the Multi-Objective Optimization GUI core functionality
"""

import sys
import numpy as np
from gui.core.state_manager import StateManager, Variable, Objective, ProblemDefinition, AlgorithmConfig


def demo_state_management():
    """Demonstrate state management capabilities."""
    print("Multi-Objective Optimization GUI - Core Demo")
    print("=" * 50)
    
    # Create state manager
    state_manager = StateManager()
    print("  [OK] State manager created")
    
    # Create a new experiment
    experiment = state_manager.create_new_experiment(
        name="Demo_Experiment",
        description="Demonstration of core functionality"
    )
    print(f"  [OK] Created experiment: {experiment.name}")
    
    # Show default problem
    print(f"\nDefault Problem Configuration:")
    print(f"  Variables: {len(experiment.problem.variables)}")
    for i, var in enumerate(experiment.problem.variables):
        print(f"    {var.name}: {var.type} [{var.lower_bound}, {var.upper_bound}]")
    
    print(f"  Objectives: {len(experiment.problem.objectives)}")
    for i, obj in enumerate(experiment.problem.objectives):
        print(f"    {obj.name}: {obj.direction} - {obj.expression}")
    
    print(f"  Constraints: {len(experiment.problem.constraints)}")
    
    # Validate the problem
    issues = state_manager.validate_problem_definition(experiment.problem)
    if issues:
        print(f"\n  [!] Validation issues found:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print(f"\n  [OK] Problem definition is valid!")
    
    # Show algorithm configuration
    print(f"\nAlgorithm Configuration:")
    print(f"  Algorithm: {experiment.algorithm.algorithm}")
    print(f"  Population Size: {experiment.algorithm.population_size}")
    print(f"  Max Generations: {experiment.algorithm.max_generations}")
    print(f"  Random Seed: {experiment.algorithm.random_seed}")
    
    # Create a custom problem
    print(f"\n" + "-" * 30)
    print("Creating Custom Problem (ZDT1-like)")
    
    # Define variables
    variables = [
        Variable("x1", "continuous", 0.0, 1.0),
        Variable("x2", "continuous", 0.0, 1.0),
        Variable("x3", "continuous", 0.0, 1.0)
    ]
    
    # Define objectives
    objectives = [
        Objective("minimize_f1", "minimize", "x[0]"),
        Objective("minimize_f2", "minimize", "1 - sqrt(x[0])")
    ]
    
    # Define constraints (optional)
    constraints = []
    
    # Create problem definition
    custom_problem = ProblemDefinition(
        variables=variables,
        objectives=objectives,
        constraints=constraints,
        problem_type="static"
    )
    
    # Update the experiment
    state_manager.update_problem_definition(custom_problem)
    print("  [OK] Updated problem definition")
    
    # Validate custom problem
    issues = state_manager.validate_problem_definition(custom_problem)
    if issues:
        print(f"  [FAIL] Custom problem validation issues:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print(f"  [OK] Custom problem is valid!")
    
    # Show updated configuration
    current_state = state_manager.get_current_state()
    print(f"\nUpdated Configuration:")
    print(f"  Variables: {len(current_state['problem']['variables'])}")
    print(f"  Objectives: {len(current_state['problem']['objectives'])}")
    print(f"  Problem Type: {current_state['problem']['problem_type']}")
    
    # Save experiment
    try:
        state_manager.save_experiment("demo_experiment.json")
        print(f"  [OK] Experiment saved to demo_experiment.json")
    except Exception as e:
        print(f"  [FAIL] Failed to save experiment: {e}")
    
    print(f"\nDemo completed successfully!")
    print(f"To run the full GUI, execute: python main.py")
    print(f"Then open your browser to: http://localhost:8080")


def demo_algorithm_setup():
    """Demonstrate algorithm setup without running optimization."""
    print(f"\n" + "=" * 50)
    print("Algorithm Setup Demo")
    print("=" * 50)
    
    from gui.core.optimization_engine import OptimizationEngine
    
    # Create state manager and experiment
    state_manager = StateManager()
    experiment = state_manager.create_new_experiment("Algorithm_Demo")
    
    # Create optimization engine
    engine = OptimizationEngine()
    print("  [OK] Optimization engine created")
    
    # Test different algorithms
    algorithms = ["nsga2", "nsga3", "moead"]
    
    for alg_name in algorithms:
        try:
            # Update algorithm
            experiment.algorithm.algorithm = alg_name
            
            # Setup algorithm
            algorithm = engine.setup_algorithm(experiment)
            print(f"  [OK] {alg_name.upper()} algorithm setup successful")
            
        except Exception as e:
            print(f"  [FAIL] {alg_name.upper()} setup failed: {e}")
    
    print(f"\nAlgorithm setup demo completed!")


if __name__ == "__main__":
    try:
        demo_state_management()
        demo_algorithm_setup()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)