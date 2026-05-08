"""
Achievements & Badges system — unlock achievements through activities.
"""

import logging
from typing import Dict, List
from enum import Enum

logger = logging.getLogger(__name__)


class AchievementTier(Enum):
    """Achievement rarity tiers."""
    COMMON = "🎖️"      # Easy to unlock
    UNCOMMON = "⭐"    # Medium difficulty
    RARE = "✨"        # Hard to unlock
    LEGENDARY = "👑"  # Very hard


class Achievement:
    """Represents a single achievement."""
    
    def __init__(self, name: str, description: str, tier: AchievementTier, icon: str, xp_reward: int = 100):
        self.name = name
        self.description = description
        self.tier = tier
        self.icon = icon
        self.xp_reward = xp_reward
    
    def __str__(self):
        return f"{self.tier.value} {self.name}"


class AchievementManager:
    """Manages all achievements."""
    
    def __init__(self, db):
        """Initialize achievement manager with database."""
        self.db = db
        self._define_achievements()
        logger.info(f"Achievement manager initialized with {len(self.achievements)} achievements")
    
    def _define_achievements(self):
        """Define all game achievements."""
        self.achievements: Dict[str, Achievement] = {
            # Activity achievements
            'first_message': Achievement(
                'First Steps',
                'Send your first message',
                AchievementTier.COMMON,
                '👣'
            ),
            'talker': Achievement(
                'Talker',
                'Send 100 messages',
                AchievementTier.COMMON,
                '💬'
            ),
            'chatterbox': Achievement(
                'Chatterbox',
                'Send 1000 messages',
                AchievementTier.UNCOMMON,
                '🗣️'
            ),
            'conversation_starter': Achievement(
                'Conversation Starter',
                'Reach level 5',
                AchievementTier.UNCOMMON,
                '🎤'
            ),
            'legendary': Achievement(
                'Legendary',
                'Reach level 50',
                AchievementTier.LEGENDARY,
                '👑'
            ),
            
            # Voice achievements
            'first_voice': Achievement(
                'Voice Debut',
                'Join voice for the first time',
                AchievementTier.COMMON,
                '🎤'
            ),
            'voiceover': Achievement(
                'Voice Over',
                'Spend 1 hour in voice',
                AchievementTier.UNCOMMON,
                '⏱️'
            ),
            'voice_master': Achievement(
                'Voice Master',
                'Spend 10 hours in voice',
                AchievementTier.RARE,
                '🔊'
            ),
            
            # NOTE: Music playback features have been removed in this deployment.
            
            # Engagement achievements
            'sociable': Achievement(
                'Sociable',
                'Use 50 commands',
                AchievementTier.COMMON,
                '👥'
            ),
            'power_user': Achievement(
                'Power User',
                'Use 500 commands',
                AchievementTier.UNCOMMON,
                '⚡'
            ),
            'ultimate_user': Achievement(
                'Ultimate User',
                'Use 2000 commands',
                AchievementTier.RARE,
                '🚀'
            ),
            
            # Special achievements
            'early_adopter': Achievement(
                'Early Adopter',
                'Be here from the beginning',
                AchievementTier.RARE,
                '🌅'
            ),
            'collector': Achievement(
                'Collector',
                'Unlock 10 achievements',
                AchievementTier.UNCOMMON,
                '🏆'
            ),
            'completionist': Achievement(
                'Completionist',
                'Unlock all achievements',
                AchievementTier.LEGENDARY,
                '✨'
            ),
        }
    
    def check_and_unlock(self, user_id: int, trigger: str) -> bool:
        """
        Check if achievement should be unlocked.
        
        Args:
            user_id: User ID
            trigger: Achievement key (e.g., 'first_message', 'reach_level_5')
        
        Returns:
            True if newly unlocked
        """
        stats = self.db.get_user(user_id)
        if not stats:
            return False
        
        # Check condition based on trigger
        conditions = {
            'first_message': stats.get('total_messages', 0) >= 1,
            'talker': stats.get('total_messages', 0) >= 100,
            'chatterbox': stats.get('total_messages', 0) >= 1000,
            'conversation_starter': stats.get('level', 1) >= 5,
            'legendary': stats.get('level', 1) >= 50,
            'first_voice': stats.get('voice_time_seconds', 0) > 0,
            'voiceover': stats.get('voice_time_seconds', 0) >= 3600,  # 1 hour
            'voice_master': stats.get('voice_time_seconds', 0) >= 36000,  # 10 hours
            # Music triggers removed — kept for backward compatibility but disabled
            'sociable': stats.get('commands_used', 0) >= 50,
            'power_user': stats.get('commands_used', 0) >= 500,
            'ultimate_user': stats.get('commands_used', 0) >= 2000,
            'collector': len(stats.get('achievements', [])) >= 10,
            'completionist': len(stats.get('achievements', [])) >= len(self.achievements),
        }
        
        if trigger not in conditions:
            return False
        
        if not conditions[trigger]:
            return False
        
        # Check if already has achievement
        if trigger in stats.get('achievements', []):
            return False
        
        # Unlock it!
        achievements = stats.get('achievements', [])
        achievements.append(trigger)
        
        self.db.set_user(user_id, achievements=achievements)
        logger.info(f"Achievement unlocked! User {user_id}: {trigger}")
        
        return True
    
    def get_achievement(self, key: str) -> Achievement:
        """Get achievement by key."""
        return self.achievements.get(key)
    
    def get_all_achievements(self) -> Dict[str, Achievement]:
        """Get all achievements."""
        return self.achievements
    
    def get_user_achievements(self, user_id: int) -> List[str]:
        """Get user's unlocked achievements."""
        stats = self.db.get_user(user_id)
        if not stats:
            return []
        
        return stats.get('achievements', [])
    
    def create_achievement_embed(self, achievement_key: str):
        """Create embed for achievement."""
        achievement = self.get_achievement(achievement_key)
        if not achievement:
            return None
        
        import discord
        from datetime import datetime
        
        embed = discord.Embed(
            title=f"🎉 Achievement Unlocked!",
            description=f"{achievement}",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Name", value=achievement.name, inline=True)
        embed.add_field(name="Tier", value=str(achievement.tier.name), inline=True)
        embed.add_field(name="XP Reward", value=f"+{achievement.xp_reward} XP", inline=True)
        embed.add_field(name="Description", value=achievement.description, inline=False)
        
        return embed
