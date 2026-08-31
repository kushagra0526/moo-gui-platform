"""Test the router callback with both inputs"""
from gui.app import create_app
import json

app = create_app()

with app.server.test_client() as client:
    deps = client.get('/_dash-dependencies').get_json()
    
    # Find the router callback
    router_dep = next(d for d in deps if d.get('output') == 'page-layout.children')
    print("Router inputs:", [(i['id'], i['property']) for i in router_dep.get('inputs', [])])
    
    # Test with both inputs
    payload = json.dumps({
        "output": "page-layout.children",
        "outputs": {"id": "page-layout", "property": "children"},
        "inputs": [
            {"id": "url", "property": "pathname", "value": "/"},
            {"id": "auth-state", "property": "data", "value": None}
        ],
        "changedPropIds": ["url.pathname"],
        "state": []
    }).encode()
    
    resp = client.post('/_dash-update-component', data=payload,
                      content_type='application/json')
    print("Router status:", resp.status_code)
    if resp.status_code == 200:
        result = resp.get_json()
        children = result.get('response', {}).get('page-layout', {}).get('children', {})
        print("Login layout type:", children.get('type') if isinstance(children, dict) else 'ERROR')
    else:
        print("Error:", resp.data.decode()[:300])
