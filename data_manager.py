"""
SQLite-based persistent data storage layer.
Replaces JSON files with a robust, queryable database with automatic backups.
"""

import sqlite3
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, Dict, List
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database for guild and user data with automatic backups."""
    
    def __init__(self, db_path: str = "data/bot.db", backup_dir: str = "data/backups"):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_db()
        logger.info(f"Database initialized: {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Guilds table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS guilds (
                    guild_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    owner_id INTEGER,
                    member_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data JSON DEFAULT '{}'
                )
            """)
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data JSON DEFAULT '{}'
                )
            """)
            
            # Guild members table (many-to-many)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS guild_members (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    nickname TEXT,
                    roles JSON DEFAULT '[]',
                    PRIMARY KEY (guild_id, user_id),
                    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Activity log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details JSON,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Create indices for common queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_guilds_owner ON guilds(owner_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_guild ON activity_log(guild_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_log(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_time ON activity_log(timestamp)")
            
            conn.commit()
    
    def backup(self) -> Path:
        """Create a backup of the database."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"bot_{timestamp}.db"
        
        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise
    
    def restore_from_backup(self, backup_path: Path) -> None:
        """Restore database from a backup file."""
        try:
            shutil.copy2(backup_path, self.db_path)
            logger.info(f"Database restored from {backup_path}")
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise
    
    # Guild operations
    
    def save_guild(self, guild_id: int, name: str, owner_id: int, 
                   member_count: int = 0, data: Optional[Dict[str, Any]] = None) -> None:
        """Save or update guild information."""
        data = data or {}
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO guilds 
                (guild_id, name, owner_id, member_count, data, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (guild_id, name, owner_id, member_count, json.dumps(data)))
    
    def get_guild(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Get guild information."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM guilds WHERE guild_id = ?", (guild_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_all_guilds(self) -> List[Dict[str, Any]]:
        """Get all guilds."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM guilds ORDER BY updated_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def update_guild_data(self, guild_id: int, data: Dict[str, Any]) -> None:
        """Update custom data for a guild."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE guilds 
                SET data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE guild_id = ?
            """, (json.dumps(data), guild_id))
    
    # User operations
    
    def save_user(self, user_id: int, username: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Save or update user information."""
        data = data or {}
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, username, data, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, username, json.dumps(data)))
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def update_user_data(self, user_id: int, data: Dict[str, Any]) -> None:
        """Update custom data for a user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (json.dumps(data), user_id))
    
    # Guild member operations
    
    def save_guild_member(self, guild_id: int, user_id: int, nickname: Optional[str] = None,
                         roles: Optional[List[int]] = None) -> None:
        """Save guild member relationship."""
        roles = roles or []
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO guild_members 
                (guild_id, user_id, nickname, roles, joined_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (guild_id, user_id, nickname, json.dumps(roles)))
    
    def get_guild_members(self, guild_id: int) -> List[Dict[str, Any]]:
        """Get all members in a guild."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM guild_members WHERE guild_id = ?
                ORDER BY joined_at DESC
            """, (guild_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # Activity logging
    
    def log_activity(self, action: str, guild_id: Optional[int] = None, 
                    user_id: Optional[int] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """Log an activity."""
        details = details or {}
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO activity_log (guild_id, user_id, action, details)
                VALUES (?, ?, ?, ?)
            """, (guild_id, user_id, action, json.dumps(details)))
    
    def get_activity_log(self, guild_id: Optional[int] = None, user_id: Optional[int] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Get activity logs with optional filtering."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM activity_log WHERE 1=1"
            params = []
            
            if guild_id:
                query += " AND guild_id = ?"
                params.append(guild_id)
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM guilds")
            guild_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM activity_log")
            activity_count = cursor.fetchone()[0]
            
            return {
                "guilds": guild_count,
                "users": user_count,
                "activities": activity_count,
            }
