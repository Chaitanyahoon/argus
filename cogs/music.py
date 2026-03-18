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
import core.embeds as E

from core.music_player import (
    MusicManager, MusicPlayer, resolve_tracks, Track,
    LOOP_NONE, LOOP_TRACK, LOOP_QUEUE,
    db_save_playlist, db_load_playlist, db_list_playlists, db_delete_playlist,
)

logger = logging.getLogger(__name__)


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
        if not mm:
            return None
        if not ctx.guild:
            return None
        return mm.get_player(ctx.guild.id)

    async def _ensure_voice(self, ctx: commands.Context) -> bool:
        if ctx.voice_client:
            return True
        if ctx.author.voice and ctx.author.voice.channel:   # type: ignore[union-attr]
            await ctx.author.voice.channel.connect()         # type: ignore[union-attr]
            return True
        await ctx.send(embed=E.error("Voice Required", "Join a voice channel first.", ctx))
        return False

    # ─────────────────────────────────────────── join / leave
    @commands.command(name="join", help="Join your current voice channel.")
    async def join_vc(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:  # type: ignore[union-attr]
            await ctx.send(embed=E.error("Voice Required", "You must be in a voice channel.", ctx))
            return
        channel = ctx.author.voice.channel  # type: ignore[union-attr]
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send(embed=E.success("📡 Connected", f"Joined **{channel.name}**", ctx))

    @commands.command(name="leave", help="Disconnect from the voice channel.")
    async def leave_vc(self, ctx: commands.Context):
        if not ctx.voice_client:
            await ctx.send(embed=E.error("Not Connected", "I'm not in a voice channel.", ctx))
            return
        await ctx.voice_client.disconnect()
        await ctx.send(embed=E.warning("📡 Disconnected", "Left the voice channel.", ctx))

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
            await ctx.send(embed=E.error("❌ Not Found", f"No tracks found for `{query}`", ctx))
            return

        player: MusicPlayer = mm.get_player_for_vc(ctx.voice_client)  # type: ignore[arg-type]

        if len(tracks) == 1:
            t = tracks[0]
            await player.play(t)
            await ctx.send(embed=E.now_playing(
                t,
                volume=int(player.volume * 100),
                loop=player.loop_mode,
                shuffle=player.shuffle,
            ))
        else:
            started = await player.enqueue_many(tracks)
            desc = f"Added **{len(tracks)}** tracks to the queue."
            if started:
                desc += f"\n▶️ Started: **{started.title}**"
            await ctx.send(embed=E.info("🎵 Playlist Queued", desc, ctx))

    @commands.command(name="skip", aliases=["s"], help="Skip the current track.")
    async def skip_music_cmd(self, ctx: commands.Context):
        player = self._get_player(ctx)
        if not player:
            return
        if not ctx.voice_client:
            return
        current = player.current
        await player.skip()
        desc = f"Skipped **{current.title}**" if current else "Skipped."
        if player.current:
            desc += f"\n▶️ Now: **{player.current.title}**"
        await ctx.send(embed=E.warning("⏭️ Skipped", desc, ctx))

    @commands.command(name="stop", help="Stop playback and clear the queue.")
    async def stop_music_cmd(self, ctx: commands.Context):
        player = self._get_player(ctx)
        if not player:
            return
        if not ctx.voice_client:
            return
        await player.stop()
        await ctx.send(embed=E.error("🛑 Stopped", "Playback stopped and queue cleared.", ctx))

    @commands.command(name="pause", help="Pause the current track.")
    async def pause_cmd(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send(embed=E.warning("⏸️ Paused", "Use `!resume` to continue.", ctx))
        else:
            await ctx.send(embed=E.error("Nothing Playing", "There is nothing to pause.", ctx))

    @commands.command(name="resume", help="Resume paused playback.")
    async def resume_cmd(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send(embed=E.success("▶️ Resumed", "", ctx))
        else:
            await ctx.send(embed=E.error("Not Paused", "Playback is not paused.", ctx))

    # ─────────────────────────────────────────── queue / np
    @commands.command(name="queue", aliases=["q"], help="Show the current music queue.")
    async def queue_music_cmd(self, ctx: commands.Context):
        player = self._get_player(ctx)
        if not player:
            return
        await ctx.send(embed=E.queue_embed(player))

    @commands.command(name="nowplaying", aliases=["np"], help="Show the current track.")
    async def nowplaying_cmd(self, ctx: commands.Context):
        player = self._get_player(ctx)
        if not player:
            return
        if not player.current:
            await ctx.send(embed=E.error("🔇 Nothing Playing", "Start something with `!play`.", ctx))
            return
        await ctx.send(embed=E.now_playing(
            player.current,
            volume=int(player.volume * 100),
            loop=player.loop_mode,
            shuffle=player.shuffle,
        ))

    @commands.command(name="remove", aliases=["rm"], help="Remove a track from the queue by position.")
    async def remove_cmd(self, ctx: commands.Context, position: int):
        player = self._get_player(ctx)
        if not player:
            return
        removed = await player.remove(position)
        if removed:
            await ctx.send(embed=E.warning("🗑️ Removed", f"Removed **{removed.title}** from the queue.", ctx))
        else:
            await ctx.send(embed=E.error("Not Found", f"No track at position `{position}`.", ctx))

    # ─────────────────────────────────────────── loop
    @commands.command(name="loop", help="Set loop mode: none | track | queue")
    async def loop_cmd(self, ctx: commands.Context, mode: str = ""):
        player = self._get_player(ctx)
        if not player:
            return
        mode = mode.lower().strip()
        if mode in ("track", "t", "song"):
            player.set_loop(LOOP_TRACK)
            await ctx.send(embed=E.purple("🔂 Loop: Track", "Repeating the current track.", ctx))
        elif mode in ("queue", "q", "all"):
            player.set_loop(LOOP_QUEUE)
            await ctx.send(embed=E.purple("🔁 Loop: Queue", "Looping the entire queue.", ctx))
        elif mode in ("none", "off", ""):
            player.set_loop(LOOP_NONE)
            await ctx.send(embed=E.warning("➡️ Loop: Off", "Loop disabled.", ctx))
        else:
            await ctx.send(embed=E.error("Invalid Mode", "Usage: `!loop [none|track|queue]`", ctx))

    # ─────────────────────────────────────────── shuffle
    @commands.command(name="shuffle", help="Toggle shuffle mode.")
    async def shuffle_cmd(self, ctx: commands.Context):
        player = self._get_player(ctx)
        if not player:
            return
        state = player.toggle_shuffle()
        if state:
            await ctx.send(embed=E.purple("🔀 Shuffle: On", "Queue has been shuffled.", ctx))
        else:
            await ctx.send(embed=E.warning("➡️ Shuffle: Off", "Shuffle disabled.", ctx))

    # ─────────────────────────────────────────── volume
    @commands.command(name="volume", aliases=["vol"], help="Set volume 0–200%. Example: !volume 80")
    async def volume_cmd(self, ctx: commands.Context, volume: int):
        player = self._get_player(ctx)
        if not player:
            return
        if not 0 <= volume <= 200:
            await ctx.send(embed=E.error("Invalid Volume", "Must be between `0` and `200`.", ctx))
            return
        player.set_volume(volume / 100)
        filled = round(volume / 10)
        bar = "█" * filled + "░" * (20 - filled)
        await ctx.send(embed=E.info("🔊 Volume", f"`{bar}`  **{volume}%**", ctx))

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
            await ctx.send(embed=E.error("Empty Queue", "Nothing in the queue to save.", ctx))
            return
        queries = [t.title for t in tracks]
        db_save_playlist(ctx.guild.id, ctx.author.id, name, queries)  # type: ignore[union-attr]
        await ctx.send(embed=E.success("💾 Playlist Saved", f"Saved **{len(queries)}** tracks as `{name}`.", ctx))

    @playlist_group.command(name="play", help="Load and play a saved playlist.")
    async def playlist_play(self, ctx: commands.Context, *, name: str):
        mm = self._get_mm()
        if not mm or not await self._ensure_voice(ctx):
            return
        queries = db_load_playlist(ctx.guild.id, ctx.author.id, name)  # type: ignore[union-attr]
        if not queries:
            await ctx.send(f"❌ No playlist named `{name}` found.")
            return

        msg = await ctx.send(embed=E.info("⏳ Loading Playlist", f"Resolving **{len(queries)}** tracks from `{name}`…"))

        tracks: list[Track] = []
        async with ctx.typing():
            for q in queries:
                resolved = await resolve_tracks(q, ctx.author)  # type: ignore[arg-type]
                if resolved:
                    tracks.append(resolved[0])

        if not tracks:
            await msg.edit(embed=E.error("❌ Failed", "Could not resolve any tracks."))
            return

        player: MusicPlayer = mm.get_player_for_vc(ctx.voice_client)  # type: ignore[arg-type]
        started = await player.enqueue_many(tracks)
        desc = f"Loaded **{len(tracks)}** tracks from `{name}`."
        if started:
            desc += f"\n▶️ Started: **{started.title}**"
        await msg.edit(embed=E.success("🎵 Playlist Loaded", desc))

    @playlist_group.command(name="list", help="List your saved playlists.")
    async def playlist_list(self, ctx: commands.Context):
        names = db_list_playlists(ctx.guild.id, ctx.author.id)  # type: ignore[union-attr]
        if not names:
            await ctx.send(embed=E.info("📋 No Playlists", "Use `!playlist save <name>` to save the current queue.", ctx))
            return
        desc = "\n".join(f"`{i:>2}.`  {n}" for i, n in enumerate(names, 1))
        await ctx.send(embed=E.info("📋 Your Playlists", desc, ctx))

    @playlist_group.command(name="delete", help="Delete a saved playlist.")
    async def playlist_delete(self, ctx: commands.Context, *, name: str):
        deleted = db_delete_playlist(ctx.guild.id, ctx.author.id, name)  # type: ignore[union-attr]
        if deleted:
            await ctx.send(embed=E.warning("🗑️ Deleted", f"Playlist `{name}` deleted.", ctx))
        else:
            await ctx.send(embed=E.error("Not Found", f"No playlist named `{name}`.", ctx))


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
