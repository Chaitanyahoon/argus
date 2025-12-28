const fs = require('fs');
const path = require('path');

const locales = {};
const localesDir = path.join(__dirname, '../locales');

// Load all locale files
fs.readdirSync(localesDir).forEach(file => {
    if (file.endsWith('.json')) {
        const lang = file.split('.')[0];
        locales[lang] = require(path.join(localesDir, file));
    }
});

/**
 * Translates a key based on the provided locale.
 * @param {string} locale - The Discord locale string (e.g., 'en-US').
 * @param {string} keyPath - The path to the translation key (e.g., 'ping.title').
 * @param {Object} placeholders - Key-value pairs for placeholders.
 * @returns {string} - The translated string.
 */
function t(locale, keyPath, placeholders = {}) {
    const lang = locale.split('-')[0]; // Simplify 'en-US' to 'en'
    const dict = locales[lang] || locales['en']; // Fallback to English

    let text = keyPath.split('.').reduce((obj, key) => obj && obj[key], dict);

    if (!text) return keyPath; // Return the key if not found

    // Replace placeholders
    Object.keys(placeholders).forEach(key => {
        text = text.replace(new RegExp(`{${key}}`, 'g'), placeholders[key]);
    });

    return text;
}

module.exports = { t };
