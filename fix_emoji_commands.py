
#!/usr/bin/env python3
"""
اسکریپت تست و رفع مشکل کامندهای ایموجی
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from unified_bot_launcher import UnifiedBotLauncher

def test_emoji_commands():
    """تست کامندهای ایموجی"""
    print("🧪 تست کامندهای ایموجی...")
    
    launcher = UnifiedBotLauncher()
    
    # تست ایموجی‌های مختلف
    test_emojis = [
        ("⚡", "برق ساده"),
        ("⚡️", "برق با variation selector"),
        ("🔮", "کریستال جادویی"),
        ("🌤", "ابری نیمه آفتابی"),
        ("💎", "الماس"),
        ("🎯", "هدف"),
        ("🏆", "جام قهرمانی")
    ]
    
    success_count = 0
    
    for emoji, description in test_emojis:
        print(f"\n🔍 تست ایموجی: {emoji} ({description})")
        
        # تلاش برای اضافه کردن
        if launcher.add_forbidden_emoji_to_db(emoji, description):
            print(f"✅ موفق: {emoji}")
            success_count += 1
        else:
            print(f"❌ ناموفق: {emoji}")
    
    print(f"\n📊 نتیجه: {success_count}/{len(test_emojis)} ایموجی اضافه شد")
    
    # تست تشخیص
    print("\n🔍 تست تشخیص ایموجی‌ها:")
    launcher.forbidden_emojis = launcher.load_forbidden_emojis_from_db()
    
    test_texts = [
        "A CHARACTER HAS SPAWNED ⚡",
        "🔮 crystal ball",
        "🌤 partly sunny",
        "متن عادی بدون ایموجی"
    ]
    
    for text in test_texts:
        found_emojis = []
        detected = launcher.contains_stop_emoji(text, found_emojis)
        status = "✅ تشخیص داده شد" if detected else "❌ تشخیص نشد"
        print(f"   '{text}' → {status}")

def fix_database_structure():
    """رفع ساختار دیتابیس"""
    print("\n🔧 رفع ساختار دیتابیس...")
    
    launcher = UnifiedBotLauncher()
    
    # تنظیم دیتابیس برای بات 1
    db_path = launcher.bot_configs[1]['db_path']
    launcher.setup_database(1, db_path)
    
    print("✅ ساختار دیتابیس بررسی و رفع شد")

if __name__ == "__main__":
    print("🚀 شروع رفع مشکل کامندهای ایموجی")
    print("=" * 50)
    
    fix_database_structure()
    test_emoji_commands()
    
    print("\n✅ تست کامل شد!")
    print("\n💡 حالا می‌توانید از کامندهای زیر استفاده کنید:")
    print("   /addemoji ⚡ توضیحات - اضافه کردن ایموجی")
    print("   /delemoji ⚡ - حذف ایموجی")
    print("   /listemoji - نمایش لیست")
    print("   /testemoji ⚡ - تست تشخیص")
    print("   /debugemoji متن تست - تست پیشرفته")
    print("   /syncemojis - همگام‌سازی")
