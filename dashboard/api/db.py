"""
Argus Dashboard API — SQLite query layer.
Reads directly from data/argus.db.
"""

import sqlite3
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).parent.parent.parent / "data" / "argus.db"


def _conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ── Users ──────────────────────────────────────────────────────────────────────

def get_leaderboard(metric: str = "xp", limit: int = 15) -> List[Dict[str, Any]]:
    allowed = {"xp", "level", "total_messages", "voice_time_seconds", "music_plays"}
    if metric not in allowed:
        metric = "xp"
    with _conn() as c:
        rows = c.execute(
            f"SELECT * FROM users ORDER BY {metric} DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    with _conn() as c:
        row = c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def get_overview_stats() -> Dict[str, Any]:
    with _conn() as c:
        total_users  = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_xp     = c.execute("SELECT COALESCE(SUM(xp), 0) FROM users").fetchone()[0]
        avg_level    = c.execute("SELECT COALESCE(AVG(level), 0) FROM users").fetchone()[0]
        total_msgs   = c.execute("SELECT COALESCE(SUM(total_messages), 0) FROM users").fetchone()[0]
        total_voice  = c.execute("SELECT COALESCE(SUM(voice_time_seconds), 0) FROM users").fetchone()[0]
        total_music  = c.execute("SELECT COALESCE(SUM(music_plays), 0) FROM users").fetchone()[0]
    return {
        "total_users":    total_users,
        "total_xp":       total_xp,
        "avg_level":      round(float(avg_level), 1),
        "total_messages": total_msgs,
        "voice_hours":    round(total_voice / 3600, 1),
        "music_plays":    total_music,
    }


# ── Guilds ─────────────────────────────────────────────────────────────────────

def get_guild(guild_id: int) -> Optional[Dict[str, Any]]:
    with _conn() as c:
        row = c.execute("SELECT * FROM guilds WHERE guild_id = ?", (guild_id,)).fetchone()
    return dict(row) if row else None


def get_all_guilds() -> List[Dict[str, Any]]:
    with _conn() as c:
        rows = c.execute("SELECT * FROM guilds").fetchall()
    return [dict(r) for r in rows]


def update_automod_settings(
    guild_id: int,
    toxicity_enabled: bool,
    spam_enabled: bool,
    threshold: float,
) -> None:
    with _conn() as c:
        exists = c.execute("SELECT 1 FROM guilds WHERE guild_id = ?", (guild_id,)).fetchone()
        if exists:
            c.execute(
                """UPDATE guilds
                   SET automod_toxicity_enabled = ?,
                       automod_spam_enabled = ?,
                       automod_threshold = ?
                   WHERE guild_id = ?""",
                (int(toxicity_enabled), int(spam_enabled), threshold, guild_id),
            )
        else:
            c.execute(
                """INSERT INTO guilds (guild_id, automod_toxicity_enabled, automod_spam_enabled, automod_threshold)
                   VALUES (?, ?, ?, ?)""",
                (guild_id, int(toxicity_enabled), int(spam_enabled), threshold),
            )
        c.commit()
