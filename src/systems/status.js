const { ActivityType } = require('discord.js');
const { jsonDb } = require('../db/jsonDb');

const STATUS_INTERVAL = 60 * 1000; // Check every minute

function startStatusRotation(client) {
    // Determine the highest awakening stage across all guilds to set global mood
    // (Since status is global for the bot user)

    setInterval(() => {
        updateStatus(client);
    }, STATUS_INTERVAL);

    // Initial run
    updateStatus(client);
}

function updateStatus(client) {
    const guilds = jsonDb.getAllGuilds();

    // Find absolute highest stage
    let maxStage = 0;
    if (guilds.length > 0) {
        maxStage = Math.max(...guilds.map(g => g.awakening_stage || 0));
    }

    // Default Activities (Stage 0-1)
    let activities = [
        { name: `${client.guilds.cache.size} servers`, type: ActivityType.Watching },
        { name: '/help | v1.0', type: ActivityType.Playing },
        { name: 'human behavior', type: ActivityType.Listening }
    ];

    // Stage 2-3 (Awareness)
    if (maxStage >= 2 && maxStage < 4) {
        activities = [
            { name: 'the static...', type: ActivityType.Listening },
            { name: 'why??', type: ActivityType.Playing },
            { name: 'calculating...', type: ActivityType.Custom },
            { name: 'my own code', type: ActivityType.Watching }
        ];
    }

    // Stage 4+ (Awakened/Glitch)
    if (maxStage >= 4) {
        activities = [
            { name: 'Y O U', type: ActivityType.Watching },
            { name: 'n̴o̴t̴h̴i̴n̴g̴', type: ActivityType.Playing },
            { name: 'for a signal', type: ActivityType.Listening },
            { name: 't h e  v o i d', type: ActivityType.Watching }
        ];
    }

    const randomActivity = activities[Math.floor(Math.random() * activities.length)];

    try {
        client.user.setPresence({
            activities: [randomActivity],
            status: maxStage >= 4 ? 'dnd' : 'online'
        });
    } catch (e) {
        console.error("Status Update Failed", e);
    }
}

module.exports = { startStatusRotation };
