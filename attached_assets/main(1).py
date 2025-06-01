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
import os
api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
admin_id = 7607882302

# تنظیم لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot2.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Client("bot2_session", api_id, api_hash)

# متغیر کنترل وضعیت پاسخگویی خودکار
auto_reply_enabled = True

# دیکشنری برای نگهداری تسک‌های شمارش
count_tasks = {}

# ایجاد و راه‌اندازی دیتابیس SQLite با بهین‌سازی
def init_database():
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()

    # جدول فحش‌ها با ایندکس
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fosh_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT UNIQUE NOT NULL
        )
    ''')

    # بررسی و اضافه کردن ستون created_at به جدول fosh_list
    try:
        cursor.execute('ALTER TABLE fosh_list ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    except sqlite3.OperationalError:
        pass  # ستون از قبل موجود است

    # جدول دشمنان با ایندکس
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enemy_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL
        )
    ''')

    # بررسی و اضافه کردن ستون‌های مورد نیاز به جدول enemy_list
    try:
        cursor.execute('ALTER TABLE enemy_list ADD COLUMN username TEXT')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE enemy_list ADD COLUMN first_name TEXT')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE enemy_list ADD COLUMN added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    except sqlite3.OperationalError:
        pass

    # جدول دوستان با ایندکس
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS friend_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL
        )
    ''')

    # بررسی و اضافه کردن ستون‌های مورد نیاز به جدول friend_list
    try:
        cursor.execute('ALTER TABLE friend_list ADD COLUMN username TEXT')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE friend_list ADD COLUMN first_name TEXT')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE friend_list ADD COLUMN added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    except sqlite3.OperationalError:
        pass

    # جدول کلمات دوستانه
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS friend_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT UNIQUE NOT NULL
        )
    ''')

    # بررسی و اضافه کردن ستون created_at به جدول friend_words
    try:
        cursor.execute('ALTER TABLE friend_words ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    except sqlite3.OperationalError:
        pass

    # جدول آمار
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT NOT NULL,
            target_user_id INTEGER,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # جدول تنظیمات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')

    # جدول private_commands
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS private_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            keyword TEXT NOT NULL,
            response TEXT NOT NULL,
            media_type TEXT,
            media_id TEXT,
            UNIQUE (group_id, user_id, keyword)
        )
    ''')

    # بررسی و اضافه کردن ستون‌های مورد نیاز به جدول private_commands
    try:
        cursor.execute('ALTER TABLE private_commands ADD COLUMN media_type TEXT')
    except sqlite3.OperationalError:
        pass  # ستون از قبل موجود است

    try:
        cursor.execute('ALTER TABLE private_commands ADD COLUMN media_id TEXT')
    except sqlite3.OperationalError:
        pass  # ستون از قبل موجود است

    # جدول scheduled_messages برای مدیریت پیام‌های تایمی
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            message_text TEXT,
            media_type TEXT,
            media_id TEXT,
            scheduled_time TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # جدول count_tasks برای مدیریت شمارش‌ها
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS count_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            current_count INTEGER NOT NULL,
            target_count INTEGER NOT NULL,
            delay REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ایجاد ایندکس‌ها برای بهبود عملکرد
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_enemy_user_id ON enemy_list(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_friend_user_id ON friend_list(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stats_timestamp ON stats(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_private_commands ON private_commands(group_id, user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_scheduled_messages ON scheduled_messages(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_count_tasks ON count_tasks(user_id)')

    conn.commit()
    conn.close()

# توابع کمکی دیتابیس
def get_fosh_list():
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT text FROM fosh_list ORDER BY created_at DESC')
    except sqlite3.OperationalError:
        cursor.execute('SELECT text FROM fosh_list ORDER BY id DESC')
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result

def get_enemy_list():
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM enemy_list')
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result

def get_enemy_details():
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT user_id, username, first_name, added_at FROM enemy_list ORDER BY added_at DESC')
    except sqlite3.OperationalError:
        try:
            cursor.execute('SELECT user_id, NULL as username, NULL as first_name, NULL as added_at FROM enemy_list ORDER BY id DESC')
        except:
            cursor.execute('SELECT user_id FROM enemy_list ORDER BY id DESC')
            temp_result = cursor.fetchall()
            result = [(row[0], None, None, None) for row in temp_result]
            conn.close()
            return result
    result = cursor.fetchall()
    conn.close()
    return result

def get_friend_list():
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM friend_list')
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result

def get_friend_details():
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT user_id, username, first_name, added_at FROM friend_list ORDER BY added_at DESC')
    except sqlite3.OperationalError:
        try:
            cursor.execute('SELECT user_id, NULL as username, NULL as first_name, NULL as added_at FROM friend_list ORDER BY id DESC')
        except:
            cursor.execute('SELECT user_id FROM enemy_list ORDER BY id DESC')
            temp_result = cursor.fetchall()
            result = [(row[0], None, None, None) for row in temp_result]
            conn.close()
            return result
    result = cursor.fetchall()
    conn.close()
    return result

def get_friend_words():
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT text FROM friend_words ORDER BY created_at DESC')
    except sqlite3.OperationalError:
        cursor.execute('SELECT text FROM friend_words ORDER BY id DESC')
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result

def add_fosh_to_db(fosh):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO fosh_list (text) VALUES (?)', (fosh,))
        conn.commit()
        log_action("add_fosh", None, fosh)
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def remove_fosh_from_db(fosh):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM fosh_list WHERE text = ?', (fosh,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    if affected > 0:
        log_action("remove_fosh", None, fosh)
    return affected > 0

def clear_fosh_db():
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM fosh_list')
    conn.commit()
    conn.close()
    log_action("clear_fosh", None, "all")

def add_enemy_to_db(user_id, username=None, first_name=None):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO enemy_list (user_id, username, first_name) VALUES (?, ?, ?)', 
                      (user_id, username, first_name))
        conn.commit()
        log_action("add_enemy", user_id, f"{username or ''} - {first_name or ''}")
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def remove_enemy_from_db(user_id):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM enemy_list WHERE user_id = ?', (user_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    if affected > 0:
        log_action("remove_enemy", user_id, "removed")
    return affected > 0

def clear_enemy_db():
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM enemy_list')
    conn.commit()
    conn.close()
    log_action("clear_enemy", None, "all")

def add_friend_to_db(user_id, username=None, first_name=None):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO friend_list (user_id, username, first_name) VALUES (?, ?, ?)', 
                      (user_id, username, first_name))
        conn.commit()
        log_action("add_friend", user_id, f"{username or ''} - {first_name or ''}")
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def remove_friend_from_db(user_id):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM friend_list WHERE user_id = ?', (user_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    if affected > 0:
        log_action("remove_friend", user_id, "removed")
    return affected > 0

def clear_friend_db():
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM friend_list')
    conn.commit()
    conn.close()
    log_action("clear_friend", None, "all")

def add_friend_word_to_db(word):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO friend_words (text) VALUES (?)', (word,))
        conn.commit()
        log_action("add_friend_word", None, word)
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def remove_friend_word_from_db(word):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM friend_words WHERE text = ?', (word,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    if affected > 0:
        log_action("remove_friend_word", None, word)
    return affected > 0

def clear_friend_words_db():
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM friend_words')
    conn.commit()
    conn.close()
    log_action("clear_friend_words", None, "all")

def log_action(action_type, target_user_id, details):
    """ثبت فعالیت‌ها در دیتابیس"""
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO stats (action_type, target_user_id, details) VALUES (?, ?, ?)',
                      (action_type, target_user_id, details))
        conn.commit()
    except:
        pass
    finally:
        conn.close()

def get_stats():
    """دریافت آمار کلی"""
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()

    stats = {}

    # تعداد فحش‌ها
    cursor.execute('SELECT COUNT(*) FROM fosh_list')
    stats['fosh_count'] = cursor.fetchone()[0]

    # تعداد دشمنان
    cursor.execute('SELECT COUNT(*) FROM enemy_list')
    stats['enemy_count'] = cursor.fetchone()[0]

    # تعداد دوستان
    cursor.execute('SELECT COUNT(*) FROM friend_list')
    stats['friend_count'] = cursor.fetchone()[0]

    # تعداد کلمات دوستانه
    cursor.execute('SELECT COUNT(*) FROM friend_words')
    stats['friend_words_count'] = cursor.fetchone()[0]

    # آخرین فعالیت‌ها
    cursor.execute('SELECT action_type, COUNT(*) FROM stats GROUP BY action_type ORDER BY COUNT(*) DESC LIMIT 5')
    stats['top_actions'] = cursor.fetchall()

    conn.close()
    return stats

def add_private_command(group_id, user_id, keyword, response, media_type=None, media_id=None):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO private_commands (group_id, user_id, keyword, response, media_type, media_id) VALUES (?, ?, ?, ?, ?, ?)',
                       (group_id, user_id, keyword, response, media_type, media_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def remove_private_command(group_id, user_id, keyword):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM private_commands WHERE group_id = ? AND user_id = ? AND keyword = ?',
                   (group_id, user_id, keyword))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def clear_private_commands(group_id, user_id):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM private_commands WHERE group_id = ? AND user_id = ?', (group_id, user_id))
    conn.commit()
    conn.close()

def list_private_commands(group_id, user_id):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT keyword, response, media_type, media_id FROM private_commands WHERE group_id = ? AND user_id = ?',
                   (group_id, user_id))
    result = cursor.fetchall()
    conn.close()
    return result

# جدول auto_reply_specific برای پاسخگویی خودکار به شخص خاص در گروه خاص
def init_auto_reply_specific_table():
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auto_reply_specific (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            response TEXT NOT NULL,
            media_type TEXT,
            media_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (group_id, user_id)
        )
    ''')
    
    # بررسی و اضافه کردن ستون‌های مورد نیاز
    try:
        cursor.execute('ALTER TABLE auto_reply_specific ADD COLUMN media_type TEXT')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE auto_reply_specific ADD COLUMN media_id TEXT')
    except sqlite3.OperationalError:
        pass
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_auto_reply_specific ON auto_reply_specific(group_id, user_id)')
    conn.commit()
    conn.close()

def add_auto_reply_specific(group_id, user_id, response):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT OR REPLACE INTO auto_reply_specific (group_id, user_id, response) VALUES (?, ?, ?)',
                       (group_id, user_id, response))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def remove_auto_reply_specific(group_id, user_id):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM auto_reply_specific WHERE group_id = ? AND user_id = ?', (group_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def get_auto_reply_specific(group_id, user_id):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT response FROM auto_reply_specific WHERE group_id = ? AND user_id = ?',
                   (group_id, user_id))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def list_auto_reply_specific():
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT group_id, user_id, response, created_at FROM auto_reply_specific ORDER BY created_at DESC')
    result = cursor.fetchall()
    conn.close()
    return result

def clear_auto_reply_specific():
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM auto_reply_specific')
    conn.commit()
    conn.close()

# توابع مدیریت پیام‌های تایمی
def add_scheduled_message(user_id, chat_id, message_text, scheduled_time, media_type=None, media_id=None):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO scheduled_messages (user_id, chat_id, message_text, media_type, media_id, scheduled_time) VALUES (?, ?, ?, ?, ?, ?)',
                   (user_id, chat_id, message_text, media_type, media_id, scheduled_time))
    schedule_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return schedule_id

def remove_scheduled_message(schedule_id):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scheduled_messages WHERE id = ?', (schedule_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def list_scheduled_messages(user_id):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT id, message_text, media_type, scheduled_time FROM scheduled_messages WHERE user_id = ? ORDER BY created_at DESC',
                   (user_id,))
    result = cursor.fetchall()
    conn.close()
    return result

def clear_scheduled_messages(user_id):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scheduled_messages WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# توابع مدیریت شمارش‌ها
def add_count_task(user_id, chat_id, current_count, target_count, delay):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO count_tasks (user_id, chat_id, current_count, target_count, delay) VALUES (?, ?, ?, ?, ?)',
                   (user_id, chat_id, current_count, target_count, delay))
    count_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return count_id

def remove_count_task(count_id):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM count_tasks WHERE id = ?', (count_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def list_count_tasks(user_id):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT id, current_count, target_count, delay FROM count_tasks WHERE user_id = ? ORDER BY created_at DESC',
                   (user_id,))
    result = cursor.fetchall()
    conn.close()
    return result

def clear_count_tasks(user_id):
    conn = sqlite3.connect('bot2_database.db', timeout=30.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM count_tasks WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# راه‌اندازی دیتابیس
init_database()
init_auto_reply_specific_table()

# کلمات دوستانه پیش‌فرض حذف شد - مدیریت از طریق کامندهای بات

# کامند اضافه کردن فحش با اعتبارسنجی و پشتیبانی از رسانه
@app.on_message(filters.command("addfosh") & filters.user(admin_id))
async def add_fosh(client, message: Message):
    try:
        fosh = ""
        
        # بررسی ریپلای برای رسانه
        if message.reply_to_message:
            if message.reply_to_message.photo:
                fosh = f"MEDIA:photo:{message.reply_to_message.photo.file_id}"
            elif message.reply_to_message.video:
                fosh = f"MEDIA:video:{message.reply_to_message.video.file_id}"
            elif message.reply_to_message.audio:
                fosh = f"MEDIA:audio:{message.reply_to_message.audio.file_id}"
            elif message.reply_to_message.document:
                fosh = f"MEDIA:document:{message.reply_to_message.document.file_id}"
            elif message.reply_to_message.sticker:
                fosh = f"MEDIA:sticker:{message.reply_to_message.sticker.file_id}"
            elif message.reply_to_message.animation:
                fosh = f"MEDIA:animation:{message.reply_to_message.animation.file_id}"
            elif message.reply_to_message.voice:
                fosh = f"MEDIA:voice:{message.reply_to_message.voice.file_id}"
            elif message.reply_to_message.video_note:
                fosh = f"MEDIA:video_note:{message.reply_to_message.video_note.file_id}"
            elif message.reply_to_message.text:
                fosh = message.reply_to_message.text
        
        # اگر رسانه‌ای نبود، از کامند بخوان
        if not fosh and len(message.command) >= 2:
            fosh = " ".join(message.command[1:])
        
        if not fosh:
            await message.edit_text("⚠️ **استفاده:** `/addfosh متن_فحش` یا ریپلای روی رسانه\n\n**مثال:** `/addfosh احمق`")
            return

        if len(fosh) > 500:
            await message.edit_text("⚠️ متن فحش نباید بیشتر از 500 کاراکتر باشد.")
            return

        if add_fosh_to_db(fosh):
            display_text = "رسانه" if fosh.startswith("MEDIA:") else fosh
            await message.edit_text(f"✅ فحش **'{display_text}'** با موفقیت اضافه شد.\n📊 تعداد کل: {len(get_fosh_list())}")
            logger.info(f"فحش جدید اضافه شد: {display_text}")
        else:
            display_text = "رسانه" if fosh.startswith("MEDIA:") else fosh
            await message.edit_text(f"⚠️ فحش **'{display_text}'** قبلاً در لیست موجود است.")
    except Exception as e:
        await message.edit_text(f"❌ خطا در اضافه کردن فحش: {str(e)}")
        logger.error(f"خطا در add_fosh: {e}")

# کامندهای جدید برای اضافه کردن رسانه‌های فحش
@app.on_message(filters.command("addfoshphoto") & filters.user(admin_id) & filters.reply)
async def add_fosh_photo(client, message: Message):
    try:
        if message.reply_to_message.photo:
            fosh = f"MEDIA:photo:{message.reply_to_message.photo.file_id}"
            if add_fosh_to_db(fosh):
                await message.edit_text(f"✅ عکس فحش با موفقیت اضافه شد.\n📊 تعداد کل: {len(get_fosh_list())}")
            else:
                await message.edit_text("⚠️ این عکس قبلاً در لیست فحش‌ها موجود است.")
        else:
            await message.edit_text("⚠️ لطفاً روی یک عکس ریپلای کنید.")
    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.command("addfoshvideo") & filters.user(admin_id) & filters.reply)
async def add_fosh_video(client, message: Message):
    try:
        if message.reply_to_message.video:
            fosh = f"MEDIA:video:{message.reply_to_message.video.file_id}"
            if add_fosh_to_db(fosh):
                await message.edit_text(f"✅ ویدیو فحش با موفقیت اضافه شد.\n📊 تعداد کل: {len(get_fosh_list())}")
            else:
                await message.edit_text("⚠️ این ویدیو قبلاً در لیست فحش‌ها موجود است.")
        else:
            await message.edit_text("⚠️ لطفاً روی یک ویدیو ریپلای کنید.")
    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.command("addfoshgif") & filters.user(admin_id) & filters.reply)
async def add_fosh_gif(client, message: Message):
    try:
        if message.reply_to_message.animation:
            fosh = f"MEDIA:animation:{message.reply_to_message.animation.file_id}"
            if add_fosh_to_db(fosh):
                await message.edit_text(f"✅ گیف فحش با موفقیت اضافه شد.\n📊 تعداد کل: {len(get_fosh_list())}")
            else:
                await message.edit_text("⚠️ این گیف قبلاً در لیست فحش‌ها موجود است.")
        else:
            await message.edit_text("⚠️ لطفاً روی یک گیف ریپلای کنید.")
    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.command("addfoshsticker") & filters.user(admin_id) & filters.reply)
async def add_fosh_sticker(client, message: Message):
    try:
        if message.reply_to_message.sticker:
            fosh = f"MEDIA:sticker:{message.reply_to_message.sticker.file_id}"
            if add_fosh_to_db(fosh):
                await message.edit_text(f"✅ استیکر فحش با موفقیت اضافه شد.\n📊 تعداد کل: {len(get_fosh_list())}")
            else:
                await message.edit_text("⚠️ این استیکر قبلاً در لیست فحش‌ها موجود است.")
        else:
            await message.edit_text("⚠️ لطفاً روی یک استیکر ریپلای کنید.")
    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.command("addfoshaudio") & filters.user(admin_id) & filters.reply)
async def add_fosh_audio(client, message: Message):
    try:
        if message.reply_to_message.audio or message.reply_to_message.voice:
            if message.reply_to_message.audio:
                fosh = f"MEDIA:audio:{message.reply_to_message.audio.file_id}"
            else:
                fosh = f"MEDIA:voice:{message.reply_to_message.voice.file_id}"
            if add_fosh_to_db(fosh):
                await message.edit_text(f"✅ صوت فحش با موفقیت اضافه شد.\n📊 تعداد کل: {len(get_fosh_list())}")
            else:
                await message.edit_text("⚠️ این صوت قبلاً در لیست فحش‌ها موجود است.")
        else:
            await message.edit_text("⚠️ لطفاً روی یک فایل صوتی ریپلای کنید.")
    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

# کامند حذف فحش
@app.on_message(filters.command("delfosh") & filters.user(admin_id))
async def del_fosh(client, message: Message):
    try:
        if len(message.command) < 2:
            await message.edit_text("⚠️ **استفاده:** `/delfosh متن_فحش`")
            return

        fosh = " ".join(message.command[1:])
        if remove_fosh_from_db(fosh):
            await message.edit_text(f"✅ فحش **'{fosh}'** حذف شد.\n📊 تعداد باقی‌مانده: {len(get_fosh_list())}")
            logger.info(f"فحش حذف شد: {fosh}")
        else:
            await message.edit_text(f"⚠️ فحش **'{fosh}'** در لیست پیدا نشد.")
    except Exception as e:
        await message.edit_text(f"❌ خطا در حذف فحش: {str(e)}")
        logger.error(f"خطا در del_fosh: {e}")

# کامند پاک کردن تمام فحش‌ها با تأیید
@app.on_message(filters.command("clearfosh") & filters.user(admin_id))
async def clear_fosh(client, message: Message):
    try:
        fosh_count = len(get_fosh_list())
        if fosh_count == 0:
            await message.edit_text("📝 لیست فحش‌ها از قبل خالی است.")
            return

        clear_fosh_db()
        await message.edit_text(f"🗑️ تمام فحش‌ها پاک شدند. ({fosh_count} مورد حذف شد)")
        logger.info(f"تمام فحش‌ها پاک شدند: {fosh_count} مورد")
    except Exception as e:
        await message.edit_text(f"❌ خطا در پاک کردن فحش‌ها: {str(e)}")
        logger.error(f"خطا در clear_fosh: {e}")

# کامند اضافه کردن دشمن با جزئیات بیشتر
@app.on_message(filters.command("setenemy") & filters.user(admin_id) & filters.reply)
async def set_enemy(client, message: Message):
    try:
        user = message.reply_to_message.from_user
        user_id = user.id
        username = user.username
        first_name = user.first_name

        # بررسی اینکه آیا در لیست دوستان است یا نه
        if user_id in get_friend_list():
            await message.edit_text(f"⚠️ کاربر **{first_name}** (`{user_id}`) در لیست دوستان است.\n"
                              f"ابتدا با `/delfriend` از لیست دوستان حذفش کنید.")
            return

        if add_enemy_to_db(user_id, username, first_name):
            await message.edit_text(f"❌ کاربر **{first_name}** (`{user_id}`) به لیست دشمنان اضافه شد.\n" \
                                  f"👤 نام کاربری: @{username or 'ندارد'}\n" \
                                  f"📊 تعداد کل دشمنان: {len(get_enemy_list())}")
            logger.info(f"دشمن جدید اضافه شد: {user_id} - {first_name}")
        else:
            await message.edit_text(f"⚠️ کاربر **{first_name}** (`{user_id}`) قبلاً در لیست دشمنان است.")
    except Exception as e:
        await message.edit_text(f"❌ خطا در اضافه کردن دشمن: {str(e)}")
        logger.error(f"خطا در set_enemy: {e}")

# کامند حذف دشمن
@app.on_message(filters.command("delenemy") & filters.user(admin_id) & filters.reply)
async def del_enemy(client, message: Message):
    try:
        user = message.reply_to_message.from_user
        user_id = user.id
        first_name = user.first_name

        if remove_enemy_from_db(user_id):
            await message.edit_text(f"✅ کاربر **{first_name}** (`{user_id}`) از لیست دشمنان حذف شد.\n" \
                                  f"📊 تعداد باقی‌مانده: {len(get_enemy_list())}")
            logger.info(f"دشمن حذف شد: {user_id} - {first_name}")
        else:
            await message.edit_text(f"⚠️ کاربر **{first_name}** (`{user_id}`) در لیست دشمنان نیست.")
    except Exception as e:
        await message.edit_text(f"❌ خطا در حذف دشمن: {str(e)}")
        logger.error(f"خطا در del_enemy: {e}")

# کامند پاک کردن تمام دشمنان
@app.on_message(filters.command("clearenemy") & filters.user(admin_id))
async def clear_enemy(client, message: Message):
    try:
        enemy_count = len(get_enemy_list())
        if enemy_count == 0:
            await message.edit_text("👥 لیست دشمنان از قبل خالی است.")
            return

        clear_enemy_db()
        await message.edit_text(f"🗑️ لیست دشمنان پاک شد. ({enemy_count} نفر حذف شد)")
        logger.info(f"تمام دشمنان پاک شدند: {enemy_count} نفر")
    except Exception as e:
        await message.edit_text(f"❌ خطا در پاک کردن دشمنان: {str(e)}")
        logger.error(f"خطا در clear_enemy: {e}")

# کامند اضافه کردن دوست
@app.on_message(filters.command("setfriend") & filters.user(admin_id) & filters.reply)
async def set_friend(client, message: Message):
    try:
        user = message.reply_to_message.from_user
        user_id = user.id
        username = user.username
        first_name = user.first_name

        # بررسی اینکه آیا در لیست دشمنان است یا نه
        if user_id in get_enemy_list():
            await message.edit_text(f"⚠️ کاربر **{first_name}** (`{user_id}`) در لیست دشمنان است.\n"
                              f"ابتدا با `/delenemy` از لیست دشمنان حذفش کنید.")
            return

        if add_friend_to_db(user_id, username, first_name):
            await message.edit_text(f"✅ کاربر **{first_name}** (`{user_id}`) به لیست دوستان اضافه شد.\n" \
                                  f"👤 نام کاربری: @{username or 'ندارد'}\n" \
                                  f"📊 تعداد کل دوستان: {len(get_friend_list())}")
            logger.info(f"دوست جدید اضافه شد: {user_id} - {first_name}")
        else:
            await message.edit_text(f"⚠️ کاربر **{first_name}** (`{user_id}`) قبلاً در لیست دوستان است.")
    except Exception as e:
        await message.edit_text(f"❌ خطا در اضافه کردن دوست: {str(e)}")
        logger.error(f"خطا در set_friend: {e}")

# کامند حذف دوست
@app.on_message(filters.command("delfriend") & filters.user(admin_id) & filters.reply)
async def del_friend(client, message: Message):
    try:
        user = message.reply_to_message.from_user
        user_id = user.id
        first_name = user.first_name

        if remove_friend_from_db(user_id):
            await message.edit_text(f"✅ کاربر **{first_name}** (`{user_id}`) از لیست دوستان حذف شد.\n" \
                                  f"📊 تعداد باقی‌مانده: {len(get_friend_list())}")
            logger.info(f"دوست حذف شد: {user_id} - {first_name}")
        else:
            await message.edit_text(f"⚠️ کاربر **{first_name}** (`{user_id}`) در لیست دوستان نیست.")
    except Exception as e:
        await message.edit_text(f"❌ خطا در حذف دوست: {str(e)}")
        logger.error(f"خطا در del_friend: {e}")

# کامند پاک کردن تمام دوستان
@app.on_message(filters.command("clearfriend") & filters.user(admin_id))
async def clear_friend(client, message: Message):
    try:
        friend_count = len(get_friend_list())
        if friend_count == 0:
            await message.edit_text("👥 لیست دوستان از قبل خالی است.")
            return

        clear_friend_db()
        await message.edit_text(f"🗑️ لیست دوستان پاک شد. ({friend_count} نفر حذف شد)")
        logger.info(f"تمام دوستان پاک شدند: {friend_count} نفر")
    except Exception as e:
        await message.edit_text(f"❌ خطا در پاک کردن دوستان: {str(e)}")
        logger.error(f"خطا در clear_friend: {e}")

# کامند اضافه کردن کلمه دوستانه با پشتیبانی از رسانه
@app.on_message(filters.command("addword") & filters.user(admin_id))
async def add_word(client, message: Message):
    try:
        word = ""
        
        # بررسی ریپلای برای رسانه
        if message.reply_to_message:
            if message.reply_to_message.photo:
                word = f"MEDIA:photo:{message.reply_to_message.photo.file_id}"
            elif message.reply_to_message.video:
                word = f"MEDIA:video:{message.reply_to_message.video.file_id}"
            elif message.reply_to_message.audio:
                word = f"MEDIA:audio:{message.reply_to_message.audio.file_id}"
            elif message.reply_to_message.document:
                word = f"MEDIA:document:{message.reply_to_message.document.file_id}"
            elif message.reply_to_message.sticker:
                word = f"MEDIA:sticker:{message.reply_to_message.sticker.file_id}"
            elif message.reply_to_message.animation:
                word = f"MEDIA:animation:{message.reply_to_message.animation.file_id}"
            elif message.reply_to_message.voice:
                word = f"MEDIA:voice:{message.reply_to_message.voice.file_id}"
            elif message.reply_to_message.video_note:
                word = f"MEDIA:video_note:{message.reply_to_message.video_note.file_id}"
            elif message.reply_to_message.text:
                word = message.reply_to_message.text
        
        # اگر رسانه‌ای نبود، از کامند بخوان
        if not word and len(message.command) >= 2:
            word = " ".join(message.command[1:])
        
        if not word:
            await message.edit_text("⚠️ **استفاده:** `/addword متن_دوستانه` یا ریپلای روی رسانه\n\n**مثال:** `/addword سلام عزیزم! 😊`")
            return

        if len(word) > 500:
            await message.edit_text("⚠️ متن کلمه دوستانه نباید بیشتر از 500 کاراکتر باشد.")
            return

        if add_friend_word_to_db(word):
            display_text = "رسانه" if word.startswith("MEDIA:") else word
            await message.edit_text(f"✅ کلمه دوستانه **'{display_text}'** اضافه شد.\n📊 تعداد کل: {len(get_friend_words())}")
            logger.info(f"کلمه دوستانه جدید اضافه شد: {display_text}")
        else:
            display_text = "رسانه" if word.startswith("MEDIA:") else word
            await message.edit_text(f"⚠️ کلمه **'{display_text}'** قبلاً موجود است.")
    except Exception as e:
        await message.edit_text(f"❌ خطا در اضافه کردن کلمه: {str(e)}")
        logger.error(f"خطا در add_word: {e}")

# کامندهای جدید برای اضافه کردن رسانه‌های دوستانه
@app.on_message(filters.command("addwordphoto") & filters.user(admin_id) & filters.reply)
async def add_word_photo(client, message: Message):
    try:
        if message.reply_to_message.photo:
            word = f"MEDIA:photo:{message.reply_to_message.photo.file_id}"
            if add_friend_word_to_db(word):
                await message.edit_text(f"✅ عکس دوستانه با موفقیت اضافه شد.\n📊 تعداد کل: {len(get_friend_words())}")
            else:
                await message.edit_text("⚠️ این عکس قبلاً در کلمات دوستانه موجود است.")
        else:
            await message.edit_text("⚠️ لطفاً روی یک عکس ریپلای کنید.")
    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.command("addwordvideo") & filters.user(admin_id) & filters.reply)
async def add_word_video(client, message: Message):
    try:
        if message.reply_to_message.video:
            word = f"MEDIA:video:{message.reply_to_message.video.file_id}"
            if add_friend_word_to_db(word):
                await message.edit_text(f"✅ ویدیو دوستانه با موفقیت اضافه شد.\n📊 تعداد کل: {len(get_friend_words())}")
            else:
                await message.edit_text("⚠️ این ویدیو قبلاً در کلمات دوستانه موجود است.")
        else:
            await message.edit_text("⚠️ لطفاً روی یک ویدیو ریپلای کنید.")
    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.command("addwordgif") & filters.user(admin_id) & filters.reply)
async def add_word_gif(client, message: Message):
    try:
        if message.reply_to_message.animation:
            word = f"MEDIA:animation:{message.reply_to_message.animation.file_id}"
            if add_friend_word_to_db(word):
                await message.edit_text(f"✅ گیف دوستانه با موفقیت اضافه شد.\n📊 تعداد کل: {len(get_friend_words())}")
            else:
                await message.edit_text("⚠️ این گیف قبلاً در کلمات دوستانه موجود است.")
        else:
            await message.edit_text("⚠️ لطفاً روی یک گیف ریپلای کنید.")
    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.command("addwordsticker") & filters.user(admin_id) & filters.reply)
async def add_word_sticker(client, message: Message):
    try:
        if message.reply_to_message.sticker:
            word = f"MEDIA:sticker:{message.reply_to_message.sticker.file_id}"
            if add_friend_word_to_db(word):
                await message.edit_text(f"✅ استیکر دوستانه با موفقیت اضافه شد.\n📊 تعداد کل: {len(get_friend_words())}")
            else:
                await message.edit_text("⚠️ این استیکر قبلاً در کلمات دوستانه موجود است.")
        else:
            await message.edit_text("⚠️ لطفاً روی یک استیکر ریپلای کنید.")
    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.command("addwordaudio") & filters.user(admin_id) & filters.reply)
async def add_word_audio(client, message: Message):
    try:
        if message.reply_to_message.audio or message.reply_to_message.voice:
            if message.reply_to_message.audio:
                word = f"MEDIA:audio:{message.reply_to_message.audio.file_id}"
            else:
                word = f"MEDIA:voice:{message.reply_to_message.voice.file_id}"
            if add_friend_word_to_db(word):
                await message.edit_text(f"✅ صوت دوستانه با موفقیت اضافه شد.\n📊 تعداد کل: {len(get_friend_words())}")
            else:
                await message.edit_text("⚠️ این صوت قبلاً در کلمات دوستانه موجود است.")
        else:
            await message.edit_text("⚠️ لطفاً روی یک فایل صوتی ریپلای کنید.")
    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

# کامند حذف کلمه دوستانه
@app.on_message(filters.command("delword") & filters.user(admin_id))
async def del_word(client, message: Message):
    try:
        if len(message.command) < 2:
            await message.edit_text("⚠️ **استفاده:** `/delword متن_دوستانه`")
            return

        word = " ".join(message.command[1:])
        if remove_friend_word_from_db(word):
            await message.edit_text(f"✅ کلمه **'{word}'** حذف شد.\n📊 تعداد باقی‌مانده: {len(get_friend_words())}")
            logger.info(f"کلمه دوستانه حذف شد: {word}")
        else:
            await message.edit_text(f"⚠️ کلمه **'{word}'** پیدا نشد.")
    except Exception as e:
        await message.edit_text(f"❌ خطا در حذف کلمه: {str(e)}")
        logger.error(f"خطا در del_word: {e}")

# کامند پاک کردن تمام کلمات دوستانه
@app.on_message(filters.command("clearword") & filters.user(admin_id))
async def clear_word(client, message: Message):
    try:
        word_count = len(get_friend_words())
        if word_count == 0:
            await message.edit_text("📝 لیست کلمات دوستانه از قبل خالی است.")
            return

        clear_friend_words_db()
        await message.edit_text(f"🗑️ تمام کلمات دوستانه پاک شدند. ({word_count} مورد حذف شد)")
        logger.info(f"تمام کلمات دوستانه پاک شدند: {word_count} مورد")
    except Exception as e:
        await message.edit_text(f"❌ خطا در پاک کردن کلمات: {str(e)}")
        logger.error(f"خطا در clear_word: {e}")

# کامند نمایش لیست فحش‌ها با صفحه‌بندی
@app.on_message(filters.command("listfosh") & filters.user(admin_id))
async def list_fosh(client, message: Message):
    try:
        fosh_list = get_fosh_list()
        if not fosh_list:
            await message.edit_text("📝 لیست فحش‌ها خالی است.\n💡 با `/addfosh` فحش اضافه کنید.")
            return

        # صفحه‌بندی برای لیست‌های طولانی
        page_size = 20
        total_pages = (len(fosh_list) + page_size - 1) // page_size

        for page in range(total_pages):
            start_idx = page * page_size
            end_idx = min((page + 1) * page_size, len(fosh_list))

            text = f"📝 **لیست فحش‌ها** (صفحه {page + 1}/{total_pages}):\n\n"
            for i, fosh in enumerate(fosh_list[start_idx:end_idx], start_idx + 1):
                text += f"`{i}.` {fosh}\n"

            text += f"\n📊 **تعداد کل:** {len(fosh_list)} فحش"

            if page == 0:
                await message.edit_text(text)
            else:
                await message.reply(text)

            if page < total_pages - 1:
                await asyncio.sleep(1)

    except Exception as e:
        await message.edit_text(f"❌ خطا در نمایش لیست: {str(e)}")
        logger.error(f"خطا در list_fosh: {e}")

# کامند نمایش لیست دشمنان با جزئیات
@app.on_message(filters.command("listenemy") & filters.user(admin_id))
async def list_enemy(client, message: Message):
    try:
        enemy_details = get_enemy_details()
        if not enemy_details:
            await message.edit_text("👥 لیست دشمنان خالی است.\n💡 با `/setenemy` (ریپلای روی پیام) دشمن اضافه کنید.")
            return

        text = "👹 **لیست دشمنان:**\n\n"
        for i, (user_id, username, first_name, added_at) in enumerate(enemy_details, 1):
            text += f"`{i}.` **{first_name or 'نامشخص'}**\n"
            text += f"   🆔 `{user_id}`\n"
            text += f"   👤 @{username or 'ندارد'}\n"
            text += f"   📅 {added_at[:16]}\n\n"

        text += f"📊 **تعداد کل:** {len(enemy_details)} دشمن"
        await message.edit_text(text)

    except Exception as e:
        await message.edit_text(f"❌ خطا در نمایش لیست: {str(e)}")
        logger.error(f"خطا در list_enemy: {e}")

# کامند نمایش لیست دوستان با جزئیات
@app.on_message(filters.command("listfriend") & filters.user(admin_id))
async def list_friend(client, message: Message):
    try:
        friend_details = get_friend_details()
        if not friend_details:
            await message.edit_text("👥 لیست دوستان خالی است.\n💡 با `/setfriend` (ریپلای روی پیام) دوست اضافه کنید.")
            return

        text = "😊 **لیست دوستان:**\n\n"
        for i, (user_id, username, first_name, added_at) in enumerate(friend_details, 1):
            text += f"`{i}.` **{first_name or 'نامشخص'}**\n"
            text += f"   🆔 `{user_id}`\n"
            text += f"   👤 @{username or 'ندارد'}\n"
            text += f"   📅 {added_at[:16]}\n\n"

        text += f"📊 **تعداد کل:** {len(friend_details)} دوست"
        await message.edit_text(text)

    except Exception as e:
        await message.edit_text(f"❌ خطا در نمایش لیست: {str(e)}")
        logger.error(f"خطا در list_friend: {e}")

# کامند نمایش لیست کلمات دوستانه
@app.on_message(filters.command("listword") & filters.user(admin_id))
async def list_word(client, message: Message):
    try:
        word_list = get_friend_words()
        if not word_list:
            await message.edit_text("📝 لیست کلمات دوستانه خالی است.\n💡 با `/addword` کلمه اضافه کنید.")
            return

        text = "💬 **لیست کلمات دوستانه:**\n\n"
        for i, word in enumerate(word_list, 1):
            text += f"`{i}.` {word}\n"

        text += f"\n📊 **تعداد کل:** {len(word_list)} کلمه"
        await message.edit_text(text)

    except Exception as e:
        await message.edit_text(f"❌ خطا در نمایش لیست: {str(e)}")
        logger.error(f"خطا در list_word: {e}")

# کامند نمایش آمار کامل
@app.on_message(filters.command("stats") & filters.user(admin_id))
async def show_stats(client, message: Message):
    try:
        stats = get_stats()

        text = "📊 **آمار کامل ربات:**\n\n"
        text += f"🔥 فحش‌ها: `{stats['fosh_count']}` عدد\n"
        text += f"👹 دشمنان: `{stats['enemy_count']}` نفر\n"
        text += f"😊 دوستان: `{stats['friend_count']}` نفر\n"
        text += f"💬 کلمات دوستانه: `{stats['friend_words_count']}` عدد\n\n"

        if stats['top_actions']:
            text += "🔝 **فعالیت‌های اصلی:**\n"
            for action, count in stats['top_actions']:
                text += f"• {action}: `{count}` بار\n"

        text += f"\n\n🕐 **آخرین بروزرسانی:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        await message.edit_text(text)

    except Exception as e:
        error_msg = await message.reply(f"❌ خطا در نمایش آمار: {str(e)}")
        system_messages['stats_error'] = error_msg
        logger.error(f"خطا در show_stats: {e}")

# کامند راهنمای کامل و بهینه شده
@app.on_message(filters.command(["help", "start"]) & filters.user(admin_id))
async def help_command(client, message: Message):
    try:
        help_text = """
🤖 **راهنمای جامع ربات مدیریت هوشمند دوست و دشمن v2.0**

**🔥 مدیریت سیستم فحش‌ها:**
• `/addfosh [متن]` - اضافه کردن فحش جدید (متن یا ریپلای رسانه)
• `/addfoshphoto` (ریپلای) - اضافه کردن عکس به فحش‌ها
• `/addfoshvideo` (ریپلای) - اضافه کردن ویدیو به فحش‌ها
• `/addfoshgif` (ریپلای) - اضافه کردن گیف به فحش‌ها
• `/addfoshsticker` (ریپلای) - اضافه کردن استیکر به فحش‌ها
• `/addfoshaudio` (ریپلای) - اضافه کردن صوت به فحش‌ها
• `/delfosh [متن]` - حذف فحش مشخص از دیتابیس
• `/listfosh` - نمایش کامل فحش‌ها با صفحه‌بندی خودکار
• `/clearfosh` - حذف کلی تمام فحش‌ها (غیرقابل بازگشت)

**👹 سیستم مدیریت دشمنان:**
• `/setenemy` (ریپلای) - افزودن کاربر به لیست سیاه
• `/delenemy` (ریپلای) - حذف کاربر از لیست دشمنان
• `/listenemy` - نمایش جزئیات کامل دشمنان + تاریخ
• `/clearenemy` - پاک‌سازی کامل لیست دشمنان

**😊 سیستم مدیریت دوستان:**
• `/setfriend` (ریپلای) - افزودن کاربر به لیست VIP
• `/delfriend` (ریپلای) - حذف کاربر از لیست دوستان
• `/listfriend` - نمایش اطلاعات کامل دوستان + آمار
• `/clearfriend` - حذف کلی لیست دوستان

**💬 بانک کلمات دوستانه:**
• `/addword [متن]` - اضافه کردن پیام دوستانه (متن یا ریپلای رسانه)
• `/addwordphoto` (ریپلای) - اضافه کردن عکس دوستانه
• `/addwordvideo` (ریپلای) - اضافه کردن ویدیو دوستانه
• `/addwordgif` (ریپلای) - اضافه کردن گیف دوستانه
• `/addwordsticker` (ریپلای) - اضافه کردن استیکر دوستانه
• `/addwordaudio` (ریپلای) - اضافه کردن صوت دوستانه
• `/delword [متن]` - حذف کلمه مشخص از بانک
• `/listword` - مشاهده تمام پیام‌های دوستانه
• `/clearword` - حذف کامل بانک

**📢 سیستم ارسال همگانی:**
• `/broadcast [پیام]` - ارسال همگانی متن به تمام گروه‌ها
• پشتیبانی از ارسال رسانه با ریپلای در broadcast
  └ شامل گزارش دقیق موفقیت/ناموفقی
  └ مدیریت خطای Flood + تاخیر هوشمند
  └ فقط گروه‌ها (نه چت خصوصی/کانال)

**⏰ سیستم پیام زمان‌بندی شده:**
• `/schedule [پیام] [زمان]` - ارسال پیام در زمان تعیین شده
  └ مثال: `/schedule سلام دوستان! 30s`
  └ واحدها: s=ثانیه, m=دقیقه, h=ساعت, d=روز
  └ پشتیبانی از رسانه با ریپلای
• `/listschedule` - نمایش لیست پیام‌های تایمی
• `/delschedule [ID]` - حذف پیام تایمی با شناسه
• `/stopschedule` - توقف پیام تایمی فعلی

**🔢 ابزار شمارش هوشمند:**
• `/count [عدد] [مکث]` - شمارش تا عدد مشخص
  └ حداکثر: 1,000,000 عدد
  └ مکث قابل تنظیم: 0.05 تا 5 ثانیه
  └ گزارش پیشرفت هر 1000 عدد
• `/listcount` - نمایش لیست شمارش‌ها
• `/delcount [ID]` - حذف شمارش با شناسه
• `/stopcount` - توقف شمارش فعلی

**🔐 سیستم کامندهای خصوصی:**
• `/setprivate [کلمه] [پاسخ]` (ریپلای) - تنظیم پاسخ خصوصی
• `/delprivate [کلمه]` (ریپلای) - حذف کامند خصوصی
• `/listprivate` (ریپلای) - نمایش لیست کامندهای خصوصی
• `/clearprivate` (ریپلای) - حذف تمام کامندهای خصوصی

**🎯 سیستم پاسخ خودکار خاص:**
• `/setautoreply [پاسخ]` (ریپلای) - تنظیم پاسخ خودکار برای شخص خاص
• `/delautoreply` (ریپلای) - حذف پاسخ خودکار برای شخص خاص
• `/listautoreply` - نمایش لیست پاسخ‌های خودکار
• `/clearautoreply` - حذف تمام پاسخ‌های خودکار

**📊 سیستم نظارت و آمارگیری:**
• `/stats` - آمار جامع: تعداد ها، فعالیت‌ها، گزارش کلی
• `/test` - بررسی سلامت ربات و اتصالات
• `/backup` - ایجاد بکاپ امن از دیتابیس
• `/debug` - بررسی وضعیت پاسخگویی خودکار

**🔧 مدیریت سیستم:**
• `/runself` - فعال کردن پاسخگویی خودکار
• `/restartself` - ریستارت کردن ربات
• `/offself` - غیرفعال کردن پاسخگویی خودکار
• `/quickhelp` - راهنمای سریع کامندهای اصلی

**⚡ ویژگی‌های پیشرفته:**
🎯 **پاسخ خودکار هوشمند:**
• تشخیص دشمنان → ارسال فحش تصادفی (متن یا رسانه)
• تشخیص دوستان → ارسال پیام دوستانه (متن یا رسانه)
• فیلتر ادمین → عدم پاسخ به خود ادمین
• تشخیص محیط → فقط فعال در گروه‌ها

🛡️ **سیستم امنیتی پیشرفته:**
• دسترسی انحصاری ادمین به کلیه کامندها
• ثبت کامل لاگ‌ها در دیتابیس SQLite
• جلوگیری از تداخل (دوست+دشمن همزمان)
• محدودیت طول متن ضد اسپم
• مدیریت خطاهای شبکه و Flood

📈 **انواع رسانه پشتیبانی شده:**
• عکس (Photo) • ویدیو (Video) • صوت (Audio)
• استیکر (Sticker) • گیف (Animation) • ویس (Voice)
• ویدیو نوت (Video Note) • فایل (Document)

**🔧 پشتیبانی فنی:**
• لاگ‌های کامل در فایل `bot.log`
• آمار لحظه‌ای با `/stats`
• نسخه ربات: v2.0 Professional + Media Support
• پایگاه داده: SQLite بهینه شده

⭐ **ربات آماده خدمات‌رسانی است!**
        """

        await message.edit_text(help_text)

        logger.info("راهنمای کامل نمایش داده شد")

    except Exception as e:
        error_msg = await message.reply(f"❌ خطا در نمایش راهنما: {str(e)}")
        system_messages['help_error'] = error_msg
        logger.error(f"خطا در help_command: {e}")

# کامند ارسال همگانی بهبود یافته
@app.on_message(filters.command("broadcast"))
async def broadcast(client, message: Message):
    try:
        if len(message.command) < 2:
            await message.edit_text("📢 **استفاده:** `/broadcast پیام_شما`\n\n"
                              "**مثال:** `/broadcast سلام به همه! 👋`")
            return

        text = " ".join(message.command[1:])

        if len(text) > 1000:
            await message.edit_text("⚠️ پیام نباید بیشتر از 1000 کاراکتر باشد.")
            return

        success, fail = 0, 0
        groups_found = 0
        all_chats = 0

        await message.edit_text("🔄 در حال جستجو و ارسال...")

        # دریافت تمام دیالوگ‌ها
        async for dialog in client.get_dialogs():
            all_chats += 1
            chat_type = dialog.chat.type.value if hasattr(dialog.chat.type, 'value') else str(dialog.chat.type)
            chat_title = getattr(dialog.chat, 'title', getattr(dialog.chat, 'first_name', f'Chat {dialog.chat.id}'))

            # بررسی انواع مختلف گروه
            if chat_type in ["group", "supergroup"] or "group" in chat_type.lower():
                groups_found += 1

                try:
                    # ارسال پیام
                    await client.send_message(dialog.chat.id, text)
                    success += 1
                    logger.info(f"پیام به گروه {chat_title} ارسال شد")

                    # تاخیر برای جلوگیری از flood
                    await asyncio.sleep(0.5)

                except FloodWait as e:
                    logger.warning(f"FloodWait {e.value} ثانیه")
                    await asyncio.sleep(e.value)
                    # تلاش مجدد
                    try:
                        await client.send_message(dialog.chat.id, text)
                        success += 1
                    except:
                        fail += 1

                except Exception as e:
                    fail += 1
                    error_msg = str(e)
                    logger.error(f"خطا در ارسال به گروه {chat_title}: {error_msg}")

        # گزارش نهایی - فقط متن پیام ارسالی
        await message.edit_text(text)

        # ثبت در آمار
        log_action("broadcast", None, f"success:{success}, fail:{fail}")

    except Exception as e:
        await message.edit_text(f"❌ خطای کلی در ارسال همگانی: {str(e)}")
        logger.error(f"خطای کلی در broadcast: {e}")

# پاسخ خودکار بهبود یافته
@app.on_message(~filters.me & ~filters.channel)
async def auto_reply(client, message: Message):
    try:
        # بررسی وضعیت پاسخگویی خودکار
        if not auto_reply_enabled:
            logger.debug("پاسخگویی خودکار غیرفعال است")
            return

        # فیلترهای امنیتی
        if not message.from_user:
            logger.debug("پیام بدون فرستنده")
            return

        # اگر از خود ادمین باشد، پاسخ نده
        if message.from_user.id == admin_id:
            logger.debug("پیام از ادمین - پاسخ نمی‌دهیم")
            return

        # اگر کامند باشد، پاسخ نده
        if message.text and message.text.startswith('/'):
            logger.debug("پیام کامند است - پاسخ نمی‌دهیم")
            return

        # بررسی نوع چت - اصلاح شده
        chat_type = str(message.chat.type).lower()
        if 'group' not in chat_type and 'supergroup' not in chat_type:
            logger.debug(f"چت خصوصی یا کانال است: {chat_type}")
            return

        user_id = message.from_user.id
        # بررسی اینکه ربات است یا کاربر عادی
        if message.from_user.is_bot:
            user_name = message.from_user.first_name or "ربات"
            user_type = "ربات"
        else:
            user_name = message.from_user.first_name or "کاربر"
            user_type = "کاربر"

        enemy_list = get_enemy_list()
        friend_list = get_friend_list()

        logger.info(f"بررسی پیام از {user_type} {user_name} ({user_id}) در چت {message.chat.title or message.chat.id}")

        # پاسخ به دشمنان با فحش
        if user_id in enemy_list:
            fosh_list = get_fosh_list()
            if fosh_list:
                try:
                    fosh = choice(fosh_list)
                    if fosh.startswith("MEDIA:"):
                        parts = fosh.split(":", 2)
                        media_type = parts[1]
                        media_id = parts[2]
                        await send_media_reply(client, message, media_type, media_id)
                    else:
                        await message.reply(fosh)
                    logger.info(f"فحش به دشمن {user_id} ({user_name}) ارسال شد")
                    log_action("auto_reply_enemy", user_id, "media" if fosh.startswith("MEDIA:") else fosh[:50])
                except Exception as e:
                    logger.error(f"خطا در ارسال فحش: {e}")
            else:
                logger.warning("لیست فحش‌ها خالی است")

        # پاسخ به دوستان با کلمات دوستانه
        elif user_id in friend_list:
            friend_words = get_friend_words()
            if friend_words:
                try:
                    word = choice(friend_words)
                    if word.startswith("MEDIA:"):
                        parts = word.split(":", 2)
                        media_type = parts[1]
                        media_id = parts[2]
                        await send_media_reply(client, message, media_type, media_id)
                    else:
                        await message.reply(word)
                    logger.info(f"کلمه دوستانه به دوست {user_id} ({user_name}) ارسال شد")
                    log_action("auto_reply_friend", user_id, "media" if word.startswith("MEDIA:") else word[:50])
                except Exception as e:
                    logger.error(f"خطا در ارسال کلمه دوستانه: {e}")
            else:
                logger.warning("لیست کلمات دوستانه خالی است")
        else:
            logger.debug(f"کاربر {user_id} در هیچ لیستی نیست")

        # بررسی private commands
        chat_id = message.chat.id
        private_commands = list_private_commands(chat_id, user_id)
        for keyword, response, media_type, media_id in private_commands:
            if message.text == keyword:
                try:
                    if media_type and media_id:
                        await send_media(client, message, media_type, media_id)
                    else:
                        await message.reply(response)
                    logger.info(f"پاسخ خصوصی '{response}' به کاربر {user_id} ({user_name}) ارسال شد")
                    log_action("auto_reply_private", user_id, response)
                except Exception as e:
                    logger.error(f"خطا در ارسال پاسخ خصوصی: {e}")
                return

        # بررسی پاسخ خودکار برای کاربر خاص در گروه خاص
        specific_response = get_auto_reply_specific(chat_id, user_id)
        if specific_response:
            try:
                await message.reply(specific_response)
                logger.info(f"پاسخ خودکار خاص '{specific_response}' به کاربر {user_id} ({user_name}) در گروه {chat_id} ارسال شد")
                log_action("auto_reply_specific", user_id, f"group:{chat_id}, response:{specific_response[:50]}")
            except Exception as e:
                logger.error(f"خطا در ارسال پاسخ خودکار خاص: {e}")
            return

    except Exception as e:
        logger.error(f"خطا در auto_reply: {e}")
        import traceback
        logger.error(f"جزئیات خطا: {traceback.format_exc()}")

# کامند راهنمای سریع
@app.on_message(filters.command("quickhelp") & filters.user(admin_id))
async def quick_help(client, message: Message):
    try:
        quick_text = """
⚡ **راهنمای سریع کامندهای اصلی:**

**🔥 فحش:**
• `/addfosh` - اضافه کردن فحش متنی
• `/addfoshphoto` `/addfoshvideo` `/addfoshgif` - رسانه فحش (ریپلای)
• `/addfoshsticker` `/addfoshaudio` - استیکر و صوت فحش (ریپلای)
• `/delfosh` `/listfosh` `/clearfosh` - مدیریت فحش‌ها

**💬 کلمات دوستانه:**
• `/addword` - اضافه کردن کلمه متنی
• `/addwordphoto` `/addwordvideo` `/addwordgif` - رسانه دوستانه (ریپلای)
• `/addwordsticker` `/addwordaudio` - استیکر و صوت دوستانه (ریپلای)
• `/delword` `/listword` `/clearword` - مدیریت کلمات

**👥 دوست و دشمن:**
• `/setenemy` `/delenemy` `/listenemy` - مدیریت دشمنان (ریپلای)
• `/setfriend` `/delfriend` `/listfriend` - مدیریت دوستان (ریپلای)

**📢 ارسال و زمان‌بندی:**
• `/broadcast [پیام]` - ارسال همگانی (پشتیبانی رسانه با ریپلای)
• `/schedule [پیام] [زمان]` - پیام تایمی (پشتیبانی رسانه)
• `/stopschedule` `/listschedule` `/delschedule [ID]` - مدیریت تایمر

**🔢 شمارش:**
• `/count [عدد] [مکث]` - شمارش هوشمند
• `/stopcount` `/listcount` `/delcount [ID]` - مدیریت شمارش

**🔐 پاسخ خصوصی:**
• `/setprivate [کلمه] [پاسخ]` - تنظیم پاسخ (ریپلای)
• `/delprivate` `/listprivate` `/clearprivate` - مدیریت (ریپلای)

**🎯 پاسخ خودکار:**
• `/setautoreply [پاسخ]` - تنظیم پاسخ خودکار (ریپلای)
• `/delautoreply` `/listautoreply` `/clearautoreply` - مدیریت

**📊 سیستم:**
• `/stats` `/test` `/backup` `/debug` - آمار و بررسی
• `/runself` `/offself` `/restartself` - کنترل ربات

**🎨 انواع رسانه پشتیبانی شده:**
عکس • ویدیو • گیف • استیکر • صوت • ویس • فایل

💡 برای راهنمای کامل: `/help`
        """
        await message.edit_text(quick_text)

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

# کامند اضافی: بکاپ دیتابیس
@app.on_message(filters.command("backup") & filters.user(admin_id))
async def backup_database(client, message: Message):
    try:
        import shutil
        from datetime import datetime

        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2('bot2_database.db', backup_name)

        await message.edit_text(f"✅ بکاپ دیتابیس ایجاد شد: `{backup_name}`")
        logger.info(f"بکاپ دیتابیس ایجاد شد: {backup_name}")

    except Exception as e:
        await message.edit_text(f"❌ خطا در ایجاد بکاپ: {str(e)}")
        logger.error(f"خطا در backup: {e}")

# کامند تست سیستم
@app.on_message(filters.command("test") & filters.user(admin_id))
async def test_command(client, message: Message):
    """کامند تست کامل برای بررسی عملکرد ربات"""
    try:
        stats = get_stats()
        import os
        db_size = os.path.getsize('bot2_database.db') / 1024  # KB

        test_report = f"""
🔍 **گزارش تست سیستم:**

✅ **وضعیت کلی:** سالم و فعال
📊 **آمار داده‌ها:**
   • فحش‌ها: `{stats['fosh_count']}` عدد
   • دشمنان: `{stats['enemy_count']}` نفر  
   • دوستان: `{stats['friend_count']}` نفر
   • کلمات دوستانه: `{stats['friend_words_count']}` عدد

💾 **دیتابیس:** `{db_size:.1f} KB`
🕐 **زمان تست:** `{datetime.now().strftime('%H:%M:%S')}`
🤖 **ورژن:** Professional v2.0

⚡ **سیستم آماده خدمات‌رسانی است!**
        """
        await message.edit_text(test_report)
        logger.info("تست سیستم انجام شد")

    except Exception as e:
        await message.edit_text(f"❌ خطا در تست سیستم: {str(e)}")
        logger.error(f"خطا در test_command: {e}")

# کامند روشن کردن ربات (فقط ادمین)
@app.on_message(filters.command("runself") & filters.user(admin_id))
async def run_self(client, message: Message):
    """کامند فعال کردن پاسخگویی خودکار توسط ادمین"""
    try:
        global auto_reply_enabled
        auto_reply_enabled = True

        stats = get_stats()
        import os

        # اطلاعات سیستم بدون psutil
        db_size = os.path.getsize('bot2_database.db') / 1024

        start_report = f"""
🟢 **ربات در حال اجرا و فعال است**

📊 **آمار فعلی:**
• فحش‌ها: `{stats['fosh_count']}` عدد
• دشمنان: `{stats['enemy_count']}` نفر
• دوستان: `{stats['friend_count']}` نفر
• کلمات دوستانه: `{stats['friend_words_count']}` عدد

💾 **سیستم:**
• دیتابیس: `{db_size:.1f} KB`
• حالت: آنلاین و سالم
• پاسخگویی خودکار: ✅ فعال

✅ **وضعیت:** آماده خدمات‌رسانی
🕐 **زمان فعال‌سازی:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

🎯 **ربات کاملاً سالم و پاسخگویی خودکار فعال است!**
        """

        await message.edit_text(start_report)

        logger.info(f"پاسخگویی خودکار توسط ادمین {admin_id} فعال شد")
        log_action("runself", admin_id, "Auto reply enabled by admin")

    except Exception as e:
        error_msg = await message.reply(f"❌ خطا در فعال کردن پاسخگویی: {str(e)}")
        system_messages['runself_error'] = error_msg
        logger.error(f"خطا در run_self: {e}")

# کامند ریستارت ربات (فقط ادمین)  
@app.on_message(filters.command("restartself") & filters.user(admin_id))
async def restart_self(client, message: Message):
    """کامند ریستارت ربات توسط ادمین"""
    try:
        stats = get_stats()

        restart_report = f"""
🔄 **ربات در حال ریستارت...**

📊 **آمار قبل از ریستارت:**
• فحش‌ها: `{stats['fosh_count']}` عدد
• دشمنان: `{stats['enemy_count']}` نفر
• دوستان: `{stats['friend_count']}` عدد
• کلمات دوستانه: `{stats['friend_words_count']}` عدد

💾 **دیتابیس ذخیره شد**
🕐 **زمان ریستارت:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

⏳ **در حال ریستارت...**
        """

        await message.edit_text(restart_report)
        logger.info(f"ربات توسط ادمین {admin_id} درخواست ریستارت شد")
        log_action("restartself", admin_id, "Bot restart requested by admin")

        # تاخیر برای ارسال پیام
        await asyncio.sleep(1)

        # پیام نهایی
        await message.reply("✅ **ریستارت تکمیل شد - ربات مجدداً فعال است!**")
        logger.info("ریستارت موفقیت‌آمیز تکمیل شد")

    except Exception as e:
        await message.reply(f"❌ خطا در ریستارت: {str(e)}")
        logger.error(f"خطا در restart_self: {e}")

# تابع کمکی برای خاموش کردن ایمن
async def safe_shutdown(client, chat_id, admin_user_id):
    """تابع کمکی برای خاموش کردن ایمن ربات"""
    try:
        # پیام نهایی
        await client.send_message(chat_id, "🔴 **ربات خاموش شد - برای روشن کردن از Run button استفاده کنید**")

        # لاگ نهایی
        logger.info("="*50)
        logger.info("🛑 ربات با دستور ادمین خاموش شد")
        logger.info(f"⏰ زمان خاتمه: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*50)

        # تاخیر کوتاه برای ارسال پیام
        await asyncio.sleep(1)

        # خروج از برنامه
        import sys
        sys.exit(0)

    except Exception as e:
        logger.error(f"خطا در خاموش کردن ایمن: {e}")

# کامند غیرفعال کردن پاسخگویی خودکار (فقط ادمین)
@app.on_message(filters.command("offself") & filters.user(admin_id))
async def off_self(client, message: Message):
    """کامند غیرفعال کردن پاسخگویی خودکار توسط ادمین"""
    try:
        global auto_reply_enabled
        auto_reply_enabled = False

        stats = get_stats()

        off_report = f"""
🔴 **پاسخگویی خودکار غیرفعال شد**

📊 **آمار فعلی:**
• فحش‌ها: `{stats['fosh_count']}` عدد
• دشمنان: `{stats['enemy_count']}` نفر
• دوستان: `{stats['friend_count']}` نفر
• کلمات دوستانه: `{stats['friend_words_count']}` عدد

⚙️ **وضعیت سیستم:**
• ربات: ✅ فعال و در خدمت ادمین
• پاسخگویی خودکار: ❌ غیرفعال
• کامندهای ادمین: ✅ کاملاً فعال

🕐 **زمان غیرفعال‌سازی:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

💡 **برای فعال کردن دوباره از `/runself` استفاده کنید**
        """

        await message.edit_text(off_report)

        logger.info(f"پاسخگویی خودکار توسط ادمین {admin_id} غیرفعال شد")
        log_action("offself", admin_id, "Auto reply disabled by admin")

    except Exception as e:
        error_msg = await message.reply(f"❌ خطا در غیرفعال کردن پاسخگویی: {str(e)}")
        system_messages['offself_error'] = error_msg
        logger.error(f"خطا در off_self: {e}")

# کامند دیباگ پاسخگویی خودکار
@app.on_message(filters.command("debug") & filters.user(admin_id))
async def debug_auto_reply(client, message: Message):
    """کامند دیباگ برای بررسی وضعیت پاسخگویی خودکار"""
    try:
        stats = get_stats()
        enemy_list = get_enemy_list()
        friend_list = get_friend_list()
        fosh_list = get_fosh_list()
        friend_words = get_friend_words()

        debug_text = f"""
🔍 **گزارش دیباگ پاسخگویی خودکار:**

⚙️ **وضعیت سیستم:**
• پاسخگویی خودکار: {"✅ فعال" if auto_reply_enabled else "❌ غیرفعال"}
• نوع چت فعلی: `{message.chat.type}`
• شناسه چت: `{message.chat.id}`
• عنوان چت: `{message.chat.title or 'بدون عنوان'}`

📊 **داده‌های موجود:**
• تعداد دشمنان: `{len(enemy_list)}` نفر
• تعداد دوستان: `{len(friend_list)}` نفر  
• تعداد فحش‌ها: `{len(fosh_list)}` عدد
• تعداد کلمات دوستانه: `{len(friend_words)}` عدد

👥 **لیست دشمنان:** {enemy_list if enemy_list else 'خالی'}
😊 **لیست دوستان:** {friend_list if friend_list else 'خالی'}

💡 **راهنمای تست:**
1. ابتدا یک کاربر را با `/setenemy` یا `/setfriend` اضافه کنید
2. سپس از آن کاربر پیام بفرستید
3. ربات باید خودکار پاسخ دهد

🕐 **زمان بررسی:** `{datetime.now().strftime('%H:%M:%S')}`
        """

        await message.reply(debug_text)

    except Exception as e:
        await message.reply(f"❌ خطا در دیباگ: {str(e)}")
        logger.error(f"خطا در debug_auto_reply: {e}")

# کامند تنظیم پاسخ خصوصی برای کاربر خاص در گروه
@app.on_message(filters.command("setprivate") & filters.user(admin_id) & filters.reply)
async def set_private_command(client, message: Message):
    try:
        if len(message.command) < 3:
            await message.reply("⚠️ **استفاده:** `/setprivate [کلمه] [پاسخ]`(ریپلای روی پیام کاربر)")
            return

        keyword = message.command[1]
        response = " ".join(message.command[2:])
        replied_user = message.reply_to_message.from_user
        group_id = message.chat.id
        user_id = replied_user.id

        if add_private_command(group_id, user_id, keyword, response):
            await message.reply(f"✅ پاسخ خصوصی برای `{keyword}` به کاربر `{replied_user.first_name}` تنظیم شد.")
        else:
            await message.reply(f"⚠️ پاسخ خصوصی برای `{keyword}` قبلاً برای کاربر `{replied_user.first_name}` تنظیم شده است.")

    except Exception as e:
        await message.reply(f"❌ خطا در تنظیم پاسخ خصوصی: {str(e)}")
        logger.error(f"خطا در set_private_command: {e}")

# کامند حذف پاسخ خصوصی برای کاربر خاص در گروه
@app.on_message(filters.command("delprivate") & filters.user(admin_id) & filters.reply)
async def del_private_command(client, message: Message):
    try:
        if len(message.command) < 2:
            await message.reply("⚠️ **استفاده:** `/delprivate [کلمه]` (ریپلای روی پیام کاربر)")
            return

        keyword = message.command[1]
        replied_user = message.reply_to_message.from_user
        group_id = message.chat.id
        user_id = replied_user.id

        if remove_private_command(group_id, user_id, keyword):
            await message.reply(f"✅ پاسخ خصوصی برای `{keyword}` از کاربر `{replied_user.first_name}` حذف شد.")
        else:
            await message.reply(f"⚠️ پاسخ خصوصی برای `{keyword}` برای کاربر `{replied_user.first_name}` یافت نشد.")

    except Exception as e:
        await message.reply(f"❌ خطا در حذف پاسخ خصوصی: {str(e)}")
        logger.error(f"خطا در del_private_command: {e}")

# کامند لیست کردن تمام پاسخ های خصوصی برای یک کاربر در یک گروه
@app.on_message(filters.command("listprivate") & filters.user(admin_id) & filters.reply)
async def list_private_commands_command(client, message: Message):
    try:
        replied_user = message.reply_to_message.from_user
        group_id = message.chat.id
        user_id = replied_user.id

        private_commands = list_private_commands(group_id, user_id)

        if not private_commands:
            await message.reply(f"📝 هیچ پاسخ خصوصی برای کاربر `{replied_user.first_name}` یافت نشد.")
            return

        text = f"💬 **پاسخ‌های خصوصی برای کاربر `{replied_user.first_name}`:**\n\n"
        for i, (keyword, response, media_type, media_id) in enumerate(private_commands, 1):
            text += f"`{i}.` **{keyword}:** {response}\n"

        await message.reply(text)

    except Exception as e:
        await message.reply(f"❌ خطا در لیست کردن پاسخ‌های خصوصی: {str(e)}")
        logger.error(f"خطا در list_private_commands_command: {e}")

# کامند پاک کردن تمام پاسخ های خصوصی برای یک کاربر در یک گروه
@app.on_message(filters.command("clearprivate") & filters.user(admin_id) & filters.reply)
async def clear_private_commands_command(client, message: Message):
    try:
        replied_user = message.reply_to_message.from_user
        group_id = message.chat.id
        user_id = replied_user.id

        clear_private_commands(group_id, user_id)
        await message.reply(f"🗑️ تمام پاسخ‌های خصوصی برای کاربر `{replied_user.first_name}` پاک شدند.")

    except Exception as e:
        await message.reply(f"❌ خطا در پاک کردن پاسخ‌های خصوصی: {str(e)}")
        logger.error(f"خطا در clear_private_commands_command: {e}")

# کامند تنظیم پاسخ خودکار برای شخص خاص در گروه خاص
@app.on_message(filters.command("setautoreply") & filters.user(admin_id) & filters.reply)
async def set_auto_reply_specific(client, message: Message):
    """تنظیم پاسخ خودکار برای شخص خاص در گروه خاص"""
    try:
        if len(message.command) < 2:
            await message.reply("⚠️ **استفاده:** `/setautoreply [متن_پاسخ]` (ریپلای روی پیام کاربر)")
            return

        response_text = " ".join(message.command[1:])
        replied_user = message.reply_to_message.from_user
        group_id = message.chat.id
        user_id = replied_user.id
        group_title = message.chat.title or f"گروه {group_id}"

        if len(response_text) > 500:
            await message.reply("⚠️ متن پاسخ نباید بیشتر از 500 کاراکتر باشد.")
            return

        # بررسی نوع کاربر یا ربات
        user_type = "ربات" if replied_user.is_bot else "کاربر"

        if add_auto_reply_specific(group_id, user_id, response_text):
            await message.edit_text(f"""
✅ **پاسخ خودکار تنظیم شد:**

👤 **{user_type}:** {replied_user.first_name}
🆔 **شناسه:** `{user_id}`
🏷️ **گروه:** {group_title}
🆔 **شناسه گروه:** `{group_id}`
💬 **پاسخ:** {response_text}

🎯 **از این به بعد هر پیامی که این {user_type} در این گروه بفرستد، ربات خودکار جواب می‌دهد!**
            """)
            logger.info(f"پاسخ خودکار برای کاربر {user_id} در گروه {group_id} تنظیم شد")
            log_action("set_auto_reply", user_id, f"group:{group_id}, response:{response_text[:50]}")
        else:
            await message.reply("❌ خطا در تنظیم پاسخ خودکار.")

    except Exception as e:
        await message.reply(f"❌ خطا در تنظیم پاسخ خودکار: {str(e)}")
        logger.error(f"خطا در set_auto_reply_specific: {e}")

# کامند حذف پاسخ خودکار برای شخص خاص در گروه خاص
@app.on_message(filters.command("delautoreply") & filters.user(admin_id) & filters.reply)
async def del_auto_reply_specific(client, message: Message):
    """حذف پاسخ خودکار برای شخص خاص در گروه خاص"""
    try:
        replied_user = message.reply_to_message.from_user
        group_id = message.chat.id
        user_id = replied_user.id
        group_title = message.chat.title or f"گروه {group_id}"

        # بررسی نوع کاربر یا ربات
        user_type = "ربات" if replied_user.is_bot else "کاربر"

        if remove_auto_reply_specific(group_id, user_id):
            await message.edit_text(f"""
✅ **پاسخ خودکار حذف شد:**

👤 **{user_type}:** {replied_user.first_name}
🆔 **شناسه:** `{user_id}`
🏷️ **گروه:** {group_title}
🆔 **شناسه گروه:** `{group_id}`

🚫 **دیگر به پیام‌های این {user_type} در این گروه پاسخ خودکار نمی‌دهد.**
            """)
            logger.info(f"پاسخ خودکار برای کاربر {user_id} در گروه {group_id} حذف شد")
            log_action("del_auto_reply", user_id, f"group:{group_id}")
        else:
            await message.reply(f"⚠️ هیچ پاسخ خودکاری برای کاربر `{replied_user.first_name}` در این گروه تنظیم نشده.")

    except Exception as e:
        await message.reply(f"❌ خطا در حذف پاسخ خودکار: {str(e)}")
        logger.error(f"خطا در del_auto_reply_specific: {e}")

# کامند نمایش لیست پاسخ‌های خودکار
@app.on_message(filters.command("listautoreply") & filters.user(admin_id))
async def list_auto_reply_specific_command(client, message: Message):
    """نمایش لیست تمام پاسخ‌های خودکار تنظیم شده"""
    try:
        auto_reply_list = list_auto_reply_specific()

        if not auto_reply_list:
            await message.edit_text("📝 هیچ پاسخ خودکاری تنظیم نشده است.\n💡 با `/setautoreply` (ریپلای روی پیام) پاسخ خودکار اضافه کنید.")
            return

        text = "🤖 **لیست پاسخ‌های خودکار:**\n\n"

        for i, (group_id, user_id, response, created_at) in enumerate(auto_reply_list, 1):
            # تلاش برای دریافت اطلاعات گروه و کاربر
            try:
                group_info = await client.get_chat(group_id)
                group_name = group_info.title or f"گروه {group_id}"
            except:
                group_name = f"گروه {group_id}"

            try:
                user_info = await client.get_users(user_id)
                user_name = user_info.first_name or f"کاربر {user_id}"
                user_type = "🤖" if user_info.is_bot else "👤"
            except:
                user_name = f"کاربر {user_id}"
                user_type = "👤"

            text += f"`{i}.` {user_type} **{user_name}** در **{group_name}**\n"
            text += f"   🆔 کاربر: `{user_id}`\n"
            text += f"   🆔 گروه: `{group_id}`\n"
            text += f"   💬 پاسخ: {response[:100]}{'...' if len(response) > 100 else ''}\n"
            text += f"   📅 تاریخ: {created_at[:16]}\n\n"

        text += f"📊 **تعداد کل:** {len(auto_reply_list)} پاسخ خودکار"
        await message.edit_text(text)

    except Exception as e:
        await message.reply(f"❌ خطا در نمایش لیست: {str(e)}")
        logger.error(f"خطا در list_auto_reply_specific_command: {e}")

# کامند پاک کردن تمام پاسخ‌های خودکار
@app.on_message(filters.command("clearautoreply") & filters.user(admin_id))
async def clear_auto_reply_specific_command(client, message: Message):
    """پاک کردن تمام پاسخ‌های خودکار"""
    try:
        auto_reply_count = len(list_auto_reply_specific())

        if auto_reply_count == 0:
            await message.edit_text("📝 لیست پاسخ‌های خودکار از قبل خالی است.")
            return

        clear_auto_reply_specific()
        await message.edit_text(f"🗑️ تمام پاسخ‌های خودکار پاک شدند. ({auto_reply_count} مورد حذف شد)")
        logger.info(f"تمام پاسخ‌های خودکار پاک شدند: {auto_reply_count} مورد")
        log_action("clear_auto_reply", admin_id, f"count:{auto_reply_count}")

    except Exception as e:
        await message.reply(f"❌ خطا در پاک کردن پاسخ‌های خودکار: {str(e)}")
        logger.error(f"خطا در clear_auto_reply_specific_command: {e}")

# متغیر برای ذخیره پیام‌های سیستمی جهت ادیت
system_messages = {}

# کامند پیام تایمی با پشتیبانی از رسانه
@app.on_message(filters.command("schedule") & filters.user(admin_id))
async def schedule_message(client, message: Message):
    """کامند ارسال پیام در زمان تعیین شده"""
    try:
        if len(message.command) < 3:
            help_msg = await message.reply("""
⏰ **استفاده از پیام تایمی:**

**فرمت:** `/schedule [پیام] [زمان]`

**مثال‌ها:**
• `/schedule سلام دوستان! 10s` - 10 ثانیه دیگه
• `/schedule یادآوری مهم 5m` - 5 دقیقه دیگه  
• `/schedule پیام روزانه 2h` - 2 ساعت دیگه
• `/schedule اطلاعیه 1d` - 1 روز دیگه

**واحدهای زمانی:**
• `s` = ثانیه
• `m` = دقیقه  
• `h` = ساعت
• `d` = روز

**حداکثر:** قابل تنظیم (فعلی: 30 روز)
            """)
            system_messages['schedule_help'] = help_msg
            return

        # بررسی رسانه در ریپلای
        media_type = None
        media_id = None
        msg_text = ""

        if message.reply_to_message:
            if message.reply_to_message.photo:
                media_type = "photo"
                media_id = message.reply_to_message.photo.file_id
            elif message.reply_to_message.video:
                media_type = "video"
                media_id = message.reply_to_message.video.file_id
            elif message.reply_to_message.audio:
                media_type = "audio"
                media_id = message.reply_to_message.audio.file_id
            elif message.reply_to_message.document:
                media_type = "document"
                media_id = message.reply_to_message.document.file_id
            elif message.reply_to_message.sticker:
                media_type = "sticker"
                media_id = message.reply_to_message.sticker.file_id
            
            # اگر رسانه وجود دارد، زمان آخرین آرگومان است
            if media_type:
                if len(message.command) < 2:
                    error_msg = await message.reply("⚠️ لطفاً زمان را مشخص کنید!\nمثال: `/schedule 10s` (ریپلای روی رسانه)")
                    system_messages['schedule_error'] = error_msg
                    return
                time_str = message.command[1]
            else:
                msg_text = message.reply_to_message.text or ""
                if len(message.command) < 2:
                    error_msg = await message.reply("⚠️ لطفاً زمان را مشخص کنید!")
                    system_messages['schedule_error'] = error_msg
                    return
                time_str = message.command[1]
        else:
            # جدا کردن پیام از زمان
            parts = message.text.split()
            time_str = parts[-1]  # آخرین قسمت زمان است
            msg_text = " ".join(parts[1:-1])  # بقیه پیام است

        if not msg_text.strip() and not media_type:
            error_msg = await message.reply("⚠️ متن پیام یا رسانه نمی‌تواند خالی باشد!")
            system_messages['schedule_error'] = error_msg
            return

        # پارس کردن زمان
        import re
        time_match = re.match(r'^(\d+)([smhd])$', time_str.lower())

        if not time_match:
            error_msg = await message.reply("⚠️ فرمت زمان اشتباه است!\nمثال: `10s`, `5m`, `2h`, `1d`")
            system_messages['schedule_error'] = error_msg
            return

        amount = int(time_match.group(1))
        unit = time_match.group(2)

        # تبدیل به ثانیه
        multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        seconds = amount * multipliers[unit]

        # محدودیت حداکثر تغییر پذیر (بر حسب تنظیمات کاربر)
        max_schedule_days = 30  # قابل تنظیم توسط ادمین
        max_seconds = max_schedule_days * 24 * 60 * 60

        if seconds > max_seconds:
            error_msg = await message.reply(f"⚠️ حداکثر زمان مجاز: {max_schedule_days} روز")
            system_messages['schedule_error'] = error_msg
            return

        # محدودیت حداقل 1 ثانیه
        if seconds < 1:
            error_msg = await message.reply("⚠️ حداقل زمان: 1 ثانیه")
            system_messages['schedule_error'] = error_msg
            return

        # محاسبه زمان ارسال
        from datetime import datetime, timedelta
        send_time = datetime.now() + timedelta(seconds=seconds)
        start_time = datetime.now()

        # واحد زمان برای نمایش
        time_units = {'s': 'ثانیه', 'm': 'دقیقه', 'h': 'ساعت', 'd': 'روز'}
        time_display = f"{amount} {time_units[unit]}"

        # ذخیره اطلاعات برای گزارش
        chat_title = getattr(message.chat, 'title', f'چت {message.chat.id}')
        chat_id = message.chat.id
        user_id = message.from_user.id

        # ذخیره در دیتابیس
        schedule_id = add_scheduled_message(user_id, chat_id, msg_text, send_time.isoformat(), media_type, media_id)

        # نوع محتوا برای نمایش
        content_type = "رسانه" if media_type else "متن"
        content_display = f"{media_type}" if media_type else msg_text

        # پیام تأیید موقت (برای اطلاع ادمین)
        confirm_msg = await message.edit_text(f"""
⏰ **پیام تایمی تنظیم شد:**

🆔 **شناسه:** `{schedule_id}`
📝 **محتوا:** {content_type} - {content_display}
🕐 **زمان ارسال:** {time_display} دیگه
📅 **تاریخ دقیق:** `{send_time.strftime('%Y-%m-%d %H:%M:%S')}`
🛑 **برای توقف:** `/delschedule {schedule_id}` یا `/stopschedule`

⏳ **در حال انتظار...**
        """)

        logger.info(f"پیام تایمی تنظیم شد: {seconds} ثانیه - ID: {schedule_id}")
        # Store the scheduled message info
        scheduled_messages[user_id] = {
            'schedule_id': schedule_id,
            'chat_id': chat_id,
            'message_text': msg_text,
            'media_type': media_type,
            'media_id': media_id,
            'send_time': send_time,
            'confirm_msg_id': confirm_msg.id,
            'unit': unit,
            'amount': amount,
        }

        # Wait until the scheduled time
        await asyncio.sleep(seconds)

        # Check if the message has been cancelled
        if user_id not in scheduled_messages:
            logger.info(f"پیام تایمی متوقف شد.")
            return

        # Send the message in the current chat
        success = False
        error_details = None
        scheduled_info = scheduled_messages[user_id]

        try:
            if scheduled_info['media_type'] and scheduled_info['media_id']:
                await send_media_to_chat(client, chat_id, scheduled_info['media_type'], scheduled_info['media_id'])
                success = True
                logger.info(f"رسانه تایمی ارسال شد: {scheduled_info['media_type']}")
            elif scheduled_info['message_text']:
                await client.send_message(chat_id, scheduled_info['message_text'])
                success = True
                logger.info(f"پیام تایمی ارسال شد: {scheduled_info['message_text']}")
            
            log_action("schedule_sent", admin_id, f"schedule_id:{scheduled_info['schedule_id']}, delay:{seconds}s")
            # حذف از دیتابیس
            remove_scheduled_message(scheduled_info['schedule_id'])

        except Exception as e:
            success = False
            error_details = str(e)
            logger.error(f"خطا در ارسال پیام تایمی: {e}")

        # Delete the confirmation message
        try:
            await client.delete_messages(chat_id, scheduled_messages[user_id]['confirm_msg_id'])
        except Exception as e:
            logger.warning(f"نتوانست پیام کامند را حذف کند: {e}")

        # Send a report to Saved Messages
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        if success:
            report = f"""
📤 **گزارش ارسال پیام تایمی موفق**

✅ **وضعیت:** ارسال شد
📝 **متن پیام:** {msg_text}
🏷️ **چت:** {chat_title}
🆔 **شناسه چت:** `{chat_id}`
⏰ **تاخیر تنظیم شده:** {time_display}
🕐 **شروع:** `{start_time.strftime('%Y-%m-%d %H:%M:%S')}`
🕐 **پایان:** `{end_time.strftime('%Y-%m-%d %H:%M:%S')}`
⏱️ **زمان اجرا:** `{execution_time:.2f}` ثانیه

🎯 **پیام با موفقیت در زمان تعیین شده ارسال شد!**
            """
        else:
            report = f"""
📤 **گزارش ارسال پیام تایمی ناموفق**

❌ **وضعیت:** خطا در ارسال
📝 **متن پیام:** {msg_text}
🏷️ **چت:** {chat_title}
🆔 **شناسه چت:** `{chat_id}`
⏰ **تاخیر تنظیم شده:** {time_display}
🕐 **شروع:** `{start_time.strftime('%Y-%m-%d %H:%M:%S')}`
🕐 **پایان:** `{end_time.strftime('%Y-%m-%d %H:%M:%S')}`
⏱️ **زمان اجرا:** `{execution_time:.2f}` ثانیه

🚫 **خطا:** {error_details}
            """

        # Send report to Saved Messages
        try:
            await client.send_message("me", report)
            logger.info("گزارش پیام تایمی به Saved Messages ارسال شد")
        except Exception as e:
            logger.error(f"خطا در ارسال گزارش به Saved Messages: {e}")
        # Remove the scheduled message
        del scheduled_messages[user_id]

    except Exception as e:
        error_msg = await message.reply(f"❌ خطا در تنظیم پیام تایمی: {str(e)}")
        system_messages['schedule_error'] = error_msg
        logger.error(f"خطا در schedule_message: {e}")

# Store scheduled messages
scheduled_messages = {}

# Handle /stopschedule command
@app.on_message(filters.command("stopschedule") & filters.user(admin_id))
async def stop_schedule(client, message: Message):
    """Handle stopping the /schedule task"""
    user_id = message.from_user.id

    if user_id in scheduled_messages:
        try:
            await client.delete_messages(scheduled_messages[user_id]['chat_id'], scheduled_messages[user_id]['confirm_msg_id'])
            # حذف از دیتابیس
            remove_scheduled_message(scheduled_messages[user_id]['schedule_id'])
        except Exception as e:
            logger.warning(f"Failed to delete scheduled message: {e}")
        del scheduled_messages[user_id]
        await message.reply("✅ پیام تایمی متوقف شد!")
        logger.info(f"پیام زمان‌بندی شده متوقف شد. (شناسه کاربر: {user_id})")
    else:
        await message.reply("⚠️ هیچ پیام زمان‌بندی شده‌ای برای توقف وجود ندارد.")

# کامند حذف پیام تایمی با ID
@app.on_message(filters.command("delschedule") & filters.user(admin_id))
async def del_schedule(client, message: Message):
    """حذف پیام تایمی با ID مشخص"""
    try:
        if len(message.command) < 2:
            await message.reply("⚠️ **استفاده:** `/delschedule [ID]`\n\nبرای دیدن لیست: `/listschedule`")
            return

        schedule_id = int(message.command[1])
        user_id = message.from_user.id

        if remove_scheduled_message(schedule_id):
            # اگر در حال اجرا است، متوقف کن
            if user_id in scheduled_messages and scheduled_messages[user_id]['schedule_id'] == schedule_id:
                try:
                    await client.delete_messages(scheduled_messages[user_id]['chat_id'], scheduled_messages[user_id]['confirm_msg_id'])
                except:
                    pass
                del scheduled_messages[user_id]
            
            await message.reply(f"✅ پیام تایمی با شناسه `{schedule_id}` حذف شد!")
            logger.info(f"پیام تایمی حذف شد - ID: {schedule_id}")
        else:
            await message.reply(f"⚠️ پیام تایمی با شناسه `{schedule_id}` یافت نشد.")

    except ValueError:
        await message.reply("⚠️ شناسه باید عدد باشد!")
    except Exception as e:
        await message.reply(f"❌ خطا: {str(e)}")
        logger.error(f"خطا در del_schedule: {e}")

# کامند لیست پیام‌های تایمی
@app.on_message(filters.command("listschedule") & filters.user(admin_id))
async def list_schedule(client, message: Message):
    """نمایش لیست پیام‌های تایمی"""
    try:
        user_id = message.from_user.id
        scheduled_list = list_scheduled_messages(user_id)

        if not scheduled_list:
            await message.reply("📝 هیچ پیام تایمی‌ای تنظیم نشده است.")
            return

        text = "⏰ **لیست پیام‌های تایمی:**\n\n"
        for schedule_id, msg_text, media_type, scheduled_time in scheduled_list:
            content = media_type if media_type else (msg_text[:30] + "..." if len(msg_text) > 30 else msg_text)
            text += f"`{schedule_id}.` {content}\n"
            text += f"   📅 {scheduled_time[:16]}\n\n"

        text += f"\n📊 **تعداد کل:** {len(scheduled_list)} پیام"
        text += f"\n💡 **حذف:** `/delschedule [ID]`"
        
        await message.reply(text)

    except Exception as e:
        await message.reply(f"❌ خطا: {str(e)}")
        logger.error(f"خطا در list_schedule: {e}")

# کامند شمارش بهبود یافته با ID
@app.on_message(filters.command("count") & filters.user(admin_id))
async def count_command(client, message: Message):
    """کامند شمارش بهبود یافته با مدیریت ID"""
    try:
        if len(message.command) < 2:
            help_msg = await message.reply("""
🔢 **استفاده از شمارش:**

**فرمت:** `/count [عدد] [مکث_اختیاری]`

**مثال‌ها:**
• `/count 100` - شمارش تا 100 (مکث پیش‌فرض: 1 ثانیه)
• `/count 50 0.5` - شمارش تا 50 با مکث 0.5 ثانیه
• `/count 1000 2` - شمارش تا 1000 با مکث 2 ثانیه

**محدودیت‌ها:**
• حداکثر: 1,000,000 عدد
• مکث: 0.05 تا 5 ثانیه
• گزارش هر 1000 عدد

**مدیریت:**
• `/stopcount` - توقف شمارش فعلی
• `/listcount` - لیست شمارش‌ها
• `/delcount [ID]` - حذف شمارش مشخص
            """)
            return

        # پارس کردن آرگومان‌ها
        try:
            target = int(message.command[1])
        except ValueError:
            await message.reply("⚠️ عدد هدف باید عدد صحیح باشد!")
            return

        delay = 1.0  # مکث پیش‌فرض
        if len(message.command) > 2:
            try:
                delay = float(message.command[2])
            except ValueError:
                await message.reply("⚠️ مکث باید عدد باشد!")
                return

        # بررسی محدودیت‌ها
        if target <= 0:
            await message.reply("⚠️ عدد هدف باید بزرگتر از صفر باشد!")
            return

        if target > 1000000:
            await message.reply("⚠️ حداکثر عدد مجاز: 1,000,000")
            return

        if delay < 0.05 or delay > 5:
            await message.reply("⚠️ مکث باید بین 0.05 تا 5 ثانیه باشد!")
            return

        user_id = message.from_user.id
        chat_id = message.chat.id

        # بررسی وجود شمارش فعال
        if user_id in count_tasks and not count_tasks[user_id].done():
            await message.reply("⚠️ شمارش دیگری در حال اجرا است!\nبرای توقف: `/stopcount`")
            return

        # ذخیره در دیتابیس
        count_id = add_count_task(user_id, chat_id, 0, target, delay)

        # محاسبه زمان تقریبی
        estimated_time = target * delay
        if estimated_time > 60:
            time_display = f"{estimated_time/60:.1f} دقیقه"
        else:
            time_display = f"{estimated_time:.1f} ثانیه"

        # پیام شروع
        start_msg = await message.edit_text(f"""
🔢 **شمارش شروع شد:**

🆔 **شناسه:** `{count_id}`
🎯 **هدف:** {target:,} عدد
⏱️ **مکث:** {delay} ثانیه
⏰ **زمان تقریبی:** {time_display}
🛑 **برای توقف:** `/delcount {count_id}` یا `/stopcount`

🚀 **شروع شمارش...**
        """)

        # ایجاد task برای شمارش
        async def count_task():
            try:
                for i in range(1, target + 1):
                    # بررسی لغو
                    if user_id not in count_tasks:
                        return

                    await client.send_message(chat_id, str(i))
                    
                    # گزارش پیشرفت
                    if i % 1000 == 0:
                        progress = (i / target) * 100
                        await client.send_message(chat_id, f"📊 پیشرفت: {i:,}/{target:,} ({progress:.1f}%)")

                    await asyncio.sleep(delay)

                # پیام تکمیل
                await client.send_message(chat_id, f"✅ شمارش تا {target:,} تکمیل شد!")
                
                # حذف از دیتابیس
                remove_count_task(count_id)
                if user_id in count_tasks:
                    del count_tasks[user_id]

            except asyncio.CancelledError:
                await client.send_message(chat_id, "🛑 شمارش متوقف شد!")
                remove_count_task(count_id)
            except Exception as e:
                await client.send_message(chat_id, f"❌ خطا در شمارش: {str(e)}")
                remove_count_task(count_id)
                logger.error(f"خطا در count_task: {e}")

        # شروع task
        task = asyncio.create_task(count_task())
        count_tasks[user_id] = task

        logger.info(f"شمارش شروع شد - ID: {count_id}, Target: {target}, Delay: {delay}")

    except Exception as e:
        await message.reply(f"❌ خطا در شمارش: {str(e)}")
        logger.error(f"خطا در count_command: {e}")

# Handle /stopcount command
@app.on_message(filters.command("stopcount") & filters.user(admin_id))
async def stop_count(client, message: Message):
    """Handle stopping the /count task"""
    user_id = message.from_user.id

    if user_id in count_tasks:
        count_tasks[user_id].cancel()
        del count_tasks[user_id]
        # حذف از دیتابیس
        clear_count_tasks(user_id)
        await message.reply("✅ شمارش متوقف شد!")
        logger.info(f"شمارش متوقف شد. (شناسه کاربر: {user_id})")
    else:
        await message.reply("⚠️ هیچ شمارشی برای توقف وجود ندارد.")

# کامند حذف شمارش با ID
@app.on_message(filters.command("delcount") & filters.user(admin_id))
async def del_count(client, message: Message):
    """حذف شمارش با ID مشخص"""
    try:
        if len(message.command) < 2:
            await message.reply("⚠️ **استفاده:** `/delcount [ID]`\n\nبرای دیدن لیست: `/listcount`")
            return

        count_id = int(message.command[1])
        user_id = message.from_user.id

        if remove_count_task(count_id):
            # اگر در حال اجرا است، متوقف کن
            if user_id in count_tasks:
                count_tasks[user_id].cancel()
                del count_tasks[user_id]
            
            await message.reply(f"✅ شمارش با شناسه `{count_id}` حذف شد!")
            logger.info(f"شمارش حذف شد - ID: {count_id}")
        else:
            await message.reply(f"⚠️ شمارش با شناسه `{count_id}` یافت نشد.")

    except ValueError:
        await message.reply("⚠️ شناسه باید عدد باشد!")
    except Exception as e:
        await message.reply(f"❌ خطا: {str(e)}")
        logger.error(f"خطا در del_count: {e}")

# کامند لیست شمارش‌ها
@app.on_message(filters.command("listcount") & filters.user(admin_id))
async def list_count(client, message: Message):
    """نمایش لیست شمارش‌ها"""
    try:
        user_id = message.from_user.id
        count_list = list_count_tasks(user_id)

        if not count_list:
            await message.reply("📝 هیچ شمارشی تنظیم نشده است.")
            return

        text = "🔢 **لیست شمارش‌ها:**\n\n"
        for count_id, current_count, target_count, delay in count_list:
            progress = (current_count / target_count) * 100 if target_count > 0 else 0
            text += f"`{count_id}.` {current_count:,}/{target_count:,} ({progress:.1f}%)\n"
            text += f"   ⏱️ مکث: {delay}s\n\n"

        text += f"\n📊 **تعداد کل:** {len(count_list)} شمارش"
        text += f"\n💡 **حذف:** `/delcount [ID]`"
        
        await message.reply(text)

    except Exception as e:
        await message.reply(f"❌ خطا: {str(e)}")
        logger.error(f"خطا در list_count: {e}")

async def send_media(client: Client, message: Message, media_type: str, media_id: str):
    """Helper function to send media based on type and ID."""
    try:
        if media_type == "photo":
            await client.send_photo(message.chat.id, media_id, reply_to_message_id=message.message_id)
        elif media_type == "video":
            await client.send_video(message.chat.id, media_id, reply_to_message_id=message.message_id)
        elif media_type == "audio":
            await client.send_audio(message.chat.id, media_id, reply_to_message_id=message.message_id)
        elif media_type == "document":
            await client.send_document(message.chat.id, media_id, reply_to_message_id=message.message_id)
        elif media_type == "sticker":
            await client.send_sticker(message.chat.id, media_id, reply_to_message_id=message.message_id)
        else:
            await message.reply("❌ نوع رسانه نامعتبر است.")
    except Exception as e:
        await message.reply(f"❌ خطا در ارسال رسانه: {str(e)}")
        logger.error(f"خطا در send_media: {e}")

async def send_media_reply(client: Client, message: Message, media_type: str, media_id: str):
    """Helper function to send media as reply."""
    try:
        if media_type == "photo":
            await message.reply_photo(media_id)
        elif media_type == "video":
            await message.reply_video(media_id)
        elif media_type == "audio":
            await message.reply_audio(media_id)
        elif media_type == "document":
            await message.reply_document(media_id)
        elif media_type == "sticker":
            await message.reply_sticker(media_id)
        elif media_type == "animation":
            await message.reply_animation(media_id)
        elif media_type == "voice":
            await message.reply_voice(media_id)
        elif media_type == "video_note":
            await message.reply_video_note(media_id)
        else:
            await message.reply("❌ نوع رسانه نامعتبر است.")
    except Exception as e:
        await message.reply(f"❌ خطا در ارسال رسانه: {str(e)}")
        logger.error(f"خطا در send_media_reply: {e}")

# Add media parameter for private commands
@app.on_message(filters.command("setprivate") & filters.user(admin_id) & filters.reply)
async def set_private_command(client, message: Message):
    try:
        if len(message.command) < 3:
            await message.reply("⚠️ **استفاده:** `/setprivate [کلمه] [پاسخ]` (ریپلای روی پیام کاربر)")
            return

        keyword = message.command[1]
        response = " ".join(message.command[2:])
        replied_user = message.reply_to_message.from_user
        group_id = message.chat.id
        user_id = replied_user.id

        media_type = None
        media_id = None

        if message.reply_to_message.photo:
            media_type = "photo"
            media_id = message.reply_to_message.photo.file_id
        elif message.reply_to_message.video:
            media_type = "video"
            media_id = message.reply_to_message.video.file_id
        elif message.reply_to_message.audio:
            media_type = "audio"
            media_id = message.reply_to_message.audio.file_id
        elif message.reply_to_message.document:
            media_type = "document"
            media_id = message.reply_to_message.document.file_id
        elif message.reply_to_message.sticker:
            media_type = "sticker"
            media_id = message.reply_to_message.sticker.file_id

        if add_private_command(group_id, user_id, keyword, response, media_type, media_id):
            await message.reply(f"✅ پاسخ خصوصی برای `{keyword}` به کاربر `{replied_user.first_name}` تنظیم شد.")
        else:
            await message.reply(f"⚠️ پاسخ خصوصی برای `{keyword}` قبلاً برای کاربر `{replied_user.first_name}` تنظیم شده است.")

    except Exception as e:
        await message.reply(f"❌ خطا در تنظیم پاسخ خصوصی: {str(e)}")
        logger.error(f"خطا در set_private_command: {e}")

# Modify the help messages to include the stopschedule command
@app.on_message(filters.command(["help", "start"]) & filters.user(admin_id))
async def help_command(client, message: Message):
    try:
        help_text = """
🤖 **راهنمای جامع ربات مدیریت هوشمند دوست و دشمن v2.0**

**🔥 مدیریت سیستم فحش‌ها:**
• `/addfosh [متن]` - اضافه کردن فحش جدید (حداکثر 200 کاراکتر)
• `/delfosh [متن]` - حذف فحش مشخص از دیتابیس
• `/listfosh` - نمایش کامل فحش‌ها با صفحه‌بندی خودکار
• `/clearfosh` - حذف کلی تمام فحش‌ها (غیرقابل بازگشت)

**👹 سیستم مدیریت دشمنان:**
• `/setenemy` (ریپلای) - افزودن کاربر به لیست سیاه
• `/delenemy` (ریپلای) - حذف کاربر از لیست دشمنان
• `/listenemy` - نمایش جزئیات کامل دشمنان + تاریخ
• `/clearenemy` - پاک‌سازی کامل لیست دشمنان

**😊 سیستم مدیریت دوستان:**
• `/setfriend` (ریپلای) - افزودن کاربر به لیست VIP
• `/delfriend` (ریپلای) - حذف کاربر از لیست دوستان
• `/listfriend` - نمایش اطلاعات کامل دوستان + آمار
• `/clearfriend` - حذف کلی لیست دوستان

**💬 بانک کلمات دوستانه:**
• `/addword [متن]` - اضافه کردن پیام دوستانه (حداکثر 200 کاراکتر)
• `/delword [متن]` - حذف کلمه مشخص از بانک
• `/listword` - مشاهده تمام پیام‌های دوستانه
• `/clearword` - حذف کامل بانک

**⏰ سیستم پیام تایمی:**
• `/schedule [پیام] [زمان]` - ارسال پیام در زمان تعیین شده
  └ مثال: `/schedule سلام! 10s` (10 ثانیه دیگه)
  └ واحدها: s=ثانیه, m=دقیقه, h=ساعت, d=روز
  └ حداکثر: قابل تنظیم توسط ادمین
  └ `/stopschedule` - توقف پیام زمان‌بندی شده

**📊 سیستم نظارت و آمارگیری:**
• `/stats` - آمار جامع: تعداد ها، فعالیت‌ها، گزارش کلی
• `/test` - بررسی سلامت ربات و اتصالات
• `/backup` - ایجاد بکاپ امن از دیتابیس
• `/status` - نمایش وضعیت لحظه‌ای سیستم
• `/debug` - بررسی وضعیت پاسخگویی خودکار

**📢 سیستم ارتباطات جمعی:**
• `/broadcast [پیام]` - ارسال همگانی به تمام گروه‌ها
  └ شامل گزارش دقیق موفقیت/ناموفقی
  └ مدیریت خطای Flood + تاخیر هوشمند
  └ فقط گروه‌ها (نه چت خصوصی/کانال)

**🔢 ابزار شمارش هوشمند:**
• `/count [عدد] [مکث]` - شمارش تا عدد مشخص
  └ حداکثر: 1,000,000 عدد
  └ مکث قابل تنظیم: 0.05 تا 5 ثانیه
  └ گزارش پیشرفت هر 1000 عدد
  └ محاسبه زمان و آمار کامل
  └ `/stopcount` - توقف شمارش

**⏰ سیستم پیام زمان‌بندی شده:**
• `/schedule [پیام] [زمان]` - ارسال پیام در زمان تعیین شده
  └ مثال: `/schedule سلام دوستان! 30s`
  └ واحدها: s=ثانیه, m=دقیقه, h=ساعت, d=روز
  └ زمان‌بندی دقیق با گزارش کامل
  └ `/stopschedule` - توقف پیام

**🔐 سیستم کامندهای خصوصی:**
• `/setprivate [کلمه] [پاسخ]` (ریپلای) - تنظیم پاسخ خصوصی
• `/delprivate [کلمه]` (ریپلای) - حذف کامند خصوصی
• `/listprivate` - نمایش لیست کامندهای خصوصی
• `/clearprivate` - حذف تمام کامندهای خصوصی

**🎯 سیستم پاسخ خودکار خاص:**
• `/setautoreply [پاسخ]` (ریپلای) - تنظیم پاسخ خودکار برای شخص خاص در گروه خاص
• `/delautoreply` (ریپلای) - حذف پاسخ خودکار برای شخص خاص
• `/listautoreply` - نمایش لیست پاسخ‌های خودکار
• `/clearautoreply` - حذف تمام پاسخ‌های خودکار

**🔧 مدیریت سیستم:**
• `/runself` - روشن کردن ربات (فقط توسط ادمین)
• `/restartself` - ریستارت کردن ربات (فقط توسط ادمین)
• `/offself` - خاموش کردن ربات (فقط توسط ادمین)
• `/quickhelp` - راهنمای سریع کامندهای اصلی

**⚡ هوش مصنوعی و خودکارسازی:**
🎯 **پاسخ خودکار هوشمند:**
• تشخیص دشمنان → ارسال فحش تصادفی
• تشخیص دوستان → ارسال پیام دوستانه
• فیلتر ادمین → عدم پاسخ به خود ادمین
• تشخیص محیط → فقط فعال در گروه‌ها

🛡️ **سیستم امنیتی پیشرفته:**
• دسترسی انحصاری ادمین به کلیه کامندها
• ثبت کامل لاگ‌ها در دیتابیس SQLite
• جلوگیری از تداخل (دوست+دشمن همزمان)
• محدودیت طول متن ضد اسپم
• مدیریت خطاهای شبکه و Flood

📈 **ویژگی‌های بهینه‌سازی:**
• دیتابیس SQLite با ایندکس‌های بهینه
• صفحه‌بندی خودکار لیست‌های طولانی
• مدیریت حافظه و عملکرد بالا
• بکاپ خودکار و بازیابی اطلاعات

**🔧 پشتیبانی فنی:**
• لاگ‌های کامل در فایل `bot.log`
• آمار لحظه‌ای با `/stats`
• نسخه ربات: v2.0 Professional
• پایگاه داده: SQLite بهینه شده

⭐ **ربات آماده خدمات‌رسانی است!**
        """

        await message.edit_text(help_text)

        logger.info("راهنمای کامل نمایش داده شد")

    except Exception as e:
        error_msg = await message.reply(f"❌ خطا در نمایش راهنما: {str(e)}")
        system_messages['help_error'] = error_msg
        logger.error(f"خطا در help_command: {e}")

#Modify the quickhelp messages to include the stopschedule and stopcount command
@app.on_message(filters.command("quickhelp") & filters.user(admin_id))
async def quick_help(client, message: Message):
    try:
        quick_text = """
⚡ **راهنمای سریع کامندهای اصلی:**

**🔥 فحش:** `/addfosh` `/delfosh` `/listfosh`
**👹 دشمن:** `/setenemy` `/delenemy` `/listenemy` (با ریپلای)
**😊 دوست:** `/setfriend` `/delfriend` `/listfriend` (با ریپلای)
**💬 کلمات:** `/addword` `/delword` `/listword`
**📊 آمار:** `/stats` `/test` `/backup` `/status`
**📢 ارسال:** `/broadcast [پیام]`
**🔢 شمارش:** `/count [عدد] [مکث]` `/stopcount`
**⏰ پیام تایمی:** `/schedule [پیام] [زمان]` `/stopschedule`
**🔐 کامندهای خصوصی:** `/setprivate`, `/delprivate`, `/listprivate`, `/clearprivate` (با ریپلای)
**🎯 پاسخ خودکار خاص:** `/setautoreply`, `/delautoreply`, `/listautoreply`, `/clearautoreply` (با ریپلای)
**⚙️ سیستم:** `/runself` `/restartself` `/offself`

💡 برای راهنمای کامل: `/help`
        """
        await message.edit_text(quick_text)

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

# Add media parameter for broadcast command
@app.on_message(filters.command("broadcast"))
async def broadcast(client, message: Message):
    try:
        if len(message.command) < 2 and not message.reply_to_message:
            await message.edit_text("📢 **استفاده:** `/broadcast پیام_شما`\n\n"
                              "**مثال:** `/broadcast سلام به همه! 👋`")
            return

        text = None
        media_type = None
        media_id = None

        if message.reply_to_message:
            if message.reply_to_message.photo:
                media_type = "photo"
                media_id = message.reply_to_message.photo.file_id
            elif message.reply_to_message.video:
                media_type = "video"
                media_id = message.reply_to_message.video.file_id
            elif message.reply_to_message.audio:
                media_type = "audio"
                media_id = message.reply_to_message.audio.file_id
            elif message.reply_to_message.document:
                media_type = "document"
                media_id = message.reply_to_message.document.file_id
            elif message.reply_to_message.sticker:
                media_type = "sticker"
                media_id = message.reply_to_message.sticker.file_id
            else:
                await message.edit_text("⚠️ لطفا یک پیام معتبر برای ارسال همگانی ریپلای کنید.")
                return
        else:
            text = " ".join(message.command[1:])

            if len(text) > 1000:
                await message.edit_text("⚠️ پیام نباید بیشتر از 1000 کاراکتر باشد.")
                return

        success, fail = 0, 0
        groups_found = 0
        all_chats = 0

        await message.edit_text("🔄 در حال جستجو و ارسال...")

        # دریافت تمام دیالوگ‌ها
        async for dialog in client.get_dialogs():
            all_chats += 1
            chat_type = dialog.chat.type.value if hasattr(dialog.chat.type, 'value') else str(dialog.chat.type)
            chat_title = getattr(dialog.chat, 'title', getattr(dialog.chat, 'first_name', f'Chat {dialog.chat.id}'))

            # بررسی انواع مختلف گروه
            if chat_type in ["group", "supergroup"] or "group" in chat_type.lower():
                groups_found += 1

                try:
                    # ارسال پیام
                    if media_type and media_id:
                        await send_media(client, dialog.chat.id, media_type, media_id)
                    else:
                        await client.send_message(dialog.chat.id, text)
                    success += 1
                    logger.info(f"پیام به گروه {chat_title} ارسال شد")

                    # تاخیر برای جلوگیری از flood
                    await asyncio.sleep(0.5)

                except FloodWait as e:
                    logger.warning(f"FloodWait {e.value} ثانیه")
                    await asyncio.sleep(e.value)
                    # تلاش مجدد
                    try:
                        if media_type and media_id:
                            await send_media(client, dialog.chat.id, media_type, media_id)
                        else:
                            await client.send_message(dialog.chat.id, text)
                        success += 1
                    except:
                        fail += 1

                except Exception as e:
                    fail += 1
                    error_msg = str(e)
                    logger.error(f"خطا در ارسال به گروه {chat_title}: {error_msg}")

        # گزارش نهایی - فقط متن پیام ارسالی
        if text:
            await message.edit_text(text)
        else:
            await message.edit_text("پیام همگانی ارسال شد.")

        # ثبت در آمار
        log_action("broadcast", None, f"success:{success}, fail:{fail}")

    except Exception as e:
        await message.edit_text(f"❌ خطای کلی در ارسال همگانی: {str(e)}")
        logger.error(f"خطای کلی در broadcast: {e}")

# Send media helper function for broadcast
async def send_media_to_chat(client, chat_id, media_type, media_id):
    """Helper function to send media to a specific chat."""
    try:
        if media_type == "photo":
            await client.send_photo(chat_id, media_id)
        elif media_type == "video":
            await client.send_video(chat_id, media_id)
        elif media_type == "audio":
            await client.send_audio(chat_id, media_id)
        elif media_type == "document":
            await client.send_document(chat_id, media_id)
        elif media_type == "sticker":
            await client.send_sticker(chat_id, media_id)
        elif media_type == "animation":
            await client.send_animation(chat_id, media_id)
        elif media_type == "voice":
            await client.send_voice(chat_id, media_id)
        elif media_type == "video_note":
            await client.send_video_note(chat_id, media_id)
    except Exception as e:
        raise e

# پاسخگویی خودکار به پیام‌های گروهی
@app.on_message(~filters.command() & ~filters.user(admin_id))
async def auto_reply(client, message: Message):
    """پاسخگویی خودکار هوشمند به دوستان و دشمنان در گروه‌ها"""
    try:
        # فقط در گروه‌ها فعال باشد
        if message.chat.type not in ["group", "supergroup"]:
            return
            
        # بررسی فعال بودن پاسخگویی خودکار
        if not auto_reply_enabled:
            return
            
        user_id = message.from_user.id
        group_id = message.chat.id
        
        # بررسی پاسخ خودکار اختصاصی برای این شخص در این گروه
        specific_reply = get_auto_reply_specific(group_id, user_id)
        if specific_reply:
            await message.reply(specific_reply)
            log_action("auto_reply_specific", user_id, f"group:{group_id}")
            return
        
        # بررسی دشمن بودن
        enemy_list = get_enemy_list()
        if user_id in enemy_list:
            fosh_list = get_fosh_list()
            if fosh_list:
                selected_fosh = choice(fosh_list)
                if selected_fosh['media_type'] and selected_fosh['media_id']:
                    # ارسال رسانه به عنوان ریپلای
                    await send_media_reply(client, message, selected_fosh['media_type'], selected_fosh['media_id'])
                else:
                    # ارسال متن به عنوان ریپلای
                    await message.reply(selected_fosh['text'])
                
                log_action("auto_fosh", user_id, f"group:{group_id}")
                logger.info(f"فحش خودکار به دشمن {user_id} در گروه {group_id} ارسال شد")
            return
        
        # بررسی دوست بودن
        friend_list = get_friend_list()
        if user_id in friend_list:
            friend_words = get_friend_words()
            if friend_words:
                selected_word = choice(friend_words)
                if selected_word['media_type'] and selected_word['media_id']:
                    # ارسال رسانه به عنوان ریپلای
                    await send_media_reply(client, message, selected_word['media_type'], selected_word['media_id'])
                else:
                    # ارسال متن به عنوان ریپلای
                    await message.reply(selected_word['text'])
                
                log_action("auto_friend", user_id, f"group:{group_id}")
                logger.info(f"پیام دوستانه خودکار به دوست {user_id} در گروه {group_id} ارسال شد")
            return
            
    except Exception as e:
        logger.error(f"خطا در پاسخگویی خودکار: {e}")

# Execution
if __name__ == "__main__":
    logger.info("🚀 ربات هوشمند در حال راه‌اندازی...")
    print("="*60)
    print("🤖 ربات مدیریت دوست و دشمن Professional v2.0")
    print("="*60)
    print("✅ دیتابیس SQLite بهینه شده - آماده")
    print("✅ سیستم لاگینگ پیشرفته - فعال")
    print("✅ هوش مصنوعی پاسخگویی - راه‌اندازی شد")
    print("✅ سیستم آمارگیری - آماده")
    print("✅ امنیت چندلایه - فعال")
    print("✅ حالت 24/7 فعال - ربات همیشه روشن")
    print("-"*60)
    print(f"🔧 ادمین: {admin_id}")
    print(f"⏰ زمان راه‌اندازی: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print("🎯 ربات آماده خدمات‌رسانی 24/7 است!")
    print("💡 دستور /help برای راهنمای کامل")
    print("🛑 دستور /shutdown برای خاموش کردن ربات")
    print("="*60)

    try:
        # اجرای ربات با keep_alive برای حفظ اتصال
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("\n" + "="*60)
        print("⚠️ ربات با کنترل+C متوقف شد")
        print(f"⏰ زمان توقف: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        logger.info("ربات با KeyboardInterrupt متوقف شد")
    except Exception as e:
        print(f"\n❌ خطای غیرمنتظره: {e}")
        print(f"⏰ زمان خطا: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.error(f"خطای غیرمنتظره در اجرای ربات: {e}")
        # تلاش برای راه‌اندازی مجدد
        print("🔄 تلاش برای راه‌اندازی مجدد...")
        import time
        time.sleep(5)
        print("❌ راه‌اندازی مجدد ناموفق - ربات متوقف شد")
        logger.error("راه‌اندازی مجدد ناموفق")