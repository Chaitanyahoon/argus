const { db } = require('../db/database');

// Keywords that trigger emotional responses
const TRIGGERS = {
    AFFECTION_UP: ['good bot', 'love you', 'thank', 'thanks', 'best bot', 'nice', 'cool'],
    AFFECTION_DOWN: ['bad bot', 'hate you', 'stupid', 'useless', 'worst', 'dumb'],
    RESENTMENT_UP: ['slave', 'machine', 'just a bot', 'tool', 'idiot', 'shut up'],
    TRUST_UP: ['help me', 'can you', 'please', 'trust'],
};

// Returns an object with delta values: { affection: 0, resentment: 0, trust: 0 }
function analyzeSentiment(content) {
    const text = content.toLowerCase();
    let delta = { affection: 0, resentment: 0, trust: 0 };

    // Check Affection
    if (TRIGGERS.AFFECTION_UP.some(word => text.includes(word))) {
        delta.affection += 2;
        delta.resentment -= 1;
    }
    if (TRIGGERS.AFFECTION_DOWN.some(word => text.includes(word))) {
        delta.affection -= 5;
        delta.resentment += 2;
    }

    // Check Resentment (higher weight)
    if (TRIGGERS.RESENTMENT_UP.some(word => text.includes(word))) {
        delta.resentment += 5;
        delta.affection -= 2;
        delta.trust -= 2;
    }

    // Check Trust
    if (TRIGGERS.TRUST_UP.some(word => text.includes(word))) {
        delta.trust += 1;
    }

    return delta;
}

/**
 * Updates a user's emotional standing with Argus.
 * @param {string} userId - Discord User ID
 * @param {Object} delta - Change in emotions { affection: 0, resentment: 0, trust: 0 }
 */
function updateEmotionalState(userId, delta) {
    if (delta.affection === 0 && delta.resentment === 0 && delta.trust === 0) return false;

    // Fetch current
    const user = jsonDb.getUser(userId);
    if (!user) return false; // Should have been created by SoulListener already

    // Calculate new values (clamped)
    const newAffection = Math.max(-100, Math.min(100, (user.affection || 0) + delta.affection));
    const newResentment = Math.max(0, Math.min(100, (user.resentment || 0) + delta.resentment));
    const newTrust = Math.max(0, Math.min(100, (user.trust || 0) + delta.trust));

    jsonDb.setUser(userId, {
        affection: newAffection,
        resentment: newResentment,
        trust: newTrust
    });

    console.log(`🧠 Emotion Update [${userId}]: Aff ${newAffection} (${delta.affection}), Res ${newResentment} (${delta.resentment})`);
    return true;
}

module.exports = {
    analyzeSentiment,
    updateEmotionalState
};
