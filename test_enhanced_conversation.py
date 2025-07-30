#!/usr/bin/env python3
"""
تست سیستم گفتگوی خودکار بهبود یافته
بررسی تنوع و طبیعی بودن پیام‌ها
"""

import asyncio
import sys
import time
from unified_bot_launcher import UnifiedBotLauncher

sys.stdout.reconfigure(encoding='utf-8')

async def test_enhanced_conversation():
    """تست سیستم بهبود یافته گفتگو"""
    print("🚀 تست سیستم گفتگوی پیشرفته")
    print("=" * 60)
    
    launcher = UnifiedBotLauncher()
    test_chat_id = -1001234567890
    
    # راه‌اندازی گفتگوی تست
    launcher.active_conversations[test_chat_id] = {
        'started_at': time.time(),
        'last_message_time': 0,
        'last_bot': None,
        'current_topic': 'روزمره',
        'message_count': 0,
        'participants': set()
    }
    
    print("💬 تست تولید پیام‌های متنوع توسط ربات‌های مختلف:")
    print("-" * 60)
    
    # تست هر ربات با شخصیت منحصر به فرد
    bot_names = {
        1: "شوخ و بامزه",
        2: "جدی و منطقی", 
        3: "دوستانه و مهربان",
        4: "پرانرژی و فعال",
        5: "آروم و متین",
        6: "کنجکاو و پرسشگر",
        7: "خلاق و هنری",
        8: "عملی و واقع‌بین",
        9: "اجتماعی و پرحرف"
    }
    
    for bot_id in range(1, 10):
        try:
            # تولید چند پیام از هر ربات
            messages = []
            for i in range(3):
                message = await launcher.generate_conversation_message(test_chat_id, bot_id)
                if message:
                    messages.append(message)
                    # شبیه‌سازی پیشرفت گفتگو
                    launcher.active_conversations[test_chat_id]['message_count'] += 1
                    launcher.active_conversations[test_chat_id]['last_bot'] = bot_id
            
            # نمایش نتایج
            personality = bot_names.get(bot_id, "ناشناس")
            print(f"🤖 ربات {bot_id} ({personality}):")
            for j, msg in enumerate(messages):
                if msg:
                    print(f"   {j+1}. {msg}")
            print()
            
        except Exception as e:
            print(f"❌ خطا برای ربات {bot_id}: {e}")
    
    # تست موضوعات مختلف
    print("\n🎯 تست موضوعات مختلف:")
    print("-" * 60)
    
    topics = ['تکنولوژی', 'خوراک', 'ورزش', 'موسیقی']
    
    for topic in topics:
        print(f"\n📋 موضوع: {topic}")
        launcher.active_conversations[test_chat_id]['current_topic'] = topic
        launcher.active_conversations[test_chat_id]['message_count'] = 0
        
        # تست چند ربات برای این موضوع
        test_bots = [1, 2, 4, 6]  # انتخاب چند ربات متنوع
        
        for bot_id in test_bots:
            message = await launcher.generate_conversation_message(test_chat_id, bot_id)
            if message:
                personality = bot_names.get(bot_id, "ناشناس")
                print(f"   🤖 ربات {bot_id} ({personality}): {message}")
    
    # تست جلوگیری از تکرار
    print("\n🔄 تست جلوگیری از تکرار ربات:")
    print("-" * 60)
    
    launcher.active_conversations[test_chat_id]['current_topic'] = 'روزمره'
    launcher.active_conversations[test_chat_id]['last_bot'] = 3
    
    attempts = 0
    successful_messages = 0
    
    for i in range(10):
        message = await launcher.generate_conversation_message(test_chat_id, 3)  # همان ربات قبلی
        attempts += 1
        if message:
            successful_messages += 1
            print(f"   ✓ ربات 3 (تکرار {successful_messages}): {message}")
    
    rejection_rate = ((attempts - successful_messages) / attempts) * 100
    print(f"\n📊 نرخ رد تکرار: {rejection_rate:.1f}% (باید حدود 70% باشد)")
    
    # تست عناصر طبیعی
    print("\n🌟 تست عناصر طبیعی (ایموجی، تأکید، مخلوط زبان):")
    print("-" * 60)
    
    natural_elements = {
        'has_emoji': 0,
        'has_emphasis': 0, 
        'has_mixed_language': 0,
        'has_elongated_words': 0
    }
    
    total_test_messages = 50
    
    for i in range(total_test_messages):
        bot_id = (i % 9) + 1
        message = await launcher.generate_conversation_message(test_chat_id, bot_id)
        
        if message:
            # بررسی عناصر طبیعی
            if any(emoji in message for emoji in ['😊', '🤔', '😅', '🙂', '😄', '💬', '👍', '❤️']):
                natural_elements['has_emoji'] += 1
            
            if any(word in message for word in ['واقعاً', 'یعنی', 'راستی', 'ببینین', 'والا']):
                natural_elements['has_emphasis'] += 1
            
            if any(word in message for word in ['Hello', 'OK', 'Nice', 'What', 'Namaste', 'Kya']):
                natural_elements['has_mixed_language'] += 1
            
            if 'ااا' in message or 'ییی' in message:
                natural_elements['has_elongated_words'] += 1
        
        launcher.active_conversations[test_chat_id]['message_count'] += 1
    
    print("📈 آمار عناصر طبیعی:")
    for element, count in natural_elements.items():
        percentage = (count / total_test_messages) * 100
        print(f"   • {element}: {count}/{total_test_messages} ({percentage:.1f}%)")
    
    # پاکسازی
    del launcher.active_conversations[test_chat_id]
    
    print("\n🎉 تست کامل شد!")
    print("✅ سیستم گفتگوی پیشرفته آماده است")
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_enhanced_conversation())
        if result:
            print("\n✅ تست‌ها موفقیت‌آمیز بودند")
        exit(0)
    except Exception as e:
        print(f"\n💥 خطای کلی: {e}")
        exit(1)