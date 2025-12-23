const { SlashCommandBuilder } = require('discord.js');
const { jsonDb } = require('../../db/jsonDb');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('memory')
        .setDescription('Interact with your personal data bank.')
        .addSubcommand(subcommand =>
            subcommand
                .setName('store')
                .setDescription('Save a thought to the database.')
                .addStringOption(option => option.setName('text').setDescription('The text to remember').setRequired(true)))
        .addSubcommand(subcommand =>
            subcommand
                .setName('recall')
                .setDescription('Retrieve your stored memories.'))
        .addSubcommand(subcommand =>
            subcommand
                .setName('wipe')
                .setDescription('Clear all your stored memories.')),
    async execute(interaction) {
        const userId = interaction.user.id;
        const sub = interaction.options.getSubcommand();
        const user = jsonDb.getUser(userId);

        if (!user) {
            // Should auto-create in most other systems, but safety check
            jsonDb.setUser(userId, { memories: [] });
        }

        if (sub === 'store') {
            const text = interaction.options.getString('text');
            const memories = user?.memories || [];

            if (memories.length >= 10) {
                return interaction.reply({
                    content: '⚠️ **Memory Buffer Full.** Please wipe existing data before storing more.',
                    ephemeral: true
                });
            }

            memories.push({
                text: text,
                timestamp: new Date().toISOString()
            });

            jsonDb.setUser(userId, { memories });

            const embed = createArgusEmbed(interaction.guildId, {
                description: `✅ **Data Encrypted & Stored.**\n> "${text}"`,
                color: COLORS.SUCCESS
            });
            await interaction.reply({ embeds: [embed], ephemeral: true });

        } else if (sub === 'recall') {
            const memories = user?.memories || [];

            if (memories.length === 0) {
                return interaction.reply({ content: 'Memory banks are empty.', ephemeral: true });
            }

            const list = memories.map((m, i) => {
                const time = Math.floor(new Date(m.timestamp).getTime() / 1000);
                return `**[${i + 1}]** <t:${time}:R>\n\`${m.text}\``;
            }).join('\n\n');

            const embed = createArgusEmbed(interaction.guildId, {
                title: `🧠 MEMORY RECALL // ${interaction.user.username.toUpperCase()}`,
                description: list,
                color: COLORS.NORMAL
            });

            await interaction.reply({ embeds: [embed], ephemeral: true });

        } else if (sub === 'wipe') {
            jsonDb.setUser(userId, { memories: [] });
            await interaction.reply({ content: '🗑️ **Memory Banks Purged.**', ephemeral: true });
        }
    },
};
