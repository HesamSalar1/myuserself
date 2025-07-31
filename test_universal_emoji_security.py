#!/usr/bin/env python3
"""
تست امنیت جهانی ایموجی ممنوعه - بررسی اعمال بدون استثنا برای همه کاربران شامل ادمین‌ها
"""

import asyncio
import time
from unified_bot_launcher import UnifiedBotLauncher
import logging

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockMessage:
    """کلاس شبیه‌سازی پیام تلگرام"""
    def __init__(self, text, user_id=123456789, chat_id=-1001234567890, message_id=1, is_admin=False, is_bot=False):
        self.text = text
        self.caption = None
        self.id = message_id
        self.chat = MockChat(chat_id)
        self.from_user = MockUser(user_id, is_admin, is_bot)

class MockChat:
    def __init__(self, chat_id):
        self.id = chat_id
        self.title = f"Test Chat {chat_id}"
        self.type = "group"

class MockUser:
    def __init__(self, user_id, is_admin=False, is_bot=False):
        self.id = user_id
        self.first_name = "Test User"
        self.username = f"testuser{user_id}"
        self.is_bot = is_bot
        # برای شبیه‌سازی اینکه کاربر ادمین است یا نه
        self._is_admin = is_admin

async def test_universal_emoji_security():
    """تست جامع امنیت ایموجی ممنوعه برای همه کاربران"""
    print("🔒 تست امنیت جهانی ایموجی ممنوعه")
    print("=" * 60)
    
    launcher = UnifiedBotLauncher()
    
    # بارگذاری ایموجی‌ها
    launcher.forbidden_emojis = launcher.load_forbidden_emojis_from_db()
    print(f"📥 {len(launcher.forbidden_emojis)} ایموجی ممنوعه بارگذاری شد")
    
    if not launcher.forbidden_emojis:
        print("❌ هیچ ایموجی ممنوعه‌ای یافت نشد!")
        return
    
    # آماده‌سازی ID های ادمین برای تست
    # در تست واقعی، ادمین‌ها با all_admin_ids شناسایی می‌شوند
    launcher.all_admin_ids = {5533325167, 7850529246, 7419698159}  # ادمین‌های نمونه
    
    # تست‌های مختلف
    test_cases = [
        # (متن پیام, user_id, نوع کاربر, باید تشخیص داده شود یا نه)
        ("A CHARACTER HAS SPAWNED IN THE CHAT ⚡", 999999, "کاربر عادی", True),
        ("⚡️ انرژی!", 5533325167, "ادمین", True),  # ادمین اصلی
        ("🔮 پیشگویی", 7850529246, "ادمین", True),  # ادمین بات 1
        ("متن عادی بدون ایموجی", 7419698159, "ادمین", False),  # ادمین بات 2
        ("CHARACTER SPAWNED ⚡ IN CHAT", 111111, "ربات تلگرام", True),
        ("سلام ⚡ چطوری؟", 222222, "کاربر عادی", True),
        ("test 🔮 crystal ball", 5533325167, "ادمین", True),  # ادمین اصلی دوباره
        ("پیام عادی", 333333, "کاربر عادی", False),
    ]
    
    print("\n🧪 تست امنیت جهانی:")
    print("-" * 50)
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, (text, user_id, user_type, should_detect) in enumerate(test_cases, 1):
        print(f"\n{i}. تست: '{text[:30]}...' ({user_type} - ID: {user_id})")
        
        # ایجاد پیام شبیه‌سازی شده با message_id منحصر به فرد
        is_admin = user_id in launcher.all_admin_ids
        is_bot = "ربات" in user_type
        message = MockMessage(text, user_id, message_id=i, is_admin=is_admin, is_bot=is_bot)
        
        # تست تشخیص
        start_time = time.time()
        detected = await launcher.should_pause_spam(message, 1)
        detection_time = (time.time() - start_time) * 1000  # میلی‌ثانیه
        
        # بررسی نتیجه
        if detected == should_detect:
            status = "✅ صحیح"
            success_count += 1
        else:
            status = "❌ نادرست"
        
        expected_text = "تشخیص داده شود" if should_detect else "تشخیص داده نشود"
        actual_text = "تشخیص داده شد" if detected else "تشخیص داده نشد"
        
        print(f"   └ انتظار: {expected_text}")
        print(f"   └ نتیجه: {actual_text} - {status}")
        print(f"   └ زمان: {detection_time:.2f}ms")
        
        # تست ویژه برای ادمین‌ها
        if is_admin and detected:
            print(f"   └ 🚨 SECURITY CONFIRMED: حتی ادمین {user_id} هم تشخیص داده شد - هیچ استثنایی نیست!")
    
    print(f"\n📊 نتیجه کلی:")
    print(f"   ✅ موفق: {success_count}/{total_count}")
    print(f"   📈 درصد موفقیت: {(success_count/total_count)*100:.1f}%")
    
    if success_count == total_count:
        print("\n🎉 تست امنیت جهانی کاملاً موفق!")
        print("🔒 تأیید شد: هیچ کاربری شامل ادمین‌ها استثنا ندارند")
        print("⚡ سیستم امنیت ایموجی ممنوعه برای همه اعمال می‌شود")
    else:
        print(f"\n⚠️ برخی تست‌ها ناموفق - نیاز به بررسی بیشتر")

def test_admin_identification():
    """تست شناسایی ادمین‌ها"""
    print("\n🔍 تست شناسایی ادمین‌ها:")
    print("-" * 30)
    
    launcher = UnifiedBotLauncher()
    launcher.all_admin_ids = {5533325167, 7850529246, 7419698159}
    
    test_ids = [
        (5533325167, True, "ادمین اصلی"),
        (7850529246, True, "ادمین بات 1"), 
        (7419698159, True, "ادمین بات 2"),
        (999999, False, "کاربر عادی"),
        (111111, False, "کاربر عادی"),
    ]
    
    for user_id, is_admin_expected, description in test_ids:
        is_admin_actual = user_id in launcher.all_admin_ids
        status = "✅" if is_admin_actual == is_admin_expected else "❌"
        print(f"   {user_id}: {description} - {status}")

if __name__ == "__main__":
    print("🚀 شروع تست امنیت جهانی ایموجی ممنوعه")
    print("🔒 هدف: تأیید عدم وجود استثنا برای هیچ کاربری شامل ادمین‌ها")
    
    # اجرای تست‌ها
    test_admin_identification()
    asyncio.run(test_universal_emoji_security())
    
    print("\n✅ تست کامل شد!")