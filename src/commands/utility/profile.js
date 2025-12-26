const { SlashCommandBuilder } = require('discord.js');
const { jsonDb } = require('../../db/jsonDb');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');
const { createProgressBar } = require('../../utils/uiUtils');
const { getXpForLevel } = require('../../systems/leveling');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('profile')
        .setDescription('View or customize your Argus profile.')
        .addSubcommand(subcommand =>
            subcommand
                .setName('view')
                .setDescription('View a user profile')
                .addUserOption(option => option.setName('target').setDescription('The user to view')))
        .addSubcommand(subcommand =>
            subcommand
                .setName('set')
                .setDescription('Update your profile details')
                .addStringOption(option => option.setName('bio').setDescription('Set your biography (max 200 chars)'))
                .addStringOption(option => option.setName('banner').setDescription('Set your banner image URL'))),
    category: 'utility',
    async execute(interaction) {
        if (interaction.options.getSubcommand() === 'set') {
            const bio = interaction.options.getString('bio');
            const banner = interaction.options.getString('banner');
            const userId = interaction.user.id;

            // Validate URL if banner provided
            if (banner && !banner.match(/^https?:\/\/.+\.(jpg|jpeg|png|gif|webp)$/i)) {
                return interaction.reply({ content: '❌ Invalid image URL. Please provide a direct link to an image (jpg, png, gif).', ephemeral: true });
            }

            const updateData = {};
            if (bio) updateData.bio = bio;
            if (banner) updateData.banner = banner;

            jsonDb.setUser(userId, updateData);

            return interaction.reply({ content: '✅ Profile updated successfully.', ephemeral: true });
        }

        if (interaction.options.getSubcommand() === 'view') {
            const target = interaction.options.getUser('target') || interaction.user;
            const user = jsonDb.getUser(target.id);

            if (!user) {
                return interaction.reply({ content: "**[ERROR]**: Subject not found in memory banks.", ephemeral: true });
            }

            const level = user.level || 1;
            const xp = user.xp || 0;
            const nextLevelXp = getXpForLevel(level);
            const progressBar = createProgressBar(xp, nextLevelXp);

            // Format Psych Profile 
            const affection = user.affection || 0;
            const resentment = user.resentment || 0;
            const trust = user.trust || 0;

            const embed = createArgusEmbed(interaction.guildId, {
                title: `PERSONNEL FILE // ${target.username.toUpperCase()}`,
                description: user.bio ? `> *"${user.bio}"*` : '> *No biography recorded.*',
                thumbnail: target.displayAvatarURL({ dynamic: true, size: 512 }),
                image: user.banner || null,
                fields: [
                    {
                        name: 'EVOLUTIONARY STATUS',
                        value: `\`LEVEL :: ${level}\`\n\`XP    :: ${xp} / ${nextLevelXp}\`\n${progressBar}`,
                        inline: false
                    },
                    {
                        name: 'PSYCHOMETRICS',
                        value: `\`AFFECTION  :: ${affection}\`\n\`RESENTMENT :: ${resentment}\`\n\`TRUST      :: ${trust}\``,
                        inline: false
                    }
                ],
                footer: `ID: ${target.id}`
            });

            await interaction.reply({ embeds: [embed] });
        }
    },
};
