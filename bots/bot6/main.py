
import json
import asyncio
import sys
import sqlite3
import logging
from datetime import datetime, timedelta
import shutil
import os
from random import choice

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

from pyrogram import Client, filters
from pyrogram.types import Message, ChatMember
from pyrogram.errors import FloodWait, UserNotParticipant, ChatWriteForbidden

# تنظیمات اصلی بات 6
api_id = 24815549
api_hash = "13d1e8f4d5e90fdd11f7cb9152d78268"
admin_id = 7927398744

# تنظیم لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot6.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Client(
    "my_bot6", 
    api_id, 
    api_hash,
    workdir="./",
    sleep_threshold=5,
    max_concurrent_transmissions=30
)

# متغیرهای کنترل
auto_reply_enabled = True
count_tasks = {}
scheduled_messages = {}

# ایجاد پایگاه داده
def init_db():
    conn = sqlite3.connect('bot6_data.db')
    cursor = conn.cursor()
    
    # جدول فحش‌ها
    cursor.execute('''CREATE TABLE IF NOT EXISTS fosh_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fosh TEXT UNIQUE,
        media_type TEXT,
        file_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول دشمنان
    cursor.execute('''CREATE TABLE IF NOT EXISTS enemy_list (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول دوستان
    cursor.execute('''CREATE TABLE IF NOT EXISTS friend_list (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول کلمات دوستانه
    cursor.execute('''CREATE TABLE IF NOT EXISTS friend_words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT UNIQUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول لاگ
    cursor.execute('''CREATE TABLE IF NOT EXISTS action_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT NOT NULL,
        user_id INTEGER,
        details TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()

# توابع مدیریت فحش‌ها
def add_fosh(fosh=None, media_type=None, file_id=None):
    conn = sqlite3.connect('bot6_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO fosh_list (fosh, media_type, file_id) VALUES (?, ?, ?)", 
                      (fosh, media_type, file_id))
        conn.commit()
        result = True
    except Exception as e:
        logger.error(f"خطا در اضافه کردن فحش: {e}")
        result = False
    conn.close()
    return result

def remove_fosh(fosh):
    conn = sqlite3.connect('bot6_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fosh_list WHERE fosh = ?", (fosh,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_fosh_list():
    conn = sqlite3.connect('bot6_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT fosh, media_type, file_id FROM fosh_list")
    result = cursor.fetchall()
    conn.close()
    return result

def clear_fosh_list():
    conn = sqlite3.connect('bot6_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fosh_list")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

# توابع مدیریت دشمنان
def add_enemy(user_id, username=None, first_name=None):
    conn = sqlite3.connect('bot6_data.db')
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

def remove_enemy(user_id):
    conn = sqlite3.connect('bot6_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM enemy_list WHERE user_id = ?", (user_id,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_enemy_list():
    conn = sqlite3.connect('bot6_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, first_name, created_at FROM enemy_list")
    result = cursor.fetchall()
    conn.close()
    return result

def clear_enemy_list():
    conn = sqlite3.connect('bot6_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM enemy_list")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

def is_enemy(user_id):
    conn = sqlite3.connect('bot6_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM enemy_list WHERE user_id = ?", (user_id,))
    result = cursor.fetchone() is not None
    conn.close()
    return result

# توابع مدیریت دوستان
def add_friend(user_id, username=None, first_name=None):
    conn = sqlite3.connect('bot6_data.db')
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

def remove_friend(user_id):
    conn = sqlite3.connect('bot6_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM friend_list WHERE user_id = ?", (user_id,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_friend_list():
    conn = sqlite3.connect('bot6_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, first_name, created_at FROM friend_list")
    result = cursor.fetchall()
    conn.close()
    return result

def is_friend(user_id):
    conn = sqlite3.connect('bot6_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM friend_list WHERE user_id = ?", (user_id,))
    result = cursor.fetchone() is not None
    conn.close()
    return result

# توابع مدیریت کلمات دوستانه
def add_friend_word(word):
    conn = sqlite3.connect('bot6_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO friend_words (word) VALUES (?)", (word,))
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    conn.close()
    return result

def remove_friend_word(word):
    conn = sqlite3.connect('bot6_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM friend_words WHERE word = ?", (word,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_friend_words():
    conn = sqlite3.connect('bot6_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT word FROM friend_words")
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result

# تابع لاگ
def log_action(action_type, user_id=None, details=None):
    conn = sqlite3.connect('bot6_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO action_log (action_type, user_id, details) VALUES (?, ?, ?)", 
                  (action_type, user_id, details))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect('bot6_data.db')
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

# شروع برنامه
init_db()

# کامند شروع
@app.on_message(filters.command("start") & filters.user(admin_id))
async def start_command(client, message: Message):
    await message.edit_text(f"🤖 **ربات 6 آماده است!**\n\n📋 برای مشاهده کامندها: `/help`\n🆔 Admin: `{admin_id}`")

# کامند راهنما
@app.on_message(filters.command("help") & filters.user(admin_id))
async def help_command(client, message: Message):
    help_text = """
🤖 **راهنمای ربات 6**

**📝 مدیریت فحش‌ها:**
• `/addfosh [متن]` - اضافه کردن فحش
• `/delfosh [متن]` - حذف فحش
• `/listfosh` - نمایش لیست فحش‌ها
• `/clearfosh` - پاک کردن همه فحش‌ها

**👿 مدیریت دشمنان:**
• `/setenemy` - اضافه کردن دشمن (ریپلای)
• `/delenemy` - حذف دشمن (ریپلای)
• `/enemies` - نمایش لیست دشمنان

**😊 مدیریت دوستان:**
• `/setfriend` - اضافه کردن دوست (ریپلای)
• `/delfriend` - حذف دوست (ریپلای)
• `/friends` - نمایش لیست دوستان

**💬 مدیریت کلمات دوستانه:**
• `/addword [کلمه]` - اضافه کردن کلمه
• `/delword [کلمه]` - حذف کلمه
• `/words` - نمایش کلمات

**⚙️ تنظیمات:**
• `/autoreply` - فعال/غیرفعال پاسخگویی
• `/stats` - نمایش آمار
• `/broadcast [پیام]` - ارسال همگانی
    """
    await message.edit_text(help_text)

# مدیریت فحش‌ها
@app.on_message(filters.command("addfosh") & filters.user(admin_id))
async def add_fosh_command(client, message: Message):
    if message.reply_to_message:
        replied_msg = message.reply_to_message
        if replied_msg.text:
            if add_fosh(replied_msg.text):
                await message.edit_text(f"✅ فحش اضافه شد: {replied_msg.text}")
                log_action("add_fosh", admin_id, replied_msg.text)
            else:
                await message.edit_text("❌ خطا در اضافه کردن فحش!")
        elif replied_msg.sticker:
            if add_fosh(media_type="sticker", file_id=replied_msg.sticker.file_id):
                await message.edit_text("✅ استیکر فحش اضافه شد!")
                log_action("add_fosh_sticker", admin_id, replied_msg.sticker.file_id)
            else:
                await message.edit_text("❌ خطا در اضافه کردن استیکر!")
        elif replied_msg.animation:
            if add_fosh(media_type="animation", file_id=replied_msg.animation.file_id):
                await message.edit_text("✅ گیف فحش اضافه شد!")
                log_action("add_fosh_gif", admin_id, replied_msg.animation.file_id)
            else:
                await message.edit_text("❌ خطا در اضافه کردن گیف!")
    else:
        if len(message.command) > 1:
            fosh_text = " ".join(message.command[1:])
            if add_fosh(fosh_text):
                await message.edit_text(f"✅ فحش اضافه شد: {fosh_text}")
                log_action("add_fosh", admin_id, fosh_text)
            else:
                await message.edit_text("❌ خطا در اضافه کردن فحش!")
        else:
            await message.edit_text("❌ روی پیام ریپلای کنید یا متن فحش را بنویسید!")

@app.on_message(filters.command("delfosh") & filters.user(admin_id))
async def del_fosh_command(client, message: Message):
    if len(message.command) > 1:
        fosh_text = " ".join(message.command[1:])
        if remove_fosh(fosh_text):
            await message.edit_text(f"✅ فحش حذف شد: {fosh_text}")
            log_action("del_fosh", admin_id, fosh_text)
        else:
            await message.edit_text("❌ فحش یافت نشد!")
    else:
        await message.edit_text("❌ متن فحش را بنویسید!")

@app.on_message(filters.command("listfosh") & filters.user(admin_id))
async def list_fosh_command(client, message: Message):
    fosh_list = get_fosh_list()
    if fosh_list:
        text = "📝 **لیست فحش‌ها:**\n\n"
        for i, (fosh, media_type, file_id) in enumerate(fosh_list, 1):
            if media_type:
                text += f"{i}. [{media_type.upper()}]\n"
            else:
                text += f"{i}. {fosh}\n"
            if len(text) > 3500:
                await message.edit_text(text)
                text = ""
        if text:
            await message.edit_text(text)
    else:
        await message.edit_text("📝 لیست فحش‌ها خالی است!")

@app.on_message(filters.command("clearfosh") & filters.user(admin_id))
async def clear_fosh_command(client, message: Message):
    count = clear_fosh_list()
    await message.edit_text(f"✅ {count} فحش حذف شد!")
    log_action("clear_fosh", admin_id, f"{count} items")

# مدیریت دشمنان
@app.on_message(filters.command("setenemy") & filters.user(admin_id))
async def set_enemy_command(client, message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user
        if add_enemy(user.id, user.username, user.first_name):
            await message.edit_text(f"👿 {user.first_name or user.username} به دشمنان اضافه شد!")
            log_action("add_enemy", admin_id, f"User: {user.id}")
        else:
            await message.edit_text("❌ این کاربر قبلاً در لیست دشمنان است!")
    else:
        await message.edit_text("❌ روی پیام کاربر ریپلای کنید!")

@app.on_message(filters.command("delenemy") & filters.user(admin_id))
async def del_enemy_command(client, message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user
        if remove_enemy(user.id):
            await message.edit_text(f"✅ {user.first_name or user.username} از دشمنان حذف شد!")
            log_action("del_enemy", admin_id, f"User: {user.id}")
        else:
            await message.edit_text("❌ این کاربر در لیست دشمنان نیست!")
    else:
        await message.edit_text("❌ روی پیام کاربر ریپلای کنید!")

@app.on_message(filters.command("enemies") & filters.user(admin_id))
async def enemies_command(client, message: Message):
    enemies = get_enemy_list()
    if enemies:
        text = "👿 **لیست دشمنان:**\n\n"
        for user_id, username, first_name, created_at in enemies:
            name = first_name or username or str(user_id)
            text += f"• {name} (ID: {user_id})\n"
        await message.edit_text(text)
    else:
        await message.edit_text("👿 لیست دشمنان خالی است!")

# مدیریت دوستان
@app.on_message(filters.command("setfriend") & filters.user(admin_id))
async def set_friend_command(client, message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user
        if add_friend(user.id, user.username, user.first_name):
            await message.edit_text(f"😊 {user.first_name or user.username} به دوستان اضافه شد!")
            log_action("add_friend", admin_id, f"User: {user.id}")
        else:
            await message.edit_text("❌ این کاربر قبلاً در لیست دوستان است!")
    else:
        await message.edit_text("❌ روی پیام کاربر ریپلای کنید!")

@app.on_message(filters.command("delfriend") & filters.user(admin_id))
async def del_friend_command(client, message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user
        if remove_friend(user.id):
            await message.edit_text(f"✅ {user.first_name or user.username} از دوستان حذف شد!")
            log_action("del_friend", admin_id, f"User: {user.id}")
        else:
            await message.edit_text("❌ این کاربر در لیست دوستان نیست!")
    else:
        await message.edit_text("❌ روی پیام کاربر ریپلای کنید!")

@app.on_message(filters.command("friends") & filters.user(admin_id))
async def friends_command(client, message: Message):
    friends = get_friend_list()
    if friends:
        text = "😊 **لیست دوستان:**\n\n"
        for user_id, username, first_name, created_at in friends:
            name = first_name or username or str(user_id)
            text += f"• {name} (ID: {user_id})\n"
        await message.edit_text(text)
    else:
        await message.edit_text("😊 لیست دوستان خالی است!")

# مدیریت کلمات دوستانه
@app.on_message(filters.command("addword") & filters.user(admin_id))
async def add_word_command(client, message: Message):
    if len(message.command) > 1:
        word = " ".join(message.command[1:])
        if add_friend_word(word):
            await message.edit_text(f"✅ کلمه اضافه شد: {word}")
            log_action("add_word", admin_id, word)
        else:
            await message.edit_text("❌ این کلمه قبلاً وجود دارد!")
    else:
        await message.edit_text("❌ کلمه را بنویسید!")

@app.on_message(filters.command("delword") & filters.user(admin_id))
async def del_word_command(client, message: Message):
    if len(message.command) > 1:
        word = " ".join(message.command[1:])
        if remove_friend_word(word):
            await message.edit_text(f"✅ کلمه حذف شد: {word}")
            log_action("del_word", admin_id, word)
        else:
            await message.edit_text("❌ کلمه یافت نشد!")
    else:
        await message.edit_text("❌ کلمه را بنویسید!")

@app.on_message(filters.command("words") & filters.user(admin_id))
async def words_command(client, message: Message):
    words = get_friend_words()
    if words:
        text = "💬 **کلمات دوستانه:**\n\n"
        for i, word in enumerate(words, 1):
            text += f"{i}. {word}\n"
        await message.edit_text(text)
    else:
        await message.edit_text("💬 لیست کلمات خالی است!")

# تنظیمات
@app.on_message(filters.command("autoreply") & filters.user(admin_id))
async def autoreply_command(client, message: Message):
    global auto_reply_enabled
    auto_reply_enabled = not auto_reply_enabled
    status = "فعال" if auto_reply_enabled else "غیرفعال"
    await message.edit_text(f"🔄 پاسخگویی خودکار {status} شد!")

@app.on_message(filters.command("stats") & filters.user(admin_id))
async def stats_command(client, message: Message):
    stats = get_stats()
    text = f"""
📊 **آمار ربات 6:**

🔥 فحش‌ها: {stats['fosh_count']}
👿 دشمنان: {stats['enemy_count']}
😊 دوستان: {stats['friend_count']}
💬 کلمات: {stats['word_count']}

🆔 Admin: {admin_id}
    """
    await message.edit_text(text)

# پاسخگویی خودکار
@app.on_message(filters.private & ~filters.user(admin_id) & ~filters.command(["start", "help"]))
async def auto_reply_handler(client, message: Message):
    if not auto_reply_enabled:
        return
    
    user_id = message.from_user.id
    
    # بررسی دشمن
    if is_enemy(user_id):
        fosh_list = get_fosh_list()
        if fosh_list:
            fosh_data = choice(fosh_list)
            fosh_text, media_type, file_id = fosh_data
            
            try:
                if media_type == "sticker":
                    await message.reply_sticker(file_id)
                elif media_type == "animation":
                    await message.reply_animation(file_id)
                else:
                    await message.reply_text(fosh_text)
                log_action("auto_reply_enemy", user_id, "Sent curse")
            except Exception as e:
                logger.error(f"خطا در ارسال فحش: {e}")
    
    # بررسی دوست
    elif is_friend(user_id):
        friend_words = get_friend_words()
        if friend_words:
            try:
                await message.reply_text(choice(friend_words))
                log_action("auto_reply_friend", user_id, "Sent friendly word")
            except Exception as e:
                logger.error(f"خطا در ارسال کلمه دوستانه: {e}")

# ارسال همگانی
@app.on_message(filters.command("broadcast") & filters.user(admin_id))
async def broadcast_command(client, message: Message):
    if len(message.command) > 1:
        broadcast_text = " ".join(message.command[1:])
        
        # دریافت همه دوستان
        friends = get_friend_list()
        success_count = 0
        
        for user_id, username, first_name, created_at in friends:
            try:
                await client.send_message(user_id, broadcast_text)
                success_count += 1
                await asyncio.sleep(1)  # تاخیر برای جلوگیری از فلود
            except Exception as e:
                logger.error(f"خطا در ارسال به {user_id}: {e}")
        
        await message.edit_text(f"✅ پیام به {success_count} نفر ارسال شد!")
        log_action("broadcast", admin_id, f"Sent to {success_count} users")
    else:
        await message.edit_text("❌ متن پیام را بنویسید!")

# شروع بات
if __name__ == "__main__":
    print("Bot 6 initialized and ready!")
    logger.info("ربات 6 آماده شد!")
    logger.info("ربات 6 آماده شد و کش راه‌اندازی شد!")
    
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("ربات 6 متوقف شد!")
    except Exception as e:
        logger.error(f"خطا در اجرای ربات 6: {e}")
