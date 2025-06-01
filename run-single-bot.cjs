const { spawn } = require('child_process');
const path = require('path');

const botId = process.argv[2] || '1';
const botPath = path.join(__dirname, 'bots', `bot${botId}`);

console.log(`راه‌اندازی بات ${botId}...`);

const botProcess = spawn('python3', ['main.py'], {
  cwd: botPath,
  stdio: 'inherit',
  env: { 
    ...process.env, 
    BOT_ID: botId,
    PYTHONUNBUFFERED: '1'
  }
});

botProcess.on('close', (code) => {
  console.log(`بات ${botId} با کد ${code} بسته شد`);
  process.exit(code);
});

botProcess.on('error', (error) => {
  console.error(`خطا در راه‌اندازی بات ${botId}:`, error);
  process.exit(1);
});

// مدیریت سیگنال‌های خاموشی
process.on('SIGTERM', () => {
  console.log(`خاموش کردن بات ${botId}...`);
  botProcess.kill('SIGTERM');
});

process.on('SIGINT', () => {
  console.log(`خاموش کردن بات ${botId}...`);
  botProcess.kill('SIGINT');
});