#!/usr/bin/env python3
"""
Basic example demonstrating the MOO GUI core functionality programmatically.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from gui.core.state_manager import StateManager, Variable, Objective, Constraint, ProblemDefinition, AlgorithmConfig
from gui.core.optimization_engine import OptimizationEngine

def create_zdt1_problem():
    """Create the ZDT1 benchmark problem."""
    variables = [Variable(f"x{i}", "continuous", 0.0, 1.0) for i in range(30)]
    objectives = [
        Objective("f1", "minimize", "x[0]"),
        Objective("f2", "minimize", "(1 + 9*sum(x[1:])/len(x[1:])) * (1 - sqrt(x[0]/(1 + 9*sum(x[1:])/len(x[1:]))))")
    ]
    return ProblemDefinition(
        variables=variables,
        objectives=objectives,
        constraints=[],
        problem_type="static"
    )

def create_algorithm_config():
    """Create NSGA-II algorithm configuration."""
    return AlgorithmConfig(
        algorithm="nsga2",
        population_size=50,
        max_generations=50,
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

def run_optimization_example():
    """Run a complete optimization example."""
    print("\nMulti-Objective Optimization Example")
    print("=" * 40)
    
    state_manager = StateManager()
    experiment = state_manager.create_new_experiment(
        name="ZDT1_Example",
        description="ZDT1 benchmark problem with NSGA-II"
    )
    
    problem = create_zdt1_problem()
    state_manager.update_problem_definition(problem)
    
    algorithm_config = create_algorithm_config()
    state_manager.update_algorithm_config(algorithm_config)
    
    issues = state_manager.validate_problem_definition(problem)
    if issues:
        print("Problem validation issues:")
        for issue in issues:
            print(f"  - {issue}")
        return
    
    print("  [OK] Problem definition is valid")
    
    engine = OptimizationEngine()
    
    def progress_callback(result):
        if result.generation % 10 == 0:
            metrics = result.metrics
            print(f"  Generation {result.generation}: "
                  f"HV={metrics.get('hypervolume', 0):.4f}, "
                  f"Solutions={metrics.get('n_solutions', 0)}")
    
    print(f"Starting optimization with {algorithm_config.algorithm.upper()}...")
    engine.run_optimization(experiment, progress_callback)
    
    while engine.is_running:
        import time
        time.sleep(0.1)
    
    final_result = engine.current_result
    if final_result:
        print("\nOptimization completed successfully!")
        print(f"Final generation: {final_result.generation}")
        print(f"Pareto solutions: {len(final_result.pareto_front)}")
        print(f"Final hypervolume: {final_result.metrics.get('hypervolume', 0):.6f}")
    else:
        print("Optimization failed or was interrupted")

def demonstrate_state_management():
    """Demonstrate state management capabilities."""
    print("State Management Demo")
    print("-" * 20)
    
    state_manager = StateManager()
    experiment = state_manager.create_new_experiment("Demo", "State management demo")
    current_state = state_manager.get_current_state()
    print(f"Experiment name: {current_state['name']}")
    print(f"Variables: {len(current_state['problem']['variables'])}")
    print(f"Objectives: {len(current_state['problem']['objectives'])}")
    print(f"Algorithm: {current_state['algorithm']['algorithm']}")
    
    issues = state_manager.validate_problem_definition(experiment.problem)
    if issues:
        print("Validation issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("  [OK] Problem definition is valid")

if __name__ == "__main__":
    try:
        demonstrate_state_management()
        run_optimization_example()
    except KeyboardInterrupt:
        print("\nExample interrupted by user")
    except Exception as e:
        print(f"Example failed with error: {e}")
        import traceback
        traceback.print_exc()