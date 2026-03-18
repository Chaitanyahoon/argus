"""
Music Cog — handles all music-related commands for the bot.
Delegates playback to MusicManager / MusicPlayer from core.music_player.

Commands:
  Playback:  !play, !skip, !stop, !pause, !resume
  Info:      !queue (!q), !nowplaying (!np)
  Controls:  !loop, !shuffle, !volume (!vol), !remove
  Playlists: !playlist save/play/list/delete
"""

import discord
from discord.ext import commands
import logging
from typing import Optional, List

from core.music_player import (
    MusicManager, MusicPlayer, resolve_tracks, Track,
    LOOP_NONE, LOOP_TRACK, LOOP_QUEUE,
    db_save_playlist, db_load_playlist, db_list_playlists, db_delete_playlist,
)

logger = logging.getLogger(__name__)

# ── Colour palette ─────────────────────────────────────────────────────────────
_BLUE   = 0x0066ff
_GREEN  = 0x00ff88
_RED    = 0xff3355
_PURPLE = 0x6600ff
_GOLD   = 0xffba00


def _fmt_dur(seconds: int | None) -> str:
    if not seconds:
        return ""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f" [{h}:{m:02d}:{s:02d}]" if h else f" [{m}:{s:02d}]"


class MusicCog(commands.Cog, name="Music"):
    """Commands for playing and managing music playback."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ─────────────────────────────────────────── helpers
    def _get_mm(self) -> Optional[MusicManager]:
        return getattr(self.bot, "music_manager", None)

    def _get_player(self, ctx: commands.Context) -> Optional[MusicPlayer]:
        mm = self._get_mm()
        if not mm or not ctx.guild:
            return None
        return mm.get_player(ctx.guild.id)

    async def _ensure_voice(self, ctx: commands.Context) -> bool:
        if ctx.voice_client:
            return True
        if ctx.author.voice and ctx.author.voice.channel:   # type: ignore[union-attr]
            await ctx.author.voice.channel.connect()         # type: ignore[union-attr]
            return True
        await ctx.send(embed=discord.Embed(
            title="❌ Voice Required",
            description="Join a voice channel first.",
            color=_RED,
        ))
        return False

    # ─────────────────────────────────────────── join / leave
    @commands.command(name="join", help="Join your current voice channel.")
    async def join_vc(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:  # type: ignore[union-attr]
            await ctx.send(embed=discord.Embed(title="❌ Error", description="You must be in a voice channel.", color=_RED))
            return
        channel = ctx.author.voice.channel  # type: ignore[union-attr]
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send(embed=discord.Embed(title="📡 Connected", description=f"Joined **{channel.name}**", color=_GREEN))

    @commands.command(name="leave", help="Disconnect from the voice channel.")
    async def leave_vc(self, ctx: commands.Context):
        if not ctx.voice_client:
            await ctx.send(embed=discord.Embed(title="❌ Error", description="I'm not in a voice channel.", color=_RED))
            return
        await ctx.voice_client.disconnect()
        await ctx.send(embed=discord.Embed(title="📡 Disconnected", description="Left the voice channel.", color=_GOLD))

    # ─────────────────────────────────────────── play / skip / stop / pause / resume
    @commands.command(name="play", aliases=["p"], help="Play a song or Spotify/YouTube URL.")
    async def play_music_cmd(self, ctx: commands.Context, *, query: str):
        mm = self._get_mm()
        if not mm:
            await ctx.send("❌ Music system not ready.")
            return
        if not await self._ensure_voice(ctx):
            return

        async with ctx.typing():
            tracks = await resolve_tracks(query, ctx.author)  # type: ignore[arg-type]

        if not tracks:
            await ctx.send(embed=discord.Embed(title="❌ Not Found", description=f"No tracks found for `{query}`", color=_RED))
            return

        player: MusicPlayer = mm.get_player_for_vc(ctx.voice_client)  # type: ignore[arg-type]

        if len(tracks) == 1:
            t = tracks[0]
            await player.play(t)
            embed = discord.Embed(title="▶️ Now Playing", description=f"**{t.title}**{_fmt_dur(t.duration)}", color=_GREEN)
            embed.set_footer(text=f"Requested by {t.requested_by_name}")
            await ctx.send(embed=embed)
        else:
            started = await player.enqueue_many(tracks)
            desc = f"Added **{len(tracks)}** tracks to the queue."
            if started:
                desc += f"\n▶️ Started: **{started.title}**"
            await ctx.send(embed=discord.Embed(title="🎵 Playlist Queued", description=desc, color=_BLUE))

    @commands.command(name="skip", aliases=["s"], help="Skip the current track.")
    async def skip_music_cmd(self, ctx: commands.Context):
        player = self._get_player(ctx)
        if not player or not ctx.voice_client:
            return
        current = player.current
        await player.skip()
        desc = f"Skipped **{current.title}**" if current else "Skipped."
        if player.current:
            desc += f"\n▶️ Now playing: **{player.current.title}**"
        await ctx.send(embed=discord.Embed(title="⏭️ Skipped", description=desc, color=_GOLD))

    @commands.command(name="stop", help="Stop playback and clear the queue.")
    async def stop_music_cmd(self, ctx: commands.Context):
        player = self._get_player(ctx)
        if not player or not ctx.voice_client:
            return
        await player.stop()
        await ctx.send(embed=discord.Embed(title="🛑 Stopped", description="Playback stopped and queue cleared.", color=_RED))

    @commands.command(name="pause", help="Pause the current track.")
    async def pause_cmd(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send(embed=discord.Embed(title="⏸️ Paused", color=_GOLD))
        else:
            await ctx.send("Nothing is playing.")

    @commands.command(name="resume", help="Resume paused playback.")
    async def resume_cmd(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send(embed=discord.Embed(title="▶️ Resumed", color=_GREEN))
        else:
            await ctx.send("Playback is not paused.")

    # ─────────────────────────────────────────── queue / np
    @commands.command(name="queue", aliases=["q"], help="Show the current music queue.")
    async def queue_music_cmd(self, ctx: commands.Context):
        player = self._get_player(ctx)
        if not player:
            return
        q = player.queue

        # Status line
        status_parts = []
        if player.loop_mode == LOOP_TRACK: status_parts.append("🔂 Loop: Track")
        if player.loop_mode == LOOP_QUEUE: status_parts.append("🔁 Loop: Queue")
        if player.shuffle:                 status_parts.append("🔀 Shuffle: On")
        vol_pct = int(player.volume * 100)
        status_parts.append(f"🔊 {vol_pct}%")

        lines: List[str] = []
        if player.current:
            lines.append(f"▶️ **Now Playing:** {player.current.title}{_fmt_dur(player.current.duration)}")
        if q:
            for i, t in enumerate(q[:10], 1):
                lines.append(f"`{i}.` {t.title}{_fmt_dur(t.duration)} — *{t.requested_by_name}*")
            if len(q) > 10:
                lines.append(f"… and **{len(q) - 10}** more tracks.")
        else:
            lines.append("Queue is empty.")

        embed = discord.Embed(title="🎵 Music Queue", description="\n".join(lines), color=_BLUE)
        embed.set_footer(text=" · ".join(status_parts))
        await ctx.send(embed=embed)

    @commands.command(name="nowplaying", aliases=["np"], help="Show the current track.")
    async def nowplaying_cmd(self, ctx: commands.Context):
        player = self._get_player(ctx)
        if not player:
            return
        current = player.current
        if not current:
            await ctx.send(embed=discord.Embed(title="🔇 Nothing Playing", color=_RED))
            return
        embed = discord.Embed(
            title="▶️ Now Playing",
            description=f"**{current.title}**{_fmt_dur(current.duration)}\n\n*Requested by {current.requested_by_name}*",
            color=_GREEN,
        )
        embed.add_field(name="🔊 Volume", value=f"{int(player.volume * 100)}%")
        embed.add_field(name="🔂 Loop",   value=player.loop_mode.title())
        embed.add_field(name="🔀 Shuffle", value="On" if player.shuffle else "Off")
        await ctx.send(embed=embed)

    @commands.command(name="remove", aliases=["rm"], help="Remove a track from the queue by position.")
    async def remove_cmd(self, ctx: commands.Context, position: int):
        player = self._get_player(ctx)
        if not player:
            return
        removed = await player.remove(position)
        if removed:
            await ctx.send(embed=discord.Embed(
                title="🗑️ Removed", description=f"Removed **{removed.title}** from the queue.", color=_GOLD))
        else:
            await ctx.send(f"❌ No track at position `{position}`.")

    # ─────────────────────────────────────────── loop
    @commands.command(name="loop", help="Set loop mode: none | track | queue")
    async def loop_cmd(self, ctx: commands.Context, mode: str = ""):
        player = self._get_player(ctx)
        if not player:
            return
        mode = mode.lower().strip()
        if mode in ("track", "t", "song"):
            player.set_loop(LOOP_TRACK)
            await ctx.send(embed=discord.Embed(title="🔂 Loop: Track", description="Repeating the current track.", color=_PURPLE))
        elif mode in ("queue", "q", "all"):
            player.set_loop(LOOP_QUEUE)
            await ctx.send(embed=discord.Embed(title="🔁 Loop: Queue", description="Looping the entire queue.", color=_PURPLE))
        elif mode in ("none", "off", ""):
            player.set_loop(LOOP_NONE)
            await ctx.send(embed=discord.Embed(title="➡️ Loop: Off", description="Loop disabled.", color=_GOLD))
        else:
            await ctx.send("Usage: `!loop [none|track|queue]`")

    # ─────────────────────────────────────────── shuffle
    @commands.command(name="shuffle", help="Toggle shuffle mode.")
    async def shuffle_cmd(self, ctx: commands.Context):
        player = self._get_player(ctx)
        if not player:
            return
        state = player.toggle_shuffle()
        if state:
            await ctx.send(embed=discord.Embed(title="🔀 Shuffle: On", description="Queue has been shuffled.", color=_PURPLE))
        else:
            await ctx.send(embed=discord.Embed(title="➡️ Shuffle: Off", description="Shuffle disabled.", color=_GOLD))

    # ─────────────────────────────────────────── volume
    @commands.command(name="volume", aliases=["vol"], help="Set volume 0–200%. Example: !volume 80")
    async def volume_cmd(self, ctx: commands.Context, volume: int):
        player = self._get_player(ctx)
        if not player:
            return
        if not 0 <= volume <= 200:
            await ctx.send("❌ Volume must be between `0` and `200`.")
            return
        player.set_volume(volume / 100)
        bar = "█" * (volume // 10) + "░" * (20 - volume // 10)
        await ctx.send(embed=discord.Embed(
            title="🔊 Volume Set",
            description=f"`{bar}` **{volume}%**",
            color=_BLUE,
        ))

    # ─────────────────────────────────────────── playlists
    @commands.group(name="playlist", aliases=["pl"], invoke_without_command=True, help="Saved playlists.")
    async def playlist_group(self, ctx: commands.Context):
        await ctx.send(
            "**Playlist commands:**\n"
            "`!playlist save <name>` — Save the current queue as a playlist\n"
            "`!playlist play <name>` — Load and play a saved playlist\n"
            "`!playlist list`        — List your saved playlists\n"
            "`!playlist delete <name>` — Delete a saved playlist"
        )

    @playlist_group.command(name="save", help="Save the current queue as a named playlist.")
    async def playlist_save(self, ctx: commands.Context, *, name: str):
        player = self._get_player(ctx)
        if not player:
            return
        tracks = ([player.current] if player.current else []) + player.queue
        if not tracks:
            await ctx.send("❌ Nothing in the queue to save.")
            return
        queries = [t.title for t in tracks]  # use titles as search queries for re-resolution
        db_save_playlist(ctx.guild.id, ctx.author.id, name, queries)  # type: ignore[union-attr]
        await ctx.send(embed=discord.Embed(
            title="💾 Playlist Saved",
            description=f"Saved **{len(queries)}** tracks as `{name}`.",
            color=_GREEN,
        ))

    @playlist_group.command(name="play", help="Load and play a saved playlist.")
    async def playlist_play(self, ctx: commands.Context, *, name: str):
        mm = self._get_mm()
        if not mm or not await self._ensure_voice(ctx):
            return
        queries = db_load_playlist(ctx.guild.id, ctx.author.id, name)  # type: ignore[union-attr]
        if not queries:
            await ctx.send(f"❌ No playlist named `{name}` found.")
            return

        msg = await ctx.send(embed=discord.Embed(
            title="⏳ Loading Playlist",
            description=f"Resolving **{len(queries)}** tracks from `{name}`…",
            color=_BLUE,
        ))

        tracks: list[Track] = []
        async with ctx.typing():
            for q in queries:
                resolved = await resolve_tracks(q, ctx.author)  # type: ignore[arg-type]
                if resolved:
                    tracks.append(resolved[0])

        if not tracks:
            await msg.edit(embed=discord.Embed(title="❌ Failed", description="Could not resolve any tracks.", color=_RED))
            return

        player: MusicPlayer = mm.get_player_for_vc(ctx.voice_client)  # type: ignore[arg-type]
        started = await player.enqueue_many(tracks)
        desc = f"Loaded **{len(tracks)}** tracks from `{name}`."
        if started:
            desc += f"\n▶️ Started: **{started.title}**"
        await msg.edit(embed=discord.Embed(title="🎵 Playlist Loaded", description=desc, color=_GREEN))

    @playlist_group.command(name="list", help="List your saved playlists.")
    async def playlist_list(self, ctx: commands.Context):
        names = db_list_playlists(ctx.guild.id, ctx.author.id)  # type: ignore[union-attr]
        if not names:
            await ctx.send("You have no saved playlists. Use `!playlist save <name>` to save one.")
            return
        desc = "\n".join(f"`{i}.` {n}" for i, n in enumerate(names, 1))
        await ctx.send(embed=discord.Embed(title="📋 Your Playlists", description=desc, color=_BLUE))

    @playlist_group.command(name="delete", help="Delete a saved playlist.")
    async def playlist_delete(self, ctx: commands.Context, *, name: str):
        deleted = db_delete_playlist(ctx.guild.id, ctx.author.id, name)  # type: ignore[union-attr]
        if deleted:
            await ctx.send(embed=discord.Embed(title="🗑️ Deleted", description=f"Playlist `{name}` deleted.", color=_GOLD))
        else:
            await ctx.send(f"❌ No playlist named `{name}` found.")


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
