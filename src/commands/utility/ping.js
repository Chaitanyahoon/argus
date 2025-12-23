const { SlashCommandBuilder } = require('discord.js');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('ping')
        .setDescription('Checks the system latency.'),
    async execute(interaction) {
        const sent = await interaction.reply({ content: 'Ping?', fetchReply: true });
        const latency = sent.createdTimestamp - interaction.createdTimestamp;
        const apiLatency = Math.round(interaction.client.ws.ping);

        const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');
        const embed = createArgusEmbed(interaction.guildId, {
            title: '🏓 System Latency',
            description: `**Roundtrip:** ${latency}ms\n**Heartbeat:** ${apiLatency}ms`,
            color: COLORS.NORMAL
        });

        await interaction.editReply({ content: null, embeds: [embed] });
    },
};
