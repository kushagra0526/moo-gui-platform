"""Test every URL-triggered callback using the correct Dash 3 payload format"""
from gui.app import create_app
import json

app = create_app()

print("Total callbacks:", len(app.callback_map))

with app.server.test_client() as client:
    deps = client.get('/_dash-dependencies').get_json()
    
    errors = []
    for d in deps:
        inputs = d.get('inputs', [])
        if not any(i.get('id') == 'url' and i.get('property') == 'pathname' for i in inputs):
            continue
        
        out_key = d.get('output', '')
        
        # Build correct outputs spec from the output key
        # Single output: "id.property@hash" -> {"id": "id", "property": "property"}
        # Multi output: "..id1.prop1@hash...id2.prop2@hash.." -> list
        if out_key.startswith('..') and out_key.endswith('..'):
            parts = out_key[2:-2].split('...')
            outputs_spec = []
            for p in parts:
                base = p.split('@')[0]
                dot_idx = base.rfind('.')
                outputs_spec.append({"id": base[:dot_idx], "property": base[dot_idx+1:]})
        else:
            base = out_key.split('@')[0]
            dot_idx = base.rfind('.')
            outputs_spec = {"id": base[:dot_idx], "property": base[dot_idx+1:]}
        
        payload = json.dumps({
            "output": out_key,
            "outputs": outputs_spec,
            "inputs": [{"id": "url", "property": "pathname", "value": "/"}],
            "changedPropIds": ["url.pathname"],
            "state": [{"id": s["id"], "property": s["property"], "value": None}
                      for s in d.get('state', []) if isinstance(s.get('id'), str)]
        }).encode()
        
        resp = client.post('/_dash-update-component', data=payload,
                          content_type='application/json')
        status = resp.status_code
        if status != 200:
            errors.append(f"FAIL {status}: {out_key[:70]}")
        else:
            print(f"OK {status}: {out_key[:70]}")
    
    if errors:
        print("\nFAILED:")
        for e in errors:
            print(" ", e)
    else:
        print("\nAll URL-triggered callbacks return 200!")
