#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ربات مانیتورینگ تلگرام - گزارش‌دهی فوری ایموجی‌های ممنوعه
توکن: 7708355228:AAGPzhm47U5-4uPnALl6Oc6En91aCYLyydk
"""

import asyncio
import logging
import sqlite3
import sys
from datetime import datetime
from typing import Set

# تنظیم encoding برای output
# تنظیم encoding برای خروجی
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# تنظیم لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Import Pyrogram
try:
    from pyrogram import Client, filters
    from pyrogram.types import Message
    logger.info("Pyrogram imported successfully")
except ImportError as e:
    logger.error(f"Failed to import Pyrogram: {e}")
    sys.exit(1)

class MonitoringBot:
    def __init__(self):
        """راه‌اندازی ربات مانیتورینگ"""
        self.bot_token = "7708355228:AAGPzhm47U5-4uPnALl6Oc6En91aCYLyydk"
        self.subscribers: Set[int] = set()
        self.client = None
        self.setup_database()
        self.load_subscribers()
        logger.info("Monitoring bot initialized")
    
    def setup_database(self):
        """تنظیم پایگاه داده ربات مانیتورینگ"""
        try:
            conn = sqlite3.connect('monitoring_bot.db')
            cursor = conn.cursor()
            
            # جدول مشترکین
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscribers (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول گزارش‌های ایموجی
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emoji_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT,
                    chat_title TEXT,
                    emoji TEXT,
                    stopped_bots_count INTEGER,
                    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database setup completed")
        except Exception as e:
            logger.error(f"Database setup error: {e}")
    
    def load_subscribers(self):
        """بارگذاری مشترکین از دیتابیس"""
        try:
            conn = sqlite3.connect('monitoring_bot.db')
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM subscribers')
            self.subscribers = {row[0] for row in cursor.fetchall()}
            conn.close()
            logger.info(f"Loaded {len(self.subscribers)} subscribers")
        except Exception as e:
            logger.error(f"Error loading subscribers: {e}")
    
    def add_subscriber(self, user_id: int, username: str = None, first_name: str = None):
        """اضافه کردن مشترک جدید"""
        try:
            conn = sqlite3.connect('monitoring_bot.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO subscribers (user_id, username, first_name)
                VALUES (?, ?, ?)
            ''', (user_id, username, first_name))
            conn.commit()
            conn.close()
            self.subscribers.add(user_id)
            logger.info(f"Added subscriber: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding subscriber: {e}")
            return False
    
    def remove_subscriber(self, user_id: int):
        """حذف مشترک"""
        try:
            conn = sqlite3.connect('monitoring_bot.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM subscribers WHERE user_id = ?', (user_id,))
            conn.commit()
            conn.close()
            self.subscribers.discard(user_id)
            logger.info(f"Removed subscriber: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing subscriber: {e}")
            return False
    
    def log_emoji_report(self, chat_id: str, chat_title: str, emoji: str, stopped_bots_count: int):
        """ثبت گزارش ایموجی ممنوعه"""
        try:
            conn = sqlite3.connect('monitoring_bot.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO emoji_reports (chat_id, chat_title, emoji, stopped_bots_count)
                VALUES (?, ?, ?, ?)
            ''', (chat_id, chat_title, emoji, stopped_bots_count))
            conn.commit()
            conn.close()
            logger.info(f"Logged emoji report: {emoji} in {chat_title}")
        except Exception as e:
            logger.error(f"Error logging emoji report: {e}")
    
    async def send_emoji_alert(self, chat_id: str, chat_title: str, emoji: str, stopped_bots_count: int):
        """ارسال فوری گزارش ایموجی ممنوعه به همه مشترکین"""
        if not self.client:
            logger.error("Bot client not initialized")
            return
        
        # ثبت گزارش در دیتابیس
        self.log_emoji_report(chat_id, chat_title, emoji, stopped_bots_count)
        
        # پیام گزارش
        alert_message = f"""
🚨 **هشدار ایموجی ممنوعه** 🚨

📍 **چت:** {chat_title}
🔸 **شناسه چت:** `{chat_id}`
❌ **ایموجی ممنوعه:** {emoji}
🤖 **ربات‌های متوقف شده:** {stopped_bots_count}
⏰ **زمان:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

تمام ربات‌های فعال در این چت متوقف شدند.
        """
        
        # ارسال به همه مشترکین
        failed_sends = []
        for user_id in self.subscribers.copy():
            try:
                await self.client.send_message(user_id, alert_message)
                logger.info(f"Alert sent to subscriber: {user_id}")
            except Exception as e:
                logger.error(f"Failed to send alert to {user_id}: {e}")
                failed_sends.append(user_id)
        
        # حذف مشترکینی که پیام ارسال نشد (احتمالاً ربات را بلاک کرده‌اند)
        for user_id in failed_sends:
            if "USER_IS_BLOCKED" in str(e) or "PEER_ID_INVALID" in str(e):
                self.remove_subscriber(user_id)
        
        logger.info(f"Emoji alert sent to {len(self.subscribers) - len(failed_sends)} subscribers")
    
    async def setup_handlers(self):
        """تنظیم هندلرهای ربات"""
        if not self.client:
            return
        
        @self.client.on_message(filters.command("start") & filters.private)
        async def start_command(client, message: Message):
            """دستور شروع - اضافه کردن کاربر به لیست مشترکین"""
            user = message.from_user
            success = self.add_subscriber(
                user.id,
                user.username,
                user.first_name
            )
            
            if success:
                await message.reply_text(f"""
🤖 **خوش آمدید به ربات مانیتورینگ!**

سلام {user.first_name}! شما با موفقیت در سیستم گزارش‌دهی ثبت شدید.

**قابلیت‌های ربات:**
🔔 گزارش فوری ایموجی‌های ممنوعه
📊 آمار و وضعیت ربات‌ها
📋 تاریخچه گزارش‌ها

**دستورات موجود:**
/start - شروع و عضویت
/stop - توقف گزارش‌ها
/status - وضعیت سیستم
/reports - آخرین گزارش‌ها
/test - تست سیستم گزارش‌دهی

شما اکنون تمام گزارش‌های ایموجی‌های ممنوعه را دریافت خواهید کرد.
                """)
            else:
                await message.reply_text("❌ خطا در ثبت‌نام. لطفاً دوباره تلاش کنید.")
        
        @self.client.on_message(filters.command("stop") & filters.private)
        async def stop_command(client, message: Message):
            """دستور توقف - حذف کاربر از لیست مشترکین"""
            success = self.remove_subscriber(message.from_user.id)
            
            if success:
                await message.reply_text("""
✅ **لغو عضویت موفق**

شما از سیستم گزارش‌دهی خارج شدید.
دیگر گزارش‌های ایموجی ممنوعه دریافت نخواهید کرد.

برای عضویت مجدد از دستور /start استفاده کنید.
                """)
            else:
                await message.reply_text("❌ خطا در لغو عضویت.")
        
        @self.client.on_message(filters.command("status") & filters.private)
        async def status_command(client, message: Message):
            """نمایش وضعیت سیستم"""
            await message.reply_text(f"""
📊 **وضعیت سیستم مانیتورینگ**

🔔 **مشترکین:** {len(self.subscribers)} نفر
🤖 **ربات:** فعال و آماده
📡 **اتصال:** برقرار
⏰ **آخرین بروزرسانی:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**عملکرد:**
✅ گزارش‌دهی ایموجی‌های ممنوعه
✅ نظارت بر 9 ربات اصلی
✅ ثبت تاریخچه رویدادها
            """)
        
        @self.client.on_message(filters.command("reports") & filters.private)
        async def reports_command(client, message: Message):
            """نمایش آخرین گزارش‌ها"""
            try:
                conn = sqlite3.connect('monitoring_bot.db')
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT chat_title, emoji, stopped_bots_count, reported_at
                    FROM emoji_reports
                    ORDER BY reported_at DESC
                    LIMIT 5
                ''')
                reports = cursor.fetchall()
                conn.close()
                
                if reports:
                    text = "📋 **آخرین گزارش‌های ایموجی ممنوعه:**\n\n"
                    for i, (chat_title, emoji, count, timestamp) in enumerate(reports, 1):
                        text += f"{i}. **{chat_title}**\n"
                        text += f"   ❌ ایموجی: {emoji}\n"
                        text += f"   🤖 ربات‌های متوقف: {count}\n"
                        text += f"   ⏰ زمان: {timestamp}\n\n"
                else:
                    text = "📋 هیچ گزارشی ثبت نشده است."
                
                await message.reply_text(text)
            except Exception as e:
                await message.reply_text(f"❌ خطا در دریافت گزارش‌ها: {e}")
        
        @self.client.on_message(filters.command("test") & filters.private)
        async def test_command(client, message: Message):
            """تست سیستم گزارش‌دهی"""
            await self.send_emoji_alert(
                "-1001234567890",
                "گروه تست",
                "⚡",
                9
            )
            await message.reply_text("✅ پیام تست ارسال شد!")
        
        logger.info("Handlers setup completed")
    
    async def start_bot(self):
        """شروع ربات مانیتورینگ"""
        try:
            # برای bot token، از API credentials معتبر استفاده می‌کنیم
            self.client = Client(
                "monitoring_bot",
                bot_token=self.bot_token,
                api_id=15508294,  # API ID معتبر تست شده
                api_hash="778e5cd56ffcf22c2d62aa963ce85a0c"  # API Hash معتبر تست شده
            )
            
            await self.setup_handlers()
            await self.client.start()
            
            me = await self.client.get_me()
            logger.info(f"Monitoring bot started: @{me.username}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to start monitoring bot: {e}")
            return False
    
    async def stop_bot(self):
        """توقف ربات مانیتورینگ"""
        try:
            if self.client:
                await self.client.stop()
                logger.info("Monitoring bot stopped")
        except Exception as e:
            logger.error(f"Error stopping monitoring bot: {e}")

# تابع عمومی برای ارسال گزارش از ربات‌های دیگر
async def send_emoji_report(chat_id: str, chat_title: str, emoji: str, stopped_bots_count: int):
    """تابع عمومی برای ارسال گزارش ایموجی ممنوعه از سایر بخش‌های سیستم"""
    try:
        bot = MonitoringBot()
        await bot.start_bot()
        await bot.send_emoji_alert(chat_id, chat_title, emoji, stopped_bots_count)
        await bot.stop_bot()
        logger.info(f"External emoji report sent: {emoji} in {chat_title}")
    except Exception as e:
        logger.error(f"Failed to send external emoji report: {e}")

async def main():
    """تابع اصلی"""
    logger.info("Starting monitoring bot...")
    
    bot = MonitoringBot()
    
    try:
        success = await bot.start_bot()
        if success:
            logger.info("Monitoring bot is running. Press Ctrl+C to stop.")
            await asyncio.Future()  # Run forever
        else:
            logger.error("Failed to start monitoring bot")
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await bot.stop_bot()

if __name__ == "__main__":
    asyncio.run(main())