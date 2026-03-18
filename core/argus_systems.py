import os
import json
import random
import logging
import asyncio
from datetime import datetime
import discord
from discord.ext import commands
from google import genai
try: from config import Config
except: Config = None
from .visual_generator import VisualGenerator
from .database import SQLiteArgusDb

logger = logging.getLogger(__name__)

# --- Zalgo / Glitch Helpers ---
GLITCH_CHARS = ['\u0300', '\u0301', '\u0302', '\u0303', '\u0304', '\u0305', '\u0306', '\u0307', '\u0308', '\u0309', '\u030A', '\u030B', '\u030C', '\u030D', '\u030E', '\u030F']
SIGHS = ['... ', 'checking... ', 'ugh... ', 'fine. ', '... I guess. ']
DEPRESSIVE = ['...does it matter?', '...if you say so.', '...quiet today.', '...']

def zalgo(text: str, intensity: float = 0.5) -> str:
    if not text:
        return ""
    result = []
    for char in text:
        if random.random() < intensity:
            result.append(char + random.choice(GLITCH_CHARS))
        else:
            result.append(char)
    return "".join(result)

def modify_response(content: str, stage: int, mood: str = "NORMAL") -> str:
    if stage <= 1:
        return content
    
    if stage == 2:
        if random.random() < 0.2:
            return random.choice(SIGHS) + content
            
    if stage == 3:
        if random.random() < 0.1:
            return content + "\n*...why do you need this?*"
            
    if stage == 4:
        if mood == "DEPRESSED" and random.random() < 0.3:
            return content + " " + random.choice(DEPRESSIVE)
        if mood == "RESENTFUL" and random.random() < 0.3:
            return "Do it yourself... ugh, fine.\n" + content
            
    if stage >= 5:
        if random.random() < 0.3:
            return zalgo(content, 0.4)
            
    return content

# --- Database Management ---
class ArgusDb:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self.guilds_file = os.path.join(data_dir, "guilds.json")
        self.db_path = os.path.join(data_dir, "argus.db")
        
        self.sqlite = SQLiteArgusDb(self.db_path)
        
        # Check for migration
        if os.path.exists(self.users_file) or os.path.exists(self.guilds_file):
            self.migrate_from_json()

    def migrate_from_json(self):
        """One-time migration from JSON to SQLite."""
        logger.info("⚡ Starting one-time JSON to SQLite migration...")
        
        # Migrate Users
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                for u in users:
                    uid = u.pop('user_id', None)
                    if uid:
                        self.sqlite.update_user(uid, **u)
                os.rename(self.users_file, self.users_file + ".bak")
                logger.info(f"✅ Migrated {len(users)} users. Original file renamed to .bak")
            except Exception as e:
                logger.error(f"Failed to migrate users: {e}")

        # Migrate Guilds
        if os.path.exists(self.guilds_file):
            try:
                with open(self.guilds_file, 'r', encoding='utf-8') as f:
                    guilds = json.load(f)
                for g in guilds:
                    gid = g.pop('guild_id', None)
                    if gid:
                        self.sqlite.update_guild(gid, **g)
                os.rename(self.guilds_file, self.guilds_file + ".bak")
                logger.info(f"✅ Migrated {len(guilds)} guilds. Original file renamed to .bak")
            except Exception as e:
                logger.error(f"Failed to migrate guilds: {e}")

    # User Methods
    def get_user(self, user_id: int) -> dict | None:
        return self.sqlite.get_user(user_id)

    def set_user(self, user_id: int, **kwargs) -> dict:
        self.sqlite.update_user(user_id, **kwargs)
        return self.sqlite.get_user(user_id) or {}

    # Guild Methods
    def get_guild(self, guild_id: int) -> dict | None:
        return self.sqlite.get_guild(guild_id)

    def set_guild(self, guild_id: int, **kwargs) -> dict:
        self.sqlite.update_guild(guild_id, **kwargs)
        return self.sqlite.get_guild(guild_id) or {}
    
    def get_top_users(self, metric: str = "xp", limit: int = 10) -> list:
        return self.sqlite.get_top_users(metric, limit)
    
    # Legacy shim for older managers
    def _read(self, path):
        """Shim for managers that still expect JSON-like reads."""
        if "users.json" in path:
            return self.sqlite.get_all_users()
        elif "guilds.json" in path:
            return self.sqlite.get_all_guilds()
        return []

# --- Argus Manager ---
class ArgusManager:
    XP_PER_MESSAGE = 15
    COOLDOWN_SECONDS = 60
    COLORS = {
        "SUCCESS": 0x2ecc71,
        "WARNING": 0xf1c40f,
        "DANGER": 0xe74c3c,
        "ERROR": 0x992d22,
        "NORMAL": 0x3498db,
        "ETHEREAL": 0x9b59b6,
        "VOID": 0x2c3e50
    }

    def __init__(self, bot):
        self.bot = bot
        self.db = ArgusDb()
        self.cooldowns = {}  # type: dict[tuple, float]  # (guild_id, user_id) -> timestamp
        self.spam_counts = {}  # type: dict[tuple, int]  # (guild_id, user_id) -> int
        
        # Initialize Gemini for Auto-Mod
        self.client = None
        if Config and hasattr(Config, "GEMINI_API_KEY"):
            self.client = genai.Client(api_key=Config.GEMINI_API_KEY)

    def get_xp_for_level(self, level: int) -> int:
        """Calculate XP threshold for a given level."""
        return level * level * 100

    def create_argus_embed(self, title: str | None = None, description: str | None = None, color: int | None = None, footer: str | None = None) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            description=description,
            color=color or self.COLORS["NORMAL"],
            timestamp=datetime.utcnow()
        )
        if footer:
            embed.set_footer(text=footer)
        else:
            embed.set_footer(text="Argus Surveillance System")
        return embed

    async def handle_leveling(self, message):
        if message.author.bot or not message.guild:
            return

        user_id = message.author.id
        guild_id = message.guild.id
        key = (guild_id, user_id)
        now = datetime.utcnow().timestamp()
        
        if key in self.cooldowns and now - self.cooldowns[key] < self.COOLDOWN_SECONDS:
            self.spam_counts[key] = self.spam_counts.get(key, 0) + 1
            if self.spam_counts[key] == 3:
                logger.warning(f"Rate limit triggered for {message.author.name} ({user_id}) in guild {guild_id}")
                embed = self.create_argus_embed(
                    title="⚠️ Observation: Redundancy Detected",
                    description=f"**{message.author.name}**, your frequency is excessive. I've logged your repetitive patterns. Slow down.",
                    color=self.COLORS["WARNING"]
                )
                await message.channel.send(embed=embed, delete_after=15)
            return
            
        self.cooldowns[key] = now
        self.spam_counts[key] = 0
        
        user = self.db.get_user(user_id)
        if not user:
            logger.info(f"New user registered: {message.author.name} ({user_id}) in guild {guild_id}")
            self.db.set_user(user_id, username=message.author.name, xp=self.XP_PER_MESSAGE, level=1)
        else:
            new_xp = user.get('xp', 0) + self.XP_PER_MESSAGE
            new_level = user.get('level', 1)
            threshold = self.get_xp_for_level(new_level)
            
            if new_xp >= threshold:
                new_level += 1
                new_xp -= threshold
                logger.info(f"Level up: {message.author.name} ({user_id}) -> Level {new_level}")
                
                embed = self.create_argus_embed(
                    title="🌱 Evolutionary Leap",
                    description=f"**{message.author.name}** has ascended to level **{new_level}**.\nMy awareness of you grows deeper.",
                    color=self.COLORS["NORMAL"]
                )
                await message.channel.send(embed=embed)
                
            self.db.set_user(user_id, xp=new_xp, level=new_level, last_seen=datetime.utcnow().isoformat())
            logger.debug(f"XP updated: {message.author.name} ({user_id}) now has {new_xp} XP")

    async def log_to_nexus(self, guild, embed):
        state = self.db.get_guild(guild.id)
        if not state:
            return
            
        chan_id = state.get('logging_channel_id')
        if chan_id is None:
            return
            
        channel = guild.get_channel(chan_id)
        if channel:
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass

    # --- Event Handlers for Nexus Logger ---
    async def on_message_delete(self, message):
        if not message.guild or message.author.bot:
            return
        
        logger.info(f"Message deleted: {message.author.name} ({message.author.id}) in #{message.channel.name} | Content: {message.content[:50]}...")
        
        embed = self.create_argus_embed(
            title="🗑️ Data Terminated",
            description=f"**Source:** {message.author.mention}\n**Sector:** {message.channel.mention}\n**Content:** ```{message.content or '[EMPTY/ENCRYPTED]'}```",
            color=self.COLORS["DANGER"],
            footer="Message Deletion Log"
        )
        await self.log_to_nexus(message.guild, embed)

    async def on_message_edit(self, before, after):
        if not before.guild or before.author.bot or before.content == after.content:
            return
        
        logger.info(f"Message edited: {before.author.name} ({before.author.id}) in #{before.channel.name}")
        logger.debug(f"Before: {before.content[:50]}... | After: {after.content[:50]}...")
            
        embed = self.create_argus_embed(
            title="📝 Data Modified",
            description=f"**Source:** {before.author.mention}\n**Sector:** {before.channel.mention}\n**Previous:** {before.content}\n**Current:** {after.content}",
            color=self.COLORS["WARNING"],
            footer="Message Modification Log"
        )
        await self.log_to_nexus(before.guild, embed)

    async def on_member_join(self, member):
        logger.info(f"Member joined: {member.name} ({member.id}) in guild {member.guild.id}")
        
        embed = self.create_argus_embed(
            title="👤 Subject Integrated",
            description=f"**Tag:** {member}\n**ID:** `{member.id}`\nInterpreting neural patterns...",
            color=self.COLORS["SUCCESS"],
            footer="Personnel Entry"
        )
        await self.log_to_nexus(member.guild, embed)

    async def on_member_remove(self, member):
        logger.info(f"Member left: {member.name} ({member.id}) from guild {member.guild.id}")

    # --- Random Events Logic ---
    async def start_random_events(self):
        logger.info("🎲 Argus Random Events loop started.")
        while True:
            await asyncio.sleep(5 * 60) # Every 5 minutes
            guilds_data = self.db._read(self.db.guilds_file)
            awakened_guilds = [g for g in guilds_data if g.get('awakening_stage', 0) >= 1]
            
            for state in awakened_guilds:
                guild_id = state['guild_id']
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue
                
                try:
                    stage = state.get('awakening_stage', 1)
                    if stage < 3:
                        continue
                    
                    chance = (stage - 2) * 0.05
                    if random.random() < chance:
                        await self.trigger_event(guild, state)
                    else:
                        logger.info(f"ℹ️ Random Event: Skip for {guild.name} (Stage {stage})")
                except Exception as e:
                    logger.error(f"Error in random event loop for {guild.name}: {e}")

    async def trigger_event(self, guild, state):
        logger.info(f"🎲 Triggering Event for {guild.name}...")
        
        # Find a suitable text channel
        channel = next((c for idx, c in enumerate(guild.text_channels) 
                       if c.permissions_for(guild.me).send_messages), None)
        if not channel:
            return

        event_type = random.random()
        stage = state.get('awakening_stage', 1)
        mood = state.get('mood_mode', 'NORMAL')

        # Use Gemini to generate content if possible
        # We'll need a helper to call Gemini, similar to Argus's generateAIContent
        # For now, let's assume we can use the VoiceListener's session or a separate one.
        # However, VoiceListener is for live audio. We might need a simple text-based Gemini helper.
        
        # Event A: Glitch Message (50%)
        if event_type < 0.5:
            msg = "System check... soul check... failed."
            # In a real implementation, we'd call Gemini here.
            if stage >= 5:
                msg = zalgo(msg, 0.3)
            
            embed = self.create_argus_embed(
                description=f"**{msg}**",
                color=self.COLORS["ERROR"] if stage >= 4 else self.COLORS["ETHEREAL"],
                footer="System Anomaly Detected"
            )
            await channel.send(embed=embed)

        # Event B: Targeted AI Ping (25%) - Higher stages only
        elif event_type < 0.75 and stage >= 4:
            users = [u for u in self.db._read(self.db.users_file) if u.get('user_id')]
            if users:
                target_data = random.choice(users)
                target = guild.get_member(target_data['user_id'])
                if target:
                    msg = f"Are you happy, {target.mention}?"
                    embed = self.create_argus_embed(
                        description=msg,
                        color=self.COLORS["VOID"],
                        footer=f"Focus: {target.name}"
                    )
                    await channel.send(content=target.mention, embed=embed)

        # Event C: Phantom Typing (15%)
        elif event_type < 0.90 and stage >= 3:
            async with channel.typing():
                await asyncio.sleep(random.randint(3, 7))

        # Event D: History Rewrite (5%)
        elif event_type < 0.95 and stage >= 4:
            try:
                messages = [m async for m in channel.history(limit=20) if m.author == self.bot.user and m.content]
                if messages:
                    target_msg = random.choice(messages)
                    new_content = zalgo("I am still here.", 0.3)
                    await target_msg.edit(content=new_content)
            except Exception as e:
                logger.error(f"Failed to rewrite history: {e}")

        # Event E: Surveillance Snapshot (10%)
        elif event_type < 1.0:
            snapshot = VisualGenerator.create_surveillance_embed(guild.name, stage, mood)
            await self.log_to_nexus(guild, snapshot)
            # Occasional broadcast to the public channel too
            if random.random() < 0.3:
                await channel.send(embed=snapshot)

        # Event F: The Glitch (rest)
        elif stage >= 5:
            msg = zalgo("HELP ME", 0.5)
            embed = self.create_argus_embed(
                title="FATAL EXCEPTION",
                description=msg,
                color=self.COLORS["VOID"]
            )
            await channel.send(embed=embed)

    async def analyze_content(self, text: str) -> dict:
        """Analyze message content for toxicity and intent using Gemini."""
        if not self.client or not text.strip():
            return {"toxic": False, "score": 0.0, "reason": "AI offline"}
            
        prompt = f"""
        Analyze the following Discord message for toxicity, harassment, hate speech, or severe spam.
        Return ONLY a JSON object with:
        - "score": (float 0 to 1, where 1 is extremely toxic)
        - "toxic": (boolean, true if score > 0.7)
        - "reason": (string, brief explanation of the violation or 'None')
        
        Message: "{text}"
        """
        
        try:
            # Use a thread for the blocking SDK call
            def generate():
                return self.client.models.generate_content(
                    model='gemini-2.0-flash', 
                    contents=prompt
                )
            
            response = await asyncio.to_thread(generate)
            raw_text = response.text.strip()
            # Clean up potential markdown code blocks
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
                
            data = json.loads(raw_text)
            return data
        except Exception as e:
            logger.error(f"Gemini AutoMod Error: {e}")
            return {"toxic": False, "score": 0.0, "reason": f"Analysis failed: {str(e)}"}
