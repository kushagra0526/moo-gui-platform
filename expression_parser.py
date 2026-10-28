#!/usr/bin/env python3
"""
Expression parser for mathematical expressions in optimization problems.
Safely evaluates user-defined objective and constraint functions.
"""

import ast
import numpy as np
from typing import Any, Dict, Optional, Tuple


class ExpressionParser:
    """
    Safe parser and evaluator for mathematical expressions.
    Only arithmetic, comparisons, indexing, numbers and the functions below are allowed.
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
        'len': len,

        # Power functions
        'pow': np.power,
        'square': np.square,

        # Constants
        'pi': np.pi,
        'e': np.e,
    }

    # Names an expression may read besides SAFE_FUNCTIONS: the decision vector and time
    VARIABLES = {'x', 't'}

    # Syntax allowed in an expression; anything else (attributes, lambdas, comprehensions, strings) is rejected
    _ALLOWED_NODES = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare, ast.IfExp,
        ast.Call, ast.Name, ast.Load, ast.Constant, ast.Subscript, ast.Slice, ast.Tuple,
        ast.operator, ast.unaryop, ast.boolop, ast.cmpop,
    )

    def __init__(self):
        """Initialize the expression parser."""
        self.compiled_cache: Dict[str, Any] = {}

    def validate(self, expression: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an expression for safety and syntax.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not expression or not expression.strip():
            return False, "Expression cannot be empty"

        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"

        for node in ast.walk(tree):
            if not isinstance(node, self._ALLOWED_NODES):
                return False, f"Not allowed in an expression: {type(node).__name__}"
            if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
                return False, "Only numbers are allowed as constants"
            if isinstance(node, ast.Name) and node.id not in self.SAFE_FUNCTIONS and node.id not in self.VARIABLES:
                return False, f"Unknown name: {node.id}"
            if isinstance(node, ast.Call) and (not isinstance(node.func, ast.Name) or node.keywords):
                return False, "Only plain calls to the allowed functions are supported"

        return True, None

    def compile(self, expression: str, cache_key: Optional[str] = None) -> Any:
        """
        Validate and compile an expression for faster evaluation.

        Raises:
            ValueError: If expression is invalid
        """
        if cache_key and cache_key in self.compiled_cache:
            return self.compiled_cache[cache_key]

        is_valid, error = self.validate(expression)
        if not is_valid:
            raise ValueError(f"Invalid expression: {error}")

        code = compile(expression, '<expression>', 'eval')
        if cache_key:
            self.compiled_cache[cache_key] = code
        return code

    def namespace(self, x: Any = None, time: Optional[float] = None) -> Dict[str, Any]:
        """The only names a compiled expression can see."""
        return {"__builtins__": {}, **self.SAFE_FUNCTIONS, "x": x, "t": time}

    def evaluate(self, expression: str, variables: Dict[str, Any],
                 time: Optional[float] = None) -> Any:
        """Evaluate an expression; `variables` must provide `x`."""
        code = self.compile(expression)
        try:
            return eval(code, self.namespace(variables.get('x'), time))
        except Exception as e:
            raise ValueError(f"Failed to evaluate expression: {str(e)}")
