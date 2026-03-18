"""
Stats Cog — handles user profiles, leaderboards, and achievements.
Modularized from the original monolithic bot.py.
"""

import discord
from discord.ext import commands
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class StatsCog(commands.Cog, name="Stats"):
    """Commands for viewing user statistics, profiles, and achievements."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_user_stats_manager(self):
        return getattr(self.bot, "user_stats_manager", None)

    def get_leaderboard_manager(self):
        return getattr(self.bot, "leaderboard_manager", None)

    def get_achievement_manager(self):
        return getattr(self.bot, "achievement_manager", None)

    @commands.command(name="profile", help="Show your profile and stats.")
    async def profile_command(self, ctx: commands.Context, user: Optional[discord.User] = None):
        usm = self.get_user_stats_manager()
        if not usm:
            await ctx.send("❌ Stats system not ready.")
            return
        
        target_user = user or ctx.author
        if target_user.bot:
            await ctx.send("❌ Cannot get stats for bot accounts.")
            return
        
        try:
            embed = usm.create_profile_embed(target_user, target_user.id)
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error showing profile: {e}")
            await ctx.send("❌ Error fetching profile.")

    @commands.command(name="leaderboard", aliases=["lb"], help="Show server leaderboard.")
    async def leaderboard_command(self, ctx: commands.Context, metric: str = "xp"):
        lm = self.get_leaderboard_manager()
        if not lm:
            await ctx.send("❌ Leaderboard system not ready.")
            return
        
        valid_metrics = ['xp', 'level', 'messages', 'voice_time', 'music_plays', 'commands']
        if metric.lower() not in valid_metrics:
            await ctx.send(f"❌ Invalid metric. Choose from: {', '.join(valid_metrics)}")
            return
        
        try:
            embed = lm.create_leaderboard_embed(metric.lower())
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error showing leaderboard: {e}")
            await ctx.send("❌ Error fetching leaderboard.")

    @commands.command(name="achievements", aliases=["badges"], help="Show your achievements.")
    async def achievements_command(self, ctx: commands.Context, user: Optional[discord.User] = None):
        am = self.get_achievement_manager()
        if not am:
            await ctx.send("❌ Achievement system not ready.")
            return
        
        target_user = user or ctx.author
        achievements = am.get_user_achievements(target_user.id)
        
        if not achievements:
            await ctx.send(f"🏅 {target_user.name} has no achievements yet.")
            return
        
        embed = discord.Embed(
            title=f"🏅 {target_user.name}'s Achievements",
            description=f"Unlocked {len(achievements)} achievements",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        
        for ach_key in achievements:
            ach = am.get_achievement(ach_key)
            if ach:
                embed.add_field(
                    name=ach.tier.value + " " + ach.name,
                    value=ach.description,
                    inline=False
                )
        
        await ctx.send(embed=embed)

    @commands.command(name="stats", help="Show overall bot statistics.")
    async def stats_command(self, ctx: commands.Context):
        lm = self.get_leaderboard_manager()
        if not lm:
            await ctx.send("❌ Stats system not ready.")
            return
        
        try:
            stats = lm.get_leaderboard_stats()
            embed = discord.Embed(
                title="📊 Bot Statistics",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="👥 Users", value=f"{stats['total_users']} total users", inline=True)
            embed.add_field(name="💬 Messages", value=f"{stats['total_messages']:,} total", inline=True)
            embed.add_field(name="🎤 Voice Time", value=f"{stats['total_voice_time'] // 3600:,} hours", inline=True)
            embed.add_field(name="🎵 Songs Played", value=f"{stats['total_songs']:,} total", inline=True)
            embed.add_field(name="⭐ Average Level", value=f"{stats['avg_level']:.1f}", inline=True)
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error showing stats: {e}")
            await ctx.send("❌ Error fetching statistics.")

async def setup(bot):
    await bot.add_cog(StatsCog(bot))
