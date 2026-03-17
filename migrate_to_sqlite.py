"""
Migration script: Convert JSON guild/user data to SQLite database.
Run this once to migrate from the old JSON-based storage to SQLite.
"""

import json
import logging
from pathlib import Path
from data_manager import DatabaseManager
from logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


def migrate_json_to_sqlite(json_guilds_path: str = "data/guilds.json",
                          json_users_path: str = "data/users.json") -> None:
    """Migrate JSON data files to SQLite database."""
    
    db = DatabaseManager()
    
    guilds_path = Path(json_guilds_path)
    users_path = Path(json_users_path)
    
    # Migrate guilds
    if guilds_path.exists():
        try:
            with open(guilds_path, "r") as f:
                guilds_data = json.load(f)
            
            # Handle both list and dict formats
            if isinstance(guilds_data, list):
                guilds_list = guilds_data
            else:
                guilds_list = list(guilds_data.values()) if guilds_data else []
            
            logger.info(f"Migrating {len(guilds_list)} guilds to SQLite...")
            
            for guild_info in guilds_list:
                guild_id = guild_info.get("guild_id")
                if not guild_id:
                    logger.warning(f"Skipping guild entry without guild_id: {guild_info}")
                    continue
                
                db.save_guild(
                    guild_id=int(guild_id),
                    name=guild_info.get("name", f"Guild {guild_id}"),
                    owner_id=guild_info.get("owner_id", 0),
                    member_count=0,
                    data=guild_info
                )
            
            logger.info(f"✅ Successfully migrated {len(guilds_list)} guilds")
            
            # Create backup of JSON file
            backup_path = guilds_path.parent / f"{guilds_path.name}.backup"
            guilds_path.rename(backup_path)
            logger.info(f"Original JSON backed up to: {backup_path}")
        
        except Exception as e:
            logger.error(f"❌ Guild migration failed: {e}")
            raise
    else:
        logger.info("No guilds.json found, skipping guild migration")
    
    # Migrate users
    if users_path.exists():
        try:
            with open(users_path, "r") as f:
                users_data = json.load(f)
            
            # Handle both list and dict formats
            if isinstance(users_data, list):
                users_list = users_data
            else:
                users_list = list(users_data.values()) if users_data else []
            
            logger.info(f"Migrating {len(users_list)} users to SQLite...")
            
            for user_info in users_list:
                user_id = user_info.get("user_id")
                if not user_id:
                    logger.warning(f"Skipping user entry without user_id: {user_info}")
                    continue
                
                db.save_user(
                    user_id=int(user_id),
                    username=user_info.get("username", f"User {user_id}"),
                    data=user_info
                )
            
            logger.info(f"✅ Successfully migrated {len(users_list)} users")
            
            # Create backup of JSON file
            backup_path = users_path.parent / f"{users_path.name}.backup"
            users_path.rename(backup_path)
            logger.info(f"Original JSON backed up to: {backup_path}")
        
        except Exception as e:
            logger.error(f"❌ User migration failed: {e}")
            raise
    else:
        logger.info("No users.json found, skipping user migration")
    
    # Create backup of database
    db.backup()
    
    # Print statistics
    stats = db.get_stats()
    logger.info(f"\n📊 Migration complete! Database stats:")
    logger.info(f"   - Guilds: {stats['guilds']}")
    logger.info(f"   - Users: {stats['users']}")
    logger.info(f"   - Activity entries: {stats['activities']}")


if __name__ == "__main__":
    migrate_json_to_sqlite()
