#!/usr/bin/env python3
"""
Test script to verify the MOO GUI installation and basic functionality
"""

import sys
import importlib
import traceback

def test_imports():
    """Test that all required packages can be imported."""
    required_packages = [
        'dash',
        'dash_bootstrap_components',
        'plotly',
        'numpy',
        'pandas',
        'pymoo',
        'scipy',
        'yaml'
    ]
    
    print("Testing package imports...")
    failed_imports = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"  [OK] {package}")
        except ImportError as e:
            print(f"  [FAIL] {package}: {e}")
            failed_imports.append(package)
    
    if failed_imports:
        print(f"\nFailed to import: {', '.join(failed_imports)}")
        print("Please install missing packages using: pip install -r requirements.txt")
        return False
    
    print("\nAll required packages imported successfully!")
    return True

def test_gui_components():
    """Test that GUI components can be imported."""
    print("\nTesting GUI components...")
    
    try:
        from gui.app import create_app
        from gui.core.state_manager import StateManager
        from gui.core.optimization_engine import OptimizationEngine
        print("  [OK] GUI components imported successfully")
        return True
    except Exception as e:
        print(f"  [FAIL] GUI component import failed: {e}")
        traceback.print_exc()
        return False

def test_app_creation():
    """Test that the Dash app can be created."""
    print("\nTesting app creation...")
    
    try:
        from gui.app import create_app
        app = create_app()
        print("  [OK] Dash app created successfully")
        return True
    except Exception as e:
        print(f"  [FAIL] App creation failed: {e}")
        traceback.print_exc()
        return False

def test_optimization_engine():
    """Test basic optimization engine functionality."""
    print("\nTesting optimization engine...")
    
    try:
        from gui.core.optimization_engine import OptimizationEngine
        from gui.core.state_manager import StateManager, ExperimentState
        
        # Create a simple test experiment
        state_manager = StateManager()
        experiment = state_manager.create_new_experiment("test_experiment")
        
        # Create optimization engine
        engine = OptimizationEngine()
        
        # Test algorithm setup
        algorithm = engine.setup_algorithm(experiment)
        print("  [OK] Optimization engine working correctly")
        return True
    except Exception as e:
        print(f"  [FAIL] Optimization engine test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Multi-Objective Optimization GUI - Installation Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_gui_components,
        test_app_creation,
        test_optimization_engine
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  [FAIL] Test failed with exception: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! The installation is working correctly.")
        print("\nYou can now run the GUI with: python main.py")
        return 0
    else:
        print("Some tests failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())