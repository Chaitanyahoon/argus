const { SlashCommandBuilder } = require('discord.js');
const { createArgusEmbed, COLORS } = require('../../utils/embedFactory');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('remind')
        .setDescription('Set a reminder for yourself.')
        .addStringOption(option =>
            option.setName('time')
                .setDescription('Time in minutes (e.g., 5, 60)')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('message')
                .setDescription('What should I remind you about?')
                .setRequired(true)),
    async execute(interaction) {
        const timeInput = interaction.options.getString('time');
        const message = interaction.options.getString('message');
        const minutes = parseInt(timeInput);

        if (isNaN(minutes) || minutes <= 0) {
            return await interaction.reply({ content: "Time must be a positive number of minutes.", ephemeral: true });
        }

        const embed = createArgusEmbed(interaction.guildId, {
            title: '⏰ Reminder Set',
            description: `I will remind you about "**${message}**" in **${minutes}** minutes.`,
            color: COLORS.NORMAL
        });

        await interaction.reply({ embeds: [embed], ephemeral: true });

        setTimeout(async () => {
            try {
                await interaction.user.send({
                    content: `🔔 **Reminder from Argus:** ${message}`
                });
            } catch (err) {
                // If DMs are closed, try to ping in the channel
                await interaction.channel.send({
                    content: `🔔 <@${interaction.user.id}>, you asked me to remind you: ${message}`
                });
            }
        }, minutes * 60000);
    },
};
