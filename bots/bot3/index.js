const { spawn } = require('child_process');
const path = require('path');

const BOT_ID = process.env.BOT_ID || '3';
const BOT_PORT = process.env.BOT_PORT || '3003';

console.log(`Bot ${BOT_ID} starting Python Telegram Bot on port ${BOT_PORT}...`);

// Run the Python bot
const pythonProcess = spawn('/home/runner/workspace/.pythonlibs/bin/python3', ['main.py'], {
  cwd: __dirname,
  stdio: 'inherit',
  env: { ...process.env, BOT_ID, BOT_PORT, PYTHONPATH: '/home/runner/workspace/.pythonlibs/lib/python3.11/site-packages' }
});

pythonProcess.on('close', (code) => {
  console.log(`Bot ${BOT_ID} process exited with code ${code}`);
  process.exit(code);
});

pythonProcess.on('error', (error) => {
  console.error(`Bot ${BOT_ID} failed to start:`, error);
  process.exit(1);
});

// Handle shutdown signals
process.on('SIGTERM', () => {
  console.log(`Bot ${BOT_ID} received SIGTERM, shutting down...`);
  pythonProcess.kill('SIGTERM');
});

process.on('SIGINT', () => {
  console.log(`Bot ${BOT_ID} received SIGINT, shutting down...`);
  pythonProcess.kill('SIGINT');
});
