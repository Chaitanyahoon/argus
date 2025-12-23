const { SlashCommandBuilder } = require('discord.js');
const { jsonDb } = require('../../db/jsonDb');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');
const { createProgressBar } = require('../../utils/uiUtils');
const { getXpForLevel } = require('../../systems/leveling');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('rank')
        .setDescription('Checks your current evolutionary standing.')
        .addUserOption(option => option.setName('target').setDescription('Member to check')),
    async execute(interaction) {
        const target = interaction.options.getUser('target') || interaction.user;
        const user = jsonDb.getUser(target.id);

        if (!user) {
            return await interaction.reply({ content: "I have no memory of this subject. They must interact more.", ephemeral: true });
        }

        const level = user.level || 1;
        const xp = user.xp || 0;
        const nextLevelXp = getXpForLevel(level);
        const progressBar = createProgressBar(xp, nextLevelXp);

        const embed = createArgusEmbed(interaction.guildId, {
            title: `RANK // ${target.username.toUpperCase()}`,
            description: `<@${target.id}>`,
            fields: [
                { name: 'Level', value: `${level}`, inline: true },
                { name: 'Experience', value: `${xp} / ${nextLevelXp}`, inline: true },
                { name: 'Progress', value: progressBar }
            ],
            color: COLORS.SUCCESS,
            thumbnail: target.displayAvatarURL({ dynamic: true })
        });

        await interaction.reply({ embeds: [embed] });
    },
};
