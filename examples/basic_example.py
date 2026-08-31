#!/usr/bin/env python3
"""
Basic example demonstrating the MOO GUI core functionality
This example shows how to use the core components programmatically
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
from gui.core.state_manager import StateManager, Variable, Objective, Constraint, ProblemDefinition, AlgorithmConfig
from gui.core.optimization_engine import OptimizationEngine

def create_zdt1_problem():
    """Create the ZDT1 benchmark problem."""
    
    # Define 30 decision variables
    variables = []
    for i in range(30):
        variables.append(Variable(f"x{i}", "continuous", 0.0, 1.0))
    
    # Define objectives
    objectives = [
        Objective("f1", "minimize", "x[0]"),
        Objective("f2", "minimize", "(1 + 9*sum(x[1:])/len(x[1:])) * (1 - sqrt(x[0]/(1 + 9*sum(x[1:])/len(x[1:]))))")
    ]
    
    # No constraints for ZDT1
    constraints = []
    
    return ProblemDefinition(
        variables=variables,
        objectives=objectives,
        constraints=constraints,
        problem_type="static"
    )

def create_algorithm_config():
    """Create NSGA-II algorithm configuration."""
    return AlgorithmConfig(
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

def run_optimization_example():
    """Run a complete optimization example."""
    print("Multi-Objective Optimization Example")
    print("=" * 40)
    
    # Create state manager
    state_manager = StateManager()
    
    # Create experiment
    experiment = state_manager.create_new_experiment(
        name="ZDT1_Example",
        description="ZDT1 benchmark problem with NSGA-II"
    )
    
    # Update problem definition
    problem = create_zdt1_problem()
    state_manager.update_problem_definition(problem)
    
    # Update algorithm configuration
    algorithm_config = create_algorithm_config()
    state_manager.update_algorithm_config(algorithm_config)
    
    # Validate problem
    issues = state_manager.validate_problem_definition(problem)
    if issues:
        print("Problem validation issues:")
        for issue in issues:
            print(f"  - {issue}")
        return
    
    print("✓ Problem definition is valid")
    
    # Create optimization engine
    engine = OptimizationEngine()
    
    # Define callback for progress monitoring
    def progress_callback(result):
        if result.generation % 50 == 0:  # Print every 50 generations
            metrics = result.metrics
            print(f"Generation {result.generation}: "
                  f"HV={metrics.get('hypervolume', 0):.4f}, "
                  f"Solutions={metrics.get('n_solutions', 0)}")
    
    print(f"Starting optimization with {algorithm_config.algorithm.upper()}...")
    print(f"Population size: {algorithm_config.population_size}")
    print(f"Max generations: {algorithm_config.max_generations}")
    
    # Run optimization
    engine.run_optimization(experiment, progress_callback)
    
    # Wait for completion
    while engine.is_running:
        import time
        time.sleep(0.1)
    
    # Get final results
    final_result = engine.current_result
    
    if final_result:
        print("\nOptimization completed!")
        print(f"Final generation: {final_result.generation}")
        print(f"Number of Pareto-optimal solutions: {len(final_result.pareto_front)}")
        print(f"Final hypervolume: {final_result.metrics.get('hypervolume', 0):.6f}")
        
        # Plot results
        plot_results(final_result)
        
        # Save experiment
        try:
            state_manager.save_experiment("zdt1_example.json")
            print("✓ Experiment saved to zdt1_example.json")
        except Exception as e:
            print(f"Failed to save experiment: {e}")
    
    else:
        print("Optimization failed or was interrupted")

def plot_results(result):
    """Plot the Pareto front."""
    try:
        pareto_front = result.pareto_front
        
        plt.figure(figsize=(10, 6))
        plt.scatter(pareto_front[:, 0], pareto_front[:, 1], 
                   c='red', alpha=0.7, s=30, label='Pareto Front')
        
        # Plot true Pareto front for comparison
        x_true = np.linspace(0, 1, 100)
        y_true = 1 - np.sqrt(x_true)
        plt.plot(x_true, y_true, 'b--', linewidth=2, label='True Pareto Front')
        
        plt.xlabel('Objective 1 (f1)')
        plt.ylabel('Objective 2 (f2)')
        plt.title('ZDT1 Problem - Pareto Front Comparison')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save plot
        plt.savefig('zdt1_pareto_front.png', dpi=300, bbox_inches='tight')
        print("✓ Pareto front plot saved to zdt1_pareto_front.png")
        
        # Show plot if running interactively
        plt.show()
        
    except Exception as e:
        print(f"Failed to create plot: {e}")

def demonstrate_state_management():
    """Demonstrate state management capabilities."""
    print("\nState Management Demo")
    print("-" * 20)
    
    # Create state manager
    state_manager = StateManager()
    
    # Create and configure experiment
    experiment = state_manager.create_new_experiment("Demo", "State management demo")
    
    # Show current state
    current_state = state_manager.get_current_state()
    print(f"Experiment name: {current_state['name']}")
    print(f"Number of variables: {len(current_state['problem']['variables'])}")
    print(f"Number of objectives: {len(current_state['problem']['objectives'])}")
    print(f"Algorithm: {current_state['algorithm']['algorithm']}")
    
    # Validate problem
    issues = state_manager.validate_problem_definition(experiment.problem)
    if issues:
        print("Validation issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✓ Problem definition is valid")

if __name__ == "__main__":
    try:
        # Run state management demo
        demonstrate_state_management()
        
        # Run full optimization example
        run_optimization_example()
        
    except KeyboardInterrupt:
        print("\nExample interrupted by user")
    except Exception as e:
        print(f"Example failed with error: {e}")
        import traceback
        traceback.print_exc()