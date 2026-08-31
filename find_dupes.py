from gui.app import create_app
import json

app = create_app()

with app.server.test_client() as client:
    resp = client.get('/_dash-dependencies')
    deps = resp.get_json()

# Build a map of individual output -> list of callbacks that write it
output_map = {}
for dep in deps:
    raw_output = dep.get('output', '')
    # Split multi-outputs
    if raw_output.startswith('..') and raw_output.endswith('..'):
        # multi-output: ..id1.prop1@hash...id2.prop2@hash..
        parts = raw_output[2:-2].split('...')
    else:
        parts = [raw_output]
    
    for part in parts:
        # strip hash
        base = part.split('@')[0] if '@' in part else part
        if base not in output_map:
            output_map[base] = []
        output_map[base].append({
            'full_output': raw_output[:80],
            'allow_duplicate': dep.get('allow_duplicate', False),
            'prevent_initial_call': dep.get('prevent_initial_call', True),
            'inputs': [f"{i['id']}.{i['property']}" for i in dep.get('inputs', []) if isinstance(i.get('id'), str)]
        })

print("=== OUTPUTS WITH MULTIPLE CALLBACKS ===")
for output, cbs in output_map.items():
    if len(cbs) > 1:
        print(f"\nOUTPUT: {output}")
        for i, cb in enumerate(cbs):
            print(f"  [{i+1}] allow_duplicate={cb['allow_duplicate']} prevent_initial={cb['prevent_initial_call']}")
            print(f"       inputs: {cb['inputs']}")
            print(f"       full: {cb['full_output']}")
