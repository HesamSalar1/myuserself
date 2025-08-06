#!/usr/bin/env python3
"""
تست سیستم گزارش‌دهی - بررسی عملکرد ربات گزارش
"""

import asyncio
import os
import sys
from report_bot import ReportBot, send_emoji_report

async def test_report_bot():
    """تست کامل سیستم گزارش‌دهی"""
    print("🚀 شروع تست سیستم گزارش‌دهی...")
    
    # بررسی توکن
    token = os.getenv('REPORT_BOT_TOKEN', '')
    if not token:
        print("❌ توکن REPORT_BOT_TOKEN یافت نشد!")
        return False
    
    print(f"✅ توکن یافت شد: {token[:20]}...")
    
    try:
        # ایجاد ربات گزارش‌دهی
        report_bot = ReportBot()
        
        if not report_bot.is_valid:
            print("❌ ربات گزارش‌دهی نامعتبر است")
            return False
        
        print("✅ ربات گزارش‌دهی معتبر است")
        
        # تست راه‌اندازی
        print("📡 در حال راه‌اندازی ربات...")
        success = await report_bot.start_bot()
        
        if success:
            print("✅ ربات گزارش‌دهی با موفقیت راه‌اندازی شد")
            
            # تست ارسال گزارش تست
            print("📤 در حال ارسال گزارش تست...")
            await report_bot.send_emoji_alert(
                chat_id="-1001234567890",
                chat_title="گروه تست سیستم",
                emoji="🧪",
                stopped_bots_count=9
            )
            print("✅ گزارش تست ارسال شد")
            
            # توقف ربات
            await report_bot.stop_bot()
            print("🛑 ربات گزارش‌دهی متوقف شد")
            
            return True
        else:
            print("❌ خطا در راه‌اندازی ربات گزارش‌دهی")
            return False
            
    except Exception as e:
        print(f"❌ خطای کلی در تست: {e}")
        return False

async def test_external_report_function():
    """تست تابع خارجی ارسال گزارش"""
    print("\n🔄 تست تابع گزارش خارجی...")
    
    try:
        await send_emoji_report(
            chat_id="-1001987654321",
            chat_title="تست تابع خارجی",
            emoji="🔧",
            stopped_bots_count=5
        )
        print("✅ تابع گزارش خارجی کار می‌کند")
        return True
    except Exception as e:
        print(f"❌ خطا در تابع گزارش خارجی: {e}")
        return False

async def main():
    """تابع اصلی تست"""
    print("="*50)
    print("🧪 تست کامل سیستم گزارش‌دهی")
    print("="*50)
    
    # تست ربات گزارش‌دهی
    test1_result = await test_report_bot()
    
    # تست تابع خارجی
    test2_result = await test_external_report_function()
    
    print("\n" + "="*50)
    print("📊 نتایج تست:")
    print(f"   ربات گزارش‌دهی: {'✅ موفق' if test1_result else '❌ ناموفق'}")
    print(f"   تابع گزارش خارجی: {'✅ موفق' if test2_result else '❌ ناموفق'}")
    
    if test1_result and test2_result:
        print("\n🎉 همه تست‌ها موفق - سیستم گزارش‌دهی آماده!")
        return True
    else:
        print("\n⚠️ برخی تست‌ها ناموفق - نیاز به بررسی")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⌨️ تست توسط کاربر متوقف شد")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 خطای غیرمنتظره: {e}")
        sys.exit(1)