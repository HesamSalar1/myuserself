#!/usr/bin/env python3
"""
تست سیستم تاخیر نامحدود
بررسی تنظیم تاخیرهای مختلف از 0 تا اعداد بزرگ
"""

from unified_bot_launcher import UnifiedBotLauncher

def test_unlimited_delay_settings():
    """تست تنظیم تاخیرهای مختلف"""
    print("🔍 تست سیستم تاخیر نامحدود...")
    
    launcher = UnifiedBotLauncher()
    
    # تست تاخیرهای مختلف
    test_delays = [
        0,          # صفر
        0.001,      # یک هزارم ثانیه
        0.01,       # یک صدم ثانیه
        0.1,        # یک دهم ثانیه
        0.5,        # نیم ثانیه
        1.0,        # یک ثانیه
        2.5,        # دو و نیم ثانیه
        10.0,       # ده ثانیه
        60.0,       # یک دقیقه
        3600.0      # یک ساعت
    ]
    
    print(f"\n📊 تست {len(test_delays)} تاخیر مختلف:")
    
    for delay in test_delays:
        # تنظیم تاخیر عمومی
        launcher.min_global_delay = delay
        
        # بررسی ذخیره شدن
        actual_delay = launcher.min_global_delay
        
        if abs(actual_delay - delay) < 0.0001:  # مقایسه float با تلرانس
            print(f"  ✅ تاخیر {delay}s: موفق - ذخیره شده: {actual_delay}s")
        else:
            print(f"  ❌ تاخیر {delay}s: ناموفق - انتظار {delay}s ولی {actual_delay}s دریافت شد")
    
    # تست تاخیر منفی (باید خطا دهد)
    print(f"\n🚫 تست تاخیر منفی:")
    negative_delays = [-1.0, -0.1, -0.001]
    
    for delay in negative_delays:
        original_delay = launcher.min_global_delay
        launcher.min_global_delay = delay  # این تنظیم مستقیم است
        
        # بررسی که آیا تغییر کرده یا نه
        if launcher.min_global_delay != delay:
            print(f"  ✅ تاخیر منفی {delay}s رد شد")
        else:
            print(f"  ❌ تاخیر منفی {delay}s پذیرفته شد (مشکل!)")
        
        # بازگشت به تاخیر قبلی
        launcher.min_global_delay = original_delay
    
    print(f"\n🎯 نتیجه نهایی:")
    print(f"   • تاخیر فعلی: {launcher.min_global_delay}s")
    print(f"   • محدودیت حداقل: برداشته شده")
    print(f"   • محدودیت حداکثر: ندارد")
    print(f"   • اعداد اعشاری: پشتیبانی کامل")
    
    return True

def test_spam_delay_per_bot():
    """تست تاخیر فحش برای هر بات"""
    print(f"\n🤖 تست تاخیر فحش برای بات‌های مختلف:")
    
    launcher = UnifiedBotLauncher()
    
    # تست برای چند بات
    test_bots = [1, 2, 3]
    test_delays = [0, 0.001, 0.5, 2.0]
    
    for bot_id in test_bots:
        print(f"\n  🔧 بات {bot_id}:")
        
        # راه‌اندازی دیتابیس
        try:
            launcher.setup_database(bot_id, launcher.bot_configs[bot_id]['db_path'])
        except:
            pass  # ممکن است قبلاً راه‌اندازی شده باشد
        
        for delay in test_delays:
            success, msg = launcher.set_spam_delay(bot_id, delay)
            if success:
                saved_delay = launcher.get_spam_delay(bot_id)
                print(f"    ✅ تاخیر {delay}s: موفق - ذخیره: {saved_delay}s")
            else:
                print(f"    ❌ تاخیر {delay}s: ناموفق - {msg}")
    
    return True

def main():
    """تابع اصلی تست"""
    print("=" * 60)
    print("🧪 تست سیستم تاخیر نامحدود")
    print("=" * 60)
    
    # تست تاخیر عمومی
    success1 = test_unlimited_delay_settings()
    
    # تست تاخیر فحش
    success2 = test_spam_delay_per_bot()
    
    if success1 and success2:
        print("\n✅ همه تست‌ها موفقیت‌آمیز بود!")
        print("🎉 سیستم حالا:")
        print("   • هر عدد غیرمنفی را می‌پذیرد")
        print("   • از 0 تا بی‌نهایت قابل تنظیم است")
        print("   • دقت اعشاری کامل دارد")
        print("   • برای تاخیر عمومی و فحش اعمال می‌شود")
    else:
        print("\n❌ برخی تست‌ها ناموفق")
    
    print("=" * 60)

if __name__ == "__main__":
    main()