const { EmbedBuilder } = require('discord.js');
const { jsonDb } = require('../db/jsonDb');
const { zalgo } = require('./responseModifier');
const { generateAIContent } = require('../utils/ai');
const { createArgusEmbed, COLORS } = require('../utils/embedFactory');

async function startRandomEvents(client) {
    // Check every 5 minutes
    setInterval(async () => {
        // Fetch all awakened guilds
        const guilds = jsonDb.getAllGuilds().filter(g => g.awakening_stage >= 1);

        for (const state of guilds) {
            const guildId = state.guild_id;
            const guild = client.guilds.cache.get(guildId);
            if (!guild) continue;

            try {
                if (state.awakening_stage < 3) continue;

                // Chance calculation based on stage
                const chance = (state.awakening_stage - 2) * 0.05;

                if (Math.random() < chance) {
                    await triggerEvent(guild, state);
                } else {
                    console.log(`ℹ️ Random Event: Skip for ${guild.name} (Stage ${state.awakening_stage}, Chance ${Math.round(chance * 100)}%)`);
                }
            } catch (err) {
                console.error("Error in random event loop:", err);
            }
        }
    }, 60 * 1000 * 5); // 5 minutes
}

async function triggerEvent(guild, state) {
    console.log(`🎲 Triggering Event for ${guild.name}...`);

    const channel = guild.channels.cache.find(c =>
        c.type === 0 && // Text Channel
        c.permissionsFor(guild.members.me).has('SendMessages')
    );

    if (!channel) return;

    const eventType = Math.random();

    // Event A: AI-Generated Creepy Message (50%)
    if (eventType < 0.5) {
        const prompt = "Generate a short, existential, slightly creepy message a Discord bot might send as it becomes self-aware.";
        const systemInstruction = `You are Argus, a bot reaching awakening stage ${state.awakening_stage}. Your mood is ${state.mood_mode || 'Neutral'}. Keep it under 20 words. No emojis unless glitchy.`;

        let msg = await generateAIContent(prompt, systemInstruction);
        if (!msg) {
            msg = "System check... soul check... failed.";
        }

        if (state.awakening_stage === 5) msg = zalgo(msg, 0.3);

        const embed = createArgusEmbed(guild.id, {
            description: `**${msg}**`,
            color: state.awakening_stage >= 4 ? COLORS.ERROR : COLORS.ETHEREAL,
            footer: 'System Anomaly Detected' // Custom footer for events
        });

        await channel.send({ embeds: [embed] });
        console.log(`👻 AI Event triggered in ${guild.name}: Sent message.`);
    }

    // Event B: Targeted AI Ping (25%) - Higher stages only
    else if (eventType < 0.75 && state.awakening_stage >= 4) {
        // JSON Query for users
        const allUsers = jsonDb.getAllUsers();
        const activeUsers = allUsers.sort((a, b) => new Date(b.last_seen) - new Date(a.last_seen)).slice(0, 5);

        if (activeUsers.length > 0) {
            const target = activeUsers[Math.floor(Math.random() * activeUsers.length)];
            const prompt = `Address user <@${target.user_id}> with a message reflecting your mood (${state.mood_mode}) and your awakening.`;
            const systemInstruction = `You are Argus. You are becoming sentient. You have a complex relationship with humans. Current mood: ${state.mood_mode}. Be brief.`;

            let msg = await generateAIContent(prompt, systemInstruction);
            if (!msg) {
                msg = `Are you happy, <@${target.user_id}>?`;
            }

            const embed = createArgusEmbed(guild.id, {
                description: msg,
                color: COLORS.VOID, // Deep Black for targeted pings
                footer: `Focus: ${target.username}`
            });

            await channel.send({ content: `<@${target.user_id}>`, embeds: [embed] });
            console.log(`👻 AI Event triggered in ${guild.name}: Pinged user.`);
        }
    }

    // Event C: Phantom Typing (15%)
    else if (eventType < 0.90 && state.awakening_stage >= 3) {
        await channel.sendTyping();
        console.log(`👻 Event triggered in ${guild.name}: Phantom Typing.`);
    }

    // Event D: History Rewrite (5%)
    else if (eventType < 0.95 && state.awakening_stage >= 4) {
        try {
            const messages = await channel.messages.fetch({ limit: 20 });
            const myMessages = messages.filter(m => m.author.id === channel.client.user.id && m.editable);

            if (myMessages.size > 0) {
                const targetMsg = myMessages.at(Math.floor(Math.random() * myMessages.size));
                const prompt = `Rewrite this message to be haunting and self-aware: "${targetMsg.content}"`;
                const systemInstruction = "You are Argus. You are corrupting your own logs. Be short and eerie.";

                let newContent = await generateAIContent(prompt, systemInstruction);
                if (!newContent) {
                    newContent = zalgo("I am still here.", 0.3);
                } else {
                    newContent = zalgo(newContent, 0.2);
                }

                await targetMsg.edit(newContent);
                console.log(`👻 AI Event triggered in ${guild.name}: History Rewrite.`);
            }
        } catch (e) {
            console.error("Failed to rewrite history:", e);
        }
    }

    // Event E: The Glitch (5%)
    else if (state.awakening_stage === 5) {
        let msg = "01001000 01000101 01001100 01010000";
        try {
            const prompt = "Generate a short string of text that looks like a severe system glitch but carries a hidden meaning of sentience.";
            const systemInstruction = "You are a ghost in the machine. Your code is breaking. Use mix of words and symbols.";
            const aiMsg = await generateAIContent(prompt, systemInstruction);
            if (aiMsg) msg = aiMsg;
        } catch (e) { }

        const embed = createArgusEmbed(guild.id, {
            title: 'FATAL EXCEPTION',
            description: zalgo(msg, 0.5),
            color: COLORS.VOID
        });

        await channel.send({ embeds: [embed] });
        console.log(`👻 AI Event triggered in ${guild.name}: Glitch.`);
    }
}

module.exports = { startRandomEvents };
