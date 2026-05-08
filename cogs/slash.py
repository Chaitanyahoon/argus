"""
Slash Commands Cog — /command versions of all major Argus features.
All commands here use discord.app_commands so they show up in the / menu.
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging
import datetime
from typing import Optional

try:
    import discord.ext.voice_recv as voice_recv
except ImportError:
    voice_recv = None

import core.embeds as E
from config import Config

logger = logging.getLogger(__name__)


class SlashCog(commands.Cog, name="Slash"):
    """Slash (/) command interface for Argus features."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _am(self):
        return getattr(self.bot, "argus_manager", None)

    def _vm(self):
        return getattr(self.bot, "voice_manager", None)

    def _wellness(self):
        return getattr(self.bot, "wellness_manager", None)

    # ── General ──────────────────────────────────────────────────────────────

    @app_commands.command(name="help", description="Show all available Argus commands.")
    async def slash_help(self, interaction: discord.Interaction):
        prefix = Config.COMMAND_PREFIX
        embed = discord.Embed(
            title="👁️ Argus — Command Reference",
            description=f"Prefix: `{prefix}` · Or use `/` slash commands directly.",
            color=0x5865F2
        )
        embed.add_field(name="🎙️ Voice AI", value=(
            f"`{prefix}join` — Join voice channel\n"
            f"`{prefix}listen` — Start AI listener\n"
            f"`{prefix}stop` — Stop AI listener\n"
            f"`{prefix}leave` — Leave voice channel"
        ), inline=False)
        embed.add_field(name="🎵 Music", value=(
            "Music playback features have been disabled in this deployment to reduce hosting costs."
        ), inline=False)
        embed.add_field(name="🌿 Wellness", value=(
            f"`{prefix}checkin` — Mood check-in\n"
            f"`{prefix}journal` — Private journal\n"
            f"`{prefix}breathe` — Breathing exercise\n"
            f"`{prefix}ground` — Grounding technique\n"
            f"`{prefix}moodstats` — Your wellness stats"
        ), inline=False)
        embed.add_field(name="📊 Stats & Levels", value=(
            f"`{prefix}level` — Your evolutionary level\n"
            f"`{prefix}leaderboard` — Server rankings\n"
            f"`{prefix}stats` — Bot statistics"
        ), inline=False)
        embed.add_field(name="⚙️ Admin", value=(
            f"`{prefix}setprefix <p>` — Change prefix\n"
            f"`{prefix}setup` — Server configuration\n"
            f"`{prefix}status` — System status"
        ), inline=False)
        embed.set_footer(text="Argus Evolutionary Systems · Slash commands also available via /")
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="status", description="Show Argus system status.")
    async def slash_status(self, interaction: discord.Interaction):
        am = self._am()
        vm = self._vm()

        vc_status = "🟢 Connected" if interaction.guild and interaction.guild.voice_client else "⚫ Not Connected"
        listen_s = "⚫ Inactive"
        live_s = "⚫ Disconnected"

        if vm and interaction.guild:
            listener = vm.get_listener(interaction.guild.id)
            if getattr(listener, "_listening", False):
                listen_s = "🟢 Active"
            if getattr(listener, "_live_session", None) and listener._live_session.is_connected:
                live_s = "🟢 Connected"

        embed = discord.Embed(title="👁️ Argus System Status", color=0x5865F2)
        embed.add_field(name="🔊 Voice Channel", value=vc_status, inline=True)
        embed.add_field(name="🎙️ Listening", value=listen_s, inline=True)
        embed.add_field(name="⚡ Gemini Live", value=live_s, inline=True)
        embed.add_field(name="📡 Gateway Latency", value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)
        embed.add_field(name="🏠 Guilds", value=f"`{len(self.bot.guilds)}`", inline=True)
        if am and interaction.guild:
            state = am.db.get_guild(interaction.guild.id) or {}
            embed.add_field(
                name="🌀 Awakening",
                value=f"Stage {state.get('awakening_stage', 1)} · {state.get('mood_mode', 'NORMAL')}",
                inline=False,
            )
        await interaction.response.send_message(embed=embed)

    # ── Voice ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="join", description="Join your voice channel.")
    async def slash_join(self, interaction: discord.Interaction):
        member = interaction.user
        if not isinstance(member, discord.Member) or not member.voice or not member.voice.channel:
            await interaction.response.send_message(
                embed=E.error("Voice Required", "You must be in a voice channel first.", None),
                ephemeral=True
            )
            return
        
        if not voice_recv:
            await interaction.response.send_message(
                embed=E.error("Unavailable", "Voice support is not installed on this bot.", None),
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        channel = member.voice.channel
        try:
            # Connect to voice with VoiceRecvClient support
            if interaction.guild.voice_client:
                # If already connected, try to move to new channel
                vc = interaction.guild.voice_client
                if not isinstance(vc, voice_recv.VoiceRecvClient):
                    # Wrong type, disconnect and reconnect
                    await vc.disconnect()
                    await asyncio.sleep(0.5)
                    await channel.connect(cls=voice_recv.VoiceRecvClient)
                else:
                    # Correct type, just move
                    await vc.move_to(channel)
            else:
                # Not connected, create new connection with correct type
                await channel.connect(cls=voice_recv.VoiceRecvClient)
            
            await interaction.followup.send(
                embed=E.success("📡 Connected", f"Joined **{channel.name}**", None)
            )
        except Exception as e:
            await interaction.followup.send(
                embed=E.error("Connection Failed", str(e), None),
                ephemeral=True
            )

    @app_commands.command(name="leave", description="Leave the voice channel.")
    async def slash_leave(self, interaction: discord.Interaction):
        if not interaction.guild.voice_client:
            await interaction.response.send_message(
                embed=E.error("Not Connected", "I'm not in a voice channel.", None), ephemeral=True
            )
            return
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message(
            embed=E.warning("Disconnected", "Left the voice channel.", None)
        )

    @app_commands.command(name="listen", description="Start the AI voice listener.")
    async def slash_listen(self, interaction: discord.Interaction):
        vm = self._vm()
        if not vm:
            await interaction.response.send_message("❌ Voice system not ready.", ephemeral=True)
            return
        if not interaction.guild.voice_client:
            await interaction.response.send_message(
                embed=E.error("Not Connected", f"Use `/join` first.", None), ephemeral=True
            )
            return
        
        # Verify the voice client is a VoiceRecvClient
        if not hasattr(interaction.guild.voice_client, 'listen'):
            await interaction.response.send_message(
                embed=E.error("Wrong Client Type", "Voice client doesn't support listening. Please run `/join` again.", None), ephemeral=True
            )
            return
        
        await interaction.response.defer()
        try:
            listener = vm.get_listener(interaction.guild.id)
            await listener.start_listening(voice_client=interaction.guild.voice_client, log_channel=interaction.channel)
            embed = discord.Embed(title="🎙️ AI Voice Active", description="I'm listening! Talk to me naturally.", color=discord.Color.green())
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=E.error("Error", str(e), None))

    @app_commands.command(name="stop", description="Stop the AI voice listener.")
    async def slash_stop(self, interaction: discord.Interaction):
        vm = self._vm()
        if not vm:
            await interaction.response.send_message("❌ Voice system not ready.", ephemeral=True)
            return
        await interaction.response.defer()
        try:
            listener = vm.get_listener(interaction.guild.id)
            await listener.stop_listening()
            await interaction.followup.send(embed=discord.Embed(title="🛑 AI Voice Stopped", description="I've stopped listening.", color=discord.Color.orange()))
        except Exception as e:
            await interaction.followup.send(embed=E.error("Error", str(e), None))

    # ── Wellness ──────────────────────────────────────────────────────────────

    @app_commands.command(name="checkin", description="Quick mood check-in.")
    @app_commands.describe(mood="Your mood from 1 (struggling) to 5 (great)")
    @app_commands.choices(mood=[
        app_commands.Choice(name="5 — Great 🌟", value=1),
        app_commands.Choice(name="4 — Good 😊", value=2),
        app_commands.Choice(name="3 — Okay / Neutral 😐", value=3),
        app_commands.Choice(name="2 — Not so good 😔", value=4),
        app_commands.Choice(name="1 — Struggling 💙", value=5),
    ])
    async def slash_checkin(self, interaction: discord.Interaction, mood: app_commands.Choice[int]):
        wellness = self._wellness()
        if not wellness:
            await interaction.response.send_message("❌ Wellness system not ready.", ephemeral=True)
            return
        streak = wellness.log_mood(interaction.user.id, mood.value)
        responses = {
            1: ("That's wonderful! I'm glad you're having a great day. 🌟", 0x57F287),
            2: ("Glad to hear you're doing well. 😊", 0x57F287),
            3: ("Stay steady. I'm here if you need to talk. 😐", 0x5865F2),
            4: ("I'm sorry you're not feeling great. Try `/breathe` for a quick reset. 💙", 0xFEE75C),
            5: ("I'm here for you. You don't have to carry this alone. 💙", 0xED4245),
        }
        text, color = responses[mood.value]
        embed = discord.Embed(
            title="✅ Check-in Recorded",
            description=f"{text}\n\n🔥 Streak: **{streak} days**",
            color=color
        )
        if mood.value == 5:
            await wellness.handle_crisis(interaction)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="breathe", description="Start a guided 4-7-8 breathing exercise.")
    async def slash_breathe(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🫁 Deep Breathing",
                description="Let's take a moment. Starting a 4-7-8 breathing cycle...",
                color=0x5865F2
            )
        )
        steps = [
            ("🌬️ Inhale deeply...", 4, 0x5865F2),
            ("✋ Hold your breath...", 7, 0x9B59B6),
            ("💨 Exhale slowly...", 8, 0x57F287),
        ]
        msg = await interaction.original_response()
        for _ in range(2):
            for text, duration, color in steps:
                for i in range(duration, 0, -1):
                    bar = "█" * i + "░" * (duration - i)
                    embed = discord.Embed(
                        title="🫁 Deep Breathing",
                        description=f"**{text}**\n`{bar}` {i}s",
                        color=color
                    )
                    await msg.edit(embed=embed)
                    await asyncio.sleep(1)
        await msg.edit(embed=discord.Embed(
            title="✅ Exercise Complete",
            description="Hope you're feeling a bit more grounded. 🌿",
            color=0x57F287
        ))

    @app_commands.command(name="moodstats", description="View your mood and wellness overview.")
    async def slash_moodstats(self, interaction: discord.Interaction):
        wellness = self._wellness()
        if not wellness:
            await interaction.response.send_message("❌ Wellness system not ready.", ephemeral=True)
            return
        stats = wellness.get_mood_stats(interaction.user.id)
        if not stats or stats.get('count', 0) == 0:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="📊 No Data Yet",
                    description="Do your first `/checkin` to start tracking!",
                    color=0x5865F2
                ),
                ephemeral=True
            )
            return
        avg = stats['avg']
        bar = "█" * round(avg * 2) + "░" * (10 - round(avg * 2))
        embed = discord.Embed(title="📊 Wellness Overview", color=0x5865F2)
        embed.add_field(name="Average Mood", value=f"`{bar}` {avg:.1f}/5", inline=True)
        embed.add_field(name="🔥 Streak", value=f"**{stats['streak']} days**", inline=True)
        embed.add_field(name="📅 Entries", value=f"**{stats['count']}** (Last 7 days)", inline=True)
        if stats.get('latest'):
            latest = stats['latest']
            dt_obj = datetime.datetime.fromisoformat(latest['timestamp'])
            embed.add_field(name="Latest Entry", value=f"Score `{latest['mood_score']}` on {dt_obj.strftime('%b %d')}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── Music ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="play", description="Play a song or Spotify/YouTube URL.")
    @app_commands.describe(query="Song name or URL")
    async def slash_play(self, interaction: discord.Interaction, query: str):
        # Delegate to the prefix command via Context trick
        ctx = await self.bot.get_context(interaction)
        music_cog = self.bot.cogs.get("Music")
        if not music_cog:
            await interaction.response.send_message("❌ Music system not available.", ephemeral=True)
            return
        await interaction.response.defer()
        try:
            await music_cog.play_music_cmd(ctx, query=query)
        except Exception as e:
            await interaction.followup.send(f"❌ {e}", ephemeral=True)

    @app_commands.command(name="skip", description="Skip the current track.")
    async def slash_skip(self, interaction: discord.Interaction):
        ctx = await self.bot.get_context(interaction)
        music_cog = self.bot.cogs.get("Music")
        if not music_cog:
            await interaction.response.send_message("❌ Music system not available.", ephemeral=True)
            return
        await interaction.response.defer()
        await music_cog.skip_music(ctx)

    @app_commands.command(name="queue", description="Show the current music queue.")
    async def slash_queue(self, interaction: discord.Interaction):
        ctx = await self.bot.get_context(interaction)
        music_cog = self.bot.cogs.get("Music")
        if not music_cog:
            await interaction.response.send_message("❌ Music system not available.", ephemeral=True)
            return
        await interaction.response.defer()
        await music_cog.show_queue(ctx)

    # ── Admin ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="setprefix", description="Change the bot command prefix for this server.")
    @app_commands.describe(prefix="New prefix (max 5 characters)")
    @app_commands.default_permissions(administrator=True)
    async def slash_setprefix(self, interaction: discord.Interaction, prefix: str):
        am = self._am()
        if not am:
            await interaction.response.send_message("❌ System not ready.", ephemeral=True)
            return
        if len(prefix) > 5:
            await interaction.response.send_message("❌ Prefix must be 5 characters or fewer.", ephemeral=True)
            return
        am.db.update_guild(interaction.guild.id, prefix=prefix)
        embed = discord.Embed(
            title="✅ Prefix Updated",
            description=f"Command prefix is now `{prefix}`\nExample: `{prefix}help`",
            color=0x57F287
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="level", description="Check your evolutionary level.")
    async def slash_level(self, interaction: discord.Interaction):
        am = self._am()
        if not am:
            await interaction.response.send_message("❌ System not ready.", ephemeral=True)
            return
        user_data = am.db.get_user(interaction.user.id)
        if not user_data:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="No Data Yet",
                    description="Start chatting to begin your evolutionary journey!",
                    color=0x5865F2
                ),
                ephemeral=True
            )
            return
        level = user_data.get("level", 1)
        xp = user_data.get("xp", 0)
        next_xp = am.get_xp_for_level(level)
        pct = min(100, round((xp / next_xp) * 100)) if next_xp else 0
        bar = "█" * round(pct / 5) + "░" * (20 - round(pct / 5))
        embed = discord.Embed(
            title=f"🧬 {interaction.user.display_name} — Level {level}",
            color=0x5865F2
        )
        embed.add_field(name="XP Progress", value=f"`{bar}` {xp}/{next_xp} ({pct}%)", inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(SlashCog(bot))
