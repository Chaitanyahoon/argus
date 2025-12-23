const { SlashCommandBuilder, PermissionFlagsBits } = require('discord.js');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('ban')
        .setDescription('Bans a member from the server.')
        .addUserOption(option =>
            option.setName('target')
                .setDescription('The member to ban')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('reason')
                .setDescription('Reason for the ban'))
        .setDefaultMemberPermissions(PermissionFlagsBits.BanMembers),
    async execute(interaction) {
        const target = interaction.options.getUser('target');
        const reason = interaction.options.getString('reason') || 'No reason provided';

        try {
            await interaction.guild.members.ban(target, { reason });

            const embed = createArgusEmbed(interaction.guildId, {
                title: '🔨 Perpetual Exile',
                description: `**${target.tag}** has been permanently severed from this reality.\n**Reason:** ${reason}`,
                color: COLORS.ERROR
            });

            await interaction.reply({ embeds: [embed] });
        } catch (error) {
            console.error(error);
            await interaction.reply({ content: "The ban protocol failed. The subject is too resilient.", ephemeral: true });
        }
    },
};
