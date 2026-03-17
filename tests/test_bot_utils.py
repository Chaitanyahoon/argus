"""
Unit tests for bot utility functions (fuzzy matching, etc).

Run with: python -m pytest tests/test_bot_utils.py -v
"""

import unittest
from unittest.mock import Mock, MagicMock
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.bot_utils import fuzzy_find_member, fuzzy_find_channel


class MockMember:
    """Mock Discord member for testing."""
    def __init__(self, display_name: str, name: str, global_name: str = ""):
        self.display_name = display_name
        self.name = name
        self.global_name = global_name


class MockChannel:
    """Mock Discord channel for testing."""
    def __init__(self, name: str, channel_type=None):
        self.name = name
        self.type = channel_type


class TestFuzzyFindMember(unittest.TestCase):
    """Tests for fuzzy member matching."""

    def setUp(self):
        """Create mock guild and members."""
        self.guild = Mock()
        self.members = [
            MockMember("John Doe", "johndoe", "John"),
            MockMember("Jane Smith", "janesmith", "Jane"),
            MockMember("Bob Johnson", "bobjohnson", "Bob"),
            MockMember("Alice Wonder", "alicewonder", "Alice"),
        ]
        self.guild.members = self.members

    def test_exact_display_name_match(self):
        """Should find member with exact display name match."""
        result = fuzzy_find_member(self.guild, "John Doe")
        self.assertIsNotNone(result)
        self.assertEqual(result.display_name, "John Doe")

    def test_exact_username_match(self):
        """Should find member with exact username match."""
        result = fuzzy_find_member(self.guild, "johndoe")
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "johndoe")

    def test_partial_match(self):
        """Should find member with partial name match."""
        result = fuzzy_find_member(self.guild, "John")
        self.assertIsNotNone(result)
        self.assertEqual(result.display_name, "John Doe")

    def test_case_insensitive(self):
        """Should match regardless of case."""
        result = fuzzy_find_member(self.guild, "ALICE")
        self.assertIsNotNone(result)
        self.assertEqual(result.display_name, "Alice Wonder")

    def test_substring_match(self):
        """Should match substring with bonus score."""
        result = fuzzy_find_member(self.guild, "Smith")
        self.assertIsNotNone(result)
        self.assertEqual(result.display_name, "Jane Smith")

    def test_no_match_returns_none(self):
        """Should return None if no good match found."""
        result = fuzzy_find_member(self.guild, "NonExistentUser")
        self.assertIsNone(result)

    def test_short_name_exact_match(self):
        """Should find short names only if exact match."""
        result = fuzzy_find_member(self.guild, "Bob")
        self.assertIsNotNone(result)
        # 'Bob' should match well with 'Bob Johnson' display name
        self.assertEqual(result.display_name, "Bob Johnson")

    def test_short_name_no_match(self):
        """Should return None for short name without good match."""
        result = fuzzy_find_member(self.guild, "Jo")
        # 'Jo' is too ambiguous and short, should not match
        self.assertIsNone(result)

    def test_whitespace_handling(self):
        """Should handle leading/trailing whitespace."""
        result = fuzzy_find_member(self.guild, "  Jane  ")
        self.assertIsNotNone(result)
        self.assertEqual(result.display_name, "Jane Smith")


class TestFuzzyFindChannel(unittest.TestCase):
    """Tests for fuzzy channel matching."""

    def setUp(self):
        """Create mock guild and channels."""
        self.guild = Mock()
        self.channels = [
            MockChannel("general"),
            MockChannel("gaming"),
            MockChannel("voice-channel"),
            MockChannel("announcements"),
        ]
        self.guild.channels = self.channels

    def test_exact_channel_match(self):
        """Should find channel with exact name match."""
        result = fuzzy_find_channel(self.guild, "general")
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "general")

    def test_partial_channel_match(self):
        """Should find channel with partial name match."""
        result = fuzzy_find_channel(self.guild, "game")
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "gaming")

    def test_space_to_dash_conversion(self):
        """Should handle space-to-dash conversion."""
        result = fuzzy_find_channel(self.guild, "voice channel")
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "voice-channel")

    def test_case_insensitive_channel(self):
        """Should match channels case-insensitively."""
        result = fuzzy_find_channel(self.guild, "ANNOUNCEMENTS")
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "announcements")

    def test_no_channel_match(self):
        """Should return None for non-existent channel."""
        result = fuzzy_find_channel(self.guild, "nonexistent-channel")
        self.assertIsNone(result)

    def test_channel_type_filter(self):
        """Should filter channels by type if specified."""
        from discord import ChannelType
        mock_channel = MockChannel("general", ChannelType.text)
        self.channels[0] = mock_channel
        
        result = fuzzy_find_channel(self.guild, "general", ChannelType.text)
        self.assertIsNotNone(result)


class TestFuzzyMatchingEdgeCases(unittest.TestCase):
    """Edge case tests for fuzzy matching."""

    def test_empty_name_returns_none(self):
        """Should return None for empty search string."""
        guild = Mock()
        guild.members = [MockMember("John", "john", "John")]
        result = fuzzy_find_member(guild, "")
        self.assertIsNone(result)

    def test_member_with_empty_global_name(self):
        """Should handle members with empty global_name."""
        guild = Mock()
        guild.members = [MockMember("John", "john", "")]
        result = fuzzy_find_member(guild, "john")
        self.assertIsNotNone(result)

    def test_score_threshold(self):
        """Should respect the 0.5 score threshold."""
        guild = Mock()
        guild.members = [MockMember("Alexander", "alexander", "Alex")]
        # "x" has very low similarity to "Alexander"
        result = fuzzy_find_member(guild, "xyz")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
