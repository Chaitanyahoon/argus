# 🔧 Troubleshooting Guide

Common issues and solutions for the Argus Discord Bot.

## Setup & Installation

### ❌ `ModuleNotFoundError: No module named 'discord'`
**Solution**: Install requirements
```bash
pip install -r requirements.txt
```

### ❌ `ImportError: DLL load failed` (OpusError on Windows)
**Solution**: 
- Download libopus DLL: https://github.com/xiph/opus/releases
- Place in `C:\Program Files\` or add to PATH
- Or install via vcpkg: `vcpkg install opus`

### ❌ `FileNotFoundError: .env file not found`
**Solution**:
1. Copy `.env.example` to `.env`
2. Fill in your Discord token and API keys
```bash
cp .env.example .env
# Edit .env with your tokens
```

### ❌ `Exception occurred while reading from stream: name 'OPUS_LOADED' is not defined`
**Solution**: Opus library not loading. Try different paths:
- macOS: `/opt/homebrew/lib/libopus.dylib`
- Linux: `/usr/lib/x86_64-linux-gnu/libopus.so.0`
- Windows: Install via vcpkg

---

## Discord Bot Configuration

### ❌ Bot doesn't respond to commands
**Check**:
1. Is the bot in the server? Invite URL from OAuth2 generator
2. Does the bot have `Send Messages` permission?
3. Is the prefix correct? (default: `!`)

### ❌ Bot can't join voice channels
**Check**:
1. Bot has `Connect` and `Speak` permissions in voice channels
2. Try from terminal: `!join` (must be in a voice channel first)
3. Verify bot intents enabled in Developer Portal:
   - ✅ Voice States Intent
   - ✅ Message Content Intent

### ❌ Bot shows "Permission denied" when moderating
**Solution**:
- Bot's role must be **higher** than the target member's role
- Bot cannot moderate the server owner
- Adjust role hierarchy in server settings

---

## Voice Recognition & AI

### ❌ Bot doesn't respond to voice commands
**Check**:
1. Did you use `!listen` to start listening?
2. Are you speaking clearly? Try simple words
3. Check logs: `!status` shows current state

### ⚠️ Slow voice response (30+ seconds)
**Solution**: 
- First run is slow (Whisper model loading ~1GB)
- Decrease model size in `.env`:
  ```
  WHISPER_MODEL=tiny.en  # Faster, less accurate
  # or
  WHISPER_MODEL=small.en  # Balanced (default: base.en)
  ```

### ❌ "ModuleNotFoundError: No module named 'faster_whisper'"
**Solution**:
```bash
pip install faster-whisper
```

### ❌ Gemini API returns error 403
**Solution**:
1. Verify API key in `.env` is correct
2. Check quota: https://aistudio.google.com/app/apikey
3. Create new key if needed

### ❌ "google.generativeai.types.BlocUsageError"
**Solution**: Rate limit exceeded
- Wait 1 minute before retrying
- Check usage at console.cloud.google.com

---

## Moderation & Commands

### ❌ "Permission denied: Cannot kick [user]"
**Reasons**:
1. Bot role is lower than user's role
2. User is server owner (cannot kick)
3. User is a bot (cannot kick)

**Solution**: 
- Promote bot role in server settings
- Or use `!permissions @bot_name` to check

### ❌ Command says "User already muted" after unmute
**Possible cause**: User was muted by another source (role settings)

**Solution**:
1. Check user's role mute status
2. Manually adjust in role permissions
3. Try unmute again

### ❌ "Channel not found" when creating voice channel
**Solution**:
- Channel name might be too long (max 100 chars)
- Server might be at channel limit (500 max)
- Try a simpler name

### ❌ Cannot delete voice channel
**Reason**: Channel has users in it

**Solution**:
1. Move all users out first: `!voice move [new_channel]`
2. Or wait for users to leave
3. Then try delete again

---

## Database & Persistence

### ❌ `users.json` or `guilds.json` corrupted
**Solution**:
1. Stop the bot
2. Create backup: `mv users.json users.json.backup`
3. Delete corrupted file
4. Restart bot (will recreate empty)

### ⚠️ Data lost after restart
**Issue**: Bot uses local JSON files (not persistent across restarts)

**Solution**: 
- For production: Use PostgreSQL instead
- Or mount volume if using Docker

---

## Performance & Resources

### ⚠️ Bot uses high memory (>1GB)
**Reason**: Whisper model loaded in memory

**Solution**:
- Use smaller model: `WHISPER_MODEL=tiny.en`
- Or share GPU: Install CUDA + set `device="cuda"` in code

### ⚠️ High latency between voice input and response
**Solution**:
1. Check network speed
2. Use smaller Whisper model
3. Reduce audio buffer size (advanced)

### ❌ Bot crashes after 10 minutes
**Check logs for**:
1. Connection timeout to Gemini API
2. Opus/Discord connection dropped
3. Memory exhaustion

**Solution**:
- Increase timeout: `_MAX_SESSION_DURATION` in code
- Restart bot periodically via cron/systemd

---

## Docker Deployment

### ❌ "No module named discord" in Docker
**Solution**: Rebuild image
```bash
docker build --no-cache -t discordbot .
```

### ❌ Opus library not found in Docker
**Solution**: Update Dockerfile
```dockerfile
RUN apt-get install -y libopus0 opus-tools
```

### ❌ "Permission denied" errors in Docker
**Solution**: Run with proper capabilities
```bash
docker run --cap-add=SYS_PTRACE --security-opt apparmor=unconfined discordbot
```

---

## Testing & Debugging

### Run Unit Tests
```bash
python run_tests.py -v       # All tests
python run_tests.py --coverage   # With coverage report
```

### Enable Debug Logging
In `.env`:
```
LOG_LEVEL=DEBUG
```

### Test Bot Commands Manually
```bash
# Test in terminal
export DISCORD_TOKEN="your-token"
python bot.py
```

### Check Bot Status
In Discord:
```
!status
```

---

## Common Error Messages

| Message | Meaning | Fix |
|---------|---------|-----|
| `❌ Permission denied` | Bot role too low | Promote bot role |
| `❌ User not found` | Fuzzy matching failed | Use exact username |
| `⏳ Rate limited` | Too many commands | Wait 30 seconds |
| `⚠️ Connection Timeout` | API took too long | Retry or restart |
| `❌ Already muted` | Double-mute prevented | Already muted, skip |
| `🚫 Cannot kick bot` | Safety check | Can't moderate bots |

---

## Getting Help

1. **Check logs** for error messages
2. **Run tests**: `python run_tests.py -v`
3. **Check Discord permissions**: Server Settings > Roles
4. **Verify .env file**: All required variables set
5. **Check GitHub Issues** or open a new one

---

## Advanced Troubleshooting

### Enable Verbose Logging
```python
# In bot.py or config.py
logging.getLogger().setLevel(logging.DEBUG)
```

### Capture Full Stack Trace
```bash
python -u bot.py 2>&1 | tee bot.log
```

### Test Discord Connections
```python
# Quick test script
import discord
client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    print(f"Connected as {client.user}")
    await client.close()

client.run("YOUR_TOKEN")
```

### Monitor Resource Usage
```bash
# Linux
watch -n 1 'ps aux | grep python'

# macOS
top -p $(pgrep -f bot.py)

# Windows PowerShell
Get-Process python | Select-Object Name, CPU, Memory
```

---

**Still stuck?** Check the logs at:
- Terminal output
- `bot.log` file (if created)
- Discord error embeds

Last updated: March 2026
