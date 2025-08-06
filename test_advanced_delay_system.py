#!/usr/bin/env python3
"""
🚀 تست سیستم تاخیر پیشرفته
"""

import sys
import time
import asyncio

sys.stdout.reconfigure(encoding='utf-8')

async def test_advanced_delay_system():
    """تست کامل سیستم تاخیر پیشرفته"""
    print("🚀 تست سیستم تاخیر پیشرفته")
    print("=" * 50)
    
    # شبیه‌سازی کلاس BotLauncher
    class MockBotLauncher:
        def __init__(self):
            self.advanced_delay_settings = {
                'enemy_spam_delay': 1.0,
                'friend_reply_delay': 0.3,
                'global_message_delay': 0.5,
                'conversation_delay': 2.0,
                'emoji_reaction_delay': 0.1,
                'burst_protection_delay': 3.0,
                'per_chat_delay_multiplier': 1.0,
                'adaptive_delay_enabled': True,
                'smart_delay_reduction': True,
            }
            self.chat_specific_delays = {}
            self.last_message_time = {}
            
        def get_adaptive_delay(self, delay_type, chat_id, user_type="unknown"):
            """محاسبه تاخیر انطباقی"""
            base_delay = self.advanced_delay_settings.get(delay_type, 1.0)
            chat_multiplier = self.chat_specific_delays.get(chat_id, {}).get('multiplier', 1.0)
            
            if delay_type == 'emoji_reaction_delay':
                base_delay = 0.05
                
            if user_type == "enemy" and delay_type == 'enemy_spam_delay':
                base_delay = self.advanced_delay_settings.get('enemy_spam_delay', 1.0)
            elif user_type == "friend" and delay_type == 'friend_reply_delay':
                base_delay = self.advanced_delay_settings.get('friend_reply_delay', 0.3)
                
            final_delay = base_delay * chat_multiplier
            final_delay = max(0.01, min(final_delay, 30.0))
            
            return final_delay
            
        async def smart_delay_with_adaptation(self, delay_type, chat_id, user_type="unknown"):
            """تاخیر هوشمند با انطباق"""
            start_time = time.time()
            delay = self.get_adaptive_delay(delay_type, chat_id, user_type)
            
            if self.advanced_delay_settings.get('adaptive_delay_enabled', True):
                current_time = time.time()
                last_activity = self.last_message_time.get(chat_id, 0)
                
                if current_time - last_activity > 30:
                    delay *= 0.7
                elif current_time - last_activity > 60:
                    delay *= 0.5
            
            if self.advanced_delay_settings.get('smart_delay_reduction', True):
                if delay_type == 'emoji_reaction_delay':
                    delay = min(delay, 0.1)
                    
            if delay > 0:
                await asyncio.sleep(delay)
                
            self.last_message_time[chat_id] = time.time()
            actual_delay = time.time() - start_time
            
            return actual_delay
    
    # شروع تست
    launcher = MockBotLauncher()
    
    test_cases = [
        {
            'delay_type': 'emoji_reaction_delay',
            'chat_id': -1001234567890,
            'user_type': 'unknown',
            'expected_max': 0.1,
            'description': 'واکنش فوری به ایموجی ممنوعه'
        },
        {
            'delay_type': 'friend_reply_delay',
            'chat_id': -1001234567890,
            'user_type': 'friend',
            'expected_max': 0.5,
            'description': 'پاسخ به دوست'
        },
        {
            'delay_type': 'enemy_spam_delay',
            'chat_id': -1001234567890,
            'user_type': 'enemy',
            'expected_max': 2.0,
            'description': 'اسپم دشمن'
        }
    ]
    
    print("🔍 تست‌های سرعت:")
    for i, test_case in enumerate(test_cases, 1):
        actual_delay = await launcher.smart_delay_with_adaptation(
            test_case['delay_type'],
            test_case['chat_id'],
            test_case['user_type']
        )
        
        status = "✅" if actual_delay <= test_case['expected_max'] else "❌"
        print(f"   {i}. {test_case['description']}: {actual_delay:.3f}s {status}")
        
        # کمی استراحت بین تست‌ها
        await asyncio.sleep(0.1)
    
    # تست ضریب چت
    print("\n🎯 تست ضریب چت:")
    chat_id = -1001111111111
    launcher.chat_specific_delays[chat_id] = {'multiplier': 0.5}  # نصف تاخیر
    
    delay_before = await launcher.smart_delay_with_adaptation('friend_reply_delay', -1001234567890, 'friend')
    delay_after = await launcher.smart_delay_with_adaptation('friend_reply_delay', chat_id, 'friend')
    
    print(f"   • چت عادی: {delay_before:.3f}s")
    print(f"   • چت با ضریب 0.5: {delay_after:.3f}s")
    print(f"   • کاهش: {((delay_before - delay_after) / delay_before * 100):.1f}%")
    
    # تست تاخیر انطباقی
    print("\n🧠 تست تاخیر انطباقی:")
    
    # شبیه‌سازی چت خلوت
    launcher.last_message_time[chat_id] = time.time() - 35  # 35 ثانیه پیش
    delay_quiet = await launcher.smart_delay_with_adaptation('global_message_delay', chat_id)
    
    # شبیه‌سازی چت پرفعالیت
    launcher.last_message_time[chat_id] = time.time() - 5   # 5 ثانیه پیش
    delay_active = await launcher.smart_delay_with_adaptation('global_message_delay', chat_id)
    
    print(f"   • چت خلوت (35s): {delay_quiet:.3f}s")
    print(f"   • چت پرفعالیت (5s): {delay_active:.3f}s")
    
    print("\n✅ تست سیستم تاخیر پیشرفته تکمیل شد!")
    print("🎯 ویژگی‌های تست شده:")
    print("   • واکنش فوری به ایموجی ممنوعه")
    print("   • تفکیک دوست/دشمن")
    print("   • ضریب تاخیر مختص چت")
    print("   • تاخیر انطباقی بر اساس فعالیت")
    print("   • کاهش هوشمند تاخیر")

if __name__ == "__main__":
    asyncio.run(test_advanced_delay_system())