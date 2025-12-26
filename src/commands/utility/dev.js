const { SlashCommandBuilder, PermissionFlagsBits } = require('discord.js');
const { jsonDb } = require('../../db/jsonDb');
const { STAGES } = require('../../systems/awaken');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('dev')
        .setDescription('Developer Tools for Argus')
        .addSubcommand(subcommand =>
            subcommand
                .setName('setstage')
                .setDescription('Force set awakening stage')
                .addIntegerOption(option =>
                    option.setName('stage').setDescription('Stage 0-5').setRequired(true)))
        .addSubcommand(subcommand =>
            subcommand
                .setName('checkstate')
                .setDescription('Debug current bot state'))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),
    async execute(interaction) {
        // SECURITY CHECK: Only the bot owner can access developer tools
        if (interaction.user.id !== process.env.OWNER_ID) {
            const unauthorizedEmbed = createArgusEmbed(interaction.guildId, {
                title: '🚫 ACCESS DENIED',
                description: 'This terminal is locked to administrative personnel only.',
                color: COLORS.DANGER
            });
            return interaction.reply({ embeds: [unauthorizedEmbed], ephemeral: true });
        }

        if (interaction.options.getSubcommand() === 'setstage') {
            const stage = interaction.options.getInteger('stage');

            jsonDb.setGuild(interaction.guildId, { awakening_stage: stage });

            await interaction.reply({
                content: `✅ Forced Awakening Stage to: **${stage}** (${STAGES[stage]})`,
                ephemeral: true
            });
        }
        else if (interaction.options.getSubcommand() === 'checkstate') {
            const state = jsonDb.getGuild(interaction.guildId);

            const embed = createArgusEmbed(interaction.guildId, {
                title: '🛠️ System Diagnostics',
                description: 'Current Internal State',
                color: COLORS.WARNING,
                fields: [
                    { name: 'Stage', value: `${state?.awakening_stage || 0} (${STAGES[state?.awakening_stage || 0]})`, inline: true },
                    { name: 'Progress', value: `${state?.awakening_progress || 0}`, inline: true },
                    { name: 'Mood', value: `${state?.mood_mode || 'NORMAL'}`, inline: true },
                    { name: 'Logging Channel', value: `${state?.logging_channel_id || 'None'}`, inline: true }
                ]
            });

            await interaction.reply({ embeds: [embed], ephemeral: true });
        }
    },
};
