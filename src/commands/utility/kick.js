const { SlashCommandBuilder, PermissionFlagsBits } = require('discord.js');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('kick')
        .setDescription('Kicks a member from the server.')
        .addUserOption(option =>
            option.setName('target')
                .setDescription('The member to kick')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('reason')
                .setDescription('Reason for the kick'))
        .setDefaultMemberPermissions(PermissionFlagsBits.KickMembers),
    async execute(interaction) {
        const target = interaction.options.getMember('target');
        const reason = interaction.options.getString('reason') || 'No reason provided';

        if (!target) {
            return await interaction.reply({ content: "That user doesn't seem to be in this guild.", ephemeral: true });
        }

        if (!target.kickable) {
            return await interaction.reply({ content: "I lack the authority to kick this individual. They may be protected by higher powers (roles).", ephemeral: true });
        }

        try {
            await target.kick(reason);

            const embed = createArgusEmbed(interaction.guildId, {
                title: '👢 Member Expelled',
                description: `**${target.user.tag}** has been removed from the collective.\n**Reason:** ${reason}`,
                color: COLORS.WARNING
            });

            await interaction.reply({ embeds: [embed] });
        } catch (error) {
            console.error(error);
            await interaction.reply({ content: "A glitch occurred while trying to expel the subject.", ephemeral: true });
        }
    },
};
