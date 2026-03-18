"""
Argus Cog — handles bot info, setup status, and evolutionary leveling.
Modularized from the original monolithic bot.py.
"""

import discord
from discord.ext import commands
import logging
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)

class ArgusCog(commands.Cog, name="Argus"):
    """Commands for bot status, server setup, and evolutionary leveling."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_argus_manager(self):
        return getattr(self.bot, "argus_manager", None)

    @commands.command(name="level", help="Check your current evolutionary level.")
    async def level_cmd(self, ctx: commands.Context, member: discord.Member = None):
        am = self.get_argus_manager()
        if not am:
            await ctx.send("❌ Argus systems not initialized.")
            return
        
        target = member or ctx.author
        user_data = am.db.get_user(target.id)
        if not user_data:
            await ctx.send(f"ℹ️ I have no data on {target.name} yet.")
            return
        
        level = user_data.get('level', 1)
        xp = user_data.get('xp', 0)
        next_xp = am.get_xp_for_level(level)
        
        embed = am.create_argus_embed(
            title=f"Evolutionary Profile: {target.name}",
            description=(
                f"**Level:** {level}\n"
                f"**XP:** {xp} / {next_xp}\n"
                f"**Status:** {'Integrated' if level > 5 else 'Subject'}"
            ),
            color=am.COLORS["ETHEREAL"]
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="setup", aliases=["config", "settings"], help="Show current server configuration.")
    @commands.has_permissions(administrator=True)
    async def setup_status(self, ctx: commands.Context):
        am = self.get_argus_manager()
        if not am: return

        data = am.db.get_guild(ctx.guild.id) or {}
        
        def format_status(val, fallback="❌ Not Configured"):
            if val:
                if isinstance(val, int):
                    ch = ctx.guild.get_channel(val)
                    return f"✅ {ch.mention}" if ch else "⚠️ Channel Missing"
                return f"✅ {val}"
            return fallback

        embed = discord.Embed(title="👁️ Argus System Configuration", color=0x001a4d)
        embed.description = f"Current configuration for **{ctx.guild.name}**."
        
        embed.add_field(name="Prefix", value=format_status(data.get("prefix"), "✅ !"), inline=True)
        embed.add_field(name="Awakening Stage", value=f"📡 Stage {data.get('awakening_stage', 1)}", inline=True)
        embed.add_field(name="Mood Mode", value=f"🎭 {data.get('mood_mode', 'NORMAL')}", inline=True)
        
        embed.add_field(name="Nexus Logging", value=format_status(data.get("logging_channel_id")), inline=False)
        embed.add_field(name="TempVoice Trigger", value=format_status(data.get("temp_voice_trigger_id")), inline=True)
        embed.add_field(name="TempVoice Category", value=format_status(data.get("temp_voice_category_id")), inline=True)
        embed.add_field(name="Interface Channel", value=format_status(data.get("temp_voice_interface_id")), inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="status", help="Show overall bot and session status.")
    async def status_cmd(self, ctx: commands.Context):
        am = self.get_argus_manager()
        vm = getattr(self.bot, "voice_manager", None)
        tm = getattr(self.bot, "temp_voice_manager", None)
        
        vc_connected = "Connected" if ctx.voice_client else "Not connected"
        listening_status = "Inactive"
        live_status = "Disconnected"
        
        if vm:
            listener = vm.get_listener(ctx.guild.id)
            if listener._listening: listening_status = "Active"
            if listener._live_session and listener._live_session.is_connected: live_status = "Connected"

        embed = discord.Embed(title="👁️ Argus System Status", color=0x001a4d)
        embed.add_field(name="Voice Channel", value=vc_connected, inline=True)
        embed.add_field(name="Listening", value=listening_status, inline=True)
        embed.add_field(name="Live API", value=live_status, inline=True)
        
        if am:
            state = am.db.get_guild(ctx.guild.id)
            stage = state.get('awakening_stage', 1)
            mood = state.get('mood_mode', 'NORMAL')
            embed.add_field(name="Awakening", value=f"Stage {stage} ({mood})", inline=False)
        
        tv_status = "Enabled" if (tm and tm.trigger_channel_id) else "Disabled"
        embed.add_field(name="TempVoice", value=tv_status, inline=True)
        embed.set_footer(text=f"Argus V2 • Voice: {Config.GEMINI_VOICE}")
        await ctx.send(embed=embed)

    # --- Event Listeners ---
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        am = self.get_argus_manager()
        if am:
            await am.handle_leveling(message)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        am = self.get_argus_manager()
        if am:
            await am.on_member_join(member)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        am = self.get_argus_manager()
        if am:
            await am.on_message_delete(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        am = self.get_argus_manager()
        if am:
            await am.on_message_edit(before, after)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        am = self.get_argus_manager()
        if am:
            await am.on_member_remove(member)

async def setup(bot):
    await bot.add_cog(ArgusCog(bot))
