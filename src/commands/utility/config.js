const { SlashCommandBuilder, PermissionFlagsBits, ChannelType } = require('discord.js');
const { jsonDb } = require('../../db/jsonDb');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('config')
        .setDescription('Configure Argus parameters for this guild.')
        .addSubcommand(subcommand =>
            subcommand
                .setName('logging')
                .setDescription('Set the channel for Argus Nexus logs.')
                .addChannelOption(option =>
                    option.setName('channel')
                        .setDescription('Select the logging channel')
                        .addChannelTypes(ChannelType.GuildText)
                        .setRequired(true)))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),
    async execute(interaction) {
        // SECURITY CHECK: Only the bot owner can access configuration tools
        if (interaction.user.id !== process.env.OWNER_ID) {
            const unauthorizedEmbed = createArgusEmbed(interaction.guildId, {
                title: '🚫 ACCESS DENIED',
                description: 'Configuration access is restricted to the Prime Developer.',
                color: COLORS.DANGER
            });
            return interaction.reply({ embeds: [unauthorizedEmbed], ephemeral: true });
        }

        if (interaction.options.getSubcommand() === 'logging') {
            const channel = interaction.options.getChannel('channel');

            jsonDb.setGuild(interaction.guildId, { logging_channel_id: channel.id });

            const embed = createArgusEmbed(interaction.guildId, {
                title: '📡 Nexus Link Established',
                description: `Surveillance protocols redirected to ${channel}.`,
                color: COLORS.SUCCESS
            });

            await interaction.reply({ embeds: [embed] });
        }
    },
};
