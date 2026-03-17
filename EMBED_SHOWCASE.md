# 👁️ Argus Bot - Embed Messages Showcase

Visual guide to all Discord embed messages the bot displays.

---

## 🎤 Voice Commands

### Join Voice Channel - Success
```
╔════════════════════════════════════════════════════════════════╗
║ ✅ Joined Voice Channel                                        ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Connected to **General**                                       ║
║                                                                ║
║ Use `!listen` to start the AI.                                ║
║                                                                ║
║ [Green embed - discord.Color.green()]                         ║
╚════════════════════════════════════════════════════════════════╝
```

### Join Voice Channel - Already Connected Error
```
╔════════════════════════════════════════════════════════════════╗
║ ❌ Already Connected                                           ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ I'm already in a voice channel.                               ║
║                                                                ║
║ [Red embed - discord.Color.red()]                             ║
╚════════════════════════════════════════════════════════════════╝
```

### Join Voice Channel - Connection Failed
```
╔════════════════════════════════════════════════════════════════╗
║ ❌ Connection Failed                                           ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ [Error details in code block]                                 ║
║                                                                ║
║ [Red embed - discord.Color.red()]                             ║
╚════════════════════════════════════════════════════════════════╝
```

### Leave Voice Channel
```
╔════════════════════════════════════════════════════════════════╗
║ 👋 Left Voice Channel                                          ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Disconnected from the voice channel.                          ║
║                                                                ║
║ [Green embed - discord.Color.green()]                         ║
╚════════════════════════════════════════════════════════════════╝
```

### Listen - Not in Voice Channel
```
╔════════════════════════════════════════════════════════════════╗
║ ❌ Not Connected to Voice                                      ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Use `!join` first to connect me to your voice channel.        ║
║                                                                ║
║ [Red embed - discord.Color.red()]                             ║
╚════════════════════════════════════════════════════════════════╝
```

### Listen - Rate Limited
```
╔════════════════════════════════════════════════════════════════╗
║ ⏳ Rate Limited                                                 ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Too many voice commands. Wait 15s before trying again.        ║
║                                                                ║
║ [Orange embed - discord.Color.orange()]                       ║
╚════════════════════════════════════════════════════════════════╝
```

### Listen - Active Conversation Started
```
╔════════════════════════════════════════════════════════════════╗
║ 🎙️ AI Voice Conversation Active                               ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ **Real-time voice conversation**                              ║
║                                                                ║
║ 🗣️ **Just talk naturally** — I'll respond by speaking back!   ║
║                                                                ║
║ **I can also moderate:**                                       ║
║ • *"kick john"*  •  *"mute someone"*                          ║
║ • *"create channel gaming"*                                   ║
║                                                                ║
║ 🔊 Voice: **Phoebe** • 🌐 Any language                        ║
║                                                                ║
║ [Green embed - discord.Color.green()]                         ║
╚════════════════════════════════════════════════════════════════╝
```

### Stop Listening
```
╔════════════════════════════════════════════════════════════════╗
║ 🔇 Listening Stopped                                           ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Gemini Live session closed.                                   ║
║                                                                ║
║ [Green embed - discord.Color.green()]                         ║
╚════════════════════════════════════════════════════════════════╝
```

---

## 🎵 Music Commands

### Play - Missing Query
```
╔════════════════════════════════════════════════════════════════╗
║ ❌ Missing Query                                               ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Use `!play <URL or search terms>`                             ║
║                                                                ║
║ *Example: `!play never gonna give you up`*                    ║
║                                                                ║
║ [Red embed - discord.Color.red()]                             ║
╚════════════════════════════════════════════════════════════════╝
```

### Play - Success (Single Track)
```
╔════════════════════════════════════════════════════════════════╗
║ ▶️ Now playing: Rick Astley - Never Gonna Give You Up        ║
╚════════════════════════════════════════════════════════════════╝
```

### Play - Success (Multiple Tracks)
```
╔════════════════════════════════════════════════════════════════╗
║ ▶️ Now playing: Track 1                                        ║
║ ✅ Added **5** more track(s) to the queue.                     ║
╚════════════════════════════════════════════════════════════════╝
```

### Skip
```
╔════════════════════════════════════════════════════════════════╗
║ ⏭️ Skipped                                                      ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Skipped to the next track.                                    ║
║                                                                ║
║ [Green embed - discord.Color.green()]                         ║
╚════════════════════════════════════════════════════════════════╝
```

### Stop Music
```
╔════════════════════════════════════════════════════════════════╗
║ ⏹️ Stopped                                                      ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Playback stopped and queue cleared.                           ║
║                                                                ║
║ [Green embed - discord.Color.green()]                         ║
╚════════════════════════════════════════════════════════════════╝
```

### Music Queue
```
╔════════════════════════════════════════════════════════════════╗
║ Music Queue                                                    ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ **Now playing:** Song Title (requested by Username)           ║
║                                                                ║
║ 1. Next Song 1 (requested by Username)                        ║
║ 2. Next Song 2 (requested by Username)                        ║
║ 3. Next Song 3 (requested by Username)                        ║
║ … and 5 more                                                  ║
║                                                                ║
║ [Blue embed - discord.Color.blue()]                           ║
╚════════════════════════════════════════════════════════════════╝
```

### Now Playing
```
╔════════════════════════════════════════════════════════════════╗
║ ▶️ Now Playing                                                  ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ **Song Title** (120s)                                          ║
║                                                                ║
║ *Requested by Username*                                       ║
║                                                                ║
║ [Green embed - discord.Color.green()]                         ║
╚════════════════════════════════════════════════════════════════╝
```

### Nothing Playing
```
╔════════════════════════════════════════════════════════════════╗
║ 🔇 Nothing Playing                                             ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ No track is currently playing.                                ║
║                                                                ║
║ [Grey embed - discord.Color.greyple()]                        ║
╚════════════════════════════════════════════════════════════════╝
```

---

## ⚙️ Admin & Setup Commands

### Set Create Channel
```
╔════════════════════════════════════════════════════════════════╗
║ ✅ Create VC Channel Set                                       ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Join **#create-vc** to create a temporary voice channel.     ║
║                                                                ║
║ [Green embed - discord.Color.green()]                         ║
╚════════════════════════════════════════════════════════════════╝
```

### Set TempVC Category
```
╔════════════════════════════════════════════════════════════════╗
║ ✅ Temp VC Category Set                                        ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ New temporary voice channels will be created in **Gaming**.    ║
║                                                                ║
║ [Green embed - discord.Color.green()]                         ║
╚════════════════════════════════════════════════════════════════╝
```

### Set Interface Channel
```
╔════════════════════════════════════════════════════════════════╗
║ ✅ Interface Channel Set                                       ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Temp VC interface will be posted in #vc-management.           ║
║                                                                ║
║ Run `!postvcinterface` to post the interface.                 ║
║                                                                ║
║ [Green embed - discord.Color.green()]                         ║
╚════════════════════════════════════════════════════════════════╝
```

### Post VC Interface Confirmation
```
╔════════════════════════════════════════════════════════════════╗
║ ✅ Interface Posted                                            ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Everyone uses this message; clicks affect only their own VC. ║
║                                                                ║
║ [Green embed - discord.Color.green()]                         ║
╚════════════════════════════════════════════════════════════════╝
```

### Nexus Setup (Logging Channel)
```
╔════════════════════════════════════════════════════════════════╗
║ 👁️ Nexus Logger Initialized                                   ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Surveillance logs will be routed to #nexus-logs.              ║
║                                                                ║
║ [Green embed - discord.Color.green()]                         ║
╚════════════════════════════════════════════════════════════════╝
```

### Auto Setup Started
```
╔════════════════════════════════════════════════════════════════╗
║ ⚙️ Initializing Fast Setup                                     ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Creating categories and channels...                           ║
║                                                                ║
║ [Blue embed - discord.Color.blue()]                           ║
╚════════════════════════════════════════════════════════════════╝
```

### Auto Setup Complete
```
╔════════════════════════════════════════════════════════════════╗
║ ✅ Setup Complete!                                             ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ - **Category:** #➕-Argus-Systems                             ║
║ - **Trigger:** #➕-Create-VC                                  ║
║ - **Logs:** #👁️-nexus-logs                                   ║
║ - **Interface:** #🎮-vc-management                            ║
║                                                                ║
║ Everything is pre-configured. Join #➕-Create-VC to start!   ║
║                                                                ║
║ [Green embed - discord.Color.green()]                         ║
╚════════════════════════════════════════════════════════════════╝
```

### Auto Setup - Permission Error
```
╔════════════════════════════════════════════════════════════════╗
║ ❌ Permission Error                                            ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ I don't have permission to create channels/categories.        ║
║                                                                ║
║ [Red embed - discord.Color.red()]                             ║
╚════════════════════════════════════════════════════════════════╝
```

### Set Prefix
```
╔════════════════════════════════════════════════════════════════╗
║ ✅ Command Prefix Updated                                      ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ New prefix: `?`                                               ║
║                                                                ║
║ [Green embed - discord.Color.green()]                         ║
╚════════════════════════════════════════════════════════════════╝
```

### Set Activity
```
╔════════════════════════════════════════════════════════════════╗
║ ✅ Activity Updated                                            ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ **listening the evolution...**                                ║
║                                                                ║
║ [Green embed - discord.Color.green()]                         ║
╚════════════════════════════════════════════════════════════════╝
```

---

## ℹ️ Info & Status Commands

### Server Configuration/Setup Status
```
╔════════════════════════════════════════════════════════════════╗
║ 👁️ Argus System Configuration                                 ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Current configuration for **Discord Server**                  ║
║ Use `!autosetup` to automate this.                            ║
║                                                                ║
║ Prefix | ✅ !                                                  ║
║ Awakening Stage | 📡 Stage 3                                  ║
║ Mood Mode | 🎭 NORMAL                                         ║
║                                                                ║
║ Nexus Logging | ✅ #👁️-nexus-logs                            ║
║ TempVoice Trigger | ✅ #➕-Create-VC                          ║
║ TempVoice Category | ✅ #Argus-Systems                        ║
║ Interface Channel | ✅ #🎮-vc-management                      ║
║                                                                ║
║ [Blue embed - 0x3498db]                                        ║
╚════════════════════════════════════════════════════════════════╝
```

### User Level
```
╔════════════════════════════════════════════════════════════════╗
║ Evolutionary Profile: Username                                 ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ **Level:** 8                                                   ║
║ **XP:** 4250 / 5000                                            ║
║ **Status:** Integrated                                         ║
║                                                                ║
║ [Thumbnail: User avatar]                                       ║
║ [Ethereal color embed]                                         ║
╚════════════════════════════════════════════════════════════════╝
```

### User Level - No Data
```
╔════════════════════════════════════════════════════════════════╗
║ ℹ️ No Data Available                                           ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ I have no data on that user yet. Interact more to begin       ║
║ evolution.                                                     ║
║                                                                ║
║ [Grey embed - discord.Color.greyple()]                        ║
╚════════════════════════════════════════════════════════════════╝
```

### System Status
```
╔════════════════════════════════════════════════════════════════╗
║ 👁️ Argus System Status                                        ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Voice Channel | Connected                                      ║
║ Listening | Active                                             ║
║ Live API | Connected                                           ║
║                                                                ║
║ Awakening | Stage 2 (FOCUSED)                                 ║
║ Nexus Logger | Operational                                     ║
║ Leveling | Active                                              ║
║                                                                ║
║ AI Engine | Gemini 2.5 Flash Native (Sentient)               ║
║ Voice | Phoebe                                                 ║
║ TempVoice | Enabled                                            ║
║                                                                ║
║ Footer: Argus V2 • Surveillance & Evolution Integration       ║
║                                                                ║
║ [Blue embed - discord.Color.blue()]                           ║
╚════════════════════════════════════════════════════════════════╝
```

---

## 📖 Help Command

### Main Help (All Commands)
```
╔════════════════════════════════════════════════════════════════╗
║ 👁️ Argus Commands                                              ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ AI-Powered Discord Moderation Bot                              ║
║                                                                ║
║ Use `!help <command>` for detailed info on a command.         ║
║                                                                ║
║ 🎤 Voice Commands                                              ║
║ ─────────────────────────────────────────────────────────────  ║
║ `!join` — Join the voice channel you are in.                  ║
║ `!leave` — Bot leaves the voice channel.                      ║
║ `!listen` — Start listening for voice commands.               ║
║ `!stop` — Stop listening for voice commands.                  ║
║                                                                ║
║ 🎵 Music Commands                                              ║
║ ─────────────────────────────────────────────────────────────  ║
║ `!play` — Play a track from URL or search query.              ║
║ `!skip` — Skip the current track.                             ║
║ `!stopmusic` — Stop playback and clear queue.                 ║
║ `!queue` — Show current track and queue.                      ║
║ `!nowplaying` — Show the current track.                       ║
║                                                                ║
║ ⚙️ Admin Commands                                              ║
║ ─────────────────────────────────────────────────────────────  ║
║ `!setcreatechannel` — Set the trigger channel for TempVC.     ║
║ `!settempvcategory` — Set category for temp channels.         ║
║ `!setinterfacechannel` — Set the management channel.          ║
║ `!postvcinterface` — Post the shared TempVoice interface.     ║
║ `!nexus_setup` — Set the logging channel.                     ║
║ `!autosetup` — Auto-create all necessary channels.            ║
║ `!setprefix` — Set the command prefix.                        ║
║ `!setactivity` — Set the bot's status/activity.               ║
║                                                                ║
║ ℹ️ Info Commands                                               ║
║ ─────────────────────────────────────────────────────────────  ║
║ `!level` — Check your current evolutionary level.             ║
║ `!setup` — Show server configuration and setup status.        ║
║ `!status` — Show bot status.                                  ║
║                                                                ║
║ Footer: Prefix: ! | Total Commands: 30                        ║
║ Thumbnail: Bot avatar                                          ║
║                                                                ║
║ [Purple embed - discord.Color.purple()]                       ║
╚════════════════════════════════════════════════════════════════╝
```

### Help for Specific Command
```
╔════════════════════════════════════════════════════════════════╗
║ 📖 Help: !join                                                 ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Join the voice channel you are in.                            ║
║                                                                ║
║ Footer: Use !help to see all commands                          ║
║                                                                ║
║ [Blue embed - discord.Color.blue()]                           ║
╚════════════════════════════════════════════════════════════════╝
```

### Command Not Found
```
╔════════════════════════════════════════════════════════════════╗
║ ❌ Command Not Found                                           ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ The command `fakecmd` does not exist.                         ║
║                                                                ║
║ [Red embed - discord.Color.red()]                             ║
╚════════════════════════════════════════════════════════════════╝
```

---

## ⚠️ Error Handling

### Command Cooldown
```
╔════════════════════════════════════════════════════════════════╗
║ ⏳ Sector Cooldown Active                                      ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Recalibrating neural buffers... Please wait **3.5s** before   ║
║ re-entering this command.                                      ║
║                                                                ║
║ [Orange embed - discord.Color.orange()]                       ║
║ Deleted after 10 seconds                                       ║
╚════════════════════════════════════════════════════════════════╝
```

### Permission Denied
```
╔════════════════════════════════════════════════════════════════╗
║ 🚫 Permission Denied                                           ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ You don't have permission to execute this command.            ║
║                                                                ║
║ [Red embed - discord.Color.red()]                             ║
║ Deleted after 10 seconds                                       ║
╚════════════════════════════════════════════════════════════════╝
```

### Missing Required Argument
```
╔════════════════════════════════════════════════════════════════╗
║ ❌ Missing Argument                                            ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ **Parameter:** `query`                                         ║
║                                                                ║
║ Use `!help play` for more info.                               ║
║                                                                ║
║ [Red embed - discord.Color.red()]                             ║
║ Deleted after 15 seconds                                       ║
╚════════════════════════════════════════════════════════════════╝
```

### Invalid Prefix
```
╔════════════════════════════════════════════════════════════════╗
║ ❌ Invalid Prefix                                              ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Prefix must be 1-3 characters and contain no spaces.          ║
║                                                                ║
║ [Red embed - discord.Color.red()]                             ║
╚════════════════════════════════════════════════════════════════╝
```

### System Exception
```
╔════════════════════════════════════════════════════════════════╗
║ ⚠️ System Exception                                            ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ [Error details in code block]                                 ║
║                                                                ║
║ [Red embed - discord.Color.red()]                             ║
║ Deleted after 10 seconds                                       ║
╚════════════════════════════════════════════════════════════════╝
```

---

## 🎨 Color Scheme Reference

| Purpose | Color | Emoji |
|---------|-------|-------|
| **Success** | 🟢 Green | ✅ |
| **Error** | 🔴 Red | ❌ |
| **Warning** | 🟠 Orange | ⚠️ |
| **Info** | 🔵 Blue | ℹ️ |
| **Voice** | 🟢 Green | 🎤 |
| **Music** | 🟢 Green | 🎵 |
| **Admin** | 🟠 Orange | ⚙️ |
| **Status** | 🔵 Blue | 👁️ |
| **Help** | 🟣 Purple | 📖 |
| **Ethereal** | 🟣 Ethereal | ✨ |
| **Greyple** | ⚫ Grey | 🔇 |

---

## 📝 TempVoice Interface Embed

```
╔════════════════════════════════════════════════════════════════╗
║ TempVoice Interface                                            ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Use the buttons below to manage **your** temp VC.             ║
║ Actions apply only to the VC you own.                         ║
║                                                                ║
║ [Lock/Unlock] [Hide/Show] [Waiting Room] [Rename] [Limit]    ║
║                                                                ║
║ Footer: Create a temp VC by joining the Create VC channel     ║
║                                                                ║
║ [Blue embed - discord.Color.blue()]                           ║
╚════════════════════════════════════════════════════════════════╝
```

---

## Summary

**Total Embed Types:** 50+
**Primary Colors Used:** Green, Red, Orange, Blue, Purple
**Common Patterns:**
- ✅ Success messages use green
- ❌ Errors use red
- ⏳ Warnings use orange
- ℹ️ Info uses blue
- 👁️ Special (Argus) uses purple/ethereal

All embeds include relevant emoji for quick visual identification and follow the Argus persona's design language.
