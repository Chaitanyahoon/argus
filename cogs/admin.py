"""
Admin Cog — bot management, setup automation, activities, and logging.
"""

import discord
from discord.ext import commands
import logging
from core.bot_logs import get_logs_manager
import core.embeds as E
from config import Config

logger = logging.getLogger(__name__)


class AdminCog(commands.Cog, name="Admin"):
    """Administrative commands for bot configuration and system setup."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_argus_manager(self):
        return getattr(self.bot, "argus_manager", None)

    @commands.command(name="autosetup", help="Automatically configure all required channels.")
    @commands.has_permissions(administrator=True)
    async def auto_setup_cmd(self, ctx: commands.Context):
        am = self.get_argus_manager()
        if not am:
            return

        msg = await ctx.send(embed=E.info("⚙️ Initializing Setup", "Creating Argus system channels…", ctx))

        try:
            category  = await ctx.guild.create_category("➕ Argus Systems")
            logs      = await category.create_text_channel("👁️-nexus-logs")
            bot_logs  = await category.create_text_channel("🤖-bot-logs")

            am.db.set_guild(
                ctx.guild.id,
                logging_channel_id=logs.id,
                bot_logs_channel_id=bot_logs.id,
            )

            embed = E.success("✅ Setup Complete!", "All Argus channels have been created.", ctx)
            embed.add_field(name="📁 Category",   value=category.name,      inline=True)
            embed.add_field(name="📋 Nexus Logs", value=logs.mention,       inline=True)
            embed.add_field(name="🤖 Bot Logs",   value=bot_logs.mention,   inline=True)
            embed.set_footer(text="Run >>botlogs, >>health, or >>errors to monitor bot performance")
            await msg.edit(embed=embed)

        except Exception as e:
            await msg.edit(embed=E.error("❌ Setup Failed", str(e), ctx))

    @commands.command(name="setactivity", help="Set the bot's status activity.")
    @commands.is_owner()
    async def set_activity_cmd(self, ctx: commands.Context, type: str, *, name: str):
        activity_type = {
            "playing":   discord.ActivityType.playing,
            "listening": discord.ActivityType.listening,
            "watching":  discord.ActivityType.watching,
        }.get(type.lower(), discord.ActivityType.watching)

        await self.bot.change_presence(activity=discord.Activity(type=activity_type, name=name))
        await ctx.send(embed=E.success(
            "🎭 Activity Updated",
            f"**{type.title()}** {name}",
            ctx,
        ))

    @commands.command(name="nexus_setup", help="Set the Nexus logging channel.")
    @commands.has_permissions(administrator=True)
    async def nexus_setup_cmd(self, ctx: commands.Context, channel: discord.TextChannel):
        am = self.get_argus_manager()
        if not am:
            return
        am.db.set_guild(ctx.guild.id, logging_channel_id=channel.id)
        await ctx.send(embed=E.success(
            "👁️ Nexus Logs Configured",
            f"Mod logs will be sent to {channel.mention}.",
            ctx,
        ))

    @commands.command(name="botlogs", help="Show recent bot logs.")
    @commands.has_permissions(administrator=True)
    async def botlogs_cmd(self, ctx: commands.Context, lines: int = 20, level: str = None):
        """Display recent bot logs with optional filtering by level."""
        if lines > 50:
            lines = 50
        if lines < 5:
            lines = 5

        logs_mgr = get_logs_manager()
        log_content = logs_mgr.get_latest_logs(lines=lines, level=level)

        embed = E.info("🤖 Bot Logs", log_content, ctx)
        if level:
            embed.title += f" ({level})"
        embed.set_footer(text=f"Last {lines} lines")
        
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            # If too large, send in code block
            await ctx.send(f"**🤖 Bot Logs** ({level or 'all levels'})\n{log_content}")

    @commands.command(name="health", help="Show bot system health status.")
    @commands.has_permissions(administrator=True)
    async def health_cmd(self, ctx: commands.Context):
        """Display bot system health including error counts and warnings."""
        logs_mgr = get_logs_manager()
        health_status = logs_mgr.get_system_health()
        
        embed = E.success("💚 System Health", health_status, ctx)
        embed.add_field(name="📊 Guilds", value=f"`{len(self.bot.guilds)}`", inline=True)
        embed.add_field(name="📡 Latency", value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)
        embed.add_field(name="⚙️ Uptime", value="`~active`", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="errors", help="Show recent errors and warnings.")
    @commands.has_permissions(administrator=True)
    async def errors_cmd(self, ctx: commands.Context, hours: int = 24):
        """Display errors and warnings from the last N hours."""
        if hours < 1 or hours > 7 * 24:
            hours = 24

        logs_mgr = get_logs_manager()
        error_count, warning_count, summary = logs_mgr.get_errors_and_warnings(hours=hours)

        if error_count > 5:
            embed = E.warning("📋 Error Report", summary, ctx)
        else:
            embed = E.success("📋 Error Report", summary, ctx)
        embed.set_footer(text=f"Last {hours} hour{'s' if hours > 1 else ''}")
        
        await ctx.send(embed=embed)

    @commands.command(name="loglogs", help="Show available log files.")
    @commands.has_permissions(administrator=True)
    async def loglogs_cmd(self, ctx: commands.Context):
        """Display information about available log files."""
        logs_mgr = get_logs_manager()
        logs_info = logs_mgr.get_log_timestamps()

        embed = E.info("📂 Log Files", logs_info, ctx)
        
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
