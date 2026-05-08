"""
Voice Session Timeout Manager — automatic disconnection after inactivity.

Tracks active voice sessions, monitors for inactivity, and automatically
disconnects the bot from voice channels after a configurable timeout period.
Prevents resource waste from forgotten sessions.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Any

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


@dataclass
class VoiceSession:
    """Represents an active voice session in a guild."""
    guild_id: int
    channel_id: int
    started_at: datetime
    last_activity: datetime = field(default_factory=datetime.now)
    is_listening: bool = False  # Is in Gemini Live conversation
    inactivity_warnings_sent: int = 0
    
    def get_duration(self) -> timedelta:
        """Get total session duration."""
        return datetime.now() - self.started_at
    
    def get_inactivity_time(self) -> timedelta:
        """Get time since last activity."""
        return datetime.now() - self.last_activity
    
    def is_idle(self, timeout_seconds: int) -> bool:
        """Check if session has been idle for longer than timeout."""
        return self.get_inactivity_time().total_seconds() > timeout_seconds


class VoiceSessionTimeoutManager:
    """Manage voice session timeouts with idle detection."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize session timeout manager."""
        self.bot = bot
        self.sessions: dict[int, VoiceSession] = {}  # guild_id -> VoiceSession
        
        # Configuration
        self.default_inactivity_timeout = 600  # 10 minutes
        self.warning_threshold = 480  # Warn at 8 minutes
        self.check_interval = 30  # Check every 30 seconds
        
        # Active monitoring task
        self._monitor_task: Optional[asyncio.Task] = None
    
    def start(self) -> None:
        """Start the session timeout monitoring system."""
        if self._monitor_task:
            return
        
        self._monitor_task = asyncio.create_task(self._monitor_sessions())
        logger.info("Voice session timeout manager started")
    
    def stop(self) -> None:
        """Stop the session timeout monitoring system."""
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
            logger.info("Voice session timeout manager stopped")
    
    async def _monitor_sessions(self) -> None:
        """Periodically check all voice sessions for inactivity."""
        try:
            while True:
                try:
                    await asyncio.sleep(self.check_interval)
                    
                    # Check each session
                    for guild_id in list(self.sessions.keys()):
                        session = self.sessions[guild_id]
                        guild = self.bot.get_guild(guild_id)
                        
                        if not guild:
                            del self.sessions[guild_id]
                            continue
                        
                        # Get voice client
                        voice_client = guild.voice_client
                        if not voice_client or not voice_client.is_connected():
                            # Voice connection lost, remove session
                            del self.sessions[guild_id]
                            continue
                        
                        # Get timeout for this guild
                        timeout = self._get_guild_timeout(guild_id)
                        
                        # Check for timeout (music playback removed; only listening state prevents timeout)
                        if session.is_idle(timeout) and not session.is_listening:
                            logger.warning(
                                f"Voice session timeout for guild {guild_id} "
                                f"(idle for {session.get_inactivity_time().total_seconds():.0f}s)"
                            )
                            await self._disconnect_session(guild, session)
                            del self.sessions[guild_id]
                        
                        # Check for warning threshold
                        elif session.get_inactivity_time().total_seconds() > self.warning_threshold:
                            if session.inactivity_warnings_sent == 0:
                                await self._send_warning(guild, session)
                                session.inactivity_warnings_sent += 1
                
                except Exception as e:
                    logger.error(f"Error in voice session monitoring: {e}")
        
        except asyncio.CancelledError:
            logger.debug("Voice session monitoring task cancelled")
        except Exception as e:
            logger.error(f"Unexpected error in session monitoring: {e}")
    
    async def _disconnect_session(self, guild: discord.Guild, session: VoiceSession) -> None:
        """Disconnect a voice session due to timeout."""
        try:
            if guild.voice_client:
                await guild.voice_client.disconnect()
                logger.info(f"Disconnected voice session in guild {guild.id} due to inactivity")
        except Exception as e:
            logger.warning(f"Error disconnecting voice session: {e}")
    
    async def _send_warning(self, guild: discord.Guild, session: VoiceSession) -> None:
        """Send a warning about upcoming timeout."""
        try:
            # Get the first text channel we can send to
            if guild.voice_client and guild.voice_client.channel:
                remaining = self.default_inactivity_timeout - int(session.get_inactivity_time().total_seconds())
                
                embed = discord.Embed(
                    title="⏰ Inactivity Warning",
                    description=f"I've been idle for a while. I'll disconnect in {remaining // 60} minutes if there's no activity.",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                
                # Try to send in a text channel
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        try:
                            await channel.send(embed=embed)
                            return
                        except Exception:
                            continue
        except Exception as e:
            logger.debug(f"Could not send inactivity warning: {e}")
    
    def start_session(self, guild: discord.Guild, channel: discord.VoiceChannel) -> None:
        """Start tracking a new voice session."""
        guild_id = guild.id
        
        if guild_id in self.sessions:
            # Update existing session
            session = self.sessions[guild_id]
            session.channel_id = channel.id
            session.started_at = datetime.now()
            session.last_activity = datetime.now()
            session.inactivity_warnings_sent = 0
        else:
            # Create new session
            self.sessions[guild_id] = VoiceSession(
                guild_id=guild_id,
                channel_id=channel.id,
                started_at=datetime.now()
            )
        
        logger.info(f"Started voice session for guild {guild_id} in channel {channel.id}")
    
    def end_session(self, guild_id: int) -> None:
        """End a voice session."""
        if guild_id in self.sessions:
            del self.sessions[guild_id]
            logger.info(f"Ended voice session for guild {guild_id}")
    
    def update_activity(self, guild_id: int) -> None:
        """Update last activity timestamp for a session."""
        if guild_id in self.sessions:
            self.sessions[guild_id].last_activity = datetime.now()
            self.sessions[guild_id].inactivity_warnings_sent = 0  # Reset warnings
    
    def set_listening(self, guild_id: int, is_listening: bool) -> None:
        """Mark session as in active conversation or idle."""
        if guild_id in self.sessions:
            self.sessions[guild_id].is_listening = is_listening
    
    def set_playing_music(self, guild_id: int, is_playing: bool) -> None:
        """Music playback tracking removed; kept no-op for compatibility."""
        return
    
    def _get_guild_timeout(self, guild_id: int) -> int:
        """Get configured timeout for a guild (in seconds)."""
        # TODO: Load from database if implementing per-guild timeouts
        return self.default_inactivity_timeout
    
    def _load_config(self, guild_id: int, db: Any) -> dict:
        """Load timeout configuration from database."""
        guild_data = db.get_guild(guild_id) if hasattr(db, 'get_guild') else None
        if guild_data and 'session_timeout' in guild_data:
            return guild_data['session_timeout']
        
        return {
            'inactivity_timeout': self.default_inactivity_timeout,
            'warning_threshold': self.warning_threshold,
            'enabled': True
        }
    
    def _save_config(self, guild_id: int, db: Any, config: dict) -> None:
        """Save timeout configuration to database."""
        if hasattr(db, 'set_guild_field'):
            db.set_guild_field(guild_id, 'session_timeout', config)
    
    def set_timeout(self, guild_id: int, seconds: int, db: Any) -> None:
        """Set inactivity timeout for a guild."""
        if seconds < 60:
            raise ValueError("Timeout must be at least 60 seconds (1 minute)")
        if seconds > 3600:
            raise ValueError("Timeout cannot exceed 3600 seconds (1 hour)")
        
        config = self._load_config(guild_id, db)
        config['inactivity_timeout'] = seconds
        self._save_config(guild_id, db, config)
        
        # Update in-memory config
        self.default_inactivity_timeout = seconds
        logger.info(f"Set session timeout to {seconds}s for guild {guild_id}")
    
    def get_session(self, guild_id: int) -> Optional[VoiceSession]:
        """Get active session for a guild."""
        return self.sessions.get(guild_id)
    
    def get_all_sessions(self) -> dict[int, VoiceSession]:
        """Get all active sessions."""
        return self.sessions.copy()
    
    async def get_status_embed(self, guild_id: int) -> discord.Embed:
        """Get a formatted embed showing session status."""
        session = self.get_session(guild_id)
        timeout = self._get_guild_timeout(guild_id)
        
        embed = discord.Embed(
            title="🎤 Voice Session Status",
            color=discord.Color.blue() if session else discord.Color.gray(),
            timestamp=discord.utils.utcnow()
        )
        
        if not session:
            embed.description = "No active voice session"
            embed.add_field(
                name="Inactivity Timeout",
                value=f"{timeout // 60} minutes ({timeout}s)",
                inline=False
            )
            return embed
        
        embed.description = "Active voice session"
        
        # Session info
        embed.add_field(
            name="Duration",
            value=f"{int(session.get_duration().total_seconds())} seconds",
            inline=True
        )
        
        embed.add_field(
            name="Inactivity",
            value=f"{int(session.get_inactivity_time().total_seconds())} seconds",
            inline=True
        )
        
        # Status indicators
        status = ("🗣️" if session.is_listening else "😴")
        embed.add_field(
            name="Mode",
            value=f"{status} {'Listening' if session.is_listening else 'Idle'}",
            inline=True
        )
        
        # Timeout info
        embed.add_field(
            name="Timeout Threshold",
            value=f"{timeout // 60} minutes ({timeout}s)",
            inline=True
        )
        
        remaining = timeout - int(session.get_inactivity_time().total_seconds())
        status_bar = "🟩" * max(1, remaining // 60) + "🟪" * max(1, (timeout - remaining) // 60)
        
        embed.add_field(
            name="Inactivity Timer",
            value=f"{status_bar}\n{max(0, remaining)}s remaining",
            inline=False
        )
        
        # Warning status
        if session.inactivity_warnings_sent > 0:
            embed.add_field(
                name="⚠️ Status",
                value=f"Inactivity warning sent",
                inline=False
            )
        
        return embed
