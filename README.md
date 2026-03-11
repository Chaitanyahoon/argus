# 🎙️ Voice-Controlled Discord Moderation Bot

A Discord bot that listens to your voice in a voice channel and executes moderation commands — **kick, ban, mute, unmute, create/delete voice channels** — all hands-free using speech recognition.

## How It Works

1. Bot joins your voice channel
2. You say the **wake word** (default: `"hey bot"`) followed by a command
3. Your speech is transcribed locally using **OpenAI Whisper** (via `faster-whisper`)
4. The bot parses the command and executes it

**Example**: *"Hey bot, kick John"* → kicks the user named John from the server.

## Supported Voice Commands

| Say this | Action |
|---|---|
| `"hey bot, kick [name]"` | Kicks a member |
| `"hey bot, ban [name]"` | Bans a member |
| `"hey bot, mute [name]"` | Server-mutes a member |
| `"hey bot, unmute [name]"` | Unmutes a member |
| `"hey bot, create channel [name]"` | Creates a new voice channel |
| `"hey bot, delete channel [name]"` | Deletes a voice channel |

> You can also say natural variants like *"remove"* instead of *"kick"*, or *"create a vc"* instead of *"create channel"*.

## Setup

### 1. Prerequisites

```bash
# macOS
brew install ffmpeg opus

# Python 3.11+
python3 --version
```

### 2. Create the Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a **New Application** → go to **Bot** tab
3. Enable these **Privileged Gateway Intents**:
   - ✅ Message Content Intent
   - ✅ Server Members Intent
   - ✅ Presence Intent
4. Copy the **Bot Token**
5. Go to **OAuth2 → URL Generator**:
   - Scopes: `bot`
   - Permissions: `Administrator` (or individually: Kick Members, Ban Members, Manage Channels, Connect, Speak)
6. Use the generated URL to invite the bot to your server

### 3. Install & Configure

```bash
cd discord_ai_bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# Uses discord.py with voice + discord-ext-voice-recv for two-way voice (hear + speak).
# discord.py has DAVE support in core; no patch required.

# Configure
cp .env.example .env
# Edit .env with your bot token and admin user IDs
```

To find your Discord User ID: Enable Developer Mode in Discord settings → right-click your name → Copy User ID.

### 4. Run

```bash
python bot.py
```

## Text Commands

| Command | Description |
|---|---|
| `!join` | Bot joins your voice channel |
| `!leave` | Bot leaves the voice channel |
| `!listen` | Start listening for voice commands |
| `!stop` | Stop listening |
| `!status` | Show bot status |

## Configuration (.env)

| Variable | Description | Default |
|---|---|---|
| `DISCORD_TOKEN` | Your bot token | *required* |
| `ADMIN_USER_IDS` | Comma-separated user IDs allowed to use voice commands | *required* |
| `WAKE_WORD` | Phrase to trigger a command | `hey bot` |
| `WHISPER_MODEL` | Whisper model size (`tiny.en`, `base.en`, `small.en`, etc.) | `base.en` |
| `COMMAND_PREFIX` | Prefix for text commands | `!` |

## Project Structure

├── bot.py              # Main entry point & text commands
├── config.py           # Configuration loader
├── core/               # System logic package
│   ├── argus_systems.py  # Sentient AI logic
│   ├── voice_listener.py # Voice pipeline
│   ├── live_session.py   # Gemini Live manager
│   ├── temp_voice.py     # Channel management
│   ├── music_player.py   # Audio playback
│   └── audio_utils.py    # Audio processing
├── data/               # Persistent JSON databases
├── requirements.txt    # Python dependencies
└── .env.example        # Configuration template

## Security

- Only users listed in `ADMIN_USER_IDS` can trigger voice commands
- All executed commands are logged in the text channel with rich embeds
- Speech recognition runs **100% locally** (or via Gemini Live API) — no audio leaves your machine except to Google's API.

## ☁️ Deployment (Recommended for Low Latency)

For the best voice response speed, deploy this bot to a cloud server (VPS) close to your Discord voice region.

### Docker (Simplest)

1.  **Build the image:**
    ```bash
    docker build -t discord-gemini-bot .
    ```

2.  **Run the container:**
    ```bash
    docker run -d \
      --env-file .env \
      --restart unless-stopped \
      discord-gemini-bot
    ```

### Recommended Hosts
*   **Railway / Fly.io / Heroku:** Great for easy deployment.
*   **DigitalOcean / AWS / Google Cloud:** Use a small VPS (Ubuntu) for maximum control and lowest latency.

