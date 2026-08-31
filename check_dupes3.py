"""Check how Dash 3 actually serializes allow_duplicate"""
import dash
from dash import html, Input, Output, dcc

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.layout = html.Div([
    dcc.Store(id="store"),
    html.Div(id="out1"),
    html.Div(id="out2"),
])

@app.callback(Output("store", "data", allow_duplicate=True), Input("out1", "children"), prevent_initial_call=True)
def cb1(v): return v

@app.callback(Output("store", "data", allow_duplicate=True), Input("out2", "children"), prevent_initial_call=True)
def cb2(v): return v

with app.server.test_client() as client:
    resp = client.get('/_dash-dependencies')
    deps = resp.get_json()
    for d in deps:
        print("output:", d.get('output','')[:60])
        print("  allow_duplicate:", d.get('allow_duplicate'))
        print("  keys:", list(d.keys()))
        print()
