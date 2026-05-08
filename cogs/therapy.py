import discord
from discord.ext import commands
import asyncio
import logging
import datetime
from typing import List, Dict, Any, Optional
import core.embeds as E
from core.therapy import WellnessManager

class TherapyCog(commands.Cog, name="Wellness"):
    """Therapy-lite and wellness companion features."""
    
    def __init__(self, bot):
        self.bot = bot
        self.wellness = WellnessManager(bot)
        # Re-attach to bot for access from other cogs if needed
        self.bot.wellness_manager = self.wellness

    @commands.command(name="checkin", help="Guided mood check-in.")
    async def checkin(self, ctx: commands.Context):
        """Guided mood check-in flow."""
        embed = E.info("🌈 Daily Check-in", "How are you feeling today, **" + ctx.author.name + "**?\n\n"
                       "Please react with the emoji that best matches your mood:\n"
                       "1️⃣ — Great\n"
                       "2️⃣ — Good\n"
                       "3️⃣ — Okay / Neutral\n"
                       "4️⃣ — Not so good\n"
                       "5️⃣ — Struggling", ctx)
        
        msg = await ctx.send(embed=embed)
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        for e in emojis:
            await msg.add_reaction(e)
            
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in emojis and reaction.message.id == msg.id
            
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            score = 6 - emojis.index(str(reaction.emoji)) # 5=Great, 1=Struggling (inverted for math)
            # Re-map: 1=Great, 2=Good, 3=Okay, 4=Bad, 5=Crisis
            actual_score = emojis.index(str(reaction.emoji)) + 1
            
            # Save mood
            streak = self.wellness.log_mood(ctx.author.id, actual_score)
            
            # Feedback
            responses = {
                1: ("That's wonderful! I'm glad you're having a great day.", E.C_SUCCESS),
                2: ("Glad to hear you're doing well.", E.C_SUCCESS),
                3: ("Stay steady. I'm here if you need to talk.", E.C_PRIMARY),
                4: ("I'm sorry you're not feeling great. Want to try a breathing exercise? `!breathe`", E.C_WARNING),
                5: ("I'm here for you. You don't have to carry this alone.", E.C_ERROR)
            }
            
            text, color = responses[actual_score]
            res_embed = E.base("Check-in Recorded", text + f"\n\n🔥 Streak: **{streak} days**", color, ctx=ctx)
            await msg.clear_reactions()
            await msg.edit(embed=res_embed)
            
            if actual_score == 5:
                await self.wellness.handle_crisis(ctx)
                
        except asyncio.TimeoutError:
            await msg.clear_reactions()
            await msg.edit(embed=E.error("Check-in Timed Out", "We can try again later.", ctx))

    @commands.command(name="journal", help="Private DM-based journaling.")
    async def journal(self, ctx: commands.Context, *, entry: Optional[str] = None):
        """Private journaling."""
        if entry:
            # Inline entry
            if self.wellness.check_crisis(entry):
                await self.wellness.handle_crisis(ctx)
            
            self.wellness.add_journal(ctx.author.id, entry)
            await ctx.message.delete()
            await ctx.send(embed=E.success("Journal Saved", "Your entry has been encrypted and stored privately.", ctx), delete_after=5)
        else:
            # DM flow
            try:
                await ctx.author.send(embed=E.info("📓 Private Journal", "Tell me what's on your mind. Your next message here will be saved as a private journal entry.", None))
                await ctx.send("📥 I've sent you a DM to start your private journal entry.", delete_after=5)
            except discord.Forbidden:
                await ctx.send(embed=E.error("DM Blocked", "I can't DM you! Please enable DMs for this server to use the journal.", ctx))
                return
            
            def check_dm(m):
                return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)
                
            try:
                m = await self.bot.wait_for('message', timeout=300.0, check=check_dm)
                if self.wellness.check_crisis(m.content):
                    await self.wellness.handle_crisis(ctx.author)
                
                self.wellness.add_journal(ctx.author.id, m.content)
                await ctx.author.send(embed=E.success("Journal Saved", "Your entry has been secured.", None))
            except asyncio.TimeoutError:
                await ctx.author.send(embed=E.error("Journal Timed Out", "Session ended. Entry was not saved.", None))

    @commands.command(name="breathe", help="Timed breathing exercise.")
    async def breathe(self, ctx: commands.Context):
        """Guided breathing (4-7-8)."""
        embed = E.info("🫁 Deep Breathing", "Let's take a moment. We'll do a 4-7-8 cycle.", ctx)
        msg = await ctx.send(embed=embed)
        
        steps = [
            ("🌬️ Inhale deeply...", 4, E.C_PRIMARY),
            ("✋ Hold your breath...", 7, E.C_PURPLE),
            ("💨 Exhale slowly...", 8, E.C_SUCCESS)
        ]
        
        for _ in range(2): # 2 cycles
            for text, duration, color in steps:
                for i in range(duration, 0, -1):
                    bar = "█" * i + "░" * (duration - i)
                    step_embed = E.base("Deep Breathing", f"**{text}**\n`{bar}` {i}s", color, ctx=ctx)
                    await msg.edit(embed=step_embed)
                    await asyncio.sleep(1)
                    
        await msg.edit(embed=E.success("Exercise Complete", "Hope you're feeling a bit more grounded.", ctx))

    @commands.command(name="ground", help="5-4-3-2-1 grounding technique.")
    async def ground(self, ctx: commands.Context):
        """5-4-3-2-1 grounding technique."""
        steps = [
            "👀 Look around you. Name **5 things** you can see.",
            "✋ Name **4 things** you can feel (e.g., texture of your shirt).",
            "👂 Name **3 things** you can hear right now.",
            "👃 Name **2 things** you can smell.",
            "👅 Name **1 thing** you can taste."
        ]
        
        embed = E.info("🌱 Grounding Exercise", "Focus on your surroundings. I'll guide you through the 5-4-3-2-1 technique.", ctx)
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(3)
        
        for step in steps:
            curr_embed = E.info("Grounding Exercise", step + "\n\n*Take your time. Type anything to continue.*", ctx)
            await msg.edit(embed=curr_embed)
            
            try:
                await self.bot.wait_for('message', timeout=60.0, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            except asyncio.TimeoutError:
                break
                
        await msg.edit(embed=E.success("Grounding Complete", "You've successfully refocused your senses.", ctx))

    @commands.command(name="moodstats", help="View your wellness overview.")
    async def moodstats(self, ctx: commands.Context):
        """View mood stats."""
        stats = self.wellness.get_mood_stats(ctx.author.id)
        if not stats or stats['count'] == 0:
            await ctx.send(embed=E.info("No Data", "Do your first `!checkin` to start tracking!", ctx))
            return
            
        avg = stats['avg']
        bar = "█" * round(avg * 2) + "░" * (10 - round(avg * 2))
        
        embed = E.navy("📊 Wellness Overview", "", ctx)
        embed.add_field(name="Average Mood", value=f"`{bar}` {avg:.1f}/5", inline=True)
        embed.add_field(name="🔥 Streak", value=f"**{stats['streak']} days**", inline=True)
        embed.add_field(name="📅 Entries", value=f"**{stats['count']}** (Last 7 days)", inline=True)
        
        if stats.get('latest'):
            latest = stats['latest']
            # Correcting datetime usage: datetime module has a datetime class
            dt_obj = datetime.datetime.fromisoformat(latest['timestamp'])
            date_str = dt_obj.strftime("%b %d")
            embed.add_field(name="Latest Entry", value=f"Score: `{latest['mood_score']}` on {date_str}", inline=False)
            
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Passive crisis detection in all messages."""
        if message.author.bot or not message.guild:
            return
            
        if self.wellness.check_crisis(message.content):
            await self.wellness.handle_crisis(message)
        
        # IMPORTANT: always forward to command processor
        await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(TherapyCog(bot))
