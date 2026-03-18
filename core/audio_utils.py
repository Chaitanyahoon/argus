"""
Audio utilities — resampling between Discord and Gemini formats,
plus a custom AudioSource for streaming PCM playback.

Audio format specifications:
  Discord audio: 48 kHz, stereo, 16-bit signed LE PCM
  Gemini input:  16 kHz, mono,   16-bit signed LE PCM
  Gemini output: 24 kHz, mono,   16-bit signed LE PCM
"""

import audioop
import asyncio
import logging
import struct
from collections import deque
from typing import Tuple, Optional

import discord

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

DISCORD_RATE = 48000
DISCORD_CHANNELS = 2
DISCORD_SAMPLE_WIDTH = 2  # 16-bit

GEMINI_INPUT_RATE = 16000
GEMINI_OUTPUT_RATE = 24000
GEMINI_CHANNELS = 1
GEMINI_SAMPLE_WIDTH = 2  # 16-bit

# Discord sends 20ms frames → 48000 * 2ch * 2bytes * 0.02s = 3840 bytes
DISCORD_FRAME_SIZE = DISCORD_RATE * DISCORD_CHANNELS * DISCORD_SAMPLE_WIDTH // 50  # 3840

# ── Resampling Functions ─────────────────────────────────────────────────────


def discord_to_gemini(pcm_48k_stereo: bytes) -> bytes:
    """
    Convert Discord PCM (48 kHz stereo 16-bit) to Gemini input format
    (16 kHz mono 16-bit).

    Steps: stereo→mono, then 48000→16000 (ratio 3:1).
    """
    if not pcm_48k_stereo:
        return b""

    # Stereo to mono
    mono = audioop.tomono(pcm_48k_stereo, DISCORD_SAMPLE_WIDTH, 0.5, 0.5)

    # Downsample 48kHz → 16kHz (ratio 3:1)
    # audioop.ratecv(fragment, width, nchannels, inrate, outrate, state)
    resampled, _ = audioop.ratecv(
        mono, DISCORD_SAMPLE_WIDTH, 1, DISCORD_RATE, GEMINI_INPUT_RATE, None
    )

    return resampled


def gemini_to_discord(pcm_24k_mono: bytes) -> bytes:
    """
    Convert Gemini output PCM (24 kHz mono 16-bit) to Discord playback format
    (48 kHz stereo 16-bit).

    Steps: 24000→48000 (ratio 2:1), then mono→stereo.
    """
    if not pcm_24k_mono:
        return b""

    # Upsample 24kHz → 48kHz (ratio 2:1)
    resampled, _ = audioop.ratecv(
        pcm_24k_mono, GEMINI_SAMPLE_WIDTH, 1, GEMINI_OUTPUT_RATE, DISCORD_RATE, None
    )

    # Mono to stereo (duplicate the channel)
    stereo = audioop.tostereo(resampled, DISCORD_SAMPLE_WIDTH, 1.0, 1.0)

    return stereo


# ── PCM Audio Source for Discord Playback ────────────────────────────────────


class PCMAudioSource(discord.AudioSource):
    """
    A Discord AudioSource that reads from an asyncio-safe byte buffer.

    Audio is fed in via `write()` (from the Gemini response handler) and
    consumed by Discord's voice client in 20ms PCM frames.
    """

    def __init__(self):
        self._buffer = bytearray()
        self._lock = asyncio.Lock()
        self._finished = asyncio.Event()

    def write(self, data: bytes) -> None:
        """Append audio data to the playback buffer (thread-safe via GIL)."""
        self._buffer.extend(data)

    def mark_finished(self) -> None:
        """Signal that no more audio will be written."""
        self._finished.set()

    @property
    def is_finished(self) -> bool:
        return self._finished.is_set() and len(self._buffer) == 0

    def read(self) -> bytes:
        """
        Called by Discord's voice client every 20ms.
        Returns exactly DISCORD_FRAME_SIZE bytes, or silence if buffer is empty.
        """
        if len(self._buffer) >= DISCORD_FRAME_SIZE:
            frame = bytes(self._buffer[:DISCORD_FRAME_SIZE])
            del self._buffer[:DISCORD_FRAME_SIZE]
            return frame

        # If finished and buffer is fully drained, signal end
        if self._finished.is_set() and len(self._buffer) == 0:
            return b""

        # Not enough data yet — return silence to avoid stutter
        return b"\x00" * DISCORD_FRAME_SIZE

    def is_opus(self) -> bool:
        return False

    def cleanup(self) -> None:
        self._buffer.clear()




