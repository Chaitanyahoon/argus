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
