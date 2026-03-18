import discord
from discord.ext import commands
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AutoModCog(commands.Cog, name="AutoMod"):
    """AI-powered moderation and surveillance."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_argus_manager(self):
        return getattr(self.bot, "argus_manager", None)

    @commands.group(name="automod", help="Configure AI Auto-Moderation settings.")
    @commands.has_permissions(administrator=True)
    async def automod(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @automod.command(name="toggle", help="Toggle toxicity or spam detection (e.g., !automod toggle toxicity).")
    async def toggle_mod(self, ctx: commands.Context, setting: str):
        am = self.get_argus_manager()
        if not am: return
        
        setting = setting.lower()
        if setting not in ["toxicity", "spam"]:
            await ctx.send("❌ Use `toxicity` or `spam`.")
            return
            
        guild_data = am.db.get_guild(ctx.guild.id) or {}
        key = f"automod_{setting}_enabled"
        current = guild_data.get(key, 0)
        new_val = 1 if current == 0 else 0
        
        am.db.update_guild(ctx.guild.id, **{key: new_val})
        status = "ENABLED" if new_val == 1 else "DISABLED"
        await ctx.send(f"🛡️ AI **{setting.upper()}** detection is now **{status}**.")

    @automod.command(name="threshold", help="Set the AI sensitivity threshold (0.1 to 1.0).")
    async def set_threshold(self, ctx: commands.Context, value: float):
        am = self.get_argus_manager()
        if not am: return
        
        if not (0.1 <= value <= 1.0):
            await ctx.send("❌ Threshold must be between 0.1 (strict) and 1.0 (lenient).")
            return
            
        am.db.update_guild(ctx.guild.id, automod_threshold=value)
        await ctx.send(f"🎯 AI sensitivity threshold set to **{value}**.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or not message.content:
            return
            
        am = self.get_argus_manager()
        if not am: return
        
        guild_data = am.db.get_guild(message.guild.id) or {}
        
        # 1. Toxicity Check
        if guild_data.get("automod_toxicity_enabled", 0) == 1:
            threshold = guild_data.get("automod_threshold", 0.7)
            
            # Perform AI scan
            result = await am.analyze_content(message.content)
            score = result.get("score", 0.0)
            
            if score >= threshold or result.get("toxic", False):
                logger.info(f"AI Flagged Toxicity: {score} | Reason: {result.get('reason')} | User: {message.author}")
                
                # Take Action
                try:
                    await message.delete()
                    
                    # Notify Nexus
                    embed = am.create_argus_embed(
                        title="🚨 Neural Anomaly Terminated",
                        description=(
                            f"**Source:** {message.author.mention}\n"
                            f"**Sector:** {message.channel.mention}\n"
                            f"**AI Confidence:** `{score:.2%}`\n"
                            f"**Detection:** {result.get('reason', 'Toxic Content')}\n"
                            f"**Action:** Message Purged"
                        ),
                        color=am.COLORS["DANGER"],
                        footer="AI Auto-Moderation Protocol"
                    )
                    await am.log_to_nexus(message.guild, embed)
                    
                    # Warn User (briefly)
                    warn_msg = await message.channel.send(
                        f"⚠️ {message.author.mention}, your last transmission was flagged as toxic by my neural filters. Purged.",
                        delete_after=10
                    )
                except discord.Forbidden:
                    logger.warning(f"Failed to delete toxic message in {message.guild.id} - Missing Permissions")
                except Exception as e:
                    logger.error(f"Error in AutoMod logic: {e}")

async def setup(bot):
    await bot.add_cog(AutoModCog(bot))
