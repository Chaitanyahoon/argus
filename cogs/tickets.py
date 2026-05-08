"""
Tickets Cog — Support ticket system for server assistance.
Users can create tickets for help, bugs, suggestions, etc.
Staff can manage and resolve tickets.
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional
from datetime import datetime
import core.embeds as E

logger = logging.getLogger(__name__)


class TicketButton(discord.ui.Button):
    """Button to create a new support ticket."""
    def __init__(self, ticket_cog):
        super().__init__(style=discord.ButtonStyle.green, label="📩 Create Ticket", custom_id="create_ticket")
        self.ticket_cog = ticket_cog
    
    async def callback(self, interaction: discord.Interaction):
        await self.ticket_cog.create_ticket_modal(interaction)


class TicketModal(discord.ui.Modal, title="Create Support Ticket"):
    """Modal for creating a new ticket."""
    subject = discord.ui.TextInput(label="Subject", placeholder="What do you need help with?", max_length=100)
    description = discord.ui.TextInput(label="Description", placeholder="Describe your issue in detail...", style=discord.TextStyle.long, max_length=1000)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        # Callback will be set by the cog
        await self.on_submit_callback(interaction, self.subject.value, self.description.value)


class CloseTicketButton(discord.ui.Button):
    """Button to close a ticket."""
    def __init__(self, ticket_id):
        super().__init__(style=discord.ButtonStyle.red, label="❌ Close Ticket", custom_id=f"close_ticket_{ticket_id}")
        self.ticket_id = ticket_id
    
    async def callback(self, interaction: discord.Interaction):
        # Callback set by cog
        await self.close_callback(interaction, self.ticket_id)


class TicketView(discord.ui.View):
    """View containing ticket management buttons."""
    def __init__(self, ticket_id):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
        self.add_item(CloseTicketButton(ticket_id))


class TicketsCog(commands.Cog, name="Tickets"):
    """Support ticket system — create, manage, and resolve tickets."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tickets: dict = {}  # ticket_id -> {"creator": user_id, "channel": channel_id, "status": "open", "created_at": timestamp}
        self.next_ticket_id = 1

    def _am(self):
        """Get ArgusManager for database access."""
        return getattr(self.bot, "argus_manager", None)

    async def create_ticket_modal(self, interaction: discord.Interaction):
        """Show the ticket creation modal."""
        modal = TicketModal()
        modal.on_submit_callback = self.handle_ticket_creation
        await interaction.response.show_modal(modal)

    async def handle_ticket_creation(self, interaction: discord.Interaction, subject: str, description: str):
        """Handle a new ticket creation."""
        if not interaction.guild:
            await interaction.followup.send(embed=E.error("Error", "Tickets only work in servers.", None), ephemeral=True)
            return
        
        am = self._am()
        if not am:
            await interaction.followup.send(embed=E.error("Error", "Bot systems not ready.", None), ephemeral=True)
            return
        
        try:
            # Create ticket channel under a category
            category_name = "🎫 Tickets"
            category = discord.utils.get(interaction.guild.categories, name=category_name)
            
            if not category:
                # Create category if it doesn't exist
                category = await interaction.guild.create_category(category_name)
            
            ticket_id = self.next_ticket_id
            self.next_ticket_id += 1
            channel_name = f"ticket-{ticket_id}"
            
            # Create ticket channel
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            }
            # Give staff role access if it exists
            staff_role = discord.utils.get(interaction.guild.roles, name="Staff") or discord.utils.get(interaction.guild.roles, name="Moderator")
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)
            
            ticket_channel = await category.create_text_channel(channel_name, overwrites=overwrites)
            
            # Store ticket info
            self.tickets[ticket_id] = {
                "creator": interaction.user.id,
                "channel": ticket_channel.id,
                "status": "open",
                "created_at": datetime.utcnow().isoformat(),
                "subject": subject
            }
            
            # Send welcome message in ticket channel
            embed = discord.Embed(
                title=f"🎫 Ticket #{ticket_id}",
                description=f"**Subject:** {subject}\n\n{description}",
                color=discord.Color.blue()
            )
            embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.set_footer(text=f"Ticket opened by {interaction.user.name}")
            embed.timestamp = discord.utils.utcnow()
            
            view = TicketView(ticket_id)
            view.close_callback = self.handle_ticket_close
            await ticket_channel.send(embed=embed, view=view)
            
            # Reply to user
            await interaction.followup.send(
                embed=E.success("📩 Ticket Created", f"Your support ticket has been created! Visit {ticket_channel.mention}", None),
                ephemeral=True
            )
            
            logger.info(f"Ticket #{ticket_id} created by {interaction.user} in {interaction.guild}")
            
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            await interaction.followup.send(embed=E.error("Error", f"Could not create ticket: {str(e)}", None), ephemeral=True)

    async def handle_ticket_close(self, interaction: discord.Interaction, ticket_id: int):
        """Handle closing a ticket."""
        if not interaction.guild:
            await interaction.response.send_message(embed=E.error("Error", "Action unavailable.", None), ephemeral=True)
            return
        
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            await interaction.response.send_message(embed=E.error("Error", f"Ticket #{ticket_id} not found.", None), ephemeral=True)
            return
        
        # Check permissions
        if interaction.user.id != ticket["creator"] and not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                embed=E.error("Permission Denied", "Only ticket creator or staff can close this ticket.", None),
                ephemeral=True
            )
            return
        
        try:
            ticket["status"] = "closed"
            ticket_channel = interaction.guild.get_channel(ticket["channel"])
            
            if ticket_channel:
                # Mark channel as closed
                await ticket_channel.edit(name=f"closed-ticket-{ticket_id}")
                embed = discord.Embed(
                    title="🎫 Ticket Closed",
                    description=f"This ticket was closed by {interaction.user.mention}.",
                    color=discord.Color.red()
                )
                embed.timestamp = discord.utils.utcnow()
                await ticket_channel.send(embed=embed)
                
                # Optional: Delete after a delay (commented out, can be enabled)
                # await asyncio.sleep(300)  # 5 minutes
                # await ticket_channel.delete()
            
            await interaction.response.send_message(
                embed=E.success("✅ Closed", f"Ticket #{ticket_id} has been closed.", None),
                ephemeral=True
            )
            logger.info(f"Ticket #{ticket_id} closed by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error closing ticket: {e}")
            await interaction.response.send_message(embed=E.error("Error", f"Could not close ticket: {str(e)}", None), ephemeral=True)

    @app_commands.command(name="ticket", description="Create a support ticket")
    async def slash_ticket_create(self, interaction: discord.Interaction):
        """Slash command to create a new ticket."""
        await self.create_ticket_modal(interaction)

    @commands.command(name="ticket", help="Create a support ticket")
    async def prefix_ticket_create(self, ctx: commands.Context):
        """Prefix command to create a new ticket."""
        await self.create_ticket_modal(ctx.interaction or ctx)

    @commands.command(name="tickets", help="Show all tickets in this server")
    @commands.has_permissions(manage_messages=True)
    async def tickets_list(self, ctx: commands.Context):
        """List all tickets in the server."""
        if not self.tickets:
            await ctx.send(embed=E.info("Tickets", "No tickets have been created yet.", ctx))
            return
        
        ticket_list = []
        for tid, ticket in self.tickets.items():
            creator = self.bot.get_user(ticket["creator"])
            creator_name = creator.name if creator else f"User {ticket['creator']}"
            status = ticket["status"].upper()
            ticket_list.append(f"**#{tid}** — {ticket['subject'][:50]} ({status}) by {creator_name}")
        
        embed = E.info(
            "🎫 All Tickets",
            "\n".join(ticket_list),
            ctx
        )
        await ctx.send(embed=embed)

    @app_commands.command(name="tickets", description="List all tickets (staff only)")
    @app_commands.default_permissions(manage_messages=True)
    async def slash_tickets_list(self, interaction: discord.Interaction):
        """Slash command to list all tickets."""
        if not self.tickets:
            await interaction.response.send_message(embed=E.info("Tickets", "No tickets have been created yet.", None), ephemeral=True)
            return
        
        ticket_list = []
        for tid, ticket in self.tickets.items():
            creator = self.bot.get_user(ticket["creator"])
            creator_name = creator.name if creator else f"User {ticket['creator']}"
            status = ticket["status"].upper()
            ticket_list.append(f"**#{tid}** — {ticket['subject'][:50]} ({status}) by {creator_name}")
        
        embed = E.info(
            "🎫 All Tickets",
            "\n".join(ticket_list),
            None
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command(name="setup-tickets", help="Setup the ticket system with a welcome message")
    @commands.has_permissions(administrator=True)
    async def setup_tickets(self, ctx: commands.Context):
        """Setup ticket system with welcome message in the current channel."""
        try:
            embed = discord.Embed(
                title="🎫 Support Tickets",
                description="Need help? Create a support ticket to get assistance from our team.",
                color=discord.Color.blue()
            )
            embed.add_field(name="How it works:", value="1. Click the button below\n2. Describe your issue\n3. Wait for staff to respond", inline=False)
            embed.set_footer(text="Planthesia Bot • Server Helper")
            
            view = discord.ui.View(timeout=None)
            button = TicketButton(self)
            view.add_item(button)
            
            await ctx.send(embed=embed, view=view)
            await ctx.send(embed=E.success("✅ Setup Complete", "Ticket system is ready! Users can now create tickets.", ctx))
            logger.info(f"Ticket system setup completed in {ctx.guild.name}")
            
        except Exception as e:
            logger.error(f"Error setting up tickets: {e}")
            await ctx.send(embed=E.error("Error", f"Could not setup tickets: {str(e)}", ctx))


async def setup(bot: commands.Bot):
    """Load the Tickets cog."""
    await bot.add_cog(TicketsCog(bot))
    logger.info("Tickets cog loaded")
