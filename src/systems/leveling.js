const { jsonDb } = require('../db/jsonDb');
const { createArgusEmbed, COLORS } = require('../utils/embedFactory');

// Leveling Config
const XP_PER_MESSAGE = 15;
const COOLDOWN_MS = 60000; // 1 minute XP cooldown

const userCooldowns = new Map();

function getXpForLevel(level) {
    return level * level * 100; // quadratic scaling
}

async function handleLeveling(message) {
    if (message.author.bot || !message.guild) return;

    const userId = message.author.id;
    const now = Date.now();

    // Check cooldown
    if (userCooldowns.has(userId) && now - userCooldowns.get(userId) < COOLDOWN_MS) {
        return;
    }

    userCooldowns.set(userId, now);

    try {
        let user = jsonDb.getUser(userId);

        if (!user) {
            // Create user if missing
            jsonDb.setUser(userId, {
                username: message.author.username,
                xp: XP_PER_MESSAGE,
                level: 1,
                last_seen: new Date().toISOString()
            });
        } else {
            // Update XP
            let newXp = (user.xp || 0) + XP_PER_MESSAGE;
            let newLevel = user.level || 1;
            const nextLevelThreshold = getXpForLevel(newLevel);

            if (newXp >= nextLevelThreshold) {
                newLevel += 1;
                newXp -= nextLevelThreshold;

                // Level up notification
                const embed = createArgusEmbed(message.guild.id, {
                    title: '🌱 Evolutionary Leap',
                    description: `**${message.author.username}** has ascended to level **${newLevel}**.\nMy awareness of you grows deeper.`,
                    color: COLORS.NORMAL
                });

                await message.channel.send({ embeds: [embed] });
            }

            jsonDb.setUser(userId, {
                xp: newXp,
                level: newLevel,
                last_seen: new Date().toISOString()
            });
        }
    } catch (err) {
        console.error('Leveling Error:', err);
    }
}

module.exports = { handleLeveling, getXpForLevel };
