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

    # Temporary voice channel configuration
    TEMP_VOICE_TRIGGER_CHANNEL_ID: Optional[int] = None
    _tv_trigger: str = os.getenv("TEMP_VOICE_TRIGGER_CHANNEL_ID", "")
    if _tv_trigger.strip():
        try:
            TEMP_VOICE_TRIGGER_CHANNEL_ID = int(_tv_trigger.strip())
        except ValueError:
            logger.warning("TEMP_VOICE_TRIGGER_CHANNEL_ID must be an integer; ignoring.")

    TEMP_VOICE_CATEGORY_ID: Optional[int] = None
    _tv_cat: str = os.getenv("TEMP_VOICE_CATEGORY_ID", "")
    if _tv_cat.strip():
        try:
            TEMP_VOICE_CATEGORY_ID = int(_tv_cat.strip())
        except ValueError:
            logger.warning("TEMP_VOICE_CATEGORY_ID must be an integer; ignoring.")

    # TempVoice: customizable welcome message shown when user gets their temp VC
    TEMP_VOICE_WELCOME_MESSAGE: str = os.getenv(
        "TEMP_VOICE_WELCOME_MESSAGE",
        "Welcome To Your Pvt Space, If anyone force enters vc report the, to management!",
    )

    # TempVoice: optional path to instruction image (replaces text legend in interface embed)
    TEMP_VOICE_INSTRUCTION_IMAGE_PATH: str = os.getenv("TEMP_VOICE_INSTRUCTION_IMAGE_PATH", "").strip()

    # TempVoice: optional text channel where the VC management interface is sent
    TEMP_VOICE_INTERFACE_CHANNEL_ID: Optional[int] = None
    _tv_interface: str = os.getenv("TEMP_VOICE_INTERFACE_CHANNEL_ID", "")
    if _tv_interface.strip():
        try:
            TEMP_VOICE_INTERFACE_CHANNEL_ID = int(_tv_interface.strip())
        except ValueError:
            logger.warning("TEMP_VOICE_INTERFACE_CHANNEL_ID must be an integer; ignoring.")

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
