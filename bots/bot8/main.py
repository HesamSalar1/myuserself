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

    cursor.execute('''CREATE TABLE IF NOT EXISTS fosh_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fosh TEXT,
        media_type TEXT,
        file_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.commit()
    conn.close()

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

💡 **نکات:**
• برای لاگین اولیه از کامند `/login` استفاده کنید"""

        await message.edit_text(text)

    except Exception as e:
        await message.edit_text(f"❌ خطا: {str(e)}")

async def main():
    """تابع اصلی راه‌اندازی"""
    print("🚀 شروع ربات 8...")

    # بررسی وجود session
    if not os.path.exists("my_bot8.session"):
        print("📱 Session یافت نشد. شروع فرآیند لاگین...")
        success = await login_user()
        if not success:
            print("❌ لاگین ناموفق. خروج...")
            return

    # راه‌اندازی ربات
    print("✅ شروع ربات...")
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())