import logging
import discord
from typing import Optional, Dict, List, Any
from datetime import datetime
import core.embeds as E

logger = logging.getLogger(__name__)

CRISIS_KEYWORDS = [
    "suicide", "kill myself", "want to die", "self harm", "end my life", 
    "cut myself", "overdose", "hurt myself"
]

CRISIS_RESOURCES = (
    "❤️ **You are not alone.** If you're going through a tough time, please reach out for help:\n\n"
    "🇺🇸 **National Suicide Prevention Lifeline:** Call or text **988**\n"
    "🇬🇧 **Samaritans (UK):** Call **116 123**\n"
    "🌍 **Crisis Text Line:** Text **HOME** to **741741**\n\n"
    "I'm an AI and cannot provide professional medical or mental health help, but these humans can."
)

class WellnessManager:
    """Manages mood tracking, journaling, and safety detection."""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = getattr(bot, "argus_manager", None).db.sqlite if hasattr(bot, "argus_manager") else None

    def check_crisis(self, text: str) -> bool:
        """Simple check for crisis keywords."""
        text = text.lower()
        return any(keyword in text for keyword in CRISIS_KEYWORDS)

    async def handle_crisis(self, ctx_or_member):
        """Send crisis resources privately or to the channel."""
        embed = E.error("Safety Resource", CRISIS_RESOURCES, None)
        try:
            if isinstance(ctx_or_member, discord.Member):
                await ctx_or_member.send(embed=embed)
            else:
                await ctx_or_member.author.send(embed=embed)
                await ctx_or_member.send("❤️ I've sent you some safety resources in your DMs. Please take care.")
        except:
            if hasattr(ctx_or_member, "send"):
                await ctx_or_member.send(embed=embed)

    def log_mood(self, user_id: int, score: int, note: str = ""):
        if self.db:
            self.db.log_mood(user_id, score, note)
            
            # Update streak
            settings = self.db.get_wellness_settings(user_id)
            last = settings.get("last_checkin")
            streak = settings.get("checkin_streak", 0)
            
            now = datetime.utcnow().date()
            if last:
                last_date = datetime.fromisoformat(last).date()
                diff = (now - last_date).days
                if diff == 1:
                    streak += 1
                elif diff > 1:
                    streak = 1
            else:
                streak = 1
                
            self.db.update_wellness(user_id, last_checkin=datetime.utcnow().isoformat(), checkin_streak=streak)
            return streak
        return 0

    def get_mood_stats(self, user_id: int):
        if not self.db: return None
        history = self.db.get_mood_history(user_id, limit=7)
        settings = self.db.get_wellness_settings(user_id)
        
        if not history:
            return {"avg": 0, "count": 0, "streak": settings.get("checkin_streak", 0)}
            
        avg = sum(h['mood_score'] for h in history) / len(history)
        return {
            "avg": avg,
            "count": len(history),
            "streak": settings.get("checkin_streak", 0),
            "latest": history[0]
        }

    def add_journal(self, user_id: int, text: str):
        if self.db:
            self.db.add_journal_entry(user_id, text)
            return True
        return False
