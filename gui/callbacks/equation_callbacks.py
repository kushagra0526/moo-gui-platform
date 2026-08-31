"""
Callbacks for equation rendering and image upload
"""

from dash import Input, Output, State, html, callback_context, ALL
import dash_bootstrap_components as dbc
import base64
import io
import re


def register_equation_callbacks(app):
    """Register equation-related callbacks."""

    @app.callback(
        Output({"type": "upload-obj-image", "index": ALL}, "style"),
        [Input({"type": "btn-upload-obj-image", "index": ALL}, "n_clicks")],
        [State({"type": "upload-obj-image", "index": ALL}, "style")],
        prevent_initial_call=True
    )
    def toggle_upload_area(n_clicks_list, current_styles):
        if not callback_context.triggered:
            return current_styles
        triggered_id = callback_context.triggered[0]["prop_id"]
        import json as _json
        if "{" in triggered_id:
            id_dict = _json.loads(triggered_id.split(".")[0])
            clicked_index = id_dict["index"]
            new_styles = []
            for i, style in enumerate(current_styles):
                if i == clicked_index:
                    new_style = style.copy()
                    new_style["display"] = "none" if style.get("display") != "none" else "block"
                    new_styles.append(new_style)
                else:
                    new_styles.append(style)
            return new_styles
        return current_styles

    @app.callback(
        [Output({"type": "obj-ocr-result", "index": ALL}, "children"),
         Output({"type": "obj-ocr-result", "index": ALL}, "style"),
         Output({"type": "obj-expression", "index": ALL}, "value")],
        [Input({"type": "upload-obj-image", "index": ALL}, "contents")],
        [State({"type": "upload-obj-image", "index": ALL}, "filename"),
         State({"type": "obj-expression", "index": ALL}, "value")],
        prevent_initial_call=True
    )
    def handle_image_upload(contents_list, filenames_list, current_expressions):
        if not contents_list or not any(contents_list):
            return (
                [[]] * len(contents_list),
                [{"display": "none"}] * len(contents_list),
                current_expressions
            )

        results = []
        styles = []
        new_expressions = list(current_expressions)

        for i, (content, filename) in enumerate(zip(contents_list, filenames_list)):
            if content is None:
                results.append([])
                styles.append({"display": "none"})
                continue
            try:
                content_type, content_string = content.split(',')
                decoded = base64.b64decode(content_string)
                try:
                    from PIL import Image
                    import pytesseract
                    import os
                    if os.name == 'nt':
                        for path in [
                            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                        ]:
                            if os.path.exists(path):
                                pytesseract.pytesseract.tesseract_cmd = path
                                break
                    image = Image.open(io.BytesIO(decoded))
                    text = pytesseract.image_to_string(image)
                    equation = clean_ocr_text(text)
                    if equation:
                        new_expressions[i] = equation
                        result = dbc.Alert(f"OCR: {equation}", color="success", className="mt-2")
                    else:
                        result = dbc.Alert("OCR found no equation. Enter manually.", color="warning", className="mt-2")
                except ImportError:
                    result = dbc.Alert("OCR not available. Enter equation manually.", color="info", className="mt-2")
                except Exception as ocr_error:
                    result = dbc.Alert(f"OCR error: {str(ocr_error)}", color="warning", className="mt-2")
                results.append(result)
                styles.append({"display": "block"})
            except Exception as e:
                results.append(dbc.Alert(f"Upload error: {str(e)}", color="danger", className="mt-2"))
                styles.append({"display": "block"})

        return results, styles, new_expressions

    @app.callback(
        Output({"type": "obj-rendered", "index": ALL}, "children"),
        [Input({"type": "obj-expression", "index": ALL}, "value")],
        prevent_initial_call=True
    )
    def update_rendered_equation(expressions):
        rendered = []
        for i, expr in enumerate(expressions):
            if not expr:
                expr = "x[0]**2 + x[1]**2"
            html_expr = convert_to_html(expr, i)
            rendered.append(
                html.Div(
                    html_expr,
                    style={
                        "padding": "1.5rem",
                        "background": "white",
                        "border": "2px solid rgba(0, 212, 255, 0.3)",
                        "borderRadius": "12px",
                        "fontSize": "1.4rem",
                        "textAlign": "center",
                        "color": "#1e293b",
                        "fontWeight": "500",
                        "fontFamily": "Georgia, serif"
                    }
                )
            )
        return rendered


def convert_to_html(python_expr, index):
    parts = [
        html.Span("f", style={"fontStyle": "italic"}),
        html.Sub(str(index)),
        html.Span("(x) = ", style={"fontStyle": "italic"})
    ]
    expr = python_expr.strip()
    terms = re.split(r'(\+|\-)', expr)
    for term in terms:
        term = term.strip()
        if not term:
            continue
        if term in ['+', '-']:
            parts.append(html.Span(f" {term} ", style={"margin": "0 0.3rem"}))
            continue
        if '(' in term:
            paren_parts = re.split(r'(\(|\))', term)
            for pp in paren_parts:
                if pp == '(':
                    parts.append(html.Span("("))
                elif pp == ')':
                    parts.append(html.Span(")"))
                elif pp:
                    parts.extend(parse_term(pp))
        else:
            parts.extend(parse_term(term))
    return html.Div(parts, style={"display": "inline"})


def parse_term(term):
    elements = []

    # x[n]**p
    match = re.match(r'^x\[(\d+)\]\*\*(\d+)$', term)
    if match:
        elements.append(html.Span("x", style={"fontStyle": "italic"}))
        elements.append(html.Sub(match.group(1)))
        elements.append(html.Sup(match.group(2)))
        return elements

    # x[n]
    match = re.match(r'^x\[(\d+)\]$', term)
    if match:
        elements.append(html.Span("x", style={"fontStyle": "italic"}))
        elements.append(html.Sub(match.group(1)))
        return elements

    # c*x[n]**p
    match = re.match(r'^(\d+\.?\d*)\*x\[(\d+)\]\*\*(\d+)$', term)
    if match:
        elements.append(html.Span(match.group(1)))
        elements.append(html.Span("x", style={"fontStyle": "italic"}))
        elements.append(html.Sub(match.group(2)))
        elements.append(html.Sup(match.group(3)))
        return elements

    # c*x[n]
    match = re.match(r'^(\d+\.?\d*)\*x\[(\d+)\]$', term)
    if match:
        elements.append(html.Span(match.group(1)))
        elements.append(html.Span("x", style={"fontStyle": "italic"}))
        elements.append(html.Sub(match.group(2)))
        return elements

    # plain number
    if re.match(r'^\d+\.?\d*$', term):
        elements.append(html.Span(term))
        return elements

    # expr**p  (e.g. (x[0]-1)**2 after paren stripping)
    match = re.match(r'^(.*)\*\*(\d+)$', term)
    if match:
        inner = match.group(1)
        power = match.group(2)
        elements.extend(parse_term(inner))
        elements.append(html.Sup(power))
        return elements

    # fallback: show as-is (don't split on * to avoid showing × for **)
    elements.append(html.Span(term))
    return elements


def clean_ocr_text(text):
    equation = text.strip().replace(' ', '')
    equation = equation.replace('×', '*').replace('÷', '/').replace('^', '**')
    equation = equation.replace('²', '**2').replace('³', '**3')
    equation = re.sub(r'x(\d+)', r'x[\1]', equation)
    equation = equation.replace('|', '').replace('I', '1').replace('O', '0')
    if any(char in equation for char in ['x', '+', '-', '*', '/', '(', ')']):
        return equation
    return None
