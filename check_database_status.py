#!/usr/bin/env python3
"""
بررسی وضعیت پایگاه داده و ایموجی‌های ممنوعه
"""

import sys
import sqlite3
import os
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

def check_database_status():
    """بررسی وضعیت پایگاه داده"""
    print("🔍 بررسی وضعیت پایگاه داده ربات‌ها")
    print("="*60)
    
    # بررسی همه دیتابیس‌های بات‌ها
    bot_databases = [
        "bots/bot1/bot1_data.db",
        "bots/bot2/bot2_data.db", 
        "bots/bot3/bot3_data.db",
        "bots/bot4/bot4_data.db",
        "bots/bot5/bot5_data.db",
        "bots/bot6/bot6_data.db",
        "bots/bot7/bot7_data.db",
        "bots/bot8/bot8_data.db",
        "bots/bot9/bot9_data.db"
    ]
    
    for i, db_path in enumerate(bot_databases, 1):
        print(f"\n📊 بات {i}: {db_path}")
        
        if not os.path.exists(db_path):
            print(f"   ❌ دیتابیس وجود ندارد")
            continue
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # بررسی جدول ایموجی‌های ممنوعه
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='forbidden_emojis'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM forbidden_emojis")
                emoji_count = cursor.fetchone()[0]
                print(f"   ✅ جدول forbidden_emojis: {emoji_count} ایموجی")
                
                # نمایش چند ایموجی اول
                cursor.execute("SELECT emoji FROM forbidden_emojis LIMIT 5")
                emojis = cursor.fetchall()
                if emojis:
                    emoji_list = [emoji[0] for emoji in emojis]
                    print(f"   📋 نمونه ایموجی‌ها: {emoji_list}")
            else:
                print(f"   ❌ جدول forbidden_emojis وجود ندارد")
            
            # بررسی جدول‌های اصلی
            tables = ['fosh_list', 'enemy_list', 'friend_list', 'friend_words']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   📊 {table}: {count} رکورد")
            
            conn.close()
            
        except Exception as e:
            print(f"   ❌ خطا: {e}")
    
    # بررسی دیتابیس ربات گزارش‌دهی
    print(f"\n📢 ربات گزارش‌دهی: report_bot.db")
    
    if os.path.exists("report_bot.db"):
        try:
            conn = sqlite3.connect("report_bot.db")
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM subscribers")
            subscribers = cursor.fetchone()[0]
            print(f"   👥 مشترکین: {subscribers}")
            
            cursor.execute("SELECT COUNT(*) FROM emoji_reports")
            reports = cursor.fetchone()[0]
            print(f"   📊 گزارش‌ها: {reports}")
            
            # آخرین گزارش‌ها
            cursor.execute("SELECT chat_title, emoji, reported_at FROM emoji_reports ORDER BY reported_at DESC LIMIT 3")
            recent_reports = cursor.fetchall()
            
            if recent_reports:
                print(f"   📋 آخرین گزارش‌ها:")
                for report in recent_reports:
                    title, emoji, timestamp = report
                    print(f"      - {emoji} در {title} ({timestamp})")
            
            conn.close()
            
        except Exception as e:
            print(f"   ❌ خطا: {e}")
    else:
        print(f"   ❌ دیتابیس وجود ندارد")

def show_emoji_unicode_info():
    """نمایش اطلاعات Unicode ایموجی‌ها"""
    print(f"\n🔤 اطلاعات Unicode ایموجی‌های ممنوعه")
    print("="*60)
    
    try:
        conn = sqlite3.connect("bots/bot1/bot1_data.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT emoji FROM forbidden_emojis")
        emojis = cursor.fetchall()
        
        for i, (emoji,) in enumerate(emojis[:10], 1):  # فقط 10 تای اول
            unicode_codes = [f"U+{ord(c):04X}" for c in emoji]
            print(f"{i:2d}. {emoji} → {' '.join(unicode_codes)}")
            
        if len(emojis) > 10:
            print(f"    ... و {len(emojis) - 10} ایموجی دیگر")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ خطا: {e}")

def main():
    """تابع اصلی"""
    print("🔧 بررسی وضعیت سیستم پایگاه داده")
    print("="*60)
    print(f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_database_status()
    show_emoji_unicode_info()
    
    print("\n✅ بررسی کامل شد!")

if __name__ == "__main__":
    main()