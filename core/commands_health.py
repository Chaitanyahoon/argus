"""
Health check and status Discord commands.
Provides bot status, health, and statistics commands.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging

from core.health_monitor import get_health_manager, HealthStatus
from core.conversation_context import get_context_manager
from core.response_cache import get_cache
from core.enhanced_logging import get_performance_tracker
from core.error_handling import get_error_metrics

logger = logging.getLogger(__name__)


class HealthCommands(commands.Cog):
    """Commands for monitoring bot health and statistics."""
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @app_commands.command(name="health", description="Check bot and API health status")
    async def health_check(self, interaction: discord.Interaction) -> None:
        """Show detailed health check results."""
        health_manager = get_health_manager()
        
        if not health_manager:
            await interaction.response.send_message(
                "❌ Health monitoring not initialized",
                ephemeral=True
            )
            return
        
        # Run health checks
        await interaction.response.defer()
        report = await health_manager.run_all_checks()
        
        # Create embed
        Color_map = {
            HealthStatus.HEALTHY: discord.Color.green(),
            HealthStatus.DEGRADED: discord.Color.orange(),
            HealthStatus.UNHEALTHY: discord.Color.red(),
            HealthStatus.UNKNOWN: discord.Color.greyple(),
        }
        
        embed = discord.Embed(
            title="🏥 Health Status",
            color=Color_map.get(report.overall_status, discord.Color.greyple()),
            description=f"Overall Status: **{report.overall_status.value.upper()}**"
        )
        
        # Add component statuses
        for component_name, check in report.checks.items():
            status_emoji = {
                HealthStatus.HEALTHY: "✅",
                HealthStatus.DEGRADED: "⚠️",
                HealthStatus.UNHEALTHY: "❌",
                HealthStatus.UNKNOWN: "❓",
            }.get(check.status, "❓")
            
            embed.add_field(
                name=f"{status_emoji} {component_name.upper()}",
                value=f"{check.message}\nLatency: {check.latency_ms:.1f}ms",
                inline=False
            )
        
        # Add uptime
        uptime = health_manager.get_uptime()
        embed.add_field(
            name="⏱️ Uptime",
            value=uptime['formatted'],
            inline=True
        )
        
        embed.set_footer(text=f"Last check: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="stats", description="Show bot statistics and metrics")
    async def bot_stats(self, interaction: discord.Interaction) -> None:
        """Display bot usage statistics."""
        embed = discord.Embed(
            title="📊 Bot Statistics",
            color=discord.Color.blue()
        )
        
        # Bot info
        embed.add_field(
            name="📍 Guilds",
            value=f"{len(self.bot.guilds)} active",
            inline=True
        )
        
        # Conversation context stats
        context_manager = get_context_manager()
        if context_manager:
            ctx_stats = context_manager.get_stats()
            embed.add_field(
                name="💬 Conversations",
                value=f"{ctx_stats['active_conversations']} active, {ctx_stats['total_messages']} messages",
                inline=True
            )
        
        # Cache stats
        cache = get_cache()
        if cache:
            cache_stats = cache.get_stats()
            embed.add_field(
                name="✻ Cache",
                value=f"{cache_stats['valid_entries']} valid, {cache_stats['expired_entries']} expired",
                inline=True
            )
        
        # Performance metrics
        tracker = get_performance_tracker()
        embed.add_field(
            name="⏱️ Performance",
            value=f"Tracked {len(tracker.metrics)} operations",
            inline=False
        )
        
        # Error metrics
        error_metrics = get_error_metrics()
        error_summary = error_metrics.get_summary()
        embed.add_field(
            name="⚠️ Errors",
            value=f"Total: {error_summary['total_errors']}",
            inline=True
        )
        
        # Uptime
        health_manager = get_health_manager()
        if health_manager:
            uptime = health_manager.get_uptime()
            embed.add_field(
                name="🕐 Uptime",
                value=uptime['formatted'],
                inline=True
            )
        
        await interaction.response.send_embed(embed)
    
    @app_commands.command(name="uptime", description="Show bot uptime")
    async def uptime(self, interaction: discord.Interaction) -> None:
        """Display bot uptime."""
        health_manager = get_health_manager()
        
        if not health_manager:
            await interaction.response.send_message(
                "❌ Health monitoring not initialized",
                ephemeral=True
            )
            return
        
        uptime = health_manager.get_uptime()
        
        embed = discord.Embed(
            title="⏰ Bot Uptime",
            description=f"**{uptime['formatted']}**",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Total Seconds",
            value=f"{uptime['total_seconds']:.0f}",
            inline=False
        )
        
        await interaction.response.send_embed(embed)
    
    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction) -> None:
        """Show bot ping/latency."""
        latency_ms = self.bot.latency * 1000
        
        # Determine status emoji
        if latency_ms < 50:
            emoji = "🟢"
        elif latency_ms < 100:
            emoji = "🟡"
        else:
            emoji = "🔴"
        
        embed = discord.Embed(
            title=f"{emoji} Pong!",
            description=f"**{latency_ms:.0f}ms**",
            color=discord.Color.green() if latency_ms < 100 else discord.Color.orange()
        )
        
        await interaction.response.send_embed(embed)


async def setup(bot: commands.Bot) -> None:
    """Load health commands cog."""
    await bot.add_cog(HealthCommands(bot))
    logger.info("✅ Health commands loaded")
