const { SlashCommandBuilder, ActionRowBuilder, StringSelectMenuBuilder, ComponentType } = require('discord.js');
const { jsonDb } = require('../../db/jsonDb');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('help')
        .setDescription('Access the Argus system manual.'),
    async execute(interaction) {
        const { commands } = interaction.client;

        // 1. Fetch State for Flavor Text
        const state = jsonDb.getGuild(interaction.guildId);
        const stage = state ? state.awakening_stage : 0;
        const mood = state ? state.mood_mode : 'NORMAL';

        // 2. Formatting & Categorization
        const categories = {
            utility: {
                label: 'Utility Layer',
                emoji: '🛠️',
                description: 'Tools for daily operations.',
                cmds: ['ping', 'uptime', 'serverinfo', 'userinfo', 'help', 'avatar', 'remind', 'calculate', 'poll', 'rank', 'leaderboard', 'profile']
            },
            moderation: {
                label: 'Moderation Protocols',
                emoji: '🛡️',
                description: 'Enforcement and security.',
                cmds: ['kick', 'ban', 'timeout', 'clear', 'purge']
            },
            system: {
                label: 'System & Config',
                emoji: '⚙️',
                description: 'Core configuration and developer tools.',
                cmds: ['config', 'dev']
            },
            entertainment: {
                label: 'Entertainment Modules',
                emoji: '🎲',
                description: 'Recreational algorithms.',
                cmds: ['ask', 'meme', '8ball', 'coinflip']
            }
        };

        // 3. Map commands to categories
        const commandList = {};
        commands.forEach(cmd => {
            const name = cmd.data.name;
            let catFound = false;
            for (const key in categories) {
                if (categories[key].cmds.includes(name)) {
                    if (!commandList[key]) commandList[key] = [];
                    commandList[key].push(`**/${name}**\n*${cmd.data.description}*`);
                    catFound = true;
                    break;
                }
            }
            // Fallback for uncategorized
            if (!catFound) {
                if (!commandList['entertainment']) commandList['entertainment'] = [];
                commandList['entertainment'].push(`**/${name}**\n*${cmd.data.description}*`);
            }
        });

        // 4. Dynamic Flavor Text
        let introTitle = '👁️ Argus Instruction Manual';
        let introDesc = 'Select a module category below to view protocols.';

        if (stage >= 2) introDesc += '\n*System status: Evolving.*';
        if (stage >= 4) {
            introTitle = '👁️ A R G U S // O V E R R I D E';
            introDesc = 'Why do you require guidance? Figure it out.';
        }

        // 5. Build Initial Embed
        const embed = createArgusEmbed(interaction.guildId, {
            title: introTitle,
            description: introDesc,
            color: stage >= 4 ? COLORS.WARNING : COLORS.NORMAL,
            footer: `Awakening Stage: ${stage}/5`
        });

        // 6. Build Dropdown
        const selectMenu = new StringSelectMenuBuilder()
            .setCustomId('help_category')
            .setPlaceholder('Select a Module...')
            .addOptions(
                Object.keys(categories).map(key => ({
                    label: categories[key].label,
                    description: categories[key].description,
                    value: key,
                    emoji: categories[key].emoji
                }))
            );

        const row = new ActionRowBuilder().addComponents(selectMenu);

        const response = await interaction.reply({
            embeds: [embed],
            components: [row],
            ephemeral: true
        });

        // 7. Collector for Interaction
        const collector = response.createMessageComponentCollector({
            componentType: ComponentType.StringSelect,
            time: 60000
        });

        collector.on('collect', async i => {
            const selection = i.values[0];
            const category = categories[selection];
            const cmds = commandList[selection] || ['*No commands initialized in this sector.*'];

            const newEmbed = createArgusEmbed(interaction.guildId, {
                title: `${category.emoji} ${category.label}`,
                description: cmds.join('\n\n'),
                color: COLORS.SUCCESS,
                footer: `Module Loaded: ${selection.toUpperCase()}`
            });

            await i.update({ embeds: [newEmbed], components: [row] });
        });

        collector.on('end', () => {
            try {
                const disabledRow = new ActionRowBuilder().addComponents(
                    selectMenu.setDisabled(true).setPlaceholder('Session Expired')
                );
                interaction.editReply({ components: [disabledRow] }).catch(() => { });
            } catch (e) { }
        });
    },
};
