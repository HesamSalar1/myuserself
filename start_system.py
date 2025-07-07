#!/usr/bin/env python3
"""
سیستم راه‌اندازی کامل
شروع همزمان پنل وب و ربات‌های تلگرام
"""

import asyncio
import subprocess
import signal
import sys
import os
import time
import logging
from unified_bot_launcher import UnifiedBotLauncher

# تنظیم لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SystemLauncher:
    def __init__(self):
        self.bot_launcher = None
        self.web_process = None
        self.running = False
        
    async def start_web_panel(self):
        """شروع پنل وب"""
        try:
            logger.info("🌐 شروع پنل مدیریت وب...")
            
            # شروع سرور Express/Vite
            self.web_process = subprocess.Popen(
                ['npm', 'run', 'dev'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # انتظار برای راه‌اندازی سرور
            await asyncio.sleep(5)
            
            if self.web_process.poll() is None:
                logger.info("✅ پنل وب راه‌اندازی شد - http://localhost:5000")
                return True
            else:
                stdout, stderr = self.web_process.communicate()
                logger.error(f"❌ خطا در راه‌اندازی پنل وب:")
                logger.error(f"stdout: {stdout.decode()}")
                logger.error(f"stderr: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"❌ خطا در شروع پنل وب: {e}")
            return False
    
    async def start_bot_system(self):
        """شروع سیستم ربات‌ها"""
        try:
            logger.info("🤖 شروع سیستم ربات‌های تلگرام...")
            
            self.bot_launcher = UnifiedBotLauncher()
            await self.bot_launcher.start_all_bots()
            
            logger.info("✅ سیستم ربات‌ها راه‌اندازی شد")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطا در شروع سیستم ربات‌ها: {e}")
            return False
    
    async def start_system(self):
        """شروع کل سیستم"""
        self.running = True
        logger.info("🚀 شروع سیستم کامل مدیریت ربات‌های تلگرام...")
        
        # شروع پنل وب در پس‌زمینه
        web_task = asyncio.create_task(self.start_web_panel())
        
        # شروع سیستم ربات‌ها
        bot_task = asyncio.create_task(self.start_bot_system())
        
        # انتظار برای راه‌اندازی هر دو
        web_result = await web_task
        bot_result = await bot_task
        
        if web_result and bot_result:
            logger.info("🎉 سیستم کامل راه‌اندازی شد!")
            logger.info("📊 پنل مدیریت: http://localhost:5000")
            logger.info("🤖 ربات‌ها: 9 ربات اصلی + 1 ربات مانیتورینگ")
            return True
        else:
            logger.error("❌ خطا در راه‌اندازی کامل سیستم")
            await self.stop_system()
            return False
    
    async def stop_system(self):
        """توقف کل سیستم"""
        logger.info("🛑 توقف سیستم...")
        self.running = False
        
        # توقف ربات‌ها
        if self.bot_launcher:
            try:
                await self.bot_launcher.stop_all_bots()
                logger.info("✅ ربات‌ها متوقف شدند")
            except Exception as e:
                logger.error(f"❌ خطا در توقف ربات‌ها: {e}")
        
        # توقف پنل وب
        if self.web_process:
            try:
                self.web_process.terminate()
                try:
                    self.web_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.web_process.kill()
                    self.web_process.wait()
                logger.info("✅ پنل وب متوقف شد")
            except Exception as e:
                logger.error(f"❌ خطا در توقف پنل وب: {e}")
        
        logger.info("🏁 سیستم کاملاً متوقف شد")
    
    async def run_forever(self):
        """اجرای دائمی سیستم"""
        try:
            if await self.start_system():
                logger.info("⏳ سیستم در حال اجرا... (Ctrl+C برای توقف)")
                
                # نمایش وضعیت دوره‌ای
                async def show_status():
                    while self.running:
                        await asyncio.sleep(300)  # هر 5 دقیقه
                        if self.running:
                            logger.info("💡 سیستم فعال - پنل: http://localhost:5000")
                
                status_task = asyncio.create_task(show_status())
                
                # انتظار برای سیگنال توقف
                try:
                    await asyncio.Event().wait()
                except KeyboardInterrupt:
                    logger.info("⌨️ سیگنال توقف دریافت شد...")
                finally:
                    status_task.cancel()
                    await self.stop_system()
        except Exception as e:
            logger.error(f"❌ خطا در اجرای سیستم: {e}")
            await self.stop_system()

def signal_handler(signum, frame):
    """مدیریت سیگنال‌های سیستم"""
    logger.info(f"🔔 سیگنال {signum} دریافت شد - توقف سیستم...")
    sys.exit(0)

async def main():
    """تابع اصلی"""
    # تنظیم signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    launcher = SystemLauncher()
    
    try:
        await launcher.run_forever()
    except KeyboardInterrupt:
        logger.info("⌨️ دریافت سیگنال توقف...")
    except Exception as e:
        logger.error(f"❌ خطا در سیستم: {e}")
    finally:
        await launcher.stop_system()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⌨️ سیستم متوقف شد")
    except Exception as e:
        logger.error(f"❌ خطای کلی: {e}")
        sys.exit(1)