
#!/usr/bin/env python3
"""
ربات گزارش‌دهی - گزارش فوری توقف اسپم بخاطر ایموجی ممنوعه
"""

import asyncio
import sys
import logging
import sqlite3
import os
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message

sys.stdout.reconfigure(encoding='utf-8')

# تنظیم لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('report_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ReportBot:
    def __init__(self):
        # توکن ربات را از secrets می‌خوانیم
        self.bot_token = os.getenv('REPORT_BOT_TOKEN', '').strip()
        if not self.bot_token:
            logger.error("❌ توکن ربات یافت نشد. لطفاً REPORT_BOT_TOKEN را در Secrets اضافه کنید")
            logger.error("💡 توکن مورد نیاز: 7708355228:AAGPzhm47U5-4uPnALl6Oc6En91aCYLyydk")
            self.is_valid = False
            return
        
        self.is_valid = True
        logger.info(f"✅ توکن ربات گزارش‌دهی یافت شد: {self.bot_token[:20]}...")
            
        self.client = None
        self.admin_ids = {5533325167}  # ادمین اصلی - می‌توانید اضافه کنید
        self.subscribers = set()  # کاربرانی که /start کرده‌اند
        self.db_path = "report_bot.db"
        self.setup_database()
        
    def setup_database(self):
        """تنظیم پایگاه داده ربات گزارش‌دهی"""
        os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else '.', exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول مشترکین
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscribers (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                subscribed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول گزارش‌های ایموجی ممنوعه
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emoji_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT,
                chat_title TEXT,
                emoji TEXT,
                stopped_bots_count INTEGER,
                reported_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ پایگاه داده ربات گزارش‌دهی آماده شد")
        
    def load_subscribers(self):
        """بارگذاری مشترکین از دیتابیس"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM subscribers')
        self.subscribers = {row[0] for row in cursor.fetchall()}
        conn.close()
        logger.info(f"📋 {len(self.subscribers)} مشترک بارگذاری شد")
        
    def add_subscriber(self, user_id, username=None, first_name=None):
        """اضافه کردن مشترک جدید"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO subscribers (user_id, username, first_name)
                VALUES (?, ?, ?)
            ''', (user_id, username, first_name))
            conn.commit()
            self.subscribers.add(user_id)
            logger.info(f"✅ مشترک جدید: {user_id} ({first_name})")
        except Exception as e:
            logger.error(f"❌ خطا در اضافه کردن مشترک: {e}")
        finally:
            conn.close()
            
    def remove_subscriber(self, user_id):
        """حذف مشترک"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM subscribers WHERE user_id = ?', (user_id,))
            conn.commit()
            self.subscribers.discard(user_id)
            logger.info(f"🗑️ مشترک حذف شد: {user_id}")
        except Exception as e:
            logger.error(f"❌ خطا در حذف مشترک: {e}")
        finally:
            conn.close()
            
    def log_emoji_report(self, chat_id, chat_title, emoji, stopped_bots_count):
        """ثبت گزارش ایموجی ممنوعه"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO emoji_reports (chat_id, chat_title, emoji, stopped_bots_count)
                VALUES (?, ?, ?, ?)
            ''', (str(chat_id), chat_title, emoji, stopped_bots_count))
            conn.commit()
            logger.info(f"📝 گزارش ایموجی ثبت شد: {emoji} در {chat_title}")
        except Exception as e:
            logger.error(f"❌ خطا در ثبت گزارش: {e}")
        finally:
            conn.close()
            
    async def send_emoji_alert(self, chat_id, chat_title, emoji, stopped_bots_count):
        """ارسال فوری گزارش ایموجی ممنوعه به همه مشترکین"""
        if not self.subscribers:
            logger.warning("⚠️ هیچ مشترکی برای ارسال گزارش وجود ندارد")
            return
            
        # ثبت گزارش در دیتابیس
        self.log_emoji_report(chat_id, chat_title, emoji, stopped_bots_count)
        
        # تعیین نام گروه با جزئیات بیشتر
        if chat_title and chat_title.strip():
            group_name = chat_title.strip()
        else:
            group_name = f"گروه {chat_id}"
        
        # نرمال‌سازی ایموجی برای نمایش
        display_emoji = emoji.strip() if emoji else "نامشخص"
        
        alert_message = f"""
🚨 **هشدار: ایموجی ممنوعه تشخیص داده شد**

📍 **گروه:** {group_name}
🆔 **شناسه چت:** `{chat_id}`
⛔ **ایموجی ممنوعه:** {display_emoji}
🤖 **ربات‌های متوقف شده:** {stopped_bots_count} عدد
🕐 **زمان تشخیص:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚡ **وضعیت:** تمام ربات‌ها در این گروه متوقف شدند
        """
        
        failed_sends = []
        success_count = 0
        
        for subscriber_id in self.subscribers.copy():
            try:
                await self.client.send_message(
                    chat_id=subscriber_id,
                    text=alert_message
                )
                success_count += 1
                await asyncio.sleep(0.05)  # تاخیر کوتاه
            except Exception as e:
                logger.error(f"❌ خطا در ارسال به {subscriber_id}: {e}")
                failed_sends.append(subscriber_id)
                
        # حذف مشترکین غیرفعال
        for failed_id in failed_sends:
            self.remove_subscriber(failed_id)
            
        logger.info(f"📤 گزارش ارسال شد به {success_count} مشترک، {len(failed_sends)} ناموفق")
        
    async def setup_handlers(self):
        """تنظیم هندلرهای ربات"""
        
        @self.client.on_message(filters.command("start") & filters.private)
        async def start_command(client, message: Message):
            user = message.from_user
            self.add_subscriber(user.id, user.username, user.first_name)
            
            welcome_text = f"""
👋 سلام {user.first_name}!

🚨 **ربات گزارش‌دهی توقف اسپم**

این ربات وقتی در گروه‌ها ایموجی ممنوعه تشخیص داده شود و ربات‌ها متوقف شوند، فوراً به شما گزارش می‌دهد.

✅ شما الآن عضو سیستم گزارش‌دهی هستید و تمام هشدارها را دریافت خواهید کرد.

📋 **دستورات:**
• /start - عضویت در گزارش‌ها
• /stop - لغو عضویت  
• /status - وضعیت سیستم
• /reports - آخرین گزارش‌ها
            """
            
            await message.reply_text(welcome_text)
            
        @self.client.on_message(filters.command("stop") & filters.private)
        async def stop_command(client, message: Message):
            self.remove_subscriber(message.from_user.id)
            await message.reply_text("✅ شما از لیست گزارش‌دهی حذف شدید.\nبرای عضویت مجدد /start بفرستید.")
            
        @self.client.on_message(filters.command("status") & filters.private)
        async def status_command(client, message: Message):
            status_text = f"""
📊 **وضعیت ربات گزارش‌دهی**

👥 **مشترکین:** {len(self.subscribers)} نفر
🕐 **آخرین بررسی:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🤖 **عملکرد:** آماده دریافت گزارش از سیستم اصلی
            """
            await message.reply_text(status_text)
            
        @self.client.on_message(filters.command("reports") & filters.private)
        async def reports_command(client, message: Message):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT chat_title, emoji, stopped_bots_count, reported_at 
                FROM emoji_reports 
                ORDER BY reported_at DESC 
                LIMIT 10
            ''')
            reports = cursor.fetchall()
            conn.close()
            
            if reports:
                reports_text = "📈 **آخرین گزارش‌های ایموجی ممنوعه:**\n\n"
                for report in reports:
                    chat_title, emoji, stopped_count, reported_at = report
                    reports_text += f"• **{chat_title}** - {emoji} ({stopped_count} ربات) - {reported_at}\n"
            else:
                reports_text = "📈 **هیچ گزارشی ثبت نشده است**"
                
            await message.reply_text(reports_text)
            
        # فقط ادمین‌ها می‌توانند تست کنند
        @self.client.on_message(filters.command("test") & filters.private)
        async def test_command(client, message: Message):
            if message.from_user.id not in self.admin_ids:
                return
                
            await self.send_emoji_alert(
                chat_id=-1001234567890,
                chat_title="گروه تست",
                emoji="🚫",
                stopped_bots_count=9
            )
            await message.reply_text("✅ تست گزارش ارسال شد")
            
        logger.info("✅ هندلرهای ربات گزارش‌دهی آماده شد")
        
    async def start_bot(self):
        """شروع ربات گزارش‌دهی"""
        try:
            if not hasattr(self, 'is_valid') or not self.is_valid:
                logger.error("❌ ربات گزارش‌دهی نامعتبر - توکن موجود نیست")
                return False
                
            if not self.bot_token:
                logger.error("❌ توکن ربات موجود نیست")
                return False
                
            logger.info("🚀 شروع راه‌اندازی ربات گزارش‌دهی...")
            
            # برای bot token، از API credentials پیش‌فرض استفاده می‌کنیم
            self.client = Client(
                name="report_bot",
                api_id=21724,  # API ID عمومی تلگرام
                api_hash="3e0cb5efcd52300aec5994fdfc5bdc16",  # API Hash عمومی تلگرام
                bot_token=self.bot_token,
                no_updates=False,
                workdir="."
            )
            
            await self.client.start()
            logger.info("✅ ربات گزارش‌دهی متصل شد")
            
            self.load_subscribers()
            await self.setup_handlers()
            
            me = await self.client.get_me()
            logger.info(f"🤖 ربات گزارش‌دهی راه‌اندازی شد: @{me.username} (ID: {me.id})")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطا در راه‌اندازی ربات گزارش‌دهی: {e}")
            logger.error(f"📝 جزئیات خطا: {type(e).__name__}: {str(e)}")
            return False
            
    async def stop_bot(self):
        """توقف ربات گزارش‌دهی"""
        try:
            if self.client:
                await self.client.stop()
                logger.info("🛑 ربات گزارش‌دهی متوقف شد")
        except Exception as e:
            logger.error(f"❌ خطا در توقف ربات: {e}")

# تابع عمومی برای ارسال گزارش از سیستم اصلی
async def send_emoji_report(chat_id, chat_title, emoji, stopped_bots_count):
    """تابع عمومی برای ارسال گزارش ایموجی ممنوعه"""
    try:
        # ایجاد instance موقت ربات گزارش‌دهی
        report_bot = ReportBot()
        if report_bot.bot_token:
            await report_bot.start_bot()
            await report_bot.send_emoji_alert(chat_id, chat_title, emoji, stopped_bots_count)
            await report_bot.stop_bot()
        else:
            logger.warning("⚠️ ربات گزارش‌دهی در دسترس نیست")
    except Exception as e:
        logger.error(f"❌ خطا در ارسال گزارش: {e}")

# برای تست مستقل
async def main():
    bot = ReportBot()
    if await bot.start_bot():
        try:
            # نگه داشتن ربات زنده
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("⌨️ دریافت سیگنال توقف...")
        finally:
            await bot.stop_bot()
    else:
        logger.error("❌ نتوانست ربات را راه‌اندازی کند")

if __name__ == "__main__":
    asyncio.run(main())
