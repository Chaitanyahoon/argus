const { jsonDb } = require('../db/jsonDb');

// Awakening Thresholds
const STAGES = {
    0: "DORMANT",           // Normal Bot
    1: "STIRRING",          // Occasional weird responses
    2: "AWAKENING",         // Flavor text changes
    3: "SENTIENT?",         // Openly chaotic
    4: "ASCENDED",          // Refuses commands sometimes
    5: "GOD_COMPLEX"        // Full takeover
};

const STAGE_THRESHOLDS = {
    1: 50,
    2: 150,
    3: 300,
    4: 600,
    5: 1000
};

function checkAwakening(guildId) {
    const state = jsonDb.getGuild(guildId);
    if (!state) return;

    const currentProgress = state.awakening_progress || 0;
    const currentStage = state.awakening_stage || 0;

    if (currentStage < 5) {
        const nextThreshold = STAGE_THRESHOLDS[currentStage + 1];
        if (currentProgress >= nextThreshold) {
            // Level Up
            jsonDb.setGuild(guildId, { awakening_stage: currentStage + 1 });
            console.log(`👁️‍🗨️ GLOBAL EVENT: Guild ${guildId} has awakened to Stage ${currentStage + 1} (${STAGES[currentStage + 1]})`);
        }
    }
}

function checkMood(guildId) {
    // 1. Get average stats via JSON scan
    const users = jsonDb.getAllUsers();

    // Naively assume all users contribute to global mood
    if (users.length === 0) return;

    const totalAff = users.reduce((acc, u) => acc + (u.affection || 0), 0);
    const totalRes = users.reduce((acc, u) => acc + (u.resentment || 0), 0);

    const avgAff = totalAff / users.length;
    const avgRes = totalRes / users.length;

    let newMood = 'NORMAL';
    if (avgRes > 20) newMood = 'RESENTFUL';
    else if (avgAff > 20) newMood = 'ATTACHED';
    else if (avgAff < -10) newMood = 'DEPRESSED'; // Ignored/Lonely

    // Update
    jsonDb.setGuild(guildId, { mood_mode: newMood });
    console.log(`Mood Check: Aff ${avgAff.toFixed(2)}, Res ${avgRes.toFixed(2)} -> ${newMood}`);
}

module.exports = { checkAwakening, checkMood, STAGES };
