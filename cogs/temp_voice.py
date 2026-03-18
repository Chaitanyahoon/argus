"""
TempVoice Cog — handles temporary voice channel creation and management.
Modularized from the original monolithic bot.py.
"""

import discord
from discord.ext import commands
import logging
from typing import cast, Optional
from config import Config

logger = logging.getLogger(__name__)

class TempVoiceCog(commands.Cog, name="TempVoice"):
    """Commands for setting up and managing temporary voice channels."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_temp_voice_manager(self):
        return getattr(self.bot, "temp_voice_manager", None)

    def get_argus_manager(self):
        return getattr(self.bot, "argus_manager", None)

    @commands.command(name="setcreatechannel", help="Set the channel that triggers temp VC creation.")
    @commands.has_permissions(administrator=True)
    async def set_create_channel(self, ctx: commands.Context, channel: discord.VoiceChannel):
        am = self.get_argus_manager()
        if not am: return
        am.db.set_guild(ctx.guild.id, temp_voice_trigger_id=channel.id)
        await ctx.send(f"✅ Users joining **{channel.name}** will now get a temp VC.")

    @commands.command(name="settempvcategory", help="Set the category for temp VCs.")
    @commands.has_permissions(administrator=True)
    async def set_temp_vc_category(self, ctx: commands.Context, category: discord.CategoryChannel):
        am = self.get_argus_manager()
        if not am: return
        am.db.set_guild(ctx.guild.id, temp_voice_category_id=category.id)
        await ctx.send(f"✅ Temp VCs will now be created in **{category.name}**.")

    @commands.command(name="setinterfacechannel", help="Set the channel for the management interface.")
    @commands.has_permissions(administrator=True)
    async def set_interface_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        am = self.get_argus_manager()
        if not am: return
        am.db.set_guild(ctx.guild.id, temp_voice_interface_id=channel.id)
        await ctx.send(f"✅ Temp VC management interface set to {channel.mention}.")

    @commands.command(name="postvcinterface", help="Post the shared TempVoice management interface.")
    @commands.has_permissions(administrator=True)
    async def post_vc_interface(self, ctx: commands.Context):
        tm = self.get_temp_voice_manager()
        if not tm:
            await ctx.send("❌ TempVoice not initialized.")
            return
        
        from core.temp_voice_ui import SharedTempVoiceView
        embed = discord.Embed(
            title="TempVoice Interface",
            description="Use the buttons below to manage **your** temporary voice channel.",
            color=0x001a4d,
        )
        embed.set_footer(text="Join the Create VC channel first to get your own channel.")
        view = SharedTempVoiceView(tm, timeout=None)
        await ctx.send(embed=embed, view=view)
        await ctx.send("✅ Interface posted.")

    # --- Event Listeners ---
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Create temp VC when user joins the Create VC channel; cleanup when temp channel is empty."""
        tm = self.get_temp_voice_manager()
        am = self.get_argus_manager()
        
        if tm is not None and am is not None:
            guild_data = am.db.get_guild(member.guild.id)
            if not guild_data:
                return
                
            trigger_id = guild_data.get('temp_voice_trigger_id')
            
            if after.channel and after.channel.id == trigger_id:
                await tm.create_temp_channel(member)
                return
            if before.channel and before.channel.id in tm.temp_channels:
                await tm.check_cleanup(before.channel)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle TempVoice button interactions (works after bot restart)."""
        if interaction.type != discord.InteractionType.component:
            return
        inter_data = getattr(interaction, "data", None)
        cid = str(inter_data.get("custom_id")) if isinstance(inter_data, dict) else None
        if not cid:
            return
            
        tm = self.get_temp_voice_manager()
        if tm is None:
            return

        from core.temp_voice_ui import TempVoiceView

        # Shared interface channel: resolve VC by owner, then run action
        if cid.startswith("tempvoice_shared:"):
            parts = cid.split(":")
            if len(parts) < 2:
                return
            action = parts[1]
            channel_id = tm.get_owned_channel_id(interaction.user.id)
            if channel_id is None:
                await interaction.response.send_message(
                    "You don't have a temp VC. Join the **Create VC** channel to create one.",
                    ephemeral=True,
                )
                return
            channel = interaction.guild.get_channel(channel_id)
            if channel is None or not isinstance(channel, discord.VoiceChannel):
                await interaction.response.send_message("Your temp VC no longer exists.", ephemeral=True)
                return
            await TempVoiceView._execute_action(tm, interaction, channel, action)
            return

        if not cid.startswith("tempvoice:"):
            return
        parts = cid.split(":")
        if len(parts) < 3:
            return
        action, channel_id_s = parts[1], parts[2]
        try:
            channel_id = int(channel_id_s)
        except ValueError:
            return
        channel = interaction.guild.get_channel(channel_id)
        if channel is None:
            try:
                channel = await interaction.guild.fetch_channel(channel_id)
            except (discord.NotFound, discord.HTTPException):
                await interaction.response.send_message("Channel not found.", ephemeral=True)
                return
        if not isinstance(channel, discord.VoiceChannel):
            await interaction.response.send_message("Channel not found.", ephemeral=True)
            return
        await TempVoiceView._execute_action(tm, interaction, channel, action)

async def setup(bot):
    await bot.add_cog(TempVoiceCog(bot))
