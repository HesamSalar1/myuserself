#!/usr/bin/env python3
"""
🔧 برطرافی مشکل ساختار دیتابیس و اضافه کردن ستون‌های جدید
"""

import sys
import os
import sqlite3

sys.stdout.reconfigure(encoding='utf-8')

def fix_database_schema():
    """برطرافی ساختار دیتابیس"""
    print("🔧 برطرافی مشکل ساختار دیتابیس")
    print("=" * 50)
    
    # لیست دیتابیس‌های بات‌ها
    db_paths = []
    for i in range(1, 10):
        db_path = f"bots/bot{i}/bot{i}_data.db"
        if os.path.exists(db_path):
            db_paths.append(db_path)
    
    if not db_paths:
        print("❌ هیچ دیتابیسی یافت نشد")
        return
    
    print(f"📋 یافت شد: {len(db_paths)} دیتابیس")
    
    for db_path in db_paths:
        print(f"\n🔧 برطرافی {db_path}...")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # بررسی ساختار فعلی جدول
            cursor.execute("PRAGMA table_info(forbidden_emojis)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"   📊 ستون‌های موجود: {', '.join(columns)}")
            
            # لیست ستون‌های مورد نیاز
            required_columns = [
                ('description', 'TEXT'),
                ('severity_level', 'INTEGER DEFAULT 1'),
                ('added_by_user_id', 'INTEGER'),
                ('added_by_username', 'TEXT'),
                ('category', 'TEXT DEFAULT "custom"'),
                ('auto_pause', 'BOOLEAN DEFAULT 1'),
                ('notification_enabled', 'BOOLEAN DEFAULT 1'),
                ('unicode_variants', 'TEXT'),
                ('trigger_count', 'INTEGER DEFAULT 0'),
                ('last_triggered', 'DATETIME'),
                ('notes', 'TEXT'),
                ('tags', 'TEXT'),
                ('is_active', 'BOOLEAN DEFAULT 1'),
                ('updated_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
            ]
            
            # اضافه کردن ستون‌های جدید
            added_columns = []
            for col_name, col_type in required_columns:
                if col_name not in columns:
                    try:
                        cursor.execute(f"ALTER TABLE forbidden_emojis ADD COLUMN {col_name} {col_type}")
                        added_columns.append(col_name)
                    except Exception as e:
                        if "duplicate column name" not in str(e).lower():
                            print(f"   ⚠️ خطا در اضافه کردن {col_name}: {e}")
            
            if added_columns:
                print(f"   ✅ ستون‌های جدید: {', '.join(added_columns)}")
            else:
                print(f"   ✅ همه ستون‌ها موجود هستند")
            
            # بررسی و ایجاد جدول کلمات ممنوعه
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS forbidden_words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT UNIQUE NOT NULL,
                    description TEXT,
                    added_by_user_id INTEGER,
                    added_by_username TEXT,
                    category TEXT DEFAULT 'custom',
                    severity_level INTEGER DEFAULT 1,
                    case_sensitive BOOLEAN DEFAULT 0,
                    partial_match BOOLEAN DEFAULT 1,
                    word_boundaries BOOLEAN DEFAULT 1,
                    regex_pattern TEXT,
                    auto_pause BOOLEAN DEFAULT 1,
                    notification_enabled BOOLEAN DEFAULT 1,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_triggered DATETIME,
                    trigger_count INTEGER DEFAULT 0,
                    notes TEXT,
                    tags TEXT
                )
            """)
            
            print(f"   ✅ جدول forbidden_words آماده شد")
            
            conn.commit()
            conn.close()
            
            print(f"   ✅ {db_path} برطرف شد")
            
        except Exception as e:
            print(f"   ❌ خطا در {db_path}: {e}")
    
    print("\n✅ برطرافی دیتابیس‌ها تکمیل شد!")
    print("🎯 حالا می‌توانید ایموجی و کلمات را اضافه کنید")

def test_emoji_addition_fixed():
    """تست اضافه کردن ایموجی بعد از برطرافی"""
    print("\n🔍 تست اضافه کردن ایموجی...")
    
    db_path = "bots/bot1/bot1_data.db"
    if not os.path.exists(db_path):
        print("❌ دیتابیس یافت نشد")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # تست اضافه کردن 🔮
        test_emoji = "🔮"
        
        # حذف قبلی
        cursor.execute("DELETE FROM forbidden_emojis WHERE emoji = ?", (test_emoji,))
        
        # اضافه کردن جدید
        cursor.execute("""
            INSERT INTO forbidden_emojis 
            (emoji, description, severity_level, added_by_user_id, added_by_username, category, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (test_emoji, "ایموجی جادویی تست", 2, 12345, "تستر", "test", 1))
        
        # بررسی
        cursor.execute("SELECT * FROM forbidden_emojis WHERE emoji = ?", (test_emoji,))
        result = cursor.fetchone()
        
        if result:
            print(f"✅ {test_emoji} با موفقیت اضافه شد!")
            print(f"   📝 توضیحات: {result[2] if len(result) > 2 else 'نامشخص'}")
            print(f"   ⚡ سطح خطر: {result[4] if len(result) > 4 else 1}")
        else:
            print(f"❌ خطا در اضافه کردن {test_emoji}")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ خطا در تست: {e}")

if __name__ == "__main__":
    fix_database_schema()
    test_emoji_addition_fixed()