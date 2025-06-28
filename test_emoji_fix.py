#!/usr/bin/env python3
import sqlite3
import os
import unicodedata

def create_test_database():
    """ایجاد دیتابیس تست"""
    os.makedirs("bots/bot1", exist_ok=True)
    db_path = "bots/bot1/bot_database.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # ایجاد جدول
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forbidden_emojis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emoji TEXT UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # اضافه کردن ایموجی‌های تست
    test_emojis = ["🔮", "⚡️", "⚡", "🚫", "❌"]
    for emoji in test_emojis:
        try:
            cursor.execute("INSERT INTO forbidden_emojis (emoji) VALUES (?)", (emoji,))
            print(f"✅ ایموجی {emoji} اضافه شد")
        except sqlite3.IntegrityError:
            print(f"⚠️ ایموجی {emoji} از قبل وجود دارد")
    
    conn.commit()
    conn.close()
    print(f"✅ دیتابیس در {db_path} ایجاد شد")

def normalize_emoji(emoji):
    """نرمال‌سازی ایموجی برای مقایسه دقیق‌تر"""
    # نرمال‌سازی Unicode
    normalized = unicodedata.normalize('NFC', emoji)
    
    # حذف Variation Selectors (U+FE0F, U+FE0E)
    cleaned = normalized.replace('\uFE0F', '').replace('\uFE0E', '')
    
    return cleaned

def test_advanced_emoji_matching():
    """تست مقایسه ایموجی‌های پیشرفته"""
    print("\n🧪 تست مقایسه ایموجی‌های پیشرفته:")
    
    # ایموجی‌های تست (شامل حالات مختلف ⚡)
    forbidden_emojis = {"🔮", "⚡️", "⚡", "🚫"}
    
    test_texts = [
        "این متن شامل 🔮 است",
        "این متن شامل ⚡️ است",
        "این متن شامل ⚡ است",
        "این متن شامل 🚫 است",
        "این متن شامل ❌ است",
        "متن عادی بدون ایموجی",
    ]
    
    for text in test_texts:
        print(f"\nمتن تست: '{text}'")
        
        found = False
        for emoji in forbidden_emojis:
            normalized_emoji = normalize_emoji(emoji)
            normalized_text = normalize_emoji(text)
            
            # بررسی چند حالت مختلف
            checks = [
                emoji in text,                              # مقایسه مستقیم
                normalized_emoji in normalized_text,        # مقایسه نرمال شده
                emoji.replace('\uFE0F', '') in text,       # بدون Variation Selector
                emoji in text.replace('\uFE0F', ''),       # متن بدون Variation Selector
            ]
            
            if any(checks):
                print(f"  ✅ ایموجی ممنوعه تشخیص داده شد: {emoji}")
                print(f"     کدهای ایموجی: {[hex(ord(c)) for c in emoji]}")
                print(f"     نرمال شده: {repr(normalized_emoji)}")
                found = True
                break
        
        if not found:
            print("  ❌ ایموجی ممنوعه‌ای یافت نشد")

if __name__ == "__main__":
    print("🔧 ایجاد دیتابیس تست و بررسی ایموجی‌ها")
    print("=" * 50)
    
    create_test_database()
    test_advanced_emoji_matching()