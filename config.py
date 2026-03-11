"""
Configuration — loads environment variables from .env file.
"""

import os
import sys
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Bot configuration from environment variables."""

    # Required
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Admin user IDs (comma-separated integers)
    ADMIN_USER_IDS: set[int] = set()
    _raw_admin_ids = os.getenv("ADMIN_USER_IDS", "")
    if _raw_admin_ids:
        try:
            ADMIN_USER_IDS = {int(uid.strip()) for uid in _raw_admin_ids.split(",") if uid.strip()}
        except ValueError:
            logger.error("ADMIN_USER_IDS must be comma-separated integers.")
            sys.exit(1)

    COMMAND_PREFIX: str = os.getenv("COMMAND_PREFIX", "!")

    
    GEMINI_VOICE: str = os.getenv("GEMINI_VOICE", "Aoede")


    TEMP_VOICE_TRIGGER_CHANNEL_ID: int | None = None
    _tv_trigger = os.getenv("TEMP_VOICE_TRIGGER_CHANNEL_ID", "")
    if _tv_trigger.strip():
        try:
            TEMP_VOICE_TRIGGER_CHANNEL_ID = int(_tv_trigger.strip())
        except ValueError:
            logger.warning("TEMP_VOICE_TRIGGER_CHANNEL_ID must be an integer; ignoring.")

    TEMP_VOICE_CATEGORY_ID: int | None = None
    _tv_cat = os.getenv("TEMP_VOICE_CATEGORY_ID", "")
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

    # TempVoice: optional text channel where the VC management interface is sent (users manage their VC from here)
    TEMP_VOICE_INTERFACE_CHANNEL_ID: int | None = None
    _tv_interface = os.getenv("TEMP_VOICE_INTERFACE_CHANNEL_ID", "")
    if _tv_interface.strip():
        try:
            TEMP_VOICE_INTERFACE_CHANNEL_ID = int(_tv_interface.strip())
        except ValueError:
            logger.warning("TEMP_VOICE_INTERFACE_CHANNEL_ID must be an integer; ignoring.")

    @classmethod
    def validate(cls) -> None:
        """Validate critical configuration."""
        errors = []
        if not cls.DISCORD_TOKEN:
            errors.append("DISCORD_TOKEN is not set.")
        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is not set.")
        if not cls.ADMIN_USER_IDS:
            errors.append("ADMIN_USER_IDS is not set.")
        if errors:
            for e in errors:
                logger.error("Config error: %s", e)
            sys.exit(1)
