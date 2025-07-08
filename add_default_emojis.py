
#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')

from unified_bot_launcher import UnifiedBotLauncher

def add_default_emojis():
    """اضافه کردن ایموجی‌های پیش‌فرض"""
    print("➕ اضافه کردن ایموجی‌های ممنوعه پیش‌فرض...")
    
    launcher = UnifiedBotLauncher()
    
    # ایموجی‌های ضروری که باید ممنوع باشند
    default_emojis = [
        "⚡",      # برق (ساده)
        "⚡️",     # برق (با variation selector)
        "🔮",      # کریستال
        "💎",      # الماس
        "🎯",      # هدف
        "🏆",      # جام
        "❤️",     # قلب
        "💰",      # پول
        "🎁",      # هدیه
    ]
    
    added_count = 0
    for emoji in default_emojis:
        if launcher.add_forbidden_emoji_to_db(emoji):
            print(f"✅ اضافه شد: {emoji}")
            added_count += 1
        else:
            print(f"⚠️ قبلاً موجود: {emoji}")
    
    print(f"\n📊 {added_count} ایموجی جدید اضافه شد")
    
    # بارگذاری مجدد برای تست
    emojis = launcher.load_forbidden_emojis_from_db()
    print(f"✅ مجموع {len(emojis)} ایموجی در دیتابیس")

if __name__ == "__main__":
    add_default_emojis()
