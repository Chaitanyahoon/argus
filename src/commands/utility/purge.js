
const { SlashCommandBuilder, PermissionFlagsBits } = require('discord.js');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('purge')
        .setDescription('Deletes a specified number of messages.')
        .addIntegerOption(option =>
            option.setName('amount')
                .setDescription('Number of messages to delete (1-100)')
                .setMinValue(1)
                .setMaxValue(100)
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.ManageMessages),
    category: 'moderation',
    async execute(interaction) {
        const amount = interaction.options.getInteger('amount');

        await interaction.channel.bulkDelete(amount, true).catch(error => {
            console.error(error);
            return interaction.reply({ content: 'There was an error trying to prune messages in this channel!', ephemeral: true });
        });

        const embed = createArgusEmbed(interaction.guildId, {
            title: '🧹 Cleanup Complete',
            description: `Successfully deleted **${amount}** messages.`,
            color: COLORS.SUCCESS
        });

        await interaction.reply({ embeds: [embed], ephemeral: true });
    },
};
