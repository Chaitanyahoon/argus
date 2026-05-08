"""
Welcome Cog — Member onboarding and welcome system.
Greets new members, assigns roles, and provides server information.
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional
import core.embeds as E

logger = logging.getLogger(__name__)


class RoleButton(discord.ui.Button):
    """Button for assigning a role to a member."""
    def __init__(self, role: discord.Role, role_id: int):
        label = f"Get {role.name}" if len(role.name) <= 80 else f"Get Role {role_id}"
        super().__init__(
            style=discord.ButtonStyle.blurple,
            label=label,
            custom_id=f"assign_role_{role_id}"
        )
        self.role = role
        self.role_id = role_id
    
    async def callback(self, interaction: discord.Interaction):
        try:
            if isinstance(interaction.user, discord.Member):
                if self.role in interaction.user.roles:
                    await interaction.user.remove_roles(self.role)
                    await interaction.response.send_message(
                        f"✅ Removed role: **{self.role.name}**",
                        ephemeral=True
                    )
                else:
                    await interaction.user.add_roles(self.role)
                    await interaction.response.send_message(
                        f"✅ Assigned role: **{self.role.name}**",
                        ephemeral=True
                    )
            else:
                await interaction.response.send_message("Error: Could not assign role", ephemeral=True)
        except Exception as e:
            logger.error(f"Error assigning role: {e}")
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)


class WelcomeCog(commands.Cog, name="Welcome"):
    """Member welcome and onboarding system."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.welcome_channels: dict = {}  # guild_id -> channel_id
        self.role_channels: dict = {}  # guild_id -> channel_id
        self.welcome_enabled: dict = {}  # guild_id -> bool
        self.auto_role_id: dict = {}  # guild_id -> role_id

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Welcome new members to the server."""
        guild = member.guild
        if not guild:
            return
        
        # Check if welcome system is enabled for this guild
        if not self.welcome_enabled.get(guild.id, True):
            return
        
        try:
            # Get welcome channel
            welcome_channel_id = self.welcome_channels.get(guild.id)
            if not welcome_channel_id:
                # Try to find a general or welcome channel
                welcome_channel = discord.utils.get(
                    guild.text_channels,
                    name__in=["welcome", "general", "introductions"]
                ) or guild.text_channels[0] if guild.text_channels else None
            else:
                welcome_channel = guild.get_channel(welcome_channel_id)
            
            if not welcome_channel:
                logger.warning(f"No welcome channel found for {guild.name}")
                return
            
            # Create welcome embed
            embed = discord.Embed(
                title=f"👋 Welcome to {guild.name}!",
                description=f"Hey {member.mention}, glad to have you here!",
                color=discord.Color.green()
            )
            embed.add_field(
                name="📋 Server Rules",
                value="Please read the rules and code of conduct. Be respectful!",
                inline=False
            )
            embed.add_field(
                name="🎤 Get Roles",
                value="Check the role assignment channel to customize your experience.",
                inline=False
            )
            embed.add_field(
                name="❓ Need Help?",
                value="Use `/help` or `/ticket` to create a support ticket!",
                inline=False
            )
            embed.set_footer(text=f"Member #{len(guild.members)}")
            embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
            
            await welcome_channel.send(embed=embed)
            
            # Auto-assign role if configured
            auto_role_id = self.auto_role_id.get(guild.id)
            if auto_role_id:
                role = guild.get_role(auto_role_id)
                if role:
                    try:
                        await member.add_roles(role)
                        logger.info(f"Auto-assigned role '{role.name}' to {member}")
                    except Exception as e:
                        logger.error(f"Could not auto-assign role: {e}")
            
        except Exception as e:
            logger.error(f"Error welcoming member {member}: {e}")

    @commands.command(name="setup-welcome", help="Setup welcome system")
    @commands.has_permissions(administrator=True)
    async def setup_welcome(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Setup the welcome system for new members."""
        try:
            target_channel = channel or ctx.channel
            self.welcome_channels[ctx.guild.id] = target_channel.id
            self.welcome_enabled[ctx.guild.id] = True
            
            embed = discord.Embed(
                title="👋 Welcome to our Server!",
                description="We're excited to have you join our community. Read the information below to get started.",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📋 Server Guidelines",
                value="• Be respectful to all members\n• Follow the server rules\n• Have fun and enjoy!",
                inline=False
            )
            
            embed.add_field(
                name="🎯 Getting Started",
                value="1. Introduce yourself\n2. Assign yourself roles\n3. Check pinned messages\n4. Ask questions!",
                inline=False
            )
            
            embed.add_field(
                name="🆘 Support",
                value="Need help? Use `/help` or create a support ticket with `/ticket`",
                inline=False
            )
            
            embed.set_footer(text="Welcome! 🌿")
            embed.set_image(url="https://via.placeholder.com/900x300?text=Welcome+to+our+Server")
            
            await target_channel.send(embed=embed)
            await ctx.send(embed=E.success("✅ Welcome System Setup", f"Welcome messages will be sent when new members join {target_channel.mention}", ctx))
            logger.info(f"Welcome system setup in {ctx.guild.name}")
            
        except Exception as e:
            logger.error(f"Error setting up welcome: {e}")
            await ctx.send(embed=E.error("Error", f"Could not setup welcome: {str(e)}", ctx))

    @commands.command(name="setup-roles", help="Setup role assignment system")
    @commands.has_permissions(administrator=True)
    async def setup_roles(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Setup role self-assignment buttons."""
        try:
            target_channel = channel or ctx.channel
            self.role_channels[ctx.guild.id] = target_channel.id
            
            # Get assignable roles (roles below bot's highest role, excludable roles)
            assignable_roles = [
                r for r in ctx.guild.roles
                if r < ctx.guild.me.top_role and r != ctx.guild.default_role
                and not r.managed and not r.name.startswith("@")
            ][:5]  # Limit to 5 for button layout
            
            if not assignable_roles:
                await ctx.send(embed=E.error("No Roles", "No assignable roles found. Create some roles first.", ctx))
                return
            
            # Create embed
            embed = discord.Embed(
                title="🏷️ Role Assignment",
                description="Click the buttons below to assign yourself roles!",
                color=discord.Color.blurple()
            )
            
            for role in assignable_roles:
                embed.add_field(name=role.name, value=f"Click to assign/remove", inline=False)
            
            # Create view with buttons
            view = discord.ui.View(timeout=None)
            for role in assignable_roles:
                view.add_item(RoleButton(role, role.id))
            
            await target_channel.send(embed=embed, view=view)
            await ctx.send(embed=E.success("✅ Roles Setup", f"Role assignment system is ready in {target_channel.mention}", ctx))
            logger.info(f"Role assignment system setup in {ctx.guild.name}")
            
        except Exception as e:
            logger.error(f"Error setting up roles: {e}")
            await ctx.send(embed=E.error("Error", f"Could not setup roles: {str(e)}", ctx))

    @commands.command(name="set-auto-role", help="Set a role to automatically assign to new members")
    @commands.has_permissions(administrator=True)
    async def set_auto_role(self, ctx: commands.Context, role: discord.Role):
        """Set a role to be automatically assigned to new members."""
        try:
            # Check if bot can assign the role
            if role >= ctx.guild.me.top_role:
                await ctx.send(embed=E.error("Error", "Role is too high for bot to assign.", ctx))
                return
            
            self.auto_role_id[ctx.guild.id] = role.id
            await ctx.send(embed=E.success("✅ Auto-Role Set", f"New members will automatically get {role.mention}", ctx))
            logger.info(f"Auto-role set to {role.name} in {ctx.guild.name}")
            
        except Exception as e:
            logger.error(f"Error setting auto-role: {e}")
            await ctx.send(embed=E.error("Error", f"Could not set auto-role: {str(e)}", ctx))

    @commands.command(name="disable-welcome", help="Disable welcome messages")
    @commands.has_permissions(administrator=True)
    async def disable_welcome(self, ctx: commands.Context):
        """Disable welcome messages for new members."""
        self.welcome_enabled[ctx.guild.id] = False
        await ctx.send(embed=E.info("⚠️ Disabled", "Welcome messages are now disabled.", ctx))

    @commands.command(name="enable-welcome", help="Enable welcome messages")
    @commands.has_permissions(administrator=True)
    async def enable_welcome(self, ctx: commands.Context):
        """Enable welcome messages for new members."""
        self.welcome_enabled[ctx.guild.id] = True
        await ctx.send(embed=E.info("✅ Enabled", "Welcome messages are now enabled.", ctx))


async def setup(bot: commands.Bot):
    """Load the Welcome cog."""
    await bot.add_cog(WelcomeCog(bot))
    logger.info("Welcome cog loaded")
