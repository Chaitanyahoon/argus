"""
Permissions Cog — server permission management.
"""

import discord
from discord.ext import commands
import logging
from typing import Optional
import core.embeds as E
from core.permissions import PermissionLevel

logger = logging.getLogger(__name__)

_LEVELS = "USER · MODERATOR · ADMIN · OWNER"


class PermissionsCog(commands.Cog, name="Permissions"):
    """Commands for managing server permissions and trust roles."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_pm(self):
        return getattr(self.bot, "permission_manager", None)

    @commands.command(name="perms", help="Manage server permissions.")
    @commands.has_permissions(administrator=True)
    async def perms_command(self, ctx: commands.Context, action: str = "show", *, args: str = ""):
        pm = self.get_pm()
        if not pm:
            await ctx.send(embed=E.error("Unavailable", "Permission system not initialized.", ctx))
            return

        action = action.lower()
        if action == "show":
            try:
                embed = await pm.get_permissions_embed(ctx.guild)
                await ctx.send(embed=embed)
            except Exception as e:
                logger.error("Error showing permissions: %s", e)
                await ctx.send(embed=E.error("Error", "Could not fetch permissions.", ctx))

        elif action == "setvoice":
            if not args:
                await ctx.send(embed=E.error("Missing Level", f"Usage: `!perms setvoice <LEVEL>`\nLevels: {_LEVELS}", ctx))
                return
            try:
                level = PermissionLevel[args.upper()]
                pm.set_command_level(ctx.guild.id, "voice", level)
                await ctx.send(embed=E.success("🔐 Voice Permissions Updated", f"Voice commands now require **{level.name}**.", ctx))
            except KeyError:
                await ctx.send(embed=E.error("Invalid Level", f"Choose from: {_LEVELS}", ctx))

        else:
            await ctx.send(embed=E.error("Unknown Action", "Valid actions: `show`, `setvoice`.", ctx))

    @commands.command(name="setroleperm", help="Set permission level for a role.")
    @commands.has_permissions(administrator=True)
    async def set_role_perm(self, ctx: commands.Context, role: discord.Role, level: str):
        pm = self.get_pm()
        if not pm:
            return
        try:
            perm_level = PermissionLevel[level.upper()]
            pm.set_role_permission(ctx.guild.id, role.id, perm_level)
            await ctx.send(embed=E.success("🔐 Role Permission Set", f"{role.mention} → **{perm_level.name}**", ctx))
        except KeyError:
            await ctx.send(embed=E.error("Invalid Level", f"Choose from: {_LEVELS}", ctx))

    @commands.command(name="trustuser", help="Add user to trusted list.")
    @commands.has_permissions(administrator=True)
    async def trust_user(self, ctx: commands.Context, user: discord.User):
        pm = self.get_pm()
        if not pm:
            return
        pm.add_trusted_user(ctx.guild.id, user.id)
        await ctx.send(embed=E.success("⭐ Trusted", f"{user.mention} is now a trusted user.", ctx))

    @commands.command(name="untrustuser", help="Remove user from trusted list.")
    @commands.has_permissions(administrator=True)
    async def untrust_user(self, ctx: commands.Context, user: discord.User):
        pm = self.get_pm()
        if not pm:
            return
        if pm.remove_trusted_user(ctx.guild.id, user.id):
            await ctx.send(embed=E.warning("⭐ Trust Removed", f"{user.mention} removed from trusted list.", ctx))
        else:
            await ctx.send(embed=E.error("Not Found", f"{user.mention} was not in the trusted list.", ctx))

    @commands.command(name="blacklist", help="Blacklist a user from commands.")
    @commands.has_permissions(administrator=True)
    async def blacklist_user(self, ctx: commands.Context, user: discord.User):
        pm = self.get_pm()
        if not pm:
            return
        pm.blacklist_user(ctx.guild.id, user.id)
        await ctx.send(embed=E.error("🚫 Blacklisted", f"{user.mention} is now blacklisted from bot commands.", ctx))

    @commands.command(name="mypermissions", aliases=["myperms"], help="Check your permission level.")
    async def my_permissions(self, ctx: commands.Context):
        pm = self.get_pm()
        if not pm:
            return
        user_level = pm.get_user_level(ctx.author)
        embed = E.gold("🔐 Your Permission Level", ctx=ctx)
        embed.add_field(name="Level",  value=f"`{user_level.name}`", inline=True)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(PermissionsCog(bot))
