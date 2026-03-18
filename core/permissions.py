"""
Permissions Manager — granular command access control and role-based restrictions.

Define permission levels (User, Moderator, Admin, Owner), assign roles per guild,
and check permissions before executing sensitive commands (voice, music, moderation).
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, Any

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Permission hierarchy: higher number = more privileges."""
    USER = 0           # Regular users
    MODERATOR = 1      # Moderators (mute, kick, music control)
    ADMIN = 2          # Server admins (settings, temp channels)
    OWNER = 3          # Bot owner (system commands, shutdowns)


@dataclass
class GuildPermissions:
    """Permission configuration for a guild."""
    guild_id: int
    voice_command_level: PermissionLevel = PermissionLevel.USER
    music_command_level: PermissionLevel = PermissionLevel.USER
    moderation_level: PermissionLevel = PermissionLevel.MODERATOR
    admin_level: PermissionLevel = PermissionLevel.ADMIN
    
    # Role-based permissions (role_id -> PermissionLevel)
    role_permissions: dict[int, PermissionLevel] = field(default_factory=dict)
    
    # Users who bypass permission checks
    trusted_users: set[int] = field(default_factory=set)
    
    # Blacklisted users/roles
    blacklisted_users: set[int] = field(default_factory=set)
    blacklisted_roles: set[int] = field(default_factory=set)


class PermissionManager:
    """Manage command permissions across guilds."""
    
    def __init__(self, db: Any):
        """Initialize permission manager with database."""
        self.db = db
        self.guild_permissions: dict[int, GuildPermissions] = {}
    
    def _load_permissions(self, guild_id: int) -> GuildPermissions:
        """Load or create permission config for guild."""
        if guild_id in self.guild_permissions:
            return self.guild_permissions[guild_id]
        
        # Try to load from database
        guild_data = self.db.get_guild(guild_id)
        if guild_data and 'permissions' in guild_data:
            perms_data = guild_data['permissions']
            
            # Convert string keys to ints for role_permissions
            role_perms = {}
            if 'role_permissions' in perms_data:
                for role_id_str, level_str in perms_data['role_permissions'].items():
                    try:
                        role_id = int(role_id_str)
                        level = PermissionLevel[level_str]
                        role_perms[role_id] = level
                    except (ValueError, KeyError):
                        pass
            
            perms = GuildPermissions(
                guild_id=guild_id,
                voice_command_level=PermissionLevel[perms_data.get('voice_command_level', 'USER')],
                music_command_level=PermissionLevel[perms_data.get('music_command_level', 'USER')],
                moderation_level=PermissionLevel[perms_data.get('moderation_level', 'MODERATOR')],
                admin_level=PermissionLevel[perms_data.get('admin_level', 'ADMIN')],
                role_permissions=role_perms,
                trusted_users=set(perms_data.get('trusted_users', [])),
                blacklisted_users=set(perms_data.get('blacklisted_users', [])),
                blacklisted_roles=set(perms_data.get('blacklisted_roles', []))
            )
        else:
            perms = GuildPermissions(guild_id=guild_id)
        
        self.guild_permissions[guild_id] = perms
        return perms
    
    def _save_permissions(self, guild_id: int) -> None:
        """Save permission config to database."""
        perms = self.guild_permissions.get(guild_id)
        if not perms:
            return
        
        perms_data = {
            'voice_command_level': perms.voice_command_level.name,
            'music_command_level': perms.music_command_level.name,
            'moderation_level': perms.moderation_level.name,
            'admin_level': perms.admin_level.name,
            'role_permissions': {
                str(role_id): level.name
                for role_id, level in perms.role_permissions.items()
            },
            'trusted_users': list(perms.trusted_users),
            'blacklisted_users': list(perms.blacklisted_users),
            'blacklisted_roles': list(perms.blacklisted_roles)
        }
        
        self.db.set_guild_field(guild_id, 'permissions', perms_data)
    
    def get_user_level(self, member: discord.Member) -> PermissionLevel:
        """Get the effective permission level for a user."""
        guild_id = member.guild.id
        perms = self._load_permissions(guild_id)
        
        # Owner gets max permissions
        if member.id in self.db.owner_ids if hasattr(self.db, 'owner_ids') else []:
            return PermissionLevel.OWNER
        
        # Trusted users skip to max
        if member.id in perms.trusted_users:
            return PermissionLevel.OWNER
        
        # Check if blacklisted
        if member.id in perms.blacklisted_users:
            return PermissionLevel.USER
        
        if any(role.id in perms.blacklisted_roles for role in member.roles):
            return PermissionLevel.USER
        
        # Check server permissions
        if member.guild_permissions.administrator:
            return PermissionLevel.ADMIN
        
        # Check role-based permissions
        max_level = PermissionLevel.USER
        for role in member.roles:
            if role.id in perms.role_permissions:
                level = perms.role_permissions[role.id]
                if level.value > max_level.value:
                    max_level = level
        
        # Check for moderator permissions (manage_messages, kick_members, etc.)
        if member.guild_permissions.manage_messages or member.guild_permissions.kick_members:
            if PermissionLevel.MODERATOR.value > max_level.value:
                max_level = PermissionLevel.MODERATOR
        
        return max_level
    
    def can_use_command(
        self,
        member: discord.Member,
        required_level: PermissionLevel
    ) -> bool:
        """Check if member can use a command at the required permission level."""
        user_level = self.get_user_level(member)
        return user_level.value >= required_level.value
    
    def set_role_permission(self, guild_id: int, role_id: int, level: PermissionLevel) -> None:
        """Assign a permission level to a role."""
        perms = self._load_permissions(guild_id)
        perms.role_permissions[role_id] = level
        self._save_permissions(guild_id)
        logger.info(f"Set role {role_id} to {level.name} in guild {guild_id}")
    
    def remove_role_permission(self, guild_id: int, role_id: int) -> bool:
        """Remove role-based permission override."""
        perms = self._load_permissions(guild_id)
        if role_id in perms.role_permissions:
            del perms.role_permissions[role_id]
            self._save_permissions(guild_id)
            logger.info(f"Removed role {role_id} permissions from guild {guild_id}")
            return True
        return False
    
    def add_trusted_user(self, guild_id: int, user_id: int) -> None:
        """Add user to trusted list (no permission checks)."""
        perms = self._load_permissions(guild_id)
        perms.trusted_users.add(user_id)
        self._save_permissions(guild_id)
        logger.info(f"Added user {user_id} to trusted list in guild {guild_id}")
    
    def remove_trusted_user(self, guild_id: int, user_id: int) -> bool:
        """Remove user from trusted list."""
        perms = self._load_permissions(guild_id)
        if user_id in perms.trusted_users:
            perms.trusted_users.discard(user_id)
            self._save_permissions(guild_id)
            logger.info(f"Removed user {user_id} from trusted list in guild {guild_id}")
            return True
        return False
    
    def blacklist_user(self, guild_id: int, user_id: int) -> None:
        """Blacklist a user from using commands."""
        perms = self._load_permissions(guild_id)
        perms.blacklisted_users.add(user_id)
        self._save_permissions(guild_id)
        logger.info(f"Blacklisted user {user_id} in guild {guild_id}")
    
    def unblacklist_user(self, guild_id: int, user_id: int) -> bool:
        """Remove user from blacklist."""
        perms = self._load_permissions(guild_id)
        if user_id in perms.blacklisted_users:
            perms.blacklisted_users.discard(user_id)
            self._save_permissions(guild_id)
            logger.info(f"Unblacklisted user {user_id} in guild {guild_id}")
            return True
        return False
    
    def set_command_level(
        self,
        guild_id: int,
        command_type: str,
        level: PermissionLevel
    ) -> bool:
        """Set required permission level for a command type."""
        perms = self._load_permissions(guild_id)
        
        if command_type == 'voice':
            perms.voice_command_level = level
        elif command_type == 'music':
            perms.music_command_level = level
        elif command_type == 'moderation':
            perms.moderation_level = level
        elif command_type == 'admin':
            perms.admin_level = level
        else:
            return False
        
        self._save_permissions(guild_id)
        logger.info(f"Set {command_type} requirement to {level.name} in guild {guild_id}")
        return True
    
    async def get_permissions_embed(self, guild: discord.Guild) -> discord.Embed:
        """Get a formatted embed showing current permissions."""
        perms = self._load_permissions(guild.id)
        
        embed = discord.Embed(
            title="🔐 Server Permissions",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        # Command level requirements
        embed.add_field(
            name="Voice Commands",
            value=f"`{perms.voice_command_level.name}`",
            inline=True
        )
        embed.add_field(
            name="Music Commands",
            value=f"`{perms.music_command_level.name}`",
            inline=True
        )
        embed.add_field(
            name="Moderation",
            value=f"`{perms.moderation_level.name}`",
            inline=True
        )
        
        # Role-based permissions
        if perms.role_permissions:
            role_perms_text = ""
            for role_id, level in sorted(perms.role_permissions.items()):
                role = guild.get_role(role_id)
                role_name = role.name if role else f"Unknown ({role_id})"
                role_perms_text += f"• {role_name}: `{level.name}`\n"
            
            embed.add_field(
                name="🎭 Role Overrides",
                value=role_perms_text[:1024],
                inline=False
            )
        
        # Trusted users
        if perms.trusted_users:
            trusted_text = ""
            for user_id in list(perms.trusted_users)[:5]:
                trusted_text += f"• <@{user_id}>\n"
            
            if len(perms.trusted_users) > 5:
                trusted_text += f"• +{len(perms.trusted_users) - 5} more"
            
            embed.add_field(
                name="⭐ Trusted Users",
                value=trusted_text,
                inline=False
            )
        
        # Blacklisted users
        if perms.blacklisted_users:
            blacklist_text = f"{len(perms.blacklisted_users)} user(s) blacklisted"
            embed.add_field(
                name="🚫 Blacklist",
                value=blacklist_text,
                inline=False
            )
        
        return embed


def require_permission(required_level: PermissionLevel):
    """Decorator to check permissions before executing a command."""
    def decorator(func: Callable) -> Callable:
        async def wrapper(ctx: commands.Context, *args, **kwargs) -> Any:
            # Get permission manager from bot
            if not hasattr(ctx.bot, 'permission_manager'):
                await ctx.send("❌ Permission system not initialized.")
                return
            
            perm_mgr = ctx.bot.permission_manager
            member = ctx.author
            
            # Check permissions
            if not perm_mgr.can_use_command(member, required_level):
                user_level = perm_mgr.get_user_level(member)
                embed = discord.Embed(
                    title="🚫 Permission Denied",
                    description=f"You need **{required_level.name}** permissions to use this command.\n"
                                f"Your level: **{user_level.name}**",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Execute command
            try:
                await func(ctx, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in permission-protected command: {e}")
                await ctx.send(f"❌ Command error: {str(e)[:100]}")
        
        return wrapper
    return decorator
