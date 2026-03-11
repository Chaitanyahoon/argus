"""
TempVoice — temporary voice channel manager.

When a user joins a designated "Create VC" channel, creates a personal
voice channel, moves the user into it, grants admin permissions, and
sends a management interface. Cleans up empty temp channels.
"""

import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO

import discord

logger = logging.getLogger(__name__)

# Google Drive view URL pattern: /file/d/FILE_ID/ or /file/d/FILE_ID
_GDRIVE_FILE_ID_RE = re.compile(r"drive\.google\.com/file/d/([a-zA-Z0-9_-]+)")


async def _resolve_instruction_image(
    config_value: str,
    attachment_filename: str,
) -> tuple[discord.File | None, bool]:
    """
    Resolve instruction image from config: local path or URL (including Google Drive).
    Returns (file to attach, use_instruction_image).
    """
    if not config_value or not config_value.strip():
        return None, False
    config_value = config_value.strip()

    # URL: download and return a File built from bytes
    if config_value.startswith("http://") or config_value.startswith("https://"):
        url = config_value
        m = _GDRIVE_FILE_ID_RE.search(url)
        if m:
            url = f"https://drive.google.com/uc?export=download&id={m.group(1)}"
        try:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        logger.warning("TempVoice: instruction image URL returned %s", resp.status)
                        return None, False
                    data = await resp.read()
            if not data or len(data) < 100:
                logger.warning("TempVoice: instruction image download too small or empty")
                return None, False
            f = discord.File(BytesIO(data), filename=attachment_filename)
            return f, True
        except Exception as e:
            logger.warning("TempVoice: could not download instruction image from URL: %s", e)
            return None, False

    # Local path
    if os.path.isfile(config_value):
        try:
            return discord.File(config_value, filename=attachment_filename), True
        except Exception as e:
            logger.warning("TempVoice: could not open instruction image file: %s", e)
            return None, False
    return None, False


@dataclass
class TempChannelData:
    """Metadata for a temporary voice channel."""

    owner_id: int
    channel_id: int
    interface_message_id: int | None
    created_at: datetime
    interface_channel_id: int | None = None  # channel where interface was sent (for cleanup)
    locked: bool = False
    hidden: bool = False
    waiting_room: bool = False
    user_limit: int = 0
    banned_ids: set[int] = field(default_factory=set)
    permitted_ids: set[int] = field(default_factory=set)


class TempVoiceManager:
    """
    Manages temporary voice channels: creation, tracking, and cleanup.
    """

    def __init__(self, bot: discord.Client, argus_manager=None):
        self.bot = bot
        self.argus_manager = argus_manager
        self.temp_channels: dict[int, TempChannelData] = {}

    def _get_config(self, guild_id: int) -> dict:
        if not self.argus_manager:
            return {}
        return self.argus_manager.db.get_guild(guild_id) or {}

    def _get_category(self, guild: discord.Guild) -> discord.CategoryChannel | None:
        """Resolve category for creating temp channels."""
        config = self._get_config(guild.id)
        cat_id = config.get('temp_voice_category_id')
        if cat_id:
            return guild.get_channel(cat_id)
        return None

    def _get_first_text_channel(self, category: discord.CategoryChannel) -> discord.TextChannel | None:
        """First text channel in category for sending the interface."""
        for ch in category.channels:
            if isinstance(ch, discord.TextChannel):
                return ch
        return None

    async def create_temp_channel(self, member: discord.Member) -> None:
        """
        Create a temporary voice channel for the member, set overwrites,
        move the member, and send the management interface.
        """
        guild = member.guild
        category = self._get_category(guild)
        if not category:
            logger.warning("TempVoice: no category configured; cannot create temp channel.")
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=True, view_channel=True, speak=True),
            member: discord.PermissionOverwrite(
                connect=True,
                speak=True,
                mute_members=True,
                deafen_members=True,
                move_members=True,
                manage_channels=True,
                manage_permissions=True,
                view_channel=True,
            ),
        }

        channel_name = f"{member.display_name}'s VC"
        try:
            channel = await category.create_voice_channel(channel_name, overwrites=overwrites)
        except discord.Forbidden as e:
            logger.error("TempVoice: cannot create channel: %s", e)
            return
        except discord.HTTPException as e:
            logger.error("TempVoice: create channel HTTP error: %s", e)
            return

        data = TempChannelData(
            owner_id=member.id,
            channel_id=channel.id,
            interface_message_id=None,
            created_at=datetime.utcnow(),
        )
        self.temp_channels[channel.id] = data

        try:
            await member.move_to(channel)
        except discord.HTTPException as e:
            logger.error("TempVoice: move member failed: %s", e)
            # Channel still created; cleanup on empty
            return

        # Send welcome + interface: prefer voice channel chat (so it shows in "voice chat" panel), else text channel, else DM
        from config import Config
        from .temp_voice_ui import (
            INSTRUCTION_IMAGE_ATTACHMENT_NAME,
            build_temp_voice_embed,
            build_welcome_embed,
            TempVoiceView,
        )

        welcome_embed = build_welcome_embed(Config.TEMP_VOICE_WELCOME_MESSAGE)
        instruction_file, use_instruction_image = await _resolve_instruction_image(
            Config.TEMP_VOICE_INSTRUCTION_IMAGE_PATH,
            INSTRUCTION_IMAGE_ATTACHMENT_NAME,
        )
        interface_embed = build_temp_voice_embed(channel, use_instruction_image=use_instruction_image)
        files: list[discord.File] = []
        if instruction_file:
            files.append(instruction_file)
            interface_embed.set_image(url=f"attachment://{INSTRUCTION_IMAGE_ATTACHMENT_NAME}")

        welcome_text = f"**Welcome to {channel.mention}!** This is the start of the {channel.name} channel."

        sent = False
        # Do not post to the interface channel here; that channel has one shared message (see !postvcinterface).
        # Always try to send to the voice channel so it appears in the VC chat panel
        view_vc = TempVoiceView(self, channel, timeout=None)
        try:
            await channel.send(
                welcome_text,
                embeds=[welcome_embed, interface_embed],
                view=view_vc,
                files=files or None,
            )
            sent = True
            logger.info("TempVoice: sent interface to voice channel %s", channel.name)
        except (AttributeError, discord.HTTPException) as e:
            logger.debug("TempVoice: cannot send to voice channel (%s), trying text channel or DM", e)

        if not sent:
            text_channel = self._get_first_text_channel(category)
            if text_channel:
                try:
                    view_fallback = TempVoiceView(self, channel, timeout=None)
                    msg = await text_channel.send(
                        welcome_text,
                        embeds=[welcome_embed, interface_embed],
                        view=view_fallback,
                        files=files or None,
                    )
                    if data.interface_message_id is None:
                        data.interface_message_id = msg.id
                        data.interface_channel_id = text_channel.id
                    sent = True
                except Exception as e:
                    logger.error("TempVoice: send interface failed: %s", e)
            if not sent:
                try:
                    view_dm = TempVoiceView(self, channel, timeout=None)
                    await member.send(
                        welcome_text,
                        embeds=[welcome_embed, interface_embed],
                        view=view_dm,
                        files=files or None,
                    )
                    logger.info("TempVoice: sent interface via DM to %s", member.display_name)
                except discord.Forbidden:
                    logger.warning("TempVoice: cannot DM %s (DMs disabled).", member.display_name)
                except Exception as e:
                    logger.error("TempVoice: send interface via DM failed: %s", e)

        logger.info("TempVoice: created %s for %s", channel.name, member.display_name)

    async def check_cleanup(self, channel: discord.VoiceChannel) -> None:
        """If the channel is a temp channel and empty, delete it and remove from tracking."""
        if channel.id not in self.temp_channels:
            return
        if len(channel.members) > 0:
            return

        data = self.temp_channels.pop(channel.id)
        try:
            await channel.delete(reason="TempVoice: channel empty")
        except discord.HTTPException as e:
            logger.error("TempVoice: delete channel failed: %s", e)
            self.temp_channels[channel.id] = data
            return

        # Try to remove interface message if we know where it is
        if data.interface_message_id:
            guild = channel.guild
            ch = None
            if data.interface_channel_id:
                ch = guild.get_channel(data.interface_channel_id)
            
            config = self._get_config(guild.id)
            cat_id = config.get('temp_voice_category_id')
            if ch is None and cat_id:
                cat = guild.get_channel(cat_id)
                if cat and isinstance(cat, discord.CategoryChannel):
                    ch = self._get_first_text_channel(cat)
            if ch and isinstance(ch, discord.TextChannel):
                try:
                    msg = await ch.fetch_message(data.interface_message_id)
                    await msg.delete()
                except (discord.NotFound, discord.HTTPException):
                    pass

        logger.info("TempVoice: deleted empty channel %s", channel.name)

    def get_data(self, channel_id: int) -> TempChannelData | None:
        return self.temp_channels.get(channel_id)

    def is_owner(self, channel_id: int, user_id: int) -> bool:
        data = self.get_data(channel_id)
        return data is not None and data.owner_id == user_id

    def get_owned_channel_id(self, user_id: int) -> int | None:
        """Return the temp VC channel id that this user owns, or None."""
        for ch_id, data in self.temp_channels.items():
            if data.owner_id == user_id:
                return ch_id
        return None

    def set_owner(self, channel_id: int, new_owner_id: int) -> None:
        data = self.get_data(channel_id)
        if data:
            data.owner_id = new_owner_id
