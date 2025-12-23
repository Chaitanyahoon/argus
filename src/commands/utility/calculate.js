const { SlashCommandBuilder } = require('discord.js');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('calculate')
        .setDescription('Perform basic mathematical operations.')
        .addStringOption(option =>
            option.setName('expression')
                .setDescription('The math expression to solve (e.g., 2+2, 10*5)')
                .setRequired(true)),
    async execute(interaction) {
        const expression = interaction.options.getString('expression');

        try {
            // Using a basic eval for simplicity, but restricting characters for safety
            // WARNING: In a real production app, use a math library like mathjs
            const safeExpression = expression.replace(/[^- +*/%().0-9]/g, '');
            const result = eval(safeExpression);

            if (result === undefined || result === null || isNaN(result)) {
                throw new Error('Invalid calculation');
            }

            const embed = createArgusEmbed(interaction.guildId, {
                title: '🔢 Calculation Result',
                description: `\`\`\`\n${expression} = ${result}\n\`\`\``,
                color: COLORS.NORMAL
            });

            await interaction.reply({ embeds: [embed] });
        } catch (error) {
            await interaction.reply({ content: "I cannot compute that. My logic circuits find it... illogical.", ephemeral: true });
        }
    },
};
