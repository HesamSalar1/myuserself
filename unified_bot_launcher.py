import json
import asyncio
import sys
import sqlite3
import logging
from datetime import datetime
import os
from pathlib import Path
from random import choice

sys.stdout.reconfigure(encoding='utf-8')

from pyrogram import Client, filters
from pyrogram.types import Message, ChatMember
from pyrogram.errors import FloodWait, UserNotParticipant, ChatWriteForbidden

# تنظیم لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unified_bots.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class UnifiedBotLauncher:
    def __init__(self):
        self.bots = {}
        # متغیرهای کنترل
        self.running = False
        self.count_tasks = {}  # برای ذخیره تسک‌های شمارش
        self.global_paused = {}  # برای توقف کلی {chat_id: user_id} - وقتی ایموجی ممنوعه تشخیص داده شه
        self.continuous_spam_tasks = {}  # برای نگه داشتن تسک‌های فحش مداوم {bot_id: {user_id: task}}
        
        # تنظیمات تاخیر فحش برای هر بات (ثانیه)
        self.bot_spam_delays = {i: 1.0 for i in range(1, 10)}  # تاخیر پیش‌فرض: 1 ثانیه
        
        # ایموجی‌های ممنوعه (مدیریت کامل توسط ادمین از طریق کامندها)
        self.forbidden_emojis = set()
        
        # ایموجی‌های ممنوعه از دیتابیس در startup بارگذاری می‌شوند
        
        # کامندهای ممنوعه فقط برای دشمنان
        self.enemy_forbidden_commands = ['/catch', '/grab', '/guess', '/arise', '/take', '/secure']

        # ادمین اصلی لانچر (کنترل همه بات‌ها)
        self.launcher_admin_id = 5533325167
        
        # تنظیمات بات‌ها
        self.bot_configs = {
            1: {
                'api_id': 23700094,
                'api_hash': "7cd6b0ba9c5b1a5f21b8b76f1e2b8e40",
                'session_name': "bots/bot1/my_bot1",
                'db_path': "bots/bot1/bot1_data.db",
                'log_path': "bots/bot1/bot1.log",
                'admin_id': 7850529246,  # ادمین اصلی بات 1
                'auto_reply_enabled': True
            },
            2: {
                'api_id': 29262538,
                'api_hash': "0417ebf26dbd92d3455d51595f2c923c",
                'session_name': "bots/bot2/my_bot2",
                'db_path': "bots/bot2/bot2_data.db",
                'log_path': "bots/bot2/bot2.log",
                'admin_id': 7419698159,  # ادمین اصلی بات 2
                'auto_reply_enabled': True
            },
            3: {
                'api_id': 21555907,
                'api_hash': "16f4e09d753bc4b182434d8e37f410cd",
                'session_name': "bots/bot3/my_bot3",
                'db_path': "bots/bot3/bot3_data.db",
                'log_path': "bots/bot3/bot3.log",
                'admin_id': 7607882302,  # ادمین اصلی بات 3
                'auto_reply_enabled': True
            },
            4: {
                'api_id': 15508294,
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot4/my_bot4",
                'db_path': "bots/bot4/bot4_data.db",
                'log_path': "bots/bot4/bot4.log",
                'admin_id': 7739974888,  # ادمین اصلی بات 4
                'auto_reply_enabled': True
            },
            5: {
                'api_id': 15508294,
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot5/my_bot5",
                'db_path': "bots/bot5/bot5_data.db",
                'log_path': "bots/bot5/bot5.log",
                'admin_id': 7346058093,  # ادمین اصلی بات 5
                'auto_reply_enabled': True
            },
            6: {
                'api_id': 15508294,
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot6/my_bot6",
                'db_path': "bots/bot6/bot6_data.db",
                'log_path': "bots/bot6/bot6.log",
                'admin_id': 7927398744,  # ادمین اصلی بات 6
                'auto_reply_enabled': True
            },
            7: {
                'api_id': 15508294,
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot7/my_bot7",
                'db_path': "bots/bot7/bot7_data.db",
                'log_path': "bots/bot7/bot7.log",
                'admin_id': 8092847456,  # ادمین اصلی بات 7
                'auto_reply_enabled': True
            },
            8: {
                'api_id': 15508294,
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot8/my_bot8",
                'db_path': "bots/bot8/bot8_data.db",
                'log_path': "bots/bot8/bot8.log",
                'admin_id': 7220521953,  # ادمین اصلی بات 8
                'auto_reply_enabled': True
            },
            9: {
                'api_id': 15508294,
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot9/my_bot9",
                'db_path': "bots/bot9/bot9_data.db",
                'log_path': "bots/bot9/bot9.log",
                'admin_id': 7143723023,  # ادمین اصلی بات 9
                'auto_reply_enabled': True
            }
        }

        # لیست همه admin_id های بات‌ها (بدون ادمین لانچر)
        self.bot_admin_ids = {config['admin_id'] for config in self.bot_configs.values()}
        
        # لیست کامل همه ادمین‌ها (شامل ادمین لانچر + ادمین‌های بات‌ها)
        self.all_admin_ids = self.bot_admin_ids | {self.launcher_admin_id}
        
        logger.info(f"👑 ادمین اصلی لانچر: {self.launcher_admin_id}")
        logger.info(f"🔐 ادمین‌های بات‌ها: {list(self.bot_admin_ids)}")
        logger.info(f"📋 همه ادمین‌ها: {list(self.all_admin_ids)}")

    def setup_database(self, bot_id, db_path):
        """تنظیم پایگاه داده برای هر بات"""
        try:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # ایجاد جداول مورد نیاز
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fosh_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fosh TEXT,
                    media_type TEXT,
                    file_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enemy_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS friend_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS friend_words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT,
                    media_type TEXT,
                    file_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS action_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_type TEXT NOT NULL,
                    user_id INTEGER,
                    details TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # جدول جدید برای ایموجی‌های ممنوعه (مشترک بین همه بات‌ها)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS forbidden_emojis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    emoji TEXT UNIQUE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول تنظیمات تاخیر فحش
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS spam_delay_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    delay_seconds REAL NOT NULL DEFAULT 1.0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # اگر تنظیمات تاخیر وجود ندارد، مقدار پیش‌فرض را وارد کن
            cursor.execute('SELECT COUNT(*) FROM spam_delay_settings')
            if cursor.fetchone()[0] == 0:
                cursor.execute('INSERT INTO spam_delay_settings (delay_seconds) VALUES (1.0)')

            conn.commit()
            conn.close()
            logger.info(f"✅ پایگاه داده بات {bot_id} آماده شد")

        except Exception as e:
            logger.error(f"❌ خطا در تنظیم پایگاه داده بات {bot_id}: {e}")

    # توابع مدیریت پایگاه داده
    def add_fosh(self, bot_id, fosh=None, media_type=None, file_id=None):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO fosh_list (fosh, media_type, file_id) VALUES (?, ?, ?)", 
                          (fosh, media_type, file_id))
            conn.commit()
            result = True
        except Exception as e:
            logger.error(f"خطا در اضافه کردن فحش بات {bot_id}: {e}")
            result = False
        conn.close()
        return result

    def remove_fosh(self, bot_id, fosh):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fosh_list WHERE fosh = ?", (fosh,))
        result = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return result

    def get_fosh_list(self, bot_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT fosh, media_type, file_id FROM fosh_list")
        result = cursor.fetchall()
        conn.close()
        return result

    def clear_fosh_list(self, bot_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fosh_list")
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count

    def add_enemy(self, bot_id, user_id, username=None, first_name=None):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM friend_list WHERE user_id = ?", (user_id,))
            cursor.execute("INSERT INTO enemy_list (user_id, username, first_name) VALUES (?, ?, ?)", 
                          (user_id, username, first_name))
            conn.commit()
            result = True
        except sqlite3.IntegrityError:
            result = False
        conn.close()
        return result

    def remove_enemy(self, bot_id, user_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM enemy_list WHERE user_id = ?", (user_id,))
        result = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return result

    def get_enemy_list(self, bot_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, first_name, created_at FROM enemy_list")
        result = cursor.fetchall()
        conn.close()
        return result

    def clear_enemy_list(self, bot_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM enemy_list")
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count

    def add_friend(self, bot_id, user_id, username=None, first_name=None):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM enemy_list WHERE user_id = ?", (user_id,))
            cursor.execute("INSERT INTO friend_list (user_id, username, first_name) VALUES (?, ?, ?)", 
                          (user_id, username, first_name))
            conn.commit()
            result = True
        except sqlite3.IntegrityError:
            result = False
        conn.close()
        return result

    def remove_friend(self, bot_id, user_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM friend_list WHERE user_id = ?", (user_id,))
        result = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return result

    def get_friend_list(self, bot_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, first_name, created_at FROM friend_list")
        result = cursor.fetchall()
        conn.close()
        return result

    def clear_friend_list(self, bot_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM friend_list")
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count

    def add_friend_word(self, bot_id, word=None, media_type=None, file_id=None):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO friend_words (word, media_type, file_id) VALUES (?, ?, ?)", 
                          (word, media_type, file_id))
            conn.commit()
            result = True
        except Exception as e:
            logger.error(f"خطا در اضافه کردن کلمه بات {bot_id}: {e}")
            result = False
        conn.close()
        return result

    def remove_friend_word(self, bot_id, word):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM friend_words WHERE word = ?", (word,))
        result = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return result

    def get_friend_words(self, bot_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT word, media_type, file_id FROM friend_words")
        result = cursor.fetchall()
        conn.close()
        return result

    def clear_friend_words(self, bot_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM friend_words")
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count

    def log_action(self, bot_id, action_type, user_id=None, details=None):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO action_log (action_type, user_id, details) VALUES (?, ?, ?)", 
                      (action_type, user_id, details))
        conn.commit()
        conn.close()

    def get_stats(self, bot_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM fosh_list")
        fosh_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM enemy_list")
        enemy_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM friend_list")
        friend_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM friend_words")
        word_count = cursor.fetchone()[0]

        conn.close()

        return {
            'fosh_count': fosh_count,
            'enemy_count': enemy_count,
            'friend_count': friend_count,
            'word_count': word_count
        }

    def add_forbidden_emoji_to_db(self, emoji):
        """اضافه کردن ایموجی ممنوعه به دیتابیس (از بات 1)"""
        db_path = self.bot_configs[1]['db_path']  # استفاده از دیتابیس بات 1 برای ذخیره مشترک
        
        # اطمینان از وجود دیتابیس و جدول
        self.setup_database(1, db_path)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO forbidden_emojis (emoji) VALUES (?)", (emoji,))
            conn.commit()
            result = True
        except sqlite3.IntegrityError:
            result = False  # ایموجی از قبل وجود دارد
        except Exception as e:
            logger.error(f"خطا در اضافه کردن ایموجی ممنوعه: {e}")
            result = False
        conn.close()
        return result

    def remove_forbidden_emoji_from_db(self, emoji):
        """حذف ایموجی ممنوعه از دیتابیس"""
        db_path = self.bot_configs[1]['db_path']
        
        # اطمینان از وجود دیتابیس و جدول
        self.setup_database(1, db_path)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM forbidden_emojis WHERE emoji = ?", (emoji,))
        result = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return result

    def load_forbidden_emojis_from_db(self):
        """بارگذاری ایموجی‌های ممنوعه از دیتابیس"""
        try:
            db_path = self.bot_configs[1]['db_path']
            
            # اطمینان از وجود دیتابیس و جدول
            self.setup_database(1, db_path)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT emoji FROM forbidden_emojis")
            result = cursor.fetchall()
            conn.close()
            
            # تبدیل به set
            emojis = {row[0] for row in result}
            logger.info(f"📥 بارگذاری {len(emojis)} ایموجی ممنوعه از دیتابیس")
            return emojis
        except Exception as e:
            logger.error(f"خطا در بارگذاری ایموجی‌های ممنوعه: {e}")
            return set()
    
    def get_spam_delay(self, bot_id):
        """دریافت تاخیر فحش برای بات مشخص"""
        try:
            db_path = self.bot_configs[bot_id]['db_path']
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT delay_seconds FROM spam_delay_settings ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                delay = float(result[0])
                self.bot_spam_delays[bot_id] = delay
                return delay
            else:
                return self.bot_spam_delays.get(bot_id, 1.0)
                
        except Exception as e:
            logger.error(f"❌ خطا در دریافت تاخیر فحش بات {bot_id}: {e}")
            return self.bot_spam_delays.get(bot_id, 1.0)
    
    def set_spam_delay(self, bot_id, delay_seconds):
        """تنظیم تاخیر فحش برای بات مشخص"""
        try:
            # تبدیل به float و اعتبارسنجی
            delay = float(delay_seconds)
            if delay < 0:
                return False, "تاخیر نمی‌تواند منفی باشد"
            
            db_path = self.bot_configs[bot_id]['db_path']
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # به‌روزرسانی یا درج مقدار جدید
            cursor.execute("DELETE FROM spam_delay_settings")  # حذف تنظیمات قبلی
            cursor.execute("INSERT INTO spam_delay_settings (delay_seconds) VALUES (?)", (delay,))
            
            conn.commit()
            conn.close()
            
            # به‌روزرسانی کش
            self.bot_spam_delays[bot_id] = delay
            
            logger.info(f"⏱️ تاخیر فحش بات {bot_id} به {delay} ثانیه تنظیم شد")
            return True, f"تاخیر فحش بات {bot_id} به {delay} ثانیه تنظیم شد"
            
        except ValueError:
            return False, "مقدار تاخیر باید عدد باشد"
        except Exception as e:
            logger.error(f"❌ خطا در تنظیم تاخیر فحش بات {bot_id}: {e}")
            return False, f"خطا در تنظیم تاخیر: {str(e)}"

    def is_admin(self, user_id):
        """بررسی اینکه آیا کاربر ادمین است یا نه"""
        return user_id in self.all_admin_ids

    def normalize_emoji(self, emoji):
        """نرمال‌سازی ایموجی برای مقایسه دقیق‌تر"""
        import unicodedata
        
        # نرمال‌سازی Unicode
        normalized = unicodedata.normalize('NFC', emoji)
        
        # حذف Variation Selectors (U+FE0F, U+FE0E)
        cleaned = normalized.replace('\uFE0F', '').replace('\uFE0E', '')
        
        return cleaned

    def contains_stop_emoji(self, text):
        """بررسی وجود ایموجی‌های توقف در متن"""
        if not text:
            return False

        # نرمال‌سازی متن
        normalized_text = self.normalize_emoji(text)

        for emoji in self.forbidden_emojis:
            normalized_emoji = self.normalize_emoji(emoji)
            
            # بررسی چند حالت مختلف
            checks = [
                emoji in text,                              # مقایسه مستقیم
                normalized_emoji in normalized_text,        # مقایسه نرمال شده
                emoji.replace('\uFE0F', '') in text,       # بدون Variation Selector
                emoji in text.replace('\uFE0F', ''),       # متن بدون Variation Selector
            ]
            
            if any(checks):
                logger.info(f"🛑 ایموجی ممنوعه تشخیص داده شد: {emoji} در متن: {text[:50]}...")
                logger.debug(f"   ایموجی اصلی: {repr(emoji)} (کدها: {[hex(ord(c)) for c in emoji]})")
                logger.debug(f"   ایموجی نرمال: {repr(normalized_emoji)} (کدها: {[hex(ord(c)) for c in normalized_emoji]})")
                logger.debug(f"   متن اصلی: {repr(text[:30])}")
                logger.debug(f"   متن نرمال: {repr(normalized_text[:30])}")
                return True
        return False

    def should_pause_spam(self, message, bot_id):
        """بررسی اینکه آیا باید اسپم را متوقف کرد"""

        # بررسی ایموجی‌های توقف در متن اصلی پیام (همگانی)
        if message.text and self.contains_stop_emoji(message.text):
            logger.info(f"🛑 ایموجی توقف در متن تشخیص داده شد: {message.text[:50]}...")
            return True

        # بررسی ایموجی‌های توقف در کپشن (همگانی)
        if message.caption and self.contains_stop_emoji(message.caption):
            logger.info(f"🛑 ایموجی توقف در کپشن تشخیص داده شد: {message.caption[:50]}...")
            return True

        # بررسی کامندهای ممنوعه فقط برای دشمنان
        if message.from_user:
            user_id = message.from_user.id
            enemy_list = self.get_enemy_list(bot_id)
            enemy_ids = {row[0] for row in enemy_list}
            
            if user_id in enemy_ids:
                message_text = message.text or message.caption or ""
                if message_text:
                    message_lower = message_text.lower().strip()

                    for command in self.enemy_forbidden_commands:
                        # بررسی در ابتدای پیام یا بعد از فاصله
                        if message_lower.startswith(command) or f' {command}' in message_lower:
                            logger.info(f"🛑 کامند ممنوعه دشمن تشخیص داده شد: {command} از دشمن {user_id}")
                            return True

        return False

    def is_flooding_message(self, text):
        """تشخیص پیام‌های مربوط به فلودینگ و اسپم"""
        if not text:
            return False

        flooding_keywords = [
            'flooding', 'spamming', 'ignoring your existence', 
            'upcoming', 'minutes', 'ғʟᴏᴏᴅɪɴɢ', 'sᴘᴀᴍᴍɪɴɢ',
            'ɪɢɴᴏʀɪɴɢ', 'ᴇxɪsᴛᴇɴᴄᴇ', 'ᴜᴘᴄᴏᴍɪɴɢ', 'ᴍɪɴᴜᴛᴇs',
            'flood wait', 'too many requests', 'rate limit', 'spam detected'
        ]

        text_lower = text.lower().strip()
        flood_count = sum(1 for keyword in flooding_keywords if keyword.lower() in text_lower)

        # اگر 2 یا بیشتر کلمه کلیدی فلودینگ وجود داشته باشد (حساسیت بیشتر)
        if flood_count >= 2:
            return True

        return False

    def get_bot_for_admin(self, user_id):
        """پیدا کردن شماره بات برای ادمین مشخص"""
        for bot_id, config in self.bot_configs.items():
            if config['admin_id'] == user_id:
                return bot_id
        return None
    
    def is_launcher_admin(self, user_id):
        """بررسی آیا کاربر ادمین اصلی لانچر است"""
        return user_id == self.launcher_admin_id
    
    def can_control_bot(self, user_id, target_bot_id):
        """بررسی آیا کاربر مجاز به کنترل بات مشخصی است"""
        # ادمین اصلی لانچر می‌تواند همه بات‌ها را کنترل کند
        if self.is_launcher_admin(user_id):
            return True
        
        # ادمین‌های بات فقط می‌توانند بات‌هایی که به آن‌ها اختصاص داده شده را کنترل کنند
        accessible_bots = self.get_accessible_bots(user_id)
        return target_bot_id in accessible_bots
    
    def get_accessible_bots(self, user_id):
        """دریافت لیست بات‌هایی که کاربر مجاز به کنترل آن‌ها است"""
        if self.is_launcher_admin(user_id):
            return list(self.bot_configs.keys())  # همه بات‌ها
        
        # پیدا کردن همه بات‌هایی که این ادمین کنترل می‌کند
        accessible_bots = []
        for bot_id, config in self.bot_configs.items():
            if config['admin_id'] == user_id:
                accessible_bots.append(bot_id)
        
        return accessible_bots

    async def create_bot(self, bot_id, config):
        """ایجاد و تنظیم یک بات"""
        try:
            # تنظیم پایگاه داده
            self.setup_database(bot_id, config['db_path'])
            
            # بارگذاری تنظیمات تاخیر فحش از دیتابیس
            self.get_spam_delay(bot_id)

            # ایجاد کلاینت
            app = Client(
                config['session_name'],
                api_id=config['api_id'],
                api_hash=config['api_hash']
            )

            admin_id = config['admin_id']

            # تعریف هندلرها - کنترل دسترسی بر اساس نوع ادمین
            def is_admin_user(_, __, message):
                if not message.from_user:
                    return False
                user_id = message.from_user.id
                
                # بررسی آیا کاربر اصلاً ادمین است
                if user_id not in self.all_admin_ids:
                    return False
                
                # بررسی آیا کاربر مجاز به کنترل این بات است
                can_control = self.can_control_bot(user_id, bot_id)
                
                if can_control:
                    if self.is_launcher_admin(user_id):
                        logger.info(f"👑 ادمین اصلی لانچر: {user_id} - کنترل بات {bot_id}")
                    else:
                        logger.info(f"🔧 ادمین بات: {user_id} - کنترل بات {bot_id}")
                else:
                    logger.warning(f"🚫 ادمین {user_id} مجاز به کنترل بات {bot_id} نیست")
                
                return can_control

            admin_filter = filters.create(is_admin_user)

            @app.on_message(filters.command("start") & admin_filter)
            async def start_command(client, message):
                try:
                    user_id = message.from_user.id
                    await message.reply_text(f"🤖 **ربات {bot_id} آماده است!**\n\n📋 برای مشاهده کامندها: `/help`\n🆔 Admin: `{admin_id}`\n👤 شما: `{user_id}`\n✅ تشخیص ادمین موفق")
                except Exception as e:
                    logger.error(f"خطا در start command: {e}")

            @app.on_message(filters.command("testadmin") & admin_filter)
            async def test_admin_command(client, message):
                try:
                    user_id = message.from_user.id
                    user_bot = self.get_bot_for_admin(user_id)
                    is_launcher = self.is_launcher_admin(user_id)
                    accessible_bots = self.get_accessible_bots(user_id)

                    text = f"🔍 **تست تشخیص ادمین:**\n\n"
                    text += f"👤 شما: `{user_id}`\n"
                    
                    if is_launcher:
                        text += f"👑 نوع: ادمین اصلی لانچر\n"
                        text += f"🎯 دسترسی: کنترل همه بات‌ها\n"
                    else:
                        text += f"🔧 نوع: ادمین بات شخصی\n"
                        text += f"🤖 بات مربوطه: `{user_bot or 'یافت نشد'}`\n"
                    
                    text += f"🎮 بات‌های قابل کنترل: `{accessible_bots}`\n"
                    text += f"🎯 بات فعلی: `{bot_id}`\n"
                    text += f"✅ وضعیت: دسترسی تایید شده"

                    await message.reply_text(text)
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامند اضافه کردن فحش (تمام انواع رسانه)
            @app.on_message(filters.command("addfosh") & admin_filter)
            async def add_fosh_command(client, message):
                try:
                    if message.reply_to_message:
                        replied = message.reply_to_message
                        media_type = None
                        file_id = None
                        fosh_text = None

                        if replied.photo:
                            media_type = "photo"
                            file_id = replied.photo.file_id
                        elif replied.video:
                            media_type = "video"
                            file_id = replied.video.file_id
                        elif replied.animation:
                            media_type = "animation"
                            file_id = replied.animation.file_id
                        elif replied.sticker:
                            media_type = "sticker"
                            file_id = replied.sticker.file_id
                        elif replied.audio:
                            media_type = "audio"
                            file_id = replied.audio.file_id
                        elif replied.voice:
                            media_type = "voice"
                            file_id = replied.voice.file_id
                        elif replied.video_note:
                            media_type = "video_note"
                            file_id = replied.video_note.file_id
                        elif replied.document:
                            media_type = "document"
                            file_id = replied.document.file_id
                        elif replied.text:
                            fosh_text = replied.text

                        if media_type or fosh_text:
                            if self.add_fosh(bot_id, fosh_text, media_type, file_id):
                                await message.reply_text(f"✅ فحش جدید اضافه شد ({media_type or 'متن'}) - بات {bot_id}")
                                self.log_action(bot_id, "add_fosh", message.from_user.id, f"{media_type or fosh_text}")
                            else:
                                await message.reply_text("❌ خطا در اضافه کردن فحش")
                        else:
                            await message.reply_text("⚠️ نوع رسانه پشتیبانی نمی‌شود")
                    else:
                        if len(message.command) < 2:
                            await message.reply_text("⚠️ لطفاً یک فحش وارد کنید یا روی پیام ریپلای کنید.\n💡 استفاده: `/addfosh متن فحش`")
                            return

                        fosh = " ".join(message.command[1:])
                        if self.add_fosh(bot_id, fosh):
                            await message.reply_text(f"✅ فحش جدید اضافه شد - بات {bot_id}:\n`{fosh}`")
                            self.log_action(bot_id, "add_fosh", message.from_user.id, fosh[:50])
                        else:
                            await message.reply_text("❌ خطا در اضافه کردن فحش")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("delfosh") & admin_filter)
            async def del_fosh_command(client, message):
                try:
                    if len(message.command) < 2:
                        await message.reply_text("⚠️ لطفاً فحش مورد نظر را وارد کنید.\n💡 استفاده: `/delfosh متن فحش`")
                        return

                    fosh = " ".join(message.command[1:])
                    if self.remove_fosh(bot_id, fosh):
                        await message.reply_text(f"✅ فحش حذف شد - بات {bot_id}:\n`{fosh}`")
                        self.log_action(bot_id, "del_fosh", message.from_user.id, fosh[:50])
                    else:
                        await message.reply_text(f"⚠️ این فحش در لیست یافت نشد:\n`{fosh}`")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("listfosh") & admin_filter)
            async def list_fosh_command(client, message):
                try:
                    fosh_list = self.get_fosh_list(bot_id)
                    if not fosh_list:
                        await message.reply_text(f"📝 لیست فحش‌های بات {bot_id} خالی است.\n💡 با `/addfosh` فحش اضافه کنید.")
                        return

                    text = f"🔥 **لیست فحش‌های بات {bot_id}:**\n\n"
                    for i, (fosh, media_type, file_id) in enumerate(fosh_list, 1):
                        if media_type:
                            text += f"`{i}.` [{media_type.upper()}]\n"
                        else:
                            text += f"`{i}.` {fosh}\n"

                        if i >= 20:
                            text += f"\n... و {len(fosh_list) - 20} مورد دیگر"
                            break

                    text += f"\n📊 **تعداد کل:** {len(fosh_list)} فحش"
                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("clearfosh") & admin_filter)
            async def clear_fosh_command(client, message):
                try:
                    count = self.clear_fosh_list(bot_id)
                    await message.reply_text(f"✅ تمام فحش‌های بات {bot_id} حذف شدند.\n📊 تعداد حذف شده: {count} مورد")
                    self.log_action(bot_id, "clear_fosh", message.from_user.id, f"حذف {count} فحش")
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامندهای دشمنان
            @app.on_message(filters.command("setenemy") & admin_filter & filters.reply)
            async def set_enemy_command(client, message):
                try:
                    replied = message.reply_to_message
                    user_id = replied.from_user.id
                    username = replied.from_user.username
                    first_name = replied.from_user.first_name

                    if self.add_enemy(bot_id, user_id, username, first_name):
                        await message.reply_text(f"👹 کاربر به لیست دشمنان بات {bot_id} اضافه شد:\n**نام:** {first_name}\n**آیدی:** `{user_id}`")
                        self.log_action(bot_id, "add_enemy", user_id, f"{first_name} (@{username})")
                    else:
                        await message.reply_text(f"⚠️ این کاربر قبلاً در لیست دشمنان است")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("delenemy") & admin_filter & filters.reply)
            async def del_enemy_command(client, message):
                try:
                    replied = message.reply_to_message
                    user_id = replied.from_user.id
                    first_name = replied.from_user.first_name

                    if self.remove_enemy(bot_id, user_id):
                        await message.reply_text(f"✅ کاربر از لیست دشمنان بات {bot_id} حذف شد:\n**نام:** {first_name}")
                        self.log_action(bot_id, "del_enemy", user_id, f"{first_name}")
                    else:
                        await message.reply_text(f"⚠️ این کاربر در لیست دشمنان یافت نشد")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("listenemy") & admin_filter)
            async def list_enemy_command(client, message):
                try:
                    enemy_list = self.get_enemy_list(bot_id)
                    if not enemy_list:
                        await message.reply_text(f"📝 لیست دشمنان بات {bot_id} خالی است.")
                        return

                    text = f"👹 **لیست دشمنان بات {bot_id}:**\n\n"
                    for i, (user_id, username, first_name, created_at) in enumerate(enemy_list, 1):
                        text += f"`{i}.` {first_name or 'نامشخص'} (`{user_id}`)\n"
                        if i >= 20:
                            text += f"... و {len(enemy_list) - 20} نفر دیگر\n"
                            break

                    text += f"\n📊 **تعداد کل:** {len(enemy_list)} دشمن"
                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("clearenemy") & admin_filter)
            async def clear_enemy_command(client, message):
                try:
                    count = self.clear_enemy_list(bot_id)
                    await message.reply_text(f"✅ تمام دشمنان بات {bot_id} حذف شدند.\n📊 تعداد حذف شده: {count} نفر")
                    self.log_action(bot_id, "clear_enemy", message.from_user.id, f"حذف {count} دشمن")
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامندهای دوستان
            @app.on_message(filters.command("setfriend") & admin_filter & filters.reply)
            async def set_friend_command(client, message):
                try:
                    replied = message.reply_to_message
                    user_id = replied.from_user.id
                    username = replied.from_user.username
                    first_name = replied.from_user.first_name

                    if self.add_friend(bot_id, user_id, username, first_name):
                        await message.reply_text(f"😊 کاربر به لیست دوستان بات {bot_id} اضافه شد:\n**نام:** {first_name}\n**آیدی:** `{user_id}`")
                        self.log_action(bot_id, "add_friend", user_id, f"{first_name} (@{username})")
                    else:
                        await message.reply_text(f"⚠️ این کاربر قبلاً در لیست دوستان است")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("delfriend") & admin_filter & filters.reply)
            async def del_friend_command(client, message):
                try:
                    replied = message.reply_to_message
                    user_id = replied.from_user.id
                    first_name = replied.from_user.first_name

                    if self.remove_friend(bot_id, user_id):
                        await message.reply_text(f"✅ کاربر از لیست دوستان بات {bot_id} حذف شد:\n**نام:** {first_name}")
                        self.log_action(bot_id, "del_friend", user_id, f"{first_name}")
                    else:
                        await message.reply_text(f"⚠️ این کاربر در لیست دوستان یافت نشد")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("listfriend") & admin_filter)
            async def list_friend_command(client, message):
                try:
                    friend_list = self.get_friend_list(bot_id)
                    if not friend_list:
                        await message.reply_text(f"📝 لیست دوستان بات {bot_id} خالی است.")
                        return

                    text = f"😊 **لیست دوستان بات {bot_id}:**\n\n"
                    for i, (user_id, username, first_name, created_at) in enumerate(friend_list, 1):
                        text += f"`{i}.` {first_name or 'نامشخص'} (`{user_id}`)\n"
                        if i >= 20:
                            text += f"... و {len(friend_list) - 20} نفر دیگر\n"
                            break

                    text += f"\n📊 **تعداد کل:** {len(friend_list)} دوست"
                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("clearfriend") & admin_filter)
            async def clear_friend_command(client, message):
                try:
                    count = self.clear_friend_list(bot_id)
                    await message.reply_text(f"✅ تمام دوستان بات {bot_id} حذف شدند.\n📊 تعداد حذف شده: {count} نفر")
                    self.log_action(bot_id, "clear_friend", message.from_user.id, f"حذف {count} دوست")
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامند اضافه کردن کلمه دوستانه (تمام انواع رسانه)
            @app.on_message(filters.command("addword") & admin_filter)
            async def add_word_command(client, message):
                try:
                    if message.reply_to_message:
                        replied = message.reply_to_message
                        media_type = None
                        file_id = None
                        word_text = None

                        if replied.photo:
                            media_type = "photo"
                            file_id = replied.photo.file_id
                        elif replied.video:
                            media_type = "video"
                            file_id = replied.video.file_id
                        elif replied.animation:
                            media_type = "animation"
                            file_id = replied.animation.file_id
                        elif replied.sticker:
                            media_type = "sticker"
                            file_id = replied.sticker.file_id
                        elif replied.audio:
                            media_type = "audio"
                            file_id = replied.audio.file_id
                        elif replied.voice:
                            media_type = "voice"
                            file_id = replied.voice.file_id
                        elif replied.video_note:
                            media_type = "video_note"
                            file_id = replied.video_note.file_id
                        elif replied.document:
                            media_type = "document"
                            file_id = replied.document.file_id
                        elif replied.text:
                            word_text = replied.text

                        if media_type or word_text:
                            if self.add_friend_word(bot_id, word_text, media_type, file_id):
                                await message.reply_text(f"✅ کلمه دوستانه اضافه شد ({media_type or 'متن'}) - بات {bot_id}")
                                self.log_action(bot_id, "add_word", message.from_user.id, f"{media_type or word_text}")
                            else:
                                await message.reply_text("❌ خطا در اضافه کردن کلمه")
                        else:
                            await message.reply_text("⚠️ نوع رسانه پشتیبانی نمی‌شود")
                    else:
                        if len(message.command) < 2:
                            await message.reply_text("⚠️ لطفاً یک کلمه وارد کنید یا روی پیام ریپلای کنید.\n💡 استفاده: `/addword سلام دوست عزیز`")
                            return

                        word = " ".join(message.command[1:])
                        if self.add_friend_word(bot_id, word):
                            await message.reply_text(f"✅ کلمه دوستانه اضافه شد - بات {bot_id}:\n`{word}`")
                            self.log_action(bot_id, "add_word", message.from_user.id, word[:50])
                        else:
                            await message.reply_text("❌ خطا در اضافه کردن کلمه")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("delword") & admin_filter)
            async def del_word_command(client, message):
                try:
                    if len(message.command) < 2:
                        await message.reply_text("⚠️ لطفاً کلمه مورد نظر را وارد کنید.\n💡 استفاده: `/delword کلمه`")
                        return

                    word = " ".join(message.command[1:])
                    if self.remove_friend_word(bot_id, word):
                        await message.reply_text(f"✅ کلمه دوستانه حذف شد - بات {bot_id}:\n`{word}`")
                        self.log_action(bot_id, "del_word", message.from_user.id, word[:50])
                    else:
                        await message.reply_text(f"⚠️ این کلمه در لیست یافت نشد:\n`{word}`")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("listword") & admin_filter)
            async def list_word_command(client, message):
                try:
                    word_list = self.get_friend_words(bot_id)
                    if not word_list:
                        await message.reply_text(f"📝 لیست کلمات دوستانه بات {bot_id} خالی است.\n💡 با `/addword` کلمه اضافه کنید.")
                        return

                    text = f"💬 **لیست کلمات دوستانه بات {bot_id}:**\n\n"
                    for i, (word, media_type, file_id) in enumerate(word_list, 1):
                        if media_type:
                            text += f"`{i}.` [{media_type.upper()}]\n"
                        else:
                            text += f"`{i}.` {word}\n"

                        if i >= 20:
                            text += f"\n... و {len(word_list) - 20} مورد دیگر"
                            break

                    text += f"\n📊 **تعداد کل:** {len(word_list)} کلمه"
                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("clearword") & admin_filter)
            async def clear_word_command(client, message):
                try:
                    count = self.clear_friend_words(bot_id)
                    await message.reply_text(f"✅ تمام کلمات دوستانه بات {bot_id} حذف شدند.\n📊 تعداد حذف شده: {count} مورد")
                    self.log_action(bot_id, "clear_word", message.from_user.id, f"حذف {count} کلمه")
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامند آمار
            @app.on_message(filters.command("stats") & admin_filter)
            async def stats_command(client, message):
                try:
                    stats = self.get_stats(bot_id)

                    text = f"📊 **آمار کامل ربات {bot_id}:**\n\n"
                    text += f"🔥 فحش‌ها: `{stats['fosh_count']}` عدد\n"
                    text += f"👹 دشمنان: `{stats['enemy_count']}` نفر\n"
                    text += f"😊 دوستان: `{stats['friend_count']}` نفر\n"
                    text += f"💬 کلمات دوستانه: `{stats['word_count']}` عدد\n\n"
                    text += f"🤖 **وضعیت پاسخگویی:** {'فعال ✅' if config['auto_reply_enabled'] else 'غیرفعال ❌'}\n"
                    text += f"⏰ **آخرین بروزرسانی:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                    await message.reply_text(text)
                    self.log_action(bot_id, "stats_view", message.from_user.id, "نمایش آمار")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامند فعال/غیرفعال پاسخگویی
            @app.on_message(filters.command(["autoreply", "toggle", "runself"]) & admin_filter)
            async def toggle_auto_reply(client, message):
                try:
                    self.bot_configs[bot_id]['auto_reply_enabled'] = True
                    await message.reply_text(f"🤖 **پاسخگویی خودکار بات {bot_id} فعال شد ✅**")
                    self.log_action(bot_id, "toggle_auto_reply", message.from_user.id, "فعال")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("offself") & admin_filter)
            async def off_auto_reply(client, message):
                try:
                    self.bot_configs[bot_id]['auto_reply_enabled'] = False
                    await message.reply_text(f"🤖 **پاسخگویی خودکار بات {bot_id} غیرفعال شد ❌**")
                    self.log_action(bot_id, "toggle_auto_reply", message.from_user.id, "غیرفعال")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامند ارسال همگانی
            @app.on_message(filters.command("broadcast") & admin_filter)
            async def broadcast_command(client, message):
                try:
                    if len(message.command) < 2 and not message.reply_to_message:
                        await message.reply_text("⚠️ لطفاً پیام مورد نظر را وارد کنید یا روی پیام ریپلای کنید.\n💡 استفاده: `/broadcast سلام به همه`")
                        return

                    if message.reply_to_message:
                        target_message = message.reply_to_message
                    else:
                        text = " ".join(message.command[1:])

                    await message.reply_text(f"📤 شروع ارسال همگانی از بات {bot_id}...")

                    success = 0
                    fail = 0

                    async for dialog in client.get_dialogs():
                        if dialog.chat.type in ["group", "supergroup"]:
                            try:
                                if message.reply_to_message:
                                    await target_message.copy(dialog.chat.id)
                                else:
                                    await client.send_message(dialog.chat.id, text)
                                success += 1
                                await asyncio.sleep(0.01)
                            except FloodWait as e:
                                await asyncio.sleep(e.value)
                                try:
                                    if message.reply_to_message:
                                        await target_message.copy(dialog.chat.id)
                                    else:
                                        await client.send_message(dialog.chat.id, text)
                                    success += 1
                                except:
                                    fail += 1
                            except:
                                fail += 1

                    result_text = f"✅ **ارسال همگانی بات {bot_id} تکمیل شد:**\n\n"
                    result_text += f"📤 **موفق:** {success} گروه\n"
                    result_text += f"❌ **ناموفق:** {fail} گروه\n"
                    result_text += f"📊 **کل:** {success + fail} گروه"

                    # ارسال نتیجه در پیام جدید
                    await client.send_message(message.chat.id, result_text)
                    self.log_action(bot_id, "broadcast", message.from_user.id, f"موفق:{success}, ناموفق:{fail}")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامند اکو برای بات 3 (فقط دشمنان می‌توانند استفاده کنند)
            if bot_id == 3:
                @app.on_message(filters.command("echo") & filters.group)
                async def echo_command(client, message):
                    try:
                        user_id = message.from_user.id if message.from_user else None
                        if not user_id:
                            return

                        # اگر ادمین است، هیچ کاری نکن
                        if user_id in self.all_admin_ids:
                            return

                        # بررسی اینکه کاربر دشمن باشد
                        enemy_list = self.get_enemy_list(bot_id)
                        enemy_ids = {row[0] for row in enemy_list}

                        if user_id not in enemy_ids:
                            return  # اگر دشمن نیست، هیچ کاری نکن

                        # فعال کردن حالت اکو
                        import sys
                        sys.path.append('./bots')
                        from echo_control import set_echo_active
                        set_echo_active(True)

                        # استخراج متن بعد از /echo
                        echo_text = None
                        if len(message.command) > 1:
                            # متن بعد از /echo
                            echo_text = " ".join(message.command[1:])

                        try:
                            if message.reply_to_message:
                                # اگر روی پیامی ریپلای شده، همان پیام را اکو کن
                                target_message = message.reply_to_message

                                if target_message.text:
                                    await client.send_message(
                                        message.chat.id,
                                        target_message.text,
                                        reply_to_message_id=target_message.reply_to_message_id if target_message.reply_to_message else None
                                    )
                                elif target_message.photo:
                                    await client.send_photo(
                                        message.chat.id,
                                        target_message.photo.file_id,
                                        caption=target_message.caption,
                                        reply_to_message_id=target_message.reply_to_message_id if target_message.reply_to_message else None
                                    )
                                elif target_message.video:
                                    await client.send_video(
                                        message.chat.id,
                                        target_message.video.file_id,
                                        caption=target_message.caption,
                                        reply_to_message_id=target_message.reply_to_message_id if target_message.reply_to_message else None
                                    )
                                elif target_message.animation:
                                    await client.send_animation(
                                        message.chat.id,
                                        target_message.animation.file_id,
                                        caption=target_message.caption,
                                        reply_to_message_id=target_message.reply_to_message_id if target_message.reply_to_message else None
                                    )
                                elif target_message.sticker:
                                    await client.send_sticker(
                                        message.chat.id,
                                        target_message.sticker.file_id,
                                        reply_to_message_id=target_message.reply_to_message_id if target_message.reply_to_message else None
                                    )
                                elif target_message.audio:
                                    await client.send_audio(
                                        message.chat.id,
                                        target_message.audio.file_id,
                                        caption=target_message.caption,
                                        reply_to_message_id=target_message.reply_to_message_id if target_message.reply_to_message else None
                                    )
                                elif target_message.voice:
                                    await client.send_voice(
                                        message.chat.id,
                                        target_message.voice.file_id,
                                        caption=target_message.caption,
                                        reply_to_message_id=target_message.reply_to_message_id if target_message.reply_to_message else None
                                    )
                                elif target_message.video_note:
                                    await client.send_video_note(
                                        message.chat.id,
                                        target_message.video_note.file_id,
                                        reply_to_message_id=target_message.reply_to_message_id if target_message.reply_to_message else None
                                    )
                                elif target_message.document:
                                    await client.send_document(
                                        message.chat.id,
                                        target_message.document.file_id,
                                        caption=target_message.caption,
                                        reply_to_message_id=target_message.reply_to_message_id if target_message.reply_to_message else None
                                    )
                            elif echo_text:
                                # اگر متن بعد از /echo وجود دارد، آن را اکو کن
                                await client.send_message(message.chat.id, echo_text)

                            # غیرفعال کردن حالت اکو بعد از اکو
                            await asyncio.sleep(0.1)  # کمی تاخیر برای اطمینان از ارسال
                            set_echo_active(False)

                        except Exception as echo_error:
                            logger.error(f"خطا در اکو کردن پیام: {echo_error}")
                            set_echo_active(False)

                    except Exception as e:
                        logger.error(f"خطا در کامند اکو: {e}")

            # کامند مدیریت توقف اسپم
            @app.on_message(filters.command("pausestatus") & admin_filter)
            async def pause_status_command(client, message):
                try:
                    if not self.global_paused:
                        await message.reply_text(f"✅ **وضعیت سیستم:** همه بات‌ها فعال در همه چت‌ها")
                        return

                    text = f"⏸️ **چت‌های متوقف شده (کلی):**\n\n"
                    for chat_id, user_id in self.global_paused.items():
                        try:
                            chat_info = await client.get_chat(chat_id)
                            chat_name = chat_info.title or f"چت {chat_id}"
                        except:
                            chat_name = f"چت {chat_id}"

                        text += f"🔸 {chat_name}\n   └ متوقف توسط: `{user_id}`\n"

                    text += f"\n📌 **نحوه ازسرگیری:** دشمن باید پیام بفرسته"
                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("resumespam") & admin_filter)
            async def resume_spam_command(client, message):
                try:
                    if len(message.command) < 2:
                        await message.reply_text("⚠️ استفاده: `/resumespam [chat_id]`\nمثال: `/resumespam -1001234567890`")
                        return

                    try:
                        chat_id = int(message.command[1])
                    except ValueError:
                        await message.reply_text("❌ شناسه چت نامعتبر")
                        return

                    if chat_id in self.global_paused:
                        user_id = self.global_paused[chat_id]
                        del self.global_paused[chat_id]
                        await message.reply_text(f"▶️ **همه بات‌ها در چت `{chat_id}` ازسرگیری شدند**\n👤 متوقف شده توسط: `{user_id}`")
                        self.log_action(bot_id, "manual_global_resume", message.from_user.id, f"ازسرگیری دستی کلی در چت {chat_id}")
                    else:
                        await message.reply_text(f"✅ چت `{chat_id}` قبلاً فعال بوده")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامند مدیریت ایموجی‌های ممنوعه
            @app.on_message(filters.command("addemoji") & admin_filter)
            async def add_forbidden_emoji_command(client, message):
                try:
                    if len(message.command) < 2:
                        await message.reply_text("⚠️ لطفاً ایموجی مورد نظر را وارد کنید.\n💡 استفاده: `/addemoji 🚫`")
                        return

                    new_emoji = " ".join(message.command[1:])
                    
                    if new_emoji in self.forbidden_emojis:
                        await message.reply_text(f"⚠️ این ایموجی قبلاً در لیست ممنوعه است: {new_emoji}")
                        return
                    
                    # اضافه کردن به دیتابیس
                    if self.add_forbidden_emoji_to_db(new_emoji):
                        # اضافه کردن به حافظه (همه بات‌ها مشترک هستند)
                        self.forbidden_emojis.add(new_emoji)
                        
                        # بارگذاری مجدد از دیتابیس برای اطمینان از همگام‌سازی
                        fresh_emojis = self.load_forbidden_emojis_from_db()
                        self.forbidden_emojis = fresh_emojis
                        
                        await message.reply_text(f"✅ ایموجی جدید به لیست ممنوعه اضافه شد: {new_emoji}\n📊 تعداد کل: {len(self.forbidden_emojis)} ایموجی\n💾 در دیتابیس ذخیره شد\n🔄 همه بات‌ها همگام‌سازی شدند")
                        self.log_action(bot_id, "add_forbidden_emoji", message.from_user.id, new_emoji)
                        logger.info(f"✅ ایموجی {new_emoji} به همه بات‌ها اضافه شد")
                    else:
                        await message.reply_text(f"❌ خطا در ذخیره ایموجی در دیتابیس")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("delemoji") & admin_filter)
            async def del_forbidden_emoji_command(client, message):
                try:
                    if len(message.command) < 2:
                        await message.reply_text("⚠️ لطفاً ایموجی مورد نظر را وارد کنید.\n💡 استفاده: `/delemoji 🚫`")
                        return

                    emoji_to_remove = " ".join(message.command[1:])
                    
                    if emoji_to_remove not in self.forbidden_emojis:
                        await message.reply_text(f"⚠️ این ایموجی در لیست ممنوعه یافت نشد: {emoji_to_remove}")
                        return
                    
                    # حذف از دیتابیس
                    if self.remove_forbidden_emoji_from_db(emoji_to_remove):
                        # حذف از حافظه
                        if emoji_to_remove in self.forbidden_emojis:
                            self.forbidden_emojis.remove(emoji_to_remove)
                        
                        # بارگذاری مجدد از دیتابیس برای اطمینان از همگام‌سازی
                        fresh_emojis = self.load_forbidden_emojis_from_db()
                        self.forbidden_emojis = fresh_emojis
                        
                        await message.reply_text(f"✅ ایموجی از لیست ممنوعه حذف شد: {emoji_to_remove}\n📊 تعداد باقی‌مانده: {len(self.forbidden_emojis)} ایموجی\n💾 از دیتابیس حذف شد\n🔄 همه بات‌ها همگام‌سازی شدند")
                        self.log_action(bot_id, "del_forbidden_emoji", message.from_user.id, emoji_to_remove)
                        logger.info(f"✅ ایموجی {emoji_to_remove} از همه بات‌ها حذف شد")
                    else:
                        await message.reply_text(f"❌ خطا در حذف ایموجی از دیتابیس")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("listemoji") & admin_filter)
            async def list_forbidden_emoji_command(client, message):
                try:
                    if not self.forbidden_emojis:
                        await message.reply_text("📝 لیست ایموجی‌های ممنوعه خالی است.")
                        return

                    emoji_list = list(self.forbidden_emojis)
                    text = f"🚫 **لیست ایموجی‌های ممنوعه (همگانی):**\n\n"
                    
                    for i, emoji in enumerate(emoji_list, 1):
                        # نمایش کد یونیکد هم برای دیباگ
                        unicode_codes = [f"U+{ord(char):04X}" for char in emoji]
                        text += f"`{i}.` {emoji} `{' '.join(unicode_codes)}`\n"
                        if i >= 20:  # محدود به 20 ایموجی در هر پیام
                            text += f"\n... و {len(emoji_list) - 20} ایموجی دیگر"
                            break

                    text += f"\n📊 **تعداد کل:** {len(emoji_list)} ایموجی"
                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("testemoji") & admin_filter)
            async def test_emoji_command(client, message):
                try:
                    if len(message.command) < 2:
                        await message.reply_text("⚠️ استفاده: `/testemoji [ایموجی]`\nمثال: `/testemoji ⚡️`")
                        return

                    test_emoji = " ".join(message.command[1:])
                    
                    # تست تشخیص
                    is_detected = self.contains_stop_emoji(test_emoji)
                    
                    # نمایش جزئیات
                    import unicodedata
                    unicode_codes = [f"U+{ord(char):04X}" for char in test_emoji]
                    normalized = unicodedata.normalize('NFC', test_emoji)
                    normalized_codes = [f"U+{ord(char):04X}" for char in normalized]
                    
                    text = f"🔍 **تست تشخیص ایموجی:**\n\n"
                    text += f"ایموجی: {test_emoji}\n"
                    text += f"کد اصلی: `{' '.join(unicode_codes)}`\n"
                    text += f"کد نرمال: `{' '.join(normalized_codes)}`\n"
                    text += f"در لیست ممنوعه: {'✅ بله' if test_emoji in self.forbidden_emojis else '❌ خیر'}\n"
                    text += f"تشخیص داده شد: {'✅ بله' if is_detected else '❌ خیر'}\n\n"
                    text += f"📊 تعداد کل ایموجی‌های ممنوعه: {len(self.forbidden_emojis)}"
                    
                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("spamstatus") & admin_filter)
            async def spam_status_command(client, message):
                try:
                    if not self.continuous_spam_tasks:
                        await message.reply_text("✅ **هیچ فحش نامحدودی در حال اجرا نیست**")
                        return

                    text = f"🔥 **فحش‌های نامحدود فعال:**\n\n"
                    
                    for i, (spam_key, task) in enumerate(self.continuous_spam_tasks.items(), 1):
                        bot_id, user_id, chat_id = spam_key.split('_')
                        
                        try:
                            chat_info = await client.get_chat(int(chat_id))
                            chat_name = chat_info.title or f"چت {chat_id}"
                        except:
                            chat_name = f"چت {chat_id}"
                        
                        text += f"`{i}.` بات {bot_id} → دشمن `{user_id}`\n"
                        text += f"    └ در: {chat_name}\n"
                        text += f"    └ وضعیت: {'✅ فعال' if not task.done() else '❌ متوقف'}\n\n"
                        
                        if i >= 10:  # محدود به 10 مورد
                            text += f"... و {len(self.continuous_spam_tasks) - 10} مورد دیگر\n"
                            break

                    text += f"\n📊 **تعداد کل:** {len(self.continuous_spam_tasks)} فحش نامحدود فعال"
                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("stopspam") & admin_filter)
            async def stop_spam_command(client, message):
                try:
                    if len(message.command) < 2:
                        await message.reply_text("⚠️ استفاده: `/stopspam [bot_id]` یا `/stopspam all`\nمثال: `/stopspam 1` یا `/stopspam all`")
                        return

                    target = message.command[1].lower()
                    stopped_count = 0

                    if target == "all":
                        # متوقف کردن همه فحش‌های نامحدود
                        for spam_key, task in list(self.continuous_spam_tasks.items()):
                            try:
                                task.cancel()
                                stopped_count += 1
                            except:
                                pass
                        self.continuous_spam_tasks.clear()
                        
                        await message.reply_text(f"🛑 **همه فحش‌های نامحدود متوقف شدند**\n📊 تعداد متوقف شده: {stopped_count}")
                        
                    else:
                        try:
                            target_bot_id = int(target)
                            
                            # متوقف کردن فحش‌های مربوط به بات مشخص
                            keys_to_remove = []
                            for spam_key, task in self.continuous_spam_tasks.items():
                                bot_id, user_id, chat_id = spam_key.split('_')
                                if int(bot_id) == target_bot_id:
                                    try:
                                        task.cancel()
                                        keys_to_remove.append(spam_key)
                                        stopped_count += 1
                                    except:
                                        pass
                            
                            for key in keys_to_remove:
                                del self.continuous_spam_tasks[key]
                            
                            if stopped_count > 0:
                                await message.reply_text(f"🛑 **فحش‌های نامحدود بات {target_bot_id} متوقف شدند**\n📊 تعداد متوقف شده: {stopped_count}")
                            else:
                                await message.reply_text(f"ℹ️ هیچ فحش نامحدودی برای بات {target_bot_id} یافت نشد")
                                
                        except ValueError:
                            await message.reply_text("❌ شماره بات نامعتبر")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامندهای تنظیم تاخیر فحش
            @app.on_message(filters.command("setdelay") & admin_filter)
            async def set_delay_command(client, message):
                try:
                    if len(message.command) < 2:
                        await message.reply_text("⚠️ استفاده: /setdelay [ثانیه]\nمثال: /setdelay 2.5")
                        return
                    
                    delay_str = message.command[1]
                    success, msg = self.set_spam_delay(bot_id, delay_str)
                    
                    if success:
                        await message.reply_text(f"✅ {msg}")
                        self.log_action(bot_id, "set_delay", message.from_user.id, f"تاخیر: {delay_str} ثانیه")
                    else:
                        await message.reply_text(f"❌ {msg}")
                        
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("getdelay") & admin_filter)
            async def get_delay_command(client, message):
                try:
                    current_delay = self.get_spam_delay(bot_id)
                    await message.reply_text(f"⏱️ **تاخیر فعلی فحش بات {bot_id}:**\n\n🕒 {current_delay} ثانیه\n\n💡 برای تغییر از `/setdelay [ثانیه]` استفاده کنید")
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # راهنما
            @app.on_message(filters.command("help") & admin_filter)
            async def help_command(client, message):
                try:
                    user_id = message.from_user.id
                    is_launcher = self.is_launcher_admin(user_id)
                    accessible_bots = self.get_accessible_bots(user_id)
                    
                    help_text = f"""🤖 **راهنمای جامع سیستم ۹ بات هوشمند - بات {bot_id}**

👤 **دسترسی شما:**
{'👑 ادمین اصلی لانچر - کنترل همه بات‌ها' if is_launcher else f'🔧 ادمین بات شخصی - کنترل بات‌های: {accessible_bots}'}

🔥 **سیستم فحش نامحدود:**
• فحش خودکار و مداوم به دشمنان تا دریافت ایموجی توقف
• توقف هوشمند با ایموجی‌های ممنوعه: 🔮💎⚡🎯🏆❤️💰🎁
• مانیتورینگ real-time تعداد فحش‌های ارسالی"""

                    # اضافه کردن توضیح اکو برای بات 3
                    if bot_id == 3:
                        help_text += f"""

🔊 **قابلیت اکو (ویژه بات {bot_id}):**
• `/echo` - اکو کردن پیام (فقط برای دشمنان)
  └ با ریپلای: پیام ریپلای شده را اکو می‌کند
  └ بدون ریپلای: خود پیام کامند را اکو می‌کند
  └ تمام انواع رسانه پشتیبانی می‌شود"""

                    text = help_text + f"""

🔥 **مدیریت فحش‌ها:**
• `/addfosh [متن/رسانه]` - اضافه کردن فحش جدید
• `/delfosh [متن]` - حذف فحش مشخص
• `/listfosh` - نمایش تمام فحش‌های بات {bot_id}
• `/clearfosh` - حذف همه فحش‌ها
• `/startfosh` - شروع فحش نامحدود (ریپلای روی دشمن)
• `/stopfosh` - توقف فوری فحش نامحدود

👹 **مدیریت دشمنان:**
• `/setenemy` - اضافه کردن دشمن (ریپلای)
• `/delenemy` - حذف دشمن (ریپلای)
• `/listenemy` - نمایش لیست دشمنان
• `/clearenemy` - حذف همه دشمنان

😊 **مدیریت دوستان:**
• `/setfriend` - اضافه کردن دوست (ریپلای)
• `/delfriend` - حذف دوست (ریپلای)
• `/listfriend` - نمایش لیست دوستان
• `/clearfriend` - حذف همه دوستان

💬 **کلمات دوستانه:**
• `/addword [متن/رسانه]` - اضافه کردن کلمه دوستانه
• `/delword [متن]` - حذف کلمه دوستانه
• `/listword` - نمایش لیست کلمات
• `/clearword` - حذف همه کلمات

🔧 **تنظیمات:**
• `/autoreply` - فعال/غیرفعال پاسخگویی خودکار
• `/stats` - نمایش آمار کامل بات {bot_id}
• `/broadcast [پیام]` - ارسال همگانی
• `/pause` - توقف موقت همه بات‌ها
• `/resume` - ادامه کار همه بات‌ها

🛑 **ایموجی‌های توقف:**
🔮 💎 ⚡ 🎯 🏆 ❤️ 💰 🎁

هنگام دیدن این ایموجی‌ها، تمام بات‌ها متوقف می‌شوند.

📊 **وضعیت سیستم:**
• 9 بات همزمان فعال
• فحش نامحدود تا دریافت ایموجی توقف
• مدیریت خودکار flood wait
• آمارگیری لحظه‌ای

💡 **نکات مهم:**
• فحش نامحدود خودکار با تشخیص دشمن شروع می‌شود
• سیستم توقف هوشمند برای جلوگیری از مشکل
• همه کامندها فقط برای ادمین‌ها
• پشتیبانی کامل از انواع رسانه

💡 **نکات مهم:**
• فحش نامحدود خودکار با تشخیص دشمن شروع می‌شود
• سیستم توقف هوشمند برای جلوگیری از مشکل
• همه کامندها فقط برای ادمین‌ها
• پشتیبانی کامل از انواع رسانه

🔗 **دستورات اضافی:**
• `/help` - راهنمای اصلی
• `/help2` - راهنمای پیشرفته و ویژگی‌های خاص
• `/stats` - آمار کامل سیستم"""

                    # اضافه کردن کامندهای ویژه ادمین اصلی لانچر
                    if is_launcher:
                        text += f"""

👑 **کامندهای ویژه ادمین اصلی لانچر:**
• `/launcherstatus` - نمایش وضعیت کامل همه بات‌ها
• `/restartbot [شماره]` - راه‌اندازی مجدد بات مشخص
• `/manageall autoreply [on|off]` - کنترل پاسخگویی همه بات‌ها
• `/testadmin` - بررسی دسترسی و نوع ادمین

🎯 **دسترسی شما:** کنترل کامل همه ۹ بات
⚠️ **توجه:** این کامندها فقط برای شما قابل استفاده هستند"""
                    
                    text += """

💡 **نکات مهم:**
• هر ادمین فقط بات خودش را کنترل می‌کند
• ادمین اصلی لانچر همه بات‌ها را کنترل می‌کند
• فحش نامحدود خودکار با تشخیص دشمن شروع می‌شود
• سیستم توقف هوشمند برای جلوگیری از مشکل"""

                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # راهنمای پیشرفته (بخش دوم)
            @app.on_message(filters.command("help2") & admin_filter)
            async def help2_command(client, message):
                try:
                    user_id = message.from_user.id
                    is_launcher = self.is_launcher_admin(user_id)
                    accessible_bots = self.get_accessible_bots(user_id)
                    
                    help2_text = f"""🔧 **راهنمای پیشرفته - بات {bot_id}**

👤 **دسترسی شما:**
{'👑 ادمین اصلی لانچر - کنترل همه بات‌ها' if is_launcher else f'🔧 ادمین بات شخصی - کنترل بات‌های: {accessible_bots}'}

🔥 **مدیریت سیستم فحش‌ها:**
• `/addfosh [متن]` - اضافه کردن فحش جدید (متن یا ریپلای رسانه)
  └ پشتیبانی: متن، عکس، ویدیو، گیف، استیکر، صوت
• `/delfosh [متن]` - حذف فحش مشخص از دیتابیس
• `/listfosh` - نمایش کامل فحش‌ها با صفحه‌بندی خودکار
• `/clearfosh` - حذف کلی تمام فحش‌ها (غیرقابل بازگشت)

📢 **سیستم ارسال همگانی:**
• `/broadcast [پیام]` - ارسال همگانی متن به تمام گروه‌ها
• پشتیبانی از ارسال رسانه با ریپلای در broadcast

🤖 **تنظیمات سیستم:**
• `/runself` - فعال کردن پاسخگویی خودکار
• `/offself` - غیرفعال کردن پاسخگویی
• `/start` - راه‌اندازی مجدد ربات

⏸️ **کنترل هوشمند اسپم:**
• `/pausestatus` - نمایش وضعیت توقف اسپم در چت‌ها
• `/resumespam [chat_id]` - ازسرگیری دستی اسپم در چت مشخص

🛑 **توقف خودکار اسپم:**
• ایموجی‌های توقف (همگانی): 🎐🔮⚜️❓🪅🏵🌤☀️🌧⚡️💮
• کامندهای ممنوعه (فقط دشمن): /catch /grab /guess /arise /take /secure

🚫 **مدیریت ایموجی‌های ممنوعه:**
• `/addemoji [ایموجی]` - اضافه کردن ایموجی جدید به لیست ممنوعه
• `/delemoji [ایموجی]` - حذف ایموجی از لیست ممنوعه
• `/listemoji` - نمایش تمام ایموجی‌های ممنوعه

🔥 **مدیریت فحش نامحدود:**
• `/spamstatus` - نمایش وضعیت فحش‌های نامحدود فعال
• `/stopspam [bot_id|all]` - متوقف کردن فحش‌های نامحدود
  └ مثال: `/stopspam 1` یا `/stopspam all`

⏱️ **تنظیمات تاخیر فحش:**
• `/setdelay [ثانیه]` - تنظیم تاخیر بین فحش‌ها
  └ مثال: `/setdelay 2.5` (2.5 ثانیه تاخیر)
  └ مثال: `/setdelay 0.1` (0.1 ثانیه تاخیر)
• `/getdelay` - نمایش تاخیر فعلی فحش

⚡ **ویژگی‌های جدید:**
• فحش نامحدود به دشمنان تا ایموجی ممنوعه فرستاده شود
• سیستم کامندهای ممنوعه مخصوص دشمنان
• مدیریت قابل تنظیم ایموجی‌های ممنوعه
• کامندهای توقف: `/catch` `/grab` `/guess` `/take` `/arise`
└ اسپم تا پیام بعدی دشمن متوقف می‌شود"""

                    # اضافه کردن کامندهای ویژه ادمین اصلی لانچر برای help2
                    if is_launcher:
                        help2_text += f"""

👑 **کامندهای ویژه ادمین اصلی لانچر:**
• `/launcherstatus` - نمایش وضعیت کامل همه بات‌ها
• `/restartbot [شماره]` - راه‌اندازی مجدد بات مشخص
• `/manageall autoreply [on|off]` - کنترل پاسخگویی همه بات‌ها
• `/testadmin` - بررسی دسترسی و نوع ادمین

🎯 **دسترسی شما:** کنترل کامل همه ۹ بات
⚠️ **توجه:** این کامندها فقط برای شما قابل استفاده هستند"""
                    
                    help2_text += """

💡 **نکات پیشرفته:**
• هر ادمین فقط بات خودش را کنترل می‌کند
• ادمین اصلی لانچر همه بات‌ها را کنترل می‌کند
• فحش نامحدود خودکار با تشخیص دشمن شروع می‌شود
• سیستم توقف هوشمند برای جلوگیری از مشکل

🔗 **دستورات راهنما:**
• `/help` - راهنمای اصلی
• `/help2` - این راهنمای پیشرفته
• `/stats` - آمار کامل سیستم"""

                    await message.reply_text(help2_text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # دستورات مدیریتی ویژه ادمین اصلی لانچر
            @app.on_message(filters.command("launcherstatus") & admin_filter)
            async def launcher_status_command(client, message):
                try:
                    user_id = message.from_user.id
                    if not self.is_launcher_admin(user_id):
                        await message.reply_text("🚫 این کامند فقط برای ادمین اصلی لانچر است")
                        return
                        
                    status = self.get_status()
                    status_text = f"""
👑 **وضعیت لانچر واحد - ادمین اصلی:**

🤖 تعداد کل بات‌ها: {status['total_bots']}
✅ بات‌های فعال: {status['running_bots']}
❌ بات‌های خطا: {status['error_bots']}

📋 **جزئیات بات‌ها:**
"""

                    for bot_info in status['bots']:
                        emoji = "✅" if bot_info['status'] == 'running' else "❌"
                        bot_admin = self.bot_configs.get(bot_info['id'], {}).get('admin_id', 'Unknown')
                        status_text += f"{emoji} بات {bot_info['id']}: {bot_info['status']} (Admin: {bot_admin})\n"

                    await message.reply_text(status_text.strip())

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {e}")

            @app.on_message(filters.command("restartbot") & admin_filter)
            async def restart_bot_command(client, message):
                try:
                    user_id = message.from_user.id
                    
                    if len(message.command) < 2:
                        await message.reply_text("⚠️ استفاده: /restartbot [شماره_بات]\nمثال: /restartbot 2")
                        return

                    target_bot_id = int(message.command[1])
                    if target_bot_id not in self.bot_configs:
                        await message.reply_text(f"❌ بات {target_bot_id} یافت نشد")
                        return
                    
                    # بررسی دسترسی
                    if not self.can_control_bot(user_id, target_bot_id):
                        await message.reply_text(f"🚫 شما مجاز به راه‌اندازی مجدد بات {target_bot_id} نیستید")
                        return

                    await message.reply_text(f"🔄 راه‌اندازی مجدد بات {target_bot_id}...")

                    success = await self.restart_bot(target_bot_id)
                    if success:
                        await message.reply_text(f"✅ بات {target_bot_id} مجدداً راه‌اندازی شد")
                    else:
                        await message.reply_text(f"❌ خطا در راه‌اندازی مجدد بات {target_bot_id}")

                except ValueError:
                    await message.reply_text("❌ شماره بات نامعتبر")
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {e}")
            
            # کامند جدید برای مدیریت کردن همه بات‌ها (فقط ادمین اصلی)
            @app.on_message(filters.command("manageall") & admin_filter)
            async def manage_all_bots_command(client, message):
                try:
                    user_id = message.from_user.id
                    if not self.is_launcher_admin(user_id):
                        await message.reply_text("🚫 این کامند فقط برای ادمین اصلی لانچر است")
                        return
                    
                    if len(message.command) < 3:
                        await message.reply_text("⚠️ استفاده: /manageall [کامند] [پارامتر]\nمثال: /manageall autoreply on")
                        return
                    
                    command = message.command[1].lower()
                    parameter = message.command[2].lower()
                    
                    if command == "autoreply":
                        enabled = parameter == "on"
                        for bot_id in self.bot_configs.keys():
                            self.bot_configs[bot_id]['auto_reply_enabled'] = enabled
                        
                        status = "فعال" if enabled else "غیرفعال" 
                        await message.reply_text(f"✅ پاسخگویی خودکار همه بات‌ها {status} شد")
                    
                    else:
                        await message.reply_text("❌ کامند نامعتبر. کامندهای موجود: autoreply")
                        
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {e}")

            # پاسخگویی خودکار
            @app.on_message(
                ~filters.me & 
                ~filters.channel & 
                ~admin_filter &
                ~filters.service &
                filters.group
            )
            async def auto_reply_handler(client, message):
                """هندلر پاسخگویی خودکار"""
                # بررسی وضعیت اکو - اگر اکو فعال است، پاسخگویی خودکار نکن
                try:
                    import sys
                    sys.path.append('./bots')
                    from echo_control import is_echo_active
                    if is_echo_active():
                        return
                except:
                    pass

                if not config['auto_reply_enabled']:
                    return

                chat_id = message.chat.id

                # بررسی ایموجی/کامند ممنوعه برای همه کاربران
                if self.should_pause_spam(message, bot_id):
                    # دریافت اطلاعات فرستنده
                    user_id = message.from_user.id if message.from_user else 0
                    sender_name = message.from_user.first_name if message.from_user else "نامشخص"
                    sender_username = message.from_user.username if message.from_user else "نامشخص"

                    # تشخیص نوع فرستنده
                    if message.from_user:
                        if message.from_user.is_bot:
                            sender_type = "ربات تلگرام"
                            sender_detail = f"@{sender_username}" if sender_username else f"ربات {user_id}"
                        else:
                            sender_type = "کاربر"
                            sender_detail = f"{sender_name} (@{sender_username})" if sender_username else f"{sender_name}"
                    else:
                        sender_type = "فرستنده نامشخص"
                        sender_detail = "بدون اطلاعات"

                    logger.info(f"🛑 بات {bot_id} - ایموجی/کامند ممنوعه تشخیص داده شد در چت {chat_id}")
                    logger.info(f"   └ توسط: {sender_type} - {sender_detail} (ID: {user_id})")

                    # نمایش محتوای پیام با بررسی امنیت
                    message_content = message.text or message.caption or "[بدون متن]"
                    if len(message_content) > 100:
                        message_content = message_content[:100] + "..."
                    logger.info(f"   └ محتوای پیام: {message_content}")

                    # **توقف کلی همه بات‌ها در این چت تا پیام بعدی دشمن**
                    self.global_paused[chat_id] = user_id
                    logger.info(f"⏸️ همه بات‌ها در چت {chat_id} متوقف شدند تا پیام بعدی دشمن")

                    # لاگ عملیات در دیتابیس
                    chat_title = message.chat.title if message.chat.title else f"چت {chat_id}"
                    self.log_action(bot_id, "global_pause_forbidden", user_id, f"توقف کلی توسط {sender_type} ({sender_detail}) در {chat_title}")

                    # ❌ هیچ واکنشی نشون نده و همه بات‌ها رو متوقف کن
                    return

                # بررسی اینکه آیا این چت متوقف شده یا نه
                if chat_id in self.global_paused:
                    # اگر پیام از دشمن باشد، سیستم رو فعال کن
                    if message.from_user:
                        user_id = message.from_user.id
                        enemy_list = self.get_enemy_list(bot_id)
                        enemy_ids = {row[0] for row in enemy_list}
                        
                        if user_id in enemy_ids:
                            # دشمن پیام فرستاده - ازسرگیری فعالیت
                            paused_by = self.global_paused[chat_id]
                            del self.global_paused[chat_id]
                            logger.info(f"▶️ سیستم در چت {chat_id} ازسرگیری شد - دشمن {user_id} پیام فرستاد")
                            logger.info(f"   └ قبلاً توسط کاربر {paused_by} متوقف شده بود")
                            self.log_action(bot_id, "global_resume_by_enemy", user_id, f"ازسرگیری توسط دشمن {user_id}")
                            # ادامه به منطق پاسخگویی
                        else:
                            # کاربر عادی پیام فرستاده - همچنان متوقف
                            logger.debug(f"⏸️ چت {chat_id} همچنان متوقف - کاربر عادی {user_id} پیام فرستاد")
                            return
                    else:
                        # پیام بدون فرستنده - همچنان متوقف
                        return

                # ادامه منطق فقط برای پیام‌هایی که from_user دارند
                if not message.from_user:
                    return

                user_id = message.from_user.id

                # بررسی دشمن بودن
                enemy_list = self.get_enemy_list(bot_id)
                enemy_ids = {row[0] for row in enemy_list}

                if user_id in enemy_ids:
                    # شروع فحش نامحدود به دشمن
                    fosh_list = self.get_fosh_list(bot_id)
                    if fosh_list:
                        # ایجاد کلید یونیک برای این دشمن در این بات
                        spam_key = f"{bot_id}_{user_id}_{chat_id}"
                        
                        # اگر قبلاً تسک فعال برای این دشمن وجود دارد، آن را متوقف کن
                        if spam_key in self.continuous_spam_tasks:
                            try:
                                self.continuous_spam_tasks[spam_key].cancel()
                                logger.info(f"🔄 تسک قبلی فحش برای دشمن {user_id} در بات {bot_id} متوقف شد")
                            except:
                                pass
                        
                        # شروع تسک جدید فحش نامحدود
                        spam_task = asyncio.create_task(
                            self.continuous_spam_attack(client, message, user_id, fosh_list, bot_id, chat_id)
                        )
                        self.continuous_spam_tasks[spam_key] = spam_task
                        logger.info(f"🔥 شروع فحش نامحدود به دشمن {user_id} توسط بات {bot_id}")
                    return

                # بررسی دوست بودن
                friend_list = self.get_friend_list(bot_id)
                friend_ids = {row[0] for row in friend_list}

                if user_id in friend_ids:
                    word_list = self.get_friend_words(bot_id)
                    if word_list:
                        selected = choice(word_list)
                        await self.send_reply(message, selected)

            # ذخیره بات
            self.bots[bot_id] = {
                'client': app,
                'config': config,
                'status': 'initialized'
            }

            logger.info(f"✅ بات {bot_id} ایجاد شد")
            return app

        except Exception as e:
            logger.error(f"❌ خطا در ایجاد بات {bot_id}: {e}")
            return None

    async def send_reply(self, message, selected_content):
        """ارسال پاسخ"""
        try:
            content_text, media_type, file_id = selected_content

            if media_type and file_id:
                reply_methods = {
                    "photo": message.reply_photo,
                    "video": message.reply_video,
                    "animation": message.reply_animation,
                    "sticker": message.reply_sticker,
                    "audio": message.reply_audio,
                    "voice": message.reply_voice,
                    "video_note": message.reply_video_note,
                    "document": message.reply_document
                }

                method = reply_methods.get(media_type)
                if method:
                    await method(file_id)
            elif content_text:
                await message.reply_text(content_text)
        except Exception as e:
            logger.error(f"خطا در ارسال پاسخ: {e}")

    async def start_all_bots(self):
        """شروع همه بات‌ها"""
        self.running = True
        logger.info("🚀 شروع لانچر واحد بات‌ها...")

        # ایجاد همه بات‌ها
        tasks = []
        for bot_id, config in self.bot_configs.items():
            logger.info(f"🔧 ایجاد بات {bot_id}...")
            bot = await self.create_bot(bot_id, config)
            if bot:
                tasks.append(self.start_single_bot(bot_id))

        # شروع همه بات‌ها به صورت موازی
        if tasks:
            logger.info(f"🎯 شروع {len(tasks)} بات...")
            await asyncio.gather(*tasks, return_exceptions=True)

    async def start_single_bot(self, bot_id):
        """شروع یک بات"""
        try:
            if bot_id not in self.bots:
                logger.error(f"❌ بات {bot_id} یافت نشد")
                return

            bot_info = self.bots[bot_id]
            client = bot_info['client']

            logger.info(f"🚀 شروع بات {bot_id}...")

            await client.start()
            bot_info['status'] = 'running'
            bot_info['start_time'] = datetime.now()

            # بارگذاری ایموجی‌های ممنوعه از دیتابیس برای همه بات‌ها
            try:
                loaded_emojis = self.load_forbidden_emojis_from_db()
                self.forbidden_emojis.update(loaded_emojis)
                logger.info(f"📥 بات {bot_id} - ایموجی‌های ممنوعه بارگذاری شدند: {len(loaded_emojis)} ایموجی از دیتابیس")
                logger.info(f"📊 کل ایموجی‌های ممنوعه در حافظه: {len(self.forbidden_emojis)} ایموجی")
            except Exception as e:
                logger.error(f"❌ خطا در بارگذاری ایموجی‌های ممنوعه برای بات {bot_id}: {e}")

            logger.info(f"✅ بات {bot_id} آماده و در حال اجرا!")

            # مانیتورینگ و نگه داشتن بات زنده
            while self.running and bot_info['status'] == 'running':
                try:
                    # بررسی وضعیت اتصال
                    if not client.is_connected:
                        logger.warning(f"⚠️ بات {bot_id} اتصال قطع شده - تلاش برای اتصال مجدد...")
                        await client.start()

                    await asyncio.sleep(10)  # بررسی هر 10 ثانیه

                except Exception as monitor_error:
                    logger.error(f"❌ خطا در مانیتورینگ بات {bot_id}: {monitor_error}")
                    await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"❌ خطا در شروع بات {bot_id}: {e}")
            if bot_id in self.bots:
                self.bots[bot_id]['status'] = 'error'

                # تلاش برای راه‌اندازی مجدد خودکار
                logger.info(f"🔄 تلاش برای راه‌اندازی مجدد خودکار بات {bot_id} در 30 ثانیه...")
                await asyncio.sleep(30)
                if self.running:
                    await self.restart_bot(bot_id)

    async def stop_single_bot(self, bot_id):
        """متوقف کردن یک بات"""
        try:
            if bot_id in self.bots:
                bot_info = self.bots[bot_id]
                if bot_info['status'] == 'running':
                    logger.info(f"⏹️ متوقف کردن بات {bot_id}...")
                    await bot_info['client'].stop()
                    bot_info['status'] = 'stopped'
                    logger.info(f"✅ بات {bot_id} متوقف شد")
        except Exception as e:
            logger.error(f"❌ خطا در متوقف کردن بات {bot_id}: {e}")

    async def stop_all_bots(self):
        """متوقف کردن همه بات‌ها"""
        logger.info("🛑 متوقف کردن همه بات‌ها...")
        self.running = False

        # متوقف کردن تمام تسک‌های فحش نامحدود
        if self.continuous_spam_tasks:
            logger.info(f"🛑 متوقف کردن {len(self.continuous_spam_tasks)} تسک فحش نامحدود...")
            for spam_key, task in list(self.continuous_spam_tasks.items()):
                try:
                    task.cancel()
                    logger.info(f"✅ تسک فحش {spam_key} متوقف شد")
                except:
                    pass
            self.continuous_spam_tasks.clear()

        tasks = []
        for bot_id in list(self.bots.keys()):
            tasks.append(self.stop_single_bot(bot_id))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def restart_bot(self, bot_id):
        """راه‌اندازی مجدد یک بات"""
        try:
            logger.info(f"🔄 راه‌اندازی مجدد بات {bot_id}...")

            # متوقف کردن بات فعلی
            await self.stop_single_bot(bot_id)
            await asyncio.sleep(2)

            # ایجاد مجدد بات
            if bot_id in self.bot_configs:
                config = self.bot_configs[bot_id]
                bot = await self.create_bot(bot_id, config)
                if bot:
                    # شروع مجدد بات
                    asyncio.create_task(self.start_single_bot(bot_id))
                    logger.info(f"✅ بات {bot_id} مجدداً راه‌اندازی شد")
                    return True

            return False

        except Exception as e:
            logger.error(f"❌ خطا در راه‌اندازی مجدد بات {bot_id}: {e}")
            return False

    def get_status(self):
        """دریافت وضعیت همه بات‌ها"""
        status = {
            'total_bots': len(self.bot_configs),
            'running_bots': len([b for b in self.bots.values() if b['status'] == 'running']),
            'error_bots': len([b for b in self.bots.values() if b['status'] == 'error']),
            'bots': []
        }

        for bot_id, bot_info in self.bots.items():
            status['bots'].append({
                'id': bot_id,
                'status': bot_info['status'],
                'config': bot_info['config']['session_name']
            })

        return status

    async def continuous_spam_attack(self, client, message, user_id, fosh_list, bot_id, chat_id):
        """فحش نامحدود به دشمن تا ایموجی ممنوعه فرستاده شود"""
        try:
            spam_key = f"{bot_id}_{user_id}_{chat_id}"
            fosh_count = 0
            
            logger.info(f"🔥 شروع فحش نامحدود بات {bot_id} به دشمن {user_id} در چت {chat_id}")
            
            while True:
                # بررسی اینکه آیا چت متوقف شده یا نه
                if chat_id in self.global_paused:
                    logger.info(f"⏸️ فحش نامحدود بات {bot_id} متوقف شد - چت {chat_id} در حالت توقف")
                    break
                
                # بررسی اینکه آیا تسک کنسل شده یا نه
                if spam_key not in self.continuous_spam_tasks:
                    logger.info(f"⏹️ فحش نامحدود بات {bot_id} متوقف شد - تسک حذف شده")
                    break
                
                try:
                    # انتخاب فحش تصادفی
                    selected = choice(fosh_list)
                    await self.send_fosh_reply(client, message, selected)
                    fosh_count += 1
                    
                    # لاگ هر 10 فحش
                    if fosh_count % 10 == 0:
                        logger.info(f"🔥 بات {bot_id} - ارسال {fosh_count} فحش به دشمن {user_id}")
                    
                    # دریافت تاخیر قابل تنظیم برای این بات
                    spam_delay = self.get_spam_delay(bot_id)
                    
                    # تقسیم تاخیر به قطعات کوچک برای چک کردن سریع‌تر توقف
                    sleep_intervals = max(1, int(spam_delay * 10))  # حداقل 1 قطعه، حداکثر 10 قطعه در هر ثانیه
                    interval_time = spam_delay / sleep_intervals if sleep_intervals > 0 else spam_delay
                    
                    should_break = False
                    for _ in range(sleep_intervals):
                        await asyncio.sleep(interval_time)
                        
                        # چک کردن توقف در هر قطعه
                        if chat_id in self.global_paused:
                            logger.info(f"⏸️ فحش نامحدود بات {bot_id} متوقف شد - چت {chat_id} در حالت توقف (حین انتظار)")
                            should_break = True
                            break
                        
                        if spam_key not in self.continuous_spam_tasks:
                            logger.info(f"⏹️ فحش نامحدود بات {bot_id} متوقف شد - تسک حذف شده (حین انتظار)")
                            should_break = True
                            break
                    
                    # اگر در loop داخلی break شد، از loop اصلی هم break کن
                    if should_break:
                        break
                    
                except FloodWait as e:
                    # اگر تلگرام محدودیت زمانی اعمال کرد
                    wait_time = float(e.value) if hasattr(e, 'value') else 30.0
                    logger.warning(f"⏳ فلود ویت {wait_time} ثانیه برای بات {bot_id}")
                    await asyncio.sleep(wait_time)
                    continue
                    
                except Exception as send_error:
                    logger.error(f"❌ خطا در ارسال فحش بات {bot_id}: {send_error}")
                    await asyncio.sleep(5)  # تاخیر بعد از خطا
                    continue
            
            # پاک کردن تسک از لیست
            if spam_key in self.continuous_spam_tasks:
                del self.continuous_spam_tasks[spam_key]
            
            # لاگ نهایی
            self.log_action(bot_id, "continuous_spam", user_id, f"{fosh_count} فحش نامحدود در {message.chat.title}")
            logger.info(f"✅ بات {bot_id} - فحش نامحدود تمام شد. کل ارسالی: {fosh_count} فحش به دشمن {user_id}")

        except asyncio.CancelledError:
            # تسک کنسل شده
            if spam_key in self.continuous_spam_tasks:
                del self.continuous_spam_tasks[spam_key]
            logger.info(f"🚫 فحش نامحدود بات {bot_id} به دشمن {user_id} کنسل شد")
            
        except Exception as e:
            # پاک کردن تسک در صورت خطا
            if spam_key in self.continuous_spam_tasks:
                del self.continuous_spam_tasks[spam_key]
            logger.error(f"❌ خطا در فحش نامحدود بات {bot_id}: {e}")

    async def staged_attack(self, client, message, user_id, fosh_list, bot_id):
        """حمله مرحله‌ای - 5 مرحله با فاصله زمانی (متد قدیمی - حفظ شده برای سازگاری)"""
        try:
            chat_id = message.chat.id

            # بررسی اینکه آیا چت متوقف شده یا نه
            if chat_id in self.global_paused:
                logger.info(f"⏸️ حمله مرحله‌ای بات {bot_id} متوقف شد - چت {chat_id} در حالت توقف")
                return

            # مرحله 1: فوری
            selected = choice(fosh_list)
            await self.send_fosh_reply(client, message, selected)
            logger.info(f"🔥 بات {bot_id} - مرحله 1: فحش به دشمن {user_id}")

            # مرحله 2: بعد از 1 ثانیه
            await asyncio.sleep(1)
            if chat_id not in self.global_paused:
                selected = choice(fosh_list)
                await self.send_fosh_reply(client, message, selected)
                logger.info(f"🔥 بات {bot_id} - مرحله 2: فحش به دشمن {user_id}")

            # مرحله 3: بعد از 1 ثانیه دیگر  
            await asyncio.sleep(1)
            if chat_id not in self.global_paused:
                selected = choice(fosh_list)
                await self.send_fosh_reply(client, message, selected)
                logger.info(f"🔥 بات {bot_id} - مرحله 3: فحش به دشمن {user_id}")

            # مرحله 4: بعد از 1 ثانیه دیگر
            await asyncio.sleep(1)
            if chat_id not in self.global_paused:
                selected = choice(fosh_list)
                await self.send_fosh_reply(client, message, selected)
                logger.info(f"🔥 بات {bot_id} - مرحله 4: فحش به دشمن {user_id}")

            # مرحله 5: بعد از 1 ثانیه دیگر
            await asyncio.sleep(1)
            if chat_id not in self.global_paused:
                selected = choice(fosh_list)
                await self.send_fosh_reply(client, message, selected)
                logger.info(f"🔥 بات {bot_id} - مرحله 5: فحش به دشمن {user_id}")

            # لاگ کامل حمله
            self.log_action(bot_id, "staged_attack", user_id, f"حمله مرحله‌ای 5 فحش در {message.chat.title}")
            logger.info(f"✅ بات {bot_id} - حمله مرحله‌ای کامل شد به دشمن {user_id}")

        except Exception as e:
            logger.error(f"خطا در حمله مرحله‌ای بات {bot_id}: {e}")

    async def send_fosh_reply(self, client, message, selected_content):
        """ارسال فحش"""
        try:
            content_text, media_type, file_id = selected_content

            if media_type and file_id:
                reply_methods = {
                    "photo": client.send_photo,
                    "video": client.send_video,
                    "animation": client.send_animation,
                    "sticker": client.send_sticker,
                    "audio": client.send_audio,
                    "voice": client.send_voice,
                    "video_note": client.send_video_note,
                    "document": client.send_document
                }

                method = reply_methods.get(media_type)
                if method:
                    await method(message.chat.id, file_id, reply_to_message_id=message.id)
            elif content_text:
                await client.send_message(message.chat.id, content_text, reply_to_message_id=message.id)
        except Exception as e:
            logger.error(f"خطا در ارسال فحش: {e}")

# متغیر کلی لانچر
launcher = UnifiedBotLauncher()

async def main():
    """تابع اصلی"""
    try:
        print("="*60)
        print("🤖 لانچر واحد بات‌های تلگرام")
        print("="*60)
        print("🎯 شروع همه ۹ بات در یک فرآیند...")
        print("📍 برای متوقف کردن: Ctrl+C")
        print("="*60)

        # شروع همه بات‌ها
        await launcher.start_all_bots()

    except KeyboardInterrupt:
        logger.info("🔴 متوقف شدن با Ctrl+C")
    except Exception as e:
        logger.error(f"❌ خطای غیرمنتظره: {e}")
    finally:
        await launcher.stop_all_bots()

if __name__ == "__main__":
    asyncio.run(main())