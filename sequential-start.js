const { spawn } = require('child_process');
const path = require('path');

// Store bot processes
const bots = [];
let startupIndex = 0;

function startBotSequentially(botId) {
  return new Promise((resolve, reject) => {
    const botPath = path.join(__dirname, 'bots', `bot${botId}`);
    
    console.log(`[${new Date().toISOString()}] شروع بات ${botId}...`);
    
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
    let errorBuffer = '';

    // Handle stdout
    botProcess.stdout.on('data', (data) => {
      const output = data.toString();
      console.log(`[بات ${botId}] ${output.trim()}`);
      
      // Check for successful startup indicators
      if (output.includes('Started') || output.includes('Client initialized') || output.includes('البات آماده است')) {
        if (!startupComplete) {
          startupComplete = true;
          console.log(`[بات ${botId}] ✅ راه اندازی موفق`);
          resolve(botProcess);
        }
      }
    });

    // Handle stderr
    botProcess.stderr.on('data', (data) => {
      const error = data.toString();
      errorBuffer += error;
      console.error(`[بات ${botId} خطا] ${error.trim()}`);
    });

    // Handle process exit
    botProcess.on('close', (code) => {
      console.log(`[بات ${botId}] فرآیند با کد ${code} بسته شد`);
      
      // Remove from bots array
      const index = bots.findIndex(bot => bot.id === botId);
      if (index !== -1) {
        bots.splice(index, 1);
      }

      if (!startupComplete) {
        reject(new Error(`بات ${botId} قبل از راه اندازی کامل بسته شد. کد خروج: ${code}`));
      }
    });

    // Handle startup errors
    botProcess.on('error', (error) => {
      console.error(`[بات ${botId}] خطا در راه اندازی:`, error.message);
      if (!startupComplete) {
        reject(error);
      }
    });

    // Store bot info
    bots.push({
      id: botId,
      process: botProcess,
      startTime: new Date()
    });

    // Timeout after 30 seconds if bot doesn't start
    setTimeout(() => {
      if (!startupComplete) {
        console.log(`[بات ${botId}] ⚠️ راه اندازی کامل شد (تایم اوت)`);
        startupComplete = true;
        resolve(botProcess);
      }
    }, 30000);
  });
}

async function startAllBotsSequentially() {
  console.log('🚀 شروع راه اندازی ترتیبی بات ها...');
  
  for (let botId = 1; botId <= 3; botId++) {
    try {
      console.log(`\n📍 مرحله ${botId}: راه اندازی بات ${botId}`);
      await startBotSequentially(botId);
      
      // Wait 5 seconds before starting next bot
      if (botId < 3) {
        console.log(`⏱️ انتظار 5 ثانیه قبل از شروع بات بعدی...`);
        await new Promise(resolve => setTimeout(resolve, 5000));
      }
    } catch (error) {
      console.error(`❌ خطا در راه اندازی بات ${botId}:`, error.message);
      console.log(`🔄 ادامه با بات های بعدی...`);
    }
  }
  
  console.log(`\n✅ فرآیند راه اندازی کامل شد. تعداد بات های فعال: ${bots.length}/3`);
  
  // Start monitoring
  startMonitoring();
}

function startMonitoring() {
  setInterval(() => {
    const runningBots = bots.filter(bot => !bot.process.killed).length;
    console.log(`📊 وضعیت: ${runningBots}/${bots.length} بات در حال اجرا`);
    
    // Log individual bot status
    bots.forEach(bot => {
      const status = bot.process.killed ? 'متوقف' : 'فعال';
      const uptime = Math.floor((new Date() - bot.startTime) / 1000);
      console.log(`   بات ${bot.id}: ${status} (${uptime}s)`);
    });
  }, 60000); // Every minute
}

function stopAllBots() {
  console.log('🛑 متوقف کردن همه بات ها...');
  
  bots.forEach(bot => {
    if (!bot.process.killed) {
      console.log(`متوقف کردن بات ${bot.id}...`);
      bot.process.kill('SIGTERM');
    }
  });

  // Force kill after 10 seconds
  setTimeout(() => {
    bots.forEach(bot => {
      if (!bot.process.killed) {
        console.log(`کشتن اجباری بات ${bot.id}...`);
        bot.process.kill('SIGKILL');
      }
    });
  }, 10000);
}

// Handle shutdown signals
process.on('SIGTERM', () => {
  console.log('\n📴 دریافت SIGTERM، خاموش کردن...');
  stopAllBots();
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('\n📴 دریافت SIGINT، خاموش کردن...');
  stopAllBots();
  process.exit(0);
});

// Start the process
console.log('🎯 مدیر چند بات (ترتیبی) در حال شروع...');
startAllBotsSequentially();