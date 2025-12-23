const { SlashCommandBuilder } = require('discord.js');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('avatar')
        .setDescription('Get the avatar of a user.')
        .addUserOption(option => option.setName('target').setDescription('The user to get the avatar for')),
    async execute(interaction) {
        const user = interaction.options.getUser('target') || interaction.user;
        const avatarUrl = user.displayAvatarURL({ dynamic: true, size: 1024 });

        const embed = createArgusEmbed(interaction.guildId, {
            title: `${user.username}'s Visual Identity`,
            image: avatarUrl,
            color: COLORS.NORMAL
        });

        await interaction.reply({ embeds: [embed] });
    },
};
