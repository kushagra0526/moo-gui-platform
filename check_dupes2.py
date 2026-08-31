from gui.app import create_app
import json

app = create_app()

with app.server.test_client() as client:
    resp = client.get('/_dash-dependencies')
    deps = resp.get_json()

print("Callbacks writing auth-state.data:")
for d in deps:
    out = d.get('output', '')
    if 'auth-state' in out and 'data' in out:
        ad = d.get('allow_duplicate')
        inputs = [i['id'] for i in d.get('inputs', []) if isinstance(i.get('id'), str)]
        print(f"  allow_duplicate={ad}  inputs={inputs}")

print()
print("Callbacks writing app-state.data:")
for d in deps:
    out = d.get('output', '')
    if 'app-state' in out and 'data' in out:
        ad = d.get('allow_duplicate')
        inputs = [i['id'] for i in d.get('inputs', []) if isinstance(i.get('id'), str)]
        print(f"  allow_duplicate={ad}  inputs={inputs}")

print()
print("Callbacks writing url.pathname:")
for d in deps:
    out = d.get('output', '')
    if 'url' in out and 'pathname' in out:
        ad = d.get('allow_duplicate')
        inputs = [i['id'] for i in d.get('inputs', []) if isinstance(i.get('id'), str)]
        print(f"  allow_duplicate={ad}  inputs={inputs}")

print()
print("Callbacks writing optimization-results.data:")
for d in deps:
    out = d.get('output', '')
    if 'optimization-results' in out and 'data' in out:
        ad = d.get('allow_duplicate')
        inputs = [i['id'] for i in d.get('inputs', []) if isinstance(i.get('id'), str)]
        print(f"  allow_duplicate={ad}  inputs={inputs}")

print()
print("Callbacks writing status-text.children:")
for d in deps:
    out = d.get('output', '')
    if 'status-text' in out:
        ad = d.get('allow_duplicate')
        inputs = [i['id'] for i in d.get('inputs', []) if isinstance(i.get('id'), str)]
        print(f"  allow_duplicate={ad}  inputs={inputs}")
