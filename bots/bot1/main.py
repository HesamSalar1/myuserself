import json
import asyncio
import sys
import sqlite3
import logging
import getpass
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
from pyrogram.errors import FloodWait, UserNotParticipant, ChatWriteForbidden, SessionPasswordNeeded, PhoneCodeInvalid, PhoneNumberInvalid

# تنظیمات اصلی بات 1
api_id = 15508294
api_hash = "778e5cd56ffcf22c2d62aa963ce85a0c"
admin_id = 7850529246

# تنظیم لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot1.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Client(
    "my_bot1", 
    api_id, 
    api_hash,
    workdir="./",
    sleep_threshold=5,
    max_concurrent_transmissions=30
)

# import ماژول کنترل اکو مشترک
import sys
sys.path.append('..')
from echo_control import set_echo_active, is_echo_active

# متغیرهای کنترل
auto_reply_enabled = True
count_tasks = {}
scheduled_messages = {}

async def login_user():
    """سیستم پیشرفته لاگین و دریافت session"""
    try:
        print(f"🔐 شروع فرآیند لاگین برای بات 1...")
        print(f"📱 API ID: {api_id}")
        print(f"🔑 API Hash: {api_hash[:10]}...")

        # تلاش برای اتصال
        await app.connect()

        # بررسی وضعیت احراز هویت
        try:
            me = await app.get_me()
            print(f"✅ شما قبلاً وارد شده‌اید: {me.first_name} (@{me.username})")
            print(f"📞 شماره تلفن: {me.phone_number}")
            print(f"🆔 User ID: {me.id}")
            return True
        except:
            print("❌ session موجود نیست یا منقضی شده. شروع فرآیند لاگین جدید...")

        # درخواست شماره تلفن
        phone_number = input("📱 شماره تلفن خود را وارد کنید (به همراه کد کشور): ").strip()

        if not phone_number:
            print("❌ شماره تلفن نمی‌تواند خالی باشد")
            return False

        print(f"📤 ارسال کد تأیید به {phone_number}...")

        try:
            # ارسال کد
            sent_code = await app.send_code(phone_number)
            print(f"✅ کد تأیید ارسال شد")
            print(f"📋 نوع کد: {sent_code.type}")

            # درخواست کد تأیید
            verification_code = input("🔢 کد 5 رقمی ارسال شده را وارد کنید: ").strip()

            if not verification_code or len(verification_code) != 5:
                print("❌ کد تأیید باید 5 رقم باشد")
                return False

            try:
                # تأیید کد و لاگین
                await app.sign_in(phone_number, sent_code.phone_code_hash, verification_code)

            except SessionPasswordNeeded:
                print("🔐 احراز هویت دو مرحله‌ای فعال است")
                password = getpass.getpass("🔑 رمز عبور خود را وارد کنید: ")

                if not password:
                    print("❌ رمز عبور نمی‌تواند خالی باشد")
                    return False

                await app.check_password(password)
                print("✅ احراز هویت دو مرحله‌ای موفق")

            # تأیید نهایی لاگین
            me = await app.get_me()
            print(f"🎉 لاگین موفقیت‌آمیز!")
            print(f"👤 نام: {me.first_name} {me.last_name or ''}")
            print(f"🏷️ نام کاربری: @{me.username}")
            print(f"📞 شماره: {me.phone_number}")
            print(f"🆔 User ID: {me.id}")
            print(f"✅ Session ذخیره شد در: my_bot1.session")

            return True

        except PhoneCodeInvalid:
            print("❌ کد تأیید نامعتبر است")
            return False
        except PhoneNumberInvalid:
            print("❌ شماره تلفن نامعتبر است")
            return False
        except Exception as e:
            print(f"❌ خطا در لاگین: {e}")
            return False

    except Exception as e:
        print(f"❌ خطا در اتصال: {e}")
        return False
    finally:
        await app.disconnect()

# تابع اتصال به دیتابیس با جداول کامل
def init_db():
    conn = sqlite3.connect('bot1_data.db')
    cursor = conn.cursor()

    # جدول فحش‌ها با پشتیبانی رسانه
    cursor.execute('''CREATE TABLE IF NOT EXISTS fosh_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fosh TEXT,
        media_type TEXT,
        file_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # جدول دشمنان
    cursor.execute('''CREATE TABLE IF NOT EXISTS enemy_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        first_name TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # جدول دوستان
    cursor.execute('''CREATE TABLE IF NOT EXISTS friend_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        first_name TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # جدول کلمات دوستانه با پشتیبانی رسانه
    cursor.execute('''CREATE TABLE IF NOT EXISTS friend_words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT,
        media_type TEXT,
        file_id TEXT,
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
    conn = sqlite3.connect('bot1_data.db')
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
    conn = sqlite3.connect('bot1_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fosh_list WHERE fosh = ?", (fosh,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_fosh_list():
    conn = sqlite3.connect('bot1_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT fosh, media_type, file_id FROM fosh_list")
    result = cursor.fetchall()
    conn.close()
    return result

def clear_fosh_list():
    conn = sqlite3.connect('bot1_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fosh_list")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

# توابع مدیریت دشمنان
def add_enemy(user_id, username=None, first_name=None):
    conn = sqlite3.connect('bot1_data.db')
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
    conn = sqlite3.connect('bot1_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM enemy_list WHERE user_id = ?", (user_id,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_enemy_list():
    conn = sqlite3.connect('bot1_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, first_name, created_at FROM enemy_list")
    result = cursor.fetchall()
    conn.close()
    return result

def clear_enemy_list():
    conn = sqlite3.connect('bot1_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM enemy_list")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

# توابع مدیریت دوستان
def add_friend(user_id, username=None, first_name=None):
    conn = sqlite3.connect('bot1_data.db')
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
    conn = sqlite3.connect('bot1_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM friend_list WHERE user_id = ?", (user_id,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_friend_list():
    conn = sqlite3.connect('bot1_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, first_name, created_at FROM friend_list")
    result = cursor.fetchall()
    conn.close()
    return result

def clear_friend_list():
    conn = sqlite3.connect('bot1_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM friend_list")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

# توابع مدیریت کلمات دوستانه
def add_friend_word(word=None, media_type=None, file_id=None):
    conn = sqlite3.connect('bot1_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO friend_words (word, media_type, file_id) VALUES (?, ?, ?)", 
                      (word, media_type, file_id))
        conn.commit()
        result = True
    except Exception as e:
        logger.error(f"خطا در اضافه کردن کلمه: {e}")
        result = False
    conn.close()
    return result

def remove_friend_word(word):
    conn = sqlite3.connect('bot1_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM friend_words WHERE word = ?", (word,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_friend_words():
    conn = sqlite3.connect('bot1_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT word, media_type, file_id FROM friend_words")
    result = cursor.fetchall()
    conn.close()
    return result

def clear_friend_words():
    conn = sqlite3.connect('bot1_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM friend_words")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

# سایر توابع پایگاه داده
def log_action(action_type, user_id=None, details=None):
    conn = sqlite3.connect('bot1_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO action_log (action_type, user_id, details) VALUES (?, ?, ?)", 
                  (action_type, user_id, details))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect('bot1_data.db')
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

# کامند لاگین
@app.on_message(filters.command("login") & filters.user(admin_id))
async def login_command(client, message: Message):
    await message.edit_text("🔐 شروع فرآیند لاگین مجدد...")
    await app.stop()
    success = await login_user()
    if success:
        await app.start()
        await message.edit_text("✅ لاگین موفقیت‌آمیز! بات مجدداً راه‌اندازی شد.")
    else:
        await message.edit_text("❌ لاگین ناموفق. لطفاً دوباره تلاش کنید.")

# کامند شروع
@app.on_message(filters.command("start") & filters.user(admin_id))
async def start_command(client, message: Message):
    await message.edit_text(f"🤖 **ربات 1 آماده است!**\n\n📋 برای مشاهده کامندها: `/help`\n🆔 Admin: `{admin_id}`")

# کامند اضافه کردن فحش (تمام انواع رسانه)
@app.on_message(filters.command("addfosh") & filters.user(admin_id))
async def add_fosh_command(client, message: Message):
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
                if add_fosh(fosh_text, media_type, file_id):
                    await message.edit_text(f"✅ فحش جدید اضافه شد ({media_type or 'متن'})")
                    log_action("add_fosh", admin_id, f"{media_type or fosh_text}")
                else:
                    await message.edit_text("❌ خطا در اضافه کردن فحش")
            else:
                await message.edit_text("⚠️ نوع رسانه پشتیبانی نمی‌شود")
        else:
            if len(message.command) < 2:
                await message.edit_text("⚠️ لطفاً یک فحش وارد کنید یا روی پیام ریپلای کنید.\n💡 استفاده: `/addfosh متن فحش`")
                return

            fosh = " ".join(message.command[1:])
            if add_fosh(fosh):
                await message.edit_text(f"✅ فحش جدید اضافه شد:\n`{fosh}`")
                log_action("add_fosh", admin_id, fosh[:50])
            else:
                await message.edit_text("❌ خطا در اضافه کردن فحش")

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

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
        else:
            await message.edit_text(f"⚠️ این فحش در لیست یافت نشد:\n`{fosh}`")

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.command("listfosh") & filters.user(admin_id))
async def list_fosh_command(client, message: Message):
    try:
        fosh_list = get_fosh_list()
        if not fosh_list:
            await message.edit_text("📝 لیست فحش‌ها خالی است.\n💡 با `/addfosh` فحش اضافه کنید.")
            return

        text = "🔥 **لیست فحش‌ها:**\n\n"
        for i, (fosh, media_type, file_id) in enumerate(fosh_list, 1):
            if media_type:
                text += f"`{i}.` [{media_type.upper()}]\n"
            else:
                text += f"`{i}.` {fosh}\n"

            if i >= 20:
                text += f"\n... و {len(fosh_list) - 20} مورد دیگر"
                break

        text += f"\n📊 **تعداد کل:** {len(fosh_list)} فحش"
        await message.edit_text(text)

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.command("clearfosh") & filters.user(admin_id))
async def clear_fosh_command(client, message: Message):
    try:
        count = clear_fosh_list()
        await message.edit_text(f"✅ تمام فحش‌ها حذف شدند.\n📊 تعداد حذف شده: {count} مورد")
        log_action("clear_fosh", admin_id, f"حذف {count} فحش")
    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

# کامندهای دشمنان
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
        else:
            await message.edit_text(f"⚠️ این کاربر قبلاً در لیست دشمنان است")

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.command("delenemy") & filters.user(admin_id) & filters.reply)
async def del_enemy_command(client, message: Message):
    try:
        replied = message.reply_to_message
        user_id = replied.from_user.id
        first_name = replied.from_user.first_name

        if remove_enemy(user_id):
            await message.edit_text(f"✅ کاربر از لیست دشمنان حذف شد:\n**نام:** {first_name}")
            log_action("del_enemy", user_id, f"{first_name}")
        else:
            await message.edit_text(f"⚠️ این کاربر در لیست دشمنان یافت نشد")

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.command("listenemy") & filters.user(admin_id))
async def list_enemy_command(client, message: Message):
    try:
        enemy_list = get_enemy_list()
        if not enemy_list:
            await message.edit_text("📝 لیست دشمنان خالی است.")
            return

        text = "👹 **لیست دشمنان:**\n\n"
        for i, (user_id, username, first_name, created_at) in enumerate(enemy_list, 1):
            text += f"`{i}.` {first_name or 'نامشخص'} (`{user_id}`)\n"
            if i >= 20:
                text += f"... و {len(enemy_list) - 20} نفر دیگر\n"
                break

        text += f"\n📊 **تعداد کل:** {len(enemy_list)} دشمن"
        await message.edit_text(text)

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.command("clearenemy") & filters.user(admin_id))
async def clear_enemy_command(client, message: Message):
    try:
        count = clear_enemy_list()
        await message.edit_text(f"✅ تمام دشمنان حذف شدند.\n📊 تعداد حذف شده: {count} نفر")
        log_action("clear_enemy", admin_id, f"حذف {count} دشمن")
    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

# کامندهای دوستان
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
        else:
            await message.edit_text(f"⚠️ این کاربر قبلاً در لیست دوستان است")

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.command("delfriend") & filters.user(admin_id) & filters.reply)
async def del_friend_command(client, message: Message):
    try:
        replied = message.reply_to_message
        user_id = replied.from_user.id
        first_name = replied.from_user.first_name

        if remove_friend(user_id):
            await message.edit_text(f"✅ کاربر از لیست دوستان حذف شد:\n**نام:** {first_name}")
            log_action("del_friend", user_id, f"{first_name}")
        else:
            await message.edit_text(f"⚠️ این کاربر در لیست دوستان یافت نشد")

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.command("listfriend") & filters.user(admin_id))
async def list_friend_command(client, message: Message):
    try:
        friend_list = get_friend_list()
        if not friend_list:
            await message.edit_text("📝 لیست دوستان خالی است.")
            return

        text = "😊 **لیست دوستان:**\n\n"
        for i, (user_id, username, first_name, created_at) in enumerate(friend_list, 1):
            text += f"`{i}.` {first_name or 'نامشخص'} (`{user_id}`)\n"
            if i >= 20:
                text += f"... و {len(friend_list) - 20} نفر دیگر\n"
                break

        text += f"\n📊 **تعداد کل:** {len(friend_list)} دوست"
        await message.edit_text(text)

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.command("clearfriend") & filters.user(admin_id))
async def clear_friend_command(client, message: Message):
    try:
        count = clear_friend_list()
        await message.edit_text(f"✅ تمام دوستان حذف شدند.\n📊 تعداد حذف شده: {count} نفر")
        log_action("clear_friend", admin_id, f"حذف {count} دوست")
    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

# کامند اضافه کردن کلمه دوستانه (تمام انواع رسانه)
@app.on_message(filters.command("addword") & filters.user(admin_id))
async def add_word_command(client, message: Message):
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
                if add_friend_word(word_text, media_type, file_id):
                    await message.edit_text(f"✅ کلمه دوستانه اضافه شد ({media_type or 'متن'})")
                    log_action("add_word", admin_id, f"{media_type or word_text}")
                else:
                    await message.edit_text("❌ خطا در اضافه کردن کلمه")
            else:
                await message.edit_text("⚠️ نوع رسانه پشتیبانی نمی‌شود")
        else:
            if len(message.command) < 2:
                await message.edit_text("⚠️ لطفاً یک کلمه وارد کنید یا روی پیام ریپلای کنید.\n💡 استفاده: `/addword سلام دوست عزیز`")
                return

            word = " ".join(message.command[1:])
            if add_friend_word(word):
                await message.edit_text(f"✅ کلمه دوستانه اضافه شد:\n`{word}`")
                log_action("add_word", admin_id, word[:50])
            else:
                await message.edit_text("❌ خطا در اضافه کردن کلمه")

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

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
        else:
            await message.edit_text(f"⚠️ این کلمه در لیست یافت نشد:\n`{word}`")

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.command("listword") & filters.user(admin_id))
async def list_word_command(client, message: Message):
    try:
        word_list = get_friend_words()
        if not word_list:
            await message.edit_text("📝 لیست کلمات دوستانه خالی است.\n💡 با `/addword` کلمه اضافه کنید.")
            return

        text = "💬 **لیست کلمات دوستانه:**\n\n"
        for i, (word, media_type, file_id) in enumerate(word_list, 1):
            if media_type:
                text += f"`{i}.` [{media_type.upper()}]\n"
            else:
                text += f"`{i}.` {word}\n"

            if i >= 20:
                text += f"\n... و {len(word_list) - 20} مورد دیگر"
                break

        text += f"\n📊 **تعداد کل:** {len(word_list)} کلمه"
        await message.edit_text(text)

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.command("clearword") & filters.user(admin_id))
async def clear_word_command(client, message: Message):
    try:
        count = clear_friend_words()
        await message.edit_text(f"✅ تمام کلمات دوستانه حذف شدند.\n📊 تعداد حذف شده: {count} مورد")
        log_action("clear_word", admin_id, f"حذف {count} کلمه")
    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

# کامند آمار
@app.on_message(filters.command("stats") & filters.user(admin_id))
async def stats_command(client, message: Message):
    try:
        stats = get_stats()

        text = "📊 **آمار کامل ربات 1:**\n\n"
        text += f"🔥 فحش‌ها: `{stats['fosh_count']}` عدد\n"
        text += f"👹 دشمنان: `{stats['enemy_count']}` نفر\n"
        text += f"😊 دوستان: `{stats['friend_count']}` نفر\n"
        text += f"💬 کلمات دوستانه: `{stats['word_count']}` عدد\n\n"
        text += f"🤖 **وضعیت پاسخگویی:** {'فعال ✅' if auto_reply_enabled else 'غیرفعال ❌'}\n"
        text += f"⏰ **آخرین بروزرسانی:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        await message.edit_text(text)
        log_action("stats_view", admin_id, "نمایش آمار")

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

# کامند فعال/غیرفعال پاسخگویی
@app.on_message(filters.command(["autoreply", "toggle", "runself"]) & filters.user(admin_id))
async def toggle_auto_reply(client, message: Message):
    global auto_reply_enabled
    try:
        auto_reply_enabled = True
        await message.edit_text("🤖 **پاسخگویی خودکار فعال شد ✅**")
        log_action("toggle_auto_reply", admin_id, "فعال")

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.command("offself") & filters.user(admin_id))
async def off_auto_reply(client, message: Message):
    global auto_reply_enabled
    try:
        auto_reply_enabled = False
        await message.edit_text("🤖 **پاسخگویی خودکار غیرفعال شد ❌**")
        log_action("toggle_auto_reply", admin_id, "غیرفعال")

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

# کامند اکو (تکرار دقیق پیام)
@app.on_message(filters.command("echo") & filters.user(admin_id))
async def echo_command(client, message: Message):
    """کامند اکو - تکرار دقیق پیام کاربر"""
    try:
        set_echo_active(True)  # فعال کردن حالت اکو
        
        if message.reply_to_message:
            # اگر روی پیامی ریپلای شده، آن پیام را اکو کن
            original_msg = message.reply_to_message
            
            # حذف پیام کامند اکو
            await message.delete()
            
            # اکو کردن پیام اصلی
            if original_msg.text:
                await client.send_message(
                    message.chat.id, 
                    original_msg.text,
                    reply_to_message_id=original_msg.reply_to_message_id if original_msg.reply_to_message else None
                )
            elif original_msg.photo:
                await client.send_photo(
                    message.chat.id,
                    original_msg.photo.file_id,
                    caption=original_msg.caption,
                    reply_to_message_id=original_msg.reply_to_message_id if original_msg.reply_to_message else None
                )
            elif original_msg.video:
                await client.send_video(
                    message.chat.id,
                    original_msg.video.file_id,
                    caption=original_msg.caption,
                    reply_to_message_id=original_msg.reply_to_message_id if original_msg.reply_to_message else None
                )
            elif original_msg.animation:
                await client.send_animation(
                    message.chat.id,
                    original_msg.animation.file_id,
                    caption=original_msg.caption,
                    reply_to_message_id=original_msg.reply_to_message_id if original_msg.reply_to_message else None
                )
            elif original_msg.sticker:
                await client.send_sticker(
                    message.chat.id,
                    original_msg.sticker.file_id,
                    reply_to_message_id=original_msg.reply_to_message_id if original_msg.reply_to_message else None
                )
            elif original_msg.audio:
                await client.send_audio(
                    message.chat.id,
                    original_msg.audio.file_id,
                    caption=original_msg.caption,
                    reply_to_message_id=original_msg.reply_to_message_id if original_msg.reply_to_message else None
                )
            elif original_msg.voice:
                await client.send_voice(
                    message.chat.id,
                    original_msg.voice.file_id,
                    caption=original_msg.caption,
                    reply_to_message_id=original_msg.reply_to_message_id if original_msg.reply_to_message else None
                )
            elif original_msg.video_note:
                await client.send_video_note(
                    message.chat.id,
                    original_msg.video_note.file_id,
                    reply_to_message_id=original_msg.reply_to_message_id if original_msg.reply_to_message else None
                )
            elif original_msg.document:
                await client.send_document(
                    message.chat.id,
                    original_msg.document.file_id,
                    caption=original_msg.caption,
                    reply_to_message_id=original_msg.reply_to_message_id if original_msg.reply_to_message else None
                )
            
            log_action("echo", admin_id, f"اکو پیام در {message.chat.title}")
            
        else:
            # اگر ریپلای نشده، متن بعد از کامند را اکو کن
            if len(message.command) > 1:
                echo_text = " ".join(message.command[1:])
                await message.edit_text(echo_text)
                log_action("echo", admin_id, f"اکو متن: {echo_text[:50]}")
            else:
                await message.edit_text("⚠️ لطفاً روی پیامی ریپلای کنید یا متنی وارد کنید.\n💡 استفاده: `/echo متن` یا ریپلای `/echo`")
        
        # تاخیر کوتاه برای اطمینان از اتمام عملیات اکو
        await asyncio.sleep(0.5)
        set_echo_active(False)  # غیرفعال کردن حالت اکو

    except Exception as e:
        set_echo_active(False)
        await message.edit_text(f"❌ خطا در اکو: {str(e)}")
        logger.error(f"خطا در echo_command: {e}")

# کامند ارسال همگانی
@app.on_message(filters.command("broadcast") & filters.user(admin_id))
async def broadcast_command(client, message: Message):
    try:
        if len(message.command) < 2 and not message.reply_to_message:
            await message.edit_text("⚠️ لطفاً پیام مورد نظر را وارد کنید یا روی پیام ریپلای کنید.\n💡 استفاده: `/broadcast سلام به همه`")
            return

        if message.reply_to_message:
            target_message = message.reply_to_message
        else:
            text = " ".join(message.command[1:])

        await message.edit_text("📤 شروع ارسال همگانی...")

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

        result_text = f"✅ **ارسال همگانی تکمیل شد:**\n\n"
        result_text += f"📤 **موفق:** {success} گروه\n"
        result_text += f"❌ **ناموفق:** {fail} گروه\n"
        result_text += f"📊 **کل:** {success + fail} گروه"

        await message.edit_text(result_text)
        log_action("broadcast", admin_id, f"موفق:{success}, ناموفق:{fail}")

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

# کش بهینه‌شده برای سرعت فوق‌العاده
enemy_cache = set()
friend_cache = set()
fosh_cache = []
word_cache = []
last_cache_update = 0

async def update_cache_async():
    """بروزرسانی async کش برای سرعت بیشتر"""
    global enemy_cache, friend_cache, fosh_cache, word_cache, last_cache_update
    try:
        # اجرای همزمان تمام عملیات دیتابیس
        tasks = [
            asyncio.create_task(asyncio.to_thread(get_enemy_list)),
            asyncio.create_task(asyncio.to_thread(get_friend_list)),
            asyncio.create_task(asyncio.to_thread(get_fosh_list)),
            asyncio.create_task(asyncio.to_thread(get_friend_words))
        ]
        
        enemy_list, friend_list, fosh_list, word_list = await asyncio.gather(*tasks)
        
        enemy_cache = {row[0] for row in enemy_list}
        friend_cache = {row[0] for row in friend_list}
        fosh_cache = fosh_list
        word_cache = word_list
        
        last_cache_update = datetime.now().timestamp()
    except:
        pass

# تابع ارسال فوری پاسخ
async def send_instant_reply(message, selected_content):
    """ارسال فوری بدون تاخیر"""
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

# پاسخگویی فوری بدون تاخیر
@app.on_message(
    ~filters.me & 
    ~filters.channel & 
    ~filters.user(admin_id) &
    ~filters.service &
    filters.group
)
async def auto_reply_handler(client, message: Message):
    """هندلر فوری پاسخگویی"""
    
    # اگر حالت اکو فعال است، هیچ پاسخی نده
    if is_echo_active():
        return
        
    if not auto_reply_enabled or not message.from_user:
        return

    user_id = message.from_user.id
    
    # بررسی فوری دشمن بودن - بات 1 بدون تاخیر
    if user_id in enemy_cache and fosh_cache:
        selected = choice(fosh_cache)
        asyncio.create_task(send_instant_reply(message, selected))
        return

    # بررسی فوری دوست بودن - بات 1 بدون تاخیر
    if user_id in friend_cache and word_cache:
        selected = choice(word_cache)
        asyncio.create_task(send_instant_reply(message, selected))

# تسک پس‌زمینه برای بروزرسانی کش
async def cache_updater():
    """بروزرسانی خودکار کش هر 10 ثانیه"""
    while True:
        await update_cache_async()
        await asyncio.sleep(10)

# راهنما
@app.on_message(filters.command("help") & filters.user(admin_id))
async def help_command(client, message: Message):
    try:
        text = """🤖 **راهنمای ربات 1 - نسخه پیشرفته**

🔐 **مدیریت Session:**
• `/login` - لاگین مجدد و ایجاد session جدید
• `/start` - شروع ربات

🔥 **مدیریت فحش‌ها:**
• `/addfosh [متن]` - اضافه کردن فحش
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
• `/delword [متن]` - حذف کلمه مشخص از بانک
• `/listword` - مشاهده تمام پیام‌های دوستانه
• `/clearword` - حذف کامل بانک

📢 **سیستم ارسال همگانی:**
• `/broadcast [پیام]` - ارسال همگانی متن به تمام گروه‌ها
• پشتیبانی از ارسال رسانه با ریپلای در broadcast
  └ شامل گزارش دقیق موفقیت/ناموفقی
  └ مدیریت خطای Flood + تاخیر هوشمند
  └ فقط گروه‌ها (نه چت خصوصی/کانال)

🤖 **تنظیمات سیستم:**
• `/runself` - فعال کردن پاسخگویی خودکار
• `/offself` - غیرفعال کردن پاسخگویی
• `/stats` - نمایش آمار کامل سیستم
• `/start` - راه‌اندازی مجدد ربات
• `/help` - نمایش این راهنما

🔊 **قابلیت اکو:**
• `/echo [متن]` - تکرار دقیق متن (ریپلای یا متنی)
  └ حین اکو، سایر بات‌ها واکنش نشان نمی‌دهند
  └ پشتیبانی کامل از تمام انواع رسانه و ریپلای

💡 **نکات مهم:**
• از ریپلای برای اضافه کردن رسانه استفاده کنید
• پشتیبانی کامل از عکس، ویدیو، صوت، استیکر، گیف و...
• پاسخگویی فوری و بدون تاخیر در گروه‌ها
• سیستم لاگ کامل برای تمام عملیات
• امکان بکاپ و بازیابی اطلاعات"""

        await message.edit_text(text)

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

async def bot_ready():
    """راه‌اندازی کش و تسک‌های پس‌زمینه پس از شروع بات"""
    asyncio.create_task(update_cache_async())
    asyncio.create_task(cache_updater())
    logger.info("ربات 1 آماده شد و کش راه‌اندازی شد!")

async def main():
    """تابع اصلی راه‌اندازی"""
    print("🚀 شروع ربات 1...")

    # بررسی وجود session
    if not os.path.exists("my_bot1.session"):
        print("📱 Session یافت نشد. شروع فرآیند لاگین...")
        success = await login_user()
        if not success:
            print("❌ لاگین ناموفق. خروج...")
            return

    # راه‌اندازی ربات
    print("✅ شروع ربات...")
    await app.start()

if __name__ == "__main__":
    asyncio.run(main())