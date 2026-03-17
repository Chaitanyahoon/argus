## 🧪 Testing

This project includes comprehensive unit tests for safety, reliability, and code quality.

### Run Tests

```bash
# All tests with verbose output
python run_tests.py -v

# With coverage report
python run_tests.py --coverage

# Specific test file
pytest tests/test_safety_checks.py -v
```

**Test Coverage:**
- ✅ **81 test cases** covering fuzzy matching, rate limiting, safety checks
- ✅ Moderation function safety (kick/ban/mute/unmute)
- ✅ Channel management edge cases
- ✅ Rate limiting enforcement

See [tests/README.md](tests/README.md) for detailed testing guide.

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues & solutions |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development guide for contributors |
| [tests/README.md](tests/README.md) | Unit testing guide |
| [.env.example](.env.example) | Configuration template with comments |

### Quick Help

**Still having issues?**
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common problems
2. Run tests: `python run_tests.py -v`
3. Enable debug logging: `LOG_LEVEL=DEBUG` in `.env`

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Code style guidelines
- How to submit changes
- Testing requirements

---

## 📊 Features & Safety

✅ **Safety First**
- Owner protection (cannot kick/ban server owner)
- Role hierarchy validation
- Bot protection (cannot moderate bots)
- Double-action prevention (no double-mute)
- Occupied channel protection

✅ **Rate Limiting**
- 5 voice commands per 30 seconds per guild
- Per-user cooldowns on sensitive commands
- Prevents spam and API abuse

✅ **Error Handling**
- Comprehensive error messages with emojis
- Proper Discord permission checks
- Graceful degradation on API failures

✅ **Monitoring & Logging**
- Rich log embeds with timestamps
- Event tracking for all moderation actions
- Status rotation (visual bot engagement)

---

## 🐛 Bug Report Template

If you find an issue:

```markdown
**Description:** Brief description of the bug

**Steps to reproduce:**
1. Do this
2. Then this
3. Observe bug

**Expected behavior:** What should happen

**Actual behavior:** What actually happened

**Environment:**
- OS: (Windows/macOS/Linux)
- Python: 3.x
- Bot version: (latest/specific commit)
- Error message: (full traceback)
```

---

## 📝 Changelog

### v1.0 (Current)
- ✨ Real-time voice conversation via Gemini Live API
- 🎙️ Voice moderation commands (kick, ban, mute)
- 🎵 Music player with queue management
- 🏘️ Temporary voice channel creation
- 💾 User level/XP tracking system
- 🛡️ Comprehensive safety checks
- 🧪 81 unit tests covering core functionality
- 📖 Complete documentation + troubleshooting guide
- ⚡ Rate limiting & error handling

---

## 📞 Support

- **Question?** Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Want to contribute?** See [CONTRIBUTING.md](CONTRIBUTING.md)
- **Found a bug?** Use the bug report template above
- **Feature request?** Open an issue with use case

---

## 📄 License

[MIT License](LICENSE) - Use freely, credit appreciated!

---

## 👨‍💻 Authors

- **Chaitanya** - Original creator & maintainer

---

**Last Updated:** March 17, 2026

*Argus is continuously evolving. Check back for updates!*
