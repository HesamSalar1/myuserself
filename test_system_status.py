
#!/usr/bin/env python3
"""
تست سریع وضعیت سیستم
"""

import asyncio
import sqlite3
import os
import subprocess
import sys

async def test_system():
    print("🔍 تست وضعیت سیستم...")
    
    # 1. بررسی دیتابیس بات‌ها
    print("\n📊 بررسی دیتابیس‌ها:")
    for i in range(1, 10):
        db_path = f"bots/bot{i}/bot{i}_data.db"
        if os.path.exists(db_path):
            print(f"✅ بات {i}: دیتابیس موجود")
            
            # بررسی داده‌های نمونه
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM fosh_list")
                fosh_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM enemy_list")
                enemy_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM friend_list")
                friend_count = cursor.fetchone()[0]
                
                conn.close()
                
                print(f"   └ فحش‌ها: {fosh_count}, دشمنان: {enemy_count}, دوستان: {friend_count}")
                
            except Exception as e:
                print(f"   └ ❌ خطا در خواندن دیتابیس: {e}")
        else:
            print(f"❌ بات {i}: دیتابیس موجود نیست")
    
    # 2. بررسی session فایل‌ها
    print("\n🔐 بررسی session فایل‌ها:")
    for i in range(1, 10):
        session_path = f"bots/bot{i}/my_bot{i}.session"
        if os.path.exists(session_path):
            print(f"✅ بات {i}: session موجود")
        else:
            print(f"❌ بات {i}: session موجود نیست")
    
    # 3. بررسی ایموجی‌های ممنوعه
    print("\n🚫 بررسی ایموجی‌های ممنوعه:")
    try:
        db_path = "bots/bot1/bot_database.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT emoji FROM forbidden_emojis")
            emojis = cursor.fetchall()
            conn.close()
            
            print(f"✅ {len(emojis)} ایموجی ممنوعه یافت شد:")
            for emoji in emojis[:5]:  # نمایش 5 تای اول
                print(f"   └ {emoji[0]}")
            if len(emojis) > 5:
                print(f"   └ ... و {len(emojis)-5} مورد دیگر")
        else:
            print("❌ دیتابیس ایموجی‌های ممنوعه موجود نیست")
    except Exception as e:
        print(f"❌ خطا در بررسی ایموجی‌ها: {e}")
    
    # 4. بررسی پنل وب
    print("\n🌐 بررسی پنل وب:")
    if os.path.exists("package.json"):
        print("✅ package.json موجود")
        try:
            # تست npm
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ npm نسخه: {result.stdout.strip()}")
            else:
                print("❌ npm در دسترس نیست")
        except Exception as e:
            print(f"❌ خطا در بررسی npm: {e}")
    else:
        print("❌ package.json موجود نیست")
    
    # 5. بررسی ربات مانیتورینگ
    print("\n🤖 بررسی ربات مانیتورینگ:")
    if os.path.exists("monitoring_bot.py"):
        print("✅ ربات مانیتورینگ موجود")
        if os.path.exists("monitoring_bot.db"):
            print("✅ دیتابیس مانیتورینگ موجود")
        else:
            print("⚠️ دیتابیس مانیتورینگ موجود نیست")
    else:
        print("❌ ربات مانیتورینگ موجود نیست")
    
    print("\n" + "="*50)
    print("🎯 خلاصه تست:")
    print("اگر همه چیز سبز (✅) است، سیستم باید کار کند")
    print("برای مشکلات قرمز (❌)، نیاز به رفع مشکل دارید")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(test_system())
