"""
Test every callback that fires on initial load or immediately after,
by directly calling the Python functions.
"""
import sys
sys.path.insert(0, '.')

from gui.app import create_app
app = create_app()

print('=== Testing router callback directly ===')
# Simulate unauthenticated load
try:
    from gui.layouts import create_login_layout
    result = create_login_layout()
    # Try to serialize it like Dash would
    from dash._utils import AttributeDict
    import plotly
    result_json = plotly.io.json.to_json_plotly(result)
    print(f'Login layout serializes OK, length={len(result_json)}')
except Exception as e:
    import traceback
    print('LOGIN LAYOUT ERROR:')
    traceback.print_exc()

print()
print('=== Testing reconcile_optimization_state callback ===')
# This fires on url change - find it
for cb_id, cb in app.callback_map.items():
    out = cb['output']
    outputs = out if isinstance(out, (list, tuple)) else [out]
    output_ids = [o.component_id for o in outputs if hasattr(o, 'component_id')]
    if 'app-state' in output_ids and 'optimization-interval' in output_ids:
        func = cb.get('f') or cb.get('callback')
        if func and callable(func):
            print(f'Found reconcile callback, testing...')
            try:
                result = func('/', None)
                print(f'Result: {result}')
            except Exception as e:
                import traceback
                print('RECONCILE ERROR:')
                traceback.print_exc()
        break

print()
print('=== Checking for any callback returning non-serializable objects ===')
import json

# Test the update_status callback (fires on app-state change)
for cb_id, cb in app.callback_map.items():
    out = cb['output']
    outputs = out if isinstance(out, (list, tuple)) else [out]
    output_ids = [getattr(o, 'component_id', '') for o in outputs]
    if 'status-text' in output_ids:
        func = cb.get('f') or cb.get('callback')
        if func and callable(func):
            print('Testing update_status with None state...')
            try:
                result = func(None)
                print(f'Result: {repr(result)}')
                json.dumps(result)
                print('Serializes OK')
            except Exception as e:
                print(f'ERROR: {e}')
        break

print()
print('=== Checking update_progress callback ===')
for cb_id, cb in app.callback_map.items():
    out = cb['output']
    outputs = out if isinstance(out, (list, tuple)) else [out]
    output_ids = [getattr(o, 'component_id', '') for o in outputs]
    if 'progress-bar' in output_ids:
        func = cb.get('f') or cb.get('callback')
        if func and callable(func):
            print('Testing update_progress with None state...')
            try:
                result = func(None)
                print(f'Result: {repr(result)}')
            except Exception as e:
                print(f'ERROR: {e}')
        break
