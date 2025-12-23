const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(process.cwd(), 'data');
const USERS_FILE = path.join(DATA_DIR, 'users.json');
const GUILDS_FILE = path.join(DATA_DIR, 'guilds.json');

// Ensure data directory and files exist
if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR);
}

function initFile(filePath, defaultData = []) {
    if (!fs.existsSync(filePath)) {
        fs.writeFileSync(filePath, JSON.stringify(defaultData, null, 4));
    }
}

initFile(USERS_FILE, []); // Users array
initFile(GUILDS_FILE, []); // Guilds array

// Helper to read data (Synchronous for simplicity in this context)
function readData(filePath) {
    try {
        const data = fs.readFileSync(filePath, 'utf8');
        return JSON.parse(data);
    } catch (err) {
        console.error(`Error reading ${filePath}:`, err);
        return [];
    }
}

// Helper to write data
function writeData(filePath, data) {
    try {
        fs.writeFileSync(filePath, JSON.stringify(data, null, 4));
    } catch (err) {
        console.error(`Error writing ${filePath}:`, err);
    }
}

const jsonDb = {
    // --- USER METHODS ---
    getUser: (userId) => {
        const users = readData(USERS_FILE);
        return users.find(u => u.user_id === userId);
    },

    setUser: (userId, newData) => {
        const users = readData(USERS_FILE);
        const index = users.findIndex(u => u.user_id === userId);

        if (index !== -1) {
            // Update existing (merge)
            users[index] = { ...users[index], ...newData };
        } else {
            // Create new
            users.push({ user_id: userId, ...newData });
        }
        writeData(USERS_FILE, users);
        return users.find(u => u.user_id === userId);
    },

    getAllUsers: () => {
        return readData(USERS_FILE);
    },

    // --- GUILD/BOT STATE METHODS ---
    getGuild: (guildId) => {
        const guilds = readData(GUILDS_FILE);
        return guilds.find(g => g.guild_id === guildId);
    },

    setGuild: (guildId, newData) => {
        const guilds = readData(GUILDS_FILE);
        const index = guilds.findIndex(g => g.guild_id === guildId);

        if (index !== -1) {
            guilds[index] = { ...guilds[index], ...newData };
        } else {
            guilds.push({ guild_id: guildId, ...newData });
        }
        writeData(GUILDS_FILE, guilds);
        return guilds.find(g => g.guild_id === guildId);
    },

    getAllGuilds: () => {
        return readData(GUILDS_FILE);
    }
};

module.exports = { jsonDb };
