const fs = require('fs');
const path = require('path');

const BOT_ID = process.env.BOT_ID || '2';
const BOT_PORT = process.env.BOT_PORT || '3002';

console.log(`Bot ${BOT_ID} starting on port ${BOT_PORT}...`);

// Simulate bot initialization
setTimeout(() => {
  console.log(`Bot ${BOT_ID} initialized successfully`);
  console.log(`Bot ${BOT_ID} connected to account @bot_account_${BOT_ID}`);
}, 1500);

// Simulate periodic activity
setInterval(() => {
  const activities = [
    'Processing messages',
    'Checking for updates',
    'Sending heartbeat',
    'Handling user requests',
    'Performing maintenance tasks'
  ];
  
  const activity = activities[Math.floor(Math.random() * activities.length)];
  console.log(`Bot ${BOT_ID}: ${activity}`);
}, 35000);

// Keep the process running
process.on('SIGTERM', () => {
  console.log(`Bot ${BOT_ID} received SIGTERM, shutting down gracefully...`);
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log(`Bot ${BOT_ID} received SIGINT, shutting down gracefully...`);
  process.exit(0);
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error(`Bot ${BOT_ID} uncaught exception:`, error);
  process.exit(1);
});

console.log(`Bot ${BOT_ID} is now running. PID: ${process.pid}`);
