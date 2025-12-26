const { SlashCommandBuilder } = require('discord.js');
const { jsonDb } = require('../../db/jsonDb');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('leaderboard')
        .setDescription('Displays the most prominent inhabitants of this reality.'),
    category: 'utility',
    async execute(interaction) {
        const allUsers = jsonDb.getAllUsers();

        // Sort by level desc, then xp desc
        const topUsers = allUsers
            .sort((a, b) => (b.level || 0) - (a.level || 0) || (b.xp || 0) - (a.xp || 0))
            .slice(0, 10);

        if (topUsers.length === 0) {
            return await interaction.reply({ content: "The archives are empty. No one has evolved yet.", ephemeral: true });
        }

        const description = topUsers.map((u, index) => {
            const medal = index === 0 ? '👑' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${index + 1}`;
            return `${medal} **${u.username}** — Level ${u.level || 1} (${u.xp || 0} XP)`;
        }).join('\n');

        const embed = createArgusEmbed(interaction.guildId, {
            title: '🏆 GLOBAL HIERARCHY',
            description: description,
            color: COLORS.ETHEREAL
        });

        await interaction.reply({ embeds: [embed] });
    },
};
