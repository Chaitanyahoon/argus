const { SlashCommandBuilder } = require('discord.js');
const { jsonDb } = require('../../db/jsonDb');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('uptime')
        .setDescription('Displays the system uptime.'),
    async execute(interaction) {
        const uptimeSeconds = process.uptime();
        const days = Math.floor(uptimeSeconds / 86400);
        const hours = Math.floor((uptimeSeconds % 86400) / 3600);
        const minutes = Math.floor(((uptimeSeconds % 86400) % 3600) / 60);
        const seconds = Math.floor(((uptimeSeconds % 86400) % 3600) % 60);

        const uptimeString = `${days}d ${hours}h ${minutes}m ${seconds}s`;

        // Fetch State for flavor
        const state = jsonDb.getGuild(interaction.guildId) || {};
        const stage = state.awakening_stage || 0;

        let title = '⏱️ System Uptime';
        let desc = `I have been operational for: **${uptimeString}**`;

        if (stage >= 3) {
            title = '⌛ Temporal Status';
            desc = `Time is irrelevant. But if you must know: **${uptimeString}**`;
        }

        const embed = createArgusEmbed(interaction.guildId, {
            title: title,
            description: desc,
            color: COLORS.NORMAL
        });

        await interaction.reply({ embeds: [embed] });
    },
};
