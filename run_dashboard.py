"""
Argus Dashboard API — Quick launch script.
Run with: python run_dashboard.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from dashboard.api.app import app

if __name__ == "__main__":
    host  = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    port  = int(os.getenv("DASHBOARD_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    print("\n" + "="*52)
    print("  👁  ARGUS DASHBOARD API")
    print("="*52)
    print(f"  🌐  URL:    http://localhost:{port}")
    print(f"  🔑  Login:  http://localhost:{port}/login")
    print(f"  📊  Health: http://localhost:{port}/api/health")
    print(f"  📁  DB:     data/argus.db")
    print("="*52 + "\n")

    app.run(host=host, port=port, debug=debug)
