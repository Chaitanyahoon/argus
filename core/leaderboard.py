"""
Leaderboard system — track top users by various metrics.
"""

import logging
import discord
from datetime import datetime
from typing import List, Tuple, Optional, Any, Dict

logger = logging.getLogger(__name__)


class LeaderboardManager:
    """Manages leaderboards across multiple metrics."""
    
    def __init__(self, db):
        """Initialize leaderboard manager."""
        self.db = db
        logger.info("Leaderboard manager initialized")
    
    def get_leaderboard(self, metric: str = "xp", guild_id: Optional[int] = None, limit: int = 10) -> List[Tuple]:
        """
        Get leaderboard for a specific metric.
        
        Args:
            metric: 'xp', 'messages', 'voice_time', 'music_plays', 'commands'
            guild_id: Filter by guild (optional)
            limit: Number of entries (default 10)
        
        Returns:
            List of (rank, user_id, username, value)
        """
        # Get top users from SQLite
        # If db has get_top_users, use it. Otherwise fallback to read() shim.
        if hasattr(self.db, 'get_top_users'):
            sorted_users = self.db.get_top_users(metric, limit)
        else:
            # Fallback for old ArgusDb shim
            all_users = self.db._read("users.json")
            sort_key_map = {
                'xp': lambda u: u.get('xp', 0) + (u.get('level', 1) * 10000),
                'level': lambda u: u.get('level', 1),
                'messages': lambda u: u.get('total_messages', 0),
                'voice_time_seconds': lambda u: u.get('voice_time_seconds', 0),
                'music_plays': lambda u: u.get('music_plays', 0),
                'commands_used': lambda u: u.get('commands_used', 0),
            }
            m_key = 'voice_time_seconds' if metric == 'voice_time' else metric
            if m_key not in sort_key_map: m_key = 'xp'
            all_users_list: List[Dict[str, Any]] = list(all_users)
            full_sorted = sorted(all_users_list, key=sort_key_map[m_key], reverse=True)
            sorted_users = full_sorted[:limit]
        
        # Build leaderboard
        leaderboard = []
        for rank, user in enumerate(sorted_users, 1):
            if metric == 'xp':
                value = user.get('xp', 0) + (user.get('level', 1) * 10000)
            elif metric == 'voice_time':
                value = user.get('voice_time_seconds', 0)
            else:
                value = user.get(metric, 0)
            
            leaderboard.append((
                rank,
                user.get('user_id'),
                user.get('username', 'Unknown'),
                value
            ))
        
        return leaderboard
    
    def get_user_rank(self, user_id: int, metric: str = "xp") -> Optional[int]:
        """Get user's rank for a specific metric."""
        leaderboard = self.get_leaderboard(metric, limit=10000)
        
        for rank, uid, _, _ in leaderboard:
            if uid == user_id:
                return rank
        
        return None
    
    def create_leaderboard_embed(self, metric: str = "xp") -> discord.Embed:
        """Create a beautiful leaderboard embed."""
        leaderboard = self.get_leaderboard(metric, limit=10)
        
        # Metric display names
        metric_names = {
            'xp': 'Experience Points',
            'level': 'Level',
            'messages': 'Messages Sent',
            'voice_time': 'Voice Time (seconds)',
            'music_plays': 'Songs Played',
            'commands': 'Commands Used',
        }
        
        # Medal emojis
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        embed = discord.Embed(
            title=f"🏆 **{metric_names.get(metric, metric)} Leaderboard**",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        # Build leaderboard text
        lb_text = ""
        for rank, user_id, username, value in leaderboard:
            medal = medals[rank - 1] if rank <= len(medals) else f"{rank}️⃣"
            
            if metric == 'voice_time':
                hours = value // 3600
                minutes = (value % 3600) // 60
                value_str = f"{hours}h {minutes}m"
            else:
                value_str = f"{value:,}"
            
            lb_text += f"{medal} **{username}** - {value_str}\n"
        
        embed.description = lb_text or "No users yet!"
        embed.set_footer(text=f"Last updated: {datetime.utcnow().strftime('%H:%M:%S')}")
        
        return embed
    
    def get_leaderboard_stats(self) -> dict:
        """Get overall leaderboard statistics."""
        # Optimized with SQL if possible
        if hasattr(self.db, 'sqlite'):
            cursor = self.db.sqlite._conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*), 
                    SUM(xp), 
                    SUM(total_messages), 
                    SUM(voice_time_seconds), 
                    SUM(music_plays),
                    AVG(level)
                FROM users
            """)
            counts = cursor.fetchone()
            return {
                'total_users': int(counts[0] or 0),
                'total_xp': int(counts[1] or 0),
                'total_messages': int(counts[2] or 0),
                'total_voice_time': int(counts[3] or 0),
                'total_songs': int(counts[4] or 0),
                'avg_level': float(f"{float(counts[5] or 0):.1f}"),
            }
        
        # Fallback for JSON
        all_users = self.db._read("users.json")
        if not all_users:
            return {'total_users': 0, 'total_xp': 0, 'total_messages': 0, 'total_voice_time': 0, 'total_songs': 0, 'avg_level': 0}
            
        total_xp = sum(u.get('xp', 0) for u in all_users)
        total_messages = sum(u.get('total_messages', 0) for u in all_users)
        total_voice_seconds = sum(u.get('voice_time_seconds', 0) for u in all_users)
        total_songs = sum(u.get('music_plays', 0) for u in all_users)
        
        return {
            'total_users': int(len(all_users)),
            'total_xp': int(total_xp),
            'total_messages': int(total_messages),
            'total_voice_time': int(total_voice_seconds),
            'total_songs': int(total_songs),
            'avg_level': float(f"{float(sum(u.get('level', 1) for u in all_users) / len(all_users)):.1f}"),
        }
