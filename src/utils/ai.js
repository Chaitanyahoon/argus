const { GoogleGenerativeAI } = require("@google/generative-ai");

// Rate limiting configuration
// Gemini Flash 1.5 free tier is typically 15 RPM
const MAX_REQUESTS = 15; // Max requests per window
const WINDOW_MS = 60000; // 1 minute window

class RateLimiter {
    constructor() {
        this.requests = [];
    }

    isLimited() {
        const now = Date.now();
        // Remove requests outside the window
        this.requests = this.requests.filter(timestamp => now - timestamp < WINDOW_MS);

        if (this.requests.length >= MAX_REQUESTS) {
            return true;
        }

        this.requests.push(now);
        return false;
    }

    getRetryAfter() {
        if (this.requests.length === 0) return 0;
        const oldest = this.requests[0];
        const wait = WINDOW_MS - (Date.now() - oldest);
        return Math.max(0, Math.ceil(wait / 1000));
    }
}

const limiter = new RateLimiter();
const genAI = process.env.GEMINI_API_KEY ? new GoogleGenerativeAI(process.env.GEMINI_API_KEY) : null;

async function generateAIContent(prompt, systemInstruction = "") {
    if (!genAI) {
        return null;
    }

    if (limiter.isLimited()) {
        console.warn(`🚀 AI Rate Limited. Retrying after ${limiter.getRetryAfter()}s`);
        return null;
    }

    try {
        const model = genAI.getGenerativeModel({
            model: "gemini-flash-latest",
            systemInstruction: systemInstruction
        });

        const result = await model.generateContent(prompt);
        const response = await result.response;
        return response.text();
    } catch (error) {
        console.error("❌ Gemini API Error:", error.message);
        return null;
    }
}

module.exports = { generateAIContent };
