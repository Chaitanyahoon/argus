<div align="center">

<img src="https://readme-typing-svg.herokuapp.com?font=Inter&weight=900&size=48&pause=1000&color=22C55E&center=true&vCenter=true&width=700&height=90&lines=🌿+PLANTHESIA;Server+Helper+Bot;Grow+Your+Community." alt="Planthesia" />

<br/>

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![discord.py](https://img.shields.io/badge/discord.py-2.7+-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discordpy.readthedocs.io)
[![Gemini AI](https://img.shields.io/badge/Gemini_2.5_Flash-Live_Voice-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

<br/>

> **Planthesia** is a friendly, helpful Discord bot designed to grow your community.  
> Share server info and enjoy voice conversations.

<br/>

**By [Chaitanyahoon](https://github.com/Chaitanyahoon)** · Built with 🌿 and Python

<br/>

</div>

---

## 🌿 What Planthesia Does

<table>
<tr>
<td width="50%">

### � Wellness & Therapy
Guided mood check-ins, wellness tracking, and crisis support resources. A supportive companion for mental health awareness.

</td>
<td width="50%">

### 🎤 Voice AI Conversations
Real-time voice chat powered by Gemini 2.5 Flash. Talk naturally in voice channels — the bot listens and responds naturally.

</td>
</tr>
</table>

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.13+**
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
COMMAND_PREFIX=>>
GEMINI_VOICE=Aoede

# Optional settings
LOG_LEVEL=INFO
WHISPER_MODEL=base.en
```

### 3 — Run

```bash
# Start the bot
python bot.py
```

---

## 🎮 Command Reference

### � Wellness
| Command | Description |
|---------|-------------|
| `!checkin` | Guided mood check-in |
| `!moodlog` | View your mood history |
| `!journal` | Write a journal entry |
| `!wellness` | Wellness dashboard |

### 🎙️ AI Voice
| Command | Description |
|---------|-------------|
| `!join` | Join your voice channel |
| `!listen` | Start Gemini Live AI session |
| `!stop` | End AI voice session |
| `!leave` | Disconnect from voice |

---

## 🗂️ Project Structure

```
discordbot/
├── bot.py                    ← Entry point & cog loader
├── config.py                 ← Env config
├── requirements.txt
├── pyrightconfig.json        ← IDE type checking config
├── cogs/
│   ├── therapy.py            ← Wellness features
│   └── voice.py              ← Voice AI commands
└── core/
    ├── audio_utils.py        ← Audio processing
    ├── bot_utils.py          ← Shared utilities
    ├── database.py           ← SQLite database
    ├── embeds.py             ← Discord embed helpers
    ├── live_session.py       ← Gemini Live API
    ├── therapy.py            ← Wellness manager
    ├── transcriber.py        ← Speech-to-text
    ├── voice_*.py            ← Voice processing modules
    └── ...
```
├── Dockerfile
│
├── cogs/                     ← Discord command modules (core)
│   ├── argus.py              ← AI + leveling commands
│   ├── automod.py            ← AI moderation controls
│   ├── stats.py              ← XP, profiles, leaderboard
│   ├── voice.py              ← AI voice interaction
│   ├── permissions.py        ← Role-based access control
│   └── admin.py              ← Bot administration
│
├── core/                     ← Backend systems
│   ├── embeds.py             ← 🎨 Shared embed design system
│   ├── argus_systems.py      ← ArgusManager + AI analysis
│   ├── database.py           ← SQLite data layer
│   ├── live_session.py       ← Gemini Live API connection
│   ├── leaderboard.py        ← XP & ranking logic
│   ├── achievements.py       ← Achievement engine
│   ├── permissions.py        ← Permission system
│   └── enhanced_logging.py   ← Structured logging + metrics
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
