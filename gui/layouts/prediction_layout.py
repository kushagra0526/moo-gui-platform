"""
Dynamic Prediction page: random restart, ISVM-SMOTE and ISVM-LoRAS compared on one CEC2018 DF problem.
"""
from dash import dcc, html
import dash_bootstrap_components as dbc

from .cec2018_layout import _PROBLEMS, _empty_fig

_CARD = {"background": "rgba(20,24,41,0.7)",
         "border": "1px solid rgba(0,212,255,0.15)",
         "borderRadius": "12px"}
_SECONDARY = {"color": "var(--text-secondary)"}  # the theme's text-muted is too dark on these cards

_STEPS = [
    ("fas fa-clone", "1. Oversample",
     "The last Pareto-optimal set is enlarged with LoRAS (SMOTE in the paper) and labelled optimal; "
     "random points from the search space are labelled non-optimal."),
    ("fas fa-project-diagram", "2. Learn",
     "An incremental RBF-SVM, which keeps its support vectors from earlier changes, learns where "
     "optimal solutions lie."),
    ("fas fa-bullseye", "3. Predict",
     "When the environment changes, random candidates the SVM classifies as optimal become NSGA-II's "
     "new initial population."),
]


def _number(label, elem_id, value, lo, hi):
    return dbc.Col([
        html.Label(label, className="form-label small"),
        dbc.Input(id=elem_id, type="number", value=value, min=lo, max=hi, step=1),
    ], width=2)


def create_prediction_layout():
    steps = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.Div([html.I(className=f"{icon} me-2 text-primary"), html.Strong(title)], className="mb-2"),
            html.P(text, className="small mb-0", style=_SECONDARY),
        ]), className="h-100", style=_CARD), md=4)
        for icon, title, text in _STEPS
    ], className="mb-4 g-3")

    controls = dbc.Card(dbc.CardBody([
        dbc.Row([
            dbc.Col([
                html.Label("Problem", className="form-label small"),
                dbc.Select(id="pred-problem", value="5", options=[
                    {"label": f"{name} ({n_obj}-obj)", "value": str(pid)}
                    for pid, (name, n_obj, _) in _PROBLEMS.items()
                ]),
            ], width=2),
            _number("Environment Changes", "pred-changes", 10, 1, 30),
            _number("Change Freq (taut)",  "pred-taut",    10, 1, 50),
            _number("Severity (nt)",       "pred-nt",      10, 1, 20),
            dbc.Col(dbc.ButtonGroup([
                dbc.Button([html.I(className="fas fa-play me-2"), "Run comparison"],
                           id="pred-run-btn", color="success"),
                dbc.Button([html.I(className="fas fa-stop me-2"), "Stop"],
                           id="pred-stop-btn", color="danger", disabled=True),
            ]), width=4),
        ], className="align-items-end"),
        html.Div(id="pred-status", className="small mt-3", style=_SECONDARY,
                 children="Runs random restart, ISVM-SMOTE and ISVM-LoRAS one after another with the same seed."),
    ]), className="mb-4", style=_CARD)

    results = dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("IGD per Environment"),
            dbc.CardBody(dcc.Graph(id="pred-igd-plot", figure=_empty_fig("IGD per environment"),
                                   style={"height": "380px"}, config={"displayModeBar": False}),
                         style={"padding": "0.5rem"}),
        ], style=_CARD), width=7),
        dbc.Col(dbc.Card([
            dbc.CardHeader("Summary"),
            dbc.CardBody([
                html.Div(id="pred-table"),
                html.P("MIGD and MHV average IGD and hypervolume over the environments after each change "
                       "(lower MIGD and higher MHV are better). \"vs random\" is the MIGD reduction "
                       "against random restart.", className="small mt-3 mb-0", style=_SECONDARY),
            ]),
        ], style=_CARD), width=5),
    ], className="mb-4")

    return html.Div([
        dcc.Interval(id="pred-interval", interval=2000, disabled=True),
        html.H4("Dynamic Prediction (ISVM-DMOEA)", style={"color": "#00d4ff", "fontWeight": "800"}),
        html.P("Predicts NSGA-II's initial population after each environment change (Xu et al., IEEE TEVC 2022), "
               "with LoRAS in place of SMOTE.", className="mb-4", style=_SECONDARY),
        steps,
        controls,
        results,
    ], className="fade-in", style={"padding": "1rem"})
