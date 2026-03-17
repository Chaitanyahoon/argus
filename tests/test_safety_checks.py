"""
Unit tests for safety checks in moderation functions.

Run with: python -m pytest tests/test_safety_checks.py -v
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class SafetyChecks:
    """Safety check utilities for moderation (for testing purposes)."""
    
    @staticmethod
    def can_kick_user(member_id: int, guild_owner_id: int, member_role_position: int, 
                      bot_role_position: int) -> tuple[bool, str]:
        """Check if user can be kicked safely."""
        if member_id == guild_owner_id:
            return False, "Cannot kick server owner"
        if member_role_position >= bot_role_position:
            return False, "Insufficient permissions (role too high)"
        return True, ""
    
    @staticmethod
    def can_ban_user(member_id: int, guild_owner_id: int, member_role_position: int,
                     bot_role_position: int, is_bot: bool) -> tuple[bool, str]:
        """Check if user can be banned safely."""
        if is_bot:
            return False, "Cannot ban bots"
        if member_id == guild_owner_id:
            return False, "Cannot ban server owner"
        if member_role_position >= bot_role_position:
            return False, "Insufficient permissions (role too high)"
        return True, ""
    
    @staticmethod
    def can_mute_user(member_id: int, already_muted: bool, in_voice: bool,
                      is_bot: bool) -> tuple[bool, str]:
        """Check if user can be muted safely."""
        if is_bot:
            return False, "Cannot mute bots"
        if not in_voice:
            return False, "User not in voice channel"
        if already_muted:
            return False, "User already muted"
        return True, ""
    
    @staticmethod
    def can_unmute_user(member_id: int, already_unmuted: bool, in_voice: bool,
                        is_bot: bool) -> tuple[bool, str]:
        """Check if user can be unmuted safely."""
        if is_bot:
            return False, "Cannot unmute bots"
        if not in_voice:
            return False, "User not in voice channel"
        if already_unmuted:
            return False, "User already unmuted"
        return True, ""


class TestKickSafety(unittest.TestCase):
    """Tests for kick safety checks."""

    def test_can_kick_normal_user(self):
        """Should allow kicking normal users."""
        allowed, msg = SafetyChecks.can_kick_user(
            member_id=123456,
            guild_owner_id=654321,
            member_role_position=1,
            bot_role_position=5
        )
        self.assertTrue(allowed)

    def test_cannot_kick_owner(self):
        """Should prevent kicking server owner."""
        allowed, msg = SafetyChecks.can_kick_user(
            member_id=654321,
            guild_owner_id=654321,
            member_role_position=10,
            bot_role_position=5
        )
        self.assertFalse(allowed)
        self.assertIn("owner", msg.lower())

    def test_cannot_kick_higher_role(self):
        """Should prevent kicking users with higher role."""
        allowed, msg = SafetyChecks.can_kick_user(
            member_id=123456,
            guild_owner_id=654321,
            member_role_position=10,
            bot_role_position=5
        )
        self.assertFalse(allowed)
        self.assertIn("permissions", msg.lower())

    def test_can_kick_equal_role_position(self):
        """Should prevent kicking users at same role level."""
        allowed, msg = SafetyChecks.can_kick_user(
            member_id=123456,
            guild_owner_id=654321,
            member_role_position=5,
            bot_role_position=5
        )
        self.assertFalse(allowed)

    def test_can_kick_lower_role(self):
        """Should allow kicking users with lower role."""
        allowed, msg = SafetyChecks.can_kick_user(
            member_id=123456,
            guild_owner_id=654321,
            member_role_position=2,
            bot_role_position=5
        )
        self.assertTrue(allowed)


class TestBanSafety(unittest.TestCase):
    """Tests for ban safety checks."""

    def test_cannot_ban_bots(self):
        """Should prevent banning bots."""
        allowed, msg = SafetyChecks.can_ban_user(
            member_id=123456,
            guild_owner_id=654321,
            member_role_position=1,
            bot_role_position=5,
            is_bot=True
        )
        self.assertFalse(allowed)
        self.assertIn("bot", msg.lower())

    def test_cannot_ban_owner(self):
        """Should prevent banning server owner."""
        allowed, msg = SafetyChecks.can_ban_user(
            member_id=654321,
            guild_owner_id=654321,
            member_role_position=10,
            bot_role_position=5,
            is_bot=False
        )
        self.assertFalse(allowed)
        self.assertIn("owner", msg.lower())

    def test_cannot_ban_higher_role(self):
        """Should prevent banning users with higher role."""
        allowed, msg = SafetyChecks.can_ban_user(
            member_id=123456,
            guild_owner_id=654321,
            member_role_position=8,
            bot_role_position=5,
            is_bot=False
        )
        self.assertFalse(allowed)

    def test_can_ban_normal_user(self):
        """Should allow banning normal users."""
        allowed, msg = SafetyChecks.can_ban_user(
            member_id=123456,
            guild_owner_id=654321,
            member_role_position=1,
            bot_role_position=5,
            is_bot=False
        )
        self.assertTrue(allowed)


class TestMuteSafety(unittest.TestCase):
    """Tests for mute safety checks."""

    def test_cannot_mute_bots(self):
        """Should prevent muting bots."""
        allowed, msg = SafetyChecks.can_mute_user(
            member_id=123456,
            already_muted=False,
            in_voice=True,
            is_bot=True
        )
        self.assertFalse(allowed)
        self.assertIn("bot", msg.lower())

    def test_cannot_mute_not_in_voice(self):
        """Should prevent muting users not in voice."""
        allowed, msg = SafetyChecks.can_mute_user(
            member_id=123456,
            already_muted=False,
            in_voice=False,
            is_bot=False
        )
        self.assertFalse(allowed)
        self.assertIn("voice", msg.lower())

    def test_cannot_mute_already_muted(self):
        """Should prevent double-muting."""
        allowed, msg = SafetyChecks.can_mute_user(
            member_id=123456,
            already_muted=True,
            in_voice=True,
            is_bot=False
        )
        self.assertFalse(allowed)
        self.assertIn("already muted", msg.lower())

    def test_can_mute_normal_user(self):
        """Should allow muting normal users in voice."""
        allowed, msg = SafetyChecks.can_mute_user(
            member_id=123456,
            already_muted=False,
            in_voice=True,
            is_bot=False
        )
        self.assertTrue(allowed)


class TestUnmuteSafety(unittest.TestCase):
    """Tests for unmute safety checks."""

    def test_cannot_unmute_bots(self):
        """Should prevent unmuting bots."""
        allowed, msg = SafetyChecks.can_unmute_user(
            member_id=123456,
            already_unmuted=False,
            in_voice=True,
            is_bot=True
        )
        self.assertFalse(allowed)
        self.assertIn("bot", msg.lower())

    def test_cannot_unmute_not_in_voice(self):
        """Should prevent unmuting users not in voice."""
        allowed, msg = SafetyChecks.can_unmute_user(
            member_id=123456,
            already_unmuted=False,
            in_voice=False,
            is_bot=False
        )
        self.assertFalse(allowed)
        self.assertIn("voice", msg.lower())

    def test_cannot_unmute_already_unmuted(self):
        """Should prevent double-unmuting."""
        allowed, msg = SafetyChecks.can_unmute_user(
            member_id=123456,
            already_unmuted=True,
            in_voice=True,
            is_bot=False
        )
        self.assertFalse(allowed)
        self.assertIn("already unmuted", msg.lower())

    def test_can_unmute_normal_user(self):
        """Should allow unmuting muted users in voice."""
        allowed, msg = SafetyChecks.can_unmute_user(
            member_id=123456,
            already_unmuted=False,
            in_voice=True,
            is_bot=False
        )
        self.assertTrue(allowed)


class TestSafetyChecksCombinations(unittest.TestCase):
    """Tests for combinations of safety scenarios."""

    def test_owner_protection_across_operations(self):
        """Owner should be protected across all operations."""
        owner_id = 999999
        
        # Cannot kick owner
        kick_ok, _ = SafetyChecks.can_kick_user(owner_id, owner_id, 10, 5)
        self.assertFalse(kick_ok)
        
        # Cannot ban owner
        ban_ok, _ = SafetyChecks.can_ban_user(owner_id, owner_id, 10, 5, False)
        self.assertFalse(ban_ok)

    def test_bot_protection_across_operations(self):
        """Bots should be protected across operations."""
        bot_id = 888888
        
        # Cannot ban bot
        ban_ok, _ = SafetyChecks.can_ban_user(bot_id, 999999, 1, 5, True)
        self.assertFalse(ban_ok)
        
        # Cannot mute bot
        mute_ok, _ = SafetyChecks.can_mute_user(bot_id, False, True, True)
        self.assertFalse(mute_ok)

    def test_role_hierarchy_enforcement(self):
        """Role hierarchy should be enforced consistently."""
        # Create a hierarchy: bot @5, regular user @2, high role user @8
        
        # Can kick user @2
        ok1, _ = SafetyChecks.can_kick_user(111, 999, 2, 5)
        self.assertTrue(ok1)
        
        # Cannot kick user @8
        ok2, _ = SafetyChecks.can_kick_user(222, 999, 8, 5)
        self.assertFalse(ok2)
        
        # Cannot kick user @5 (equal)
        ok3, _ = SafetyChecks.can_kick_user(333, 999, 5, 5)
        self.assertFalse(ok3)


if __name__ == "__main__":
    unittest.main()
