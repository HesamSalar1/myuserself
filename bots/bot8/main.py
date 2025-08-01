
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
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# تابع کمکی برای مدیریت امن Unicode
def safe_text_process(text, max_length=100):
    """پردازش امن متن با مدیریت خطاهای Unicode"""
    try:
        if not text:
            return "[بدون متن]"
        
        # تبدیل به string و محدود کردن طول
        safe_text = str(text)
        if len(safe_text) > max_length:
            return safe_text[:max_length] + "..."
        return safe_text
    except (UnicodeError, UnicodeDecodeError, UnicodeEncodeError):
        return "[خطای کدگذاری]"
    except Exception:
        return "[خطای متن]"

from pyrogram import Client, filters
from pyrogram.types import Message, ChatMember
from pyrogram.errors import FloodWait, UserNotParticipant, ChatWriteForbidden, SessionPasswordNeeded, PhoneCodeInvalid, PhoneNumberInvalid

# تنظیمات اصلی بات 8
api_id = 23900003
api_hash = "5f6fb8f1c6d80d264d5eb08af3b038b6"
admin_id = 7220521953

# تنظیم لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot8.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Client(
    "my_bot8", 
    api_id, 
    api_hash,
    workdir="./",
    sleep_threshold=5,
    max_concurrent_transmissions=30
)

# متغیرهای کنترل
auto_reply_enabled = True

async def login_user():
    """سیستم پیشرفته لاگین و دریافت session"""
    try:
        print(f"🔐 شروع فرآیند لاگین برای بات 8...")
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
            print(f"✅ Session ذخیره شد در: my_bot8.session")

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

# تابع اتصال به دیتابیس
def init_db():
    conn = sqlite3.connect('bot8_data.db')
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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        username TEXT,
        first_name TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # جدول دوستان
    cursor.execute('''CREATE TABLE IF NOT EXISTS friend_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        username TEXT,
        first_name TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_fosh_text ON fosh_list(fosh)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_enemy_user_id ON enemy_list(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_friend_user_id ON friend_list(user_id)')

    conn.commit()
    conn.close()

# توابع مدیریت فحش‌ها
def add_fosh(fosh, media_type=None, file_id=None):
    conn = sqlite3.connect('bot8_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO fosh_list (fosh, media_type, file_id) VALUES (?, ?, ?)", 
                      (fosh, media_type, file_id))
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        logger.error(f"خطا در اضافه کردن فحش: فحش تکراری")
        result = False
    except Exception as e:
        logger.error(f"خطا در اضافه کردن فحش: {e}")
        result = False
    conn.close()
    return result

def remove_fosh(fosh):
    conn = sqlite3.connect('bot8_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fosh_list WHERE fosh = ?", (fosh,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_fosh_list():
    conn = sqlite3.connect('bot8_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT fosh, media_type, file_id FROM fosh_list")
    result = cursor.fetchall()
    conn.close()
    return result

def clear_fosh_list():
    conn = sqlite3.connect('bot8_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fosh_list")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

# توابع مدیریت دشمنان
def add_enemy(user_id, username=None, first_name=None):
    conn = sqlite3.connect('bot8_data.db')
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
    conn = sqlite3.connect('bot8_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM enemy_list WHERE user_id = ?", (user_id,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_enemy_list():
    conn = sqlite3.connect('bot8_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, first_name, created_at FROM enemy_list")
    result = cursor.fetchall()
    conn.close()
    return result

def clear_enemy_list():
    conn = sqlite3.connect('bot8_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM enemy_list")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

# توابع مدیریت دوستان
def add_friend(user_id, username=None, first_name=None):
    conn = sqlite3.connect('bot8_data.db')
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
    conn = sqlite3.connect('bot8_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM friend_list WHERE user_id = ?", (user_id,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_friend_list():
    conn = sqlite3.connect('bot8_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, first_name, created_at FROM friend_list")
    result = cursor.fetchall()
    conn.close()
    return result

def clear_friend_list():
    conn = sqlite3.connect('bot8_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM friend_list")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

# کامندهای ربات
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

@app.on_message(filters.command("start") & filters.user(admin_id))
async def start_command(client, message: Message):
    await message.edit_text(f"🤖 **ربات 8 آماده است!**\n\n📋 برای لاگین: `/login`\n🆔 Admin: `{admin_id}`")

@app.on_message(filters.command("help") & filters.user(admin_id))
async def help_command(client, message: Message):
    try:
        text = """🤖 **راهنمای ربات 8 - نسخه پیشرفته**

🔐 **مدیریت Session:**
• `/login` - لاگین مجدد و ایجاد session جدید
• `/start` - شروع ربات

📊 **مدیریت دیتابیس:**
• `/addfosh [متن]` - اضافه کردن فحش
• `/removefosh [متن]` - حذف فحش
• `/foshlist` - لیست فحش‌ها
• `/clearfosh` - پاک کردن همه فحش‌ها

👥 **مدیریت کاربران:**
• `/addenemy [ریپلای]` - اضافه کردن دشمن
• `/removenemy [ریپلای]` - حذف دشمن
• `/enemylist` - لیست دشمنان
• `/clearenemy` - پاک کردن همه دشمنان

💡 **نکات:**
• برای لاگین اولیه از کامند `/login` استفاده کنید"""

        await message.edit_text(text)

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

# شروع برنامه
init_db()

async def main():
    """تابع اصلی راه‌اندازی"""
    print("🚀 شروع ربات 8...")

    try:
        # بررسی وجود session
        if not os.path.exists("my_bot8.session"):
            print("📱 Session یافت نشد. شروع فرآیند لاگین...")
            success = await login_user()
            if not success:
                print("❌ لاگین ناموفق. خروج...")
                return

        # راه‌اندازی ربات
        print("✅ شروع ربات...")
        await app.start()
        print("✅ ربات 8 با موفقیت راه‌اندازی شد!")
        
        # نگه داشتن ربات در حالت فعال
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        print("🛑 متوقف شدن ربات...")
    except Exception as e:
        print(f"❌ خطا در راه‌اندازی ربات: {e}")
    finally:
        if app.is_connected:
            await app.stop()

if __name__ == "__main__":
    try:
        # تلاش برای اجرای مستقیم
        asyncio.run(main())
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            # در صورت وجود event loop فعال، از آن استفاده کنید
            import nest_asyncio
            nest_asyncio.apply()
            asyncio.run(main())
        else:
            raise e
