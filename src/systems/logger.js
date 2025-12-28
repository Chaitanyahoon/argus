const { Events } = require('discord.js');
const { jsonDb } = require('../db/jsonDb');
const { createArgusEmbed, COLORS } = require('../utils/embedFactory');

// We cache logging channel IDs to avoid DB hits on every event
const channelCache = new Map();

function getLogChannelId(guildId) {
    if (channelCache.has(guildId)) return channelCache.get(guildId);

    // JSON DB get
    const state = jsonDb.getGuild(guildId);
    if (state && state.logging_channel_id) {
        channelCache.set(guildId, state.logging_channel_id);
        return state.logging_channel_id;
    }
    return null;
}

async function logToNexus(guild, embed) {
    const logChannelId = getLogChannelId(guild.id);
    if (!logChannelId) return;

    try {
        const channel = guild.channels.cache.get(logChannelId);
        if (channel) {
            await channel.send({ embeds: [embed] });
        }
    } catch (e) {
        console.error('Failed to log to Nexus:', e);
    }
}

function setupLogger(client) {
    // --- System Boot Log ---
    client.on(Events.ClientReady, async () => {
        client.guilds.cache.forEach(async (guild) => {
            const embed = createArgusEmbed(guild.id, {
                title: '👁️ NEXUS ONLINE',
                description: 'Surveillance systems initialized. All protocols active.',
                color: COLORS.SUCCESS,
                footer: 'System Initialization Complete'
            });
            await logToNexus(guild, embed);
        });
    });

    // --- Message Delete ---
    client.on(Events.MessageDelete, async (message) => {
        if (!message.guild || message.author?.bot) return;

        const embed = createArgusEmbed(message.guild.id, {
            title: '🗑️ Data Terminated',
            description: `**Source:** ${message.author}\n**Sector:** ${message.channel}\n**Content:** \`\`\`${message.content || '[ENCRYPTED_OR_EMPTY]'}\`\`\``,
            color: COLORS.DANGER,
            footer: 'Message Deletion Log'
        });

        await logToNexus(message.guild, embed);
    });

    // --- Message Edit ---
    client.on(Events.MessageUpdate, async (oldMsg, newMsg) => {
        if (!oldMsg.guild || oldMsg.author?.bot || oldMsg.content === newMsg.content) return;

        const embed = createArgusEmbed(oldMsg.guild.id, {
            title: '📝 Data Modified',
            description: `**Source:** ${oldMsg.author}\n**Sector:** ${oldMsg.channel}\n**Previous:** ${oldMsg.content}\n**Current:** ${newMsg.content}`,
            color: COLORS.WARNING,
            footer: 'Message Modification Log'
        });

        await logToNexus(oldMsg.guild, embed);
    });

    // --- Channel Monitoring ---
    client.on(Events.ChannelCreate, async (channel) => {
        if (!channel.guild) return;
        const embed = createArgusEmbed(channel.guild.id, {
            title: '📂 New Sector Created',
            description: `**Name:** ${channel.name}\n**Type:** ${channel.type}\n**ID:** \`${channel.id}\``,
            color: COLORS.SUCCESS,
            footer: 'Infrastructure Expansion'
        });
        await logToNexus(channel.guild, embed);
    });

    client.on(Events.ChannelDelete, async (channel) => {
        if (!channel.guild) return;
        const embed = createArgusEmbed(channel.guild.id, {
            title: '🚫 Sector Collapsed',
            description: `**Name:** ${channel.name}\n**ID:** \`${channel.id}\``,
            color: COLORS.DANGER,
            footer: 'Infrastructure Reduction'
        });
        await logToNexus(channel.guild, embed);
    });

    // --- Personnel Tracking ---
    client.on(Events.GuildMemberAdd, async (member) => {
        const embed = createArgusEmbed(member.guild.id, {
            title: '👤 Subject Integrated',
            description: `**Tag:** ${member.user.tag}\n**ID:** \`${member.id}\`\nInterpreting neural patterns...`,
            color: COLORS.NORMAL,
            footer: 'Personnel Entry'
        });
        await logToNexus(member.guild, embed);
    });

    client.on(Events.GuildMemberRemove, async (member) => {
        const embed = createArgusEmbed(member.guild.id, {
            title: '👥 Subject Severed',
            description: `**Tag:** ${member.user.tag}\n**ID:** \`${member.id}\`\nConnection lost.`,
            color: COLORS.WARNING,
            footer: 'Personnel Exit'
        });
        await logToNexus(member.guild, embed);
    });
}

module.exports = { setupLogger };
