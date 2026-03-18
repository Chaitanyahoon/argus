"""
Argus Dashboard API — Discord OAuth2 authentication.
Handles /login, /callback, /logout and session management.
"""

import os
import secrets
import requests
from functools import wraps
from flask import Blueprint, redirect, request, session, url_for, jsonify
from dotenv import load_dotenv

load_dotenv()

auth_bp = Blueprint("auth", __name__)

DISCORD_CLIENT_ID     = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI  = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:5000/callback")

DISCORD_API   = "https://discord.com/api/v10"
DISCORD_OAUTH = "https://discord.com/api/oauth2"
SCOPES        = "identify guilds"


def login_required(f):
    """Decorator: returns 401 if user is not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return jsonify({"error": "Unauthorized — please log in via /login"}), 401
        return f(*args, **kwargs)
    return decorated


@auth_bp.route("/login")
def login():
    """Redirect user to Discord OAuth2 authorization page."""
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    params = (
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={SCOPES.replace(' ', '%20')}"
        f"&state={state}"
    )
    return redirect(f"{DISCORD_OAUTH}/authorize{params}")


@auth_bp.route("/callback")
def callback():
    """Handle Discord OAuth2 callback, exchange code for token, fetch user."""
    code  = request.args.get("code")
    state = request.args.get("state")

    if not code or state != session.pop("oauth_state", None):
        return jsonify({"error": "Invalid OAuth state"}), 400

    # Exchange code for access token
    token_res = requests.post(
        f"{DISCORD_OAUTH}/token",
        data={
            "client_id":     DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type":    "authorization_code",
            "code":          code,
            "redirect_uri":  DISCORD_REDIRECT_URI,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    if not token_res.ok:
        return jsonify({"error": "Token exchange failed", "detail": token_res.text}), 400

    token_data   = token_res.json()
    access_token = token_data.get("access_token")

    # Fetch Discord user profile
    user_res = requests.get(
        f"{DISCORD_API}/users/@me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    if not user_res.ok:
        return jsonify({"error": "Failed to fetch user"}), 400

    user = user_res.json()
    session["user"] = {
        "id":            user["id"],
        "username":      user["username"],
        "discriminator": user.get("discriminator", "0"),
        "avatar":        user.get("avatar"),
        "access_token":  access_token,
    }

    # Redirect back to the dashboard after login
    return redirect("../../dashboard/index.html")


@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    return jsonify({"message": "Logged out successfully"})


@auth_bp.route("/me")
def me():
    """Return logged-in user info (or 401)."""
    user = session.get("user")
    if not user:
        return jsonify({"authenticated": False}), 401
    # Don't expose the access_token to the frontend
    safe = {k: v for k, v in user.items() if k != "access_token"}
    safe["authenticated"] = True
    safe["avatar_url"] = (
        f"https://cdn.discordapp.com/avatars/{safe['id']}/{safe['avatar']}.png"
        if safe.get("avatar") else
        "https://cdn.discordapp.com/embed/avatars/0.png"
    )
    return jsonify(safe)
