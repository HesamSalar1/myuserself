#!/usr/bin/env python3
"""
تست سیستم Rate Limiting بهبود یافته
بررسی جلوگیری از ارسال همزمان پیام‌ها
"""

import asyncio
import time
from unified_bot_launcher import UnifiedBotLauncher

async def test_concurrent_messaging():
    """تست پیام‌رسانی همزمان و rate limiting"""
    print("🔍 شروع تست سیستم Rate Limiting...")
    
    # ایجاد لانچر
    launcher = UnifiedBotLauncher()
    
    # تنظیم تاخیر عمومی
    launcher.min_global_delay = 1.0  # 1 ثانیه تاخیر بین پیام‌ها
    print(f"⚙️ تاخیر عمومی تنظیم شد: {launcher.min_global_delay} ثانیه")
    
    # شبیه‌سازی چت ID
    test_chat_id = -1001234567890
    
    # شبیه‌سازی ارسال پیام همزمان از چندین بات
    async def simulate_bot_message(bot_id, message_num):
        """شبیه‌سازی ارسال پیام از یک بات"""
        if test_chat_id not in launcher.chat_locks:
            launcher.chat_locks[test_chat_id] = asyncio.Lock()
        
        async with launcher.chat_locks[test_chat_id]:
            start_time = time.time()
            
            # بررسی آخرین زمان ارسال
            if test_chat_id in launcher.last_message_time:
                time_since_last = start_time - launcher.last_message_time[test_chat_id]
                if time_since_last < launcher.min_global_delay:
                    wait_time = launcher.min_global_delay - time_since_last
                    print(f"⏳ بات {bot_id} منتظر {wait_time:.2f} ثانیه...")
                    await asyncio.sleep(wait_time)
            
            # ثبت زمان ارسال
            launcher.last_message_time[test_chat_id] = time.time()
            
            end_time = time.time()
            total_time = end_time - start_time
            
            print(f"📤 بات {bot_id} - پیام {message_num} ارسال شد (زمان کل: {total_time:.2f}s)")
    
    # تست ارسال همزمان از 5 بات
    print("\n🚀 شروع تست ارسال همزمان...")
    start_test_time = time.time()
    
    tasks = []
    for bot_id in range(1, 6):
        for msg_num in range(1, 3):  # هر بات 2 پیام
            task = simulate_bot_message(bot_id, msg_num)
            tasks.append(task)
    
    # اجرای همزمان همه تسک‌ها
    await asyncio.gather(*tasks)
    
    end_test_time = time.time()
    total_test_time = end_test_time - start_test_time
    
    print(f"\n✅ تست کامل شد!")
    print(f"⏱️ زمان کل تست: {total_test_time:.2f} ثانیه")
    print(f"📊 تعداد پیام‌ها: {len(tasks)}")
    print(f"📈 میانگین زمان هر پیام: {total_test_time/len(tasks):.2f} ثانیه")
    
    # بررسی اینکه آیا تاخیر صحیح اعمال شده
    expected_min_time = (len(tasks) - 1) * launcher.min_global_delay
    if total_test_time >= expected_min_time:
        print(f"✅ Rate limiting صحیح کار می‌کند! (حداقل زمان مورد انتظار: {expected_min_time:.2f}s)")
    else:
        print(f"❌ Rate limiting ممکن است صحیح کار نکند (زمان کمتر از انتظار)")

def test_delay_settings():
    """تست تنظیمات تاخیر"""
    print("\n🔧 تست تنظیمات تاخیر...")
    
    launcher = UnifiedBotLauncher()
    
    # تست تنظیم تاخیرهای مختلف
    test_delays = [0.5, 1.0, 2.0, 0.1]
    
    for delay in test_delays:
        launcher.min_global_delay = delay
        print(f"✅ تاخیر عمومی تنظیم شد: {launcher.min_global_delay} ثانیه")
        
        # تست تاخیر فحش برای بات‌های مختلف
        for bot_id in [1, 2, 3]:
            current_delay = launcher.get_spam_delay(bot_id)
            print(f"   🔸 بات {bot_id}: {current_delay} ثانیه")

async def main():
    """تابع اصلی تست"""
    print("=" * 50)
    print("🧪 تست کامل سیستم Rate Limiting")
    print("=" * 50)
    
    # تست تنظیمات
    test_delay_settings()
    
    # تست پیام‌رسانی همزمان
    await test_concurrent_messaging()
    
    print("\n" + "=" * 50)
    print("✅ همه تست‌ها کامل شد!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())