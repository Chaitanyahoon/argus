"""
Music player — high-quality audio from URLs (YouTube, Spotify, etc.) via
yt-dlp + FFmpeg, with Spotify metadata scraping (no API keys).

Per-guild queue, 48 kHz stereo PCM playback through the Discord voice client.
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Any

import discord

logger = logging.getLogger(__name__)

# ── FFmpeg options for highest quality ────────────────────────────────────────
# Uses FFmpegOpusAudio (FFmpeg encodes to Opus directly) instead of
# FFmpegPCMAudio (FFmpeg→PCM→discord.py re-encodes to Opus), avoiding a
# lossy double-encode. The -b:a 256k flag ensures the Opus output is at a
# high bitrate; Discord will use up to the channel's limit (e.g. 96/128/384k).
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

# ── yt-dlp options (shared) ─────────────────────────────────────────────────
# Prefer Opus audio-only at highest bitrate; fall back to any best audio.
_YDL_OPTS: dict[str, Any] = {
    "format": "bestaudio[acodec=opus]/bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "extract_flat": False,
    "noplaylist": True,
    "default_search": "ytsearch1",
    "source_address": "0.0.0.0",
}


@dataclass
class Track:
    """A single track in the queue."""
    url: str
    title: str
    requested_by_id: int
    requested_by_name: str
    duration: int | None = None


# ── Spotify helpers ──────────────────────────────────────────────────────────
# Initialize Spotify client once (lazy-loaded singleton)
_SPOTIFY_CLIENT = None


def _get_spotify_client():
    """Get or initialize Spotify client (singleton pattern)."""
    global _SPOTIFY_CLIENT
    if _SPOTIFY_CLIENT is None:
        try:
            from spotify_scraper import SpotifyClient
            _SPOTIFY_CLIENT = SpotifyClient()
        except ImportError:
            logger.error("spotify_scraper is not installed; cannot resolve Spotify URLs")
            return None
        except Exception as e:
            logger.warning("SpotifyClient initialization failed: %s", e)
            return None
    return _SPOTIFY_CLIENT

def _spotify_search_queries(url: str) -> list[str] | None:
    """
    If *url* is a Spotify link, scrape track/album/playlist metadata and
    return a list of YouTube search queries ("track artist").
    Returns None when the URL is not a Spotify link.
    """
    track_m = _SPOTIFY_TRACK_RE.search(url)
    album_m = _SPOTIFY_ALBUM_RE.search(url) if not track_m else None
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
                name = info.get("name", "")
                artists = info.get("artists", [])
                artist = artists[0].get("name", "") if artists else ""
                if name:
                    queries.append(f"{name} {artist}".strip())

        elif album_m:
            info = client.get_album_info(url)
            if info:
                album_artist = ""
                album_artists = info.get("artists", [])
                if album_artists:
                    album_artist = album_artists[0].get("name", "")
                for t in info.get("tracks", []):
                    name = t.get("name", "")
                    t_artists = t.get("artists", [])
                    artist = t_artists[0].get("name", "") if t_artists else album_artist
                    if name:
                        queries.append(f"{name} {artist}".strip())

        elif playlist_m:
            info = client.get_playlist_info(url)
            if info:
                for t in info.get("tracks", []):
                    name = t.get("name", "")
                    t_artists = t.get("artists", [])
                    artist = t_artists[0].get("name", "") if t_artists else ""
                    if name:
                        queries.append(f"{name} {artist}".strip())
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
    """Pick the best audio-only stream URL from an info dict."""
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
    """
    Resolve a single query (URL or search) to {url, title, duration} via yt-dlp.
    Runs synchronously (call from a thread).
    """
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

    # Unwrap search / playlist results
    if info.get("entries") is not None:
        entries = info["entries"]
        if hasattr(entries, "__iter__") and not isinstance(entries, (str, dict)):
            entries = list(entries)
        else:
            entries = [entries] if entries else []
        info = None
        for entry in entries:
            if entry and isinstance(entry, dict):
                info = entry
                break
        if info is None:
            return None

    url = _pick_best_audio_url(info)

    # Partial entry from search — re-extract the single video
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
                info["title"] = full.get("title") or info.get("title")
                info["duration"] = full.get("duration")

    if not url:
        return None

    return {
        "url": url,
        "title": info.get("title") or "Unknown",
        "duration": info.get("duration"),
    }


# ── Public resolve API ───────────────────────────────────────────────────────

async def resolve_tracks(
    query: str, requested_by: discord.Member
) -> list[Track]:
    """
    Resolve a query to one or more Tracks.

    Handles:
    - Spotify track/album/playlist URLs (scrape metadata -> YouTube search)
    - YouTube URLs (direct)
    - Plain text search (YouTube search via yt-dlp default_search)

    Returns an empty list on failure.
    """
    query = query.strip()
    if not query:
        return []

    # Check for Spotify URL first
    spotify_queries = await asyncio.to_thread(_spotify_search_queries, query)

    if spotify_queries is not None:
        tracks: list[Track] = []
        for sq in spotify_queries:
            info = await asyncio.to_thread(_extract_single, sq)
            if info:
                tracks.append(Track(
                    url=info["url"],
                    title=info["title"],
                    requested_by_id=requested_by.id,
                    requested_by_name=requested_by.display_name,
                    duration=info.get("duration"),
                ))
        return tracks

    # YouTube URL or plain search
    info = await asyncio.to_thread(_extract_single, query)
    if not info:
        return []

    return [Track(
        url=info["url"],
        title=info["title"],
        requested_by_id=requested_by.id,
        requested_by_name=requested_by.display_name,
        duration=info.get("duration"),
    )]


async def resolve_track(
    query: str, requested_by: discord.Member
) -> Track | None:
    """Convenience wrapper: resolve a single track (first result)."""
    tracks = await resolve_tracks(query, requested_by)
    return tracks[0] if tracks else None


# ── Audio source factory ─────────────────────────────────────────────────────

async def _make_source(url: str) -> discord.AudioSource:
    """
    Create a high-quality audio source for playback.

    Uses FFmpegOpusAudio.from_probe() so FFmpeg encodes directly to Opus,
    avoiding the lossy PCM->Opus re-encode that FFmpegPCMAudio does.
    Falls back to FFmpegPCMAudio if from_probe fails (e.g. older discord.py).
    """
    try:
        source = await discord.FFmpegOpusAudio.from_probe(
            url,
            before_options=FFMPEG_BEFORE_OPTIONS,
            options=FFMPEG_OPTIONS,
        )
        return source
    except Exception as e:
        logger.debug("FFmpegOpusAudio.from_probe failed, falling back to PCM: %s", e)
        return discord.FFmpegPCMAudio(
            url,
            before_options=FFMPEG_BEFORE_OPTIONS,
            options=FFMPEG_OPTIONS,
        )


# ── MusicPlayer / MusicManager ──────────────────────────────────────────────

class MusicPlayer:
    """Per-guild music state: queue and playback."""

    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self._queue: list[Track] = []
        self._current: Track | None = None
        self._voice_client: discord.VoiceClient | None = None
        self._lock = asyncio.Lock()

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

    def set_voice_client(self, vc: discord.VoiceClient | None) -> None:
        self._voice_client = vc

    def add(self, track: Track) -> None:
        self._queue.append(track)

    def _play_next(self, error: Exception | None = None) -> None:
        """Called after a track ends (or errors). Runs in Discord's audio thread."""
        if error:
            logger.warning("Music playback error (guild %s): %s", self.guild_id, error)
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
        """Create audio source and start playback. Caller must hold self._lock."""
        source = await _make_source(track.url)
        self._voice_client.play(source, after=self._play_next)

    async def _play_next_async(self) -> None:
        async with self._lock:
            self._current = None
            if not self._voice_client or not self._voice_client.is_connected():
                return
            if self._voice_client.is_playing():
                return
            if not self._queue:
                return
            track = self._queue.pop(0)
            self._current = track
            await self._start_track(track)

    async def play(self, track: Track) -> None:
        """Enqueue and start playing if idle."""
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
        """Add multiple tracks. If idle, starts the first one. Returns the track that started playing (or None)."""
        if not tracks:
            return None
        async with self._lock:
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
        async with self._lock:
            if not self._voice_client or not self._voice_client.is_connected():
                return bool(self._queue)
            if self._voice_client.is_playing():
                self._voice_client.stop()
            self._current = None
            if not self._queue:
                return True
            track = self._queue.pop(0)
            self._current = track
            await self._start_track(track)
            return True

    async def stop(self) -> None:
        async with self._lock:
            self._queue.clear()
            self._current = None
            if self._voice_client and self._voice_client.is_connected():
                if self._voice_client.is_playing():
                    self._voice_client.stop()


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
