"""
Voice Cog — AI voice conversation, listening, and VC management.
"""

import discord
from discord.ext import commands
import logging
import core.embeds as E
from config import Config

try:
    import discord.ext.voice_recv as voice_recv
except ImportError:
    voice_recv = None

logger = logging.getLogger(__name__)


class VoiceCog(commands.Cog, name="Voice"):
    """Commands for AI voice interaction and voice channel management."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_voice_manager(self):
        return getattr(self.bot, "voice_manager", None)

    def get_permission_manager(self):
        return getattr(self.bot, "permission_manager", None)

    @commands.command(name="join", help="Join your current voice channel.")
    async def join_command(self, ctx: commands.Context):
        pm = self.get_permission_manager()
        if pm:
            perms = pm._load_permissions(ctx.guild.id)
            if not pm.can_use_command(ctx.author, perms.voice_command_level):
                await ctx.send(embed=E.error("Permission Denied", "You don't have permission for voice commands.", ctx))
                return

        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send(embed=E.error("Voice Required", "Join a voice channel first.", ctx))
            return

        if not voice_recv:
            await ctx.send(embed=E.error("Unavailable", "Voice support is not installed on this bot.", ctx))
            return

        channel = ctx.author.voice.channel
        try:
            if ctx.voice_client:
                await ctx.voice_client.move_to(channel)
            else:
                await channel.connect(cls=voice_recv.VoiceRecvClient)
            await ctx.send(embed=E.success("📡 Connected", f"Joined **{channel.name}**.", ctx))
        except Exception as e:
            await ctx.send(embed=E.error("Connection Failed", str(e), ctx))

    @commands.command(name="listen", help="Start the AI voice listener.")
    async def listen_command(self, ctx: commands.Context):
        vm = self.get_voice_manager()
        if not vm or not ctx.voice_client:
            await ctx.send(embed=E.error("Not Connected", "Connect me to a voice channel first with `!join`.", ctx))
            return

        listener = vm.get_listener(ctx.guild.id)
        status_msg = await ctx.send(embed=E.info("🔄 Connecting", "Connecting to Gemini Live API…", ctx))

        try:
            await listener.start_listening(voice_client=ctx.voice_client, log_channel=ctx.channel)
            embed = E.success("🎙️ AI Voice Active", "I'm listening! Talk to me naturally.", ctx)
            embed.add_field(name="Model",  value=f"`{Config.GEMINI_VOICE}`", inline=True)
            embed.add_field(name="Status", value="🟢 Live",                   inline=True)
            await status_msg.edit(embed=embed)
        except Exception as e:
            await status_msg.edit(embed=E.error("Connection Failed", str(e), ctx))

    @commands.command(name="stop", help="Stop the AI voice listener.")
    async def stop_listening(self, ctx: commands.Context):
        vm = self.get_voice_manager()
        if not vm:
            return
        listener = vm.get_listener(ctx.guild.id)
        await listener.stop_listening()
        await ctx.send(embed=E.warning("🔇 AI Voice Stopped", "The voice listener has been deactivated.", ctx))

    @commands.command(name="leave", help="Leave the voice channel.")
    async def leave_command(self, ctx: commands.Context):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send(embed=E.warning("📡 Disconnected", "Left the voice channel.", ctx))
        else:
            await ctx.send(embed=E.error("Not Connected", "I'm not in a voice channel.", ctx))


async def setup(bot):
    await bot.add_cog(VoiceCog(bot))
