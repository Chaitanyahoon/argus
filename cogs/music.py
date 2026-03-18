"""
Music Cog — handles all music-related commands for the bot.
Delegates playback to MusicManager / MusicPlayer from core.music_player.
"""

import discord
from discord.ext import commands
import logging
from typing import Optional, List

from core.music_player import MusicManager, MusicPlayer, resolve_tracks, Track

logger = logging.getLogger(__name__)


class MusicCog(commands.Cog, name="Music"):
    """Commands for playing and managing music playback."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --------------------------------------------------------------------- helpers
    def _get_mm(self) -> Optional[MusicManager]:
        return getattr(self.bot, "music_manager", None)

    async def _ensure_voice(self, ctx: commands.Context) -> bool:
        """Connect the bot if not already in VC. Returns True on success."""
        if ctx.voice_client:
            return True
        if ctx.author.voice and ctx.author.voice.channel:  # type: ignore[union-attr]
            await ctx.author.voice.channel.connect()  # type: ignore[union-attr]
            return True
        await ctx.send("❌ You need to be in a voice channel first.")
        return False

    # --------------------------------------------------------------------- commands
    @commands.command(name="join", help="Join your current voice channel.")
    async def join_vc(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:  # type: ignore[union-attr]
            await ctx.send(embed=discord.Embed(
                title="❌ Error", description="You must be in a voice channel.",
                color=discord.Color.red()))
            return

        channel = ctx.author.voice.channel  # type: ignore[union-attr]
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()

        await ctx.send(embed=discord.Embed(
            title="📡 Connected", description=f"Joined **{channel.name}**",
            color=discord.Color.green()))

    @commands.command(name="leave", help="Disconnect from the voice channel.")
    async def leave_vc(self, ctx: commands.Context):
        if not ctx.voice_client:
            await ctx.send(embed=discord.Embed(
                title="❌ Error", description="I'm not in a voice channel.",
                color=discord.Color.red()))
            return
        await ctx.voice_client.disconnect()
        await ctx.send(embed=discord.Embed(
            title="📡 Disconnected", description="Left the voice channel.",
            color=discord.Color.orange()))

    @commands.command(name="play", help="Search and play music from YouTube or Spotify.")
    async def play_music_cmd(self, ctx: commands.Context, *, query: str):
        mm = self._get_mm()
        if not mm:
            await ctx.send("❌ Music system not ready.")
            return
        if not await self._ensure_voice(ctx):
            return

        # Resolve tracks (blocking I/O done in thread by resolve_tracks)
        tracks = await resolve_tracks(query, ctx.author)  # type: ignore[arg-type]
        if not tracks:
            await ctx.send(f"❌ No tracks found for: `{query}`")
            return

        player: MusicPlayer = mm.get_player_for_vc(ctx.voice_client)  # type: ignore[arg-type]

        if len(tracks) == 1:
            await player.play(tracks[0])
            await ctx.send(f"✅ Now playing **{tracks[0].title}**.")
        else:
            started = await player.enqueue_many(tracks)
            msg = f"✅ Added **{len(tracks)}** tracks to the queue."
            if started:
                msg += f"\n▶️ Started playing **{started.title}**."
            await ctx.send(msg)

    @commands.command(name="skip", help="Skip the current track.")
    async def skip_music_cmd(self, ctx: commands.Context):
        mm = self._get_mm()
        if not mm or not ctx.voice_client:
            return
        player = mm.get_player(ctx.guild.id)  # type: ignore[union-attr]
        await player.skip()
        await ctx.send("⏭️ Skipped.")

    @commands.command(name="stop", help="Stop playback and clear the queue.")
    async def stop_music_cmd(self, ctx: commands.Context):
        mm = self._get_mm()
        if not mm or not ctx.voice_client:
            return
        player = mm.get_player(ctx.guild.id)  # type: ignore[union-attr]
        await player.stop()
        await ctx.send("🛑 Stopped and cleared the queue.")

    @commands.command(name="queue", aliases=["q"], help="Show the current music queue.")
    async def queue_music_cmd(self, ctx: commands.Context):
        mm = self._get_mm()
        if not mm:
            return
        player = mm.get_player(ctx.guild.id)  # type: ignore[union-attr]
        q = player.queue

        lines: List[str] = []
        if player.current:
            lines.append(f"▶️ **Now Playing:** {player.current.title}")
        if q:
            for i, t in enumerate(q[:10], 1):
                lines.append(f"{i}. {t.title} — requested by {t.requested_by_name}")
            if len(q) > 10:
                lines.append(f"… and {len(q) - 10} more.")
        else:
            lines.append("The queue is empty.")

        embed = discord.Embed(title="🎵 Music Queue",
                              description="\n".join(lines), color=0x001a4d)
        await ctx.send(embed=embed)

    @commands.command(name="nowplaying", aliases=["np"], help="Show the current track.")
    async def nowplaying_music_cmd(self, ctx: commands.Context):
        mm = self._get_mm()
        if not mm:
            return
        player = mm.get_player(ctx.guild.id)  # type: ignore[union-attr]
        current = player.current
        if not current:
            await ctx.send("🔇 Nothing is playing right now.")
            return

        duration_str = f" ({current.duration}s)" if current.duration else ""
        embed = discord.Embed(
            title="▶️ Now Playing",
            description=(
                f"**{current.title}**{duration_str}\n\n"
                f"*Requested by {current.requested_by_name}*"
            ),
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
