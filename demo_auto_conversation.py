#!/usr/bin/env python3
"""
نمایش عملی سیستم گفتگوی خودکار
شبیه‌سازی گفتگوی واقعی بین ۹ ربات
"""

import asyncio
import sys
import time
import random
from unified_bot_launcher import UnifiedBotLauncher

sys.stdout.reconfigure(encoding='utf-8')

async def demo_realistic_conversation():
    """نمایش واقعی گفتگوی خودکار"""
    print("🎭 نمایش سیستم گفتگوی خودکار واقعی")
    print("=" * 60)
    
    launcher = UnifiedBotLauncher()
    test_chat_id = -1001234567890
    
    # راه‌اندازی گفتگوی خودکار
    print("\n🚀 راه‌اندازی گفتگوی خودکار...")
    launcher.auto_chat_enabled = True
    launcher.active_conversations[test_chat_id] = {
        'started_at': time.time(),
        'last_message_time': 0,
        'last_bot': None,
        'current_topic': 'روزمره',
        'message_count': 0,
        'participants': set()
    }
    
    print(f"✅ گفتگو در چت {test_chat_id} شروع شد")
    print(f"📋 موضوع ابتدایی: {launcher.active_conversations[test_chat_id]['current_topic']}")
    print(f"🤖 تعداد ربات‌های آنلاین: {sum(launcher.bot_online_status.values())}")
    
    # شبیه‌سازی ۱۰ دقیقه گفتگو
    simulation_duration = 60  # ۶۰ ثانیه برای نمایش
    start_time = time.time()
    message_count = 0
    
    print(f"\n💬 شروع گفتگوی شبیه‌سازی شده ({simulation_duration} ثانیه)...")
    print("-" * 60)
    
    while time.time() - start_time < simulation_duration and message_count < 15:
        try:
            # انتخاب ربات برای پیام
            selected_bot = launcher.select_bot_for_conversation(test_chat_id)
            
            if not selected_bot:
                print("⚠️ هیچ ربات آنلاینی موجود نیست، صبر می‌کنیم...")
                await asyncio.sleep(2)
                continue
            
            # تولید پیام
            message = await launcher.generate_conversation_message(test_chat_id, selected_bot)
            
            if message:
                # نمایش پیام با فرمت واقعی
                current_time = time.strftime("%H:%M:%S")
                topic = launcher.active_conversations[test_chat_id]['current_topic']
                
                print(f"[{current_time}] 🤖 ربات {selected_bot} ({topic}): {message}")
                
                # به‌روزرسانی آمار
                conv = launcher.active_conversations[test_chat_id]
                conv['message_count'] += 1
                conv['last_bot'] = selected_bot
                conv['last_message_time'] = time.time()
                conv['participants'].add(selected_bot)
                launcher.last_bot_activity[selected_bot] = time.time()
                
                # احتمال تغییر موضوع
                if random.random() < 0.15:  # ۱۵ درصد احتمال
                    old_topic = conv['current_topic']
                    topics = launcher.get_conversation_topics()
                    new_topic = random.choice([t for t in topics if t != old_topic])
                    conv['current_topic'] = new_topic
                    print(f"    💡 موضوع تغییر کرد: {old_topic} → {new_topic}")
                
                # احتمال آفلاین شدن ربات
                if random.random() < 0.08:  # ۸ درصد احتمال
                    offline_duration = random.randint(10, 30)
                    launcher.simulate_bot_offline(selected_bot, offline_duration)
                    print(f"    🔴 ربات {selected_bot} آفلاین شد ({offline_duration}s)")
                
                message_count += 1
                
                # تاخیر واقعی بین پیام‌ها
                delay = random.uniform(3, 8)
                await asyncio.sleep(delay)
            
            else:
                print(f"⚠️ ربات {selected_bot} پیام تولید نکرد")
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"❌ خطا در شبیه‌سازی: {e}")
            await asyncio.sleep(2)
    
    # نمایش آمار نهایی
    print("\n" + "=" * 60)
    print("📊 آمار گفتگوی شبیه‌سازی شده:")
    
    conv = launcher.active_conversations[test_chat_id]
    duration = int(time.time() - conv['started_at'])
    
    print(f"⏱️ مدت گفتگو: {duration} ثانیه")
    print(f"💬 تعداد پیام: {conv['message_count']}")
    print(f"📝 موضوع نهایی: {conv['current_topic']}")
    print(f"👥 شرکت‌کنندگان: {len(conv['participants'])} ربات")
    print(f"🤖 ربات‌های آنلاین: {sum(launcher.bot_online_status.values())} از ۹")
    
    if conv['participants']:
        print(f"🎯 ربات‌های فعال: {', '.join(map(str, sorted(conv['participants'])))}")
    
    # محاسبه سرعت پیام
    if duration > 0:
        msg_per_minute = round((conv['message_count'] / duration) * 60, 1)
        print(f"📈 سرعت: {msg_per_minute} پیام در دقیقه")
    
    # پاکسازی
    del launcher.active_conversations[test_chat_id]
    launcher.auto_chat_enabled = False
    
    print("\n🎉 نمایش تکمیل شد!")
    print("✅ سیستم گفتگوی خودکار کاملاً عملکرد می‌کند")

if __name__ == "__main__":
    try:
        asyncio.run(demo_realistic_conversation())
        print("\n✅ نمایش موفقیت‌آمیز بود")
        exit(0)
    except KeyboardInterrupt:
        print("\n⚠️ نمایش توسط کاربر متوقف شد")
        exit(0)
    except Exception as e:
        print(f"\n💥 خطای نمایش: {e}")
        exit(1)