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

    _model: Optional[WhisperModel] = None  # Singleton pattern for model caching

    @classmethod
    def get_model(cls) -> WhisperModel:
        """Get or initialize the Whisper model (lazy-loaded singleton)."""
        if cls._model is None:
            logger.info(
                f"Loading Whisper model '{Config.WHISPER_MODEL}' on device '{Config.WHISPER_DEVICE}' "
                f"with compute type '{Config.WHISPER_COMPUTE_TYPE}' (this may take a moment on first run)..."
            )
            cls._model = WhisperModel(
                Config.WHISPER_MODEL,
                device=Config.WHISPER_DEVICE,
                compute_type=Config.WHISPER_COMPUTE_TYPE,
            )
            logger.debug("Whisper model loaded successfully.")
        return cls._model

    @classmethod
    def reset_model(cls) -> None:
        """Clear cached model from memory (useful for testing/restart)."""
        if cls._model is not None:
            del cls._model
            cls._model = None
            logger.debug("Whisper model reset.")

    @classmethod
    def is_model_loaded(cls) -> bool:
        """Check if the Whisper model is already loaded in memory."""
        return cls._model is not None

    @staticmethod
    def _get_vad_parameters() -> dict:
        """Get Voice Activity Detection parameters from configuration."""
        return {
            "min_silence_duration_ms": Config.WHISPER_VAD_MIN_SILENCE_MS,
            "speech_pad_ms": Config.WHISPER_VAD_SPEECH_PAD_MS,
        }



    def transcribe_wav(self, wav_bytes: bytes) -> Optional[str]:
        """
        Transcribe WAV audio bytes to text.

        Args:
            wav_bytes: Raw WAV file bytes from a voice recording sink (e.g. WAV export).

        Returns:
            Transcribed text string, or None if no speech detected.
        """
        model = self.get_model()
        
        try:
            # Use context manager for explicit resource handling
            with io.BytesIO(wav_bytes) as audio_file:
                # language=None enables auto language detection
                segments, info = model.transcribe(
                    audio_file,
                    language=None,
                    vad_filter=True,
                    vad_parameters=self._get_vad_parameters(),
                )

                text_parts: list[str] = []
                for segment in segments:
                    text_parts.append(segment.text.strip())

                full_text: str = " ".join(text_parts).strip()

            # Early return for empty text
            if not full_text:
                logger.debug(f"No speech detected in audio (duration: {info.duration:.1f}s)")
                return None

            language = info.language or "unknown"
            logger.info(
                f"Transcribed [{language}]: '{full_text}' ({info.duration:.1f}s audio)"
            )
            return full_text

        except ValueError as e:
            logger.error(f"Invalid audio data provided to transcriber: {e}")
            return None
        except RuntimeError as e:
            logger.error(f"Transcription inference failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected transcription error: {e}")
            return None
