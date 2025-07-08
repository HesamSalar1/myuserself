
#!/usr/bin/env python3
"""
تست سرعت تشخیص بهبود یافته ایموجی‌ها
"""
import sys
import time
import asyncio

sys.stdout.reconfigure(encoding='utf-8')

from unified_bot_launcher import UnifiedBotLauncher

class MockMessage:
    def __init__(self, text, chat_id=-1001234567890, message_id=12345):
        self.text = text
        self.caption = None
        self.id = message_id
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

async def test_detection_speed():
    """تست سرعت تشخیص"""
    print("⚡ تست سرعت تشخیص ایموجی‌های ممنوعه")
    print("=" * 50)
    
    launcher = UnifiedBotLauncher()
    
    # بارگذاری ایموجی‌ها
    launcher.forbidden_emojis = launcher.load_forbidden_emojis_from_db()
    print(f"📥 {len(launcher.forbidden_emojis)} ایموجی بارگذاری شد")
    
    # متن‌های تست
    test_texts = [
        "A CHARACTER HAS SPAWNED IN THE CHAT ⚡",
        "⚡️ انرژی!",
        "🔮 پیشگویی",
        "متن عادی بدون ایموجی",
        "بازی جدید ⚡ شروع شد",
        "کاراکتر جدید 🔮 ظاهر شد"
    ]
    
    print("\n🧪 تست سرعت تشخیص:")
    total_time = 0
    detected_count = 0
    
    for i, text in enumerate(test_texts, 1):
        message = MockMessage(text, message_id=i)
        
        start_time = time.time()
        should_stop = await launcher.should_pause_spam(message, 1)
        end_time = time.time()
        
        detection_time = (end_time - start_time) * 1000  # میلی‌ثانیه
        total_time += detection_time
        
        if should_stop:
            detected_count += 1
            status = "✅ توقف"
        else:
            status = "➡️ ادامه"
        
        print(f"{i}. {text[:30]}...")
        print(f"   └ {status} - {detection_time:.2f}ms")
    
    avg_time = total_time / len(test_texts)
    print(f"\n📊 نتایج:")
    print(f"   ⏱️ میانگین زمان: {avg_time:.2f}ms")
    print(f"   🎯 تشخیص شده: {detected_count}/{len(test_texts)}")
    print(f"   🚀 سرعت: {1000/avg_time:.0f} تشخیص/ثانیه")
    
    if avg_time < 5:
        print("   ✅ سرعت عالی!")
    elif avg_time < 10:
        print("   ✅ سرعت مناسب")
    else:
        print("   ⚠️ نیاز به بهبود")

if __name__ == "__main__":
    asyncio.run(test_detection_speed())
