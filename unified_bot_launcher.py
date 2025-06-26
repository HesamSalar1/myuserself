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
        self.spam_paused = {}  # برای توقف اسپم در چت‌های خاص {chat_id: user_id}

        # تنظیمات بات‌ها
        self.bot_configs = {
            1: {
                'api_id': 23700094,
                'api_hash': "7cd6b0ba9c5b1a5f21b8b76f1e2b8e40",
                'session_name': "bots/bot1/my_bot1",
                'db_path': "bots/bot1/bot1_data.db",
                'log_path': "bots/bot1/bot1.log",
                'admin_id': 7143723023,
                'auto_reply_enabled': True
            },
            2: {
                'api_id': 29262538,
                'api_hash': "0417ebf26dbd92d3455d51595f2c923c",
                'session_name': "bots/bot2/my_bot2",
                'db_path': "bots/bot2/bot2_data.db",
                'log_path': "bots/bot2/bot2.log",
                'admin_id': 7419698159,
                'auto_reply_enabled': True
            },
            3: {
                'api_id': 21555907,
                'api_hash': "16f4e09d753bc4b182434d8e37f410cd",
                'session_name': "bots/bot3/my_bot3",
                'db_path': "bots/bot3/bot3_data.db",
                'log_path': "bots/bot3/bot3.log",
                'admin_id': 7607882302,
                'auto_reply_enabled': True
            },
            4: {
                'api_id': 15508294,
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot4/my_bot4",
                'db_path': "bots/bot4/bot4_data.db",
                'log_path': "bots/bot4/bot4.log",
                'admin_id': 7850529246,
                'auto_reply_enabled': True
            },
            5: {
                'api_id': 15508294,
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot5/my_bot5",
                'db_path': "bots/bot5/bot5_data.db",
                'log_path': "bots/bot5/bot5.log",
                'admin_id': 7850529246,
                'auto_reply_enabled': True
            },
            6: {
                'api_id': 15508294,
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot6/my_bot6",
                'db_path': "bots/bot6/bot6_data.db",
                'log_path': "bots/bot6/bot6.log",
                'admin_id': 7850529246,
                'auto_reply_enabled': True
            },
            7: {
                'api_id': 15508294,
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot7/my_bot7",
                'db_path': "bots/bot7/bot7_data.db",
                'log_path': "bots/bot7/bot7.log",
                'admin_id': 7850529246,
                'auto_reply_enabled': True
            },
            8: {
                'api_id': 15508294,
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot8/my_bot8",
                'db_path': "bots/bot8/bot8_data.db",
                'log_path': "bots/bot8/bot8.log",
                'admin_id': 7850529246,
                'auto_reply_enabled': True
            },
            9: {
                'api_id': 15508294,
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot9/my_bot9",
                'db_path': "bots/bot9/bot9_data.db",
                'log_path': "bots/bot9/bot9.log",
                'admin_id': 7850529246,
                'auto_reply_enabled': True
            }
        }

        # لیست همه admin_id ها
        self.all_admin_ids = {config['admin_id'] for config in self.bot_configs.values()}
        logger.info(f"🔐 لیست ادمین‌های مجاز: {list(self.all_admin_ids)}")

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

    def is_admin(self, user_id):
        """بررسی اینکه آیا کاربر ادمین است یا نه"""
        is_admin = user_id in self.all_admin_ids
        if is_admin:
            logger.debug(f"کاربر {user_id} ادمین است")
        else:
            logger.debug(f"کاربر {user_id} ادمین نیست - لیست ادمین‌ها: {list(self.all_admin_ids)}")
        return is_admin

    def should_pause_spam(self, message):
        """بررسی اینکه آیا باید اسپم را متوقف کرد"""
        if not message.text:
            return False
            
        # ایموجی‌های توقف اسپم
        stop_emojis = {'🎐', '🔮', '⚜️', '❓', '🪅', '🏵', '🌤', '☀️', '🌧', '⚡️', '💮'}
        
        # بررسی وجود ایموجی‌های خاص
        for emoji in stop_emojis:
            if emoji in message.text:
                return True
        
        # بررسی کامندهای خاص در ابتدای پیام
        stop_commands = ['/catch', '/grab', '/guess', '/take', '/arise']
        message_text = message.text.strip().lower()
        
        for command in stop_commands:
            if message_text.startswith(command):
                return True
                
        return False

    def get_bot_for_admin(self, user_id):
        """پیدا کردن شماره بات برای ادمین مشخص"""
        for bot_id, config in self.bot_configs.items():
            if config['admin_id'] == user_id:
                logger.debug(f"بات {bot_id} برای ادمین {user_id} پیدا شد")
                return bot_id
        logger.debug(f"هیچ باتی برای ادمین {user_id} پیدا نشد")
        return None

    async def create_bot(self, bot_id, config):
        """ایجاد و تنظیم یک بات"""
        try:
            # تنظیم پایگاه داده
            self.setup_database(bot_id, config['db_path'])

            # ایجاد کلاینت
            app = Client(
                config['session_name'],
                api_id=config['api_id'],
                api_hash=config['api_hash']
            )

            admin_id = config['admin_id']

            # تعریف هندلرها - همه کامندها برای همه ادمین‌ها
            def is_admin_user(_, __, message):
                if not message.from_user:
                    return False
                user_id = message.from_user.id
                is_admin = user_id in self.all_admin_ids
                if is_admin:
                    logger.info(f"✅ ادمین تشخیص داده شد: {user_id} برای بات {bot_id}")
                else:
                    logger.debug(f"❌ کاربر {user_id} ادمین نیست - ادمین‌های مجاز: {self.all_admin_ids}")
                return is_admin

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
                    admin_list = list(self.all_admin_ids)

                    text = f"🔍 **تست تشخیص ادمین:**\n\n"
                    text += f"👤 شما: `{user_id}`\n"
                    text += f"🤖 بات مربوطه: `{user_bot or 'یافت نشد'}`\n"
                    text += f"📋 لیست کامل ادمین‌ها: `{admin_list}`\n"
                    text += f"✅ وضعیت: ادمین تشخیص داده شده"

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
                    if not self.spam_paused:
                        await message.reply_text(f"✅ **وضعیت اسپم بات {bot_id}:** فعال در همه چت‌ها")
                        return
                    
                    text = f"⏸️ **چت‌های متوقف شده برای بات {bot_id}:**\n\n"
                    for chat_id, user_id in self.spam_paused.items():
                        try:
                            chat_info = await client.get_chat(chat_id)
                            chat_name = chat_info.title or f"چت {chat_id}"
                        except:
                            chat_name = f"چت {chat_id}"
                        
                        text += f"🔸 {chat_name}\n   └ توسط دشمن: `{user_id}`\n"
                    
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
                    
                    if chat_id in self.spam_paused:
                        user_id = self.spam_paused[chat_id]
                        del self.spam_paused[chat_id]
                        await message.reply_text(f"▶️ **اسپم بات {bot_id} در چت `{chat_id}` ازسرگیری شد**\n👤 دشمن قبلی: `{user_id}`")
                        self.log_action(bot_id, "manual_resume", message.from_user.id, f"ازسرگیری دستی اسپم در چت {chat_id}")
                    else:
                        await message.reply_text(f"✅ اسپم در چت `{chat_id}` قبلاً فعال بوده")
                        
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # راهنما
            @app.on_message(filters.command("help") & admin_filter)
            async def help_command(client, message):
                try:
                    help_text = f"""🤖 **راهنمای جامع ربات مدیریت هوشمند دوست و دشمن - بات {bot_id}**"""

                    # اضافه کردن توضیح اکو برای بات 3
                    if bot_id == 3:
                        help_text += f"""

🔊 **قابلیت اکو (ویژه بات 3):**
• `/echo` - اکو کردن پیام (فقط برای دشمنان)
  └ با ریپلای: پیام ریپلای شده را اکو می‌کند
  └ بدون ریپلای: خود پیام کامند را اکو می‌کند
  └ تمام انواع رسانه پشتیبانی می‌شود"""

                    text = help_text + f"""

🔥 **مدیریت سیستم فحش‌ها:**

🔥 **مدیریت سیستم فحش‌ها:**
• `/addfosh [متن]` - اضافه کردن فحش جدید (متن یا ریپلای رسانه)
  └ پشتیبانی: متن، عکس، ویدیو، گیف، استیکر، صوت
• `/delfosh [متن]` - حذف فحش مشخص از دیتابیس
• `/listfosh` - نمایش کامل فحش‌ها با صفحه‌بندی خودکار
• `/clearfosh` - حذف کلی تمام فحش‌ها (غیرقابل بازگشت)

👹 **سیستم مدیریت دشمنان:**
• `/setenemy` (ریپلای) - افزودن کاربر به لیست سیاه
• `/delenemy` (ریپلای) - حذف کاربر از لیست دشمنان
• `/listenemy` - نمایش جزئیات کامل دشمنان + تاریخ
• `/clearenemy` - پاک‌سازی کامل لیست دشمنان

😊 **سیستم مدیریت دوستان:**
• `/setfriend` (ریپلای) - افزودن کاربر به لیست VIP
• `/delfriend` (ریپلای) - حذف کاربر از لیست دوستان
• `/listfriend` - نمایش اطلاعات کامل دوستان + آمار
• `/clearfriend` - حذف کلی لیست دوستان

💬 **بانک کلمات دوستانه:**
• `/addword [متن]` - اضافه کردن پیام دوستانه (متن یا ریپلای رسانه)
  └ پشتیبانی: متن، عکس، ویدیو، گیف، استیکر، صوت
• `/delword [متن]` - حذف کلمه مشخص از بانک
• `/listword` - مشاهده تمام پیام‌های دوستانه
• `/clearword` - حذف کامل بانک

📢 **سیستم ارسال همگانی:**
• `/broadcast [پیام]` - ارسال همگانی متن به تمام گروه‌ها
• پشتیبانی از ارسال رسانه با ریپلای در broadcast

🤖 **تنظیمات سیستم:**
• `/runself` - فعال کردن پاسخگویی خودکار
• `/offself` - غیرفعال کردن پاسخگویی
• `/stats` - نمایش آمار کامل سیستم
• `/start` - راه‌اندازی مجدد ربات
• `/help` - نمایش این راهنما

⏸️ **کنترل هوشمند اسپم:**
• `/pausestatus` - نمایش وضعیت توقف اسپم در چت‌ها
• `/resumespam [chat_id]` - ازسرگیری دستی اسپم در چت مشخص

🛑 **توقف خودکار اسپم:**
• ایموجی‌های توقف: 🎐🔮⚜️❓🪅🏵🌤☀️🌧⚡️💮
• کامندهای توقف: `/catch` `/grab` `/guess` `/take` `/arise`
└ اسپم تا پیام بعدی دشمن متوقف می‌شود"""

                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # دستورات مدیریتی ادمین (فقط برای بات 1)
            if bot_id == 1:
                @app.on_message(filters.command("status") & admin_filter)
                async def admin_status_command(client, message):
                    try:
                        status = self.get_status()
                        status_text = f"""
📊 **وضعیت لانچر واحد:**

🤖 تعداد کل بات‌ها: {status['total_bots']}
✅ بات‌های فعال: {status['running_bots']}
❌ بات‌های خطا: {status['error_bots']}

📋 **جزئیات بات‌ها:**
"""

                        for bot_info in status['bots']:
                            emoji = "✅" if bot_info['status'] == 'running' else "❌"
                            status_text += f"{emoji} بات {bot_info['id']}: {bot_info['status']}\n"

                        await message.reply_text(status_text.strip())

                    except Exception as e:
                        await message.reply_text(f"❌ خطا: {e}")

                @app.on_message(filters.command("restart") & admin_filter)
                async def admin_restart_command(client, message):
                    try:
                        if len(message.command) < 2:
                            await message.reply_text("⚠️ استفاده: /restart [شماره_بات]\nمثال: /restart 2")
                            return

                        target_bot_id = int(message.command[1])
                        if target_bot_id not in self.bot_configs:
                            await message.reply_text(f"❌ بات {target_bot_id} یافت نشد")
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

                if not config['auto_reply_enabled'] or not message.from_user:
                    return

                user_id = message.from_user.id
                chat_id = message.chat.id

                # بررسی دشمن بودن
                enemy_list = self.get_enemy_list(bot_id)
                enemy_ids = {row[0] for row in enemy_list}

                if user_id in enemy_ids:
                    # بررسی اینکه آیا باید اسپم را متوقف کرد
                    if self.should_pause_spam(message):
                        # متوقف کردن اسپم برای این چت
                        self.spam_paused[chat_id] = user_id
                        logger.info(f"⏸️ بات {bot_id} - اسپم متوقف شد در چت {chat_id} توسط دشمن {user_id}")
                        
                        # لاگ عملیات توقف
                        self.log_action(bot_id, "spam_paused", user_id, f"توقف اسپم با ایموجی/کامند در {message.chat.title}")
                        return
                    
                    # بررسی اینکه آیا اسپم متوقف شده است
                    if chat_id in self.spam_paused and self.spam_paused[chat_id] == user_id:
                        # ازسرگیری اسپم - دشمن دوباره پیام فرستاده
                        del self.spam_paused[chat_id]
                        logger.info(f"▶️ بات {bot_id} - ازسرگیری اسپم در چت {chat_id} - دشمن {user_id} دوباره پیام فرستاد")
                        self.log_action(bot_id, "spam_resumed", user_id, f"ازسرگیری اسپم در {message.chat.title}")
                    
                    # اگر اسپم متوقف نیست، حمله کن
                    if chat_id not in self.spam_paused:
                        fosh_list = self.get_fosh_list(bot_id)
                        if fosh_list:
                            # مرحله 1: ارسال 2 فحش بلافاصله
                            tasks_immediate = []
                            for i in range(2):
                                selected = choice(fosh_list)
                                task = self.send_fosh_reply(client, message, selected)
                                tasks_immediate.append(task)
                            
                            await asyncio.gather(*tasks_immediate, return_exceptions=True)
                            
                            # مرحله 2: تاخیر 1 ثانیه و ارسال 2 فحش دیگر
                            await asyncio.sleep(1)
                            tasks_delayed1 = []
                            for i in range(2):
                                selected = choice(fosh_list)
                                task = self.send_fosh_reply(client, message, selected)
                                tasks_delayed1.append(task)
                            
                            await asyncio.gather(*tasks_delayed1, return_exceptions=True)
                            
                            # مرحله 3: تاخیر 1 ثانیه دیگر و ارسال آخرین فحش
                            await asyncio.sleep(1)
                            selected = choice(fosh_list)
                            await self.send_fosh_reply(client, message, selected)
                            
                            # لاگ حمله
                            self.log_action(bot_id, "timed_attack", user_id, f"ارسال 5 فحش با زمان‌بندی در {message.chat.title}")
                            logger.info(f"🔥 بات {bot_id} - ارسال 5 فحش با زمان‌بندی (2+2+1) به دشمن {user_id}")
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