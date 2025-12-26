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

const glitchText = (text, intensity = 0.3) => zalgo(text, intensity);

function createArgusEmbed(guildId, { title, description, color, fields, image, thumbnail, footer, glitchIntensity = 0 }) {
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

    // Apply Glitch Aesthetics if intensity is provided or if color is VOID (Stage 5)
    const effectiveIntensity = glitchIntensity || (finalColor === COLORS.VOID ? 0.3 : 0);

    if (effectiveIntensity > 0) {
        if (finalTitle) finalTitle = glitchText(finalTitle, effectiveIntensity);
        if (description) description = glitchText(description, effectiveIntensity * 0.5); // Less intense for body
        if (finalColor === COLORS.VOID) finalFooterText = 'N O   C O N T R O L';
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

module.exports = { createArgusEmbed, COLORS, glitchText };
