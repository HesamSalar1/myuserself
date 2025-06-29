#!/usr/bin/env python3
"""
تست سیستم جداسازی چت‌ها
بررسی اینکه ایموجی ممنوعه در یک چت روی چت‌های دیگر تأثیر نگذارد
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
        self.title = f"Test Group {chat_id}"

class MockClient:
    def __init__(self):
        pass
    
    async def send_message(self, chat_id, text, reply_to_message_id=None):
        # شبیه‌سازی ارسال پیام
        pass

async def test_per_chat_isolation():
    """تست جداسازی چت‌ها"""
    print("🔍 تست سیستم جداسازی چت‌ها...")
    
    launcher = UnifiedBotLauncher()
    
    # تنظیم ایموجی‌های ممنوعه و دشمن
    launcher.forbidden_emojis.add("⚡")
    
    enemy_id = 999888777
    bot_id = 1
    chat1_id = -1001111111111  # چت اول
    chat2_id = -1002222222222  # چت دوم
    
    # اضافه کردن دشمن و فحش به دیتابیس
    launcher.add_enemy(bot_id, enemy_id, "TestEnemy", "Enemy")
    launcher.add_fosh(bot_id, "فحش تستی")
    
    client = MockClient()
    
    print(f"📝 تنظیمات:")
    print(f"   • دشمن: {enemy_id}")
    print(f"   • چت اول: {chat1_id}")
    print(f"   • چت دوم: {chat2_id}")
    print(f"   • ایموجی ممنوعه: ⚡")
    
    # مرحله 1: شروع فحش در هر دو چت
    print("\n🔥 مرحله 1: شروع فحش در هر دو چت...")
    
    # دشمن پیام در چت اول می‌فرستد
    enemy_message1 = MockMessage(text="سلام چت 1", user_id=enemy_id, chat_id=chat1_id)
    enemy_list = launcher.get_enemy_list(bot_id)
    enemy_ids = {row[0] for row in enemy_list}
    
    if enemy_id in enemy_ids:
        fosh_list = launcher.get_fosh_list(bot_id)
        if fosh_list:
            spam_key1 = f"{bot_id}_{enemy_id}_{chat1_id}"
            
            async def mock_spam_task1():
                await asyncio.sleep(10)
            
            task1 = asyncio.create_task(mock_spam_task1())
            launcher.continuous_spam_tasks[spam_key1] = task1
            print(f"✅ تسک فحش در چت {chat1_id} شروع شد")
    
    # دشمن پیام در چت دوم می‌فرستد
    enemy_message2 = MockMessage(text="سلام چت 2", user_id=enemy_id, chat_id=chat2_id)
    if enemy_id in enemy_ids:
        if fosh_list:
            spam_key2 = f"{bot_id}_{enemy_id}_{chat2_id}"
            
            async def mock_spam_task2():
                await asyncio.sleep(10)
            
            task2 = asyncio.create_task(mock_spam_task2())
            launcher.continuous_spam_tasks[spam_key2] = task2
            print(f"✅ تسک فحش در چت {chat2_id} شروع شد")
    
    print(f"📊 تسک‌های فعال: {len(launcher.continuous_spam_tasks)}")
    assert len(launcher.continuous_spam_tasks) == 2, "باید دو تسک فعال باشد"
    
    # مرحله 2: ایموجی ممنوعه فقط در چت اول
    print(f"\n⚡ مرحله 2: ایموجی ممنوعه فقط در چت {chat1_id}...")
    stop_message = MockMessage(text="توقف ⚡ کن", user_id=888777666, chat_id=chat1_id)
    
    # تشخیص ایموجی و توقف فقط چت اول
    should_stop = launcher.should_pause_spam(stop_message, bot_id)
    if should_stop:
        print(f"✅ ایموجی ممنوعه در چت {chat1_id} تشخیص داده شد")
        print(f"🚨 توقف اضطراری فقط برای چت {chat1_id} فعال شد")
    
    # انتظار تا پردازش
    await asyncio.sleep(1)
    
    # بررسی وضعیت
    chat1_stopped = chat1_id in launcher.chat_emergency_stops and launcher.chat_emergency_stops[chat1_id].is_set()
    chat2_stopped = chat2_id in launcher.chat_emergency_stops and launcher.chat_emergency_stops[chat2_id].is_set()
    
    print(f"📊 وضعیت توقف:")
    print(f"   • چت {chat1_id}: {'متوقف' if chat1_stopped else 'فعال'}")
    print(f"   • چت {chat2_id}: {'متوقف' if chat2_stopped else 'فعال'}")
    
    # بررسی تسک‌ها
    remaining_tasks = len([k for k in launcher.continuous_spam_tasks.keys() if not launcher.continuous_spam_tasks[k].cancelled()])
    print(f"📊 تسک‌های باقی‌مانده: {remaining_tasks}")
    
    # مرحله 3: بررسی جداسازی
    print(f"\n🧪 مرحله 3: بررسی جداسازی...")
    
    if chat1_stopped and not chat2_stopped:
        print("✅ جداسازی چت‌ها موفقیت‌آمیز:")
        print(f"   • چت {chat1_id} متوقف شد")
        print(f"   • چت {chat2_id} همچنان فعال است")
        success = True
    else:
        print("❌ جداسازی چت‌ها ناموفق:")
        if not chat1_stopped:
            print(f"   • چت {chat1_id} باید متوقف می‌شد")
        if chat2_stopped:
            print(f"   • چت {chat2_id} نباید متوقف می‌شد")
        success = False
    
    # پاکسازی
    for task in launcher.continuous_spam_tasks.values():
        task.cancel()
    launcher.chat_emergency_stops.clear()
    
    return success

async def main():
    """تابع اصلی تست"""
    print("=" * 60)
    print("🧪 تست جداسازی چت‌ها")
    print("=" * 60)
    
    success = await test_per_chat_isolation()
    
    if success:
        print("\n✅ تست موفقیت‌آمیز بود!")
        print("🔒 سیستم به درستی:")
        print("   • هر چت را مجزا مدیریت می‌کند")
        print("   • ایموجی ممنوعه فقط چت جاری را متوقف می‌کند")
        print("   • چت‌های دیگر بدون تأثیر ادامه می‌دهند")
    else:
        print("\n❌ تست ناموفق")
        print("⚠️  نیاز به بررسی سیستم جداسازی")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())