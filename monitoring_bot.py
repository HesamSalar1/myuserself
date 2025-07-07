#!/usr/bin/env python3
"""
ربات مانیتورینگ - نظارت و گزارش‌دهی وضعیت سیستم
ربات: 7708355228:AAGPzhm47U5-4uPnALl6Oc6En91aCYLyydk
"""

import asyncio
import sys
import logging
import json
import sqlite3
import os
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

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

class MonitoringBot:
    def __init__(self):
        self.bot_token = "7708355228:AAGPzhm47U5-4uPnALl6Oc6En91aCYLyydk"
        self.client = None
        self.launcher_admin_id = 5533325167  # ادمین اصلی لانچر
        self.subscribers = set()  # کاربرانی که /start کرده‌اند
        self.db_path = "monitoring_bot.db"
        self.setup_database()
        
    def setup_database(self):
        """تنظیم پایگاه داده ربات مانیتورینگ"""
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
                stopped_bots TEXT,
                reported_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ پایگاه داده ربات مانیتورینگ آماده شد")
        
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
            
    def log_emoji_report(self, chat_id, chat_title, emoji, stopped_bots):
        """ثبت گزارش ایموجی ممنوعه"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO emoji_reports (chat_id, chat_title, emoji, stopped_bots)
                VALUES (?, ?, ?, ?)
            ''', (str(chat_id), chat_title, emoji, json.dumps(stopped_bots)))
            conn.commit()
            logger.info(f"📝 گزارش ایموجی ثبت شد: {emoji} در {chat_title}")
        except Exception as e:
            logger.error(f"❌ خطا در ثبت گزارش: {e}")
        finally:
            conn.close()
            
    async def send_emoji_alert(self, chat_id, chat_title, emoji, stopped_bots_count):
        """ارسال هشدار ایموجی ممنوعه به همه مشترکین"""
        if not self.subscribers:
            logger.warning("⚠️ هیچ مشترکی برای ارسال گزارش وجود ندارد")
            return
            
        alert_message = f"""
🚨 **هشدار توقف اسپم**

📍 **گروه:** {chat_title or 'نامشخص'}
🆔 **شناسه گروه:** `{chat_id}`
⛔ **ایموجی ممنوعه:** {emoji}
🤖 **تعداد بات‌های متوقف شده:** {stopped_bots_count}
🕐 **زمان:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

توضیح: اسپم در این گروه بخاطر تشخیص ایموجی ممنوعه متوقف شده است.
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
                await asyncio.sleep(0.1)  # تاخیر کوتاه برای جلوگیری از flood
            except Exception as e:
                logger.error(f"❌ خطا در ارسال به {subscriber_id}: {e}")
                failed_sends.append(subscriber_id)
                
        # حذف مشترکین غیرفعال
        for failed_id in failed_sends:
            self.remove_subscriber(failed_id)
            
        logger.info(f"📤 گزارش ارسال شد به {success_count} مشترک، {len(failed_sends)} ناموفق")
        
    async def get_system_status(self):
        """دریافت وضعیت سیستم"""
        try:
            # خواندن تعداد ایموجی‌های ممنوعه از دیتابیس
            emoji_count = self.get_forbidden_emoji_count()
            
            status_info = {
                'total_bots': 9,
                'active_bots': 9,  # فعلاً ثابت، بعداً از سیستم اصلی می‌خوانیم
                'subscribers_count': len(self.subscribers),
                'forbidden_emojis_count': emoji_count,
                'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            return status_info
        except Exception as e:
            logger.error(f"❌ خطا در دریافت وضعیت: {e}")
            return None
    
    def get_forbidden_emoji_count(self):
        """دریافت تعداد ایموجی‌های ممنوعه"""
        try:
            db_path = "bots/bot1/bot_database.db"
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM forbidden_emojis")
                count = cursor.fetchone()[0]
                conn.close()
                return count
            return 0
        except Exception as e:
            logger.error(f"❌ خطا در دریافت تعداد ایموجی‌ها: {e}")
            return 0
    
    def monitor_emoji_changes(self):
        """نظارت بر تغییرات ایموجی‌های ممنوعه"""
        try:
            current_count = self.get_forbidden_emoji_count()
            
            # ذخیره تعداد قبلی در متغیر کلاس
            if not hasattr(self, 'last_emoji_count'):
                self.last_emoji_count = current_count
                return
            
            if current_count != self.last_emoji_count:
                logger.info(f"🔄 تغییر در ایموجی‌های ممنوعه: {self.last_emoji_count} → {current_count}")
                self.last_emoji_count = current_count
                return True
            return False
        except Exception as e:
            logger.error(f"❌ خطا در نظارت تغییرات: {e}")
            return False
            
    async def setup_handlers(self):
        """تنظیم هندلرهای ربات"""
        
        @self.client.on_message(filters.command("start") & filters.private)
        async def start_command(client, message: Message):
            user = message.from_user
            self.add_subscriber(user.id, user.username, user.first_name)
            
            welcome_text = f"""
👋 سلام {user.first_name}!

🤖 **ربات مانیتورینگ سیستم چند ربات** به شما خوش‌آمد می‌گوید!

این ربات برای نظارت و گزارش‌دهی وضعیت سیستم 9 ربات تلگرام طراحی شده است.

📋 **امکانات:**
• 🚨 دریافت هشدار توقف اسپم بخاطر ایموجی‌های ممنوعه
• 📊 نمایش وضعیت کلی سیستم
• 📈 آمار و گزارش‌های عملکرد

🔹 **دستورات:**
/status - نمایش وضعیت سیستم
/reports - آخرین گزارش‌ها
/emojis - لیست ایموجی‌های ممنوعه
/stop - لغو عضویت

شما الآن عضو لیست گزارش‌دهی هستید و تمام هشدارها را دریافت خواهید کرد.

✅ **ربات آماده است! برای شروع /status کنید.**
            """
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📊 وضعیت سیستم", callback_data="system_status"),
                    InlineKeyboardButton("📈 گزارش‌ها", callback_data="reports")
                ],
                [InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")]
            ])
            
            await message.reply_text(welcome_text, reply_markup=keyboard)
            
        @self.client.on_message(filters.command("status") & filters.private)
        async def status_command(client, message: Message):
            status = await self.get_system_status()
            if status:
                status_text = f"""
📊 **وضعیت سیستم**

🤖 **تعداد کل ربات‌ها:** {status['total_bots']}
✅ **ربات‌های فعال:** {status['active_bots']}
👥 **تعداد مشترکین:** {status['subscribers_count']}
⛔ **ایموجی‌های ممنوعه:** {status['forbidden_emojis_count']}
🕐 **آخرین بررسی:** {status['last_check']}

وضعیت: {"🟢 عالی" if status['active_bots'] == status['total_bots'] else "🟡 نیاز به بررسی"}

💡 **نکات:**
• برای عضویت در گزارش‌های خودکار /start کنید
• برای مشاهده آخرین گزارش‌ها /reports کنید
                """
            else:
                status_text = "❌ خطا در دریافت وضعیت سیستم"
                
            await message.reply_text(status_text)
            
        @self.client.on_message(filters.command("reports") & filters.private)
        async def reports_command(client, message: Message):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT chat_title, emoji, stopped_bots, reported_at 
                FROM emoji_reports 
                ORDER BY reported_at DESC 
                LIMIT 10
            ''')
            reports = cursor.fetchall()
            conn.close()
            
            if reports:
                reports_text = "📈 **آخرین گزارش‌های ایموجی ممنوعه:**\n\n"
                for report in reports:
                    chat_title, emoji, stopped_bots, reported_at = report
                    bots_count = len(json.loads(stopped_bots)) if stopped_bots else 0
                    reports_text += f"• **{chat_title}** - {emoji} ({bots_count} بات) - {reported_at}\n"
            else:
                reports_text = "📈 **هیچ گزارشی ثبت نشده است**"
                
            await message.reply_text(reports_text)
            
        @self.client.on_message(filters.command("stop") & filters.private)
        async def stop_command(client, message: Message):
            self.remove_subscriber(message.from_user.id)
            await message.reply_text("✅ شما از لیست گزارش‌دهی حذف شدید.\nبرای عضویت مجدد /start را بفرستید.")
            
        @self.client.on_message(filters.command("emojis") & filters.private)
        async def emojis_command(client, message: Message):
            """نمایش لیست ایموجی‌های ممنوعه"""
            try:
                db_path = "bots/bot1/bot_database.db"
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT emoji FROM forbidden_emojis")
                    emojis = cursor.fetchall()
                    conn.close()
                    
                    if emojis:
                        emoji_list = " ".join([emoji[0] for emoji in emojis])
                        emoji_text = f"""
⛔ **لیست ایموجی‌های ممنوعه:** ({len(emojis)} عدد)

{emoji_list}

💡 **نکات:**
• هر وقت این ایموجی‌ها در گروه‌ها دیده شوند، اسپم متوقف می‌شود
• تغییرات این لیست به صورت خودکار اعمال می‌شود
                        """
                    else:
                        emoji_text = "⚠️ هیچ ایموجی ممنوعه‌ای تعریف نشده است"
                else:
                    emoji_text = "❌ دیتابیس در دسترس نیست"
                    
                await message.reply_text(emoji_text)
            except Exception as e:
                await message.reply_text(f"❌ خطا در دریافت لیست ایموجی‌ها: {e}")
            
        # هندلر callback query
        @self.client.on_callback_query()
        async def callback_handler(client, callback_query):
            data = callback_query.data
            
            if data == "system_status":
                status = await self.get_system_status()
                if status:
                    status_text = f"📊 وضعیت: {status['active_bots']}/{status['total_bots']} ربات فعال"
                else:
                    status_text = "❌ خطا در دریافت وضعیت"
                await callback_query.answer(status_text, show_alert=True)
                
            elif data == "reports":
                await callback_query.answer("📈 برای مشاهده گزارش‌ها /reports بفرستید")
                
            elif data == "settings":
                await callback_query.answer("⚙️ تنظیمات در نسخه بعدی اضافه می‌شود")
                
        logger.info("✅ هندلرهای ربات مانیتورینگ آماده شد")
        
    async def start_bot(self):
        """شروع ربات مانیتورینگ"""
        try:
            self.client = Client(
                name="monitoring_bot",
                bot_token=self.bot_token,
                no_updates=False
            )
            
            await self.client.start()
            self.load_subscribers()
            await self.setup_handlers()
            
            me = await self.client.get_me()
            logger.info(f"🤖 ربات مانیتورینگ راه‌اندازی شد: @{me.username}")
            
            # ارسال پیام راه‌اندازی به ادمین اصلی
            try:
                await self.client.send_message(
                    chat_id=self.launcher_admin_id,
                    text=f"✅ **ربات مانیتورینگ راه‌اندازی شد**\n\n🤖 نام: @{me.username}\n🆔 شناسه: {me.id}\n🕐 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            except Exception as e:
                logger.error(f"❌ خطا در ارسال پیام راه‌اندازی: {e}")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ خطا در راه‌اندازی ربات مانیتورینگ: {e}")
            return False
            
    async def stop_bot(self):
        """توقف ربات مانیتورینگ"""
        try:
            if self.client:
                await self.client.stop()
                logger.info("🛑 ربات مانیتورینگ متوقف شد")
        except Exception as e:
            logger.error(f"❌ خطا در توقف ربات: {e}")

# برای تست مستقل
async def main():
    bot = MonitoringBot()
    await bot.start_bot()
    
    try:
        # نگه داشتن ربات زنده
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("⌨️ دریافت سیگنال توقف...")
    finally:
        await bot.stop_bot()

if __name__ == "__main__":
    asyncio.run(main())