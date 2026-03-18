"""
Music player — high-quality audio from URLs (YouTube, Spotify, etc.) via
yt-dlp + FFmpeg, with Spotify metadata scraping (no API keys).

Per-guild queue, 48 kHz stereo PCM playback through the Discord voice client.
Supports: loop (track/queue), shuffle, volume control, saved playlists.
"""

import asyncio
import logging
import random
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import discord

logger = logging.getLogger(__name__)

# ── FFmpeg options ─────────────────────────────────────────────────────────────
FFMPEG_BEFORE_OPTIONS = (
    "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
)
FFMPEG_OPTIONS = "-vn"

# ── Spotify URL patterns ────────────────────────────────────────────────────
_SPOTIFY_TRACK_RE = re.compile(
    r"https?://open\.spotify\.com/(?:intl-\w+/)?track/([A-Za-z0-9]+)"
)
_SPOTIFY_ALBUM_RE = re.compile(
    r"https?://open\.spotify\.com/(?:intl-\w+/)?album/([A-Za-z0-9]+)"
)
_SPOTIFY_PLAYLIST_RE = re.compile(
    r"https?://open\.spotify\.com/(?:intl-\w+/)?playlist/([A-Za-z0-9]+)"
)

# ── yt-dlp options ──────────────────────────────────────────────────────────
_YDL_OPTS: dict[str, Any] = {
    "format": "bestaudio[acodec=opus]/bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "extract_flat": False,
    "noplaylist": True,
    "default_search": "ytsearch1",
    "source_address": "0.0.0.0",
}

# ── Loop modes ─────────────────────────────────────────────────────────────────
LOOP_NONE  = "none"   # no looping
LOOP_TRACK = "track"  # repeat current track
LOOP_QUEUE = "queue"  # repeat entire queue


@dataclass
class Track:
    """A single track in the queue."""
    url: str
    title: str
    requested_by_id: int
    requested_by_name: str
    duration: int | None = None


# ── Spotify helpers ──────────────────────────────────────────────────────────
_SPOTIFY_CLIENT = None


def _get_spotify_client():
    global _SPOTIFY_CLIENT
    if _SPOTIFY_CLIENT is None:
        try:
            from spotify_scraper import SpotifyClient
            _SPOTIFY_CLIENT = SpotifyClient()
        except ImportError:
            logger.error("spotify_scraper is not installed")
            return None
        except Exception as e:
            logger.warning("SpotifyClient init failed: %s", e)
            return None
    return _SPOTIFY_CLIENT


def _spotify_search_queries(url: str) -> list[str] | None:
    track_m    = _SPOTIFY_TRACK_RE.search(url)
    album_m    = _SPOTIFY_ALBUM_RE.search(url)    if not track_m else None
    playlist_m = _SPOTIFY_PLAYLIST_RE.search(url) if not track_m and not album_m else None

    if not (track_m or album_m or playlist_m):
        return None

    client = _get_spotify_client()
    if not client:
        return None

    queries: list[str] = []
    try:
        if track_m:
            info = client.get_track_info(url)
            if info:
                name   = info.get("name", "")
                artist = (info.get("artists") or [{}])[0].get("name", "")
                if name:
                    queries.append(f"{name} {artist}".strip())
        elif album_m:
            info = client.get_album_info(url)
            if info:
                aa = (info.get("artists") or [{}])[0].get("name", "")
                for t in info.get("tracks", []):
                    n   = t.get("name", "")
                    art = (t.get("artists") or [{}])[0].get("name", "") or aa
                    if n:
                        queries.append(f"{n} {art}".strip())
        elif playlist_m:
            info = client.get_playlist_info(url)
            if info:
                for t in info.get("tracks", []):
                    n   = t.get("name", "")
                    art = (t.get("artists") or [{}])[0].get("name", "")
                    if n:
                        queries.append(f"{n} {art}".strip())
    except Exception as e:
        logger.warning("Spotify scrape failed for %s: %s", url[:80], e)
    finally:
        try:
            client.close()
        except Exception:
            pass

    return queries if queries else None


# ── yt-dlp helpers ───────────────────────────────────────────────────────────

def _pick_best_audio_url(info: dict[str, Any]) -> str | None:
    url = info.get("url")
    if url:
        return url
    formats = info.get("formats")
    if not formats:
        return None
    for f in reversed(formats):
        if f.get("vcodec") == "none" and f.get("url"):
            return f["url"]
    return formats[0].get("url") if formats else None


def _extract_single(query: str) -> dict[str, Any] | None:
    try:
        import yt_dlp
    except ImportError:
        logger.error("yt-dlp is not installed")
        return None

    try:
        with yt_dlp.YoutubeDL(_YDL_OPTS) as ydl:
            info = ydl.extract_info(query, download=False)
    except Exception as e:
        logger.warning("yt-dlp failed for %.80s: %s", query, e)
        return None

    if not info:
        return None

    if info.get("entries") is not None:
        entries = list(info["entries"]) if not isinstance(info["entries"], (str, dict)) else [info["entries"]]
        info = next((e for e in entries if e and isinstance(e, dict)), None)
        if info is None:
            return None

    url = _pick_best_audio_url(info)

    if not url and (info.get("webpage_url") or info.get("id")):
        single = info.get("webpage_url") or f"https://www.youtube.com/watch?v={info['id']}"
        try:
            with yt_dlp.YoutubeDL(_YDL_OPTS) as ydl:
                full = ydl.extract_info(single, download=False)
        except Exception:
            full = None
        if full:
            url = _pick_best_audio_url(full)
            if url:
                info["title"]    = full.get("title") or info.get("title")
                info["duration"] = full.get("duration")

    if not url:
        return None

    return {
        "url":      url,
        "title":    info.get("title") or "Unknown",
        "duration": info.get("duration"),
    }


# ── Public resolve API ───────────────────────────────────────────────────────

async def resolve_tracks(query: str, requested_by: discord.Member) -> list[Track]:
    query = query.strip()
    if not query:
        return []

    spotify_queries = await asyncio.to_thread(_spotify_search_queries, query)

    if spotify_queries is not None:
        tracks: list[Track] = []
        for sq in spotify_queries:
            info = await asyncio.to_thread(_extract_single, sq)
            if info:
                tracks.append(Track(
                    url=info["url"], title=info["title"],
                    requested_by_id=requested_by.id,
                    requested_by_name=requested_by.display_name,
                    duration=info.get("duration"),
                ))
        return tracks

    info = await asyncio.to_thread(_extract_single, query)
    if not info:
        return []

    return [Track(
        url=info["url"], title=info["title"],
        requested_by_id=requested_by.id,
        requested_by_name=requested_by.display_name,
        duration=info.get("duration"),
    )]


async def resolve_track(query: str, requested_by: discord.Member) -> Track | None:
    tracks = await resolve_tracks(query, requested_by)
    return tracks[0] if tracks else None


# ── Audio source factory ─────────────────────────────────────────────────────

async def _make_source(url: str, volume: float = 1.0) -> discord.AudioSource:
    try:
        source = await discord.FFmpegOpusAudio.from_probe(
            url,
            before_options=FFMPEG_BEFORE_OPTIONS,
            options=FFMPEG_OPTIONS,
        )
    except Exception as e:
        logger.debug("FFmpegOpusAudio.from_probe failed, falling back: %s", e)
        source = discord.FFmpegPCMAudio(
            url,
            before_options=FFMPEG_BEFORE_OPTIONS,
            options=FFMPEG_OPTIONS,
        )
    # Wrap with volume transformer (1.0 = 100%)
    return discord.PCMVolumeTransformer(source, volume=volume) if isinstance(source, discord.FFmpegPCMAudio) else source


# ── Saved Playlist DB ────────────────────────────────────────────────────────

_DB_PATH = Path(__file__).parent.parent / "data" / "argus.db"


def _init_playlist_table() -> None:
    with sqlite3.connect(str(_DB_PATH)) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS saved_playlists (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id  INTEGER NOT NULL,
                user_id   INTEGER NOT NULL,
                name      TEXT NOT NULL,
                query     TEXT NOT NULL,
                UNIQUE(guild_id, user_id, name)
            )
        """)
        c.commit()


def db_save_playlist(guild_id: int, user_id: int, name: str, queries: list[str]) -> None:
    _init_playlist_table()
    import json
    with sqlite3.connect(str(_DB_PATH)) as c:
        c.execute(
            "INSERT OR REPLACE INTO saved_playlists (guild_id, user_id, name, query) VALUES (?, ?, ?, ?)",
            (guild_id, user_id, name, json.dumps(queries)),
        )
        c.commit()


def db_load_playlist(guild_id: int, user_id: int, name: str) -> list[str] | None:
    _init_playlist_table()
    import json
    with sqlite3.connect(str(_DB_PATH)) as c:
        row = c.execute(
            "SELECT query FROM saved_playlists WHERE guild_id=? AND user_id=? AND name=?",
            (guild_id, user_id, name),
        ).fetchone()
    return json.loads(row[0]) if row else None


def db_list_playlists(guild_id: int, user_id: int) -> list[str]:
    _init_playlist_table()
    with sqlite3.connect(str(_DB_PATH)) as c:
        rows = c.execute(
            "SELECT name FROM saved_playlists WHERE guild_id=? AND user_id=? ORDER BY name",
            (guild_id, user_id),
        ).fetchall()
    return [r[0] for r in rows]


def db_delete_playlist(guild_id: int, user_id: int, name: str) -> bool:
    _init_playlist_table()
    with sqlite3.connect(str(_DB_PATH)) as c:
        c.execute(
            "DELETE FROM saved_playlists WHERE guild_id=? AND user_id=? AND name=?",
            (guild_id, user_id, name),
        )
        deleted = c.execute("SELECT changes()").fetchone()[0]
        c.commit()
    return deleted > 0


# ── MusicPlayer ──────────────────────────────────────────────────────────────

class MusicPlayer:
    """Per-guild music state: queue, playback, loop, shuffle, volume."""

    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self._queue: list[Track] = []
        self._current: Track | None = None
        self._voice_client: discord.VoiceClient | None = None
        self._lock = asyncio.Lock()

        # ── New state ──────────────────────────────────────────────────────────
        self.loop_mode: str  = LOOP_NONE   # LOOP_NONE | LOOP_TRACK | LOOP_QUEUE
        self.volume:    float = 1.0         # 0.0 – 2.0  (1.0 = 100%)
        self._shuffle:  bool  = False
        self._queue_snapshot: list[Track] = []  # used for LOOP_QUEUE

    # ── Properties ─────────────────────────────────────────────────────────────
    @property
    def queue(self) -> list[Track]:
        return self._queue.copy()

    @property
    def current(self) -> Track | None:
        return self._current

    @property
    def is_playing(self) -> bool:
        return (
            self._voice_client is not None
            and self._voice_client.is_connected()
            and self._voice_client.is_playing()
        )

    @property
    def shuffle(self) -> bool:
        return self._shuffle

    def set_voice_client(self, vc: discord.VoiceClient | None) -> None:
        self._voice_client = vc

    def add(self, track: Track) -> None:
        self._queue.append(track)

    # ── Volume ─────────────────────────────────────────────────────────────────
    def set_volume(self, volume: float) -> None:
        """Set volume 0.0 – 2.0. Applies immediately to current source."""
        self.volume = max(0.0, min(2.0, volume))
        if self._voice_client and self._voice_client.source:
            src = self._voice_client.source
            if isinstance(src, discord.PCMVolumeTransformer):
                src.volume = self.volume

    # ── Shuffle ────────────────────────────────────────────────────────────────
    def toggle_shuffle(self) -> bool:
        """Toggle shuffle. Returns new state."""
        self._shuffle = not self._shuffle
        if self._shuffle and self._queue:
            random.shuffle(self._queue)
        return self._shuffle

    # ── Loop ───────────────────────────────────────────────────────────────────
    def set_loop(self, mode: str) -> None:
        """Set loop mode: 'none', 'track', or 'queue'."""
        self.loop_mode = mode
        if mode == LOOP_QUEUE:
            # Save snapshot of the full queue + current track for cycling
            self._queue_snapshot = (
                ([self._current] if self._current else []) + self._queue.copy()
            )

    # ── Internal playback ──────────────────────────────────────────────────────
    def _play_next(self, error: Exception | None = None) -> None:
        if error:
            logger.warning("Music error (guild %s): %s", self.guild_id, error)
        vc = self._voice_client
        if not vc:
            return
        loop = getattr(vc, "loop", None) or (
            getattr(vc, "client", None) and getattr(vc.client, "loop", None)
        )
        if not loop:
            return
        loop.call_soon_threadsafe(
            lambda: asyncio.ensure_future(self._play_next_async(), loop=loop)
        )

    async def _start_track(self, track: Track) -> None:
        source = await _make_source(track.url, self.volume)
        self._voice_client.play(source, after=self._play_next)

    async def _play_next_async(self) -> None:
        async with self._lock:
            if not self._voice_client or not self._voice_client.is_connected():
                return
            if self._voice_client.is_playing():
                return

            finished = self._current

            # ── Loop track: replay the same track ─────────────────────────────
            if self.loop_mode == LOOP_TRACK and finished:
                self._current = finished
                await self._start_track(finished)
                return

            # ── Loop queue: cycle through snapshot ───────────────────────────
            if self.loop_mode == LOOP_QUEUE:
                if finished:
                    self._queue_snapshot.append(finished)
                if not self._queue:
                    self._queue = self._queue_snapshot.copy()
                    self._queue_snapshot = []
                    if self._shuffle:
                        random.shuffle(self._queue)

            self._current = None
            if not self._queue:
                return

            # Pick next track (shuffle already applied to queue order)
            track = self._queue.pop(0)
            self._current = track
            await self._start_track(track)

    # ── Public API ─────────────────────────────────────────────────────────────

    async def play(self, track: Track) -> None:
        """Enqueue one track and start if idle."""
        async with self._lock:
            self._queue.append(track)
            if not self._voice_client or not self._voice_client.is_connected():
                return
            if self._voice_client.is_playing():
                return
            self._queue.pop()
            self._current = track
            await self._start_track(track)

    async def enqueue_many(self, tracks: list[Track]) -> Track | None:
        """Add multiple tracks. Returns the track that started playing (if any)."""
        if not tracks:
            return None
        async with self._lock:
            if self._shuffle:
                tracks = tracks.copy()
                random.shuffle(tracks)
            self._queue.extend(tracks)
            if not self._voice_client or not self._voice_client.is_connected():
                return None
            if self._voice_client.is_playing():
                return None
            track = self._queue.pop(0)
            self._current = track
            await self._start_track(track)
            return track

    async def skip(self) -> bool:
        """Skip current track."""
        async with self._lock:
            if not self._voice_client or not self._voice_client.is_connected():
                return bool(self._queue)
            # Cancel loop-track so skip actually advances
            prev_loop = self.loop_mode
            if self.loop_mode == LOOP_TRACK:
                self.loop_mode = LOOP_NONE
            if self._voice_client.is_playing():
                self._voice_client.stop()
            self.loop_mode = prev_loop
            self._current = None
            if not self._queue:
                return True
            track = self._queue.pop(0)
            self._current = track
            await self._start_track(track)
            return True

    async def stop(self) -> None:
        """Stop playback and clear everything."""
        async with self._lock:
            self._queue.clear()
            self._queue_snapshot.clear()
            self._current = None
            self.loop_mode = LOOP_NONE
            self._shuffle  = False
            if self._voice_client and self._voice_client.is_connected():
                if self._voice_client.is_playing():
                    self._voice_client.stop()

    async def remove(self, index: int) -> Track | None:
        """Remove a track from the queue by 1-based index."""
        async with self._lock:
            if 1 <= index <= len(self._queue):
                return self._queue.pop(index - 1)
        return None


# ── MusicManager ────────────────────────────────────────────────────────────

class MusicManager:
    """Holds one MusicPlayer per guild."""

    def __init__(self):
        self._players: dict[int, MusicPlayer] = {}

    def get_player(self, guild_id: int) -> MusicPlayer:
        if guild_id not in self._players:
            self._players[guild_id] = MusicPlayer(guild_id)
        return self._players[guild_id]

    def get_player_for_vc(self, voice_client: discord.VoiceClient) -> MusicPlayer | None:
        if not voice_client or not voice_client.guild:
            return None
        player = self.get_player(voice_client.guild.id)
        player.set_voice_client(voice_client)
        return player
