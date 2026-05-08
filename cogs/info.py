"""
Info Cog — Server and user information commands.
Provides statistics, server details, user profiles, and helpful information.
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
from datetime import datetime, timedelta
from typing import Optional
import core.embeds as E

logger = logging.getLogger(__name__)


class InfoCog(commands.Cog, name="Info"):
    """Commands for server and user information."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="serverinfo", aliases=["sinfo"], help="Show server information")
    async def server_info(self, ctx: commands.Context):
        """Display server information and statistics."""
        guild = ctx.guild
        if not guild:
            await ctx.send(embed=E.error("Error", "This command only works in servers.", ctx))
            return
        
        try:
            # Count members by status
            online = sum(1 for m in guild.members if m.status != discord.Status.offline)
            offline = len(guild.members) - online
            
            # Count channels
            text_channels = len(guild.text_channels)
            voice_channels = len(guild.voice_channels)
            categories = len(guild.categories)
            
            # Role statistics
            roles_count = len(guild.roles)
            
            # Boost info
            boost_level = guild.premium_tier
            boost_members = guild.premium_subscription_count
            
            embed = discord.Embed(
                title=f"📊 {guild.name}",
                description=guild.description or "No description",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            
            # Server details
            embed.add_field(name="📅 Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
            embed.add_field(name="👨‍💼 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
            embed.add_field(name="🆔 ID", value=f"`{guild.id}`", inline=True)
            
            # Members
            embed.add_field(
                name="👥 Members",
                value=f"**Total:** {len(guild.members)}\n**Online:** {online}\n**Offline:** {offline}",
                inline=True
            )
            
            # Channels
            embed.add_field(
                name="📢 Channels",
                value=f"**Text:** {text_channels}\n**Voice:** {voice_channels}\n**Categories:** {categories}",
                inline=True
            )
            
            # Roles and boosts
            embed.add_field(
                name="🏷️ Roles",
                value=f"**Total:** {roles_count}",
                inline=True
            )
            
            if boost_level > 0:
                embed.add_field(
                    name="⭐ Server Boosts",
                    value=f"**Level:** {boost_level}\n**Boosters:** {boost_members}",
                    inline=True
                )
            
            # Verification level
            verify_level = {
                discord.VerificationLevel.none: "None",
                discord.VerificationLevel.low: "Low",
                discord.VerificationLevel.medium: "Medium",
                discord.VerificationLevel.high: "High",
                discord.VerificationLevel.extreme: "Extreme"
            }
            embed.add_field(name="🔐 Verification", value=verify_level.get(guild.verification_level, "Unknown"), inline=True)
            
            embed.set_footer(text="Planthesia Bot • Server Helper")
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting server info: {e}")
            await ctx.send(embed=E.error("Error", f"Could not fetch server info: {str(e)}", ctx))

    @app_commands.command(name="serverinfo", description="Show server information")
    async def slash_server_info(self, interaction: discord.Interaction):
        """Slash command for server information."""
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message(embed=E.error("Error", "This command only works in servers.", None), ephemeral=True)
            return
        
        try:
            # Count members by status
            online = sum(1 for m in guild.members if m.status != discord.Status.offline)
            offline = len(guild.members) - online
            
            # Count channels
            text_channels = len(guild.text_channels)
            voice_channels = len(guild.voice_channels)
            categories = len(guild.categories)
            
            # Boost info
            boost_level = guild.premium_tier
            boost_members = guild.premium_subscription_count
            
            embed = discord.Embed(
                title=f"📊 {guild.name}",
                description=guild.description or "No description",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            
            embed.add_field(name="📅 Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
            embed.add_field(name="👨‍💼 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
            embed.add_field(name="🆔 ID", value=f"`{guild.id}`", inline=True)
            
            embed.add_field(
                name="👥 Members",
                value=f"**Total:** {len(guild.members)}\n**Online:** {online}\n**Offline:** {offline}",
                inline=True
            )
            
            embed.add_field(
                name="📢 Channels",
                value=f"**Text:** {text_channels}\n**Voice:** {voice_channels}\n**Categories:** {categories}",
                inline=True
            )
            
            if boost_level > 0:
                embed.add_field(
                    name="⭐ Server Boosts",
                    value=f"**Level:** {boost_level}\n**Boosters:** {boost_members}",
                    inline=True
                )
            
            embed.set_footer(text="Planthesia Bot • Server Helper")
            embed.timestamp = discord.utils.utcnow()
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting server info: {e}")
            await interaction.response.send_message(embed=E.error("Error", f"Could not fetch server info: {str(e)}", None), ephemeral=True)

    @commands.command(name="userinfo", aliases=["uinfo"], help="Show user information")
    async def user_info(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """Display user profile and information."""
        target = user or ctx.author
        
        try:
            embed = discord.Embed(
                title=f"👤 {target.name}",
                color=discord.Color.blurple()
            )
            
            embed.set_thumbnail(url=target.avatar.url if target.avatar else None)
            embed.add_field(name="🆔 User ID", value=f"`{target.id}`", inline=True)
            embed.add_field(name="📅 Created", value=f"<t:{int(target.created_at.timestamp())}:R>", inline=True)
            
            if isinstance(target, discord.Member):
                embed.add_field(name="⏰ Joined", value=f"<t:{int(target.joined_at.timestamp() if target.joined_at else 0)}:R>", inline=True)
                
                # Roles
                roles = [r.mention for r in target.roles if r != ctx.guild.default_role]
                if roles:
                    embed.add_field(
                        name="🏷️ Roles",
                        value=" ".join(roles[:10]) + ("..." if len(roles) > 10 else ""),
                        inline=False
                    )
                
                # Status and activity
                status_emoji = {
                    discord.Status.online: "🟢",
                    discord.Status.idle: "🟡",
                    discord.Status.do_not_disturb: "🔴",
                    discord.Status.offline: "⚫"
                }
                embed.add_field(
                    name="💬 Status",
                    value=status_emoji.get(target.status, "❓") + " " + str(target.status).capitalize(),
                    inline=True
                )
                
                # Permissions
                if ctx.author == target or ctx.author.guild_permissions.administrator:
                    key_perms = [p[0] for p in target.guild_permissions if p[1]][:5]
                    if key_perms:
                        embed.add_field(
                            name="🔐 Key Permissions",
                            value=", ".join(p.replace("_", " ").title() for p in key_perms),
                            inline=False
                        )
            
            embed.set_footer(text="Planthesia Bot • Server Helper")
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            await ctx.send(embed=E.error("Error", f"Could not fetch user info: {str(e)}", ctx))

    @app_commands.command(name="userinfo", description="Show user information")
    @app_commands.describe(user="The user to get info about (default: yourself)")
    async def slash_user_info(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        """Slash command for user information."""
        target = user or interaction.user
        
        try:
            embed = discord.Embed(
                title=f"👤 {target.name}",
                color=discord.Color.blurple()
            )
            
            embed.set_thumbnail(url=target.avatar.url if target.avatar else None)
            embed.add_field(name="🆔 User ID", value=f"`{target.id}`", inline=True)
            embed.add_field(name="📅 Created", value=f"<t:{int(target.created_at.timestamp())}:R>", inline=True)
            
            if isinstance(target, discord.Member):
                embed.add_field(name="⏰ Joined", value=f"<t:{int(target.joined_at.timestamp() if target.joined_at else 0)}:R>", inline=True)
                
                # Roles
                roles = [r.mention for r in target.roles if r != interaction.guild.default_role]
                if roles:
                    embed.add_field(
                        name="🏷️ Roles",
                        value=" ".join(roles[:10]) + ("..." if len(roles) > 10 else ""),
                        inline=False
                    )
                
                # Status
                status_emoji = {
                    discord.Status.online: "🟢",
                    discord.Status.idle: "🟡",
                    discord.Status.do_not_disturb: "🔴",
                    discord.Status.offline: "⚫"
                }
                embed.add_field(
                    name="💬 Status",
                    value=status_emoji.get(target.status, "❓") + " " + str(target.status).capitalize(),
                    inline=True
                )
            
            embed.set_footer(text="Planthesia Bot • Server Helper")
            embed.timestamp = discord.utils.utcnow()
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            await interaction.response.send_message(embed=E.error("Error", f"Could not fetch user info: {str(e)}", None), ephemeral=True)

    @commands.command(name="roleinfo", help="Show role information")
    async def role_info(self, ctx: commands.Context, role: discord.Role):
        """Display role information and statistics."""
        try:
            member_count = len(role.members)
            
            embed = discord.Embed(
                title=f"🏷️ {role.name}",
                color=role.color,
                description=f"Members: {member_count}"
            )
            
            embed.add_field(name="🆔 Role ID", value=f"`{role.id}`", inline=True)
            embed.add_field(name="📅 Created", value=f"<t:{int(role.created_at.timestamp())}:R>", inline=True)
            embed.add_field(name="🎨 Color", value=f"`{role.color}`", inline=True)
            embed.add_field(name="👥 Members", value=str(member_count), inline=True)
            embed.add_field(name="📍 Position", value=str(role.position), inline=True)
            embed.add_field(name="🔒 Managed", value="Yes" if role.managed else "No", inline=True)
            
            embed.set_footer(text="Planthesia Bot • Server Helper")
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting role info: {e}")
            await ctx.send(embed=E.error("Error", f"Could not fetch role info: {str(e)}", ctx))

    @commands.command(name="botinfo", help="Show bot information")
    async def botinfo_cmd(self, ctx: commands.Context):
        """Display Planthesia Bot information."""
        try:
            uptime = discord.utils.utcnow() - self.bot.start_time if hasattr(self.bot, 'start_time') else None
            
            embed = discord.Embed(
                title="🌿 Planthesia Bot",
                description="Your friendly server helper bot",
                color=discord.Color.green()
            )
            
            embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
            
            embed.add_field(name="🆔 Bot ID", value=f"`{self.bot.user.id}`", inline=True)
            embed.add_field(name="📡 Guilds", value=str(len(self.bot.guilds)), inline=True)
            embed.add_field(name="👥 Users", value=str(len(set(self.bot.get_all_members()))), inline=True)
            
            if uptime:
                hours, remainder = divmod(int(uptime.total_seconds()), 3600)
                minutes = remainder // 60
                embed.add_field(name="⏱️ Uptime", value=f"{hours}h {minutes}m", inline=True)
            
            embed.add_field(
                name="✨ Features",
                value="🎫 Ticket System\n🎤 Voice AI\n📋 Info Commands",
                inline=False
            )
            
            embed.set_footer(text="Planthesia Bot • Server Helper")
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            await ctx.send(embed=E.error("Error", f"Could not fetch bot info: {str(e)}", ctx))

    @app_commands.command(name="help", description="Show help information")
    async def slash_help(self, interaction: discord.Interaction):
        """Show available commands."""
        embed = discord.Embed(
            title="🌿 Planthesia Bot Help",
            description="Your friendly server helper",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="🎫 Tickets",
            value="/ticket — Create a support ticket\n/tickets — View all tickets (staff)",
            inline=False
        )
        
        embed.add_field(
            name="📋 Information",
            value="/serverinfo — Server statistics\n/userinfo [user] — User profile\nroleinfo [role] — Role details",
            inline=False
        )
        
        embed.add_field(
            name="🎵 Music",
            value="Music playback features are disabled in this deployment.",
            inline=False
        )
        
        embed.add_field(
            name="🎤 Voice",
            value="/join — Join voice channel\n/listen — Start voice AI\n/stop — Stop listening",
            inline=False
        )
        
        embed.set_footer(text="Use /help to see detailed command information")
        embed.timestamp = discord.utils.utcnow()
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command(name="help", help="Show help information")
    async def prefix_help(self, ctx: commands.Context):
        """Show available commands."""
        embed = discord.Embed(
            title="🌿 Planthesia Bot Help",
            description="Your friendly server helper",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="🎫 Tickets",
            value=">>ticket — Create a support ticket\n>>tickets — View all tickets (staff)\n>>setup-tickets — Setup ticket system",
            inline=False
        )
        
        embed.add_field(
            name="📋 Information",
            value=">>serverinfo — Server statistics\n>>userinfo [user] — User profile\n>>roleinfo [role] — Role details",
            inline=False
        )
        
        embed.add_field(
            name="🎵 Music",
            value="Music playback features are disabled in this deployment.",
            inline=False
        )
        
        embed.add_field(
            name="🎤 Voice",
            value=">>join — Join voice channel\n>>listen — Start voice AI\n>>leave — Leave voice",
            inline=False
        )
        
        embed.set_footer(text="Happy to help! 🌿")
        embed.timestamp = discord.utils.utcnow()
        
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    """Load the Info cog."""
    await bot.add_cog(InfoCog(bot))
    logger.info("Info cog loaded")
