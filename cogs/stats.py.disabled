"""
Stats Cog — user profiles, leaderboards, and achievements.
"""

import discord
from discord.ext import commands
import logging
from typing import Optional
import core.embeds as E

logger = logging.getLogger(__name__)


class StatsCog(commands.Cog, name="Stats"):
    """Commands for viewing user statistics, profiles, and achievements."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _usm(self): return getattr(self.bot, "user_stats_manager",  None)
    def _lm(self):  return getattr(self.bot, "leaderboard_manager", None)
    def _am(self):  return getattr(self.bot, "achievement_manager", None)

    @commands.command(name="profile", help="Show your (or another user's) profile and stats.")
    async def profile_command(self, ctx: commands.Context, user: Optional[discord.User] = None):
        usm = self._usm()
        if not usm:
            await ctx.send(embed=E.error("Unavailable", "Stats system not ready.", ctx))
            return

        target = user or ctx.author
        if target.bot:
            await ctx.send(embed=E.error("Bots Not Supported", "Cannot fetch stats for bot accounts.", ctx))
            return

        try:
            embed = usm.create_profile_embed(target, target.id)
            # Ensure consistent footer/timestamp
            embed.set_footer(text=f"👁  Argus")
            embed.timestamp = discord.utils.utcnow()
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error("Error showing profile: %s", e)
            await ctx.send(embed=E.error("Error", "Could not fetch profile.", ctx))

    @commands.command(name="leaderboard", aliases=["lb"], help="Show the server leaderboard.")
    async def leaderboard_command(self, ctx: commands.Context, metric: str = "xp"):
        lm = self._lm()
        if not lm:
            await ctx.send(embed=E.error("Unavailable", "Leaderboard system not ready.", ctx))
            return

        valid = ["xp", "level", "messages", "voice_time", "music_plays", "commands"]
        if metric.lower() not in valid:
            await ctx.send(embed=E.error(
                "Invalid Metric",
                f"Choose from: `{'` · `'.join(valid)}`",
                ctx,
            ))
            return

        try:
            embed = lm.create_leaderboard_embed(metric.lower())
            embed.set_footer(text=f"👁  Argus  ·  sorted by {metric}")
            embed.timestamp = discord.utils.utcnow()
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error("Error showing leaderboard: %s", e)
            await ctx.send(embed=E.error("Error", "Could not fetch leaderboard.", ctx))

    @commands.command(name="achievements", aliases=["badges"], help="Show yours (or another user's) achievements.")
    async def achievements_command(self, ctx: commands.Context, user: Optional[discord.User] = None):
        am = self._am()
        if not am:
            await ctx.send(embed=E.error("Unavailable", "Achievement system not ready.", ctx))
            return

        target       = user or ctx.author
        achievements = am.get_user_achievements(target.id)

        if not achievements:
            await ctx.send(embed=E.info(
                "🏅 No Achievements Yet",
                f"**{target.display_name}** hasn't unlocked anything yet. Keep chatting!",
                ctx,
            ))
            return

        embed = E.gold(
            f"🏅 {target.display_name}'s Achievements",
            f"**{len(achievements)}** achievement{'s' if len(achievements) != 1 else ''} unlocked",
            ctx,
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        for ach_key in achievements:
            ach = am.get_achievement(ach_key)
            if ach:
                embed.add_field(
                    name=f"{ach.tier.value}  {ach.name}",
                    value=ach.description,
                    inline=False,
                )
        await ctx.send(embed=embed)

    @commands.command(name="stats", help="Show overall server statistics.")
    async def stats_command(self, ctx: commands.Context):
        lm = self._lm()
        if not lm:
            await ctx.send(embed=E.error("Unavailable", "Stats system not ready.", ctx))
            return

        try:
            s = lm.get_leaderboard_stats()
            embed = E.navy("📊 Server Statistics", ctx=ctx)
            embed.add_field(name="👥 Members",      value=f"`{s['total_users']:,}`",                      inline=True)
            embed.add_field(name="💬 Messages",     value=f"`{s['total_messages']:,}`",                   inline=True)
            embed.add_field(name="🎤 Voice",        value=f"`{s['total_voice_time'] // 3600:,}h`",        inline=True)
            embed.add_field(name="🎵 Songs Played", value=f"`{s['total_songs']:,}`",                      inline=True)
            embed.add_field(name="⭐ Avg Level",    value=f"`{s['avg_level']:.1f}`",                      inline=True)
            embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else discord.utils.MISSING)
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error("Error showing stats: %s", e)
            await ctx.send(embed=E.error("Error", "Could not fetch statistics.", ctx))


async def setup(bot):
    await bot.add_cog(StatsCog(bot))
