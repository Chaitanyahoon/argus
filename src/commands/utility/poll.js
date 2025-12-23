const { SlashCommandBuilder } = require('discord.js');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('poll')
        .setDescription('Create a structured poll with up to 5 options.')
        .addStringOption(option => option.setName('question').setDescription('The question to ask').setRequired(true))
        .addStringOption(option => option.setName('option1').setDescription('Option 1').setRequired(true))
        .addStringOption(option => option.setName('option2').setDescription('Option 2').setRequired(true))
        .addStringOption(option => option.setName('option3').setDescription('Option 3'))
        .addStringOption(option => option.setName('option4').setDescription('Option 4'))
        .addStringOption(option => option.setName('option5').setDescription('Option 5')),
    async execute(interaction) {
        const question = interaction.options.getString('question');
        const options = [
            interaction.options.getString('option1'),
            interaction.options.getString('option2'),
            interaction.options.getString('option3'),
            interaction.options.getString('option4'),
            interaction.options.getString('option5'),
        ].filter(opt => opt !== null);

        const emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣'];
        let description = '';

        options.forEach((opt, index) => {
            description += `${emojis[index]} ${opt}\n`;
        });

        const embed = createArgusEmbed(interaction.guildId, {
            title: `📊 Poll: ${question}`,
            description: description,
            color: COLORS.NORMAL
        });

        const message = await interaction.reply({ embeds: [embed], fetchReply: true });

        for (let i = 0; i < options.length; i++) {
            await message.react(emojis[i]);
        }
    },
};
