const { spawn } = require('child_process');
const path = require('path');

// مدیریت فرآیندهای بات
const bots = [];

function startBot(botId) {
  const botPath = path.join(__dirname, 'bots', `bot${botId}`);
  
  console.log(`شروع بات ${botId}...`);
  
  const botProcess = spawn('python3', ['main.py'], {
    cwd: botPath,
    stdio: ['inherit', 'pipe', 'pipe'],
    env: { ...process.env, BOT_ID: botId.toString() }
  });

  // نمایش خروجی بات با پیشوند
  botProcess.stdout.on('data', (data) => {
    const lines = data.toString().split('\n').filter(line => line.trim());
    lines.forEach(line => {
      console.log(`[بات ${botId}] ${line}`);
    });
  });

  botProcess.stderr.on('data', (data) => {
    const lines = data.toString().split('\n').filter(line => line.trim());
    lines.forEach(line => {
      console.error(`[بات ${botId} خطا] ${line}`);
    });
  });

  botProcess.on('close', (code) => {
    console.log(`[بات ${botId}] فرآیند با کد ${code} بسته شد`);
    
    // حذف از لیست بات‌های فعال
    const index = bots.findIndex(bot => bot.id === botId);
    if (index !== -1) {
      bots.splice(index, 1);
    }
    
    // راه‌اندازی مجدد اگر خطای غیرمنتظره باشد
    if (code !== 0) {
      console.log(`[بات ${botId}] راه‌اندازی مجدد در 5 ثانیه...`);
      setTimeout(() => {
        startBot(botId);
      }, 5000);
    }
  });

  botProcess.on('error', (error) => {
    console.error(`[بات ${botId}] خطا در راه‌اندازی:`, error.message);
  });

  // ذخیره اطلاعات بات
  bots.push({
    id: botId,
    process: botProcess,
    startTime: new Date()
  });

  return botProcess;
}

function stopAllBots() {
  console.log('متوقف کردن همه بات‌ها...');

  bots.forEach(bot => {
    console.log(`متوقف کردن بات ${bot.id}...`);
    bot.process.kill('SIGTERM');
  });

  // کشتن اجباری بعد از ۱۰ ثانیه در صورت نیاز
  setTimeout(() => {
    bots.forEach(bot => {
      if (!bot.process.killed) {
        console.log(`کشتن اجباری بات ${bot.id}...`);
        bot.process.kill('SIGKILL');
      }
    });
  }, 10000);
}

// مدیریت سیگنال‌های خاموشی
process.on('SIGTERM', () => {
  console.log('دریافت SIGTERM، خاموش کردن...');
  stopAllBots();
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('دریافت SIGINT، خاموش کردن...');
  stopAllBots();
  process.exit(0);
});

// شروع همه بات‌ها
console.log('🎯 مدیر چند بات در حال شروع...');
console.log('راه‌اندازی بات‌ها...');

// شروع بات‌های ۱، ۲ و ۳
for (let i = 1; i <= 3; i++) {
  startBot(i);
}

console.log(`✅ ${bots.length} بات با موفقیت راه‌اندازی شدند`);

// نمایش وضعیت هر ۳۰ ثانیه
setInterval(() => {
  const runningBots = bots.filter(bot => !bot.process.killed).length;
  console.log(`📊 وضعیت: ${runningBots}/${bots.length} بات در حال اجرا`);
}, 30000);