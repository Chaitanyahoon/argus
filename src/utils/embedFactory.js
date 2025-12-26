const { EmbedBuilder } = require('discord.js');

const { zalgo } = require('../systems/responseModifier');

// Argus Premium Palette (Cyber/Ethereal)
const COLORS = {
    NORMAL: 0x00F7FF,   // Neon Cyan (Core Systems)
    SUCCESS: 0x00FF9D,  // Neon Green (Success)
    WARNING: 0xFFD600,  // Cyber Gold (Warning)
    ERROR: 0xFF0055,    // Glitch Red (Critical Failure)
    VOID: 0x090014,     // Deep Void (Stage 5 / Dark Mode)
    ETHEREAL: 0x9D00FF  // Electric Violet (Mystery/Lore)
};

function createArgusEmbed(guildId, { title, description, color, fields, image, thumbnail, footer }) {
    const embed = new EmbedBuilder();
    let finalColor = color || COLORS.NORMAL;
    let finalTitle = title;
    let finalFooterText = footer || 'Argus System // Dev: Iconic';
    let finalFooterIcon = 'https://i.imgur.com/vM7LhZq.png'; // Default Icon

    // Attempt to fetch state synchronously isn't possible with Mongoose 
    // We will assume state is passed or we default to basic behavior if not async
    // NOTE: This factory is synchronous, but MongoDB is async. 
    // For a factory, we usually can't await DB. 
    // Compromise: We use the passed color/footer if provided, 
    // or rely on the calling command to fetch state if it wants dynamic corruption.

    // However, if we really want global corruption effects without every command querying DB,
    // we would need to cache state or make this async. 
    // For now, we stick to the premium visuals and let specific commands (like /ask) handle logic.

    // Apply specific Glitch Aesthetics if color is VOID (Stage 5 indicator)
    if (finalColor === COLORS.VOID) {
        if (Math.random() < 0.3 && finalTitle) finalTitle = zalgo(finalTitle, 0.3);
        finalFooterText = 'N O   C O N T R O L';
    }

    if (finalTitle) embed.setTitle(finalTitle);
    if (description) embed.setDescription(description);

    embed.setColor(finalColor);

    // Modern "Card" Style Line
    // embed.setAuthor({ name: 'ARGUS', iconURL: 'https://i.imgur.com/vM7LhZq.png' });

    if (fields) embed.addFields(fields);
    if (image) embed.setImage(image);
    if (thumbnail) embed.setThumbnail(thumbnail);

    embed.setFooter({ text: finalFooterText, iconURL: finalFooterIcon });
    embed.setTimestamp();

    return embed;
}

module.exports = { createArgusEmbed, COLORS };
