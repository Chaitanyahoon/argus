# 🌿 Contributing to Argus

Thank you for your interest in contributing! This guide will help you set up the development environment and understand our workflow.

## 🚀 Getting Started

### Prerequisites
- Git
- Python 3.11+
- Virtual environment (venv)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/Chaitanyahoon/argus.git
cd argus

# Create & activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Configure Environment

```bash
cp .env.example .env
# Edit .env with your Discord Token and Gemini API Key
```

### Verify Installation

```bash
python bot.py
```

---

## 📝 Code Standards

### Python Style Guide
- Follow **PEP 8** conventions
- Add docstrings to all functions and classes
- Type hints encouraged (but not required)
- Max line length: **100 characters**
- Use descriptive variable names

### Function Example
```python
async def checkin_callback(interaction: discord.Interaction) -> None:
    """Handle wellness check-in interaction."""
    await interaction.response.defer()
    # Implementation...
```

### Commit Message Format
```
type: brief description

Types:
  feat   - New feature
  fix    - Bug fix
  docs   - Documentation
  refactor - Code refactoring
  style  - Code style (formatting, missing semicolons, etc)
  perf   - Performance improvement

Example:
feat: Add crisis detection in wellness check-in
fix: Prevent duplicate voice sessions
docs: Update voice AI command reference
```

---

## 🔄 Workflow

### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes
- Write clean, well-documented code
- Follow existing code patterns in the project
- Test your changes locally

### 3. Commit Changes
```bash
git add .
git commit -m "feat: Your feature description"
git push origin feature/your-feature-name
```

### 4. Create Pull Request
- Describe what you changed and why
- Reference any related issues
- Be ready for feedback and iteration

---

## 🏗️ Project Structure

```
argus/
├── bot.py                    # Main entry point
├── config.py                 # Configuration from .env
├── cogs/
│   ├── therapy.py            # Wellness features
│   └── voice.py              # Voice AI commands
├── core/
│   ├── voice_listener.py     # Voice pipeline
│   ├── live_session.py       # Gemini Live API
│   ├── database.py           # SQLite database
│   └── audio_utils.py        # Audio processing
└── requirements.txt
```

### Key Components

**Voice Listener**
- Receives Discord voice audio
- Transcribes using faster-whisper
- Communicates with Gemini Live API

**Live Session**
- Maintains WebSocket connection to Gemini
- Handles bidirectional voice streaming
- Executes function calls for voice commands

**Therapy**
- Mood tracking and check-ins
- Journal entries
- Crisis detection with support resources

---

## 📚 Before You Submit

- ✅ Code follows PEP 8 standards
- ✅ Docstrings added to new functions
- ✅ Your changes don't break existing features
- ✅ Commit message follows our format
- ✅ Documentation updated if needed

---

## ❓ Questions?

- Open an issue for bugs or feature requests
- Check existing issues before creating duplicates
- Be respectful and constructive in discussions

Happy contributing! 🎉
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

# Inspect Bot State
```bash
# In Discord
!status         # Shows bot status
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
