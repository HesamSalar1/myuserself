#!/usr/bin/env python3
"""
راه‌اندازی ربات گزارش‌دهی
"""

import asyncio
import signal
import sys
from report_bot import ReportBot

def signal_handler(signum, frame):
    """مدیریت سیگنال‌های سیستم"""
    print("\n🛑 دریافت سیگنال توقف...")
    sys.exit(0)

async def main():
    """تابع اصلی"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 راه‌اندازی ربات گزارش‌دهی...")
    print("📞 نام کاربری: @SelfSpam_Bot")
    print("🆔 توکن: 7708355228:AAGPzhm47U5-4uPnALl6Oc6En91aCYLyydk")
    print("=" * 50)
    
    bot = ReportBot()
    
    try:
        success = await bot.start_bot()
        if success:
            print("✅ ربات گزارش‌دهی آماده است!")
            print("💬 کاربران می‌توانند با /start عضو شوند")
            print("🔔 گزارش‌های ایموجی ممنوعه ارسال خواهد شد")
            print("⏹️  برای توقف Ctrl+C بزنید")
            
            # Run forever
            await asyncio.Future()
        else:
            print("❌ خطا در راه‌اندازی ربات گزارش‌دهی")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 توقف ربات توسط کاربر...")
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
        return 1
    finally:
        await bot.stop_bot()
        print("✅ ربات گزارش‌دهی متوقف شد")
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))