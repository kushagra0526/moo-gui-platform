"""
Problem definition callbacks for managing variables, objectives, and constraints
"""

from dash import Input, Output, State, callback_context, no_update, ALL
import dash
from ..layouts.problem_definition import create_variable_row, create_objective_row, create_constraint_row

def register_problem_callbacks(app):
    """Register problem definition callbacks."""
    
    @app.callback(
        Output("variables-container", "children"),
        [Input("btn-add-variable", "n_clicks"),
         Input({"type": "btn-remove-var", "index": ALL}, "n_clicks")],
        [State("variables-container", "children")],
        prevent_initial_call=True
    )
    def manage_variables(add_clicks, remove_clicks, current_children):
        """Add or remove decision variables."""
        ctx = callback_context
        
        if not ctx.triggered:
            return current_children
        
        trigger_id = ctx.triggered[0]["prop_id"]
        
        if "btn-add-variable" in trigger_id:
            # Add new variable
            new_index = len(current_children)
            new_variable = create_variable_row(new_index)
            return current_children + [new_variable]
        
        elif "btn-remove-var" in trigger_id:
            # Remove variable
            import json as _j
            trigger_info = _j.loads(trigger_id.split(".")[0])
            remove_index = trigger_info["index"]
            
            # Filter out the removed variable and reindex
            filtered_children = []
            new_index = 0
            for i, child in enumerate(current_children):
                if i != remove_index:
                    # Update the index in the child component
                    updated_child = create_variable_row(new_index)
                    # Preserve existing values if possible
                    filtered_children.append(updated_child)
                    new_index += 1
            
            return filtered_children if filtered_children else [create_variable_row(0)]
        
        return current_children
    
    @app.callback(
        Output("objectives-container", "children"),
        [Input("btn-add-objective", "n_clicks"),
         Input({"type": "btn-remove-obj", "index": ALL}, "n_clicks")],
        [State("objectives-container", "children")],
        prevent_initial_call=True
    )
    def manage_objectives(add_clicks, remove_clicks, current_children):
        """Add or remove objectives."""
        ctx = callback_context
        
        if not ctx.triggered:
            return current_children
        
        trigger_id = ctx.triggered[0]["prop_id"]
        
        if "btn-add-objective" in trigger_id:
            # Add new objective
            new_index = len(current_children)
            new_objective = create_objective_row(new_index)
            return current_children + [new_objective]
        
        elif "btn-remove-obj" in trigger_id:
            # Remove objective (but keep at least 2)
            if len(current_children) <= 2:
                return current_children
            
            import json as _j
            trigger_info = _j.loads(trigger_id.split(".")[0])
            remove_index = trigger_info["index"]
            
            # Filter out the removed objective and reindex
            filtered_children = []
            new_index = 0
            for i, child in enumerate(current_children):
                if i != remove_index:
                    updated_child = create_objective_row(new_index)
                    filtered_children.append(updated_child)
                    new_index += 1
            
            return filtered_children
        
        return current_children
    
    @app.callback(
        Output("constraints-container", "children"),
        [Input("btn-add-constraint", "n_clicks"),
         Input({"type": "btn-remove-constraint", "index": ALL}, "n_clicks")],
        [State("constraints-container", "children")],
        prevent_initial_call=True
    )
    def manage_constraints(add_clicks, remove_clicks, current_children):
        """Add or remove constraints."""
        ctx = callback_context
        
        if not ctx.triggered:
            return current_children
        
        trigger_id = ctx.triggered[0]["prop_id"]
        
        if "btn-add-constraint" in trigger_id:
            # Add new constraint
            if len(current_children) == 1 and "No constraints defined" in str(current_children[0]):
                # Replace placeholder
                new_constraint = create_constraint_row(0)
                return [new_constraint]
            else:
                new_index = len(current_children)
                new_constraint = create_constraint_row(new_index)
                return current_children + [new_constraint]
        
        elif "btn-remove-constraint" in trigger_id:
            import json as _j
            trigger_info = _j.loads(trigger_id.split(".")[0])
            remove_index = trigger_info["index"]
            
            # Filter out the removed constraint and reindex
            filtered_children = []
            new_index = 0
            for i, child in enumerate(current_children):
                if i != remove_index:
                    updated_child = create_constraint_row(new_index)
                    filtered_children.append(updated_child)
                    new_index += 1
            
            if not filtered_children:
                from dash import html
                return [html.P("No constraints defined. Click 'Add Constraint' to add constraints.", 
                              className="text-muted")]
            
            return filtered_children
        
        return current_children
    
    @app.callback(
        Output("problem-type-info", "children"),
        [Input("problem-type", "value")],
        prevent_initial_call=True
    )
    def update_problem_type_info(problem_type):
        from dash import html
        info_text = {
            "static": "Standard multi-objective optimization with fixed objectives and constraints.",
            "many":   "Many-objective optimization (>3 objectives) with specialized algorithms.",
        }
        return html.Small(info_text.get(problem_type, ""), className="text-muted")
    
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
        if not var_names or len(var_names) == 0:
            issues.append("At least one decision variable is required.")
        
        for i, (name, vtype, lower, upper) in enumerate(zip(var_names or [], var_types or [], 
                                                           var_lowers or [], var_uppers or [])):
            if not name:
                issues.append(f"Variable {i}: name is required.")
            
            if lower is not None and upper is not None and lower >= upper:
                issues.append(f"Variable {name}: lower bound must be less than upper bound.")
        
        # Validate objectives
        if len(non_empty_objs) < 2:
            issues.append("At least two objective formulas are required for multi-objective optimization.")
        
        for i, expr in enumerate(obj_expressions or []):
            if not expr or not expr.strip():
                issues.append(f"Objective {i}: expression cannot be empty.")
        
        # Validate constraints
        for i, expr in enumerate(constraint_expressions or []):
            if expr and not expr.strip():
                issues.append(f"Constraint {i}: expression cannot be empty.")
        
        if issues:
            return " ".join(issues), "warning"
        else:
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
         Input({"type": "constraint-expression", "index": ALL}, "value")],
        State("app-state", "data"),
        prevent_initial_call='initial_duplicate',
    )
    def save_problem_to_state(var_names, var_types, var_lowers, var_uppers,
                              obj_names, obj_directions, obj_expressions,
                              constraint_names, constraint_expressions,
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
                "constraint_expressions":  constraint_expressions,
            })
        else:
            state.pop("obj_expressions", None)
        return state