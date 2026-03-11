"""
Shared utilities for the Discord bot.
"""

import logging
from difflib import SequenceMatcher
import discord

logger = logging.getLogger(__name__)

def fuzzy_find_member(guild: discord.Guild, name: str) -> discord.Member | None:
    """Find a guild member by fuzzy-matching their display name or username."""
    name_lower = name.lower().strip()
    best_match: discord.Member | None = None
    best_score: float = 0.0

    for member in guild.members:
        for candidate in [
            member.display_name.lower(),
            member.name.lower(),
            getattr(member, "global_name", "") or "",
        ]:
            if not candidate:
                continue
            # Basic ratio
            score = SequenceMatcher(None, name_lower, candidate.lower()).ratio()
            # Penalty for very short names unless they match exactly
            if len(name_lower) < 3 and name_lower != candidate.lower():
                score *= 0.5
            
            # Exact substring match bonus
            if name_lower in candidate.lower() or candidate.lower() in name_lower:
                score = max(score, 0.85)
            
            if score > best_score:
                best_score = score
                best_match = member

    if best_score >= 0.5:
        logger.info("Fuzzy matched '%s' -> %s (score: %.2f)", name, best_match, best_score)
        return best_match
    return None

def fuzzy_find_channel(
    guild: discord.Guild, name: str, channel_type: discord.ChannelType | None = None
) -> discord.abc.GuildChannel | None:
    """Find a guild channel by fuzzy-matching its name."""
    name_lower = name.lower().strip().replace(" ", "-")
    best_match: discord.abc.GuildChannel | None = None
    best_score: float = 0.0

    for channel in guild.channels:
        if channel_type and channel.type != channel_type:
            continue
        candidate = channel.name.lower()
        score = SequenceMatcher(None, name_lower, candidate).ratio()
        if name_lower in candidate or candidate in name_lower:
            score = max(score, 0.85)
        if score > best_score:
            best_score = score
            best_match = channel

    if best_score >= 0.5:
        return best_match
    return None
