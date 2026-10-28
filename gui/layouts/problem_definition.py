"""
Problem definition layout for variables, objectives, and constraints
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

def create_problem_definition_layout(saved_state=None):
    """Create the problem definition interface, restoring saved values if available."""

    saved = saved_state or {}
    var_names  = saved.get("var_names",  [])
    var_types  = saved.get("var_types",  [])
    var_lowers = saved.get("var_lowers", [])
    var_uppers = saved.get("var_uppers", [])
    obj_names  = saved.get("obj_names",  [])
    obj_dirs   = saved.get("obj_directions", [])
    obj_exprs  = saved.get("obj_expressions", [])
    con_names  = saved.get("constraint_names") or []
    con_types  = saved.get("constraint_types") or []
    con_exprs  = saved.get("constraint_expressions") or []

    # Build variable rows from saved state, or default 2 rows (x0, x1)
    if var_names and len(var_names) > 0:
        variable_rows = [
            create_variable_row(
                i,
                name=var_names[i] if i < len(var_names) else f"x{i}",
                vtype=var_types[i] if i < len(var_types) else "continuous",
                lower=var_lowers[i] if i < len(var_lowers) else 0,
                upper=var_uppers[i] if i < len(var_uppers) else 1,
            )
            for i in range(len(var_names))
        ]
    else:
        variable_rows = [create_variable_row(0), create_variable_row(1)]

    # Build objective rows from saved state, or default 2 empty rows
    if obj_exprs and len(obj_exprs) >= 2:
        objective_rows = [
            create_objective_row(
                i,
                name=obj_names[i] if i < len(obj_names) else f"objective_{i}",
                direction=obj_dirs[i] if i < len(obj_dirs) else "minimize",
                expression=obj_exprs[i],
            )
            for i in range(len(obj_exprs))
        ]
    else:
        objective_rows = [create_objective_row(0, expression=""), create_objective_row(1, expression="")]

    # Restore constraint rows, or show the placeholder
    constraint_rows = [
        create_constraint_row(
            i,
            name=con_names[i] if i < len(con_names) else None,
            ctype=con_types[i] if i < len(con_types) and con_types[i] else "ineq",
            expression=con_exprs[i],
        )
        for i in range(len(con_exprs))
    ] or [NO_CONSTRAINTS]

    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("Problem Definition", className="section-title"),
                html.P("Define your multi-objective optimization problem with variables, objectives, and constraints.", 
                       className="section-description")
            ])
        ], className="mb-4"),
        
        # Decision Variables Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Decision Variables", className="mb-0"),
                        dbc.Button(
                            [html.I(className="fas fa-plus me-1"), "Add Variable"],
                            id="btn-add-variable",
                            color="primary",
                            size="sm",
                            className="float-end"
                        )
                    ], className="d-flex justify-content-between align-items-center"),
                    dbc.CardBody([
                        html.Div(id="variables-container", children=variable_rows)
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Objectives Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Objectives", className="mb-0"),
                        dbc.Button(
                            [html.I(className="fas fa-plus me-1"), "Add Objective"],
                            id="btn-add-objective",
                            color="success",
                            size="sm",
                            className="float-end"
                        )
                    ], className="d-flex justify-content-between align-items-center"),
                    dbc.CardBody([
                        html.Div(id="objectives-container", children=objective_rows)
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Constraints Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Constraints", className="mb-0"),
                        dbc.Button(
                            [html.I(className="fas fa-plus me-1"), "Add Constraint"],
                            id="btn-add-constraint",
                            color="warning",
                            size="sm",
                            className="float-end"
                        )
                    ], className="d-flex justify-content-between align-items-center"),
                    dbc.CardBody([
                        html.Div(id="constraints-container", children=constraint_rows)
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Problem Validation
        dbc.Row([
            dbc.Col([
                dbc.Alert(
                    id="problem-validation",
                    children="Enter your decision variables and objective formulas to define the optimization problem.",
                    color="info",
                    dismissable=False,
                    className="mb-0"
                )
            ])
        ])
        
    ], fluid=True)

NO_CONSTRAINTS = html.P("No constraints defined. Click 'Add Constraint' to add constraints.",
                        className="text-muted")


def create_variable_row(index, name=None, vtype="continuous", lower=0, upper=1):
    """Create a single variable definition row."""
    return dbc.Row([
        dbc.Col([
            dbc.InputGroup([
                dbc.InputGroupText(f"x{index}"),
                dbc.Input(
                    id={"type": "var-name", "index": index},
                    placeholder="Variable name",
                    value=name if name is not None else f"x{index}"
                )
            ])
        ], width=5),
        dbc.Col([
            dbc.Select(
                id={"type": "var-type", "index": index},
                options=[
                    {"label": "Continuous", "value": "continuous"},
                    {"label": "Integer", "value": "integer"},
                    {"label": "Binary", "value": "binary"}
                ],
                value=vtype
            )
        ], width=2),
        dbc.Col([
            dbc.Input(
                id={"type": "var-lower", "index": index},
                type="number",
                placeholder="Lower bound",
                value=lower
            )
        ], width=2),
        dbc.Col([
            dbc.Input(
                id={"type": "var-upper", "index": index},
                type="number",
                placeholder="Upper bound",
                value=upper
            )
        ], width=2),
        dbc.Col([
            dbc.Button(
                html.I(className="fas fa-trash"),
                id={"type": "btn-remove-var", "index": index},
                color="danger",
                size="sm",
                outline=True
            )
        ], width=1)
    ], className="mb-2 variable-row")

def create_objective_row(index, name=None, direction="minimize", expression=None):
    """Create a single objective definition row with equation rendering and image upload."""
    expr_value = expression if expression is not None else ""
    name_value = name if name is not None else f"objective_{index}"

    if expr_value.strip():
        from ..callbacks.equation_callbacks import convert_to_html
        preview_child = html.Div(
            convert_to_html(expr_value, index),
            style={
                "padding": "1.2rem",
                "background": "white",
                "border": "2px solid rgba(0, 212, 255, 0.3)",
                "borderRadius": "12px",
                "fontSize": "1.3rem",
                "textAlign": "center",
                "color": "#1e293b",
                "fontWeight": "500",
                "fontFamily": "Georgia, serif"
            }
        )
    else:
        preview_child = html.Div(
            f"Enter objective f{index}(x) expression above (e.g., x[0]**2 + x[1]**2)",
            className="text-muted fst-italic py-3 text-center",
            style={
                "background": "rgba(255, 255, 255, 0.03)",
                "borderRadius": "10px",
                "border": "1px dashed rgba(255, 255, 255, 0.15)",
                "fontSize": "0.95rem"
            }
        )

    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.InputGroup([
                    dbc.InputGroupText(f"f{index}", style={"fontWeight": "bold"}),
                    dbc.Input(
                        id={"type": "obj-name", "index": index},
                        placeholder="Objective name",
                        value=name_value
                    )
                ])
            ], width=3),
            dbc.Col([
                dbc.Select(
                    id={"type": "obj-direction", "index": index},
                    options=[
                        {"label": "Minimize ↓", "value": "minimize"},
                        {"label": "Maximize ↑", "value": "maximize"}
                    ],
                    value=direction
                )
            ], width=2),
            dbc.Col([
                dbc.Button(
                    [html.I(className="fas fa-camera me-2"), "Upload Image"],
                    id={"type": "btn-upload-obj-image", "index": index},
                    color="info",
                    size="sm",
                    outline=True,
                    className="w-100"
                )
            ], width=2),
            dbc.Col([
                dbc.Button(
                    html.I(className="fas fa-trash"),
                    id={"type": "btn-remove-obj", "index": index},
                    color="danger",
                    size="sm",
                    outline=True
                )
            ], width=1)
        ], className="mb-2"),
        
        # Image Upload Component (Hidden)
        dcc.Upload(
            id={"type": "upload-obj-image", "index": index},
            children=html.Div([
                html.I(className="fas fa-cloud-upload-alt fa-2x mb-2"),
                html.P("Drag and Drop or Click to Upload Equation Image", className="mb-0")
            ]),
            style={
                'width': '100%',
                'height': '120px',
                'lineHeight': '120px',
                'borderWidth': '2px',
                'borderStyle': 'dashed',
                'borderRadius': '12px',
                'textAlign': 'center',
                'borderColor': 'rgba(0, 212, 255, 0.3)',
                'background': 'rgba(30, 35, 55, 0.4)',
                'cursor': 'pointer',
                'display': 'none'
            },
            multiple=False,
            className="mb-2"
        ),
        
        # Equation Input
        dbc.Row([
            dbc.Col([
                html.Label("Equation (Python syntax):", className="form-label small"),
                dbc.Textarea(
                    id={"type": "obj-expression", "index": index},
                    placeholder="e.g., x[0]**2 + x[1]**2",
                    rows=2,
                    value=expr_value,
                    style={"fontFamily": "monospace", "fontSize": "0.95rem"}
                )
            ], width=12)
        ], className="mb-2"),
        
        # Rendered Equation Display
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Label("Rendered Equation:", className="form-label small"),
                    html.Div(
                        id={"type": "obj-rendered", "index": index},
                        className="equation-display",
                        children=[preview_child]
                    )
                ])
            ], width=12)
        ], className="mb-2"),
        
        # OCR Result Display (Hidden initially)
        html.Div(
            id={"type": "obj-ocr-result", "index": index},
            style={"display": "none"}
        )
        
    ], className="objective-row p-3 mb-3", style={"borderRadius": "16px"})

def create_constraint_row(index, name=None, ctype="ineq", expression=None):
    """Create a single constraint definition row."""
    return dbc.Row([
        dbc.Col([
            dbc.InputGroup([
                dbc.InputGroupText(f"g{index}"),
                dbc.Input(
                    id={"type": "constraint-name", "index": index},
                    placeholder="Constraint name",
                    value=name if name is not None else f"constraint_{index}"
                )
            ])
        ], width=3),
        dbc.Col([
            dbc.Select(
                id={"type": "constraint-type", "index": index},
                options=[
                    {"label": "Inequality (≤ 0)", "value": "ineq"},
                    {"label": "Equality (= 0)", "value": "eq"}
                ],
                value=ctype
            )
        ], width=2),
        dbc.Col([
            dbc.Textarea(
                id={"type": "constraint-expression", "index": index},
                placeholder="Constraint expression, e.g. x[0] + x[1] - 1",
                rows=2,
                value=expression or ""
            )
        ], width=6),
        dbc.Col([
            dbc.Button(
                html.I(className="fas fa-trash"),
                id={"type": "btn-remove-constraint", "index": index},
                color="danger",
                size="sm",
                outline=True
            )
        ], width=1)
    ], className="mb-2 constraint-row")