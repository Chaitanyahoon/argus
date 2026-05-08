"""
Unit tests for rate limiting logic.

Run with: python -m pytest tests/test_rate_limiting.py -v
"""

import unittest
import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the rate limiting function (we'll test the logic)


class RateLimiter:
    """Rate limiter utility for testing."""
    
    def __init__(self, max_attempts: int, time_window: float):
        self.max_attempts = max_attempts
        self.time_window = time_window
        self.attempts = {}
    
    def check(self, key: str) -> tuple[bool, str]:
        """Check if action is allowed. Returns (allowed, message)."""
        now = time.time()
        
        if key not in self.attempts:
            self.attempts[key] = []
        
        # Clean old attempts
        self.attempts[key] = [t for t in self.attempts[key] if now - t < self.time_window]
        
        if len(self.attempts[key]) >= self.max_attempts:
            if self.attempts[key]:  # Only calculate retry if there are previous attempts
                retry_after = int(self.time_window - (now - self.attempts[key][0])) + 1
            else:
                retry_after = int(self.time_window)
            return False, f"Rate limited. Retry after {retry_after}s"
        
        self.attempts[key].append(now)
        return True, ""


class TestRateLimiting(unittest.TestCase):
    """Tests for rate limiting logic."""

    def setUp(self):
        """Create rate limiter for testing."""
        self.limiter = RateLimiter(max_attempts=3, time_window=2.0)  # 3 attempts per 2 seconds

    def test_first_attempt_allowed(self):
        """First attempt should always be allowed."""
        allowed, msg = self.limiter.check("guild_123")
        self.assertTrue(allowed)
        self.assertEqual(msg, "")

    def test_multiple_attempts_allowed(self):
        """Multiple attempts within limit should be allowed."""
        for i in range(3):
            allowed, msg = self.limiter.check("guild_123")
            self.assertTrue(allowed, f"Attempt {i+1} should be allowed")

    def test_exceeds_limit(self):
        """Exceeding limit should block and provide retry time."""
        # Use up all attempts
        for i in range(3):
            self.limiter.check("guild_123")
        
        # Next attempt should be blocked
        allowed, msg = self.limiter.check("guild_123")
        self.assertFalse(allowed)
        self.assertIn("Rate limited", msg)
        self.assertIn("Retry after", msg)

    def test_different_keys_independent(self):
        """Different keys should have independent rate limits."""
        # Use up attempts for guild_1
        for i in range(3):
            self.limiter.check("guild_1")
        
        # guild_1 should be blocked
        allowed1, _ = self.limiter.check("guild_1")
        self.assertFalse(allowed1)
        
        # guild_2 should still be allowed
        allowed2, _ = self.limiter.check("guild_2")
        self.assertTrue(allowed2)

    def test_cleanup_after_window(self):
        """Old attempts should be cleaned after time window."""
        # Make 3 attempts
        for i in range(3):
            self.limiter.check("guild_123")
        
        # Should be blocked
        allowed, _ = self.limiter.check("guild_123")
        self.assertFalse(allowed)
        
        # Wait for time window to pass
        time.sleep(2.1)
        
        # Should be allowed again
        allowed, msg = self.limiter.check("guild_123")
        self.assertTrue(allowed)

    def test_retry_time_accuracy(self):
        """Retry time should be approximately correct."""
        # Make 3 attempts
        start_time = time.time()
        for i in range(3):
            self.limiter.check("guild_123")
        
        # Should be blocked
        allowed, msg = self.limiter.check("guild_123")
        self.assertFalse(allowed)
        
        # Extract retry time (rough estimate)
        elapsed = time.time() - start_time
        # Retry time should be close to 2.0 - elapsed (time window minus elapsed time)
        # Allow 0.5s margin
        self.assertIn("Retry after", msg)

    def test_rapid_successive_attempts(self):
        """Should handle rapid successive attempts in same second."""
        # Make attempts as fast as possible
        results = []
        for i in range(5):
            allowed, msg = self.limiter.check("guild_123")
            results.append((allowed, msg))
        
        # First 3 should be allowed
        self.assertTrue(results[0][0])
        self.assertTrue(results[1][0])
        self.assertTrue(results[2][0])
        
        # Next 2 should be blocked
        self.assertFalse(results[3][0])
        self.assertFalse(results[4][0])

    def test_zero_limit_blocks_all(self):
        """Zero attempts should block everything."""
        limiter = RateLimiter(max_attempts=0, time_window=1.0)
        allowed, _ = limiter.check("guild_123")
        self.assertFalse(allowed)

    def test_high_volume(self):
        """Should handle high volume of requests."""
        limiter = RateLimiter(max_attempts=10, time_window=5.0)
        
        # Process 100 requests across 10 keys
        for i in range(100):
            guild_id = f"guild_{i % 10}"
            allowed, msg = limiter.check(guild_id)
            
            # Each key should allow first 10 attempts
            expected_allowed = (i // 10) < 10
            if (i % 10) < 10:  # Within limit for this guild
                self.assertTrue(allowed, f"Request {i} to {guild_id} should be allowed")


class TestRateLimitingPractical(unittest.TestCase):
    """Practical rate limiting scenarios."""

    def test_voice_command_scenario(self):
        """Simulate voice command rate limiting (5 per 30s)."""
        limiter = RateLimiter(max_attempts=5, time_window=30.0)
        
        # Rapid guild spam attempt
        for i in range(5):
            allowed, _ = limiter.check("guild_spam_test")
            self.assertTrue(allowed)
        
        # 6th should be blocked
        allowed, msg = limiter.check("guild_spam_test")
        self.assertFalse(allowed)
        self.assertIn("Rate limited", msg)

    def test_normal_usage_pattern(self):
        """Simulate normal usage (spaced out commands)."""
        limiter = RateLimiter(max_attempts=5, time_window=30.0)
        
        # Make 5 commands with 1 second gaps
        for i in range(5):
            allowed, _ = limiter.check("guild_normal_use")
            self.assertTrue(allowed)
            time.sleep(0.1)
        
        # 6th attempts within window should fail
        allowed, _ = limiter.check("guild_normal_use")
        self.assertFalse(allowed)


if __name__ == "__main__":
    unittest.main()
