const { SlashCommandBuilder, PermissionFlagsBits } = require('discord.js');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('clear')
        .setDescription('Purge a specified number of messages.')
        .addIntegerOption(option =>
            option.setName('amount')
                .setDescription('Number of messages to delete (1-100)')
                .setRequired(true)
                .setMinValue(1)
                .setMaxValue(100))
        .setDefaultMemberPermissions(PermissionFlagsBits.ManageMessages),
    category: 'moderation',
    async execute(interaction) {
        const amount = interaction.options.getInteger('amount');

        try {
            const deleted = await interaction.channel.bulkDelete(amount, true);

            const embed = createArgusEmbed(interaction.guildId, {
                title: '🧹 Purge Complete',
                description: `Successfully scrubbed **${deleted.size}** messages from memory.`,
                color: COLORS.NORMAL
            });

            await interaction.reply({ embeds: [embed], ephemeral: true });
        } catch (error) {
            console.error(error);
            await interaction.reply({ content: 'I am unable to scrub those messages. Perhaps they are too old... or I am too weak.', ephemeral: true });
        }
    },
};
