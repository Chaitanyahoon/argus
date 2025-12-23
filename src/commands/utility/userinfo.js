const { SlashCommandBuilder } = require('discord.js');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('userinfo')
        .setDescription('Displays distinct personnel data.')
        .addUserOption(option => option.setName('target').setDescription('The user to check')),
    async execute(interaction) {
        const target = interaction.options.getUser('target') || interaction.user;

        // Force fetch to get the banner
        const userWithBanner = await interaction.client.users.fetch(target.id, { force: true });
        const member = await interaction.guild.members.fetch(target.id);

        // Role Logic
        const roles = member.roles.cache
            .filter(r => r.name !== '@everyone')
            .sort((a, b) => b.position - a.position);

        const roleCount = roles.size;
        const maxRolesToShow = 5;
        let roleDisplay = roles.first(maxRolesToShow).map(r => `<@&${r.id}>`).join(' ');

        if (roleCount > maxRolesToShow) {
            roleDisplay += `\n*...and ${roleCount - maxRolesToShow} more.*`;
        }
        if (roleCount === 0) roleDisplay = "`[NO_ACCESS_GRANTED]`";

        // Timestamp Logic
        const joinedDiscord = Math.floor(target.createdTimestamp / 1000);
        const joinedServer = Math.floor(member.joinedTimestamp / 1000);

        const embed = createArgusEmbed(interaction.guildId, {
            title: `DATA RECORD // ${target.username.toUpperCase()}`,
            description: `**ID:** \`${target.id}\`\n**TAG:** \`${target.tag}\``,
            color: COLORS.ETHEREAL,
            thumbnail: target.displayAvatarURL({ dynamic: true, size: 512 }),
            image: userWithBanner.bannerURL({ dynamic: true, size: 1024 }),
            fields: [
                {
                    name: 'TIMELINE',
                    value: `**Created:** <t:${joinedDiscord}:R> (<t:${joinedDiscord}:D>)\n**Joined:** <t:${joinedServer}:R> (<t:${joinedServer}:D>)`,
                    inline: false
                },
                {
                    name: `ACCESS LEVELS [${roleCount}]`,
                    value: roleDisplay,
                    inline: false
                }
            ],
            footer: 'Personnel Identification System'
        });

        await interaction.reply({ embeds: [embed] });
    },
};
