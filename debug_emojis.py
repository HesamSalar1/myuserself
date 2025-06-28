#!/usr/bin/env python3
import sqlite3
import unicodedata

# بررسی ایموجی‌های ذخیره شده در دیتابیس
def check_database_emojis():
    try:
        # فرض کنیم دیتابیس بات 1 را چک کنیم
        db_path = "bots/bot1/bot_database.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # بررسی وجود جدول
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='forbidden_emojis'")
        if not cursor.fetchone():
            print("❌ جدول forbidden_emojis وجود ندارد")
            return
            
        cursor.execute("SELECT emoji FROM forbidden_emojis")
        emojis = cursor.fetchall()
        conn.close()
        
        print(f"📊 تعداد ایموجی‌های ذخیره شده: {len(emojis)}")
        print("\n🔍 لیست ایموجی‌های ممنوعه:")
        
        for i, (emoji,) in enumerate(emojis, 1):
            # تجزیه و تحلیل Unicode
            normalized = unicodedata.normalize('NFC', emoji)
            print(f"{i}. '{emoji}' (طول: {len(emoji)}) -> نرمال: '{normalized}' (طول: {len(normalized)})")
            
            # نمایش کدهای Unicode
            emoji_codes = [f"U+{ord(c):04X}" for c in emoji]
            normalized_codes = [f"U+{ord(c):04X}" for c in normalized]
            print(f"   کدهای اصلی: {' '.join(emoji_codes)}")
            print(f"   کدهای نرمال: {' '.join(normalized_codes)}")
            print()
            
    except Exception as e:
        print(f"❌ خطا: {e}")

def test_emoji_matching():
    """تست مقایسه ایموجی‌ها"""
    test_emojis = ["🔮", "⚡️", "⚡"]
    test_text = "این متن شامل ⚡️ است"
    
    print("🧪 تست مقایسه ایموجی‌ها:")
    print(f"متن تست: '{test_text}'")
    
    for emoji in test_emojis:
        print(f"\nتست ایموجی: '{emoji}'")
        print(f"  کدهای Unicode: {[f'U+{ord(c):04X}' for c in emoji]}")
        
        # تست مقایسه مستقیم
        direct_match = emoji in test_text
        print(f"  مقایسه مستقیم: {direct_match}")
        
        # تست با نرمال‌سازی
        normalized_emoji = unicodedata.normalize('NFC', emoji)
        normalized_text = unicodedata.normalize('NFC', test_text)
        normalized_match = normalized_emoji in normalized_text
        print(f"  مقایسه نرمال: {normalized_match}")

if __name__ == "__main__":
    print("🔍 بررسی ایموجی‌های ممنوعه در دیتابیس")
    print("=" * 50)
    check_database_emojis()
    
    print("\n" + "=" * 50)
    test_emoji_matching()