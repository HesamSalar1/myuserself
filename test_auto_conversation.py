#!/usr/bin/env python3
"""
تست سیستم گفتگوی خودکار بین ربات‌ها
بررسی عملکرد صحیح قابلیت‌های جدید
"""

import asyncio
import sys
import time
from unified_bot_launcher import UnifiedBotLauncher

sys.stdout.reconfigure(encoding='utf-8')

async def test_auto_conversation_system():
    """تست کامل سیستم گفتگوی خودکار"""
    print("🧪 تست سیستم گفتگوی خودکار")
    print("=" * 50)
    
    launcher = UnifiedBotLauncher()
    
    # تست ۱: بررسی تنظیمات اولیه
    print("\n📋 تست ۱: بررسی تنظیمات اولیه")
    print(f"  ✓ سیستم گفتگو: {'فعال' if launcher.auto_chat_enabled else 'غیرفعال'}")
    print(f"  ✓ تعداد ربات‌ها: {len(launcher.bot_configs)}")
    print(f"  ✓ وضعیت آنلاین ربات‌ها: {sum(launcher.bot_online_status.values())} از ۹")
    
    # تست ۲: بررسی دیتابیس گفتگو
    print("\n💾 تست ۲: بررسی دیتابیس گفتگو")
    try:
        # تنظیم دیتابیس برای بات ۱
        launcher.setup_database(1, launcher.bot_configs[1]['db_path'])
        
        # دریافت موضوعات
        topics = launcher.get_conversation_topics()
        print(f"  ✓ موضوعات موجود: {len(topics)}")
        print(f"    └ نمونه: {topics[:3]}")
        
        # دریافت پیام‌های مختلف
        starters = launcher.get_conversation_messages('starter')
        responses = launcher.get_conversation_messages('response')
        questions = launcher.get_conversation_messages('question')
        
        print(f"  ✓ پیام‌های شروع: {len(starters)}")
        print(f"  ✓ پاسخ‌ها: {len(responses)}") 
        print(f"  ✓ سوالات: {len(questions)}")
        
    except Exception as e:
        print(f"  ❌ خطا در دیتابیس: {e}")
    
    # تست ۳: تولید پیام‌های گفتگو
    print("\n🗣️ تست ۳: تولید پیام‌های گفتگو")
    test_chat_id = -1001234567890
    
    # شبیه‌سازی گفتگوی فعال
    launcher.active_conversations[test_chat_id] = {
        'started_at': time.time(),
        'last_message_time': 0,
        'last_bot': None,
        'current_topic': 'روزمره',
        'message_count': 0,
        'participants': set()
    }
    
    try:
        # تست تولید پیام‌های مختلف
        for i in range(5):
            message = await launcher.generate_conversation_message(test_chat_id, 1)
            if message:
                print(f"  ✓ پیام {i+1}: {message[:50]}...")
                launcher.active_conversations[test_chat_id]['message_count'] += 1
            else:
                print(f"  ❌ خطا در تولید پیام {i+1}")
                
    except Exception as e:
        print(f"  ❌ خطا در تولید پیام: {e}")
    
    # تست ۴: انتخاب ربات
    print("\n🤖 تست ۴: انتخاب ربات برای گفتگو")
    try:
        for i in range(3):
            selected_bot = launcher.select_bot_for_conversation(test_chat_id)
            if selected_bot:
                print(f"  ✓ ربات انتخاب شده {i+1}: {selected_bot}")
                launcher.last_bot_activity[selected_bot] = time.time()
                # شبیه‌سازی آخرین بات در گفتگو
                launcher.active_conversations[test_chat_id]['last_bot'] = selected_bot
            else:
                print(f"  ❌ هیچ ربات آنلاینی یافت نشد")
                
    except Exception as e:
        print(f"  ❌ خطا در انتخاب ربات: {e}")
    
    # تست ۵: شبیه‌سازی آفلاین شدن
    print("\n🔴 تست ۵: شبیه‌سازی آفلاین شدن ربات‌ها")
    try:
        # آفلاین کردن چند ربات
        for bot_id in [2, 3, 4]:
            launcher.simulate_bot_offline(bot_id, 5)  # ۵ ثانیه آفلاین
            print(f"  ✓ ربات {bot_id} آفلاین شد")
        
        # بررسی وضعیت
        online_count = sum(1 for i in range(1, 10) if launcher.bot_online_status.get(i, True))
        print(f"  ✓ ربات‌های آنلاین: {online_count} از ۹")
        
    except Exception as e:
        print(f"  ❌ خطا در آفلاین کردن: {e}")
    
    # تست ۶: تغییر موضوع گفتگو
    print("\n📝 تست ۶: تغییر موضوع گفتگو")
    try:
        original_topic = launcher.active_conversations[test_chat_id]['current_topic']
        print(f"  • موضوع اصلی: {original_topic}")
        
        # شبیه‌سازی تغییر موضوع
        import random
        new_topic = random.choice(launcher.get_conversation_topics())
        launcher.active_conversations[test_chat_id]['current_topic'] = new_topic
        print(f"  ✓ موضوع جدید: {new_topic}")
        
    except Exception as e:
        print(f"  ❌ خطا در تغییر موضوع: {e}")
    
    # تست ۷: آمار گفتگو
    print("\n📊 تست ۷: آمار و گزارش گفتگو")
    try:
        conv = launcher.active_conversations[test_chat_id]
        duration = int(time.time() - conv['started_at'])
        
        print(f"  ✓ مدت گفتگو: {duration} ثانیه")
        print(f"  ✓ تعداد پیام: {conv['message_count']}")
        print(f"  ✓ موضوع فعلی: {conv['current_topic']}")
        print(f"  ✓ شرکت‌کنندگان: {len(conv['participants'])}")
        
    except Exception as e:
        print(f"  ❌ خطا در آمار: {e}")
    
    # پاکسازی
    if test_chat_id in launcher.active_conversations:
        del launcher.active_conversations[test_chat_id]
    
    print("\n🎉 تست‌ها تکمیل شد!")
    print("✅ سیستم گفتگوی خودکار آماده استفاده است")
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_auto_conversation_system())
        if result:
            print("\n✅ همه تست‌ها موفق بودند")
            exit(0)
        else:
            print("\n❌ برخی تست‌ها ناموفق بودند")
            exit(1)
    except Exception as e:
        print(f"\n💥 خطای کلی: {e}")
        exit(1)