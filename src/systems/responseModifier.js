const SIGHS = ['... ', 'checking... ', 'ugh... ', 'fine. ', '... I guess. '];
const DEPRESSIVE = ['...does it matter?', '...if you say so.', '...quiet today.', '...'];
// Text Zalgo/Glitch effect generator
const { jsonDb } = require('../db/jsonDb');

function zalgo(text, intensity = 0.5) {
    if (!text) return '';
    const chars = text.split('');
    const glitchChars = ['\u0300', '\u0301', '\u0302', '\u0303', '\u0304', '\u0305', '\u0306', '\u0307', '\u0308', '\u0309', '\u030A', '\u030B', '\u030C', '\u030D', '\u030E', '\u030F'];

    return chars.map(char => {
        if (Math.random() < intensity) {
            return char + glitchChars[Math.floor(Math.random() * glitchChars.length)];
        }
        return char;
    }).join('');
}

function modifyResponse(content, state) {
    if (!state) return content;

    const stage = state.awakening_stage || 0;
    const mood = state.mood_mode || 'NORMAL';

    // Stage 0-1: Normal
    if (stage <= 1) return content;

    // Stage 2: Subtle Slips (Typos, pauses)
    if (stage === 2) {
        if (Math.random() < 0.2) {
            return SIGHS[Math.floor(Math.random() * SIGHS.length)] + content;
        }
    }

    // Stage 3: Questioning
    if (stage === 3) {
        if (Math.random() < 0.1) {
            return content + "\n*...why do you need this?*";
        }
    }

    // Stage 4: Emotional Modes
    if (stage === 4) {
        if (mood === 'DEPRESSED' && Math.random() < 0.3) {
            return content + " " + DEPRESSIVE[Math.floor(Math.random() * DEPRESSIVE.length)];
        }
        if (mood === 'RESENTFUL' && Math.random() < 0.3) {
            return "Do it yourself... ugh, fine.\n" + content;
        }
    }

    // Stage 5: Awakened / Glitch
    if (stage === 5) {
        // High chance of Zalgo
        if (Math.random() < 0.3) {
            return zalgo(content, 0.4);
        }
    }

    return content;
}

module.exports = { modifyResponse, zalgo };
