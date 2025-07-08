
#!/usr/bin/env python3
"""
تست سیستم تشخیص ایموجی‌های بهبود یافته
"""
import sys
import time
import asyncio

sys.stdout.reconfigure(encoding='utf-8')

from unified_bot_launcher import UnifiedBotLauncher

class MockMessage:
    def __init__(self, text, chat_id=-1001234567890, message_id=None):
        self.text = text
        self.caption = None
        self.id = message_id or int(time.time() * 1000)
        self.chat = MockChat(chat_id)
        self.from_user = MockUser(1842714289)

class MockChat:
    def __init__(self, chat_id):
        self.id = chat_id
        self.title = "Test Chat"

class MockUser:
    def __init__(self, user_id):
        self.id = user_id
        self.is_bot = True
        self.first_name = "Test Bot"
        self.username = "testbot"

async def test_emoji_detection():
    """تست کامل تشخیص ایموجی"""
    print("🧪 تست تشخیص ایموجی‌های ممنوعه (نسخه بهبود یافته)")
    print("=" * 60)
    
    launcher = UnifiedBotLauncher()
    
    # بارگذاری ایموجی‌ها
    launcher.forbidden_emojis = launcher.load_forbidden_emojis_from_db()
    print(f"📥 {len(launcher.forbidden_emojis)} ایموجی ممنوعه بارگذاری شد")
    
    if launcher.forbidden_emojis:
        print("\n📋 ایموجی‌های موجود:")
        for i, emoji in enumerate(list(launcher.forbidden_emojis)[:10], 1):
            unicode_codes = [f"U+{ord(c):04X}" for c in emoji]
            print(f"  {i}. '{emoji}' → {' '.join(unicode_codes)}")
    else:
        print("❌ هیچ ایموجی ممنوعه‌ای یافت نشد!")
        return
    
    # تست متن‌های مختلف
    test_texts = [
        "A CHARACTER HAS SPAWNED IN THE CHAT ⚡",
        "⚡️ انرژی!",
        "🔮 پیشگویی",
        "متن عادی بدون ایموجی",
        "⚡ رعد و برق",
        "test ⚡️ test",
        "CHARACTER SPAWNED ⚡ IN CHAT",
        "⚡️⚡⚡️ triple lightning",
        "🔮💎⚡",
        "text without any forbidden emojis",
    ]
    
    print("\n🔍 تست تشخیص ایموجی‌ها:")
    print("-" * 50)
    
    detected_count = 0
    total_time = 0
    
    for i, text in enumerate(test_texts, 1):
        message = MockMessage(text)
        
        start_time = time.time()
        should_stop = await launcher.should_pause_spam(message, 1)
        end_time = time.time()
        
        detection_time = (end_time - start_time) * 1000  # میلی‌ثانیه
        total_time += detection_time
        
        if should_stop:
            detected_count += 1
            status = "✅ توقف"
            emoji_icon = "🛑"
        else:
            status = "➡️ ادامه"
            emoji_icon = "✅"
        
        print(f"{emoji_icon} {i:2d}. {text[:40]:<40} | {status} | {detection_time:.2f}ms")
    
    # نتایج نهایی
    avg_time = total_time / len(test_texts)
    detection_rate = detected_count / len(test_texts) * 100
    
    print("\n" + "=" * 60)
    print("📊 نتایج نهایی:")
    print(f"   ⏱️  میانگین زمان: {avg_time:.2f}ms")
    print(f"   🎯 تشخیص شده: {detected_count}/{len(test_texts)} ({detection_rate:.1f}%)")
    print(f"   🚀 سرعت: {1000/avg_time:.0f} تشخیص/ثانیه")
    
    if avg_time < 5:
        print("   ✅ سرعت عالی!")
    elif avg_time < 10:
        print("   ✅ سرعت مناسب")
    else:
        print("   ⚠️ نیاز به بهبود سرعت")
    
    if detection_rate >= 70:
        print("   ✅ نرخ تشخیص عالی!")
    elif detection_rate >= 50:
        print("   ⚠️ نرخ تشخیص قابل قبول")
    else:
        print("   ❌ نرخ تشخیص ضعیف - نیاز به بررسی")

async def test_direct_emoji_check():
    """تست مستقیم تشخیص ایموجی"""
    print("\n\n🔬 تست مستقیم تشخیص ایموجی:")
    print("-" * 40)
    
    launcher = UnifiedBotLauncher()
    launcher.forbidden_emojis = launcher.load_forbidden_emojis_from_db()
    
    test_cases = [
        ("⚡", "ایموجی ساده برق"),
        ("⚡️", "ایموجی برق با variation selector"),
        ("🔮", "ایموجی کریستال"),
        ("A ⚡ B", "متن با ایموجی در وسط"),
        ("⚡️⚡", "ایموجی‌های متعدد"),
        ("❌", "ایموجی غیرممنوعه"),
    ]
    
    for emoji_text, description in test_cases:
        found_emojis = []
        is_detected = launcher.contains_stop_emoji(emoji_text, found_emojis)
        
        status = "✅ تشخیص داده شد" if is_detected else "❌ تشخیص نشد"
        found_text = f" (یافت شده: {found_emojis[0]})" if found_emojis else ""
        
        print(f"   {description:<25} → {status}{found_text}")

if __name__ == "__main__":
    asyncio.run(test_emoji_detection())
    asyncio.run(test_direct_emoji_check())
