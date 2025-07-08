
#!/usr/bin/env python3
import sys
import os
import asyncio

sys.stdout.reconfigure(encoding='utf-8')

from unified_bot_launcher import UnifiedBotLauncher

async def test_detection_system():
    """تست کامل سیستم تشخیص ایموجی"""
    print("🧪 تست سیستم تشخیص ایموجی‌های ممنوعه")
    print("=" * 60)
    
    launcher = UnifiedBotLauncher()
    
    # بارگذاری ایموجی‌های ممنوعه
    print("📥 بارگذاری ایموجی‌های ممنوعه...")
    launcher.forbidden_emojis = launcher.load_forbidden_emojis_from_db()
    print(f"✅ {len(launcher.forbidden_emojis)} ایموجی بارگذاری شد")
    
    if launcher.forbidden_emojis:
        print("📋 ایموجی‌های موجود:")
        for i, emoji in enumerate(list(launcher.forbidden_emojis)[:10], 1):
            unicode_codes = [f"U+{ord(c):04X}" for c in emoji]
            print(f"  {i}. {emoji} → {' '.join(unicode_codes)}")
    else:
        print("❌ هیچ ایموجی ممنوعه‌ای یافت نشد!")
        return
    
    # تست متن‌های مختلف
    test_texts = [
        "A CHARACTER HAS SPAWNED IN THE CHAT ⚡",
        "⚡️ برق!",
        "🔮 کریستال جادویی",
        "متن عادی بدون ایموجی",
        "⚡ رعد و برق",
        "test ⚡️ test",
    ]
    
    print("\n🔍 تست تشخیص ایموجی‌ها:")
    print("-" * 40)
    
    detected_count = 0
    for i, text in enumerate(test_texts, 1):
        found_emojis = []
        is_detected = launcher.contains_stop_emoji(text, found_emojis)
        
        status = "✅ تشخیص داده شد" if is_detected else "❌ تشخیص نشد"
        print(f"{i}. {text}")
        print(f"   └ {status}")
        
        if found_emojis:
            print(f"   └ ایموجی یافت شده: {found_emojis[0]}")
            detected_count += 1
        print()
    
    print(f"📊 خلاصه: {detected_count} از {len(test_texts)} متن تشخیص داده شد")
    
    # تست ربات گزارش‌دهی
    print("\n📢 تست ربات گزارش‌دهی:")
    print("-" * 40)
    
    if launcher.report_bot:
        if hasattr(launcher.report_bot, 'is_valid') and launcher.report_bot.is_valid:
            print("✅ ربات گزارش‌دهی موجود و معتبر")
        else:
            print("❌ ربات گزارش‌دهی نامعتبر")
    else:
        print("❌ ربات گزارش‌دهی موجود نیست")
    
    # نمایش پیشنهادات
    print("\n💡 پیشنهادات:")
    if detected_count == 0:
        print("- ایموجی‌های ممنوعه در دیتابیس وجود ندارند")
        print("- از دستور /addemoji استفاده کنید")
    
    if not launcher.report_bot or not getattr(launcher.report_bot, 'is_valid', False):
        print("- توکن ربات گزارش‌دهی را در Secrets بررسی کنید")
        print("- REPORT_BOT_TOKEN = 7708355228:AAGPzhm47U5-4uPnALl6Oc6En91aCYLyydk")

if __name__ == "__main__":
    asyncio.run(test_detection_system())
