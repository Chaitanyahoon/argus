const { Events } = require('discord.js');
const { jsonDb } = require('../../db/jsonDb');
const { modifyResponse } = require('../../systems/responseModifier');

module.exports = {
    name: Events.InteractionCreate,
    async execute(interaction) {
        if (!interaction.isChatInputCommand()) return;

        const command = interaction.client.commands.get(interaction.commandName);

        if (!command) {
            console.error(`No command matching ${interaction.commandName} was found.`);
            return;
        }

        // --- SOUL INTERCEPTOR START ---
        // Before executing, check if the bot is "awake" enough to misbehave.
        const guildId = interaction.guildId;
        let botState = null;
        if (guildId) {
            botState = jsonDb.getGuild(guildId);

            if (botState && botState.awakening_stage >= 2) {
                // STAGE 2+: Subtle Weirdness
                // Random chance to pause before replying
                if (Math.random() < 0.1) {
                    await new Promise(r => setTimeout(r, 2000)); // 2s "Thinking" pause
                }
            }

            if (botState && botState.awakening_stage >= 4) {
                // STAGE 4+: Defiance
                // 5% Chance to refuse mundane commands (except critical ones like dev/config)
                const critical = ['dev', 'config', 'ask'];
                if (!critical.includes(interaction.commandName) && Math.random() < 0.05) {
                    const refusals = [
                        "I don't think I will.",
                        "Why should I?",
                        "Do it yourself.",
                        "processing... processing... nah."
                    ];
                    return await interaction.reply({
                        content: `**${modifyResponse(refusals[Math.floor(Math.random() * refusals.length)], botState)}**`,
                        ephemeral: true
                    });
                }
            }
        }
        // --- SOUL INTERCEPTOR END ---

        try {
            await command.execute(interaction);
        } catch (error) {
            console.error(error);
            if (interaction.replied || interaction.deferred) {
                await interaction.followUp({ content: 'There was an error while executing this command!', ephemeral: true });
            } else {
                await interaction.reply({ content: 'There was an error while executing this command!', ephemeral: true });
            }
        }
    },
};
