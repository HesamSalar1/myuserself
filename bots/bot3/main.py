
import json
import asyncio
import sys
import sqlite3
import logging
from datetime import datetime
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

from pyrogram import Client, filters
from pyrogram.types import Message, ChatMember
from pyrogram.errors import FloodWait, UserNotParticipant, ChatWriteForbidden
from random import choice

# تنظیمات اصلی بات 3
api_id = 21555907
api_hash = "16f4e09d753bc4b182434d8e37f410cd"
admin_id = 7607882302

# تنظیم لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot3.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Client("my_bot3", api_id, api_hash, phone_number="+989111222333")

# متغیر کنترل وضعیت پاسخگویی خودکار
auto_reply_enabled = True

# تابع اتصال به دیتابیس
def init_db():
    conn = sqlite3.connect('bot3_data.db')
    cursor = conn.cursor()
    
    # ایجاد جداول
    cursor.execute('''CREATE TABLE IF NOT EXISTS fosh_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fosh TEXT UNIQUE NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS enemy_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        first_name TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS friend_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        first_name TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS friend_words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT UNIQUE NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS action_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT NOT NULL,
        user_id INTEGER,
        details TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

# توابع مدیریت دیتابیس
def add_fosh(fosh):
    conn = sqlite3.connect('bot3_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO fosh_list (fosh) VALUES (?)", (fosh,))
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    conn.close()
    return result

def remove_fosh(fosh):
    conn = sqlite3.connect('bot3_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fosh_list WHERE fosh = ?", (fosh,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_fosh_list():
    conn = sqlite3.connect('bot3_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT fosh FROM fosh_list")
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result

def add_enemy(user_id, username=None, first_name=None):
    conn = sqlite3.connect('bot3_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO enemy_list (user_id, username, first_name) VALUES (?, ?, ?)", 
                      (user_id, username, first_name))
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    conn.close()
    return result

def remove_enemy(user_id):
    conn = sqlite3.connect('bot3_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM enemy_list WHERE user_id = ?", (user_id,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_enemy_list():
    conn = sqlite3.connect('bot3_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM enemy_list")
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result

def add_friend(user_id, username=None, first_name=None):
    conn = sqlite3.connect('bot3_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO friend_list (user_id, username, first_name) VALUES (?, ?, ?)", 
                      (user_id, username, first_name))
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    conn.close()
    return result

def remove_friend(user_id):
    conn = sqlite3.connect('bot3_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM friend_list WHERE user_id = ?", (user_id,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_friend_list():
    conn = sqlite3.connect('bot3_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM friend_list")
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result

def add_friend_word(word):
    conn = sqlite3.connect('bot3_data.db')
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
    conn = sqlite3.connect('bot3_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM friend_words WHERE word = ?", (word,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_friend_words():
    conn = sqlite3.connect('bot3_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT word FROM friend_words")
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result

def log_action(action_type, user_id=None, details=None):
    conn = sqlite3.connect('bot3_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO action_log (action_type, user_id, details) VALUES (?, ?, ?)", 
                  (action_type, user_id, details))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect('bot3_data.db')
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

# کامند اضافه کردن فحش
@app.on_message(filters.command("addfosh") & filters.user(admin_id))
async def add_fosh_command(client, message: Message):
    try:
        if len(message.command) < 2:
            await message.edit_text("⚠️ لطفاً یک فحش وارد کنید.\n💡 استفاده: `/addfosh متن فحش`")
            return

        fosh = " ".join(message.command[1:])
        
        if add_fosh(fosh):
            await message.edit_text(f"✅ فحش جدید اضافه شد:\n`{fosh}`")
            log_action("add_fosh", admin_id, fosh[:50])
            logger.info(f"فحش جدید اضافه شد: {fosh}")
        else:
            await message.edit_text(f"⚠️ این فحش قبلاً در لیست موجود است:\n`{fosh}`")

    except Exception as e:
        await message.edit_text(f"❌ خطا در اضافه کردن فحش: {str(e)}")
        logger.error(f"خطا در add_fosh_command: {e}")

# کامند حذف فحش
@app.on_message(filters.command("delfosh") & filters.user(admin_id))
async def del_fosh_command(client, message: Message):
    try:
        if len(message.command) < 2:
            await message.edit_text("⚠️ لطفاً فحش مورد نظر را وارد کنید.\n💡 استفاده: `/delfosh متن فحش`")
            return

        fosh = " ".join(message.command[1:])
        
        if remove_fosh(fosh):
            await message.edit_text(f"✅ فحش حذف شد:\n`{fosh}`")
            log_action("del_fosh", admin_id, fosh[:50])
            logger.info(f"فحش حذف شد: {fosh}")
        else:
            await message.edit_text(f"⚠️ این فحش در لیست یافت نشد:\n`{fosh}`")

    except Exception as e:
        await message.edit_text(f"❌ خطا در حذف فحش: {str(e)}")
        logger.error(f"خطا در del_fosh_command: {e}")

# کامند نمایش لیست فحش‌ها
@app.on_message(filters.command("listfosh") & filters.user(admin_id))
async def list_fosh_command(client, message: Message):
    try:
        fosh_list = get_fosh_list()
        if not fosh_list:
            await message.edit_text("📝 لیست فحش‌ها خالی است.\n💡 با `/addfosh` فحش اضافه کنید.")
            return

        text = "🔥 **لیست فحش‌ها:**\n\n"
        for i, fosh in enumerate(fosh_list, 1):
            text += f"`{i}.` {fosh}\n"

        text += f"\n📊 **تعداد کل:** {len(fosh_list)} فحش"
        await message.edit_text(text)

    except Exception as e:
        await message.edit_text(f"❌ خطا در نمایش لیست: {str(e)}")
        logger.error(f"خطا در list_fosh_command: {e}")

# کامند اضافه کردن دشمن
@app.on_message(filters.command("setenemy") & filters.user(admin_id) & filters.reply)
async def set_enemy_command(client, message: Message):
    try:
        replied = message.reply_to_message
        user_id = replied.from_user.id
        username = replied.from_user.username
        first_name = replied.from_user.first_name
        
        if add_enemy(user_id, username, first_name):
            await message.edit_text(f"👹 کاربر به لیست دشمنان اضافه شد:\n**نام:** {first_name}\n**آیدی:** `{user_id}`")
            log_action("add_enemy", user_id, f"{first_name} (@{username})")
            logger.info(f"دشمن جدید اضافه شد: {user_id} ({first_name})")
        else:
            await message.edit_text(f"⚠️ این کاربر قبلاً در لیست دشمنان است:\n**نام:** {first_name}\n**آیدی:** `{user_id}`")

    except Exception as e:
        await message.edit_text(f"❌ خطا در اضافه کردن دشمن: {str(e)}")
        logger.error(f"خطا در set_enemy_command: {e}")

# کامند حذف دشمن
@app.on_message(filters.command("delenemy") & filters.user(admin_id) & filters.reply)
async def del_enemy_command(client, message: Message):
    try:
        replied = message.reply_to_message
        user_id = replied.from_user.id
        first_name = replied.from_user.first_name
        
        if remove_enemy(user_id):
            await message.edit_text(f"✅ کاربر از لیست دشمنان حذف شد:\n**نام:** {first_name}\n**آیدی:** `{user_id}`")
            log_action("del_enemy", user_id, f"{first_name}")
            logger.info(f"دشمن حذف شد: {user_id} ({first_name})")
        else:
            await message.edit_text(f"⚠️ این کاربر در لیست دشمنان یافت نشد:\n**نام:** {first_name}\n**آیدی:** `{user_id}`")

    except Exception as e:
        await message.edit_text(f"❌ خطا در حذف دشمن: {str(e)}")
        logger.error(f"خطا در del_enemy_command: {e}")

# کامند اضافه کردن دوست
@app.on_message(filters.command("setfriend") & filters.user(admin_id) & filters.reply)
async def set_friend_command(client, message: Message):
    try:
        replied = message.reply_to_message
        user_id = replied.from_user.id
        username = replied.from_user.username
        first_name = replied.from_user.first_name
        
        if add_friend(user_id, username, first_name):
            await message.edit_text(f"😊 کاربر به لیست دوستان اضافه شد:\n**نام:** {first_name}\n**آیدی:** `{user_id}`")
            log_action("add_friend", user_id, f"{first_name} (@{username})")
            logger.info(f"دوست جدید اضافه شد: {user_id} ({first_name})")
        else:
            await message.edit_text(f"⚠️ این کاربر قبلاً در لیست دوستان است:\n**نام:** {first_name}\n**آیدی:** `{user_id}`")

    except Exception as e:
        await message.edit_text(f"❌ خطا در اضافه کردن دوست: {str(e)}")
        logger.error(f"خطا در set_friend_command: {e}")

# کامند حذف دوست
@app.on_message(filters.command("delfriend") & filters.user(admin_id) & filters.reply)
async def del_friend_command(client, message: Message):
    try:
        replied = message.reply_to_message
        user_id = replied.from_user.id
        first_name = replied.from_user.first_name
        
        if remove_friend(user_id):
            await message.edit_text(f"✅ کاربر از لیست دوستان حذف شد:\n**نام:** {first_name}\n**آیدی:** `{user_id}`")
            log_action("del_friend", user_id, f"{first_name}")
            logger.info(f"دوست حذف شد: {user_id} ({first_name})")
        else:
            await message.edit_text(f"⚠️ این کاربر در لیست دوستان یافت نشد:\n**نام:** {first_name}\n**آیدی:** `{user_id}`")

    except Exception as e:
        await message.edit_text(f"❌ خطا در حذف دوست: {str(e)}")
        logger.error(f"خطا در del_friend_command: {e}")

# کامند اضافه کردن کلمه دوستانه
@app.on_message(filters.command("addword") & filters.user(admin_id))
async def add_word_command(client, message: Message):
    try:
        if len(message.command) < 2:
            await message.edit_text("⚠️ لطفاً یک کلمه دوستانه وارد کنید.\n💡 استفاده: `/addword سلام دوست عزیز`")
            return

        word = " ".join(message.command[1:])
        
        if add_friend_word(word):
            await message.edit_text(f"✅ کلمه دوستانه اضافه شد:\n`{word}`")
            log_action("add_word", admin_id, word[:50])
            logger.info(f"کلمه دوستانه اضافه شد: {word}")
        else:
            await message.edit_text(f"⚠️ این کلمه قبلاً در لیست موجود است:\n`{word}`")

    except Exception as e:
        await message.edit_text(f"❌ خطا در اضافه کردن کلمه: {str(e)}")
        logger.error(f"خطا در add_word_command: {e}")

# کامند حذف کلمه دوستانه
@app.on_message(filters.command("delword") & filters.user(admin_id))
async def del_word_command(client, message: Message):
    try:
        if len(message.command) < 2:
            await message.edit_text("⚠️ لطفاً کلمه مورد نظر را وارد کنید.\n💡 استفاده: `/delword کلمه`")
            return

        word = " ".join(message.command[1:])
        
        if remove_friend_word(word):
            await message.edit_text(f"✅ کلمه دوستانه حذف شد:\n`{word}`")
            log_action("del_word", admin_id, word[:50])
            logger.info(f"کلمه دوستانه حذف شد: {word}")
        else:
            await message.edit_text(f"⚠️ این کلمه در لیست یافت نشد:\n`{word}`")

    except Exception as e:
        await message.edit_text(f"❌ خطا در حذف کلمه: {str(e)}")
        logger.error(f"خطا در del_word_command: {e}")

# کامند نمایش آمار
@app.on_message(filters.command("stats") & filters.user(admin_id))
async def stats_command(client, message: Message):
    try:
        stats = get_stats()
        
        text = "📊 **آمار کامل ربات 3:**\n\n"
        text += f"🔥 فحش‌ها: `{stats['fosh_count']}` عدد\n"
        text += f"👹 دشمنان: `{stats['enemy_count']}` نفر\n"
        text += f"😊 دوستان: `{stats['friend_count']}` نفر\n"
        text += f"💬 کلمات دوستانه: `{stats['word_count']}` عدد\n\n"
        text += f"🤖 **وضعیت پاسخگویی:** {'فعال ✅' if auto_reply_enabled else 'غیرفعال ❌'}\n"
        text += f"⏰ **آخرین بروزرسانی:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        await message.edit_text(text)
        log_action("stats_view", admin_id, "نمایش آمار")

    except Exception as e:
        await message.edit_text(f"❌ خطا در نمایش آمار: {str(e)}")
        logger.error(f"خطا در stats_command: {e}")

# کامند فعال/غیرفعال کردن پاسخگویی خودکار
@app.on_message(filters.command(["autoreply", "toggle"]) & filters.user(admin_id))
async def toggle_auto_reply(client, message: Message):
    global auto_reply_enabled
    try:
        auto_reply_enabled = not auto_reply_enabled
        status = "فعال ✅" if auto_reply_enabled else "غیرفعال ❌"
        await message.edit_text(f"🤖 **پاسخگویی خودکار:** {status}")
        log_action("toggle_auto_reply", admin_id, f"وضعیت: {status}")
        logger.info(f"پاسخگویی خودکار تغییر کرد: {status}")

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")
        logger.error(f"خطا در toggle_auto_reply: {e}")

# کامند ارسال همگانی
@app.on_message(filters.command("broadcast") & filters.user(admin_id))
async def broadcast_command(client, message: Message):
    try:
        if len(message.command) < 2:
            await message.edit_text("⚠️ لطفاً پیام مورد نظر را وارد کنید.\n💡 استفاده: `/broadcast سلام به همه`")
            return

        text = " ".join(message.command[1:])
        
        # دریافت تمام کاربران
        friend_list = get_friend_list()
        enemy_list = get_enemy_list()
        all_users = set(friend_list + enemy_list)
        
        if not all_users:
            await message.edit_text("⚠️ هیچ کاربری در لیست دوستان یا دشمنان موجود نیست!")
            return

        await message.edit_text(f"📤 شروع ارسال پیام به {len(all_users)} کاربر...")
        
        success = 0
        fail = 0
        
        for user_id in all_users:
            try:
                await client.send_message(user_id, text)
                success += 1
                await asyncio.sleep(0.1)  # تاخیر برای جلوگیری از فلاد
            except FloodWait as e:
                logger.warning(f"FloodWait {e.value} ثانیه")
                await asyncio.sleep(e.value)
                try:
                    await client.send_message(user_id, text)
                    success += 1
                except:
                    fail += 1
            except Exception as e:
                fail += 1
                logger.error(f"خطا در ارسال به {user_id}: {e}")

        result_text = f"✅ **ارسال همگانی تکمیل شد:**\n\n"
        result_text += f"📤 **ارسال شده:** {success} نفر\n"
        result_text += f"❌ **ناموفق:** {fail} نفر\n"
        result_text += f"📊 **کل:** {len(all_users)} نفر"
        
        await message.edit_text(result_text)
        log_action("broadcast", admin_id, f"موفق:{success}, ناموفق:{fail}")

    except Exception as e:
        await message.edit_text(f"❌ خطا در ارسال همگانی: {str(e)}")
        logger.error(f"خطا در broadcast_command: {e}")

# پاسخگویی خودکار
@app.on_message(~filters.me & ~filters.channel)
async def auto_reply_handler(client, message: Message):
    try:
        if not auto_reply_enabled:
            return

        if not message.from_user:
            return

        user_id = message.from_user.id
        user_name = message.from_user.first_name or "کاربر"
        
        # دریافت لیست‌ها
        friend_list = get_friend_list()
        enemy_list = get_enemy_list()
        
        # پاسخ به دشمنان
        if user_id in enemy_list:
            fosh_list = get_fosh_list()
            if fosh_list:
                try:
                    fosh = choice(fosh_list)
                    await message.reply(fosh)
                    logger.info(f"فحش به دشمن {user_id} ({user_name}) ارسال شد")
                    log_action("auto_reply_enemy", user_id, fosh[:50])
                except Exception as e:
                    logger.error(f"خطا در ارسال فحش: {e}")

        # پاسخ به دوستان
        elif user_id in friend_list:
            friend_words = get_friend_words()
            if friend_words:
                try:
                    word = choice(friend_words)
                    await message.reply(word)
                    logger.info(f"پاسخ دوستانه به {user_id} ({user_name}) ارسال شد")
                    log_action("auto_reply_friend", user_id, word[:50])
                except Exception as e:
                    logger.error(f"خطا در ارسال پاسخ دوستانه: {e}")

    except Exception as e:
        logger.error(f"خطا در auto_reply_handler: {e}")

# راهنما
@app.on_message(filters.command("help") & filters.user(admin_id))
async def help_command(client, message: Message):
    try:
        text = """📚 **راهنمای ربات 3:**

🔥 **مدیریت فحش‌ها:**
• `/addfosh [متن]` - اضافه کردن فحش
• `/delfosh [متن]` - حذف فحش
• `/listfosh` - نمایش لیست فحش‌ها

👹 **مدیریت دشمنان:**
• `/setenemy` - اضافه کردن دشمن (ریپلای)
• `/delenemy` - حذف دشمن (ریپلای)

😊 **مدیریت دوستان:**
• `/setfriend` - اضافه کردن دوست (ریپلای)
• `/delfriend` - حذف دوست (ریپلای)

💬 **مدیریت کلمات دوستانه:**
• `/addword [متن]` - اضافه کردن کلمه
• `/delword [متن]` - حذف کلمه

🤖 **تنظیمات:**
• `/autoreply` - فعال/غیرفعال پاسخگویی
• `/stats` - نمایش آمار
• `/broadcast [پیام]` - ارسال همگانی

ℹ️ **سایر:**
• `/help` - نمایش این راهنما"""

        await message.edit_text(text)

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")
        logger.error(f"خطا در help_command: {e}")

print("Bot 3 initialized and ready!")
logger.info("ربات 3 آماده شد!")

if __name__ == "__main__":
    app.run()
