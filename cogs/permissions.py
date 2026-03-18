"""
Permissions Cog — handles server permission management.
Modularized from the original monolithic bot.py.
"""

import discord
from discord.ext import commands
import logging
from typing import Optional
from core.permissions import PermissionLevel

logger = logging.getLogger(__name__)

class PermissionsCog(commands.Cog, name="Permissions"):
    """Commands for managing server permissions and trust roles."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_permission_manager(self):
        return getattr(self.bot, "permission_manager", None)

    @commands.command(name="perms", help="Manage server permissions.")
    @commands.has_permissions(administrator=True)
    async def perms_command(self, ctx: commands.Context, action: str = "show", *, args: str = ""):
        pm = self.get_permission_manager()
        if not pm:
            await ctx.send("❌ Permission system not initialized.")
            return
        
        action = action.lower()
        if action == "show":
            try:
                embed = await pm.get_permissions_embed(ctx.guild)
                await ctx.send(embed=embed)
            except Exception as e:
                logger.error(f"Error showing permissions: {e}")
                await ctx.send("❌ Error fetching permissions.")
        
        elif action == "setvoice":
            if not args:
                await ctx.send("❌ Usage: `.perms setvoice <LEVEL>`")
                return
            try:
                level = PermissionLevel[args.upper()]
                pm.set_command_level(ctx.guild.id, 'voice', level)
                await ctx.send(f"✅ Voice commands now require **{level.name}**")
            except KeyError:
                await ctx.send("❌ Invalid level. Use: USER, MODERATOR, ADMIN, OWNER")
        
        elif action == "setmusic":
            if not args:
                await ctx.send("❌ Usage: `.perms setmusic <LEVEL>`")
                return
            try:
                level = PermissionLevel[args.upper()]
                pm.set_command_level(ctx.guild.id, 'music', level)
                await ctx.send(f"✅ Music commands now require **{level.name}**")
            except KeyError:
                await ctx.send("❌ Invalid level. Use: USER, MODERATOR, ADMIN, OWNER")

    @commands.command(name="setroleperm", help="Set permission level for a role.")
    @commands.has_permissions(administrator=True)
    async def set_role_perm(self, ctx: commands.Context, role: discord.Role, level: str):
        pm = self.get_permission_manager()
        if not pm: return
        try:
            perm_level = PermissionLevel[level.upper()]
            pm.set_role_permission(ctx.guild.id, role.id, perm_level)
            await ctx.send(f"✅ {role.mention} → **{perm_level.name}**")
        except KeyError:
            await ctx.send("❌ Invalid level. Use: USER, MODERATOR, ADMIN, OWNER")

    @commands.command(name="trustuser", help="Add user to trusted list.")
    @commands.has_permissions(administrator=True)
    async def trust_user(self, ctx: commands.Context, user: discord.User):
        pm = self.get_permission_manager()
        if not pm: return
        pm.add_trusted_user(ctx.guild.id, user.id)
        await ctx.send(f"⭐ {user.mention} is now trusted.")

    @commands.command(name="untrustuser", help="Remove user from trusted list.")
    @commands.has_permissions(administrator=True)
    async def untrust_user(self, ctx: commands.Context, user: discord.User):
        pm = self.get_permission_manager()
        if not pm: return
        if pm.remove_trusted_user(ctx.guild.id, user.id):
            await ctx.send(f"✅ Removed {user.mention} from trusted list.")
        else:
            await ctx.send("❌ User was not trusted.")

    @commands.command(name="blacklist", help="Blacklist a user from commands.")
    @commands.has_permissions(administrator=True)
    async def blacklist_user(self, ctx: commands.Context, user: discord.User):
        pm = self.get_permission_manager()
        if not pm: return
        pm.blacklist_user(ctx.guild.id, user.id)
        await ctx.send(f"🚫 {user.mention} is now blacklisted.")

    @commands.command(name="mypermissions", aliases=["myperms"], help="Check your permission level.")
    async def my_permissions(self, ctx: commands.Context):
        pm = self.get_permission_manager()
        if not pm: return
        user_level = pm.get_user_level(ctx.author)
        embed = discord.Embed(title="🔐 Your Permissions", color=discord.Color.gold())
        embed.add_field(name="Level", value=f"`{user_level.name}`", inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PermissionsCog(bot))
