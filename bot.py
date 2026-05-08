"""
🌿 Planthesia Bot - Server Helper

Your friendly Discord companion for server management and helpful information. 
Supports voice conversations via Gemini 2.5 Flash Live API.

Main entry point — handles bot setup, text commands, and event lifecycle.
Uses discord.py + discord-ext-voice-recv for voice reception and
Gemini 2.5 Flash Live API for real-time bidirectional voice conversation.
"""

import asyncio
import builtins
import logging
import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple, cast

import discord
from discord.ext import commands
from discord import utils

from config import Config
from logger import setup_logging, get_logger
from core.voice_listener import VoiceManager
# music manager removed for cost-saving deployment (music features pruned)
from core.voice_reconnection import VoiceReconnectionManager
from core.voice_session_timeout import VoiceSessionTimeoutManager

# Voice receive extension: connect with VoiceRecvClient to support both send and receive
try:
    import discord.ext.voice_recv as voice_recv
except ImportError:
    voice_recv = None

# ── Load Opus ────────────────────────────────────────────────────────────────
if not discord.opus.is_loaded():
    _opus_paths = [
        "/opt/homebrew/lib/libopus.dylib",      # macOS ARM (Homebrew)
        "/usr/local/lib/libopus.dylib",          # macOS Intel (Homebrew)
        "/usr/lib/x86_64-linux-gnu/libopus.so.0",  # Linux
        "libopus",                                # System default
    ]
    for _path in _opus_paths:
        try:
            discord.opus.load_opus(_path)
            break
        except Exception:
            continue

# ── Structured Logging ──────────────────────────────────────────────────────
setup_logging(
    log_level=Config.LOG_LEVEL,
    log_dir="logs",
    include_file_handler=True,
)
logger = get_logger("bot")

# Suppress noisy logs
logging.getLogger("discord.opus").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai.models").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)

# Suppress the opus "Error occurred while decoding opus frame." print statements
_original_print = builtins.print
def _filtered_print(*args, **kwargs):
    if args:
        msg = str(args[0]).lower()
        if "opus" in msg or "decoder" in msg:
            return
    _original_print(*args, **kwargs)
builtins.print = _filtered_print

# ── Cooldown & Rate Limiting ────────────────────────────────────────────────
# Track voice command attempts per guild to prevent spam
_voice_command_attempts: Dict[int, List[float]] = {}
_VOICE_COMMAND_RATE_LIMIT: int = 5  # max 5 commands per guild
_VOICE_COMMAND_TIME_WINDOW: int = 30  # in this many seconds
_LAST_CLEANUP_TIME: float = time.time()  # Track cleanup frequency
_CLEANUP_INTERVAL: int = 300  # Clean expired entries every 5 minutes

def check_voice_command_rate_limit(guild_id: int) -> Tuple[bool, str]:
    """Check if a guild is rate-limited for voice commands."""
    global _LAST_CLEANUP_TIME
    now = time.time()
    
    # Initialize list if not present
    if guild_id not in _voice_command_attempts:
        _voice_command_attempts[guild_id] = []
    attempts = _voice_command_attempts[guild_id]
    
    # Clean old attempts (older than time window)
    new_attempts = [t for t in attempts if now - t < _VOICE_COMMAND_TIME_WINDOW]
    _voice_command_attempts[guild_id] = new_attempts
    attempts = new_attempts
    
    if len(attempts) >= _VOICE_COMMAND_RATE_LIMIT:
        retry_after = int(_VOICE_COMMAND_TIME_WINDOW - (now - attempts[0])) + 1
        return False, f"⏳ Too many voice commands. Wait {retry_after}s before trying again."
    
    attempts.append(now)
    
    # Periodically clean up empty guild entries to prevent memory leaks
    if now - _LAST_CLEANUP_TIME > _CLEANUP_INTERVAL:
        for gid in list(_voice_command_attempts.keys()):
            if not _voice_command_attempts[gid]:
                _voice_command_attempts.pop(gid, None)
        _LAST_CLEANUP_TIME = now
        logger.debug("Cleaned up rate limit dictionary (%d active guilds)", len(_voice_command_attempts))
    
    return True, ""

# ── Dynamic Prefix ──────────────────────────────────────────────────────────
def get_prefix(bot, message):
    if not message.guild:
        return Config.COMMAND_PREFIX
    if hasattr(bot, "argus_manager") and bot.argus_manager:
        data = bot.argus_manager.db.get_guild(message.guild.id)
        if data and data.get("prefix"):
            return data.get("prefix")
    return Config.COMMAND_PREFIX

# ── Bot Setup ────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
# intents.members = True

class ArgusBot(commands.Bot):
    async def setup_hook(self):
        """Load all extensions (Cogs) from the cogs directory."""
        logger.info("Loading Cogs...")
        if os.path.exists("./cogs"):
            for filename in os.listdir("./cogs"):
                if filename.endswith(".py") and filename != "__init__.py":
                    cog_name = str(filename).replace(".py", "")
                    try:
                        await self.load_extension(f"cogs.{cog_name}")
                        logger.info(f"Loaded Cog: {filename}")
                    except Exception as e:
                        logger.error(f"Failed to load Cog {filename}: {e}")

bot = ArgusBot(
    command_prefix=get_prefix,
    intents=intents,
    description="🌿 Planthesia Bot - Your friendly server helper. Info, voice AI, and more!",
    help_command=None,
)

# Global managers (assigned to bot object in on_ready)
voice_manager: VoiceManager | None = None
voice_reconnection_manager: VoiceReconnectionManager | None = None
voice_session_timeout_manager: VoiceSessionTimeoutManager | None = None
_background_tasks: list[asyncio.Task] = []  # Track background tasks for cleanup

# Status rotation list - Planthesia Bot helper personality
_STATUS_ROTATION = [
    (discord.ActivityType.watching, "your server"),
    (discord.ActivityType.listening, "support requests"),
    (discord.ActivityType.playing, "helpful bot 🌿"),
    (discord.ActivityType.watching, "members join"),
    (discord.ActivityType.listening, "voice conversations"),
]
_STATUS_INDEX = 0

async def _update_bot_status() -> None:
    """Periodically update bot status for visual engagement."""
    global _STATUS_INDEX
    try:
        while True:
            await asyncio.sleep(30)  # Update every 30 seconds
            activity_type, status_text = _STATUS_ROTATION[_STATUS_INDEX]
            activity = discord.Activity(type=activity_type, name=status_text)
            await bot.change_presence(activity=activity, status=discord.Status.online)
            _STATUS_INDEX = (_STATUS_INDEX + 1) % len(_STATUS_ROTATION)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error("Status update error: %s", e)

# ── Events ───────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    global voice_manager, voice_reconnection_manager, voice_session_timeout_manager, _background_tasks
    
    voice_manager = VoiceManager(bot)
    bot.voice_manager = voice_manager
    
    
    voice_reconnection_manager = VoiceReconnectionManager(bot)
    voice_reconnection_manager.start()
    bot.voice_reconnection_manager = voice_reconnection_manager
    
    
    voice_session_timeout_manager = VoiceSessionTimeoutManager(bot)
    voice_session_timeout_manager.start()
    logger.info("PYTHON: %s", sys.executable)
    logger.info("PATH: %s", sys.path)
    import websockets
    logger.info("WEBSOCKETS: %s", websockets.__file__)
    import google.genai
    logger.info("GOOGLE-GENAI: %s", google.genai.__file__)
    
    try:
        # Global sync (takes up to 1 hour to propagate)
        synced = await bot.tree.sync()
        logger.info("  Synced %d slash command(s) globally", len(synced))
        # Also sync per-guild for instant availability
        for guild in bot.guilds:
            try:
                bot.tree.copy_global_to(guild=guild)
                guild_synced = await bot.tree.sync(guild=guild)
                logger.info("  Guild sync: %d commands → %s", len(guild_synced), guild.name)
            except Exception as ge:
                logger.warning("  Guild sync failed for %s: %s", guild.name, ge)
    except Exception as e:
        logger.error("  Failed to sync slash commands: %s", e)

    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("  🌿 Planthesia Bot is online: %s (ID: %s)", bot.user.name, bot.user.id)
    logger.info("  📡 Connected to %d guild(s)", len(bot.guilds))
    logger.info("  🎯 Features: Info, Voice AI")
    logger.info(f"  ✅ Ready to help! Use {Config.COMMAND_PREFIX}help for commands.")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Start status rotation
    status_task = bot.loop.create_task(_update_bot_status())
    _background_tasks.append(status_task)
    
    if argus_manager:
        events_task = bot.loop.create_task(argus_manager.start_random_events())
        _background_tasks.append(events_task)
    
    # Preload Whisper model
    logger.info("Preloading Whisper model...")
    try:
        from core.transcriber import Transcriber
        Transcriber.get_model()
        logger.debug("✅ Whisper model preloaded successfully")
    except Exception as e:
        logger.warning("Failed to preload Whisper model: %s", e)
    
    # Register health checks
    logger.info("Registering health checks...")
    try:
        from core.health_monitor import HealthCheckManager
        health = HealthCheckManager()
        
        async def bot_health():
            from core.health_monitor import HealthCheck, HealthStatus
            return HealthCheck(
                name="bot",
                status=HealthStatus.HEALTHY if bot.latency < 0.5 else HealthStatus.DEGRADED,
                latency_ms=bot.latency * 1000,
                message=f"Bot is {'online' if bot.is_ready() else 'offline'}",
                timestamp=datetime.utcnow()
            )
        
        health.register_check("bot", bot_health)
        bot.health_manager = health
        logger.debug("✅ Health checks registered")
    except Exception as e:
        logger.warning("Failed to register health checks: %s", e)


@bot.event
async def on_message(message: discord.Message):
    """Handle message events: pings and command processing."""
    if message.author.bot:
        return
        
    # Debug log to see if we are receiving ANYTHING
    logger.info(f"📩 [{message.guild.name if message.guild else 'DM'}] {message.author}: {message.content}")

    # Respond to pings
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        # Check if it's a direct mention at the start
        if message.content.startswith(f'<@{bot.user.id}>') or message.content.startswith(f'<@!{bot.user.id}>'):
            await message.channel.send(f"👁️ **Argus Evolutionary Systems: ONLINE**\nPrefix: `{Config.COMMAND_PREFIX}`\nType `{Config.COMMAND_PREFIX}help` for a list of available subroutines.")
            
    # Process commands
    await bot.process_commands(message)


# Note: Events like on_voice_state_update, etc. are now handled 
# by their respective Cog listeners (ArgusCog, TempVoiceCog).


# Note: Interaction handler is now in TempVoiceCog.

async def shutdown_bot():
    """Cleanup: cancel background tasks before shutdown."""
    global _background_tasks, voice_reconnection_manager, voice_session_timeout_manager
    
    logger.info("Shutting down: stopping voice reconnection manager...")
    if voice_reconnection_manager:
        voice_reconnection_manager.stop()
    
    logger.info("Shutting down: stopping voice session timeout manager...")
    if voice_session_timeout_manager:
        voice_session_timeout_manager.stop()
    
    logger.info("Shutting down: cancelling background tasks...")
    for task in _background_tasks:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    _background_tasks.clear()

@bot.event
async def on_close():
    """Called when bot is about to close."""
    await shutdown_bot()

# ── Error Handling ───────────────────────────────────────────────────────────

@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(
            title="⏳ Sector Cooldown Active",
            description=f"Recalibrating neural buffers... Please wait **{error.retry_after:.1f}s** before re-entering this command.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed, delete_after=10)
        return
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="🚫 Permission Denied",
            description="You don't have permission to execute this command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=10)
        return
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="❌ Missing Argument",
            description=f"**Parameter:** `{error.param.name}`\n\nUse `{ctx.prefix}help {ctx.command.name}` for more info.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=15)
        return
    cmd_name = "unknown"
    if ctx.command is not None:
        cmd_name = str(ctx.command.name)
        
    logger.error("Command error in %s: %s", cmd_name, error)
    try:
        err_msg = str(error)
        embed = discord.Embed(
            title="⚠️ System Exception",
            description=f"```{err_msg[:1024]}```",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=10)
    except Exception:
        pass

# ── Run ──────────────────────────────────────────────────────────────────────

def main():
    Config.validate()
    logger.info("Starting bot...")
    bot.run(Config.DISCORD_TOKEN)

if __name__ == "__main__":
    main()
