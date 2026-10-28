"""
Problem definition callbacks for managing variables, objectives, and constraints
"""

import json

from dash import Input, Output, State, callback_context, ALL
from dash.exceptions import PreventUpdate
from expression_parser import ExpressionParser
from ..layouts.problem_definition import (
    create_variable_row, create_objective_row, create_constraint_row, NO_CONSTRAINTS
)

_parser = ExpressionParser()


def _removed_index(ctx):
    """Index of the row whose remove button fired, or None when the add button fired."""
    if not ctx.triggered or not ctx.triggered[0]["value"]:
        raise PreventUpdate  # a newly rendered button with no clicks, not a real click
    trigger_id = ctx.triggered[0]["prop_id"].rsplit(".", 1)[0]
    return json.loads(trigger_id)["index"] if trigger_id.startswith("{") else None


def register_problem_callbacks(app):
    """Register problem definition callbacks."""

    # Rows are rebuilt from the current values so removing one row keeps what was typed in the others.
    @app.callback(
        Output("variables-container", "children"),
        Input("btn-add-variable", "n_clicks"),
        Input({"type": "btn-remove-var", "index": ALL}, "n_clicks"),
        State({"type": "var-name",  "index": ALL}, "value"),
        State({"type": "var-type",  "index": ALL}, "value"),
        State({"type": "var-lower", "index": ALL}, "value"),
        State({"type": "var-upper", "index": ALL}, "value"),
        prevent_initial_call=True
    )
    def manage_variables(_add, _remove, names, types, lowers, uppers):
        """Add or remove decision variables."""
        rows = list(zip(names, types, lowers, uppers))
        removed = _removed_index(callback_context)
        if removed is None:
            rows.append((None, "continuous", 0, 1))
        else:
            rows = [r for i, r in enumerate(rows) if i != removed] or [(None, "continuous", 0, 1)]
        return [create_variable_row(i, name=n, vtype=t, lower=lo, upper=up)
                for i, (n, t, lo, up) in enumerate(rows)]

    @app.callback(
        Output("objectives-container", "children"),
        Input("btn-add-objective", "n_clicks"),
        Input({"type": "btn-remove-obj", "index": ALL}, "n_clicks"),
        State({"type": "obj-name",       "index": ALL}, "value"),
        State({"type": "obj-direction",  "index": ALL}, "value"),
        State({"type": "obj-expression", "index": ALL}, "value"),
        prevent_initial_call=True
    )
    def manage_objectives(_add, _remove, names, directions, expressions):
        """Add or remove objectives (at least 2 are kept)."""
        rows = list(zip(names, directions, expressions))
        removed = _removed_index(callback_context)
        if removed is None:
            rows.append((None, "minimize", ""))
        elif len(rows) > 2:
            rows = [r for i, r in enumerate(rows) if i != removed]
        return [create_objective_row(i, name=n, direction=d, expression=e or "")
                for i, (n, d, e) in enumerate(rows)]

    @app.callback(
        Output("constraints-container", "children"),
        Input("btn-add-constraint", "n_clicks"),
        Input({"type": "btn-remove-constraint", "index": ALL}, "n_clicks"),
        State({"type": "constraint-name",       "index": ALL}, "value"),
        State({"type": "constraint-type",       "index": ALL}, "value"),
        State({"type": "constraint-expression", "index": ALL}, "value"),
        prevent_initial_call=True
    )
    def manage_constraints(_add, _remove, names, types, expressions):
        """Add or remove constraints."""
        rows = list(zip(names, types, expressions))
        removed = _removed_index(callback_context)
        if removed is None:
            rows.append((None, "ineq", ""))
        else:
            rows = [r for i, r in enumerate(rows) if i != removed]
        return [create_constraint_row(i, name=n, ctype=t, expression=e)
                for i, (n, t, e) in enumerate(rows)] or [NO_CONSTRAINTS]

    @app.callback(
        Output("problem-validation", "children"),
        Output("problem-validation", "color"),
        [Input({"type": "var-name", "index": ALL}, "value"),
         Input({"type": "var-type", "index": ALL}, "value"),
         Input({"type": "var-lower", "index": ALL}, "value"),
         Input({"type": "var-upper", "index": ALL}, "value"),
         Input({"type": "obj-name", "index": ALL}, "value"),
         Input({"type": "obj-expression", "index": ALL}, "value"),
         Input({"type": "constraint-expression", "index": ALL}, "value")],
        prevent_initial_call=True
    )
    def validate_problem_definition(var_names, var_types, var_lowers, var_uppers,
                                    obj_names, obj_expressions, constraint_expressions):
        """Validate the current problem definition."""
        # If all objective expressions are empty, show info prompt
        non_empty_objs = [e for e in (obj_expressions or []) if e and e.strip()]
        if len(non_empty_objs) == 0:
            return "Enter your decision variables and objective formulas to define the optimization problem.", "info"

        issues = []

        # Validate variables
        if not var_names:
            issues.append("At least one decision variable is required.")

        for i, (name, lower, upper) in enumerate(zip(var_names or [], var_lowers or [], var_uppers or [])):
            if not name:
                issues.append(f"Variable {i}: name is required.")
            if lower is None or upper is None:
                issues.append(f"Variable {name or i}: both bounds are required.")
            elif lower >= upper:
                issues.append(f"Variable {name}: lower bound must be less than upper bound.")

        # Validate objectives
        if len(non_empty_objs) < 2:
            issues.append("At least two objective formulas are required for multi-objective optimization.")

        for i, expr in enumerate(obj_expressions or []):
            if not expr or not expr.strip():
                issues.append(f"Objective {i}: expression cannot be empty.")
            else:
                ok, error = _parser.validate(expr)
                if not ok:
                    issues.append(f"Objective {i}: {error}.")

        # Validate constraints
        for i, expr in enumerate(constraint_expressions or []):
            if expr and expr.strip():
                ok, error = _parser.validate(expr)
                if not ok:
                    issues.append(f"Constraint {i}: {error}.")

        if issues:
            return " ".join(issues), "warning"
        return "Problem definition is valid. Ready to run optimization.", "success"

    # ── Save problem definition to app-state ────────────────────
    @app.callback(
        Output("app-state", "data", allow_duplicate=True),
        [Input({"type": "var-name",  "index": ALL}, "value"),
         Input({"type": "var-type",  "index": ALL}, "value"),
         Input({"type": "var-lower", "index": ALL}, "value"),
         Input({"type": "var-upper", "index": ALL}, "value"),
         Input({"type": "obj-name",       "index": ALL}, "value"),
         Input({"type": "obj-direction",  "index": ALL}, "value"),
         Input({"type": "obj-expression", "index": ALL}, "value"),
         Input({"type": "constraint-name",       "index": ALL}, "value"),
         Input({"type": "constraint-type",       "index": ALL}, "value"),
         Input({"type": "constraint-expression", "index": ALL}, "value")],
        State("app-state", "data"),
        prevent_initial_call='initial_duplicate',
    )
    def save_problem_to_state(var_names, var_types, var_lowers, var_uppers,
                              obj_names, obj_directions, obj_expressions,
                              constraint_names, constraint_types, constraint_expressions,
                              current_state):
        """Save problem definition to app-state so optimization can read it."""
        # Only save if we actually have non-empty problem data
        has_data = any(e and e.strip() for e in (obj_expressions or []))
        state = current_state.copy() if current_state else {}
        if has_data:
            state.update({
                "var_names":               var_names,
                "var_types":               var_types,
                "var_lowers":              var_lowers,
                "var_uppers":              var_uppers,
                "obj_names":               obj_names,
                "obj_directions":          obj_directions,
                "obj_expressions":         obj_expressions,
                "constraint_names":        constraint_names,
                "constraint_types":        constraint_types,
                "constraint_expressions":  constraint_expressions,
            })
        else:
            state.pop("obj_expressions", None)
        return state
