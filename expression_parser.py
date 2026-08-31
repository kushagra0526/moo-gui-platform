#!/usr/bin/env python3
"""
Expression parser for mathematical expressions in optimization problems.
Safely evaluates user-defined objective and constraint functions.
"""

import re
import ast
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
import math


class ExpressionParser:
    """
    Safe parser and evaluator for mathematical expressions.
    Supports numpy operations and common mathematical functions.
    """
    
    # Allowed functions and constants
    SAFE_FUNCTIONS = {
        # Math functions
        'sin': np.sin,
        'cos': np.cos,
        'tan': np.tan,
        'arcsin': np.arcsin,
        'arccos': np.arccos,
        'arctan': np.arctan,
        'sinh': np.sinh,
        'cosh': np.cosh,
        'tanh': np.tanh,
        'exp': np.exp,
        'log': np.log,
        'log10': np.log10,
        'log2': np.log2,
        'sqrt': np.sqrt,
        'abs': np.abs,
        'floor': np.floor,
        'ceil': np.ceil,
        'round': np.round,
        'sign': np.sign,
        
        # Aggregation functions
        'sum': np.sum,
        'mean': np.mean,
        'max': np.max,
        'min': np.min,
        'std': np.std,
        'var': np.var,
        
        # Power functions
        'pow': np.power,
        'square': np.square,
        
        # Constants
        'pi': np.pi,
        'e': np.e,
    }
    
    # Forbidden patterns for security
    FORBIDDEN_PATTERNS = [
        r'__\w+__',  # Dunder methods
        r'import\s',
        r'exec\s*\(',
        r'eval\s*\(',
        r'compile\s*\(',
        r'open\s*\(',
        r'file\s*\(',
        r'globals\s*\(',
        r'locals\s*\(',
        r'vars\s*\(',
        r'dir\s*\(',
        r'getattr',
        r'setattr',
        r'delattr',
        r'hasattr',
    ]
    
    def __init__(self):
        """Initialize the expression parser."""
        self.compiled_cache: Dict[str, Any] = {}
    
    def validate(self, expression: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an expression for safety and syntax.
        
        Args:
            expression: Mathematical expression string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not expression or not expression.strip():
            return False, "Expression cannot be empty"
        
        # Check for forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, expression, re.IGNORECASE):
                return False, f"Forbidden pattern detected: {pattern}"
        
        # Try to parse as AST
        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"
        
        # Validate AST nodes
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                return False, "Import statements are not allowed"
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name not in self.SAFE_FUNCTIONS:
                        return False, f"Unknown or unsafe function: {func_name}"
        
        return True, None
    
    def compile(self, expression: str, cache_key: Optional[str] = None) -> Any:
        """
        Compile an expression for faster evaluation.
        
        Args:
            expression: Mathematical expression string
            cache_key: Optional key for caching compiled expression
            
        Returns:
            Compiled code object
            
        Raises:
            ValueError: If expression is invalid
        """
        # Check cache
        if cache_key and cache_key in self.compiled_cache:
            return self.compiled_cache[cache_key]
        
        # Validate expression
        is_valid, error = self.validate(expression)
        if not is_valid:
            raise ValueError(f"Invalid expression: {error}")
        
        # Compile expression
        try:
            code = compile(expression, '<expression>', 'eval')
        except Exception as e:
            raise ValueError(f"Failed to compile expression: {str(e)}")
        
        # Cache if key provided
        if cache_key:
            self.compiled_cache[cache_key] = code
        
        return code
    
    def evaluate(self, expression: str, variables: Dict[str, Any], 
                 time: Optional[float] = None) -> Any:
        """
        Evaluate a mathematical expression with given variables.
        
        Args:
            expression: Mathematical expression string
            variables: Dictionary of variable names to values
            time: Optional time parameter for dynamic problems
            
        Returns:
            Evaluation result
            
        Raises:
            ValueError: If expression is invalid or evaluation fails
        """
        # Compile expression
        code = self.compile(expression)
        
        # Prepare namespace
        namespace = {
            **self.SAFE_FUNCTIONS,
            **variables,
            'np': np,  # Allow numpy operations
        }
        
        # Add time if provided
        if time is not None:
            namespace['t'] = time
        
        # Evaluate
        try:
            result = eval(code, {"__builtins__": {}}, namespace)
            return result
        except Exception as e:
            raise ValueError(f"Failed to evaluate expression: {str(e)}")
    
    def evaluate_vectorized(self, expression: str, X: np.ndarray, 
                           time: Optional[float] = None) -> np.ndarray:
        """
        Evaluate expression for multiple solution vectors.
        
        Args:
            expression: Mathematical expression string
            X: Array of shape (n_solutions, n_variables)
            time: Optional time parameter for dynamic problems
            
        Returns:
            Array of evaluation results
        """
        # Compile expression
        code = self.compile(expression)
        
        # Prepare namespace
        namespace = {
            **self.SAFE_FUNCTIONS,
            'np': np,
        }
        
        # Add time if provided
        if time is not None:
            namespace['t'] = time
        
        # Evaluate for each solution
        results = []
        for x in X:
            namespace['x'] = x
            try:
                result = eval(code, {"__builtins__": {}}, namespace)
                results.append(result)
            except Exception as e:
                raise ValueError(f"Failed to evaluate expression for x={x}: {str(e)}")
        
        return np.array(results)
    
    def clear_cache(self):
        """Clear the compiled expression cache."""
        self.compiled_cache.clear()
    
    def extract_variables(self, expression: str) -> List[str]:
        """
        Extract variable names used in an expression.
        
        Args:
            expression: Mathematical expression string
            
        Returns:
            List of variable names
        """
        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError:
            return []
        
        variables = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                name = node.id
                # Exclude function names and constants
                if name not in self.SAFE_FUNCTIONS:
                    variables.add(name)
        
        return sorted(list(variables))


# Global parser instance
_parser = ExpressionParser()


# Convenience functions
def validate_expression(expression: str) -> Tuple[bool, Optional[str]]:
    """Validate a mathematical expression."""
    return _parser.validate(expression)


def evaluate_expression(expression: str, variables: Dict[str, Any], 
                       time: Optional[float] = None) -> Any:
    """Evaluate a mathematical expression."""
    return _parser.evaluate(expression, variables, time)


def evaluate_vectorized(expression: str, X: np.ndarray, 
                       time: Optional[float] = None) -> np.ndarray:
    """Evaluate expression for multiple solutions."""
    return _parser.evaluate_vectorized(expression, X, time)


def extract_variables(expression: str) -> List[str]:
    """Extract variable names from expression."""
    return _parser.extract_variables(expression)
