"""
Argus Dashboard API — REST endpoints.
All routes are prefixed /api/* and return JSON.
"""

from flask import Blueprint, jsonify, request, session
from . import db
from .auth import login_required

api_bp = Blueprint("api", __name__, url_prefix="/api")


# ── Overview ────────────────────────────────────────────────────────────────────

@api_bp.route("/overview")
@login_required
def overview():
    """Server-wide aggregate stats."""
    stats = db.get_overview_stats()
    return jsonify(stats)


# ── Leaderboard ─────────────────────────────────────────────────────────────────

@api_bp.route("/leaderboard")
@login_required
def leaderboard():
    """
    Top users ranked by a metric.
    Query params:
      metric  — xp (default) | level | total_messages | voice_time_seconds | music_plays
      limit   — 1-50 (default 15)
    """
    metric = request.args.get("metric", "xp")
    limit  = min(max(int(request.args.get("limit", 15)), 1), 50)
    users  = db.get_leaderboard(metric=metric, limit=limit)
    return jsonify(users)


# ── Users ────────────────────────────────────────────────────────────────────────

@api_bp.route("/users/<int:user_id>")
@login_required
def get_user(user_id):
    user = db.get_user(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)


# ── Guilds ───────────────────────────────────────────────────────────────────────

@api_bp.route("/guilds")
@login_required
def guilds():
    return jsonify(db.get_all_guilds())


@api_bp.route("/guilds/<int:guild_id>")
@login_required
def guild(guild_id):
    g = db.get_guild(guild_id)
    if not g:
        return jsonify({"error": "Guild not found"}), 404
    return jsonify(g)


# ── AutoMod ─────────────────────────────────────────────────────────────────────

@api_bp.route("/guilds/<int:guild_id>/automod", methods=["GET"])
@login_required
def get_automod(guild_id):
    """Return automod settings for a guild."""
    g = db.get_guild(guild_id)
    if not g:
        return jsonify({"error": "Guild not found"}), 404
    return jsonify({
        "guild_id":         guild_id,
        "toxicity_enabled": bool(g.get("automod_toxicity_enabled", 0)),
        "spam_enabled":     bool(g.get("automod_spam_enabled", 0)),
        "threshold":        g.get("automod_threshold", 0.7),
    })


@api_bp.route("/guilds/<int:guild_id>/automod", methods=["POST"])
@login_required
def update_automod(guild_id):
    """
    Update automod settings.
    Body JSON: { toxicity_enabled, spam_enabled, threshold }
    """
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    toxicity_enabled = bool(data.get("toxicity_enabled", False))
    spam_enabled     = bool(data.get("spam_enabled", False))
    threshold        = float(data.get("threshold", 0.7))

    if not (0.1 <= threshold <= 1.0):
        return jsonify({"error": "threshold must be between 0.1 and 1.0"}), 400

    db.update_automod_settings(guild_id, toxicity_enabled, spam_enabled, threshold)
    return jsonify({"message": "AutoMod settings updated", "guild_id": guild_id})


# ── Health ───────────────────────────────────────────────────────────────────────

@api_bp.route("/health")
def health():
    """Public health check — no auth required."""
    stats = db.get_overview_stats()
    return jsonify({
        "status": "ok",
        "db_users":    stats["total_users"],
        "db_messages": stats["total_messages"],
    })
