# 🌿 Argus Development Guide

**Project Type:** Discord Bot | **Language:** Python | **Framework:** discord.py + Gemini AI

## ✅ Setup Checklist

- [x] Project scaffolded with voice AI and therapy features only
- [x] Dependencies configured via pip
- [x] No compilation needed (Python project)
- [x] Bot launches with `python bot.py`
- [x] Documentation updated

---

## 🚀 Launch Commands

```bash
# Activate virtual environment
.venv\Scripts\activate

# Run the bot
python bot.py

# Bot connects to Discord and Gemini Live API via .env credentials
```

---

## 📦 Core Features

### 💚 Wellness & Therapy
- Mood check-ins (`!checkin`)
- Mood history tracking (`!moodlog`)
- Journal entries (`!journal`)
- Crisis detection and support resources

### 🎤 Voice AI
- Real-time voice conversations with Gemini 2.5 Flash
- Natural bidirectional streaming
- Voice channel management via AI

---

## 🏗️ Repository Structure

```
argus/
├── bot.py                  # Main entry point
├── config.py               # .env configuration
├── cogs/
│   ├── therapy.py          # Wellness features
│   └── voice.py            # Voice AI interface
├── core/
│   ├── voice_listener.py   # Audio pipeline
│   ├── live_session.py     # Gemini connection
│   ├── database.py         # SQLite storage
│   └── audio_utils.py      # Audio processing
└── requirements.txt
```

---

## 💡 Development Notes

- **Python Version:** 3.11+
- **Package Manager:** pip
- **Database:** SQLite (in data/ folder)
- **API:** Gemini 2.5 Flash Live with bidirectional voice
- **No Tests:** Removed testing infrastructure for production focus

---

## 📝 Code Style

- Follow PEP 8
- Add docstrings to functions
- Type hints encouraged
- Max line length: 100 characters

---

## 🔄 Contributing

1. Create feature branch: `git checkout -b feature/name`
2. Make changes and commit: `git commit -m "feat: description"`
3. Push and create pull request
4. See [CONTRIBUTING.md](../CONTRIBUTING.md) for details

---

## 📚 Resources

- [Discord.py Documentation](https://discordpy.readthedocs.io)
- [Gemini API Guide](https://ai.google.dev)
- [FFmpeg Setup](https://ffmpeg.org/download.html)

---

Last Updated: 2026-05-08 | Status: Production Ready ✨
- If any of the scaffolding commands mention that the folder name is not correct, let the user know to create a new folder with the correct name and then reopen it again in vscode.

EXTENSION INSTALLATION RULES:
- Only install extension specified by the get_project_setup_info tool. DO NOT INSTALL any other extensions.

PROJECT CONTENT RULES:
- If the user has not specified project details, assume they want a "Hello World" project as a starting point.
- Avoid adding links of any type (URLs, files, folders, etc.) or integrations that are not explicitly required.
- Avoid generating images, videos, or any other media files unless explicitly requested.
- If you need to use any media assets as placeholders, let the user know that these are placeholders and should be replaced with the actual assets later.
- Ensure all generated components serve a clear purpose within the user's requested workflow.
- If a feature is assumed but not confirmed, prompt the user for clarification before including it.
- If you are working on a VS Code extension, use the VS Code API tool with a query to find relevant VS Code API references and samples related to that query.

TASK COMPLETION RULES:
- Your task is complete when:
  - Project is successfully scaffolded and compiled without errors
  - copilot-instructions.md file in the .github directory exists in the project
  - README.md file exists and is up to date
  - User is provided with clear instructions to debug/launch the project

- Work through each checklist item systematically.
- Keep communication concise and focused.
- Follow development best practices.
