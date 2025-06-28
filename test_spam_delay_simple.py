#!/usr/bin/env python3
"""
تست ساده سیستم تنظیم تاخیر فحش
"""

from unified_bot_launcher import UnifiedBotLauncher

def test_spam_delay_setup():
    """تست راه‌اندازی سیستم تاخیر فحش"""
    print("🔍 راه‌اندازی و تست سیستم تاخیر فحش...")
    
    # ایجاد لانچر
    launcher = UnifiedBotLauncher()
    
    # تست برای بات 1
    bot_id = 1
    print(f"\n📊 تست بات {bot_id}:")
    
    # راه‌اندازی دیتابیس
    try:
        launcher.setup_database(bot_id, launcher.bot_configs[bot_id]['db_path'])
        print("  ✅ دیتابیس راه‌اندازی شد")
    except Exception as e:
        print(f"  ❌ خطا در راه‌اندازی دیتابیس: {e}")
        return
    
    # دریافت تاخیر پیش‌فرض
    default_delay = launcher.get_spam_delay(bot_id)
    print(f"  🕒 تاخیر پیش‌فرض: {default_delay} ثانیه")
    
    # تست تنظیم تاخیرهای مختلف
    test_delays = [0.5, 1.0, 2.5, 10.0]
    
    for delay in test_delays:
        success, msg = launcher.set_spam_delay(bot_id, delay)
        if success:
            saved_delay = launcher.get_spam_delay(bot_id)
            print(f"  ✅ تنظیم {delay}s: موفق - ذخیره شده: {saved_delay}s")
        else:
            print(f"  ❌ تنظیم {delay}s: ناموفق - {msg}")
    
    # تست تاخیر منفی
    success, msg = launcher.set_spam_delay(bot_id, -1.0)
    print(f"  {'✅' if not success else '❌'} تاخیر منفی: {msg}")
    
    # تست مقدار نامعتبر
    success, msg = launcher.set_spam_delay(bot_id, "invalid")
    print(f"  {'✅' if not success else '❌'} مقدار نامعتبر: {msg}")
    
    print("\n✅ تست کامل شد!")

if __name__ == "__main__":
    test_spam_delay_setup()