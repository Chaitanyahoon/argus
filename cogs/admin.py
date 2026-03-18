"""
Admin Cog — bot management, setup automation, and activities.
"""

import discord
from discord.ext import commands
import logging
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
            trigger   = await category.create_voice_channel("➕ Create VC")
            logs      = await category.create_text_channel("👁️-nexus-logs")
            interface = await category.create_text_channel("🎮-vc-management")

            am.db.set_guild(
                ctx.guild.id,
                temp_voice_category_id=category.id,
                temp_voice_trigger_id=trigger.id,
                temp_voice_interface_id=interface.id,
                logging_channel_id=logs.id,
            )

            embed = E.success("✅ Setup Complete!", "All Argus channels have been created.", ctx)
            embed.add_field(name="📁 Category",   value=category.name,      inline=True)
            embed.add_field(name="🔊 Trigger VC", value=trigger.mention,    inline=True)
            embed.add_field(name="📋 Nexus Logs", value=logs.mention,       inline=True)
            embed.add_field(name="🎮 Interface",  value=interface.mention,  inline=True)
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


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
