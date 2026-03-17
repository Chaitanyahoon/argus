"""
Transcriber — converts WAV audio bytes to text using faster-whisper.
Multilingual support with automatic language detection.
"""

import io
import logging
from typing import Optional

from faster_whisper import WhisperModel

from config import Config

logger = logging.getLogger(__name__)


class Transcriber:
    """Handles speech-to-text using faster-whisper (multilingual)."""

    model: WhisperModel

    def __init__(self) -> None:
        logger.info(
            "Loading Whisper model '%s' (this may take a moment on first run)...",
            Config.WHISPER_MODEL,
        )
        self.model = WhisperModel(
            Config.WHISPER_MODEL,
            device="cpu",
            compute_type="int8",
        )
        logger.info("Whisper model loaded successfully.")

    def transcribe_wav(self, wav_bytes: bytes) -> Optional[str]:
        """
        Transcribe WAV audio bytes to text.

        Args:
            wav_bytes: Raw WAV file bytes from a voice recording sink (e.g. WAV export).

        Returns:
            Transcribed text string, or None if no speech detected.
        """
        try:
            audio_file = io.BytesIO(wav_bytes)

            # language=None enables auto language detection
            segments, info = self.model.transcribe(
                audio_file,
                language=None,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=300,
                    speech_pad_ms=200,
                ),
            )

            text_parts: list[str] = []
            for segment in segments:
                text_parts.append(segment.text.strip())

            full_text: str = " ".join(text_parts).strip()

            if full_text:
                logger.info(
                    "Transcribed [%s]: '%s' (%.1fs audio)",
                    info.language or "unknown",
                    full_text,
                    info.duration,
                )

            return full_text if full_text else None

        except Exception as e:
            logger.error("Transcription error: %s", e)
            return None
