const { SlashCommandBuilder, PermissionFlagsBits } = require('discord.js');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('timeout')
        .setDescription('Temporarily silence a member.')
        .addUserOption(option =>
            option.setName('target')
                .setDescription('The member to timeout')
                .setRequired(true))
        .addIntegerOption(option =>
            option.setName('duration')
                .setDescription('Duration in minutes')
                .setRequired(true)
                .setMinValue(1)
                .setMaxValue(43200)) // Max 30 days
        .addStringOption(option =>
            option.setName('reason')
                .setDescription('Reason for the timeout'))
        .setDefaultMemberPermissions(PermissionFlagsBits.ModerateMembers),
    category: 'moderation',
    async execute(interaction) {
        const target = interaction.options.getMember('target');
        const duration = interaction.options.getInteger('duration');
        const reason = interaction.options.getString('reason') || 'No reason provided';

        if (!target) {
            return await interaction.reply({ content: "Subject not found in this sector.", ephemeral: true });
        }

        try {
            await target.timeout(duration * 60000, reason);

            const embed = createArgusEmbed(interaction.guildId, {
                title: '🤐 Subject Silenced',
                description: `**${target.user.tag}** has been placed in stasis for **${duration}** minutes.\n**Reason:** ${reason}`,
                color: COLORS.WARNING
            });

            await interaction.reply({ embeds: [embed] });
        } catch (error) {
            console.error(error);
            await interaction.reply({ content: "Stasis protocol failed. Subject is too volatile.", ephemeral: true });
        }
    },
};
