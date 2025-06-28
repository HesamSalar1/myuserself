#!/usr/bin/env python3
"""
تست سیستم توقف فوری ایموجی‌های ممنوعه
بررسی توقف لحظه‌ای همه بات‌ها
"""

import asyncio
import time
from unified_bot_launcher import UnifiedBotLauncher

class MockMessage:
    def __init__(self, text=None, caption=None, user_id=123456789):
        self.text = text
        self.caption = caption
        self.from_user = MockUser(user_id)
        self.chat = MockChat()

class MockUser:
    def __init__(self, user_id):
        self.id = user_id
        self.is_bot = False

class MockChat:
    def __init__(self):
        self.id = -1001234567890

async def test_instant_stop_system():
    """تست سیستم توقف فوری"""
    print("🔍 شروع تست سیستم توقف فوری...")
    
    launcher = UnifiedBotLauncher()
    
    # اضافه کردن چند ایموجی ممنوعه برای تست
    test_emojis = ["⚡", "🔮", "💎"]
    for emoji in test_emojis:
        launcher.forbidden_emojis.add(emoji)
    
    print(f"📝 ایموجی‌های تست: {test_emojis}")
    
    # شبیه‌سازی شروع چند تسک فحش
    async def simulate_spam_task(bot_id, duration=10):
        """شبیه‌سازی تسک فحش طولانی"""
        spam_key = f"{bot_id}_enemy_chat"
        start_time = time.time()
        
        try:
            print(f"🔥 شروع تسک فحش شبیه‌سازی شده برای بات {bot_id}")
            
            while True:
                # بررسی توقف اضطراری
                if launcher.emergency_stop_event.is_set():
                    stop_time = time.time()
                    response_time = stop_time - start_time
                    print(f"🚨 بات {bot_id} متوقف شد در {response_time:.3f} ثانیه")
                    return response_time
                
                # شبیه‌سازی کار
                await asyncio.sleep(0.1)
                
                # توقف خودکار بعد از مدت زمان مشخص
                if time.time() - start_time > duration:
                    print(f"⏰ بات {bot_id} به پایان زمان رسید")
                    return duration
                    
        except asyncio.CancelledError:
            stop_time = time.time()
            response_time = stop_time - start_time
            print(f"❌ بات {bot_id} کنسل شد در {response_time:.3f} ثانیه")
            return response_time
    
    # شروع چند تسک شبیه‌سازی
    print("\n🚀 شروع 5 تسک فحش شبیه‌سازی...")
    tasks = []
    for bot_id in range(1, 6):
        task = asyncio.create_task(simulate_spam_task(bot_id))
        tasks.append(task)
        launcher.continuous_spam_tasks[f"{bot_id}_enemy_chat"] = task
    
    # انتظار کوتاه تا تسک‌ها شروع شوند
    await asyncio.sleep(1)
    print(f"✅ {len(tasks)} تسک فحش فعال")
    
    # تست تشخیص ایموجی ممنوعه
    print(f"\n⚡ شبیه‌سازی تشخیص ایموجی ممنوعه...")
    trigger_time = time.time()
    
    # ایجاد پیام شامل ایموجی ممنوعه
    test_message = MockMessage(text="سلام ⚡ چطوری؟")
    
    # تشخیص ایموجی و فعال‌سازی توقف اضطراری
    should_stop = launcher.should_pause_spam(test_message, 1)
    
    if should_stop:
        print("✅ ایموجی ممنوعه تشخیص داده شد")
        print("🚨 توقف اضطراری فعال شد")
        
        # انتظار برای توقف تسک‌ها
        response_times = await asyncio.gather(*tasks, return_exceptions=True)
        
        # تحلیل نتایج
        valid_times = [t for t in response_times if isinstance(t, (int, float))]
        if valid_times:
            avg_response = sum(valid_times) / len(valid_times)
            max_response = max(valid_times)
            min_response = min(valid_times)
            
            print(f"\n📊 نتایج توقف:")
            print(f"   ⚡ سریع‌ترین: {min_response:.3f} ثانیه")
            print(f"   🐌 کندترین: {max_response:.3f} ثانیه") 
            print(f"   📈 میانگین: {avg_response:.3f} ثانیه")
            
            if max_response < 0.5:
                print("✅ همه بات‌ها در کمتر از 0.5 ثانیه متوقف شدند - EXCELLENT!")
            elif max_response < 1.0:
                print("✅ همه بات‌ها در کمتر از 1 ثانیه متوقف شدند - GOOD")
            else:
                print("⚠️ برخی بات‌ها بیش از 1 ثانیه طول کشیدند - NEEDS IMPROVEMENT")
    else:
        print("❌ ایموجی ممنوعه تشخیص داده نشد")
        
        # لغو تسک‌ها
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

def test_forbidden_emoji_detection():
    """تست تشخیص ایموجی‌های ممنوعه"""
    print("\n🔍 تست تشخیص ایموجی‌های ممنوعه...")
    
    launcher = UnifiedBotLauncher()
    launcher.forbidden_emojis = {"⚡", "🔮", "💎", "🎯", "🏆"}
    
    test_cases = [
        ("سلام ⚡ چطوری", True),
        ("🔮 جادو", True),
        ("هیچی 💎 ندارم", True),
        ("سلام دوست من", False),
        ("🌟 ستاره", False),
        ("⚡️ برق", True),  # تست variant selector
    ]
    
    for text, expected in test_cases:
        message = MockMessage(text=text)
        result = launcher.should_pause_spam(message, 1)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{text}' -> {result} (انتظار: {expected})")

async def main():
    """تابع اصلی تست"""
    print("=" * 60)
    print("🧪 تست کامل سیستم توقف فوری ایموجی‌های ممنوعه")
    print("=" * 60)
    
    # تست تشخیص ایموجی
    test_forbidden_emoji_detection()
    
    # تست توقف فوری
    await test_instant_stop_system()
    
    print("\n" + "=" * 60)
    print("✅ همه تست‌ها کامل شد!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())