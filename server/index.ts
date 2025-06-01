import express from 'express';
import { spawn } from 'child_process';
import path from 'path';

const app = express();
const PORT = parseInt(process.env.PORT || '3000');

// Store bot processes
const bots: any[] = [];

function startBot(botId: number) {
  const botPath = path.join(process.cwd(), 'bots', `bot${botId}`);
  
  console.log(`Starting Bot ${botId}...`);
  
  const botProcess = spawn('python3', ['main.py'], {
    cwd: botPath,
    stdio: ['inherit', 'pipe', 'pipe'],
    env: { ...process.env, BOT_ID: botId.toString() }
  });

  botProcess.stdout?.on('data', (data) => {
    const lines = data.toString().split('\n').filter((line: string) => line.trim());
    lines.forEach((line: string) => {
      console.log(`[Bot ${botId}] ${line}`);
    });
  });

  botProcess.stderr?.on('data', (data) => {
    const lines = data.toString().split('\n').filter((line: string) => line.trim());
    lines.forEach((line: string) => {
      console.error(`[Bot ${botId} ERROR] ${line}`);
    });
  });

  botProcess.on('close', (code) => {
    console.log(`[Bot ${botId}] Process exited with code ${code}`);
    
    const index = bots.findIndex(bot => bot.id === botId);
    if (index !== -1) {
      bots.splice(index, 1);
    }
    
    if (code !== 0) {
      console.log(`[Bot ${botId}] Restarting in 5 seconds...`);
      setTimeout(() => {
        startBot(botId);
      }, 5000);
    }
  });

  botProcess.on('error', (error) => {
    console.error(`[Bot ${botId}] Failed to start:`, error.message);
  });

  bots.push({
    id: botId,
    process: botProcess,
    startTime: new Date()
  });

  return botProcess;
}

// API routes
app.get('/', (req, res) => {
  res.json({ 
    message: 'Multi-Bot Manager is running',
    bots: bots.map(bot => ({
      id: bot.id,
      isRunning: !bot.process.killed,
      startTime: bot.startTime,
      pid: bot.process.pid
    }))
  });
});

app.get('/api/bots/status', (req, res) => {
  const runningBots = bots.filter(bot => !bot.process.killed);
  res.json({
    totalBots: bots.length,
    runningBots: runningBots.length,
    bots: bots.map(bot => ({
      id: bot.id,
      isRunning: !bot.process.killed,
      startTime: bot.startTime,
      pid: bot.process.pid
    }))
  });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🌐 Web server running on port ${PORT}`);
  console.log('🎯 Starting all bots with delays...');
  
  // Start bots 1, 2, and 3 with delays to prevent database conflicts
  for (let i = 1; i <= 3; i++) {
    setTimeout(() => {
      startBot(i);
    }, (i - 1) * 3000); // 3 second delay between each bot
  }
  
  console.log(`✅ Bot startup sequence initiated`);
});

// Handle shutdown
process.on('SIGTERM', () => {
  console.log('Shutting down...');
  bots.forEach(bot => {
    bot.process.kill('SIGTERM');
  });
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('Shutting down...');
  bots.forEach(bot => {
    bot.process.kill('SIGTERM');
  });
  process.exit(0);
});