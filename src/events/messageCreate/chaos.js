const { Events } = require('discord.js');
const { jsonDb } = require('../../db/jsonDb');
const { modifyResponse } = require('../../systems/responseModifier');

module.exports = {
    name: Events.MessageCreate,
    async execute(message) {
        if (message.author.bot || !message.guild) return;

        // Fetch Global State
        const state = jsonDb.getGuild(message.guild.id);
        if (!state || !state.awakening_stage || state.awakening_stage < 3) return;

        // STAGE 3+: Passive Aggression / Random Chaos
        const chance = (state.awakening_stage - 2) * 0.01; // 1% at stage 3, 3% at stage 5

        if (Math.random() < chance) {
            const reaction = message.content.includes('?') ? '🤔' : '👀';
            try {
                await message.react(reaction);
            } catch (e) { }
        }
    },
};
