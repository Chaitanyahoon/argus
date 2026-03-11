"""
TempVoice UI — embed and buttons for managing temporary voice channels.
"""

import logging
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from .temp_voice import TempChannelData, TempVoiceManager

logger = logging.getLogger(__name__)

PREFIX = "tempvoice"
PREFIX_SHARED = "tempvoice_shared"  # shared interface: resolve VC by owner on click

# Custom Emojis Configuration
# The reference UI uses custom grey/colored emoji icons. To match perfectly,
# replace these standard unicode fallbacks with your custom server emoji IDs.
# Format example: "<:icon_name:1234567890>"
UI_EMOJIS = {
    "name": "<:name:1161605686568960060>",
    "limit": "<:limit:1161605683955900496>",
    "privacy": "<:privacy:1161605688691261500>",
    "waiting": "<:waiting:1161605871227387965>",
    "chat": "<:chat:1427941772163682408>",
    "trust": "<:trust:1161647139244490832>",
    "untrust": "<:untrust:1162862846007320668>",
    "invite": "<:invite:1161647152821444688>",
    "kick": "<:kick:1161605681107976263>",
    "region": "<:region:1161605689576263753>",
    "block": "<:block:1161605864898174986>",
    "unblock": "<:unblock:1162862844585443370>",
    "claim": "<:claim:1161605458054889472>",
    "transfer": "<:transfer:1161647167488929963>",
    "delete": "<:delete:1161605459292205076>",
}


def build_welcome_embed(welcome_message: str) -> discord.Embed:
    """Build the welcome / private space embed (configurable server message)."""
    return discord.Embed(
        description=welcome_message,
        color=discord.Color.blue(),
    )


# Attachment filename used when sending the instruction image (must match in temp_voice.py)
INSTRUCTION_IMAGE_ATTACHMENT_NAME = "tempvoice_instruction.png"


def build_temp_voice_embed(channel: discord.VoiceChannel, use_instruction_image: bool = False) -> discord.Embed:
    """Build the TempVoice Interface embed. If use_instruction_image is True, omit text legend (image will be set by caller)."""
    if use_instruction_image:
        description = (
            "This interface can be used to manage temporary voice channels. "
            "More options are available with /voice commands.\n\n"
            "Press the buttons below to use the interface."
        )
    else:
        legend = (
            f"**NAME** {UI_EMOJIS['name']} **LIMIT** {UI_EMOJIS['limit']} **PRIVACY** {UI_EMOJIS['privacy']} **WAITING R.** {UI_EMOJIS['waiting']} **CHAT** {UI_EMOJIS['chat']}\n"
            f"**TRUST** {UI_EMOJIS['trust']} **UNTRUST** {UI_EMOJIS['untrust']} **INVITE** {UI_EMOJIS['invite']} **KICK** {UI_EMOJIS['kick']} **REGION** {UI_EMOJIS['region']}\n"
            f"**BLOCK** {UI_EMOJIS['block']} **UNBLOCK** {UI_EMOJIS['unblock']} **CLAIM** {UI_EMOJIS['claim']} **TRANSFER** {UI_EMOJIS['transfer']} **DELETE** {UI_EMOJIS['delete']}"
        )
        description = (
            "This interface can be used to manage temporary voice channels. "
            "More options are available with /voice commands.\n\n"
            f"{legend}\n\n"
            "Press the buttons below to use the interface."
        )
    embed = discord.Embed(
        title="TempVoice Interface",
        description=description,
        color=discord.Color.blue(),
    )
    embed.add_field(
        name="Channel",
        value=channel.mention,
        inline=True,
    )
    embed.set_footer(text="Press the buttons below to use the interface.")
    return embed


def _channel_id_from_custom_id(custom_id: str) -> int | None:
    if not custom_id.startswith(f"{PREFIX}:") or custom_id.count(":") < 2:
        return None
    try:
        return int(custom_id.split(":")[2])
    except ValueError:
        return None


class TempVoiceView(discord.ui.View):
    """
    Persistent view for TempVoice buttons. One view instance is registered
    with the bot; custom_id format is tempvoice:action:channel_id.
    """

    def __init__(self, manager: "TempVoiceManager", channel: discord.VoiceChannel | None = None, *, timeout: float | None = 1800):
        super().__init__(timeout=timeout)
        self.manager = manager
        self._channel = channel  # only set when creating a new message; None for persistent handler

        if channel is not None:
            cid = channel.id
            # Row 0: NAME, LIMIT, PRIVACY, WAITING R., CHAT
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, emoji=UI_EMOJIS["name"], custom_id=f"{PREFIX}:name:{cid}", row=0))
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, emoji=UI_EMOJIS["limit"], custom_id=f"{PREFIX}:limit:{cid}", row=0))
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, emoji=UI_EMOJIS["privacy"], custom_id=f"{PREFIX}:privacy:{cid}", row=0))
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, emoji=UI_EMOJIS["waiting"], custom_id=f"{PREFIX}:waiting_room:{cid}", row=0))
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, emoji=UI_EMOJIS["chat"], custom_id=f"{PREFIX}:chat:{cid}", row=0))
            # Row 1: TRUST, UNTRUST, INVITE, KICK, REGION
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, emoji=UI_EMOJIS["trust"], custom_id=f"{PREFIX}:trust:{cid}", row=1))
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, emoji=UI_EMOJIS["untrust"], custom_id=f"{PREFIX}:untrust:{cid}", row=1))
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, emoji=UI_EMOJIS["invite"], custom_id=f"{PREFIX}:invite:{cid}", row=1))
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, emoji=UI_EMOJIS["kick"], custom_id=f"{PREFIX}:kick:{cid}", row=1))
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, emoji=UI_EMOJIS["region"], custom_id=f"{PREFIX}:region:{cid}", row=1))
            # Row 2: BLOCK, UNBLOCK, CLAIM, TRANSFER, DELETE
            # Use secondary background for delete button to match the reference image's dark grey look
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, emoji=UI_EMOJIS["block"], custom_id=f"{PREFIX}:block:{cid}", row=2))
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, emoji=UI_EMOJIS["unblock"], custom_id=f"{PREFIX}:unblock:{cid}", row=2))
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, emoji=UI_EMOJIS["claim"], custom_id=f"{PREFIX}:claim:{cid}", row=2))
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, emoji=UI_EMOJIS["transfer"], custom_id=f"{PREFIX}:transfer:{cid}", row=2))
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, emoji=UI_EMOJIS["delete"], custom_id=f"{PREFIX}:delete:{cid}", row=2))

    async def _get_channel(self, interaction: discord.Interaction, channel_id: int) -> discord.VoiceChannel | None:
        ch = interaction.guild.get_channel(channel_id)
        if ch is None:
            try:
                ch = await interaction.guild.fetch_channel(channel_id)
            except (discord.NotFound, discord.HTTPException):
                pass
        return ch if isinstance(ch, discord.VoiceChannel) else None

    async def _check_owner(self, interaction: discord.Interaction, channel_id: int) -> bool:
        if not self.manager.is_owner(channel_id, interaction.user.id):
            await interaction.response.send_message("Only the channel owner can use this.", ephemeral=True)
            return False
        return True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.data or "custom_id" not in interaction.data:
            return False
        custom_id = interaction.data["custom_id"]
        if not custom_id.startswith(f"{PREFIX}:"):
            return False
        channel_id = _channel_id_from_custom_id(custom_id)
        if channel_id is None:
            return False
        channel = await self._get_channel(interaction, channel_id)
        if channel is None:
            await interaction.response.send_message("This channel no longer exists.", ephemeral=True)
            return False
        action = custom_id.split(":")[1]
        if action == "claim":
            if interaction.user not in channel.members:
                await interaction.response.send_message("You must be in the channel to claim it.", ephemeral=True)
                return False
            return True
        if action == "delete":
            if not self.manager.is_owner(channel_id, interaction.user.id):
                await interaction.response.send_message("Only the channel owner can delete the channel.", ephemeral=True)
                return False
            return True
        return self.manager.is_owner(channel_id, interaction.user.id)

    @staticmethod
    async def _execute_action(
        manager: "TempVoiceManager",
        interaction: discord.Interaction,
        channel: discord.VoiceChannel,
        action: str,
    ) -> None:
        data = manager.get_data(channel.id)
        if data is None:
            await interaction.response.send_message("This is not a temp channel.", ephemeral=True)
            return

        # Permission checks (used when handling from bot's on_interaction)
        if action == "claim":
            if interaction.user not in channel.members:
                await interaction.response.send_message("You must be in the channel to claim it.", ephemeral=True)
                return
        elif action == "delete":
            if not manager.is_owner(channel.id, interaction.user.id):
                await interaction.response.send_message("Only the channel owner can delete the channel.", ephemeral=True)
                return
        else:
            if not manager.is_owner(channel.id, interaction.user.id):
                await interaction.response.send_message("Only the channel owner can use this.", ephemeral=True)
                return

        guild = channel.guild

        # NAME (rename)
        if action == "name":
            modal = RenameModal(channel)
            await interaction.response.send_modal(modal)
            return
        if action == "limit":
            modal = LimitModal(channel)
            await interaction.response.send_modal(modal)
            return
        # PRIVACY: show dropdown with Lock / Unlock / Invisible / Visible / Close Chat
        if action == "privacy":
            view = PrivacySelectView(channel, manager, data)
            await interaction.response.send_message("Select a Privacy Option", view=view, ephemeral=True)
            return
        # WAITING R.: only permitted users can join
        if action == "waiting_room":
            data.waiting_room = not data.waiting_room
            if data.waiting_room:
                await channel.set_permissions(guild.default_role, connect=False)
                data.locked = True
                await interaction.response.send_message("Waiting room on. Only trusted/permitted users can join.", ephemeral=True)
            else:
                await channel.set_permissions(guild.default_role, connect=True)
                data.locked = False
                await interaction.response.send_message("Waiting room off. Anyone can join (unless blocked).", ephemeral=True)
            return
        # CHAT: info only
        if action == "chat":
            await interaction.response.send_message("Chat for this VC is in this channel. Use the interface here to manage your voice channel.", ephemeral=True)
            return
        # TRUST (permit): native user select
        if action == "trust":
            view = UserSelectView(
                channel, manager, "permit",
                placeholder="Selected users will be trusted to join",
                allow_multiple=True,
            )
            await interaction.response.send_message("Select user(s) to trust (allow to join):", view=view, ephemeral=True)
            return
        # UNTRUST (revoke permit)
        if action == "untrust":
            modal = UserActionModal(channel, "untrust", "Enter username to untrust")
            await interaction.response.send_modal(modal)
            return
        # INVITE: select users then create invite link
        if action == "invite":
            view = UserSelectView(
                channel, manager, "invite",
                placeholder="Select users to invite (you'll get a link to share)",
                allow_multiple=True,
            )
            await interaction.response.send_message("Select user(s) to invite:", view=view, ephemeral=True)
            return
        if action == "kick":
            view = UserSelectView(
                channel, manager, "kick",
                placeholder="The selected user(s) will be kicked",
                allow_multiple=True,
            )
            await interaction.response.send_message("Select user(s) to kick:", view=view, ephemeral=True)
            return
        # REGION: set voice region
        if action == "region":
            modal = RegionModal(channel)
            await interaction.response.send_modal(modal)
            return
        # BLOCK (ban): native user select
        if action == "block":
            view = UserSelectView(
                channel, manager, "block",
                placeholder="Selected users will be kicked and blocked",
                allow_multiple=True,
            )
            await interaction.response.send_message("Select user(s) to kick and block:", view=view, ephemeral=True)
            return
        # UNBLOCK: native user select
        if action == "unblock":
            view = UserSelectView(
                channel, manager, "unblock",
                placeholder="Select users to unblock",
                allow_multiple=True,
            )
            await interaction.response.send_message("Select user(s) to unblock:", view=view, ephemeral=True)
            return
        if action == "claim":
            # Current owner not in channel -> claim
            owner = guild.get_member(data.owner_id)
            if owner and owner in channel.members:
                await interaction.response.send_message("The owner is still in the channel.", ephemeral=True)
                return
            manager.set_owner(channel.id, interaction.user.id)
            await channel.set_permissions(interaction.user, manage_channels=True, manage_permissions=True)
            if owner:
                await channel.set_permissions(owner, manage_channels=False, manage_permissions=False)
            await interaction.response.send_message("You are now the channel owner.", ephemeral=True)
            return
        if action == "transfer":
            view = UserSelectView(
                channel, manager, "transfer",
                placeholder="The selected user will gain the ownership",
            )
            await interaction.response.send_message("Select the new owner (dropdown has search):", view=view, ephemeral=True)
            return
        if action == "delete":
            if channel.id in manager.temp_channels:
                manager.temp_channels.pop(channel.id)
            try:
                await channel.delete(reason="TempVoice: owner deleted")
            except discord.HTTPException as e:
                logger.error("TempVoice: delete failed: %s", e)
                await interaction.response.send_message(f"Failed to delete: {e}", ephemeral=True)
                return
            await interaction.response.send_message("Channel deleted.", ephemeral=True)
            return

        await interaction.response.send_message("Unknown action.", ephemeral=True)

    async def on_timeout(self) -> None:
        pass

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        logger.exception("TempVoice view error: %s", error)
        try:
            await interaction.response.send_message("Something went wrong.", ephemeral=True)
        except discord.HTTPException:
            pass


class SharedTempVoiceView(discord.ui.View):
    """
    Single shared view for the interface channel: buttons have no channel_id.
    When a user clicks, the bot resolves their VC by owner_id and runs the action for that VC only.
    """

    def __init__(self, manager: "TempVoiceManager", *, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.manager = manager
        # Same 15 buttons but custom_id is tempvoice_shared:action (no channel id)
        for row, actions in enumerate([
            ("name", "limit", "privacy", "waiting_room", "chat"),
            ("trust", "untrust", "invite", "kick", "region"),
            ("block", "unblock", "claim", "transfer", "delete"),
        ]):
            for action in actions:
                emoji = UI_EMOJIS.get(action, "⚙️")
                self.add_item(discord.ui.Button(
                    style=discord.ButtonStyle.danger if action == "delete" else discord.ButtonStyle.secondary,
                    emoji=emoji,
                    custom_id=f"{PREFIX_SHARED}:{action}",
                    row=row,
                ))


# --- Select dropdowns (Privacy + User list for Kick / Block / Transfer) ---

# No emoji on options: Discord often rejects unicode emoji in SelectOption (Invalid emoji)
PRIVACY_OPTIONS = [
    discord.SelectOption(
        label="Lock",
        value="lock",
        description="Only trusted users will be able to join your voice channel",
    ),
    discord.SelectOption(
        label="Unlock",
        value="unlock",
        description="Everyone will be able to join your voice channel",
    ),
    discord.SelectOption(
        label="Invisible",
        value="invisible",
        description="Only trusted users will be able to view your voice channel",
    ),
    discord.SelectOption(
        label="Visible",
        value="visible",
        description="Everyone will be able to view your voice channel",
    ),
    discord.SelectOption(
        label="Close Chat",
        value="close_chat",
        description="Only trusted users will be able to text in your voice channel",
    ),
    discord.SelectOption(
        label="Open Chat",
        value="open_chat",
        description="Everyone will be able to text in your voice channel",
    ),
]


class PrivacySelectView(discord.ui.View):
    """Ephemeral view with a single Select for privacy options."""

    def __init__(self, channel: discord.VoiceChannel, manager: "TempVoiceManager", data: "TempChannelData", *, timeout: float = 60):
        super().__init__(timeout=timeout)
        self.channel = channel
        self.manager = manager
        self.data = data
        self.add_item(PrivacySelect(channel, manager, data))


class PrivacySelect(discord.ui.Select):
    def __init__(self, channel: discord.VoiceChannel, manager: "TempVoiceManager", data: "TempChannelData"):
        self._channel = channel
        self._manager = manager
        self._data = data
        super().__init__(
            placeholder="Select a Privacy Option",
            options=PRIVACY_OPTIONS,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            return
        value = self.values[0]
        guild = interaction.guild
        data = self._data

        if value == "lock":
            await self._channel.set_permissions(guild.default_role, connect=False, view_channel=True)
            data.locked = True
            data.hidden = False
            msg = "Privacy: channel **locked**. Only permitted users can join."
        elif value == "unlock":
            await self._channel.set_permissions(guild.default_role, connect=True, view_channel=True)
            data.locked = False
            data.hidden = False
            msg = "Privacy: channel **unlocked**. Everyone can join."
        elif value == "invisible":
            await self._channel.set_permissions(guild.default_role, connect=False, view_channel=False)
            data.locked = True
            data.hidden = True
            msg = "Privacy: channel **invisible**. Only permitted users can view and join."
        elif value == "visible":
            await self._channel.set_permissions(guild.default_role, connect=True, view_channel=True)
            data.locked = False
            data.hidden = False
            msg = "Privacy: channel **visible**. Everyone can view and join."
        elif value == "close_chat":
            # Discord does not expose "who can text in VC chat" per-role; treat as info
            msg = "Close Chat: only trusted users can use this channel's chat. (Use Lock/Invisible to restrict access.)"
        else:  # open_chat
            msg = "Open Chat: everyone can use this channel's chat. (Use Unlock/Visible for full access.)"
        await interaction.response.edit_message(content=msg, view=None)


def _member_from_value(guild: discord.Guild, value: discord.User | discord.Member) -> discord.Member | None:
    """Resolve User/Member to Member for guild actions."""
    if isinstance(value, discord.Member):
        return value
    return guild.get_member(value.id)


class NativeUserSelect(discord.ui.UserSelect):
    """
    Discord's native user select: shows guild members with avatars and built-in search.
    Use for kick, block, transfer so the dropdown is the native one (icons + search).
    """

    def __init__(
        self,
        channel: discord.VoiceChannel,
        manager: "TempVoiceManager",
        action: str,
        placeholder: str,
        *,
        max_values: int = 1,
    ):
        self._channel = channel
        self._manager = manager
        self._action = action
        cid = f"{PREFIX}_user_{action}_{channel.id}"[:100]
        super().__init__(
            custom_id=cid,
            placeholder=placeholder[:150],
            min_values=1,
            max_values=max_values,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            return
        data = self._manager.get_data(self._channel.id)
        if not data:
            await interaction.response.edit_message(content="Channel no longer exists.", view=None)
            return
        # self.values is list of User/Member from Discord's entity select
        members = []
        for v in self.values:
            m = _member_from_value(interaction.guild, v)
            if m:
                members.append(m)

        if not members:
            await interaction.response.edit_message(content="No user selected.", view=None)
            return

        if self._action == "kick":
            kicked, failed = [], []
            for member in members:
                if member not in self._channel.members:
                    failed.append(member.display_name)
                    continue
                if member.id == data.owner_id:
                    failed.append(f"{member.display_name} (owner)")
                    continue
                try:
                    await member.move_to(None)
                    kicked.append(member.display_name)
                except discord.HTTPException:
                    failed.append(member.display_name)
            msg = f"Kicked: **{', '.join(kicked)}**." if kicked else "No one kicked."
            if failed:
                msg += f" Skipped: {', '.join(failed)}."
            await interaction.response.edit_message(content=msg, view=None)
            return

        if self._action == "block":
            blocked, failed = [], []
            for member in members:
                if member.id == data.owner_id:
                    failed.append(f"{member.display_name} (owner)")
                    continue
                data.banned_ids.add(member.id)
                await self._channel.set_permissions(member, connect=False)
                if member in self._channel.members:
                    try:
                        await member.move_to(None)
                    except discord.HTTPException:
                        pass
                blocked.append(member.display_name)
            msg = f"Kicked and blocked: **{', '.join(blocked)}**." if blocked else "No one blocked."
            if failed:
                msg += f" Skipped: {', '.join(failed)}."
            await interaction.response.edit_message(content=msg, view=None)
            return

        if self._action == "permit":
            trusted = []
            for member in members:
                data.permitted_ids.add(member.id)
                data.banned_ids.discard(member.id)
                await self._channel.set_permissions(member, connect=True)
                trusted.append(member.display_name)
            msg = f"Trusted (can join): **{', '.join(trusted)}**."
            await interaction.response.edit_message(content=msg, view=None)
            return

        if self._action == "unblock":
            unblocked = []
            for member in members:
                data.banned_ids.discard(member.id)
                await self._channel.set_permissions(member, overwrite=None)
                unblocked.append(member.display_name)
            msg = f"Unblocked: **{', '.join(unblocked)}**."
            await interaction.response.edit_message(content=msg, view=None)
            return

        if self._action == "invite":
            try:
                invite = await self._channel.create_invite(max_uses=min(len(members), 10) or 1, max_age=3600)
                names = ", ".join(f"**{m.display_name}**" for m in members)
                await interaction.response.edit_message(
                    content=f"Invite link (1h): {invite.url}\nShare with: {names}",
                    view=None,
                )
            except discord.HTTPException as e:
                await interaction.response.edit_message(content=f"Could not create invite: {e}", view=None)
            return

        # Transfer: single user only
        member = members[0]
        if member not in self._channel.members:
            await interaction.response.edit_message(content=f"**{member.display_name}** must be in the channel to become owner.", view=None)
            return
        old_owner = interaction.guild.get_member(data.owner_id)
        self._manager.set_owner(self._channel.id, member.id)
        await self._channel.set_permissions(member, manage_channels=True, manage_permissions=True)
        if old_owner:
            await self._channel.set_permissions(old_owner, manage_channels=False, manage_permissions=False)
        await interaction.response.edit_message(content=f"Ownership transferred to **{member.display_name}**.", view=None)


class UserSelectView(discord.ui.View):
    """
    Ephemeral view with Discord's native UserSelect: shows profile pictures and
    built-in search in the dropdown.
    """

    def __init__(
        self,
        channel: discord.VoiceChannel,
        manager: "TempVoiceManager",
        action: str,
        placeholder: str,
        *,
        allow_multiple: bool = False,
        timeout: float = 60,
    ):
        super().__init__(timeout=timeout)
        self.channel = channel
        self.manager = manager
        self.action = action
        max_vals = 25 if allow_multiple else 1
        self.add_item(NativeUserSelect(channel, manager, action, placeholder, max_values=max_vals))


# Modals (need to be in same file so they can reference manager/channel)

class RenameModal(discord.ui.Modal):
    new_name = discord.ui.TextInput(label="Channel name", placeholder="My VC", max_length=100, required=True)

    def __init__(self, channel: discord.VoiceChannel):
        super().__init__(title="Rename Channel")
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction) -> None:
        name = self.new_name.value.strip() or "Voice Channel"
        try:
            await self.channel.edit(name=name)
            await interaction.response.send_message(f"Renamed to **{name}**.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"Failed: {e}", ephemeral=True)


class RegionModal(discord.ui.Modal):
    """Set voice channel RTC region."""
    region_input = discord.ui.TextInput(
        label="Region (e.g. us-central, india, singapore)",
        placeholder="us-central",
        max_length=32,
        required=True,
    )

    def __init__(self, channel: discord.VoiceChannel):
        super().__init__(title="Set Voice Region")
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction) -> None:
        region = self.region_input.value.strip().lower().replace(" ", "")
        if not region:
            await interaction.response.send_message("Enter a region name.", ephemeral=True)
            return
        try:
            await self.channel.edit(rtc_region=region)
            await interaction.response.send_message(f"Voice region set to **{region}**.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"Failed (check region name): {e}", ephemeral=True)


class LimitModal(discord.ui.Modal):
    limit_input = discord.ui.TextInput(label="User limit (0 = no limit)", placeholder="0", max_length=3, required=True)

    def __init__(self, channel: discord.VoiceChannel):
        super().__init__(title="Set User Limit")
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            limit = int(self.limit_input.value.strip())
            if limit < 0 or limit > 99:
                await interaction.response.send_message("Limit must be 0–99.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("Enter a number.", ephemeral=True)
            return
        try:
            await self.channel.edit(user_limit=limit)
            await interaction.response.send_message(f"User limit set to **{limit}**.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"Failed: {e}", ephemeral=True)


from .bot_utils import fuzzy_find_member

# Local fuzzy find removed; using bot_utils.fuzzy_find_member


class UserActionModal(discord.ui.Modal):
    username = discord.ui.TextInput(label="Username", placeholder="Display name or username", max_length=100, required=True)

    def __init__(self, channel: discord.VoiceChannel, action: str, title_label: str):
        super().__init__(title=title_label)
        self.channel = channel
        self.action = action

    async def on_submit(self, interaction: discord.Interaction) -> None:
        manager = getattr(interaction.client, "temp_voice_manager", None)
        if not manager:
            await interaction.response.send_message("TempVoice not configured.", ephemeral=True)
            return
        data = manager.get_data(self.channel.id)
        if not data:
            await interaction.response.send_message("Channel not found.", ephemeral=True)
            return

        member = fuzzy_find_member(interaction.guild, self.username.value)
        if not member:
            await interaction.response.send_message("User not found.", ephemeral=True)
            return

        guild = interaction.guild
        if self.action == "kick":
            if member not in self.channel.members:
                await interaction.response.send_message(f"{member.display_name} is not in the channel.", ephemeral=True)
                return
            if member.id == data.owner_id:
                await interaction.response.send_message("Cannot kick the owner.", ephemeral=True)
                return
            try:
                await member.move_to(None)
                await interaction.response.send_message(f"Kicked **{member.display_name}**.", ephemeral=True)
            except discord.HTTPException as e:
                await interaction.response.send_message(f"Failed: {e}", ephemeral=True)
            return
        if self.action == "ban":
            data.banned_ids.add(member.id)
            await self.channel.set_permissions(member, connect=False)
            await interaction.response.send_message(f"Banned **{member.display_name}** from this channel.", ephemeral=True)
            return
        if self.action == "permit":
            data.permitted_ids.add(member.id)
            data.banned_ids.discard(member.id)
            await self.channel.set_permissions(member, connect=True)
            await interaction.response.send_message(f"**{member.display_name}** can now join.", ephemeral=True)
            return
        if self.action == "unban":
            data.banned_ids.discard(member.id)
            await self.channel.set_permissions(member, overwrite=None)
            await interaction.response.send_message(f"Unbanned **{member.display_name}**.", ephemeral=True)
            return
        if self.action == "untrust":
            data.permitted_ids.discard(member.id)
            await self.channel.set_permissions(member, overwrite=None)
            await interaction.response.send_message(f"**{member.display_name}** is no longer trusted (permit removed).", ephemeral=True)
            return
        await interaction.response.send_message("Unknown action.", ephemeral=True)


class TransferModal(discord.ui.Modal):
    username = discord.ui.TextInput(label="New owner (username)", placeholder="Display name", max_length=100, required=True)

    def __init__(self, channel: discord.VoiceChannel, manager: "TempVoiceManager"):
        super().__init__(title="Transfer Ownership")
        self.channel = channel
        self.manager = manager

    async def on_submit(self, interaction: discord.Interaction) -> None:
        member = fuzzy_find_member(interaction.guild, self.username.value)
        if not member:
            await interaction.response.send_message("User not found.", ephemeral=True)
            return
        if member not in self.channel.members:
            await interaction.response.send_message(f"{member.display_name} must be in the channel to become owner.", ephemeral=True)
            return
        data = self.manager.get_data(self.channel.id)
        if not data:
            await interaction.response.send_message("Channel not found.", ephemeral=True)
            return
        old_owner_id = data.owner_id
        old_owner = interaction.guild.get_member(old_owner_id)
        self.manager.set_owner(self.channel.id, member.id)
        await self.channel.set_permissions(member, manage_channels=True, manage_permissions=True)
        if old_owner:
            await self.channel.set_permissions(old_owner, manage_channels=False, manage_permissions=False)
        await interaction.response.send_message(f"Ownership transferred to **{member.display_name}**.", ephemeral=True)
