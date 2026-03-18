<div align="center">

<img src="https://readme-typing-svg.herokuapp.com?font=Inter&weight=900&size=48&pause=1000&color=0066FF&center=true&vCenter=true&width=700&height=90&lines=👁+ARGUS;AI-Powered+Discord+Bot;Born+to+Moderate.+Built+to+Vibe." alt="Argus" />

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![discord.py](https://img.shields.io/badge/discord.py-2.3+-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discordpy.readthedocs.io)
[![Gemini AI](https://img.shields.io/badge/Gemini_2.0_Flash-Live_AI-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![Flask](https://img.shields.io/badge/Flask-Dashboard-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-00FF88?style=for-the-badge)](LICENSE)

<br/>

> **Argus** is a next-generation Discord bot powered by **Gemini 2.0 Flash**.  
> It listens, moderates, plays music, and tracks your server — all in real time.

<br/>

**[Chaitanyahoon](https://github.com/Chaitanyahoon)** · Built with 👁️ and Python

<br/>

</div>

---

## ✨ What Argus Does

<table>
<tr>
<td width="50%">

### 🧠 Live AI Voice
Real-time bidirectional voice conversation via Gemini 2.0 Flash Live API. Talk naturally — Argus listens, thinks, and responds in voice.

### 🛡️ AI Auto-Moderation  
Toxicity & spam detection with configurable AI thresholds. Every flagged message is logged with confidence scores.

### 🎵 Music System
YouTube & Spotify playback with loop (track/queue), shuffle, volume control, and persistent saved playlists backed by SQLite.

</td>
<td width="50%">

### 🏆 XP & Leveling
Full XP economy with level-up events, achievement unlocks, server leaderboards, and per-user profile cards.

### 📊 Web Dashboard
Premium dark glassmorphism dashboard with live data from the Flask API — overview, leaderboard, and automod settings.

### 🔊 Temp Voice Channels
Auto-create personal voice channels on join. Auto-delete when empty. Full management interface included.

</td>
</tr>
</table>

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- [FFmpeg](https://ffmpeg.org/download.html) on your `PATH`
- [Discord Bot Token](https://discord.com/developers/applications)
- [Gemini API Key](https://aistudio.google.com/app/apikey)

### 1 — Clone & Install

```bash
git clone https://github.com/Chaitanyahoon/argus.git
cd argus
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 2 — Configure `.env`

```env
# Core
DISCORD_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key
ADMIN_USER_IDS=your_discord_user_id
COMMAND_PREFIX=!
GEMINI_VOICE=Aoede

# Dashboard (optional)
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret
DASHBOARD_SECRET_KEY=change_this_to_a_random_string
```

### 3 — Run

```bash
# Bot only
python bot.py

# Bot + web dashboard API
python run_dashboard.py
```

---

## 🎮 Command Reference

### 🎵 Music
| Command | Description |
|---------|-------------|
| `!play <query>` | Play from YouTube or Spotify URL |
| `!skip` / `!s` | Skip current track |
| `!stop` | Stop & clear queue |
| `!pause` / `!resume` | Pause or resume |
| `!queue` / `!q` | View full queue with status |
| `!np` | Now playing card |
| `!loop [none\|track\|queue]` | Set loop mode |
| `!shuffle` | Toggle shuffle |
| `!volume <0–200>` | Set volume with visual bar |
| `!remove <pos>` | Remove track from queue |
| `!playlist save <name>` | 💾 Save current queue |
| `!playlist play <name>` | ▶️ Load saved playlist |
| `!playlist list` | 📋 List your playlists |
| `!playlist delete <name>` | 🗑️ Delete a playlist |

### 🎙️ AI Voice
| Command | Description |
|---------|-------------|
| `!join` | Join your voice channel |
| `!listen` | Start Gemini Live AI session |
| `!stop` | End AI voice session |
| `!leave` | Disconnect from voice |

### 🛡️ Auto-Moderation
| Command | Description |
|---------|-------------|
| `!automod toggle toxicity` | Toggle toxicity detection |
| `!automod toggle spam` | Toggle spam detection |
| `!automod threshold <0.1–1.0>` | Set AI sensitivity |
| `!automod status` | View current settings |

### 📊 Stats & Levels
| Command | Description |
|---------|-------------|
| `!level [@user]` | View XP level + progress bar |
| `!leaderboard [metric]` | Server rankings |
| `!achievements [@user]` | Unlocked achievements |
| `!stats` | Server-wide statistics |
| `!profile [@user]` | Full user profile card |

### 🔐 Permissions & Admin
| Command | Description |
|---------|-------------|
| `!autosetup` | Auto-create all Argus channels |
| `!setup` | View server configuration |
| `!status` | Bot system status |
| `!perms show` | View permission levels |
| `!setroleperm <role> <level>` | Set role permission level |
| `!trustuser / !blacklist` | Manage trusted users |

---

## 🗂️ Project Structure

```
argus/
├── bot.py                    ← Entry point & cog loader
├── config.py                 ← Env config
├── run_dashboard.py          ← Flask API launcher
├── requirements.txt
├── pyrightconfig.json        ← IDE type checking config
├── Dockerfile
│
├── cogs/                     ← Discord command modules (8 cogs)
│   ├── music.py              ← 20 music commands
│   ├── argus.py              ← AI + leveling commands
│   ├── automod.py            ← AI moderation controls
│   ├── stats.py              ← XP, profiles, leaderboard
│   ├── voice.py              ← AI voice interaction
│   ├── temp_voice.py         ← Temporary voice channels
│   ├── permissions.py        ← Role-based access control
│   └── admin.py              ← Bot administration
│
├── core/                     ← Backend systems
│   ├── embeds.py             ← 🎨 Shared embed design system
│   ├── music_player.py       ← MusicPlayer / MusicManager
│   ├── argus_systems.py      ← ArgusManager + AI analysis
│   ├── database.py           ← SQLite data layer
│   ├── live_session.py       ← Gemini Live API connection
│   ├── leaderboard.py        ← XP & ranking logic
│   ├── achievements.py       ← Achievement engine
│   ├── permissions.py        ← Permission system
│   └── enhanced_logging.py   ← Structured logging + metrics
│
├── dashboard/                ← Web admin dashboard
│   ├── index.html            ← Overview page
│   ├── leaderboard.html      ← Rankings + podium
│   ├── automod.html          ← AI moderation settings
│   ├── css/style.css         ← Glassmorphism design system
│   ├── js/dashboard.js       ← Live API fetch + fallback
│   └── api/                  ← Flask REST API
│       ├── app.py            ← Flask entry point (CORS)
│       ├── routes.py         ← 12 REST endpoints
│       ├── auth.py           ← Discord OAuth2
│       └── db.py             ← SQLite query layer
│
└── data/
    └── argus.db              ← SQLite database
```

---

## 🤖 AI Architecture

```
User speaks in voice channel
        │
        ▼
discord-ext-voice-recv  ──►  faster-whisper  (Speech → Text)
                                    │
                                    ▼
                        Gemini 2.0 Flash Live API
                         ┌──────────────────────┐
                         │  Conversation Memory  │
                         │  Content Moderation   │
                         │  Intent Detection     │
                         │  Tool Calling         │
                         └──────────────────────┘
                                    │
                                    ▼
                     Text Response  +  TTS Voice Output
                                    │
                                    ▼
                        Played back to voice channel
```

---

## 🌐 Web Dashboard

Start the Flask API, then open the dashboard in your browser:

```bash
python run_dashboard.py
# → http://localhost:5000
```

| Page | What it shows |
|------|---------------|
| **Overview** | Live stat cards, activity feed, server health metrics |
| **Leaderboard** | Gold/silver/bronze podium, full ranked table, personal stats |
| **Auto-Mod** | AI settings, sensitivity slider, real-time action log |

> Dashboard works offline too — falls back to mock data if the API isn't running.

---

## 🐳 Docker

```bash
docker build -t argus-bot .
docker run --env-file .env argus-bot
```

---

## 📜 License

MIT © [Chaitanyahoon](https://github.com/Chaitanyahoon)

---

<div align="center">

*Star ⭐ if Argus is useful — it means a lot!*

</div>
