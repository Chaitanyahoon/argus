const { SlashCommandBuilder } = require('discord.js');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('serverinfo')
        .setDescription('Displays information about this server.'),
    category: 'utility',
    async execute(interaction) {
        const guild = interaction.guild;
        const owner = await guild.fetchOwner();

        // Calculate counts
        const humans = guild.members.cache.filter(m => !m.user.bot).size;
        const bots = guild.members.cache.filter(m => m.user.bot).size;
        const textChannels = guild.channels.cache.filter(c => c.type === 0).size;
        const voiceChannels = guild.channels.cache.filter(c => c.type === 2).size;

        // Timestamps
        const created = Math.floor(guild.createdTimestamp / 1000);

        const embed = createArgusEmbed(interaction.guildId, {
            title: `SECTOR ANALYSIS // ${guild.name.toUpperCase()}`,
            description: `**ID:** \`${guild.id}\`\n**OVERSEER:** <@${owner.id}>`,
            thumbnail: guild.iconURL({ dynamic: true, size: 512 }),
            image: guild.bannerURL({ dynamic: true, size: 1024 }),
            color: COLORS.ETHEREAL,
            fields: [
                {
                    name: 'POPULATION METRICS',
                    value: `\`TOTAL :: ${guild.memberCount}\`\n\`HUMAN :: ${humans}\`\n\`DROID :: ${bots}\``,
                    inline: true
                },
                {
                    name: 'INFRASTRUCTURE',
                    value: `\`TEXT  :: ${textChannels}\`\n\`VOICE :: ${voiceChannels}\`\n\`ROLES :: ${guild.roles.cache.size}\``,
                    inline: true
                },
                {
                    name: 'TIMELINE',
                    value: `**Established:** <t:${created}:R> (<t:${created}:D>)`,
                    inline: false
                },
                {
                    name: 'SECURITY',
                    value: `\`LEVEL :: ${guild.verificationLevel}\`\n\`BOOST :: ${guild.premiumSubscriptionCount} (TIER ${guild.premiumTier})\``,
                    inline: false
                }
            ],
            footer: 'System Territory Scan'
        });

        await interaction.reply({ embeds: [embed] });
    },
};
