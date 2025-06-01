const { spawn } = require('child_process');
const path = require('path');

class BotManager {
  constructor() {
    this.bots = [];
    this.isShuttingDown = false;
  }

  startBot(botId) {
    const botPath = path.join(__dirname, 'bots', `bot${botId}`);
    
    console.log(`🚀 Starting Bot ${botId}...`);
    
    const botProcess = spawn('node', ['index.js'], {
      cwd: botPath,
      stdio: ['inherit', 'pipe', 'pipe'],
      env: { ...process.env, BOT_ID: botId.toString() }
    });

    // Log bot output with prefix
    botProcess.stdout.on('data', (data) => {
      const lines = data.toString().split('\n').filter(line => line.trim());
      lines.forEach(line => {
        console.log(`[Bot ${botId}] ${line}`);
      });
    });

    botProcess.stderr.on('data', (data) => {
      const lines = data.toString().split('\n').filter(line => line.trim());
      lines.forEach(line => {
        console.error(`[Bot ${botId} ERROR] ${line}`);
      });
    });

    botProcess.on('close', (code) => {
      console.log(`[Bot ${botId}] Process exited with code ${code}`);
      
      // Remove from active bots list
      this.bots = this.bots.filter(bot => bot.id !== botId);
      
      // Restart bot if it wasn't a planned shutdown
      if (!this.isShuttingDown && code !== 0) {
        console.log(`[Bot ${botId}] Restarting in 5 seconds...`);
        setTimeout(() => {
          if (!this.isShuttingDown) {
            this.startBot(botId);
          }
        }, 5000);
      }
    });

    botProcess.on('error', (error) => {
      console.error(`[Bot ${botId}] Failed to start:`, error.message);
    });

    // Store bot info
    this.bots.push({
      id: botId,
      process: botProcess,
      startTime: new Date()
    });

    return botProcess;
  }

  startAllBots() {
    console.log('🔄 Starting all bots...');
    
    // Start bots 1, 2, and 3
    for (let i = 1; i <= 3; i++) {
      this.startBot(i);
    }

    console.log(`✅ Started ${this.bots.length} bots successfully`);
  }

  stopAllBots() {
    console.log('🛑 Stopping all bots...');
    this.isShuttingDown = true;

    this.bots.forEach(bot => {
      console.log(`Stopping Bot ${bot.id}...`);
      bot.process.kill('SIGTERM');
    });

    // Force kill after 10 seconds if needed
    setTimeout(() => {
      this.bots.forEach(bot => {
        if (!bot.process.killed) {
          console.log(`Force killing Bot ${bot.id}...`);
          bot.process.kill('SIGKILL');
        }
      });
    }, 10000);
  }

  getStatus() {
    return {
      totalBots: this.bots.length,
      runningBots: this.bots.filter(bot => !bot.process.killed).length,
      bots: this.bots.map(bot => ({
        id: bot.id,
        isRunning: !bot.process.killed,
        startTime: bot.startTime,
        pid: bot.process.pid
      }))
    };
  }
}

// Create bot manager instance
const botManager = new BotManager();

// Handle shutdown signals
process.on('SIGTERM', () => {
  console.log('📴 Received SIGTERM, shutting down...');
  botManager.stopAllBots();
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('📴 Received SIGINT, shutting down...');
  botManager.stopAllBots();
  process.exit(0);
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('❌ Uncaught Exception:', error);
  botManager.stopAllBots();
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ Unhandled Rejection at:', promise, 'reason:', reason);
  botManager.stopAllBots();
  process.exit(1);
});

// Start all bots
console.log('🎯 Multi-Bot Manager Starting...');
botManager.startAllBots();

// Status monitoring
setInterval(() => {
  const status = botManager.getStatus();
  console.log(`📊 Status: ${status.runningBots}/${status.totalBots} bots running`);
}, 30000); // Every 30 seconds

module.exports = botManager;