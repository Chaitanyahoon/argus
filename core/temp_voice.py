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
            logger.warning("TempVoice: cannot create temp channel for %s — category not configured", member.display_name)
            try:
                await member.send("❌ **TempVoice not configured.** Your server admin needs to run `!autosetup` or `!settempvcategory`.")
            except discord.Forbidden:
                pass
            return

        # Check for permission issues before attempting creation
        bot_perms = category.permissions_for(guild.me)
        if not bot_perms.manage_channels:
            logger.error("TempVoice: bot lacks manage_channels permission in category %s", category.name)
            try:
                await member.send("❌ **Permission Error:** I don't have `manage_channels` permission in the TempVoice category.")
            except discord.Forbidden:
                pass
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

        # Sanitize channel name to avoid special characters
        channel_name = f"{member.display_name}'s VC"
        channel_name = channel_name.replace("*", "").replace("_", " ").replace("`", "")[:100]
        
        try:
            channel = await category.create_voice_channel(channel_name, overwrites=overwrites)
            logger.info("TempVoice: created voice channel %s for %s", channel.name, member.display_name)
        except discord.Forbidden as e:
            logger.error("TempVoice: permission denied creating channel: %s", e)
            try:
                await member.send("❌ **Permission Error:** I don't have permission to create voice channels.")
            except discord.Forbidden:
                pass
            return
        except discord.HTTPException as e:
            logger.error("TempVoice: HTTP error creating channel: %s", e)
            try:
                await member.send(f"❌ **Error creating channel:** {str(e)[:100]}")
            except discord.Forbidden:
                pass
            return

        data = TempChannelData(
            owner_id=member.id,
            channel_id=channel.id,
            interface_message_id=None,
            created_at=datetime.utcnow(),
        )
        self.temp_channels[channel.id] = data

        # Move member to the new channel
        try:
            await member.move_to(channel)
            logger.info("TempVoice: moved %s to %s", member.display_name, channel.name)
        except discord.Forbidden:
            logger.error("TempVoice: permission denied moving member")
        except discord.HTTPException as e:
            logger.error("TempVoice: failed to move member to channel: %s", e)
            return

        # Send interface: text channel preferred (voice channel messages not supported)
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

        welcome_text = f"**Welcome to {channel.mention}!** This is your private temporary voice channel."

        sent = False
        
        # Try to send to a text channel in the category
        text_channel = self._get_first_text_channel(category)
        if text_channel:
            try:
                bot_perms_text = text_channel.permissions_for(guild.me)
                if bot_perms_text.send_messages and bot_perms_text.embed_links:
                    view_main = TempVoiceView(self, channel, timeout=None)
                    msg = await text_channel.send(
                        welcome_text,
                        embeds=[welcome_embed, interface_embed],
                        view=view_main,
                        files=files or None,
                    )
                    data.interface_message_id = msg.id
                    data.interface_channel_id = text_channel.id
                    sent = True
                    logger.info("TempVoice: sent interface to text channel %s", text_channel.name)
            except discord.HTTPException as e:
                logger.debug("TempVoice: failed to send to text channel: %s", e)

        # Fallback: send via DM
        if not sent:
            try:
                view_dm = TempVoiceView(self, channel, timeout=None)
                await member.send(
                    welcome_text,
                    embeds=[welcome_embed, interface_embed],
                    view=view_dm,
                    files=files or None,
                )
                sent = True
                logger.info("TempVoice: sent interface via DM to %s", member.display_name)
            except discord.Forbidden:
                logger.warning("TempVoice: cannot DM %s — DMs disabled", member.display_name)
            except discord.HTTPException as e:
                logger.error("TempVoice: failed to send interface via DM: %s", e)

        if sent:
            logger.info("TempVoice: successfully created and initialized %s", channel.name)
        else:
            logger.warning("TempVoice: created channel %s but could not send interface", channel.name)

    async def check_cleanup(self, channel: discord.VoiceChannel) -> None:
        """If the channel is a temp channel and empty, delete it and remove from tracking."""
        if channel.id not in self.temp_channels:
            return
        
        # Check if channel still has members
        if len(channel.members) > 0:
            return

        data = self.temp_channels.pop(channel.id)
        
        try:
            # Try to remove interface message first
            if data.interface_message_id:
                guild = channel.guild
                text_channel = None
                
                if data.interface_channel_id:
                    text_channel = guild.get_channel(data.interface_channel_id)
                
                # Fallback to finding first text channel in category
                if text_channel is None:
                    config = self._get_config(guild.id)
                    cat_id = config.get('temp_voice_category_id')
                    if cat_id:
                        cat = guild.get_channel(cat_id)
                        if cat and isinstance(cat, discord.CategoryChannel):
                            text_channel = self._get_first_text_channel(cat)
                
                if text_channel and isinstance(text_channel, discord.TextChannel):
                    try:
                        msg = await text_channel.fetch_message(data.interface_message_id)
                        await msg.delete()
                        logger.debug("TempVoice: deleted interface message %s", data.interface_message_id)
                    except (discord.NotFound, discord.HTTPException):
                        pass  # Message already deleted or channel inaccessible
            
            # Delete the voice channel
            await channel.delete(reason="TempVoice: channel empty")
            logger.info("TempVoice: cleaned up empty channel %s", channel.name)
            
        except discord.Forbidden:
            logger.error("TempVoice: permission denied deleting channel %s", channel.name)
            # Re-add to tracking since we couldn't delete it
            self.temp_channels[channel.id] = data
        except discord.HTTPException as e:
            logger.error("TempVoice: failed to delete channel %s: %s", channel.name, e)
            # Re-add to tracking since we couldn't delete it
            self.temp_channels[channel.id] = data

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

    @property
    def trigger_channel_id(self) -> int | None:
        """Return the first configured trigger channel ID (if any guild has one set)."""
        if not self.argus_manager or not hasattr(self.argus_manager, 'db'):
            return None
        try:
            all_guilds = self.argus_manager.db.get_all_guilds()
            if not all_guilds:
                return None
            for guild_row in all_guilds:
                # Handle both dict and Row-like objects
                guild_dict = dict(guild_row) if hasattr(guild_row, 'keys') else (guild_row if isinstance(guild_row, dict) else {})
                guild_data = guild_dict.get('data', {})
                if isinstance(guild_data, str):
                    import json
                    try:
                        guild_data = json.loads(guild_data)
                    except (json.JSONDecodeError, TypeError):
                        guild_data = {}
                if isinstance(guild_data, dict):
                    trigger_id = guild_data.get('temp_voice_trigger_id')
                    if trigger_id:
                        return int(trigger_id) if isinstance(trigger_id, str) else trigger_id
        except Exception as e:
            logger.debug("TempVoice: error getting trigger_channel_id: %s", e)
        return None
