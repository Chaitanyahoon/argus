require('dotenv').config();
console.log('DEBUG: TOKEN length =', process.env.TOKEN ? process.env.TOKEN.length : 'NULL/UNDEFINED');
const { Client, GatewayIntentBits, Collection } = require('discord.js');
const fs = require('fs');
const path = require('path');

// Initialize Client with necessary intents
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
    ]
});

client.commands = new Collection();

const commandHandler = require('./handlers/commandHandler');
const eventHandler = require('./handlers/eventHandler');

client.on('ready', async () => {
    console.log(`👁️ Argus System Online. Logged in as ${client.user.tag}`);

    // Start Nexus Logger
    const { setupLogger } = require('./systems/logger');
    setupLogger(client);

    // Start the Active Event Loop (Ghost in the machine)
    const { startRandomEvents } = require('./systems/randomEvents');
    startRandomEvents(client);

    // Start Status Rotation
    const { startStatusRotation } = require('./systems/status');
    startStatusRotation(client);
});

// Basic error handling to prevent crash on "glitch"
process.on('unhandledRejection', error => {
    console.error('Unhandled promise rejection:', error);
});

// Initialization function to await handlers
async function initialize() {
    try {
        console.log('🚀 Initializing Systems...');
        await commandHandler(client);
        await eventHandler(client);
        await client.login(process.env.TOKEN);
    } catch (error) {
        console.error('❌ Initialization failed:', error);
    }
}

// Keep-Alive Mechanism for Render/Replit
const http = require('http');
const PORT = process.env.PORT || 3000;
const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('Argus is awake. The eye is open.');
});
server.listen(PORT, () => {
    console.log(`🌐 Keep-Alive Server running on port ${PORT}`);
});

initialize();
