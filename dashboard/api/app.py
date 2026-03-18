"""
Argus Dashboard API — Flask application entry point.
Run with: python -m dashboard.api.app
"""

import os
import secrets
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from .routes import api_bp
from .auth import auth_bp

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.getenv("DASHBOARD_SECRET_KEY", secrets.token_hex(32))

    # CORS: allow the local dashboard HTML to call the API
    CORS(app, supports_credentials=True, origins=[
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "null",  # for file:// HTML pages opening locally
    ])

    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)

    return app


app = create_app()

if __name__ == "__main__":
    host  = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    port  = int(os.getenv("DASHBOARD_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    print(f"\n🌐  Argus Dashboard API running at http://{host}:{port}")
    print(f"📁  Serving bot data from: data/argus.db")
    print(f"🔑  Login at: http://localhost:{port}/login\n")
    app.run(host=host, port=port, debug=debug)
