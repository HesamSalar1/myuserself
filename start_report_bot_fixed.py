#!/usr/bin/env python3
"""
راه‌اندازی ربات گزارش‌دهی با API credentials تعمیر شده
"""

import asyncio
from report_bot import ReportBot

async def main():
    """راه‌اندازی ربات گزارش‌دهی"""
    print("🚀 شروع ربات گزارش‌دهی...")
    
    bot = ReportBot()
    
    if not bot.is_valid:
        print("❌ ربات نامعتبر - توکن موجود نیست")
        return
    
    try:
        success = await bot.start_bot()
        if success:
            print("✅ ربات گزارش‌دهی راه‌اندازی شد")
            print("📧 ربات آماده دریافت کاربران جدید با دستور /start")
            print("🔄 در انتظار پیام‌ها... (Ctrl+C برای توقف)")
            
            # نگه داشتن ربات زنده
            await asyncio.Event().wait()
            
        else:
            print("❌ خطا در راه‌اندازی ربات")
            
    except KeyboardInterrupt:
        print("\n⌨️ دریافت سیگنال توقف...")
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
    finally:
        await bot.stop_bot()
        print("🛑 ربات گزارش‌دهی متوقف شد")

if __name__ == "__main__":
    asyncio.run(main())