"""
Voice-Controlled Discord Moderation Bot (AI-Powered)

Main entry point — handles bot setup, text commands, and event lifecycle.
Uses discord.py + discord-ext-voice-recv for voice (DAVE + receive) and
Gemini 2.5 Flash Live API for real-time bidirectional voice conversation.
"""

import asyncio
import builtins
import logging
import os
from typing import Optional, Tuple

import discord
from discord.ext import commands
from discord import utils

from config import Config
from logger import setup_logging, get_logger
from core.voice_listener import VoiceManager
from core.temp_voice import TempVoiceManager
from core.temp_voice_ui import TempVoiceView
from core.music_player import MusicManager, resolve_tracks, Track
from core.argus_systems import ArgusManager, modify_response

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
import time
from collections import defaultdict
from typing import Dict, List

# Track voice command attempts per guild to prevent spam
_voice_command_attempts: Dict[int, List[float]] = defaultdict(list)
_VOICE_COMMAND_RATE_LIMIT: int = 5  # max 5 commands per guild
_VOICE_COMMAND_TIME_WINDOW: int = 30  # in this many seconds


def check_voice_command_rate_limit(guild_id: int) -> Tuple[bool, str]:
    """Check if a guild is rate-limited for voice commands."""
    now = time.time()
    attempts = _voice_command_attempts[guild_id]
    
    # Clean old attempts (older than time window)
    attempts[:] = [t for t in attempts if now - t < _VOICE_COMMAND_TIME_WINDOW]
    
    if len(attempts) >= _VOICE_COMMAND_RATE_LIMIT:
        retry_after = int(_VOICE_COMMAND_TIME_WINDOW - (now - attempts[0])) + 1
        return False, f"⏳ Too many voice commands. Wait {retry_after}s before trying again."
    
    attempts.append(now)
    return True, ""


# ── Dynamic Prefix ──────────────────────────────────────────────────────────
def get_prefix(bot, message):
    if not message.guild:
        return Config.COMMAND_PREFIX
    
    # Try to get from argus_manager if it exists, else use default
    am = getattr(bot, "argus_manager", None)
    if am:
        guild_data = am.db.get_guild(message.guild.id)
        if guild_data and guild_data.get("prefix"):
            return guild_data["prefix"]
    
    return Config.COMMAND_PREFIX

# ── Bot Setup ────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
# intents.members = True

bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
    description="AI-powered voice-controlled Discord moderation bot",
)

voice_manager: VoiceManager | None = None
temp_voice_manager: TempVoiceManager | None = None
music_manager: MusicManager | None = None
argus_manager: ArgusManager | None = None

# Status rotation list
_STATUS_ROTATION = [
    (discord.ActivityType.watching, "the evolution..."),
    (discord.ActivityType.listening, "voice commands"),
    (discord.ActivityType.playing, "Gemini 2.0 Flash"),
    (discord.ActivityType.watching, "your server"),
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
    global voice_manager, temp_voice_manager, music_manager, argus_manager
    argus_manager = ArgusManager(bot)
    bot.argus_manager = argus_manager
    
    voice_manager = VoiceManager(bot, argus_manager)
    bot.voice_manager = voice_manager
    
    temp_voice_manager = TempVoiceManager(bot, argus_manager)
    bot.temp_voice_manager = temp_voice_manager
    music_manager = MusicManager()
    bot.music_manager = music_manager
    
    try:
        synced = await bot.tree.sync()
        logger.info("  Synced %d slash command(s)", len(synced))
    except Exception as e:
        logger.error("  Failed to sync slash commands: %s", e)

    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("  👁️ Argus is online: %s (ID: %s)", bot.user.name, bot.user.id)
    logger.info("  📡 Connected to %d guild(s)", len(bot.guilds))
    logger.info("  🧠 AI: Gemini 2.5 Flash (Live Audio Mode)")
    logger.info("  ✅ Ready! Use %sjoin to connect, then %slisten to start.",
                Config.COMMAND_PREFIX, Config.COMMAND_PREFIX)
    
    # Start status rotation
    bot.loop.create_task(_update_bot_status())
    
    if argus_manager:
        bot.loop.create_task(argus_manager.start_random_events())


@bot.event
async def on_voice_state_update(member, before, after):
    """Create temp VC when user joins the Create VC channel; cleanup when temp channel is empty."""
    if not temp_voice_manager or not argus_manager:
        return
    
    guild_data = argus_manager.db.get_guild(member.guild.id)
    if not guild_data:
        return
        
    trigger_id = guild_data.get('temp_voice_trigger_id')
    
    if after.channel and after.channel.id == trigger_id:
        await temp_voice_manager.create_temp_channel(member)
        return
    if before.channel and before.channel.id in temp_voice_manager.temp_channels:
        await temp_voice_manager.check_cleanup(before.channel)

@bot.event
async def on_message(message):
    if argus_manager:
        await argus_manager.handle_leveling(message)
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    if argus_manager:
        await argus_manager.on_member_join(member)

@bot.event
async def on_message_delete(message):
    if argus_manager:
        await argus_manager.on_message_delete(message)

@bot.event
async def on_message_edit(before, after):
    if argus_manager:
        await argus_manager.on_message_edit(before, after)

@bot.event
async def on_member_join(member):
    if argus_manager:
        await argus_manager.on_member_join(member)

@bot.event
async def on_member_remove(member):
    if argus_manager:
        await argus_manager.on_member_remove(member)
async def on_interaction(interaction):
    """Handle TempVoice button interactions (works after bot restart)."""
    if interaction.type != discord.InteractionType.component:
        return
    data = getattr(interaction, "data", None)
    if not data or "custom_id" not in data:
        return
    cid = data["custom_id"]
    manager = getattr(bot, "temp_voice_manager", None)
    if not manager:
        await interaction.response.send_message("TempVoice not configured.", ephemeral=True)
        return

    # Shared interface channel: resolve VC by owner, then run action
    if cid.startswith("tempvoice_shared:"):
        parts = cid.split(":")
        if len(parts) < 2:
            return
        action = parts[1]
        channel_id = manager.get_owned_channel_id(interaction.user.id)
        if channel_id is None:
            await interaction.response.send_message(
                "You don't have a temp VC. Join the **Create VC** channel to create one.",
                ephemeral=True,
            )
            return
        channel = interaction.guild.get_channel(channel_id)
        if channel is None or not isinstance(channel, discord.VoiceChannel):
            await interaction.response.send_message("Your temp VC no longer exists.", ephemeral=True)
            return
        await TempVoiceView._execute_action(manager, interaction, channel, action)
        return

    if not cid.startswith("tempvoice:"):
        return
    parts = cid.split(":")
    if len(parts) < 3:
        return
    action, channel_id_s = parts[1], parts[2]
    try:
        channel_id = int(channel_id_s)
    except ValueError:
        return
    channel = interaction.guild.get_channel(channel_id)
    if channel is None:
        try:
            channel = await interaction.guild.fetch_channel(channel_id)
        except (discord.NotFound, discord.HTTPException):
            await interaction.response.send_message("Channel not found.", ephemeral=True)
            return
    if not isinstance(channel, discord.VoiceChannel):
        await interaction.response.send_message("Channel not found.", ephemeral=True)
        return
    await TempVoiceView._execute_action(manager, interaction, channel, action)


# ── Text Commands ────────────────────────────────────────────────────────────

@bot.command(name="join", help="Join the voice channel you are in.")
@commands.cooldown(1, 5, commands.BucketType.user)
async def join(ctx: commands.Context):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ You need to be in a voice channel first!")
        return

    channel = ctx.author.voice.channel
    
    if not voice_manager:
        await ctx.send("❌ Voice not initialized.")
        return

    listener = voice_manager.get_listener(ctx.guild.id)
    await listener.stop_listening() # Close any active sessions

    try:
        if voice_recv is None:
            await ctx.send("❌ Voice support not available.")
            return
        
        if ctx.voice_client:
            if ctx.voice_client.channel != channel:
                await ctx.voice_client.move_to(channel)
        else:
            await channel.connect(cls=voice_recv.VoiceRecvClient)
            
        await ctx.send(f"✅ Joined **{channel.name}**. Use `{Config.COMMAND_PREFIX}listen` to start the AI.")
    except discord.ClientException:
        await ctx.send("❌ Already in a voice channel.")
    except Exception as e:
        await ctx.send(f"❌ Could not join voice: {e}")


@bot.command(name="leave", help="Bot leaves the voice channel.")
async def leave_vc(ctx: commands.Context):
    if not ctx.voice_client:
        await ctx.send("❌ I'm not in a voice channel.")
        return
        
    if voice_manager:
        listener = voice_manager.get_listener(ctx.guild.id)
        await listener.stop_listening()
        
    if music_manager and ctx.guild:
        player = music_manager.get_player(ctx.guild.id)
        await player.stop()
        player.set_voice_client(None)
        
    await ctx.voice_client.disconnect()
    await ctx.send("👋 Left the voice channel.")


@bot.command(name="listen", help="Start listening for voice commands.")
@commands.cooldown(1, 10, commands.BucketType.user)
async def listen(ctx: commands.Context):
    if ctx.author.id not in Config.ADMIN_USER_IDS and not ctx.author.guild_permissions.administrator:
        await ctx.send("🚫 You don't have permission to use voice commands.")
        return
    
    # Check guild-level rate limit to prevent spam
    can_proceed, rate_limit_msg = check_voice_command_rate_limit(ctx.guild.id)
    if not can_proceed:
        await ctx.send(rate_limit_msg)
        return
    
    if not ctx.voice_client:
        await ctx.send(f"❌ Use `{Config.COMMAND_PREFIX}join` first so I'm in your voice channel.")
        return
    if not ctx.voice_client.is_connected():
        await ctx.send(
            "❌ I'm not fully connected to voice yet. "
            f"Try `{Config.COMMAND_PREFIX}leave` then `{Config.COMMAND_PREFIX}join` again."
        )
        return

    if not voice_manager:
        await ctx.send("❌ Voice not initialized.")
        return

    listener = voice_manager.get_listener(ctx.guild.id)
    connecting_msg = await ctx.send("🔄 Connecting to Gemini Live API...")

    try:
        await listener.start_listening(
            voice_client=ctx.voice_client,
            log_channel=ctx.channel,
        )
    except asyncio.TimeoutError:
        await connecting_msg.edit(content="⚠️ **Connection Timeout**: Gemini Live API took too long to respond. Please try again.")
        return
    except Exception as e:
        await connecting_msg.edit(content=f"❌ **System Error**: Failed to initialize voice pipeline.\n`{e}`")
        logger.error(f"Voice listener start failure (Guild {ctx.guild.id}): {e}")
        return

    embed = discord.Embed(
        title="🎙️ AI Voice Conversation Active",
        description=(
            "**Real-time voice conversation** \n\n"
            "🗣️ **Just talk naturally** — I'll respond by speaking back!\n\n"
            "**I can also moderate:**\n"
            "• *\"kick john\"*  •  *\"mute someone\"*\n"
            "• *\"create channel gaming\"*\n\n"
            f"🔊 Voice: **{Config.GEMINI_VOICE}** • 🌐 Any language"
        ),
        color=discord.Color.green(),
    )
    await connecting_msg.edit(content=None, embed=embed)


@bot.command(name="stop", help="Stop listening for voice commands.")
async def stop_listening(ctx: commands.Context):
    if not voice_manager:
        await ctx.send("❌ Voice not initialized.")
        return
    listener = voice_manager.get_listener(ctx.guild.id)
    await listener.stop_listening()
    await ctx.send("🔇 Stopped listening. Gemini Live session closed.")


# ── Music commands ───────────────────────────────────────────────────────────

@bot.command(name="play", help="Play a track from URL or search query. Bot joins your VC if needed.")
async def play_music(ctx: commands.Context, *, query: str = None):
    if not query or not query.strip():
        await ctx.send("❌ Use `!play <URL or search terms>` (e.g. `!play never gonna give you up`).")
        return
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ You need to be in a voice channel first!")
        return

    channel = ctx.author.voice.channel
    vc = ctx.voice_client

    # Join VC if not connected
    if not vc:
        if voice_recv is None:
            await ctx.send("❌ Voice support not available.")
            return
        try:
            vc = await channel.connect(cls=voice_recv.VoiceRecvClient)
        except Exception as e:
            await ctx.send(f"❌ Could not join voice: {e}")
            return
    elif vc.channel != channel:
        await vc.move_to(channel)

    if not music_manager:
        await ctx.send("❌ Music not initialized.")
        return

    # Stop AI listener so only music is heard
    if voice_manager:
        listener = voice_manager.get_listener(ctx.guild.id)
        await listener.stop_listening()

    msg = await ctx.send("🔍 Resolving track…")
    tracks = await resolve_tracks(query.strip(), ctx.author)
    if not tracks:
        await msg.edit(content="❌ Could not resolve that URL or search. Try a different link or query.")
        return

    player = music_manager.get_player_for_vc(vc)
    if not player:
        await msg.edit(content="❌ Could not get music player.")
        return

    if len(tracks) == 1:
        was_empty = not player.is_playing and len(player.queue) == 0
        await player.play(tracks[0])
        if was_empty:
            await msg.edit(content=f"▶️ **Now playing:** {tracks[0].title}")
        else:
            await msg.edit(content=f"✅ Added to queue: **{tracks[0].title}**")
    else:
        started = await player.enqueue_many(tracks)
        if started:
            await msg.edit(content=f"▶️ **Now playing:** {started.title}\n✅ Added **{len(tracks) - 1}** more track(s) to the queue.")
        else:
            await msg.edit(content=f"✅ Added **{len(tracks)}** track(s) to the queue.")


@bot.command(name="skip", help="Skip the current track and play the next in queue.")
async def skip_music(ctx: commands.Context):
    if not ctx.voice_client or not ctx.voice_client.is_connected():
        await ctx.send("❌ I'm not in a voice channel.")
        return
    if not music_manager:
        await ctx.send("❌ Music not initialized.")
        return
    player = music_manager.get_player_for_vc(ctx.voice_client)
    if not player:
        await ctx.send("❌ No music player.")
        return
    await player.skip()
    await ctx.send("⏭️ Skipped.")


@bot.command(name="stopmusic", help="Stop playback and clear the queue.")
async def stop_music(ctx: commands.Context):
    if not ctx.voice_client or not ctx.voice_client.is_connected():
        await ctx.send("❌ I'm not in a voice channel.")
        return
    if not music_manager:
        await ctx.send("❌ Music not initialized.")
        return
    player = music_manager.get_player_for_vc(ctx.voice_client)
    if not player:
        await ctx.send("❌ No music player.")
        return
    await player.stop()
    await ctx.send("⏹️ Stopped and cleared queue.")


@bot.command(name="queue", help="Show current track and queue.")
async def queue_music(ctx: commands.Context):
    if not music_manager:
        await ctx.send("❌ Music not initialized.")
        return
    if not ctx.guild:
        await ctx.send("❌ Not in a guild.")
        return
    player = music_manager.get_player(ctx.guild.id)
    current = player.current
    q = player.queue
    lines = []
    if current:
        lines.append(f"**Now playing:** {current.title} (requested by {current.requested_by_name})")
    else:
        lines.append("**Now playing:** —")
    if q:
        for i, t in enumerate(q[:10], 1):
            lines.append(f"{i}. {t.title} (requested by {t.requested_by_name})")
        if len(q) > 10:
            lines.append(f"… and {len(q) - 10} more")
    else:
        lines.append("Queue is empty.")
    embed = discord.Embed(
        title="Music Queue",
        description="\n".join(lines),
        color=discord.Color.blue(),
    )
    await ctx.send(embed=embed)


@bot.command(name="nowplaying", help="Show the current track.")
async def nowplaying_music(ctx: commands.Context):
    if not music_manager:
        await ctx.send("❌ Music not initialized.")
        return
    if not ctx.guild:
        await ctx.send("❌ Not in a guild.")
        return
    player = music_manager.get_player(ctx.guild.id)
    current = player.current
    if not current:
        await ctx.send("Nothing playing.")
        return
    duration_str = f" ({current.duration}s)" if current.duration else ""
    await ctx.send(f"▶️ **Now playing:** {current.title}{duration_str} (requested by {current.requested_by_name})")


@bot.command(name="setcreatechannel", help="[Admin] Set the voice channel that creates temp VCs when users join.")
async def set_create_channel(ctx: commands.Context, channel: discord.VoiceChannel):
    if ctx.author.id not in Config.ADMIN_USER_IDS and not ctx.author.guild_permissions.administrator:
        await ctx.send("🚫 You don't have permission.")
        return
    if not argus_manager:
        await ctx.send("❌ Argus systems not initialized.")
        return
    argus_manager.db.set_guild(ctx.guild.id, temp_voice_trigger_id=channel.id)
    await ctx.send(f"✅ **Create VC** channel set to **{channel.name}**. Join it to create a temp VC.")


@bot.command(name="settempvcategory", help="[Admin] Set the category where temp voice channels are created.")
async def set_temp_vc_category(ctx: commands.Context, category: discord.CategoryChannel):
    if ctx.author.id not in Config.ADMIN_USER_IDS and not ctx.author.guild_permissions.administrator:
        await ctx.send("🚫 You don't have permission.")
        return
    if not argus_manager:
        await ctx.send("❌ Argus systems not initialized.")
        return
    argus_manager.db.set_guild(ctx.guild.id, temp_voice_category_id=category.id)
    await ctx.send(f"✅ **Temp VC Category** set to **{category.name}**. New channels will be created here.")


@bot.command(name="setinterfacechannel", help="[Admin] Set the text channel where users manage their temp VC.")
async def set_interface_channel_cmd(ctx: commands.Context, channel: discord.TextChannel):
    if ctx.author.id not in Config.ADMIN_USER_IDS and not ctx.author.guild_permissions.administrator:
        await ctx.send("🚫 You don't have permission.")
        return
    if not argus_manager:
        await ctx.send("❌ Argus systems not initialized.")
        return
    argus_manager.db.set_guild(ctx.guild.id, temp_voice_interface_id=channel.id)
    await ctx.send(f"✅ **Interface Channel** set to {channel.mention}. Run `{ctx.prefix}postvcinterface` there.")


@bot.command(name="postvcinterface", help="[Admin] Post the shared TempVoice interface here (one message; actions apply to your own VC only).")
async def post_vc_interface(ctx: commands.Context):
    if ctx.author.id not in Config.ADMIN_USER_IDS and not ctx.author.guild_permissions.administrator:
        await ctx.send("🚫 You don't have permission.")
        return
    if not temp_voice_manager:
        await ctx.send("❌ TempVoice not initialized.")
        return
    from core.temp_voice_ui import SharedTempVoiceView
    embed = discord.Embed(
        title="TempVoice Interface",
        description="Use the buttons below to manage **your** temp VC. Actions apply only to the VC you own.",
        color=discord.Color.blue(),
    )
    embed.set_footer(text="Create a temp VC by joining the Create VC channel, then use these buttons.")
    view = SharedTempVoiceView(temp_voice_manager, timeout=None)
    await ctx.send(embed=embed, view=view)
    await ctx.send("✅ Shared VC interface posted. Everyone uses this message; clicks affect only their own VC.")


@bot.command(name="nexus_setup", help="[Admin] Set the logging channel for the Nexus Logger.")
async def nexus_setup_cmd(ctx: commands.Context, channel: discord.TextChannel):
    if ctx.author.id not in Config.ADMIN_USER_IDS and not ctx.author.guild_permissions.administrator:
        await ctx.send("🚫 You don't have permission.")
        return
    if not argus_manager:
        await ctx.send("❌ Argus systems not initialized.")
        return
    argus_manager.db.set_guild(ctx.guild.id, logging_channel_id=channel.id)
    await ctx.send(f"👁️ **Nexus Logger** initialized. Surveillance logs will be routed to {channel.mention}.")

@bot.command(name="level", help="Check your current evolutionary level.")
async def level_cmd(ctx: commands.Context, member: discord.Member = None):
    if not argus_manager:
        await ctx.send("❌ Argus systems not initialized.")
        return
    target = member or ctx.author
    user_data = argus_manager.db.get_user(target.id)
    if not user_data:
        await ctx.send(f"I have no data on {target.name} yet. Interact more to begin evolution.")
        return
    
    level = user_data.get('level', 1)
    xp = user_data.get('xp', 0)
    next_xp = argus_manager.get_xp_for_level(level)
    
    embed = argus_manager.create_argus_embed(
        title=f"Evolutionary Profile: {target.name}",
        description=(
            f"**Level:** {level}\n"
            f"**XP:** {xp} / {next_xp}\n"
            f"**Status:** {'Integrated' if level > 5 else 'Subject'}"
        ),
        color=argus_manager.COLORS["ETHEREAL"]
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="setup", aliases=["config", "settings"], help="[Admin] Show current server configuration and setup status.")
async def setup_status(ctx: commands.Context):
    if ctx.author.id not in Config.ADMIN_USER_IDS and not ctx.author.guild_permissions.administrator:
        await ctx.send("🚫 You don't have permission.")
        return
    if not argus_manager:
        await ctx.send("❌ Argus systems not initialized.")
        return

    data = argus_manager.db.get_guild(ctx.guild.id) or {}
    
    def format_status(val, fallback="❌ Not Configured"):
        if val:
            if isinstance(val, int):
                ch = ctx.guild.get_channel(val)
                return f"✅ {ch.mention}" if ch else "⚠️ Channel Missing"
            return f"✅ {val}"
        return fallback

    embed = discord.Embed(title="👁️ Argus System Configuration", color=0x3498db)
    embed.description = f"Current configuration for **{ctx.guild.name}**. Use `{ctx.prefix}autosetup` to automate this."
    
    embed.add_field(name="Prefix", value=format_status(data.get("prefix"), "✅ !"), inline=True)
    embed.add_field(name="Awakening Stage", value=f"📡 Stage {data.get('awakening_stage', 1)}", inline=True)
    embed.add_field(name="Mood Mode", value=f"🎭 {data.get('mood_mode', 'NORMAL')}", inline=True)
    
    embed.add_field(name="Nexus Logging", value=format_status(data.get("logging_channel_id")), inline=False)
    embed.add_field(name="TempVoice Trigger", value=format_status(data.get("temp_voice_trigger_id")), inline=True)
    embed.add_field(name="TempVoice Category", value=format_status(data.get("temp_voice_category_id")), inline=True)
    embed.add_field(name="Interface Channel", value=format_status(data.get("temp_voice_interface_id")), inline=False)

    await ctx.send(embed=embed)


@bot.command(name="setactivity", help="[Admin] Set the bot's status/activity.")
async def set_activity(ctx: commands.Context, type: str, *, name: str):
    if ctx.author.id not in Config.ADMIN_USER_IDS and not ctx.author.guild_permissions.administrator:
        await ctx.send("🚫 You don't have permission.")
        return
    
    activity_type = {
        "playing": discord.ActivityType.playing,
        "streaming": discord.ActivityType.streaming,
        "listening": discord.ActivityType.listening,
        "watching": discord.ActivityType.watching,
        "competing": discord.ActivityType.competing,
    }.get(type.lower(), discord.ActivityType.watching)

    await bot.change_presence(activity=discord.Activity(type=activity_type, name=name))
    await ctx.send(f"✅ Activity updated to **{type.capitalize()} {name}**.")


@bot.command(name="autosetup", help="[Admin] Automatically create and configure all necessary channels.")
async def auto_setup(ctx: commands.Context):
    if ctx.author.id not in Config.ADMIN_USER_IDS and not ctx.author.guild_permissions.administrator:
        await ctx.send("🚫 You don't have permission.")
        return
    if not argus_manager:
        await ctx.send("❌ Argus systems not initialized.")
        return

    msg = await ctx.send("⚙️ **Initializing Fast Setup...** Creating categories and channels.")
    
    try:
        # 1. Create Category
        category = await ctx.guild.create_category("➕ Argus Systems")
        
        # 2. Create Channels
        trigger = await category.create_voice_channel("➕ Create VC")
        logs = await category.create_text_channel("👁️-nexus-logs")
        interface = await category.create_text_channel("🎮-vc-management")
        
        # 3. Update Database
        argus_manager.db.set_guild(
            ctx.guild.id,
            temp_voice_category_id=category.id,
            temp_voice_trigger_id=trigger.id,
            temp_voice_interface_id=interface.id,
            logging_channel_id=logs.id
        )
        
        # 4. Post Interface
        from core.temp_voice_ui import SharedTempVoiceView
        ui_embed = discord.Embed(
            title="TempVoice Interface",
            description="Use the buttons below to manage **your** temporary voice channel.",
            color=discord.Color.blue(),
        )
        view = SharedTempVoiceView(bot.temp_voice_manager, timeout=None)
        await interface.send(embed=ui_embed, view=view)
        
        await msg.edit(content=f"✅ **Setup Complete!**\n- Category: {category.mention}\n- Trigger: {trigger.mention}\n- Logs: {logs.mention}\n- Interface: {interface.mention}\n\nEverything is pre-configured. Join {trigger.mention} to start!")
        
    except discord.Forbidden:
        await msg.edit(content="❌ **Permission Error**: I don't have permission to create channels/categories.")
    except Exception as e:
        await msg.edit(content=f"❌ **System Error**: `{e}`")


@bot.command(name="status", help="Show bot status.")
async def status(ctx: commands.Context):
    vc_status = "Connected" if ctx.voice_client else "Not connected"
    
    listening_status = "Inactive"
    live_status = "Disconnected"
    if voice_manager:
        listener = voice_manager.get_listener(ctx.guild.id)
        if listener._listening:
            listening_status = "Active"
        if listener._live_session and listener._live_session.is_connected:
            live_status = "Connected"

    embed = discord.Embed(title="👁️ Argus System Status", color=discord.Color.blue())
    embed.add_field(name="Voice Channel", value=vc_status, inline=True)
    embed.add_field(name="Listening", value=listening_status, inline=True)
    embed.add_field(name="Live API", value=live_status, inline=True)
    
    if argus_manager:
        state = argus_manager.db.get_guild(ctx.guild.id)
        stage = state.get('awakening_stage', 1)
        mood = state.get('mood_mode', 'NORMAL')
        embed.add_field(name="Awakening", value=f"Stage {stage} ({mood})", inline=False)
        embed.add_field(name="Nexus Logger", value="Operational", inline=True)
        embed.add_field(name="Leveling", value="Active", inline=True)

    embed.add_field(name="AI Engine", value="Gemini 2.5 Flash Native (Sentient)", inline=True)
    embed.add_field(name="Voice", value=Config.GEMINI_VOICE, inline=True)
    
    tv_status = "Enabled" if (temp_voice_manager and temp_voice_manager.trigger_channel_id) else "Disabled"
    embed.add_field(name="TempVoice", value=tv_status, inline=True)
    embed.set_footer(text="Argus V2 • Surveillance & Evolution Integration")
    await ctx.send(embed=embed)

@bot.command(name="setprefix", help="[Admin] Set the command prefix for this server.")
async def set_prefix_cmd(ctx: commands.Context, new_prefix: str):
    if ctx.author.id not in Config.ADMIN_USER_IDS:
        await ctx.send("🚫 You don't have permission.")
        return
    if not argus_manager:
        await ctx.send("❌ Argus systems not initialized.")
        return
    
    if len(new_prefix) > 3 or " " in new_prefix:
        await ctx.send("❌ Prefix must be 1-3 characters and contain no spaces.")
        return
        
    argus_manager.db.set_guild(ctx.guild.id, prefix=new_prefix)
    await ctx.send(f"✅ **Command Prefix** recalibrated. New trigger: `{new_prefix}`")


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
        await ctx.send("🚫 Error: Insufficient permissions to execute this command.")
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument: `{error.param.name}`. Check `{ctx.prefix}help {ctx.command.name}`")
        return
    logger.error("Command error in %s: %s", ctx.command.name if ctx.command else "unknown", error)
    # Don't spam text for every error, but provide a generic failure if it's not handled
    try:
        await ctx.send(f"❌ System Exception: `{error}`")
    except Exception:
        pass


# ── Run ──────────────────────────────────────────────────────────────────────

def main():
    Config.validate()
    logger.info("Starting bot...")
    bot.run(Config.DISCORD_TOKEN)


if __name__ == "__main__":
    main()
