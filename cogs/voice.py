"""
Voice Cog — handles AI voice conversation, listening, and VC management.
Modularized from the original monolithic bot.py.
"""

import discord
from discord.ext import commands
import logging
import asyncio
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
                await ctx.send("❌ You don't have permission for voice commands.")
                return

        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ Join a voice channel first!")
            return

        channel = ctx.author.voice.channel
        if not voice_recv:
            await ctx.send("❌ Voice support not available.")
            return

        try:
            if ctx.voice_client:
                await ctx.voice_client.move_to(channel)
            else:
                await channel.connect(cls=voice_recv.VoiceRecvClient)
            
            await ctx.send(f"✅ Joined **{channel.name}**")
        except Exception as e:
            await ctx.send(f"❌ Connection failed: {e}")

    @commands.command(name="listen", help="Start the AI voice listener.")
    async def listen_command(self, ctx: commands.Context):
        vm = self.get_voice_manager()
        if not vm or not ctx.voice_client:
            await ctx.send("❌ Connect me to a voice channel first.")
            return

        listener = vm.get_listener(ctx.guild.id)
        await ctx.send("🔄 Connecting to Gemini Live API...")
        
        try:
            await listener.start_listening(voice_client=ctx.voice_client, log_channel=ctx.channel)
            embed = discord.Embed(
                title="🎙️ AI Voice Active",
                description="I'm listening! Talk to me naturally.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @commands.command(name="stop", help="Stop the AI voice listener.")
    async def stop_listening(self, ctx: commands.Context):
        vm = self.get_voice_manager()
        if not vm: return
        listener = vm.get_listener(ctx.guild.id)
        await listener.stop_listening()
        await ctx.send("🔇 Stopped listening.")

    @commands.command(name="leave", help="Leave the voice channel.")
    async def leave_command(self, ctx: commands.Context):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Disconnected.")
        else:
            await ctx.send("❌ I'm not in a voice channel.")

async def setup(bot):
    await bot.add_cog(VoiceCog(bot))
