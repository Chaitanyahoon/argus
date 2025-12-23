const { Events } = require('discord.js');
const { jsonDb } = require('../../db/jsonDb');
const { checkAwakening, checkMood } = require('../../systems/awaken');
const { handleLeveling } = require('../../systems/leveling');

module.exports = {
    name: Events.MessageCreate,
    async execute(message) {
        if (message.author.bot || !message.guild) return;

        const userId = message.author.id;
        const guildId = message.guild.id;

        // 1. Ensure User Memory Exists
        let user = jsonDb.getUser(userId);

        if (!user) {
            user = jsonDb.setUser(userId, {
                username: message.author.username,
                interactions: 0,
                last_seen: new Date().toISOString(),
                affection: 0,
                resentment: 0,
                trust: 0,
                xp: 0,
                level: 1
            });
        }

        // 2. Ensure Guild/Bot State Exists
        let guildState = jsonDb.getGuild(guildId);
        if (!guildState) {
            guildState = jsonDb.setGuild(guildId, {
                awakening_progress: 0,
                awakening_stage: 0,
                mood_mode: 'NORMAL',
                logging_channel_id: null
            });
        }

        // 3. Increment Interaction Counts
        jsonDb.setUser(userId, {
            interactions: (user.interactions || 0) + 1,
            last_seen: new Date().toISOString()
        });

        // 4. Global Awakening Progress
        jsonDb.setGuild(guildId, {
            awakening_progress: (guildState.awakening_progress || 0) + 1
        });

        // 5. Trigger Systems
        checkAwakening(guildId);
        handleLeveling(message);

        // Random Mood Check (10% chance per message)
        if (Math.random() < 0.1) {
            checkMood(guildId);
        }
    },
};
