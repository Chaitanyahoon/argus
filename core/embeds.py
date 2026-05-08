"""
core/embeds.py — Argus shared embed design system.

All bot output should use the helpers here to ensure a consistent
premium look: brand colours, timestamps, author branding, and footer.
"""

import discord
from discord.ext import commands
from datetime import datetime, timezone
from typing import Optional

# ── Brand palette ──────────────────────────────────────────────────────────────
C_PRIMARY  = 0x0066FF   # Electric blue  — info / playing
C_SUCCESS  = 0x00FF88   # Neon green     — confirmations
C_WARNING  = 0xFFBA00   # Amber          — warnings / skipped
C_ERROR    = 0xFF3355   # Red            — errors / stop
C_PURPLE   = 0x6600FF   # Deep purple    — loop / shuffle / special
C_NAVY     = 0x001A4D   # Dark navy      — neutral / stats
C_GOLD     = 0xFFD700   # Gold           — achievements / leaderboard

BOT_NAME   = "Argus"
BOT_ICON   = "https://cdn.discordapp.com/embed/avatars/0.png"   # overridden at runtime

# ── Base embed factory ─────────────────────────────────────────────────────────

def base(
    title:       str,
    description: str = "",
    color:       int = C_PRIMARY,
    *,
    ctx:         Optional[commands.Context] = None,
    timestamp:   bool = True,
) -> discord.Embed:
    """
    Base embed — consistent style for every response.
    Adds: timestamp, author line (if ctx given), Argus footer.
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(timezone.utc) if timestamp else None,
    )
    if ctx:
        embed.set_author(
            name=ctx.author.display_name,
            icon_url=ctx.author.display_avatar.url,
        )
    embed.set_footer(text=f"👁  {BOT_NAME}")
    return embed


# ── Shortcut constructors ──────────────────────────────────────────────────────

def success(title: str, description: str = "", ctx=None) -> discord.Embed:
    return base(title, description, C_SUCCESS, ctx=ctx)

def error(title: str, description: str = "", ctx=None) -> discord.Embed:
    return base(title, description, C_ERROR, ctx=ctx)

def warning(title: str, description: str = "", ctx=None) -> discord.Embed:
    return base(title, description, C_WARNING, ctx=ctx)

def info(title: str, description: str = "", ctx=None) -> discord.Embed:
    return base(title, description, C_PRIMARY, ctx=ctx)

def purple(title: str, description: str = "", ctx=None) -> discord.Embed:
    return base(title, description, C_PURPLE, ctx=ctx)

def gold(title: str, description: str = "", ctx=None) -> discord.Embed:
    return base(title, description, C_GOLD, ctx=ctx)

def navy(title: str, description: str = "", ctx=None) -> discord.Embed:
    return base(title, description, C_NAVY, ctx=ctx)


# ── Specialised builders ───────────────────────────────────────────────────────

def now_playing(track, volume: int = 100, loop: str = "none", shuffle: bool = False) -> discord.Embed:
    """Rich Now Playing card."""
    dur = _fmt_dur(track.duration)
        """Music playback disabled in this deployment."""
        embed = discord.Embed(title="🎵 Music Disabled", color=discord.Color.dark_gray())
        embed.description = "Music playback features have been disabled for this deployment to reduce hosting costs."
        return embed


def queue_embed(player) -> discord.Embed:
    """Full queue display with status footer."""
    q = player.queue

    status_parts = []
    if player.loop_mode == "track": status_parts.append("🔂 Track Loop")
    if player.loop_mode == "queue": status_parts.append("🔁 Queue Loop")
    if player.shuffle:              status_parts.append("🔀 Shuffle")
    status_parts.append(f"🔊 {int(player.volume * 100)}%")

    lines: list[str] = []
    if player.current:
        lines.append(f"▶️  **{player.current.title}**{_fmt_dur(player.current.duration)}")
        lines.append("")

    if q:
        for i, t in enumerate(q[:10], 1):
            lines.append(f"`{i:>2}.`  {t.title}{_fmt_dur(t.duration)}  —  *{t.requested_by_name}*")
        if len(q) > 10:
            lines.append(f"\n*… and **{len(q) - 10}** more tracks*")
    else:
        lines.append("*Queue is empty*")

        """Music queue display disabled in this deployment."""
        embed = discord.Embed(title="🎶 Music Disabled", color=discord.Color.dark_gray())
        embed.description = "Music features are disabled; the queue is not available on this deployment."
        return embed


def level_up(member: discord.Member, new_level: int) -> discord.Embed:
    """Level-up announcement."""
    embed = base(
        "⭐  Level Up!",
        f"**{member.display_name}** reached **Level {new_level}**! 🎉",
        C_GOLD,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    return embed


def automod_action(
    action: str,
    user: discord.Member,
    reason: str,
    confidence: float,
) -> discord.Embed:
    """AutoMod action card posted to mod log."""
    icons  = {"delete": "🗑️", "warn": "⚠️", "timeout": "🔕", "ban": "🔨"}
    colors = {"delete": C_ERROR, "warn": C_WARNING, "timeout": C_WARNING, "ban": C_ERROR}
    icon   = icons.get(action, "🛡️")
    color  = colors.get(action, C_NAVY)
    embed  = base(
        f"{icon}  AutoMod — {action.title()}",
        f"**User:** {user.mention}  (`{user.id}`)\n**Reason:** {reason}",
        color,
    )
    conf_label = "HIGH" if confidence >= 0.8 else "MEDIUM" if confidence >= 0.5 else "LOW"
    embed.add_field(name="Confidence", value=f"`{conf_label}`  {confidence:.0%}", inline=True)
    embed.add_field(name="Action",     value=action.title(),                       inline=True)
    return embed


# ── Internal helpers ───────────────────────────────────────────────────────────

def _fmt_dur(seconds: int | None) -> str:
    if not seconds:
        return ""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"  `{h}:{m:02d}:{s:02d}`" if h else f"  `{m}:{s:02d}`"
