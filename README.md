# 🌿 Argus - Voice AI & Therapy Bot

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![discord.py](https://img.shields.io/badge/discord.py-2.7+-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discordpy.readthedocs.io)
[![Gemini AI](https://img.shields.io/badge/Gemini_2.5_Flash-Live_Voice-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

**Argus** is an AI-powered Discord bot focused on voice conversations and wellness support. A thoughtful companion that listens, responds, and helps with mental health awareness.

## 🌿 Features

### 💚 Wellness & Therapy
- Guided mood check-ins with emoji reactions
- Personal mood tracking and history
- Journal entry system
- Crisis detection and support resources

### 🎤 Voice AI Conversations
- Real-time bidirectional voice chat with Gemini 2.5 Flash
- Natural conversation with AI-powered voice listening
- Simple join/listen/stop voice controls
- Intelligent responses that support emotional wellbeing

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **FFmpeg** installed and available on your `PATH`
- **Discord Bot Token**
- **Gemini API Key**

### Installation

```bash
git clone https://github.com/Chaitanyahoon/argus.git
cd argus
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

### Configuration

```bash
copy .env.example .env
# Edit .env with your tokens and keys
```

### Run

```bash
python bot.py
```

## 🎮 Commands

### 💚 Wellness
| Command | Description |
|---------|-------------|
| `!checkin` | Guided mood check-in |
| `!journal` | Write a journal entry |
| `!breathe` | Guided breathing exercise |
| `!ground` | 5-4-3-2-1 grounding technique |
| `!moodstats` | View wellness overview |

### 🎙️ Voice AI
| Command | Description |
|---------|-------------|
| `!join` | Join your current voice channel |
| `!listen` | Start the AI voice listener |
| `!stop` | Stop the voice listener |
| `!leave` | Disconnect from voice |

## 🗂️ Project Structure

```
argus/
├── bot.py                    ← Main bot file
├── config.py                 ← Configuration
├── cogs/
│   ├── therapy.py            ← Wellness features
│   └── voice.py              ← Voice AI commands
├── core/
│   ├── audio_utils.py        ← Audio processing
│   ├── database.py           ← SQLite database
│   ├── live_session.py       ← Gemini Live API
│   └── voice_listener.py     ← Voice pipeline
└── requirements.txt
```

## 🐳 Docker

```bash
docker build -t argus-bot .
docker run --env-file .env argus-bot
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.