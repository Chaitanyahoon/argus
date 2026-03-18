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
                prefix TEXT DEFAULT '!',
                temp_voice_trigger_id INTEGER,
                temp_voice_category_id INTEGER,
                temp_voice_interface_id INTEGER,
                automod_toxicity_enabled INTEGER DEFAULT 0,
                automod_spam_enabled INTEGER DEFAULT 0,
                automod_threshold REAL DEFAULT 0.7
            )
        ''')
        
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

    def close(self):
        self._conn.close()
