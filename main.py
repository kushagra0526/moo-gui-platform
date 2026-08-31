#!/usr/bin/env python3
"""
Multi-Objective Optimization GUI
Research-grade interface for pymoo-based optimization
"""

import os
from gui.app import create_app

# Application and WSGI server instance
app = create_app()
server = app.server

def main():
    """Main entry point for the MOO GUI application."""
    port = int(os.environ.get("PORT", os.environ.get("MOO_GUI_PORT", 8080)))
    host = os.environ.get("MOO_GUI_HOST", "0.0.0.0")
    debug = os.environ.get("MOO_GUI_DEBUG", "false").lower() in ("true", "1", "yes")

    print(f"Starting Multi-Objective Optimization GUI on {host}:{port} (debug={debug})...")
    print(f"Access the application at: http://localhost:{port}")
    app.run(debug=debug, host=host, port=port, use_reloader=False)

if __name__ == '__main__':
    main()