import express from 'express';
import { spawn } from 'child_process';
import path from 'path';

const app = express();
const PORT = parseInt(process.env.PORT || '3000');

// Store bot processes
const bots: any[] = [];

function startBotSequentially(botId: number): Promise<any> {
  return new Promise((resolve, reject) => {
    const botPath = path.join(process.cwd(), 'bots', `bot${botId}`);
    
    console.log(`Starting Bot ${botId}...`);
    
    const botProcess = spawn('python3', ['main.py'], {
      cwd: botPath,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { 
        ...process.env, 
        BOT_ID: botId.toString(),
        PYTHONUNBUFFERED: '1'
      }
    });

    let startupComplete = false;

    botProcess.stdout?.on('data', (data) => {
      const output = data.toString();
      console.log(`[Bot ${botId}] ${output.trim()}`);
      
      if ((output.includes('Started') || output.includes('Client initialized')) && !startupComplete) {
        startupComplete = true;
        console.log(`[Bot ${botId}] ✅ Successfully started`);
        resolve(botProcess);
      }
    });

    botProcess.stderr?.on('data', (data) => {
      const error = data.toString();
      console.error(`[Bot ${botId} ERROR] ${error.trim()}`);
    });

    botProcess.on('close', (code) => {
      console.log(`[Bot ${botId}] Process exited with code ${code}`);
      
      const index = bots.findIndex(bot => bot.id === botId);
      if (index !== -1) {
        bots.splice(index, 1);
      }

      if (!startupComplete) {
        reject(new Error(`Bot ${botId} closed before complete startup. Exit code: ${code}`));
      }
    });

    botProcess.on('error', (error) => {
      console.error(`[Bot ${botId}] Failed to start:`, error.message);
      if (!startupComplete) {
        reject(error);
      }
    });

    bots.push({
      id: botId,
      process: botProcess,
      startTime: new Date()
    });

    // Timeout after 30 seconds
    setTimeout(() => {
      if (!startupComplete) {
        console.log(`[Bot ${botId}] ⚠️ Startup timeout, assuming success`);
        startupComplete = true;
        resolve(botProcess);
      }
    }, 30000);
  });
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

async function startAllBotsSequentially() {
  console.log('🚀 Starting bots sequentially...');
  
  // Start only Bot 1 first to test
  try {
    console.log(`\n📍 Stage 1: Starting Bot 1`);
    await startBotSequentially(1);
    console.log(`✅ Bot 1 started successfully`);
    
    // Wait and start Bot 2
    console.log(`⏱️ Waiting 10 seconds before starting Bot 2...`);
    await new Promise(resolve => setTimeout(resolve, 10000));
    
    console.log(`\n📍 Stage 2: Starting Bot 2`);
    await startBotSequentially(2);
    console.log(`✅ Bot 2 started successfully`);
    
    // Wait and start Bot 3
    console.log(`⏱️ Waiting 10 seconds before starting Bot 3...`);
    await new Promise(resolve => setTimeout(resolve, 10000));
    
    console.log(`\n📍 Stage 3: Starting Bot 3`);
    await startBotSequentially(3);
    console.log(`✅ Bot 3 started successfully`);
    
  } catch (error) {
    console.error(`❌ Error in startup process:`, error);
  }
  
  console.log(`\n✅ Startup process completed. Active bots: ${bots.length}/3`);
}

// Start server
app.listen(PORT, '0.0.0.0', async () => {
  console.log(`🌐 Web server running on port ${PORT}`);
  await startAllBotsSequentially();
});

// Handle shutdown
function stopAllBots() {
  console.log('Stopping all bots...');
  bots.forEach(bot => {
    if (!bot.process.killed) {
      bot.process.kill('SIGTERM');
    }
  });
}

process.on('SIGTERM', () => {
  console.log('Shutting down...');
  stopAllBots();
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('Shutting down...');
  stopAllBots();
  process.exit(0);
});