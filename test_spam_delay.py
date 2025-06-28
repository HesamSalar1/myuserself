#!/usr/bin/env python3
"""
تست سیستم تنظیم تاخیر فحش
"""

from unified_bot_launcher import UnifiedBotLauncher

def test_spam_delay_system():
    """تست سیستم تنظیمات تاخیر فحش"""
    print("🔍 شروع تست سیستم تاخیر فحش...")
    
    # ایجاد لانچر
    launcher = UnifiedBotLauncher()
    
    # تست برای چند بات
    test_bots = [1, 2, 3, 4, 5]
    
    for bot_id in test_bots:
        print(f"\n📊 تست بات {bot_id}:")
        
        # دریافت تاخیر پیش‌فرض
        default_delay = launcher.get_spam_delay(bot_id)
        print(f"  🕒 تاخیر پیش‌فرض: {default_delay} ثانیه")
        
        # تست تنظیم تاخیر‌های مختلف
        test_delays = [0.5, 1.0, 2.5, 10.0, 0.1]
        
        for delay in test_delays:
            success, msg = launcher.set_spam_delay(bot_id, delay)
            print(f"  ✅ تنظیم {delay}s: {'موفق' if success else 'ناموفق'} - {msg}")
            
            # بررسی ذخیره شدن
            saved_delay = launcher.get_spam_delay(bot_id)
            if abs(saved_delay - delay) < 0.001:  # مقایسه float با تلرانس
                print(f"    ✅ ذخیره صحیح: {saved_delay}s")
            else:
                print(f"    ❌ خطا در ذخیره: انتظار {delay}s ولی {saved_delay}s دریافت شد")
        
        # تست تاخیر منفی (باید خطا دهد)
        success, msg = launcher.set_spam_delay(bot_id, -1.0)
        if not success:
            print(f"  ✅ تاخیر منفی رد شد: {msg}")
        else:
            print(f"  ❌ تاخیر منفی پذیرفته شد (مشکل!)")
        
        # تست تاخیر نامعتبر (رشته)
        success, msg = launcher.set_spam_delay(bot_id, "invalid")
        if not success:
            print(f"  ✅ مقدار نامعتبر رد شد: {msg}")
        else:
            print(f"  ❌ مقدار نامعتبر پذیرفته شد (مشکل!)")
    
    print("\n🔄 تست مقایسه بین بات‌ها:")
    
    # تنظیم تاخیرهای مختلف برای بات‌های مختلف
    delays = {1: 0.5, 2: 1.0, 3: 2.0, 4: 5.0, 5: 0.1}
    
    for bot_id, delay in delays.items():
        launcher.set_spam_delay(bot_id, delay)
    
    print("  تنظیمات نهایی:")
    for bot_id in test_bots:
        final_delay = launcher.get_spam_delay(bot_id)
        print(f"    بات {bot_id}: {final_delay}s")
    
    print("\n✅ تست سیستم تاخیر فحش کامل شد!")

if __name__ == "__main__":
    test_spam_delay_system()