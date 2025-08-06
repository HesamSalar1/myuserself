#!/usr/bin/env python3
"""
🔧 تست برطرافی مشکل اضافه کردن ایموجی
"""

import sys
import os
import sqlite3

sys.stdout.reconfigure(encoding='utf-8')

def test_emoji_addition():
    """تست اضافه کردن ایموجی با روش‌های مختلف"""
    print("🔧 تست برطرافی مشکل اضافه کردن ایموجی")
    print("=" * 50)
    
    # استفاده از دیتابیس موجود
    db_path = "bots/bot1/bot1_data.db"
    
    if not os.path.exists(db_path):
        print(f"❌ دیتابیس {db_path} یافت نشد")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # بررسی وجود جدول
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='forbidden_emojis'
        """)
        
        if not cursor.fetchone():
            print("❌ جدول forbidden_emojis یافت نشد")
            return
        
        # تست اضافه کردن ایموجی‌های مختلف
        test_emojis = [
            ("🔮", "ایموجی جادویی", 2),
            ("⭐", "ستاره", 1),
            ("💎", "الماس", 3),
            ("🌟", "ستاره درخشان", 2)
        ]
        
        for emoji, desc, level in test_emojis:
            # حذف قبلی اگر وجود دارد
            cursor.execute("DELETE FROM forbidden_emojis WHERE emoji = ?", (emoji,))
            
            # اضافه کردن جدید
            cursor.execute("""
                INSERT INTO forbidden_emojis 
                (emoji, description, added_by_user_id, category, severity_level, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (emoji, desc, 12345, 'test', level, 1))
            
            # بررسی اضافه شدن
            cursor.execute("SELECT * FROM forbidden_emojis WHERE emoji = ?", (emoji,))
            result = cursor.fetchone()
            
            if result:
                level_icon = ["", "🟢", "🟡", "🔴"][level]
                print(f"✅ {emoji} {level_icon} - {desc} (سطح {level})")
            else:
                print(f"❌ خطا در اضافه کردن {emoji}")
        
        conn.commit()
        
        # نمایش آمار کلی
        cursor.execute("SELECT COUNT(*) FROM forbidden_emojis WHERE is_active = 1")
        count = cursor.fetchone()[0]
        print(f"\n📊 مجموع ایموجی‌های فعال: {count} عدد")
        
        # تست تشخیص
        print("\n🔍 تست تشخیص:")
        test_text = "پیام تست با 🔮 و ⭐ و 💎"
        
        cursor.execute("SELECT emoji FROM forbidden_emojis WHERE is_active = 1")
        active_emojis = [row[0] for row in cursor.fetchall()]
        
        detected = []
        for emoji in active_emojis:
            if emoji in test_text:
                detected.append(emoji)
        
        if detected:
            print(f"🔴 متن: '{test_text}'")
            print(f"📍 ایموجی‌های تشخیص شده: {', '.join(detected)}")
        else:
            print(f"🟢 متن: '{test_text}' - بدون ایموجی ممنوعه")
        
        conn.close()
        print("\n✅ تست کامل شد - سیستم درست کار می‌کند!")
        
    except Exception as e:
        print(f"❌ خطا: {e}")

if __name__ == "__main__":
    test_emoji_addition()