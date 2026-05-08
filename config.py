"""
Configuration — loads environment variables from .env file.
Provides centralized configuration management with type hints and validation.
"""

import os
import sys
import logging
from typing import Optional, Set

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Bot configuration from environment variables with type hints."""

    # Required configuration
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Admin user IDs (comma-separated integers)
    ADMIN_USER_IDS: Set[int] = set()
    _raw_admin_ids: str = os.getenv("ADMIN_USER_IDS", "")
    if _raw_admin_ids:
        try:
            ADMIN_USER_IDS = {int(uid.strip()) for uid in _raw_admin_ids.split(",") if uid.strip()}
        except ValueError:
            logger.error("ADMIN_USER_IDS must be comma-separated integers.")
            sys.exit(1)

    COMMAND_PREFIX: str = os.getenv("COMMAND_PREFIX", "!")

    # Whisper model for speech-to-text
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base.en")
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu")  # "cpu" or "cuda"
    WHISPER_COMPUTE_TYPE: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")  # "int8", "float16", "float32"
    
    # Whisper VAD (Voice Activity Detection) parameters
    WHISPER_VAD_MIN_SILENCE_MS: int = int(os.getenv("WHISPER_VAD_MIN_SILENCE_MS", "300"))
    WHISPER_VAD_SPEECH_PAD_MS: int = int(os.getenv("WHISPER_VAD_SPEECH_PAD_MS", "200"))

    GEMINI_VOICE: str = os.getenv("GEMINI_VOICE", "Aoede")

    # Logging level
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    if LOG_LEVEL not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        logger.warning("Invalid LOG_LEVEL '%s'; using INFO instead.", LOG_LEVEL)
        LOG_LEVEL = "INFO"

    @classmethod
    def validate(cls) -> None:
        """
        Validate critical configuration at startup.
        
        Raises:
            SystemExit: If required configuration is missing
        """
        errors: list[str] = []
        
        if not cls.DISCORD_TOKEN:
            errors.append("DISCORD_TOKEN is not set. Get it from https://discord.com/developers/applications")
        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is not set. Get it from https://aistudio.google.com/app/apikey")
        if not cls.ADMIN_USER_IDS:
            errors.append("ADMIN_USER_IDS is not set. Use comma-separated user IDs (e.g., 123456789,987654321)")
        
        if errors:
            for e in errors:
                logger.error("❌ Config error: %s", e)
            logger.error("\nCheck your .env file or environment variables.")
            logger.error("You can use .env.example as a template.\n")
            sys.exit(1)
        
        logger.info("✅ Configuration validated successfully.")
