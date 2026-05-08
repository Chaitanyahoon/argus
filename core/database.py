import sqlite3
import os
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SQLiteArgusDb:
    """Robust SQLite backend for Argus data storage."""
    
    def __init__(self, db_path: str = "data/argus.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
        logger.info(f"SQLite database initialized at {db_path}")

    def _create_tables(self):
        """Create initial table schema if they don't exist."""
        cursor = self._conn.cursor()
        
        # User table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                total_messages INTEGER DEFAULT 0,
                voice_time_seconds INTEGER DEFAULT 0,
                music_plays INTEGER DEFAULT 0,
                commands_used INTEGER DEFAULT 0,
                achievements TEXT DEFAULT '[]',
                last_seen TEXT
            )
        ''')
        
        # Guild table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id INTEGER PRIMARY KEY,
                awakening_stage INTEGER DEFAULT 1,
                mood_mode TEXT DEFAULT 'NORMAL',
                logging_channel_id INTEGER,
                bot_logs_channel_id INTEGER,
                prefix TEXT DEFAULT '!',
                automod_toxicity_enabled INTEGER DEFAULT 0,
                automod_spam_enabled INTEGER DEFAULT 0,
                automod_threshold REAL DEFAULT 0.7
            )
        ''')
        
        # Wellness Tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mood_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                mood_score INTEGER,
                note TEXT,
                timestamp TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                entry_text TEXT,
                timestamp TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_wellness (
                user_id INTEGER PRIMARY KEY,
                therapy_mode_enabled INTEGER DEFAULT 1,
                last_checkin TEXT,
                checkin_streak INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Migration: Add bot_logs_channel_id if it doesn't exist
        try:
            cursor.execute("SELECT bot_logs_channel_id FROM guilds LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            try:
                cursor.execute("ALTER TABLE guilds ADD COLUMN bot_logs_channel_id INTEGER DEFAULT NULL")
                logger.info("Added bot_logs_channel_id column to guilds table")
            except sqlite3.OperationalError as e:
                logger.warning(f"Could not add bot_logs_channel_id column (might already exist): {e}")
        
        self._conn.commit()

    # --- User Methods ---

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        data = dict(row)
        if 'achievements' in data and isinstance(data['achievements'], str):
            try:
                data['achievements'] = json.loads(data['achievements'])
            except:
                data['achievements'] = []
        return data

    def update_user(self, user_id: int, **kwargs):
        """Update user stats or create if not exists."""
        cursor = self._conn.cursor()
        
        # Serialize achievements if present
        if 'achievements' in kwargs:
            kwargs['achievements'] = json.dumps(kwargs['achievements'])
            
        # Check if exists
        user = self.get_user(user_id)
        if not user:
            # Create with defaults
            cols = ["user_id"] + list(kwargs.keys())
            placeholders = ",".join(["?"] * len(cols))
            vals = [user_id] + list(kwargs.values())
            cursor.execute(f"INSERT INTO users ({','.join(cols)}) VALUES ({placeholders})", vals)
        else:
            # Update specific fields
            if not kwargs:
                return
            set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
            cursor.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", list(kwargs.values()) + [user_id])
            
        self._conn.commit()

    def get_top_users(self, metric: str = "xp", limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard ranking."""
        cursor = self._conn.cursor()
        # Sanitize metric to avoid SQL injection even if it's internal
        allowed_metrics = ["xp", "level", "total_messages", "voice_time_seconds", "music_plays", "commands_used"]
        if metric not in allowed_metrics:
            metric = "xp"
            
        cursor.execute(f"SELECT * FROM users ORDER BY {metric} DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

    # --- Guild Methods ---

    def get_guild(self, guild_id: int) -> Optional[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM guilds WHERE guild_id = ?", (guild_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_guild(self, guild_id: int, **kwargs):
        cursor = self._conn.cursor()
        guild = self.get_guild(guild_id)
        if not guild:
            cols = ["guild_id"] + list(kwargs.keys())
            placeholders = ",".join(["?"] * len(cols))
            vals = [guild_id] + list(kwargs.values())
            cursor.execute(f"INSERT INTO guilds ({','.join(cols)}) VALUES ({placeholders})", vals)
        else:
            if not kwargs:
                return
            set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
            cursor.execute(f"UPDATE guilds SET {set_clause} WHERE guild_id = ?", list(kwargs.values()) + [guild_id])
            
        self._conn.commit()

    # --- Utility ---

    def get_all_users(self) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM users")
        return [dict(row) for row in cursor.fetchall()]

    def get_all_guilds(self) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM guilds")
        return [dict(row) for row in cursor.fetchall()]

    # --- Wellness Methods ---
    def log_mood(self, user_id: int, score: int, note: str = ""):
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO mood_logs (user_id, mood_score, note, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, score, note, datetime.utcnow().isoformat())
        )
        self._conn.commit()

    def get_mood_history(self, user_id: int, limit: int = 7) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM mood_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        return [dict(row) for row in cursor.fetchall()]

    def add_journal_entry(self, user_id: int, text: str):
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO journal_entries (user_id, entry_text, timestamp) VALUES (?, ?, ?)",
            (user_id, text, datetime.utcnow().isoformat())
        )
        self._conn.commit()

    def get_journal_entries(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM journal_entries WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_wellness_settings(self, user_id: int) -> Dict[str, Any]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM user_wellness WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            # Initialize with defaults
            cursor.execute("INSERT INTO user_wellness (user_id) VALUES (?)", (user_id,))
            self._conn.commit()
            return {"user_id": user_id, "therapy_mode_enabled": 1, "last_checkin": None, "checkin_streak": 0}
        return dict(row)

    def update_wellness(self, user_id: int, **kwargs):
        cursor = self._conn.cursor()
        self.get_wellness_settings(user_id) # Ensure exists
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        cursor.execute(f"UPDATE user_wellness SET {set_clause} WHERE user_id = ?", list(kwargs.values()) + [user_id])
        self._conn.commit()

    def close(self):
        self._conn.close()
