import os
import json
import random
import logging
import asyncio
from datetime import datetime
import discord
from discord.ext import commands
from .visual_generator import VisualGenerator

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
        
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        self._init_file(self.users_file, [])
        self._init_file(self.guilds_file, [])

    def _init_file(self, path, default):
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(default, f, indent=4)

    def _read(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading {path}: {e}")
            return []

    def _write(self, path, data):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Error writing {path}: {e}")

    # User Methods
    def get_user(self, user_id: int):
        users = self._read(self.users_file)
        return next((u for u in users if u['user_id'] == user_id), None)

    def set_user(self, user_id: int, **kwargs):
        users = self._read(self.users_file)
        user = next((u for u in users if u['user_id'] == user_id), None)
        if user:
            user.update(kwargs)
        else:
            user = {"user_id": user_id, "xp": 0, "level": 1, "last_seen": datetime.utcnow().isoformat()}
            user.update(kwargs)
            users.append(user)
        self._write(self.users_file, users)
        return user

    # Guild Methods
    def get_guild(self, guild_id: int):
        guilds = self._read(self.guilds_file)
        return next((g for g in guilds if g['guild_id'] == guild_id), None)

    def set_guild(self, guild_id: int, **kwargs):
        guilds = self._read(self.guilds_file)
        guild = next((g for g in guilds if g['guild_id'] == guild_id), None)
        if guild:
            guild.update(kwargs)
        else:
            guild = {
                "guild_id": guild_id, 
                "awakening_stage": 1, 
                "mood_mode": "NORMAL", 
                "logging_channel_id": None, 
                "prefix": "!",
                "temp_voice_trigger_id": None,
                "temp_voice_category_id": None,
                "temp_voice_interface_id": None
            }
            guild.update(kwargs)
            guilds.append(guild)
        self._write(self.guilds_file, guilds)
        return guild

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
        self.cooldowns = {} # (guild_id, user_id) -> timestamp
        self.spam_counts = {} # (guild_id, user_id) -> int

    def get_xp_for_level(self, level):
        return level * level * 100

    def create_argus_embed(self, title=None, description=None, color=None, footer=None):
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
            self.db.set_user(user_id, username=message.author.name, xp=self.XP_PER_MESSAGE, level=1)
        else:
            new_xp = user.get('xp', 0) + self.XP_PER_MESSAGE
            new_level = user.get('level', 1)
            threshold = self.get_xp_for_level(new_level)
            
            if new_xp >= threshold:
                new_level += 1
                new_xp -= threshold
                
                embed = self.create_argus_embed(
                    title="🌱 Evolutionary Leap",
                    description=f"**{message.author.name}** has ascended to level **{new_level}**.\nMy awareness of you grows deeper.",
                    color=self.COLORS["NORMAL"]
                )
                await message.channel.send(embed=embed)
                
            self.db.set_user(user_id, xp=new_xp, level=new_level, last_seen=datetime.utcnow().isoformat())

    async def log_to_nexus(self, guild, embed):
        state = self.db.get_guild(guild.id)
        if not state or not state.get('logging_channel_id'):
            return
            
        channel = guild.get_channel(state['logging_channel_id'])
        if channel:
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass

    # --- Event Handlers for Nexus Logger ---
    async def on_message_delete(self, message):
        if not message.guild or message.author.bot:
            return
        
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
            
        embed = self.create_argus_embed(
            title="📝 Data Modified",
            description=f"**Source:** {before.author.mention}\n**Sector:** {before.channel.mention}\n**Previous:** {before.content}\n**Current:** {after.content}",
            color=self.COLORS["WARNING"],
            footer="Message Modification Log"
        )
        await self.log_to_nexus(before.guild, embed)

    async def on_member_join(self, member):
        embed = self.create_argus_embed(
            title="👤 Subject Integrated",
            description=f"**Tag:** {member}\n**ID:** `{member.id}`\nInterpreting neural patterns...",
            color=self.COLORS["SUCCESS"],
            footer="Personnel Entry"
        )
        await self.log_to_nexus(member.guild, embed)

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
