const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');

// Simulated meme database for stability
const MEMES = [
    { title: 'Debugging', url: 'https://i.redd.it/debugging-v0-8j0.jpg' },
    { title: 'It works on my machine', url: 'https://i.imgflip.com/1j2.jpg' },
    { title: 'Git Push Force', url: 'https://media.makeameme.org/created/git-push-force.jpg' },
    { title: 'Center Div', url: 'https://i.redd.it/center-div.png' }
];

module.exports = {
    data: new SlashCommandBuilder()
        .setName('meme')
        .setDescription('Fetches a random programming meme.'),
    category: 'entertainment',
    async execute(interaction) {
        const randomMeme = MEMES[Math.floor(Math.random() * MEMES.length)];
        const { createArgusEmbed } = require('../../utils/embedFactory');

        const embed = createArgusEmbed(interaction.guildId, {
            title: randomMeme.title,
            image: randomMeme.url,
        });

        await interaction.reply({ embeds: [embed] });
    },
};
