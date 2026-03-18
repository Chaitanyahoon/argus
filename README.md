<div align="center">

<img src="https://readme-typing-svg.herokuapp.com?font=Inter&weight=800&size=40&pause=1000&color=0066FF&center=true&vCenter=true&width=600&height=80&lines=👁+ARGUS;AI-Powered+Discord+Bot" alt="Argus" />

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Discord.py](https://img.shields.io/badge/discord.py-2.3+-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discordpy.readthedocs.io)
[![Gemini AI](https://img.shields.io/badge/Gemini_2.0_Flash-AI_Core-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-00d4ff?style=for-the-badge)](LICENSE)

<br/>

> **Argus** is an AI-powered Discord bot with real-time voice conversation, AI moderation,  
> music playback, server analytics, and a web dashboard — all in one.

<br/>

**Built & maintained by [Chaitanyahoon](https://github.com/Chaitanyahoon)**

<br/>

---

</div>

## ✨ Features

| Category | Feature | Status |
|----------|---------|--------|
| 🧠 **AI Voice** | Real-time bidirectional voice chat via Gemini 2.0 Flash Live API | ✅ Live |
| 🛡️ **Auto-Mod** | AI toxicity & spam detection with configurable thresholds | ✅ Live |
| 🎵 **Music** | YouTube & Spotify playback with queue, skip, volume | ✅ Live |
| 🏆 **Leveling** | XP, level-up system, leaderboard, achievements | ✅ Live |
| 📊 **Dashboard** | Premium web UI for server stats & admin settings | ✅ Live |
| 🔊 **Temp Voice** | Auto-create/delete temporary voice channels | ✅ Live |
| 🔐 **Permissions** | Role-based command access control | ✅ Live |
| 📈 **Analytics** | Server health, user stats, voice session tracking | ✅ Live |

---

## 🚀 Quick Start

### Prerequisites

- Python **3.11+**
- [FFmpeg](https://ffmpeg.org/download.html) installed and on `PATH`
- A [Discord Bot Token](https://discord.com/developers/applications)
- A [Gemini API Key](https://aistudio.google.com/app/apikey)

### 1 — Clone & Install

```bash
git clone https://github.com/Chaitanyahoon/argus.git
cd argus
pip install -r requirements.txt
```

### 2 — Configure `.env`

```env
DISCORD_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key
ADMIN_USER_IDS=your_discord_user_id
COMMAND_PREFIX=!
GEMINI_VOICE=Aoede
```

### 3 — Run

```bash
python bot.py
```

---

## 🗂️ Project Structure

```
argus/
├── bot.py                  ← Entry point & event lifecycle
├── config.py               ← Environment & settings loader
├── logger.py               ← Structured logging
├── requirements.txt
├── Dockerfile
│
├── cogs/                   ← Discord command modules
│   ├── argus.py            ← AI voice commands (!join, !listen, !stop)
│   ├── automod.py          ← AI moderation (!automod toggle/threshold)
│   ├── music.py            ← Music commands (!play, !skip, !queue)
│   ├── stats.py            ← XP, leaderboard, achievements
│   ├── temp_voice.py       ← Temporary voice channels
│   ├── voice.py            ← Voice utilities
│   ├── permissions.py      ← Permission management
│   └── admin.py            ← Admin commands
│
├── core/                   ← Backend systems
│   ├── argus_systems.py    ← ArgusManager, AI analysis
│   ├── database.py         ← SQLite data layer
│   ├── live_session.py     ← Gemini Live API session
│   ├── music_player.py     ← MusicPlayer / MusicManager
│   ├── leaderboard.py      ← XP & ranking logic
│   ├── achievements.py     ← Achievement engine
│   └── ...                 ← 20 more modules
│
├── dashboard/              ← Web admin dashboard
│   ├── index.html          ← Overview
│   ├── leaderboard.html    ← Rankings
│   ├── automod.html        ← AI moderation settings
│   ├── css/style.css       ← Shared design system
│   └── js/dashboard.js     ← Data & interactivity
│
└── data/
    └── argus.db            ← SQLite database
```

---

## 🎮 Commands

### 🎙️ Voice & AI
| Command | Description |
|---------|-------------|
| `!join` | Join your voice channel |
| `!listen` | Start AI voice session (Gemini Live) |
| `!stop` | End AI session |
| `!leave` | Disconnect from voice |

### 🎵 Music
| Command | Description |
|---------|-------------|
| `!play <query>` | Play from YouTube or Spotify |
| `!skip` | Skip current track |
| `!stop` | Stop & clear queue |
| `!queue` | Show music queue |
| `!np` | Show currently playing |

### 🛡️ Auto-Moderation
| Command | Description |
|---------|-------------|
| `!automod toggle` | Enable/disable AI moderation |
| `!automod threshold <0.1–1.0>` | Set toxicity sensitivity |

### 📊 Stats & Levels
| Command | Description |
|---------|-------------|
| `!rank` | View your XP & level |
| `!leaderboard` | Top members |
| `!achievements` | Your unlocked achievements |

---

## 🌐 Web Dashboard

Open `dashboard/index.html` directly in your browser — no server required.

| Page | Description |
|------|-------------|
| **Overview** | Live stat cards, activity feed, server health |
| **Leaderboard** | Gold/silver/bronze podium, ranked table, personal stats |
| **Auto-Mod** | AI settings, sensitivity slider, action log |

---

## 🤖 AI Architecture

```
User Voice Input
      │
      ▼
discord-ext-voice-recv  ──►  faster-whisper (STT)
                                    │
                                    ▼
                          Gemini 2.0 Flash (Live API)
                           - Conversation context
                           - Content moderation
                           - Intent detection
                                    │
                                    ▼
                     Text Response + Voice Output (TTS)
```

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

*Star ⭐ this repo if Argus is useful to you!*

</div>
