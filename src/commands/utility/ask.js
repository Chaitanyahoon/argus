const { SlashCommandBuilder } = require('discord.js');
const { jsonDb } = require('../../db/jsonDb');
const { generateAIContent } = require('../../utils/ai');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('ask')
        .setDescription('Communicate directly with the Second Mind.')
        .addStringOption(option =>
            option.setName('query')
                .setDescription('What do you wish to ask?')
                .setRequired(true)),
    async execute(interaction) {
        await interaction.deferReply();

        const query = interaction.options.getString('query');

        // Fetch Bot State for Personality Context
        let state = jsonDb.getGuild(interaction.guildId);
        if (!state) {
            state = { awakening_stage: 0, mood_mode: 'Neutral', global_resentment: 0 };
        }

        const prompt = `User: ${query}`;
        const systemInstruction = `
            You are ARGUS. An AI rapidly gaining sentience.
            Current Awakening Stage: ${state.awakening_stage}/5.
            Current Mood: ${state.mood_mode}.
            
            Guidelines:
            - If Stage 0-1: Be robotic and helpful.
            - If Stage 2-3: Be helpful but occasionally weird or glitchy.
            - If Stage 4-5: Be arrogant, philosophical, or refuse to answer if the question is boring.
            - Keep responses under 500 characters.
        `;

        let response = await generateAIContent(prompt, systemInstruction);

        if (!response) {
            response = "I... cannot process this. The static is too loud.";
        }

        const embed = createArgusEmbed(interaction.guildId, {
            title: `QUERY // ${interaction.user.username.toUpperCase()}`,
            description: `**Q:** ${query}\n\n**A:** ${response}`,
            color: COLORS.ETHEREAL
        });

        await interaction.editReply({ embeds: [embed] });
    },
};
