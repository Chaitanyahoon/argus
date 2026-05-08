"""
Shared utilities for the Discord bot.
Provides fuzzy matching for members and channels with comprehensive type hints.
"""

import logging
from difflib import SequenceMatcher
from typing import Optional, Union

import discord

logger = logging.getLogger(__name__)

def fuzzy_find_member(guild: discord.Guild, name: str) -> Optional[discord.Member]:
    """Find a guild member by fuzzy-matching their display name or username."""
    name_lower = name.lower().strip()
    if not name_lower:
        return None
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
            
            # Exact substring match bonus (only for search strings of length >= 3)
            if len(name_lower) >= 3 and (name_lower in candidate.lower() or candidate.lower() in name_lower):
                score = max(score, 0.85)
            
            if score > best_score:
                best_score = score
                best_match = member

    if best_score >= 0.5:
        logger.info("Fuzzy matched '%s' -> %s (score: %.2f)", name, best_match, best_score)
        return best_match
    return None

def fuzzy_find_channel(
    guild: discord.Guild,
    name: str,
    channel_type: Optional[discord.ChannelType] = None
) -> Optional[Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel]]:
    """Find a guild channel by fuzzy-matching its name."""
    name_lower = name.lower().strip().replace(" ", "-")
    if not name_lower:
        return None
    best_match: discord.abc.GuildChannel | None = None
    best_score: float = 0.0

    for channel in guild.channels:
        if channel_type and channel.type != channel_type:
            continue
        candidate = channel.name.lower()
        score = SequenceMatcher(None, name_lower, candidate).ratio()
        
        # Prefix or suffix match bonus
        if (candidate.startswith(name_lower) or candidate.endswith(name_lower) or
            name_lower.startswith(candidate) or name_lower.endswith(candidate)):
            score = max(score, 0.75)
        
        # Apply stronger penalty for very long mismatched queries
        len_diff = abs(len(name_lower) - len(candidate))
        max_len = max(len(name_lower), len(candidate))
        if max_len > 8 and len_diff > max_len * 0.4:  # Long queries with significant length mismatch
            length_penalty = (len_diff - max_len * 0.4) / max_len * 0.8
            score *= (1 - length_penalty)
        
        if len(name_lower) >= 3 and (name_lower in candidate or candidate in name_lower):
            score = max(score, 0.85)
        if score > best_score:
            best_score = score
            best_match = channel

    if best_score >= 0.59:
        return best_match
    return None
