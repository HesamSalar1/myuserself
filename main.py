import json
import asyncio
import sys
import sqlite3
import logging
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

from pyrogram import Client, filters

from pyrogram.types import Message, ChatMember
from pyrogram.errors import FloodWait, UserNotParticipant, ChatWriteForbidden
from random import choice

# تنظیمات اصلی
api_id = 15508294
api_hash = "778e5cd56ffcf22c2d62aa963ce85a0c"
admin_id = 7850529246

import os
import sys
import asyncio
import logging
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import subprocess
import signal
import time

# تنظیم encoding برای خروجی
sys.stdout.reconfigure(encoding='utf-8')

# تنظیم لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multi_bot_manager.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MultiBotManager:
    def __init__(self):
        self.bot_processes = {}
        self.running = False
        self.bot_dirs = [f"bots/bot{i}" for i in range(1, 10)]

    def start_single_bot(self, bot_dir):
        """شروع یک بات در پروسه جداگانه"""
        try:
            bot_id = bot_dir.split('/')[-1]
            logger.info(f"🚀 شروع {bot_id}...")

            # بررسی وجود فایل main.py
            main_py_path = os.path.join(bot_dir, 'main.py')
            if not os.path.exists(main_py_path):
                logger.warning(f"⚠️ {main_py_path} موجود نیست - رد شد")
                return None

            # تنظیم متغیر محیط برای شناسه بات
            env = os.environ.copy()
            env['BOT_ID'] = bot_id.replace('bot', '')
            env['PYTHONUNBUFFERED'] = '1'

            # اجرای پروسه
            process = subprocess.Popen(
                [sys.executable, 'main.py'],
                cwd=bot_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            # ذخیره پروسه
            self.bot_processes[bot_id] = {
                'process': process,
                'start_time': time.time(),
                'directory': bot_dir
            }

            logger.info(f"✅ {bot_id} با PID {process.pid} شروع شد")
            return process

        except Exception as e:
            logger.error(f"❌ خطا در شروع {bot_id}: {e}")
            return None

    def monitor_bot_output(self, bot_id, process):
        """مانیتورینگ خروجی بات"""
        try:
            while self.running and process.poll() is None:
                # خواندن stdout
                if process.stdout:
                    line = process.stdout.readline()
                    if line:
                        logger.info(f"[{bot_id}] {line.strip()}")

                # خواندن stderr
                if process.stderr:
                    error_line = process.stderr.readline()
                    if error_line:
                        logger.error(f"[{bot_id} خطا] {error_line.strip()}")

                time.sleep(0.1)

        except Exception as e:
            logger.error(f"خطا در مانیتورینگ {bot_id}: {e}")

    async def start_all_bots(self):
        """شروع همه بات‌ها به صورت موازی"""
        self.running = True
        logger.info("🎯 شروع مدیر چندگانه بات...")

        # شروع همه بات‌ها
        started_bots = 0
        for bot_dir in self.bot_dirs:
            if os.path.exists(bot_dir):
                process = self.start_single_bot(bot_dir)
                if process:
                    started_bots += 1
                    # تاخیر کوتاه بین شروع بات‌ها
                    await asyncio.sleep(2)

        logger.info(f"📊 {started_bots} بات از {len(self.bot_dirs)} بات شروع شدند")

        # مانیتورینگ همه بات‌ها
        monitor_tasks = []
        for bot_id, bot_info in self.bot_processes.items():
            task = asyncio.create_task(
                self.async_monitor_bot(bot_id, bot_info['process'])
            )
            monitor_tasks.append(task)

        # اجرای مانیتورینگ
        if monitor_tasks:
            await asyncio.gather(*monitor_tasks, return_exceptions=True)

    async def async_monitor_bot(self, bot_id, process):
        """مانیتورینگ غیرهمزمان بات"""
        try:
            while self.running and process.poll() is None:
                await asyncio.sleep(5)

                # بررسی وضعیت
                if process.poll() is not None:
                    exit_code = process.returncode
                    logger.warning(f"⚠️ {bot_id} متوقف شد با کد {exit_code}")

                    # حذف از لیست
                    if bot_id in self.bot_processes:
                        del self.bot_processes[bot_id]

                    # راه‌اندازی مجدد در صورت خطا
                    if exit_code != 0 and self.running:
                        logger.info(f"🔄 راه‌اندازی مجدد {bot_id} در 10 ثانیه...")
                        await asyncio.sleep(10)
                        bot_dir = next((d for d in self.bot_dirs if bot_id in d), None)
                        if bot_dir:
                            self.start_single_bot(bot_dir)
                    break

        except Exception as e:
            logger.error(f"خطا در مانیتورینگ غیرهمزمان {bot_id}: {e}")

    def stop_all_bots(self):
        """متوقف کردن همه بات‌ها"""
        logger.info("🛑 متوقف کردن همه بات‌ها...")
        self.running = False

        for bot_id, bot_info in self.bot_processes.items():
            try:
                process = bot_info['process']
                logger.info(f"متوقف کردن {bot_id} (PID: {process.pid})")

                # ارسال SIGTERM
                process.terminate()

                # انتظار 5 ثانیه برای بسته شدن نرمال
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # اگر بسته نشد، kill کن
                    logger.warning(f"⚡ kill اجباری {bot_id}")
                    process.kill()
                    process.wait()

                logger.info(f"✅ {bot_id} متوقف شد")

            except Exception as e:
                logger.error(f"خطا در متوقف کردن {bot_id}: {e}")

        self.bot_processes.clear()
        logger.info("🏁 تمام بات‌ها متوقف شدند")

    def get_status(self):
        """دریافت وضعیت همه بات‌ها"""
        status = {
            'total_bots': len(self.bot_dirs),
            'running_bots': len(self.bot_processes),
            'bots': []
        }

        for bot_id, bot_info in self.bot_processes.items():
            uptime = time.time() - bot_info['start_time']
            status['bots'].append({
                'id': bot_id,
                'pid': bot_info['process'].pid,
                'uptime': f"{uptime:.1f}s",
                'directory': bot_info['directory']
            })

        return status

# مدیر کلی
manager = MultiBotManager()

def signal_handler(signum, frame):
    """مدیریت سیگنال‌های سیستم"""
    logger.info(f"📴 دریافت سیگنال {signum}")
    manager.stop_all_bots()
    sys.exit(0)

# تنظیم signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """تابع اصلی"""
    try:
        print("="*60)
        print("🤖 مدیر مرکزی بات‌های تلگرام")
        print("="*60)
        print("🎯 شروع همه بات‌ها...")
        print("📍 برای متوقف کردن: Ctrl+C")
        print("="*60)

        # نمایش آمار هر 30 ثانیه
        async def show_periodic_status():
            while manager.running:
                await asyncio.sleep(30)
                if manager.running:
                    status = manager.get_status()
                    logger.info(f"📊 وضعیت: {status['running_bots']}/{status['total_bots']} بات فعال")

        # شروع نمایش آمار موازی
        status_task = asyncio.create_task(show_periodic_status())

        # شروع همه بات‌ها
        await manager.start_all_bots()

        # لغو تسک آمار
        status_task.cancel()

    except KeyboardInterrupt:
        logger.info("🔴 متوقف شدن با Ctrl+C")
    except Exception as e:
        logger.error(f"❌ خطای غیرمنتظره: {e}")
    finally:
        manager.stop_all_bots()

if __name__ == "__main__":
    asyncio.run(main())
```