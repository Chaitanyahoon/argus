const Database = require('better-sqlite3');
const path = require('path');
const dbPath = path.resolve(__dirname, 'bot_memory.sqlite');
const db = new Database(dbPath);

console.log('--- BOT STATE ---');
const botState = db.prepare('SELECT * FROM bot_state').all();
console.log(JSON.stringify(botState, null, 2));

console.log('\n--- USER MEMORY (Recent) ---');
const userMemory = db.prepare('SELECT * FROM user_memory ORDER BY last_seen DESC LIMIT 5').all();
console.log(JSON.stringify(userMemory, null, 2));
