#!/usr/bin/env python3
"""
راه‌اندازی فقط ربات گزارش‌دهی تلگرام
ساده و بدون پیچیدگی
"""

import asyncio
import signal
import sys
import os
from report_bot import ReportBot

def signal_handler(signum, frame):
    print("\n🛑 خروج...")
    sys.exit(0)

async def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("🤖 ربات گزارش‌دهی تلگرام")
    print("=" * 60)
    print("📱 نام کاربری: @SelfSpam_Bot")
    print("🆔 شناسه: 7708355228")
    print("🔑 توکن: 7708355228:AAGPzhm47U5-4uPnALl6Oc6En91aCYLyydk")
    print("=" * 60)
    
    # بررسی توکن
    token = os.getenv('REPORT_BOT_TOKEN', '').strip()
    if not token:
        print("❌ توکن ربات موجود نیست!")
        print("💡 لطفاً REPORT_BOT_TOKEN را در Secrets تنظیم کنید")
        return 1
    
    print("✅ توکن ربات یافت شد")
    print("🚀 راه‌اندازی...")
    print()
    
    bot = ReportBot()
    
    if not bot.is_valid:
        print("❌ ربات نامعتبر")
        return 1
    
    try:
        success = await bot.start_bot()
        
        if success:
            print("✅ ربات گزارش‌دهی آماده است!")
            print()
            print("📋 عملکرد:")
            print("  • کاربران با /start عضو می‌شوند")
            print("  • گزارش‌های ایموجی ممنوعه ارسال می‌شود")
            print("  • وضعیت سیستم با /status قابل مشاهده است")
            print()
            print("⏹️  برای توقف: Ctrl+C")
            print("=" * 60)
            
            # اجرای دائمی
            await asyncio.Future()
            
        else:
            print("❌ خطا در راه‌اندازی ربات")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 توقف توسط کاربر")
    except Exception as e:
        print(f"❌ خطا: {e}")
        return 1
    finally:
        try:
            await bot.stop_bot()
            print("✅ ربات متوقف شد")
        except:
            pass
    
    return 0

if __name__ == "__main__":
    print()
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\n🛑 خروج")
        sys.exit(0)