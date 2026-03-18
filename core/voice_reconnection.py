"""
Voice Reconnection Manager — automatic Discord voice channel reconnection.

Monitors active voice connections, detects disconnections, and attempts
automatic reconnection with exponential backoff and maximum retry limits.
Prevents cascading reconnection loops through state tracking.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


@dataclass
class VoiceConnectionState:
    """Tracks state for a guild's voice connection."""
    guild_id: int
    channel_id: Optional[int] = None
    is_connected: bool = False
    last_disconnected: Optional[datetime] = None
    reconnect_attempts: int = 0
    last_reconnect_attempt: Optional[datetime] = None
    backoff_delay: float = 1.0
    is_reconnecting: bool = False
    error_message: str = ""
    last_error_time: Optional[datetime] = None


class VoiceReconnectionManager:
    """Manages automatic voice channel reconnection with exponential backoff."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize reconnection manager."""
        self.bot = bot
        self.guild_states: dict[int, VoiceConnectionState] = {}
        
        # Configuration
        self.max_reconnect_attempts = 5
        self.initial_backoff = 1.0  # seconds
        self.max_backoff = 30.0  # seconds
        self.backoff_multiplier = 2.0
        self.connection_timeout = 10.0  # seconds to wait for connection
        self.monitoring_interval = 5.0  # seconds between connection checks
        
        # Active monitoring task
        self._monitor_task: Optional[asyncio.Task] = None
    
    def start(self) -> None:
        """Start the reconnection monitoring system."""
        if self._monitor_task:
            return
        
        self._monitor_task = asyncio.create_task(self._monitor_connections())
        logger.info("Voice reconnection manager started")
    
    def stop(self) -> None:
        """Stop the reconnection monitoring system."""
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
            logger.info("Voice reconnection manager stopped")
    
    async def _monitor_connections(self) -> None:
        """Periodically check all guild voice connections for disconnection."""
        try:
            while True:
                try:
                    await asyncio.sleep(self.monitoring_interval)
                    
                    # Check each guild
                    for guild in self.bot.guilds:
                        state = self.guild_states.get(guild.id)
                        if not state:
                            continue
                        
                        # Get current voice client
                        voice_client = guild.voice_client
                        
                        # Track connection status
                        was_connected = state.is_connected
                        is_connected = voice_client and voice_client.is_connected()
                        state.is_connected = is_connected
                        
                        # Detect disconnection
                        if was_connected and not is_connected and not state.is_reconnecting:
                            state.last_disconnected = datetime.now()
                            logger.warning(
                                f"Voice disconnection detected for guild {guild.id} "
                                f"(channel {state.channel_id})"
                            )
                            
                            # Attempt reconnection
                            asyncio.create_task(self._attempt_reconnect(guild))
                        
                        # Update connection status if currently connected
                        if is_connected and voice_client:
                            state.channel_id = voice_client.channel.id
                            state.reconnect_attempts = 0
                            state.error_message = ""
                
                except Exception as e:
                    logger.error(f"Error in voice connection monitoring: {e}")
        
        except asyncio.CancelledError:
            logger.debug("Voice monitoring task cancelled")
        except Exception as e:
            logger.error(f"Unexpected error in voice monitoring: {e}")
    
    async def _attempt_reconnect(self, guild: discord.Guild) -> None:
        """Attempt to reconnect a guild's voice connection."""
        state = self.guild_states.get(guild.id)
        if not state or not state.channel_id:
            return
        
        # Check if already reconnecting
        if state.is_reconnecting:
            logger.debug(f"Guild {guild.id} already has a reconnection in progress")
            return
        
        state.is_reconnecting = True
        
        try:
            # Get the target channel
            channel = guild.get_channel(state.channel_id)
            if not channel or not isinstance(channel, discord.VoiceChannel):
                logger.warning(
                    f"Cannot reconnect to channel {state.channel_id}: channel not found or not a voice channel"
                )
                state.channel_id = None
                state.is_reconnecting = False
                return
            
            # Check if we've exceeded max retry attempts
            if state.reconnect_attempts >= self.max_reconnect_attempts:
                logger.error(
                    f"Max reconnection attempts ({self.max_reconnect_attempts}) "
                    f"reached for guild {guild.id}. Giving up."
                )
                state.error_message = "Max reconnection attempts exceeded"
                state.is_reconnecting = False
                return
            
            # Apply exponential backoff
            backoff = min(
                self.initial_backoff * (self.backoff_multiplier ** state.reconnect_attempts),
                self.max_backoff
            )
            state.backoff_delay = backoff
            
            logger.info(
                f"Attempt {state.reconnect_attempts + 1}/{self.max_reconnect_attempts} "
                f"to reconnect guild {guild.id} to channel {state.channel_id} "
                f"(waiting {backoff:.1f}s)"
            )
            
            await asyncio.sleep(backoff)
            
            # Attempt the connection
            state.last_reconnect_attempt = datetime.now()
            state.reconnect_attempts += 1
            
            try:
                voice_client = await channel.connect(timeout=self.connection_timeout, reconnect=True)
                logger.info(f"Successfully reconnected guild {guild.id} to channel {state.channel_id}")
                state.reconnect_attempts = 0
                state.error_message = ""
                
            except asyncio.TimeoutError:
                logger.warning(
                    f"Connection timeout while reconnecting guild {guild.id} "
                    f"to channel {state.channel_id}"
                )
                state.error_message = "Connection timeout"
                
            except discord.ClientException as e:
                logger.warning(
                    f"Discord error while reconnecting guild {guild.id}: {e}"
                )
                state.error_message = f"Discord error: {str(e)[:50]}"
                
            except Exception as e:
                logger.warning(
                    f"Unexpected error while reconnecting guild {guild.id}: {e}"
                )
                state.error_message = f"Error: {str(e)[:50]}"
        
        finally:
            state.is_reconnecting = False
    
    def register_guild(self, guild: discord.Guild, channel: discord.VoiceChannel) -> None:
        """Register a guild for voice reconnection monitoring."""
        if guild.id not in self.guild_states:
            self.guild_states[guild.id] = VoiceConnectionState(
                guild_id=guild.id,
                channel_id=channel.id,
                is_connected=True
            )
            logger.debug(f"Registered guild {guild.id} for voice monitoring")
        else:
            state = self.guild_states[guild.id]
            state.channel_id = channel.id
            state.is_connected = True
    
    def unregister_guild(self, guild_id: int) -> None:
        """Unregister a guild from voice monitoring."""
        if guild_id in self.guild_states:
            del self.guild_states[guild_id]
            logger.debug(f"Unregistered guild {guild_id} from voice monitoring")
    
    def get_state(self, guild_id: int) -> Optional[VoiceConnectionState]:
        """Get the voice connection state for a guild."""
        return self.guild_states.get(guild_id)
    
    def reset_guild_state(self, guild_id: int) -> None:
        """Reset reconnection state for a guild (safe manual reset)."""
        if guild_id in self.guild_states:
            state = self.guild_states[guild_id]
            state.reconnect_attempts = 0
            state.backoff_delay = self.initial_backoff
            state.error_message = ""
            logger.info(f"Reset reconnection state for guild {guild_id}")
    
    async def get_status_embed(self, guild_id: int) -> discord.Embed:
        """Get a nice embed showing voice connection status."""
        state = self.get_state(guild_id)
        
        embed = discord.Embed(
            title="🔊 Voice Connection Status",
            color=discord.Color.green() if (state and state.is_connected) else discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        
        if not state:
            embed.add_field(name="Status", value="❌ Not monitored", inline=False)
            return embed
        
        status = "✅ Connected" if state.is_connected else "❌ Disconnected"
        embed.add_field(name="Status", value=status, inline=False)
        
        if state.channel_id:
            embed.add_field(name="Channel ID", value=f"`{state.channel_id}`", inline=True)
        
        embed.add_field(
            name="Reconnect Attempts",
            value=f"{state.reconnect_attempts}/{self.max_reconnect_attempts}",
            inline=True
        )
        
        if state.is_reconnecting:
            embed.add_field(
                name="Status",
                value="⏳ Reconnection in progress...",
                inline=False
            )
        
        if state.error_message:
            embed.add_field(
                name="Last Error",
                value=f"`{state.error_message}`",
                inline=False
            )
        
        if state.last_disconnected:
            embed.add_field(
                name="Last Disconnection",
                value=f"<t:{int(state.last_disconnected.timestamp())}:R>",
                inline=True
            )
        
        if state.last_reconnect_attempt:
            embed.add_field(
                name="Last Reconnect Attempt",
                value=f"<t:{int(state.last_reconnect_attempt.timestamp())}:R>",
                inline=True
            )
        
        return embed
