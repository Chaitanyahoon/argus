function createProgressBar(current, total, length = 15) {
    const progress = Math.min(Math.max(current / total, 0), 1);
    const filledLength = Math.round(length * progress);
    const emptyLength = length - filledLength;

    const filledBar = '█'.repeat(filledLength);
    const emptyBar = '░'.repeat(emptyLength);

    // Aesthetic percentage display
    const percent = Math.round(progress * 100);
    return `\`${filledBar}${emptyBar}\` **${percent}%**`;
}

module.exports = { createProgressBar };
