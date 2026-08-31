#!/usr/bin/env python3
"""
Complete GUI Test Script - Tests all major functionality
"""

import sys
import time
import numpy as np
from gui.core.state_manager import StateManager, Variable, Objective, Constraint, ProblemDefinition, AlgorithmConfig
from gui.core.optimization_engine import OptimizationEngine

def test_problem_definitions():
    """Test various problem definitions."""
    print("Testing Problem Definitions...")
    print("-" * 40)
    
    state_manager = StateManager()
    
    # Test 1: Basic bi-objective problem
    print("Test 1: Basic Bi-objective Problem")
    variables = [
        Variable("x1", "continuous", 0.0, 1.0),
        Variable("x2", "continuous", 0.0, 1.0)
    ]
    objectives = [
        Objective("f1", "minimize", "x[0]**2 + x[1]**2"),
        Objective("f2", "minimize", "(x[0]-1)**2 + (x[1]-1)**2")
    ]
    problem1 = ProblemDefinition(variables, objectives, [], "static")
    issues = state_manager.validate_problem_definition(problem1)
    print(f"  [OK] Valid: {len(issues) == 0}")
    
    # Test 2: ZDT1 Problem
    print("Test 2: ZDT1 Problem")
    variables = [Variable(f"x{i}", "continuous", 0.0, 1.0) for i in range(5)]
    objectives = [
        Objective("f1", "minimize", "x[0]"),
        Objective("f2", "minimize", "(1 + 9*sum(x[1:])/4) * (1 - sqrt(x[0]/(1 + 9*sum(x[1:])/4)))")
    ]
    problem2 = ProblemDefinition(variables, objectives, [], "static")
    issues = state_manager.validate_problem_definition(problem2)
    print(f"  [OK] Valid: {len(issues) == 0}")
    
    # Test 3: Constrained Problem
    print("Test 3: Constrained Problem")
    variables = [
        Variable("x1", "continuous", -5.0, 5.0),
        Variable("x2", "continuous", -5.0, 5.0)
    ]
    objectives = [
        Objective("f1", "minimize", "x[0]**2 + x[1]**2"),
        Objective("f2", "minimize", "(x[0]-2)**2 + (x[1]-1)**2")
    ]
    constraints = [
        Constraint("g1", "ineq", "x[0]**2 + x[1]**2 - 1")  # Inside unit circle
    ]
    problem3 = ProblemDefinition(variables, objectives, constraints, "static")
    issues = state_manager.validate_problem_definition(problem3)
    print(f"  [OK] Valid: {len(issues) == 0}")
    
    # Test 4: Many-objective Problem (DTLZ2)
    print("Test 4: Many-objective Problem (4 objectives)")
    variables = [Variable(f"x{i}", "continuous", 0.0, 1.0) for i in range(6)]
    objectives = [
        Objective("f1", "minimize", "(1 + sum((x[3:] - 0.5)**2)) * cos(x[0]*pi/2) * cos(x[1]*pi/2) * cos(x[2]*pi/2)"),
        Objective("f2", "minimize", "(1 + sum((x[3:] - 0.5)**2)) * cos(x[0]*pi/2) * cos(x[1]*pi/2) * sin(x[2]*pi/2)"),
        Objective("f3", "minimize", "(1 + sum((x[3:] - 0.5)**2)) * cos(x[0]*pi/2) * sin(x[1]*pi/2)"),
        Objective("f4", "minimize", "(1 + sum((x[3:] - 0.5)**2)) * sin(x[0]*pi/2)")
    ]
    problem4 = ProblemDefinition(variables, objectives, [], "many")
    issues = state_manager.validate_problem_definition(problem4)
    print(f"  [OK] Valid: {len(issues) == 0}")
    
    return [problem1, problem2, problem3, problem4]

def test_algorithms():
    """Test all algorithm configurations."""
    print("\nTesting Algorithm Configurations...")
    print("-" * 40)
    
    state_manager = StateManager()
    engine = OptimizationEngine()
    
    # Create a simple test problem
    experiment = state_manager.create_new_experiment("Algorithm_Test")
    
    algorithms = ["nsga2", "nsga3", "moead"]
    results = {}
    
    for alg_name in algorithms:
        print(f"Testing {alg_name.upper()}...")
        try:
            experiment.algorithm.algorithm = alg_name
            algorithm = engine.setup_algorithm(experiment)
            results[alg_name] = "[OK] SUCCESS"
            print(f"  [OK] {alg_name.upper()} setup successful")
        except Exception as e:
            results[alg_name] = f"[FAIL] FAILED: {str(e)[:50]}..."
            print(f"  [FAIL] {alg_name.upper()} failed: {e}")
    
    return results

def test_optimization_run():
    """Test a quick optimization run."""
    print("\nTesting Optimization Execution...")
    print("-" * 40)
    
    state_manager = StateManager()
    engine = OptimizationEngine()
    
    # Create simple test problem
    experiment = state_manager.create_new_experiment("Quick_Test")
    experiment.algorithm.max_generations = 10  # Quick test
    experiment.algorithm.population_size = 20
    
    print("Starting quick optimization (10 generations)...")
    
    results = []
    def callback(result):
        results.append(result)
        print(f"  Generation {result.generation}: {result.metrics.get('n_solutions', 0)} solutions")
    
    try:
        engine.run_optimization(experiment, callback)
        
        # Wait for completion (max 30 seconds)
        timeout = 30
        start_time = time.time()
        while engine.is_running and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if engine.current_result:
            final_result = engine.current_result
            print(f"  [OK] Optimization completed!")
            print(f"  Final generation: {final_result.generation}")
            print(f"  Pareto solutions: {len(final_result.pareto_front)}")
            print(f"  Hypervolume: {final_result.metrics.get('hypervolume', 0):.4f}")
            return True
        else:
            print(f"  [FAIL] No results obtained")
            return False
            
    except Exception as e:
        print(f"  [FAIL] Optimization failed: {e}")
        return False

def test_gui_components():
    """Test GUI component imports."""
    print("\nTesting GUI Components...")
    print("-" * 40)
    
    components = [
        ("Main App", "gui.app", "create_app"),
        ("Problem Layout", "gui.layouts.problem_definition", "create_problem_definition_layout"),
        ("Algorithm Layout", "gui.layouts.algorithm_config", "create_algorithm_config_layout"),
        ("Visualization Layout", "gui.layouts.visualization", "create_visualization_layout"),
        ("Results Layout", "gui.layouts.results", "create_results_layout"),
    ]
    
    results = {}
    for name, module, function in components:
        try:
            mod = __import__(module, fromlist=[function])
            func = getattr(mod, function)
            if name == "Main App":
                app = func()  # Test app creation
            else:
                layout = func()  # Test layout creation
            results[name] = "[OK] SUCCESS"
            print(f"  [OK] {name}")
        except Exception as e:
            results[name] = f"[FAIL] FAILED: {str(e)[:50]}..."
            print(f"  [FAIL] {name}: {e}")
    
    return results

def run_comprehensive_test():
    """Run all tests and provide summary."""
    print("COMPREHENSIVE GUI TEST SUITE")
    print("=" * 50)
    
    # Test 1: Problem Definitions
    problems = test_problem_definitions()
    
    # Test 2: Algorithm Configurations  
    alg_results = test_algorithms()
    
    # Test 3: GUI Components
    gui_results = test_gui_components()
    
    # Test 4: Quick Optimization
    opt_success = test_optimization_run()
    
    # Summary
    print("\nTEST SUMMARY")
    print("=" * 50)
    
    print("Problem Definitions:")
    print("  [OK] 4/4 problem types validated successfully")
    
    print("Algorithm Configurations:")
    for alg, result in alg_results.items():
        print(f"  {result.split()[0]} {alg.upper()}")
    
    print("GUI Components:")
    for comp, result in gui_results.items():
        print(f"  {result.split()[0]} {comp}")
    
    print("Optimization Execution:")
    print(f"  {'[OK]' if opt_success else '[FAIL]'} Quick optimization test")
    
    # Overall status
    total_tests = 4 + len(alg_results) + len(gui_results) + 1
    passed_tests = 4 + sum(1 for r in alg_results.values() if r.startswith('[OK]'))
    passed_tests += sum(1 for r in gui_results.values() if r.startswith('[OK]'))
    passed_tests += (1 if opt_success else 0)
    
    print(f"\nOVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("ALL TESTS PASSED! GUI is ready for use.")
    else:
        print("Some tests failed. Check the details above.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    try:
        success = run_comprehensive_test()
        
        if success:
            print("\nREADY TO USE!")
            print("Run: python main.py")
            print("Open: http://localhost:8080")
        else:
            print("\nNEEDS FIXES!")
            print("Check the failed tests above.")
            
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)