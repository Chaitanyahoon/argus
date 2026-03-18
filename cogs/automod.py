"""
AutoMod Cog — AI-powered moderation and surveillance.
"""

import discord
from discord.ext import commands
import logging
import core.embeds as E

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
            embed = E.info(
                "🛡️ AutoMod Commands",
                "`!automod toggle toxicity` — toggle toxicity detection\n"
                "`!automod toggle spam`     — toggle spam detection\n"
                "`!automod threshold <0.1–1.0>` — set AI sensitivity\n"
                "`!automod status`          — show current settings",
                ctx,
            )
            await ctx.send(embed=embed)

    @automod.command(name="toggle", help="Toggle toxicity or spam detection.")
    async def toggle_mod(self, ctx: commands.Context, setting: str):
        am = self.get_argus_manager()
        if not am:
            return

        setting = setting.lower()
        if setting not in ["toxicity", "spam"]:
            await ctx.send(embed=E.error("Invalid Setting", "Use `toxicity` or `spam`.", ctx))
            return

        guild_data = am.db.get_guild(ctx.guild.id) or {}
        key        = f"automod_{setting}_enabled"
        new_val    = 0 if guild_data.get(key, 0) == 1 else 1
        am.db.update_guild(ctx.guild.id, **{key: new_val})

        if new_val:
            await ctx.send(embed=E.success(
                f"🛡️ {setting.title()} Detection Enabled",
                f"AI **{setting.upper()}** scanning is now **active**.",
                ctx,
            ))
        else:
            await ctx.send(embed=E.warning(
                f"🛡️ {setting.title()} Detection Disabled",
                f"AI **{setting.upper()}** scanning has been turned off.",
                ctx,
            ))

    @automod.command(name="threshold", help="Set AI sensitivity threshold (0.1 = strict, 1.0 = lenient).")
    async def set_threshold(self, ctx: commands.Context, value: float):
        am = self.get_argus_manager()
        if not am:
            return

        if not (0.1 <= value <= 1.0):
            await ctx.send(embed=E.error(
                "Invalid Threshold",
                "Value must be between `0.1` (very strict) and `1.0` (very lenient).",
                ctx,
            ))
            return

        am.db.update_guild(ctx.guild.id, automod_threshold=value)
        bar = "█" * round(value * 10) + "░" * (10 - round(value * 10))
        label = "Strict" if value < 0.4 else "Balanced" if value < 0.7 else "Lenient"
        await ctx.send(embed=E.info(
            "🎯 Sensitivity Updated",
            f"`{bar}` **{value}** ({label})",
            ctx,
        ))

    @automod.command(name="status", help="Show current AutoMod settings.")
    async def automod_status(self, ctx: commands.Context):
        am = self.get_argus_manager()
        if not am:
            return
        data      = am.db.get_guild(ctx.guild.id) or {}
        tox       = bool(data.get("automod_toxicity_enabled", 0))
        spam      = bool(data.get("automod_spam_enabled",     0))
        threshold = data.get("automod_threshold", 0.7)
        bar       = "█" * round(threshold * 10) + "░" * (10 - round(threshold * 10))

        embed = E.navy("🛡️ AutoMod Status", "", ctx)
        embed.add_field(name="Toxicity Detection", value="✅ On" if tox  else "❌ Off", inline=True)
        embed.add_field(name="Spam Detection",     value="✅ On" if spam else "❌ Off", inline=True)
        embed.add_field(name="AI Threshold",       value=f"`{bar}` {threshold}",        inline=False)
        await ctx.send(embed=embed)

    # ── Event listener ─────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or not message.content:
            return

        am = self.get_argus_manager()
        if not am:
            return

        guild_data = am.db.get_guild(message.guild.id) or {}

        if guild_data.get("automod_toxicity_enabled", 0) == 1:
            threshold = guild_data.get("automod_threshold", 0.7)
            result    = await am.analyze_content(message.content)
            score     = result.get("score", 0.0)

            if score >= threshold or result.get("toxic", False):
                logger.info(
                    "AutoMod flagged toxicity %.2f | %s | %s",
                    score, result.get("reason"), message.author,
                )
                try:
                    await message.delete()

                    # Post to Nexus log with branded embed
                    log_embed = E.automod_action(
                        action="delete",
                        user=message.author,
                        reason=result.get("reason", "Toxic content"),
                        confidence=score,
                    )
                    await am.log_to_nexus(message.guild, log_embed)

                    # Warn user (auto-deletes after 10s)
                    await message.channel.send(
                        f"⚠️ {message.author.mention}, your message was removed by AI moderation.",
                        delete_after=10,
                    )
                except discord.Forbidden:
                    logger.warning("AutoMod: missing permissions in guild %s", message.guild.id)
                except Exception as e:
                    logger.error("AutoMod error: %s", e)


async def setup(bot):
    await bot.add_cog(AutoModCog(bot))
