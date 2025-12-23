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
    // --- Message Delete ---
    client.on(Events.MessageDelete, async (message) => {
        if (!message.guild || message.author?.bot) return;

        const embed = createArgusEmbed(message.guild.id, {
            title: '🗑️ Message Terminated',
            description: `**Author:** ${message.author}\n**Channel:** ${message.channel}\n**Content:** \`\`\`${message.content || '[No Content]'}\`\`\``,
            color: COLORS.ERROR
        });

        await logToNexus(message.guild, embed);
    });

    // --- Message Update (Edit) ---
    client.on(Events.MessageUpdate, async (oldMessage, newMessage) => {
        if (!oldMessage.guild || oldMessage.author?.bot || oldMessage.content === newMessage.content) return;

        const embed = createArgusEmbed(oldMessage.guild.id, {
            title: '📝 Message Modified',
            description: `**Author:** ${oldMessage.author}\n**Channel:** ${oldMessage.channel}\n**Before:** ${oldMessage.content}\n**After:** ${newMessage.content}`,
            color: COLORS.WARNING
        });

        await logToNexus(oldMessage.guild, embed);
    });

    // --- Member Join ---
    client.on(Events.GuildMemberAdd, async (member) => {
        const embed = createArgusEmbed(member.guild.id, {
            title: '👋 New Subject Observed',
            description: `**Member:** ${member.user.tag}\n**ID:** ${member.id}\nWelcome to the collective.`,
            color: COLORS.NORMAL
        });

        await logToNexus(member.guild, embed);
    });
}

module.exports = { setupLogger };
