#!/usr/bin/env python3
"""
اسکریپت راه‌اندازی مجدد ربات‌ها با سیستم بهبود یافته ایموجی‌های ممنوعه
"""

import os
import sys
import signal
import time
import psutil
import asyncio
from unified_bot_launcher import UnifiedBotLauncher

def kill_existing_bots():
    """کشتن تمام ربات‌های در حال اجرا"""
    print("🔄 جستجو برای ربات‌های در حال اجرا...")
    
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any('python' in cmd and ('unified_bot_launcher' in cmd or 'main.py' in cmd) for cmd in cmdline):
                print(f"⚡ کشتن پروسه: {proc.info['pid']} - {' '.join(cmdline)}")
                proc.terminate()
                killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if killed_count > 0:
        print(f"✅ {killed_count} پروسه ربات کشته شد")
        time.sleep(3)  # صبر برای تمام شدن پروسه‌ها
    else:
        print("ℹ️ هیچ ربات فعالی یافت نشد")

def check_emoji_system():
    """بررسی سیستم ایموجی قبل از راه‌اندازی"""
    print("\n🔍 بررسی سیستم ایموجی‌های ممنوعه...")
    
    launcher = UnifiedBotLauncher()
    
    # بارگذاری ایموجی‌ها از دیتابیس
    emojis = launcher.load_forbidden_emojis_from_db()
    
    print(f"📊 تعداد ایموجی‌های بارگذاری شده: {len(emojis)}")
    
    required_emojis = ["⚡", "⚡️"]
    missing_emojis = []
    
    for emoji in required_emojis:
        if emoji in emojis:
            print(f"✅ ایموجی '{emoji}' موجود است")
        else:
            print(f"❌ ایموجی '{emoji}' موجود نیست")
            missing_emojis.append(emoji)
    
    # اضافه کردن ایموجی‌های گمشده
    if missing_emojis:
        print(f"\n🔧 اضافه کردن ایموجی‌های گمشده...")
        for emoji in missing_emojis:
            if launcher.add_forbidden_emoji_to_db(emoji):
                print(f"✅ ایموجی '{emoji}' اضافه شد")
            else:
                print(f"⚠️ ایموجی '{emoji}' قبلاً موجود بود")
        
        # بارگذاری مجدد
        emojis = launcher.load_forbidden_emojis_from_db()
        launcher.forbidden_emojis = emojis
    
    # تست عملکرد
    test_text = "A CHARACTER HAS SPAWNED IN THE CHAT ⚡"
    if launcher.contains_stop_emoji(test_text):
        print(f"✅ سیستم تشخیص ایموجی کار می‌کند: '{test_text}'")
        return True
    else:
        print(f"❌ سیستم تشخیص ایموجی کار نمی‌کند: '{test_text}'")
        return False

async def start_bots_with_new_system():
    """راه‌اندازی ربات‌ها با سیستم جدید"""
    print("\n🚀 راه‌اندازی ربات‌ها با سیستم بهبود یافته...")
    
    launcher = UnifiedBotLauncher()
    
    # بارگذاری ایموجی‌های ممنوعه
    launcher.forbidden_emojis = launcher.load_forbidden_emojis_from_db()
    
    print(f"📥 {len(launcher.forbidden_emojis)} ایموجی ممنوعه بارگذاری شد")
    
    try:
        # راه‌اندازی همه ربات‌ها
        await launcher.start_all_bots()
        print("✅ همه ربات‌ها با سیستم جدید راه‌اندازی شدند")
        
        # نمایش وضعیت
        status = launcher.get_status()
        print(f"\n📊 وضعیت ربات‌ها:")
        for bot_id, info in status.items():
            status_text = "🟢 فعال" if info['running'] else "🔴 غیرفعال"
            print(f"  بات {bot_id}: {status_text}")
        
        print("\n🛡️ سیستم ایموجی‌های ممنوعه آماده:")
        print("  - هر کاربری (شامل ربات‌ها) که ایموجی ممنوعه فرستادند، همه ربات‌ها متوقف می‌شوند")
        print("  - فقط پیام دشمنان می‌تواند سیستم را مجدداً فعال کند")
        
        # اجرای بی‌نهایت
        print("\n🔄 ربات‌ها در حال اجرا... (Ctrl+C برای توقف)")
        try:
            while True:
                await asyncio.sleep(60)
                # بررسی وضعیت هر دقیقه
                running_count = sum(1 for info in launcher.get_status().values() if info['running'])
                print(f"💻 {running_count} ربات فعال - {time.strftime('%H:%M:%S')}")
        except KeyboardInterrupt:
            print("\n⏹️ درخواست توقف دریافت شد...")
            await launcher.stop_all_bots()
            print("✅ همه ربات‌ها متوقف شدند")
            
    except Exception as e:
        print(f"❌ خطا در راه‌اندازی: {e}")

def main():
    print("🔧 راه‌اندازی مجدد ربات‌ها با سیستم بهبود یافته ایموجی‌های ممنوعه")
    print("=" * 80)
    
    # مرحله 1: کشتن ربات‌های قدیمی
    kill_existing_bots()
    
    # مرحله 2: بررسی سیستم ایموجی
    if not check_emoji_system():
        print("❌ سیستم ایموجی درست کار نمی‌کند. لطفاً مشکل را بررسی کنید.")
        return
    
    # مرحله 3: راه‌اندازی ربات‌ها
    try:
        asyncio.run(start_bots_with_new_system())
    except KeyboardInterrupt:
        print("\n👋 خروج از برنامه")

if __name__ == "__main__":
    main()