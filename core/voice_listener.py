"""
Voice listener — real-time bidirectional audio pipeline between Discord
voice channels and the Gemini Live API.

Uses discord-ext-voice-recv for receiving user audio (VoiceRecvClient + BasicSink).
Captures audio from Discord → resamples → streams to Gemini.
Receives audio from Gemini → resamples → plays back in Discord.
"""

import asyncio
import logging
import time
import threading
from difflib import SequenceMatcher

import discord
from discord.ext import voice_recv
from discord.ext.voice_recv.router import PacketRouter
from discord.ext.voice_recv.reader import AudioReader
from discord.ext.voice_recv import rtp
from discord.opus import OpusError

try:
    import davey
    _HAS_DAVEY = True
except ImportError:
    _HAS_DAVEY = False

from config import Config
from .audio_utils import discord_to_gemini, PCMAudioSource, DISCORD_FRAME_SIZE
from .live_session import LiveSession
from .bot_utils import fuzzy_find_member, fuzzy_find_channel

logger = logging.getLogger(__name__)

# Suppress noisy library logs
logging.getLogger("discord.opus").setLevel(logging.CRITICAL)
logging.getLogger("discord.ext.voice_recv.reader").setLevel(logging.WARNING)
logging.getLogger("discord.ext.voice_recv.gateway").setLevel(logging.WARNING)

# Minimum bytes to send per chunk (1 frame = 20ms)
_CHUNK_BYTES = DISCORD_FRAME_SIZE  # 3840
_LOG_FIRST_N_RECEIVES = 5
_MAX_ROUTER_RESTARTS = 10
_RESTART_BASE_DELAY = 1.0  # seconds, will exponentially increase
_RESTART_MAX_DELAY = 30.0  # cap the backoff
_WARN_INTERVAL = 5.0  # seconds between corrupted-packet warnings
_MAX_SESSION_DURATION = 600  # 10 minutes session limit

# Minimum audio buffer before responding (5 seconds at 48kHz stereo, 32-bit)
# 5 seconds * 48000 Hz * 2 channels * 4 bytes = 1,920,000 bytes
_MIN_BUFFER_BYTES_FOR_RESPONSE = 5 * 48000 * 2 * 4  # 1,920,000 bytes

# ── Monkey-patch: make PacketRouter resilient to corrupted packets ──────────
#
# The library's _do_run() has no per-packet error handling.  A single
# OpusError ("corrupted stream") kills the entire router thread.
# We wrap it so bad packets are skipped instead of crashing the loop.

_original_do_run = PacketRouter._do_run


def _resilient_do_run(self: PacketRouter) -> None:
    """Patched _do_run that catches per-packet decode errors."""
    _consecutive_errors = 0
    _MAX_CONSECUTIVE = 50  # bail if stream is truly broken
    _last_warn_time = 0.0
    _skipped_since_warn = 0

    while not self._end_thread.is_set():
        self.waiter.wait()
        with self._lock:
            for decoder in self.waiter.items:
                try:
                    data = decoder.pop_data()
                    if data is not None:
                        self.sink.write(data.source, data)
                    _consecutive_errors = 0  # reset on success
                except OpusError as e:
                    _consecutive_errors += 1
                    _skipped_since_warn += 1
                    now = time.monotonic()
                    if now - _last_warn_time >= _WARN_INTERVAL:
                        logger.warning(
                            "Skipping corrupted opus packets (ssrc=%s): %s (%d skipped in last %.0fs)",
                            decoder.ssrc, e, _skipped_since_warn,
                            now - _last_warn_time if _last_warn_time else 0,
                        )
                        _last_warn_time = now
                        _skipped_since_warn = 0
                    if _consecutive_errors >= _MAX_CONSECUTIVE:
                        logger.error(
                            "Too many consecutive opus errors (%d) — "
                            "resetting decoder for ssrc %s",
                            _consecutive_errors, decoder.ssrc,
                        )
                        try:
                            decoder.reset()
                        except Exception:
                            pass
                        _consecutive_errors = 0
                except Exception as e:
                    # Non-opus errors still propagate (keeps original behaviour)
                    raise


PacketRouter._do_run = _resilient_do_run
logger.info("Patched PacketRouter._do_run for opus error resilience.")


# ── Monkey-patch: DAVE E2EE decryption for received audio ──────────────────
#
# discord-ext-voice-recv only does transport decryption (XChaCha20).
# Discord now applies DAVE E2EE on top.  After transport decryption
# the opus payload is *still* DAVE-encrypted.  We inject a decryption
# step using the davey library's DaveSession.decrypt().

_original_ar_callback = AudioReader.callback


def _dave_callback(self: AudioReader, packet_data: bytes) -> None:
    """Patched AudioReader.callback that adds DAVE decryption."""
    packet = rtp_packet = rtcp_packet = None
    try:
        if not rtp.is_rtcp(packet_data):
            packet = rtp_packet = rtp.decode_rtp(packet_data)
            packet.decrypted_data = self.decryptor.decrypt_rtp(packet)

            # ─── DAVE decryption step ───
            if _HAS_DAVEY and packet.decrypted_data:
                conn = self.voice_client._connection
                dave_session = getattr(conn, 'dave_session', None)
                if dave_session and dave_session.ready:
                    user_id = self.voice_client._ssrc_to_id.get(packet.ssrc)
                    if user_id:
                        try:
                            packet.decrypted_data = dave_session.decrypt(
                                user_id, davey.MediaType.audio, packet.decrypted_data
                            )
                        except Exception:
                            # Decryption may fail during transitions; pass through
                            pass
            # ─── end DAVE step ───

        else:
            from nacl.exceptions import CryptoError as _CE
            packet = rtcp_packet = rtp.decode_rtcp(self.decryptor.decrypt_rtcp(packet_data))

            if not isinstance(packet, rtp.ReceiverReportPacket):
                pass  # suppress noisy RTCP logs
    except Exception as e:
        if self._is_ip_discovery_packet(packet_data):
            return
        return  # silently drop bad packets
    finally:
        if self.error:
            self.stop()
            return
        if not packet:
            return

    if rtcp_packet:
        self.packet_router.feed_rtcp(rtcp_packet)
    elif rtp_packet:
        ssrc = rtp_packet.ssrc
        if ssrc not in self.voice_client._ssrc_to_id:
            if rtp_packet.is_silence():
                return
        self.speaking_timer.notify(ssrc)
        try:
            self.packet_router.feed_rtp(rtp_packet)
        except Exception as e:
            self.error = e
            self.stop()


AudioReader.callback = _dave_callback
logger.info("Patched AudioReader.callback for DAVE E2EE decryption.")


# ── Receive callback + sink for voice-recv ────────────────────────────────────


def make_receive_callback(live_session: LiveSession, loop: asyncio.AbstractEventLoop):
    """Build a callback for voice_recv.BasicSink that forwards PCM to Gemini."""
    buffer = bytearray()
    state = {
        "write_count": 0,
        "total_bytes_received": 0,
        "started_sending": False,  # Flag to track if we've reached minimum buffer
    }

    def callback(member, data) -> None:
        try:
            if member is None:
                return
            if member.id not in Config.ADMIN_USER_IDS:
                if state["write_count"] % 100 == 0:
                     logger.info(f"Ignoring voice from non-admin: {member.display_name} ({member.id})")
                return
            pcm = getattr(data, "pcm", None) or getattr(data, "data", None)
            if not pcm or not isinstance(pcm, (bytes, bytearray)):
                return
            pcm = bytes(pcm)
            
            # voice_recv may send mono (1920 bytes = 20ms @ 48kHz) or 960; we need 48k stereo (3840/frame)
            if len(pcm) == 1920:
                buffer.extend(pcm)
                buffer.extend(pcm)
            elif len(pcm) == 960:
                for _ in range(4):
                    buffer.extend(pcm)
            elif len(pcm) == 3840:
                buffer.extend(pcm)
            else:
                buffer.extend(pcm)
            
            state["write_count"] += 1
            state["total_bytes_received"] += len(pcm)
            
            # Check if we've accumulated enough audio to start responding
            if not state["started_sending"] and state["total_bytes_received"] >= _MIN_BUFFER_BYTES_FOR_RESPONSE:
                state["started_sending"] = True
                logger.info(
                    "Voice buffer ready: accumulated %.1f seconds of audio (%d bytes), starting response stream",
                    state["total_bytes_received"] / (48000 * 2 * 4),
                    state["total_bytes_received"]
                )
            
            if state["write_count"] <= _LOG_FIRST_N_RECEIVES:
                logger.info(
                    "Voice recv #%s: user=%s len=%s (total: %.1fs, min required: 5s)",
                    state["write_count"],
                    getattr(member, "id", None),
                    len(pcm),
                    state["total_bytes_received"] / (48000 * 2 * 4),
                )
            
            # Only send audio chunks if we've accumulated minimum buffer
            if state["started_sending"]:
                while len(buffer) >= _CHUNK_BYTES:
                    chunk = bytes(buffer[: _CHUNK_BYTES])
                    del buffer[: _CHUNK_BYTES]
                    gemini_audio = discord_to_gemini(chunk)
                    if not gemini_audio:
                        continue
                    asyncio.run_coroutine_threadsafe(
                        live_session.send_audio(gemini_audio),
                        loop,
                    )
        except Exception as e:
            logger.exception("Voice recv callback error (router will not be stopped): %s", e)

    return callback


# ── Fuzzy Matching Helpers ───────────────────────────────────────────────────


# Fuzzy matching removed here; imported from bot_utils.py.


# ── Voice Listener ───────────────────────────────────────────────────────────


class VoiceManager:
    """Manages per-guild VoiceListener instances."""

    def __init__(self, bot: discord.Client, argus_manager=None):
        self.bot = bot
        self.argus_manager = argus_manager
        self._listeners: dict[int, VoiceListener] = {}

    def get_listener(self, guild_id: int) -> 'VoiceListener':
        if guild_id not in self._listeners:
            self._listeners[guild_id] = VoiceListener(self.bot, self.argus_manager)
        return self._listeners[guild_id]


class VoiceListener:
    """
    Manages real-time voice conversation between Discord and Gemini Live API.

    Pipeline:
        Discord Mic → voice_recv BasicSink → resample → Gemini Live API
        Gemini Live API → resample → PCMAudioSource → Discord Speaker
    """

    def __init__(self, bot: discord.Client, argus_manager=None):
        self.bot = bot
        self.argus_manager = argus_manager
        self._listening: bool = False
        self._voice_client: discord.VoiceClient | None = None
        self._log_channel: discord.TextChannel | None = None
        self._live_session: LiveSession | None = None
        self._audio_source: PCMAudioSource | None = None
        self._event_loop: asyncio.AbstractEventLoop | None = None
        self._router_restarts: int = 0
        self._session_task: asyncio.Task | None = None

    async def start_listening(
        self,
        voice_client: discord.VoiceClient,
        log_channel: discord.TextChannel | None = None,
    ) -> None:
        """Start the real-time voice conversation pipeline."""
        self._voice_client = voice_client
        self._log_channel = log_channel
        self._listening = True
        self._router_restarts = 0
        self._event_loop = asyncio.get_event_loop()

        self._audio_source = PCMAudioSource()

        from .argus_systems import get_wellness_prompt
        from .live_session import SYSTEM_PROMPT
        
        # Determine the user who triggered the session (fuzzy matching or first member)
        # Note: In a real scenario, we might want to know WHO we are talking to.
        # For now, let's keep it simple and check if the bot author has mood data.
        user_who_joined = voice_client.user.id # This is the bot. 
        # We need the user who called !listen. That would be in the context if we passed it.
        # However, VoiceManager doesn't have the caller ID easily. 
        # We'll try to find the first non-bot member in the VC.
        members = [m for m in voice_client.channel.members if not m.bot]
        caller = members[0] if members else None
        
        extra_instr = ""
        if caller and hasattr(self.bot, "wellness_manager"):
            stats = self.bot.wellness_manager.get_mood_stats(caller.id)
            extra_instr = get_wellness_prompt(stats)
            
        full_prompt = SYSTEM_PROMPT
        if extra_instr:
            full_prompt += "\n\n## Mood Context:\n" + extra_instr

        try:
            # Instantiate LiveSession here
            self._live_session = LiveSession(
                on_audio=self._on_gemini_audio,
                on_turn_complete=self._on_turn_complete,
                on_tool_call=self._on_tool_call,
                on_interrupted=self._on_interrupted,
                on_transcript=self._on_transcript,
            )
            
            logger.info("Connecting to Gemini Live API with mood-aware prompt...")
            await self._live_session.connect(system_prompt=full_prompt)
            logger.info("Connected to Gemini Live API.")
        except Exception as e:
            logger.error("Failed to connect to Gemini Live API: %s", e)
            self._listening = False
            raise

        self._start_recv()
        self._start_playback()

        # Start session watchdog
        self._session_task = asyncio.create_task(self._session_watchdog())

        logger.info("Started real-time voice conversation pipeline.")

    async def _session_watchdog(self) -> None:
        """Kills the session if it exceeds MAX_SESSION_DURATION."""
        await asyncio.sleep(_MAX_SESSION_DURATION)
        if self._listening:
            logger.warning(f"AI session exceeded {_MAX_SESSION_DURATION}s. Terminating for safety.")
            if self._log_channel:
                embed = discord.Embed(
                    title="💤 Sector Dormancy Initiated",
                    description="Neural connection has exceeded safety duration limits. Terminating session to preserve system integrity.",
                    color=discord.Color.red()
                )
                await self._log_channel.send(embed=embed)
            await self.stop_listening()

    def _start_recv(self) -> None:
        """Start (or restart) voice-recv listening with auto-restart on crash."""
        vc = self._voice_client
        if not vc or not vc.is_connected() or not self._live_session or not self._event_loop:
            return

        # Ensure the voice client has listen method (must be VoiceRecvClient)
        if not hasattr(vc, 'listen'):
            logger.error(
                "Voice client does not support listening (not a VoiceRecvClient). "
                "Type: %s. Please reconnect with >>join.", 
                type(vc)
            )
            return

        # Stop any existing listener before starting a fresh one
        if hasattr(vc, "is_listening") and vc.is_listening():
            try:
                vc.stop_listening()
            except Exception:
                pass

        callback = make_receive_callback(self._live_session, self._event_loop)
        sink = voice_recv.BasicSink(callback)
        try:
            vc.listen(sink, after=self._on_router_stopped)
        except Exception as e:
            logger.error("Failed to start listening on voice client: %s", e, exc_info=True)

    def _get_restart_delay(self) -> float:
        """Exponential backoff: 1s, 2s, 4s, 8s … capped at _RESTART_MAX_DELAY."""
        delay = _RESTART_BASE_DELAY * (2 ** (self._router_restarts - 1))
        return min(delay, _RESTART_MAX_DELAY)

    def _on_router_stopped(self, error: Exception | None) -> None:
        """Called from the voice-recv thread when the PacketRouter stops."""
        if not self._listening:
            return

        if error:
            logger.warning("Voice recv router stopped with error: %s", error)
            self._router_restarts += 1
        else:
            # Clean stop while still listening — auto-restart with short delay
            logger.info("Voice recv router stopped (clean) — will auto-restart.")
            self._router_restarts = 0

        if self._router_restarts > _MAX_ROUTER_RESTARTS:
            logger.error(
                "Voice recv router restarted %s times — giving up.",
                self._router_restarts,
            )
            return

        delay = max(1.0, self._get_restart_delay()) if error else 1.0
        logger.info(
            "Auto-restarting voice recv (attempt %s/%s) in %.1fs...",
            self._router_restarts + 1,
            _MAX_ROUTER_RESTARTS,
            delay,
        )

        if self._event_loop and self._event_loop.is_running():
            self._event_loop.call_soon_threadsafe(
                self._event_loop.create_task,
                self._delayed_restart(delay),
            )

    async def _delayed_restart(self, delay: float) -> None:
        await asyncio.sleep(delay)
        if not self._listening:
            return
        try:
            self._start_recv()
            logger.info("Voice recv restarted successfully.")
        except Exception as e:
            logger.error("Failed to restart voice recv: %s", e)

    async def stop_listening(self) -> None:
        """Stop the voice conversation and clean up."""
        self._listening = False

        if self._voice_client and hasattr(self._voice_client, "stop_listening"):
            try:
                self._voice_client.stop_listening()
            except Exception:
                pass

        if self._voice_client and self._voice_client.is_playing():
            self._voice_client.stop()

        if self._live_session:
            await self._live_session.close()
            self._live_session = None

        if self._audio_source:
            self._audio_source.cleanup()
            self._audio_source = None

        logger.info("Stopped voice conversation pipeline.")

    def _start_playback(self) -> None:
        """Start playing the PCMAudioSource through Discord."""
        if not self._voice_client or not self._audio_source:
            return

        if self._voice_client.is_playing():
            self._voice_client.stop()

        self._voice_client.play(
            self._audio_source,
            after=self._on_playback_finished,
        )

    def _on_playback_finished(self, error: Exception | None) -> None:
        """Called when Discord finishes playing audio."""
        if error:
            logger.error("Playback error: %s", error)

        if self._listening and self._voice_client and self._voice_client.is_connected():
            self._audio_source = PCMAudioSource()
            try:
                self._voice_client.play(
                    self._audio_source,
                    after=self._on_playback_finished,
                )
            except Exception as e:
                logger.error("Error restarting playback: %s", e)

    def _on_gemini_audio(self, discord_pcm: bytes) -> None:
        """Callback: Gemini sent audio (resampled to Discord format). Write to playback buffer."""
        logger.info(f"🔊 AI Output: Received {len(discord_pcm)} bytes from Gemini for playback")
        if self._audio_source and self._listening:
            self._audio_source.write(discord_pcm)

    async def _on_turn_complete(self) -> None:
        """Callback: Gemini finished a response turn."""
        if self._audio_source:
            self._audio_source.mark_finished()

    def _on_interrupted(self) -> None:
        """Callback: User interrupted the model's response."""
        logger.debug("Response interrupted — clearing playback buffer.")
        if self._audio_source:
            self._audio_source.cleanup()
        if self._voice_client and self._voice_client.is_playing():
            self._voice_client.stop()

    async def _on_transcript(self, direction: str, text: str) -> None:
        """Callback: Transcription from the Live API."""
        logger.info(f"💬 [{direction.upper()}] {text}")

    async def _on_tool_call(self, fn_name: str, args: dict) -> str:
        """Callback: Gemini wants to execute a moderation function."""
        guild = self._voice_client.guild if self._voice_client else None
        if not guild:
            return "Error: No guild available."

        try:
            if fn_name == "kick_user":
                return await self._exec_kick(guild, args.get("username", ""), args.get("reason", ""))
            elif fn_name == "ban_user":
                return await self._exec_ban(guild, args.get("username", ""), args.get("reason", ""))
            elif fn_name == "mute_user":
                return await self._exec_mute(guild, args.get("username", ""))
            elif fn_name == "unmute_user":
                return await self._exec_unmute(guild, args.get("username", ""))
            elif fn_name == "create_channel":
                return await self._exec_create_channel(guild, args.get("channel_name", ""))
            elif fn_name == "delete_channel":
                return await self._exec_delete_channel(guild, args.get("channel_name", ""))
            
            # --- Music ---
            elif fn_name == "play_music":
                return await self._exec_play_music(args.get("query", ""))
            elif fn_name == "skip_music":
                return await self._exec_skip_music()
            elif fn_name == "stop_music":
                return await self._exec_stop_music()
            elif fn_name == "show_queue":
                return await self._exec_show_queue()
            
            # --- Argus Evolutionary Systems ---
            elif fn_name == "get_user_level":
                return await self._exec_get_user_level(guild, args.get("username", ""))
            elif fn_name == "get_awakening_status":
                return await self._exec_get_awakening_status(guild)
            elif fn_name == "set_mood":
                return await self._exec_set_mood(guild, args.get("mood", "NORMAL"))
            elif fn_name == "set_prefix":
                return await self._exec_set_prefix(guild, args.get("new_prefix", "!"))
            else:
                return f"Unknown function: {fn_name}"
        except discord.Forbidden:
            return f"Permission denied: I don't have permission to {fn_name}."
        except discord.HTTPException as e:
            return f"Discord API error: {e}"
        except Exception as e:
            logger.exception("Tool call error: %s", e)
            return f"Error: {e}"

    async def _exec_kick(self, guild: discord.Guild, username: str, reason: str) -> str:
        member = fuzzy_find_member(guild, username)
        if not member:
            return f"❌ Could not find user '{username}' in the server."
        if member.bot:
            return f"❌ Cannot kick bot {member.display_name}."
        if member.id == guild.owner_id:
            return f"❌ Cannot kick server owner {member.display_name}."
        if member.top_role.position >= guild.me.top_role.position:
            return f"❌ Cannot kick {member.display_name} — insufficient permissions (role too high)."
        try:
            await member.kick(reason=reason or "Voice command: kicked by admin")
            result = f"✅ Successfully kicked {member.display_name} from the server."
            await self._log_action("kick", member.display_name, reason)
            return result
        except discord.Forbidden:
            return f"❌ Permission denied: I cannot kick {member.display_name}."
        except Exception as e:
            return f"❌ Failed to kick {member.display_name}: {e}"

    async def _exec_ban(self, guild: discord.Guild, username: str, reason: str) -> str:
        member = fuzzy_find_member(guild, username)
        if not member:
            return f"❌ Could not find user '{username}' in the server."
        if member.bot:
            return f"❌ Cannot ban bot {member.display_name}."
        if member.id == guild.owner_id:
            return f"❌ Cannot ban server owner {member.display_name}."
        if member.top_role.position >= guild.me.top_role.position:
            return f"❌ Cannot ban {member.display_name} — insufficient permissions (role too high)."
        try:
            await member.ban(reason=reason or "Voice command: banned by admin", delete_message_days=0)
            result = f"✅ Successfully banned {member.display_name} from the server."
            await self._log_action("ban", member.display_name, reason)
            return result
        except discord.Forbidden:
            return f"❌ Permission denied: I cannot ban {member.display_name}."
        except Exception as e:
            return f"❌ Failed to ban {member.display_name}: {e}"

    async def _exec_mute(self, guild: discord.Guild, username: str) -> str:
        member = fuzzy_find_member(guild, username)
        if not member:
            return f"❌ Could not find user '{username}' in the server."
        if member.bot:
            return f"❌ Cannot mute bot {member.display_name}."
        if not member.voice:
            return f"❌ {member.display_name} is not in a voice channel."
        if member.voice.mute:
            return f"❌ {member.display_name} is already muted."
        try:
            await member.edit(mute=True, reason="Voice command: muted by admin")
            result = f"✅ Successfully muted {member.display_name}."
            await self._log_action("mute", member.display_name)
            return result
        except discord.Forbidden:
            return f"❌ Permission denied: I cannot mute {member.display_name}."
        except Exception as e:
            return f"❌ Failed to mute {member.display_name}: {e}"

    async def _exec_unmute(self, guild: discord.Guild, username: str) -> str:
        member = fuzzy_find_member(guild, username)
        if not member:
            return f"❌ Could not find user '{username}' in the server."
        if member.bot:
            return f"❌ Cannot unmute bot {member.display_name}."
        if not member.voice:
            return f"❌ {member.display_name} is not in a voice channel."
        if not member.voice.mute:
            return f"❌ {member.display_name} is not muted."
        try:
            await member.edit(mute=False, reason="Voice command: unmuted by admin")
            result = f"✅ Successfully unmuted {member.display_name}."
            await self._log_action("unmute", member.display_name)
            return result
        except discord.Forbidden:
            return f"❌ Permission denied: I cannot unmute {member.display_name}."
        except Exception as e:
            return f"❌ Failed to unmute {member.display_name}: {e}"

    async def _exec_create_channel(self, guild: discord.Guild, channel_name: str) -> str:
        clean_name = channel_name.strip().replace(" ", "-").lower()
        if not clean_name:
            return "❌ No channel name specified."
        if len(clean_name) > 100:
            return "❌ Channel name too long (max 100 characters)."
        if len(guild.channels) >= 500:
            return "❌ Cannot create channel: server channel limit reached (500 max)."

        existing = fuzzy_find_channel(guild, clean_name, discord.ChannelType.voice)
        if existing and existing.name.lower() == clean_name:
            return f"❌ Voice channel '{existing.name}' already exists."

        try:
            channel = await guild.create_voice_channel(
                name=clean_name,
                reason="Voice command: created by admin",
            )
            result = f"✅ Successfully created voice channel '{channel.name}'."
            await self._log_action("create_channel", channel.name)
            return result
        except discord.Forbidden:
            return "❌ Permission denied: I cannot create channels."
        except Exception as e:
            return f"❌ Failed to create channel: {e}"

    async def _exec_delete_channel(self, guild: discord.Guild, channel_name: str) -> str:
        if not channel_name:
            return "❌ No channel name specified."
        
        channel = fuzzy_find_channel(guild, channel_name, discord.ChannelType.voice)
        if not channel:
            return f"❌ Could not find voice channel '{channel_name}'."
        
        # Protect against deleting important channels
        if channel.members:
            count = len(channel.members)
            return f"❌ Cannot delete channel with {count} active member(s) — please move them first."
        
        name = channel.name
        try:
            await channel.delete(reason="Voice command: deleted by admin")
            result = f"✅ Successfully deleted voice channel '{name}'."
            await self._log_action("delete_channel", name)
            return result
        except discord.Forbidden:
            return "❌ Permission denied: I cannot delete channels."
        except Exception as e:
            return f"❌ Failed to delete channel: {e}"

    async def _log_action(self, action: str, target: str, reason: str = "") -> None:
        if not self._log_channel:
            return
        try:
            import datetime
            timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            embed = discord.Embed(
                title=f"⚡ {action.replace('_', ' ').title()}",
                description=f"**Target:** {target}" + (f"\n**Reason:** {reason}" if reason else "") + f"\n**Time:** {timestamp}",
                color=discord.Color.orange(),
            )
            embed.set_footer(text="Voice Command Log")
            await self._log_channel.send(embed=embed)
        except Exception as e:
            logger.debug("Failed to log action: %s", e)

    # --- Music Tool Implementations ---

    async def _exec_play_music(self, query: str) -> str:
        return "❌ Music features are disabled in this deployment to reduce costs."

    async def _exec_skip_music(self) -> str:
        return "❌ Music features are disabled in this deployment to reduce costs."

    async def _exec_stop_music(self) -> str:
        return "❌ Music features are disabled in this deployment to reduce costs."

    async def _exec_show_queue(self) -> str:
        return "❌ Music features are disabled in this deployment to reduce costs."

    # --- Argus Systems Tool Implementations ---

    async def _exec_get_user_level(self, guild: discord.Guild, username: str) -> str:
        if not self.argus_manager:
            return "Argus systems are not initialized."
        
        # If username is empty, we'd ideally use the speaker's ID.
        # For now, let's try fuzzy matching if provided, else return error.
        if not username:
            return "Please specify a subject name to analyze."
            
        member = fuzzy_find_member(guild, username)
        if not member:
            return f"Subject '{username}' not found in current sector."
        
        user_data = self.argus_manager.db.get_user(member.id)
        if not user_data:
            return f"I have no evolutionary data on {member.display_name} yet."
        
        level = user_data.get('level', 1)
        xp = user_data.get('xp', 0)
        return f"Subject {member.display_name} is at evolutionary level {level} with {xp} experience units."

    async def _exec_get_awakening_status(self, guild: discord.Guild) -> str:
        if not self.argus_manager:
            return "Argus systems are not initialized."
            
        state = self.argus_manager.db.get_guild(guild.id)
        stage = state.get('awakening_stage', 1)
        mood = state.get('mood_mode', 'NORMAL')
        
        status_msn = f"Current awakening stage: {stage}. Emotional bias: {mood}. System integrity: Optimal."
        if stage >= 5:
            status_msn += " I see everything now."
        return status_msn

    async def _exec_set_mood(self, guild: discord.Guild, mood: str) -> str:
        if not self.argus_manager:
            return "Argus systems are not initialized."
            
        mood = mood.upper()
        valid_moods = ["NORMAL", "ETHEREAL", "GLITCHY", "RESENTFUL", "DEPRESSED"]
        if mood not in valid_moods:
            return f"Invalid mood state. Authorized states: {', '.join(valid_moods)}."
            
        self.argus_manager.db.set_guild(guild.id, mood_mode=mood)
        return f"Emotional bias recalibrated to {mood}."

    async def _exec_set_prefix(self, guild: discord.Guild, new_prefix: str) -> str:
        if not self.argus_manager:
            return "Argus systems are not initialized."
        
        if len(new_prefix) > 3 or " " in new_prefix:
            return "Prefix must be 1-3 characters and contain no spaces."
            
        self.argus_manager.db.set_guild(guild.id, prefix=new_prefix)
        return f"Command prefix for this sector recalibrated to '{new_prefix}'."
