"""
User statistics and profile management — track metrics for gamification.
Handles XP, achievements, voice time, music play count, etc.
"""

import logging
import discord
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class UserStats:
    """User statistics snapshot."""
    user_id: int
    username: str
    level: int = 1
    xp: int = 0
    total_messages: int = 0
    voice_time_seconds: int = 0
    music_plays: int = 0
    commands_used: int = 0
    achievements: list = None
    joined_at: str = None
    last_activity: str = None
    favorite_music_genre: str = None
    
    def __post_init__(self):
        if self.achievements is None:
            self.achievements = []
        if self.joined_at is None:
            self.joined_at = datetime.utcnow().isoformat()
        if self.last_activity is None:
            self.last_activity = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'UserStats':
        """Create from dictionary."""
        return UserStats(**data)
    
    def get_xp_for_next_level(self, level: int) -> int:
        """Calculate XP needed for next level (exponential growth)."""
        return (level + 1) ** 2 * 100
    
    def get_progress_to_next_level(self) -> tuple:
        """Get current XP and XP needed for next level."""
        needed = self.get_xp_for_next_level(self.level)
        return self.xp, needed
    
    def get_voice_time_display(self) -> str:
        """Format voice time as readable string."""
        hours = self.voice_time_seconds // 3600
        minutes = (self.voice_time_seconds % 3600) // 60
        seconds = self.voice_time_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


class UserStatsManager:
    """Manages user statistics and profile data."""
    
    # XP rewards for different activities
    XP_PER_MESSAGE = 15
    XP_PER_VOICE_MINUTE = 10
    XP_PER_COMMAND = 5
    XP_PER_SONG = 2
    
    # Level thresholds (exponential)
    def __init__(self, db):
        """Initialize stats manager with database connection."""
        self.db = db
        logger.info("User stats manager initialized")
    
    def get_user_stats(self, user_id: int) -> Optional[UserStats]:
        """Get user statistics."""
        user_data = self.db.get_user(user_id)
        if not user_data:
            return None
        
        return UserStats(
            user_id=user_id,
            username=user_data.get('username', 'Unknown'),
            level=user_data.get('level', 1),
            xp=user_data.get('xp', 0),
            total_messages=user_data.get('total_messages', 0),
            voice_time_seconds=user_data.get('voice_time_seconds', 0),
            music_plays=user_data.get('music_plays', 0),
            commands_used=user_data.get('commands_used', 0),
            achievements=user_data.get('achievements', []),
            joined_at=user_data.get('joined_at', datetime.utcnow().isoformat()),
            last_activity=user_data.get('last_activity', datetime.utcnow().isoformat()),
            favorite_music_genre=user_data.get('favorite_music_genre', None)
        )
    
    def add_message_xp(self, user_id: int, username: str) -> tuple:
        """Add XP for message. Returns (new_level, level_up)."""
        stats = self.get_user_stats(user_id)
        if not stats:
            stats = UserStats(user_id=user_id, username=username)
        
        stats.total_messages += 1
        stats.xp += self.XP_PER_MESSAGE
        stats.last_activity = datetime.utcnow().isoformat()
        
        # Check for level up
        level_up = False
        while stats.xp >= stats.get_xp_for_next_level(stats.level):
            stats.xp -= stats.get_xp_for_next_level(stats.level)
            stats.level += 1
            level_up = True
            logger.info(f"Level up! {username} ({user_id}) reached level {stats.level}")
        
        # Save to db
        self.db.set_user(
            user_id,
            username=username,
            level=stats.level,
            xp=stats.xp,
            total_messages=stats.total_messages,
            last_activity=stats.last_activity
        )
        
        return stats.level, level_up
    
    def add_voice_time(self, user_id: int, seconds: int) -> None:
        """Track voice conversation time."""
        stats = self.get_user_stats(user_id)
        if not stats:
            return
        
        stats.voice_time_seconds += seconds
        xp_earned = (seconds // 60) * self.XP_PER_VOICE_MINUTE  # XP per minute
        stats.xp += xp_earned
        stats.last_activity = datetime.utcnow().isoformat()
        
        # Check for level up
        while stats.xp >= stats.get_xp_for_next_level(stats.level):
            stats.xp -= stats.get_xp_for_next_level(stats.level)
            stats.level += 1
        
        self.db.set_user(
            user_id,
            level=stats.level,
            xp=stats.xp,
            voice_time_seconds=stats.voice_time_seconds,
            last_activity=stats.last_activity
        )
    
    def add_command_used(self, user_id: int) -> None:
        """Track command usage."""
        stats = self.get_user_stats(user_id)
        if not stats:
            return
        
        stats.commands_used += 1
        stats.xp += self.XP_PER_COMMAND
        stats.last_activity = datetime.utcnow().isoformat()
        
        self.db.set_user(
            user_id,
            commands_used=stats.commands_used,
            xp=stats.xp,
            last_activity=stats.last_activity
        )
    
    def add_music_play(self, user_id: int, genre: str = None) -> None:
        """Music tracking disabled in this deployment. Kept as a no-op for compatibility."""
        logger.debug("add_music_play called but music features are disabled; no-op")
    
    def add_achievement(self, user_id: int, achievement: str) -> bool:
        """Add achievement. Returns True if new."""
        stats = self.get_user_stats(user_id)
        if not stats:
            return False
        
        if achievement not in stats.achievements:
            stats.achievements.append(achievement)
            logger.info(f"Achievement unlocked! {stats.username} got '{achievement}'")
            
            self.db.set_user(
                user_id,
                achievements=stats.achievements
            )
            return True
        
        return False
    
    def get_rank(self, user_id: int, guild_id: int = None) -> tuple:
        """Get user's rank. Returns (rank, total_users)."""
        if guild_id:
            guild_data = self.db.get_guild(guild_id)
            if not guild_data:
                return None, 0
            # In future, filter by guild
        
        # For now, get all users sorted by level then XP
        all_users = self.db._read(self.db.users_file)
        sorted_users = sorted(
            all_users,
            key=lambda u: (u.get('level', 1), u.get('xp', 0)),
            reverse=True
        )
        
        rank = next(
            (i + 1 for i, u in enumerate(sorted_users) if u.get('user_id') == user_id),
            None
        )
        
        return rank, len(sorted_users)
    
    def create_profile_embed(self, user: discord.User, user_id: int) -> discord.Embed:
        """Create a beautiful profile embed."""
        stats = self.get_user_stats(user_id)
        if not stats:
            stats = UserStats(user_id=user_id, username=str(user))
        
        rank, total = self.get_rank(user_id)
        xp_current, xp_needed = stats.get_progress_to_next_level()
        
        # Progress bar
        bar_length = 20
        filled = int((xp_current / xp_needed) * bar_length)
        progress_bar = "█" * filled + "░" * (bar_length - filled)
        
        embed = discord.Embed(
            title=f"👤 {stats.username}'s Profile",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📊 Level & XP",
            value=f"**Level:** {stats.level}\n**XP:** {xp_current}/{xp_needed}\n`{progress_bar}` {int((xp_current/xp_needed)*100)}%",
            inline=False
        )
        
        embed.add_field(
            name="🏆 Rank",
            value=f"**#{rank}** out of {total} users" if rank else "N/A",
            inline=True
        )
        
        embed.add_field(
            name="💬 Activity",
            value=f"**Messages:** {stats.total_messages}\n**Commands:** {stats.commands_used}",
            inline=True
        )
        
        embed.add_field(
            name="🎤 Voice Stats",
            value=f"**Time:** {stats.get_voice_time_display()}\n**Genre:** {stats.favorite_music_genre or 'Not set'}",
            inline=True
        )
        
        embed.add_field(
            name="🎵 Music",
            value="Music features disabled in this deployment",
            inline=True
        )
        
        if stats.achievements:
            achievements_str = " ".join([f"🏅 {a}" for a in stats.achievements[:10]])
            if len(stats.achievements) > 10:
                achievements_str += f" +{len(stats.achievements) - 10} more"
            embed.add_field(
                name="🎖️ Achievements",
                value=achievements_str,
                inline=False
            )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Joined: {stats.joined_at}")
        
        return embed
