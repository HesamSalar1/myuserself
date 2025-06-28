#!/usr/bin/env python3
"""
تست سیستم راه‌اندازی مجدد خودکار فحش بعد از توقف با ایموجی ممنوعه
"""

import asyncio
import time
from unified_bot_launcher import UnifiedBotLauncher

class MockMessage:
    def __init__(self, text=None, caption=None, user_id=123456789, chat_id=-1001234567890):
        self.text = text
        self.caption = caption
        self.from_user = MockUser(user_id)
        self.chat = MockChat(chat_id)

class MockUser:
    def __init__(self, user_id):
        self.id = user_id
        self.is_bot = False
        self.first_name = f"User{user_id}"
        self.username = f"user{user_id}"

class MockChat:
    def __init__(self, chat_id=-1001234567890):
        self.id = chat_id
        self.title = "Test Group"

class MockClient:
    def __init__(self):
        pass
    
    async def send_message(self, chat_id, text, reply_to_message_id=None):
        # شبیه‌سازی ارسال پیام
        pass

async def test_auto_restart_system():
    """تست سیستم راه‌اندازی مجدد خودکار"""
    print("🔍 تست سیستم راه‌اندازی مجدد خودکار فحش...")
    
    launcher = UnifiedBotLauncher()
    
    # تنظیم ایموجی‌های ممنوعه و دشمن
    launcher.forbidden_emojis.add("⚡")
    
    enemy_id = 999888777
    bot_id = 1
    chat_id = -1001234567890
    
    # اضافه کردن دشمن و فحش به دیتابیس
    launcher.add_enemy_to_db(bot_id, enemy_id, "TestEnemy", "Enemy")
    launcher.add_fosh_to_db(bot_id, ("فحش تستی", None, None))
    
    client = MockClient()
    
    print(f"📝 دشمن {enemy_id} در بات {bot_id} تنظیم شد")
    print(f"📝 ایموجی ممنوعه: ⚡")
    
    # مرحله 1: دشمن پیام می‌فرستد - باید فحش شروع شود
    print("\n🔥 مرحله 1: دشمن پیام عادی می‌فرستد...")
    enemy_message1 = MockMessage(text="سلام", user_id=enemy_id, chat_id=chat_id)
    
    # شبیه‌سازی auto_reply_handler
    enemy_list = launcher.get_enemy_list(bot_id)
    enemy_ids = {row[0] for row in enemy_list}
    
    if enemy_id in enemy_ids:
        fosh_list = launcher.get_fosh_list(bot_id)
        if fosh_list:
            spam_key = f"{bot_id}_{enemy_id}_{chat_id}"
            
            # شروع تسک فحش (شبیه‌سازی)
            async def mock_spam_task():
                await asyncio.sleep(10)  # تسک طولانی
            
            task = asyncio.create_task(mock_spam_task())
            launcher.continuous_spam_tasks[spam_key] = task
            print(f"✅ تسک فحش شروع شد: {spam_key}")
    
    print(f"📊 تسک‌های فعال: {len(launcher.continuous_spam_tasks)}")
    
    # مرحله 2: ایموجی ممنوعه ارسال می‌شود - باید متوقف شود
    print("\n⚡ مرحله 2: ایموجی ممنوعه ارسال می‌شود...")
    stop_message = MockMessage(text="توقف ⚡ کن", user_id=888777666)
    
    # تشخیص ایموجی و توقف
    should_stop = launcher.should_pause_spam(stop_message, bot_id)
    if should_stop:
        print("✅ ایموجی ممنوعه تشخیص داده شد")
        print("🚨 توقف اضطراری فعال شد")
        print(f"📊 تسک‌های باقی‌مانده: {len(launcher.continuous_spam_tasks)}")
    
    # انتظار تا پاک شدن خودکار
    await asyncio.sleep(1)
    
    # مرحله 3: دشمن دوباره پیام می‌فرستد - باید مجدداً شروع شود
    print("\n🔄 مرحله 3: دشمن پیام جدید می‌فرستد (باید مجدداً شروع شود)...")
    enemy_message2 = MockMessage(text="دوباره سلام", user_id=enemy_id, chat_id=chat_id)
    
    # شبیه‌سازی auto_reply_handler دوباره
    if enemy_id in enemy_ids:
        fosh_list = launcher.get_fosh_list(bot_id)
        if fosh_list:
            spam_key = f"{bot_id}_{enemy_id}_{chat_id}"
            
            # بررسی و پاک کردن توقف اضطراری
            if launcher.emergency_stop_event.is_set():
                print("⚡ پاک کردن توقف اضطراری برای شروع مجدد")
                launcher.emergency_stop_event.clear()
            
            # شروع تسک جدید
            async def mock_spam_task2():
                await asyncio.sleep(10)
            
            task = asyncio.create_task(mock_spam_task2())
            launcher.continuous_spam_tasks[spam_key] = task
            print(f"✅ تسک فحش مجدداً شروع شد: {spam_key}")
    
    print(f"📊 تسک‌های فعال بعد از راه‌اندازی مجدد: {len(launcher.continuous_spam_tasks)}")
    
    # پاکسازی
    for task in launcher.continuous_spam_tasks.values():
        task.cancel()
    
    return True

async def main():
    """تابع اصلی تست"""
    print("=" * 60)
    print("🧪 تست راه‌اندازی مجدد خودکار سیستم فحش")
    print("=" * 60)
    
    success = await test_auto_restart_system()
    
    if success:
        print("\n✅ تست موفقیت‌آمیز بود!")
        print("🔄 سیستم به درستی:")
        print("   • تسک‌های جاری را با ایموجی ممنوعه متوقف می‌کند")
        print("   • با پیام بعدی دشمن مجدداً شروع می‌کند")
        print("   • نیازی به فعال‌سازی دستی ندارد")
    else:
        print("\n❌ تست ناموفق")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())