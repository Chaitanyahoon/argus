const cooldowns = new Map();

/**
 * Checks if a user is on cooldown for a specific action.
 * @param {string} userId - The Discord user ID.
 * @param {string} action - The action name.
 * @param {number} duration - The cooldown duration in seconds.
 * @returns {number|null} - Remaining time in seconds, or null if not on cooldown.
 */
function checkCooldown(userId, action, duration) {
    const key = `${userId}:${action}`;
    const now = Date.now();
    const expirationTime = cooldowns.get(key);

    if (expirationTime) {
        const timeLeft = (expirationTime - now) / 1000;
        if (timeLeft > 0) return Math.ceil(timeLeft);
    }

    cooldowns.set(key, now + (duration * 1000));
    return null;
}

module.exports = { checkCooldown };
