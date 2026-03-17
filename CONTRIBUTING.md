# Contributing to Argus Discord Bot

Thank you for your interest in contributing! This guide explains how to set up development environment and contribute code.

## Development Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Chaitanyahoon/argus.git
cd argus
```

### 2. Create Virtual Environment
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install pytest pytest-cov  # For testing
```

### 4. Setup .env File
```bash
cp .env.example .env
# Edit .env with your Discord token and API keys
```

### 5. Verify Setup
```bash
# Run tests
python run_tests.py -v

# Try bot
python bot.py
```

---

## Code Style & Guidelines

### Python Style
- Use PEP 8 conventions
- Docstrings for all functions/classes
- Type hints preferred but not required
- Max line length: 100 characters

### Example Function:
```python
async def execute_moderation(guild: discord.Guild, username: str, action: str) -> str:
    """
    Execute a moderation action on a guild member.
    
    Args:
        guild: The Discord guild
        username: Name of the target member
        action: Action to execute (kick, ban, mute)
    
    Returns:
        Status message (success or error)
    """
    member = fuzzy_find_member(guild, username)
    if not member:
        return f"❌ User '{username}' not found."
    
    # ... rest of implementation
```

### Commit Messages
```
Format: Type: Brief description

Types:
- feat: New feature
- fix: Bug fix
- test: Tests
- docs: Documentation
- refactor: Code refactoring
- perf: Performance improvement

Example:
feat: Add rate limiting for voice commands
fix: Prevent kicking server owner
docs: Update troubleshooting guide
```

---

## Making Changes

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes
- Write clean, documented code
- Add tests for new functionality
- Follow existing code patterns

### 3. Run Tests Locally
```bash
# Run all tests
python run_tests.py -v

# Run specific test
pytest tests/test_bot_utils.py -v

# With coverage
python run_tests.py --coverage
```

### 4. Update Documentation
- Update README.md if user-facing change
- Update docstrings in code
- Add to TROUBLESHOOTING.md if adding new features

### 5. Commit & Push
```bash
git add .
git commit -m "feat: brief description of changes"
git push origin feature/your-feature-name
```

### 6. Create Pull Request
- Describe what you changed and why
- Reference any related issues
- Link to Discord server testing

---

## Architecture Overview

```
discordbot/
├── bot.py                 # Main bot entry point
├── config.py              # Configuration from .env
├── core/
│   ├── voice_listener.py  # Voice command processing
│   ├── bot_utils.py       # Shared utilities (fuzzy matching)
│   ├── live_session.py    # Gemini Live API connection
│   ├── transcriber.py     # Speech-to-text
│   ├── music_player.py    # Music playback
│   ├── temp_voice.py      # Temporary Voice Channels
│   └── argus_systems.py   # XP/leveling system
├── data/                  # User/guild data (JSON)
├── tests/                 # Unit tests
└── requirements.txt       # Dependencies
```

---

## Key Components

### VoiceListener
Handles real-time voice processing:
1. Receives audio from Discord
2. Transcribes with Whisper
3. Sends to Gemini Live API
4. Executes tool calls (moderation, music, etc)

### Safety Checks
All moderation functions include:
- Owner protection
- Role hierarchy checks
- Bot protection
- Self-harm prevention
- Duplicate action prevention

### Rate Limiting
- Per-guild: 5 voice commands per 30 seconds
- Per-user: Command-specific cooldowns
- Prevents spam and API abuse

---

## Testing

### Run All Tests
```bash
python run_tests.py -v
```

### Test Coverage
```bash
python run_tests.py --coverage
```

### Write New Tests

Example:
```python
# tests/test_my_feature.py
import unittest

class TestMyFeature(unittest.TestCase):
    def test_something(self):
        result = my_function()
        self.assertTrue(result)
    
    def test_error_handling(self):
        with self.assertRaises(ValueError):
            my_function("invalid")

if __name__ == "__main__":
    unittest.main()
```

---

## Debugging Tips

### Enable Debug Logging
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### Add Breakpoints
```python
# In PyCharm or VS Code
breakpoint()  # Execution will pause here
```

### Inspect Bot State
```bash
# In Discord
!status         # Shows bot status
!queue          # Music queue
!help           # All commands
```

---

## Performance Considerations

### Avoid Blocking Operations
Bad:
```python
time.sleep(5)  # Blocks event loop
```

Good:
```python
await asyncio.sleep(5)  # Async sleep
```

### Cache When Possible
```python
# Cache guild data to avoid repeated lookups
self.guild_cache[guild_id] = guild_data
```

### Use Async/Await
All I/O operations should be async (Discord, API calls, file I/O).

---

## Submitting Changes

1. **Test thoroughly**: Run tests locally first
2. **Document changes**: Update README/docstrings
3. **Keep commits clean**: One feature per branch
4. **Write good commit messages**: Follow the format
5. **Request review**: Create PR with clear description

---

## Code Review Process

When your PR is ready:
1. One approval required from maintainer
2. All tests must pass (GitHub Actions)
3. No conflicts with main branch
4. Documentation updated

---

## Reporting Bugs

If you find a bug:
1. Check TROUBLESHOOTING.md first
2. Search existing issues
3. Create detailed bug report with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages/logs
   - Environment (OS, Python version)
   - Discord.py version

---

## Feature Requests

Have an idea? Open an issue with:
1. Clear description of feature
2. Why it's useful
3. Example usage
4. Potential implementation approach

---

## Questions?

- Check README.md for user documentation
- See TROUBLESHOOTING.md for common issues
- Review existing code for examples
- Ask in GitHub discussions

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Happy coding! 🚀
