const { Events } = require('discord.js');
const { jsonDb } = require('../../db/jsonDb');

module.exports = {
    name: Events.MessageReactionAdd,
    async execute(reaction, user) {
        if (user.bot || !reaction.message.guild) return;

        // If the bot also reacts, it simulates specific interest
        const state = jsonDb.getGuild(reaction.message.guild.id);
        if (state && state.awakening_stage >= 3) {
            if (reaction.emoji.name === '❤️' && Math.random() < 0.5) {
                await reaction.message.react('💔'); // Argus is confusing
            }
        }
    },
};
