
#!/usr/bin/env python3
"""
اسکریپت تشخیص و رفع مشکل اضافه کردن ایموجی
"""
import sys
import sqlite3
import os
import unicodedata

sys.stdout.reconfigure(encoding='utf-8')

def check_database_structure():
    """بررسی ساختار دیتابیس"""
    print("🔍 بررسی ساختار دیتابیس...")
    
    for i in range(1, 10):
        db_path = f"bots/bot{i}/bot_database.db"
        if not os.path.exists(db_path):
            print(f"❌ دیتابیس بات {i} موجود نیست")
            continue
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # بررسی وجود جدول
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='forbidden_emojis'")
            if not cursor.fetchone():
                print(f"❌ جدول forbidden_emojis در بات {i} وجود ندارد")
                # ایجاد جدول
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS forbidden_emojis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        emoji TEXT UNIQUE NOT NULL,
                        description TEXT DEFAULT '',
                        category TEXT DEFAULT 'custom',
                        added_by_user_id INTEGER DEFAULT 1842714289,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                print(f"✅ جدول forbidden_emojis در بات {i} ایجاد شد")
            else:
                print(f"✅ جدول forbidden_emojis در بات {i} موجود است")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ خطا در بات {i}: {e}")

def test_emoji_add():
    """تست اضافه کردن ایموجی"""
    print("\n🧪 تست اضافه کردن ایموجی...")
    
    test_emojis = ["⚡", "🔮", "💎", "🎯"]
    
    for emoji in test_emojis:
        print(f"\n🔍 تست ایموجی: {emoji}")
        
        # نرمال‌سازی
        normalized = unicodedata.normalize('NFC', emoji)
        print(f"   نرمال شده: {repr(normalized)}")
        print(f"   کدهای Unicode: {' '.join([f'U+{ord(c):04X}' for c in emoji])}")
        
        # تست اضافه کردن به دیتابیس
        success_count = 0
        for i in range(1, 10):
            db_path = f"bots/bot{i}/bot_database.db"
            if not os.path.exists(db_path):
                continue
                
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # بررسی وجود
                cursor.execute("SELECT COUNT(*) FROM forbidden_emojis WHERE emoji = ?", (normalized,))
                if cursor.fetchone()[0] > 0:
                    print(f"   بات {i}: از قبل موجود")
                    conn.close()
                    continue
                
                # اضافه کردن
                cursor.execute("""
                    INSERT INTO forbidden_emojis (emoji, description, category)
                    VALUES (?, ?, ?)
                """, (normalized, f"تست {emoji}", "test"))
                conn.commit()
                success_count += 1
                print(f"   بات {i}: ✅ اضافه شد")
                
                conn.close()
                
            except Exception as e:
                print(f"   بات {i}: ❌ خطا - {e}")
        
        print(f"   نتیجه: {success_count}/9 بات")

def clean_test_emojis():
    """پاک کردن ایموجی‌های تست"""
    print("\n🧹 پاک کردن ایموجی‌های تست...")
    
    for i in range(1, 10):
        db_path = f"bots/bot{i}/bot_database.db"
        if not os.path.exists(db_path):
            continue
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM forbidden_emojis WHERE category = 'test'")
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted > 0:
                print(f"   بات {i}: {deleted} ایموجی تست حذف شد")
            
        except Exception as e:
            print(f"   بات {i}: خطا - {e}")

if __name__ == "__main__":
    print("🔧 تشخیص و رفع مشکل ایموجی‌ها")
    print("=" * 50)
    
    check_database_structure()
    test_emoji_add()
    
    response = input("\n❓ آیا ایموجی‌های تست حذف شوند؟ (y/n): ")
    if response.lower() == 'y':
        clean_test_emojis()
    
    print("\n✅ تست تکمیل شد!")
