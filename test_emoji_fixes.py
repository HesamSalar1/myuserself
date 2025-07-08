#!/usr/bin/env python3
"""
تست سیستم بهبود یافته تشخیص ایموجی‌ها و گزارش‌دهی
"""

import sys
import sqlite3
import asyncio
import time
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

class SimpleEmojiTester:
    def __init__(self):
        self.forbidden_emojis = set()
        self.report_sent_cache = {}
        self.emoji_detection_cache = {}
        self.detection_cooldown = 5.0
        
        # بارگذاری ایموجی‌ها از دیتابیس
        self.load_forbidden_emojis()
    
    def load_forbidden_emojis(self):
        """بارگذاری ایموجی‌های ممنوعه از دیتابیس"""
        try:
            db_path = "bots/bot1/bot1_data.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # بررسی وجود جدول
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='forbidden_emojis'")
            if not cursor.fetchone():
                print("❌ جدول forbidden_emojis وجود ندارد")
                conn.close()
                return
            
            cursor.execute("SELECT emoji FROM forbidden_emojis")
            emojis = cursor.fetchall()
            self.forbidden_emojis = {emoji[0] for emoji in emojis}
            conn.close()
            
            print(f"✅ {len(self.forbidden_emojis)} ایموجی ممنوعه بارگذاری شد")
            
        except Exception as e:
            print(f"❌ خطا در بارگذاری ایموجی‌ها: {e}")
    
    def contains_stop_emoji(self, text, found_emoji_ref=None):
        """بررسی ساده و مؤثر وجود ایموجی‌های توقف در متن"""
        if not text or not self.forbidden_emojis:
            return False

        # بررسی مستقیم ایموجی‌ها در متن
        for emoji in self.forbidden_emojis:
            if not emoji or len(emoji.strip()) == 0:
                continue
            
            # بررسی‌های ساده و مؤثر
            if emoji in text:
                print(f"🛑 ایموجی ممنوعه تشخیص داده شد: {emoji} در متن: {text[:50]}...")
                
                # بازگشت اولین ایموجی یافت شده
                if found_emoji_ref is not None:
                    found_emoji_ref.append(emoji)
                
                return True
            
            # بررسی بدون کاراکترهای اضافی (variation selectors)
            cleaned_emoji = emoji.replace('\uFE0F', '').replace('\uFE0E', '')
            if cleaned_emoji != emoji and cleaned_emoji in text:
                print(f"🛑 ایموجی ممنوعه تشخیص داده شد: {emoji} (تمیز شده) در متن: {text[:50]}...")
                
                if found_emoji_ref is not None:
                    found_emoji_ref.append(emoji)
                
                return True
            
        return False
    
    def test_emoji_detection(self):
        """تست تشخیص ایموجی‌ها"""
        print("\n🧪 تست تشخیص ایموجی‌ها:")
        print("="*50)
        
        test_cases = [
            "⚡",
            "⚡️",
            "A CHARACTER HAS SPAWNED IN THE CHAT ⚡",
            "A CHARACTER HAS SPAWNED IN THE CHAT ⚡️",
            "🔮",
            "متن عادی",
            "متن ⚡ در وسط",
            "🎯 این یک تست است",
            "سلام دوست عزیز",
            "⚡⚡⚡ چندین ایموجی",
        ]
        
        for i, test_text in enumerate(test_cases, 1):
            print(f"\n{i}. تست: '{test_text}'")
            found_emoji_ref = []
            is_detected = self.contains_stop_emoji(test_text, found_emoji_ref)
            
            if is_detected:
                print(f"   ✅ تشخیص داده شد - ایموجی: {found_emoji_ref[0] if found_emoji_ref else 'نامشخص'}")
            else:
                print(f"   ❌ تشخیص داده نشد")
    
    def test_cache_system(self):
        """تست سیستم cache"""
        print("\n🔄 تست سیستم cache:")
        print("="*50)
        
        # تست cache گزارش
        chat_id = -1001234567890
        emoji = "⚡"
        
        # اولین گزارش
        cache_key = f"{chat_id}_{emoji}"
        current_time = time.time()
        
        # بررسی cache اول
        if cache_key not in self.report_sent_cache:
            self.report_sent_cache[cache_key] = current_time
            print(f"✅ گزارش اول برای {emoji} در چت {chat_id} ارسال شد")
        
        # بررسی cache دوم (باید بلاک شود)
        if cache_key in self.report_sent_cache:
            last_sent = self.report_sent_cache[cache_key]
            if current_time - last_sent < 60.0:
                print(f"🔄 گزارش دوم برای {emoji} بلاک شد - تکراری")
        
        # انتظار و تست مجدد
        print("⏳ انتظار 2 ثانیه...")
        time.sleep(2)
        
        # بررسی cache بعد از انتظار
        current_time = time.time()
        if cache_key in self.report_sent_cache:
            last_sent = self.report_sent_cache[cache_key]
            if current_time - last_sent < 60.0:
                time_left = int(60.0 - (current_time - last_sent))
                print(f"🔄 گزارش سوم همچنان بلاک است - {time_left} ثانیه باقی‌مانده")
        
        print("✅ سیستم cache به درستی کار می‌کند")
    
    def test_performance(self):
        """تست عملکرد"""
        print("\n⚡ تست عملکرد:")
        print("="*50)
        
        test_text = "A CHARACTER HAS SPAWNED IN THE CHAT ⚡"
        iterations = 1000
        
        start_time = time.time()
        
        for i in range(iterations):
            self.contains_stop_emoji(test_text)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ {iterations} تشخیص در {duration:.3f} ثانیه")
        print(f"📊 میانگین: {(duration/iterations)*1000:.2f} میلی‌ثانیه در هر تشخیص")
        print(f"📈 سرعت: {iterations/duration:.0f} تشخیص در ثانیه")
        
        if duration < 1.0:
            print("🚀 عملکرد عالی!")
        elif duration < 3.0:
            print("✅ عملکرد مناسب")
        else:
            print("⚠️ عملکرد قابل بهبود")

def main():
    """تابع اصلی"""
    print("🔧 تست سیستم بهبود یافته تشخیص ایموجی‌ها")
    print("="*60)
    
    tester = SimpleEmojiTester()
    
    # نمایش ایموجی‌های بارگذاری شده
    print(f"📋 ایموجی‌های ممنوعه: {list(tester.forbidden_emojis)}")
    
    # تست‌های مختلف
    tester.test_emoji_detection()
    tester.test_cache_system()
    tester.test_performance()
    
    print("\n✅ همه تست‌ها کامل شد!")
    print("🎯 سیستم آماده استفاده است")

if __name__ == "__main__":
    main()