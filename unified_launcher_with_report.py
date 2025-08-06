#!/usr/bin/env python3
"""
لانچر یکپارچه با سیستم گزارش‌دهی فعال
"""

import asyncio
import sys
import os
from unified_bot_launcher import UnifiedBotLauncher
from report_bot import ReportBot

class EnhancedUnifiedLauncher(UnifiedBotLauncher):
    """لانچر بهبود یافته با سیستم گزارش‌دهی"""
    
    def __init__(self):
        super().__init__()
        self.report_bot_task = None
        self.report_bot_instance = None
        
    async def start_report_system(self):
        """راه‌اندازی سیستم گزارش‌دهی"""
        try:
            print("🚀 راه‌اندازی سیستم گزارش‌دهی...")
            
            # ایجاد ربات گزارش‌دهی
            self.report_bot_instance = ReportBot()
            
            if not self.report_bot_instance.is_valid:
                print("⚠️ ربات گزارش‌دهی غیرفعال - توکن موجود نیست")
                return False
            
            # راه‌اندازی ربات گزارش‌دهی در تسک جداگانه
            success = await self.report_bot_instance.start_bot()
            
            if success:
                print("✅ سیستم گزارش‌دهی فعال شد")
                return True
            else:
                print("❌ خطا در راه‌اندازی سیستم گزارش‌دهی")
                return False
                
        except Exception as e:
            print(f"❌ خطا در سیستم گزارش‌دهی: {e}")
            return False
    
    async def send_report_safely(self, message, chat_id=None, chat_title=None, emoji="⚠️"):
        """ارسال گزارش امن"""
        try:
            if self.report_bot_instance and hasattr(self.report_bot_instance, 'client'):
                await self.report_bot_instance.send_emoji_alert(
                    chat_id=str(chat_id) if chat_id else "unknown",
                    chat_title=chat_title or "چت نامشخص", 
                    emoji=emoji,
                    stopped_bots_count=9
                )
                print(f"📤 گزارش ارسال شد: {emoji} در {chat_title}")
            else:
                print("⚠️ سیستم گزارش‌دهی در دسترس نیست")
        except Exception as e:
            print(f"❌ خطا در ارسال گزارش: {e}")
    
    async def start_all_systems(self):
        """راه‌اندازی همه سیستم‌ها"""
        print("🚀 شروع راه‌اندازی سیستم کامل...")
        
        # راه‌اندازی سیستم گزارش‌دهی
        report_started = await self.start_report_system()
        
        # راه‌اندازی سیستم اصلی
        try:
            await self.initialize_system()
            print(f"✅ سیستم راه‌اندازی شد - گزارش‌دهی: {'فعال' if report_started else 'غیرفعال'}")
            return True
        except Exception as e:
            print(f"❌ خطا در راه‌اندازی سیستم اصلی: {e}")
            return False

async def main():
    """تابع اصلی راه‌اندازی"""
    launcher = EnhancedUnifiedLauncher()
    
    try:
        await launcher.start_all_systems()
        print("🎯 همه سیستم‌ها فعال - در انتظار پیام‌ها...")
        
        # نگه داشتن سیستم زنده
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        print("\n⌨️ دریافت سیگنال توقف...")
    except Exception as e:
        print(f"❌ خطای کلی: {e}")
    finally:
        try:
            if launcher.report_bot_instance:
                await launcher.report_bot_instance.stop_bot()
            await launcher.stop_all_bots()
            print("🛑 همه سیستم‌ها متوقف شد")
        except:
            pass

if __name__ == "__main__":
    # تنظیم encoding
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    
    asyncio.run(main())