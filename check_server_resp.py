"""Simulate the exact callback the browser fires on startup and check the response"""
import urllib.request, json

BASE = 'http://localhost:8080'

# Get dependencies to find the exact output key for the logout callback
req = urllib.request.Request(BASE + '/_dash-dependencies')
with urllib.request.urlopen(req) as r:
    deps = json.loads(r.read())

# Find the logout callback (inputs: url.pathname, outputs: auth-state + app-state + optimization-results)
logout_dep = None
for d in deps:
    inputs = d.get('inputs', [])
    if len(inputs) == 1 and inputs[0].get('id') == 'url' and inputs[0].get('property') == 'pathname':
        if 'auth-state' in d.get('output', ''):
            logout_dep = d
            break

if logout_dep:
    print("Found logout callback:")
    print("  output key:", logout_dep['output'][:80])
    
    # Simulate it firing with pathname="/"
    payload = {
        "output": logout_dep['output'],
        "outputs": logout_dep.get('outputs', []),
        "inputs": [{"id": "url", "property": "pathname", "value": "/"}],
        "changedPropIds": ["url.pathname"],
        "state": []
    }
    
    data = json.dumps(payload).encode()
    req2 = urllib.request.Request(BASE + '/_dash-update-component', data=data,
                                   headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req2) as r:
            result = json.loads(r.read())
            print("  Status: 200")
            print("  Response:", str(result)[:200])
    except urllib.error.HTTPError as e:
        print("  Status:", e.code)
        print("  Error:", e.read().decode()[:300])
else:
    print("Logout callback not found")
    print("All callbacks with url input:")
    for d in deps:
        inputs = d.get('inputs', [])
        if any(i.get('id') == 'url' for i in inputs):
            print(" ", d.get('output','')[:80])
