#!/usr/bin/env python3
import sqlite3
import os

def check_forbidden_emojis():
    """بررسی ایموجی‌های ممنوعه موجود در دیتابیس"""
    db_path = "bots/bot1/bot_database.db"
    
    if not os.path.exists(db_path):
        print(f"❌ دیتابیس در مسیر {db_path} وجود ندارد")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # بررسی وجود جدول
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='forbidden_emojis'")
        if not cursor.fetchone():
            print("❌ جدول forbidden_emojis وجود ندارد")
            conn.close()
            return
        
        # دریافت همه ایموجی‌ها
        cursor.execute("SELECT emoji FROM forbidden_emojis")
        emojis = cursor.fetchall()
        conn.close()
        
        print(f"📊 تعداد ایموجی‌های ممنوعه: {len(emojis)}")
        
        if len(emojis) == 0:
            print("⚠️ هیچ ایموجی ممنوعه‌ای در دیتابیس وجود ندارد")
            return
        
        print("\n🔍 لیست ایموجی‌های ممنوعه:")
        target_emojis = ["⚡", "⚡️"]
        
        for i, (emoji,) in enumerate(emojis, 1):
            status = ""
            if emoji in target_emojis:
                status = " ✅ (مرتبط با مشکل)"
            
            print(f"{i}. '{emoji}' - کدهای Unicode: {[hex(ord(c)) for c in emoji]}{status}")
        
        # بررسی مستقیم ایموجی‌های مرتبط
        print(f"\n🎯 بررسی مستقیم ایموجی‌های مرتبط:")
        emojis_set = {emoji[0] for emoji in emojis}
        
        for target in target_emojis:
            if target in emojis_set:
                print(f"✅ '{target}' در دیتابیس موجود است")
            else:
                print(f"❌ '{target}' در دیتابیس موجود نیست")
                
    except Exception as e:
        print(f"❌ خطا در بررسی دیتابیس: {e}")

def test_emoji_detection():
    """تست سیستم تشخیص ایموجی"""
    print("\n🧪 تست سیستم تشخیص ایموجی:")
    
    # شبیه‌سازی کد اصلی
    def normalize_emoji(emoji):
        import unicodedata
        normalized = unicodedata.normalize('NFC', emoji)
        cleaned = normalized.replace('\uFE0F', '').replace('\uFE0E', '')
        return cleaned

    def contains_stop_emoji(text, forbidden_emojis):
        if not text:
            return False

        normalized_text = normalize_emoji(text)

        for emoji in forbidden_emojis:
            normalized_emoji = normalize_emoji(emoji)
            
            checks = [
                emoji in text,
                normalized_emoji in normalized_text,
                emoji.replace('\uFE0F', '') in text,
                emoji in text.replace('\uFE0F', ''),
            ]
            
            if any(checks):
                return True, emoji
        return False, None
    
    # بارگذاری ایموجی‌ها از دیتابیس
    db_path = "bots/bot1/bot_database.db"
    forbidden_emojis = set()
    
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT emoji FROM forbidden_emojis")
            emojis = cursor.fetchall()
            forbidden_emojis = {emoji[0] for emoji in emojis}
            conn.close()
        except:
            pass
    
    # متن‌های تست (شبیه به آنچه در عکس دیده می‌شود)
    test_texts = [
        "⚡",           # ایموجی ساده
        "⚡️",          # ایموجی با variation selector
        "A CHARACTER HAS SPAWNED IN THE CHAT ⚡",  # متن با ایموجی
        "متن عادی",      # متن بدون ایموجی
    ]
    
    print(f"ایموجی‌های ممنوعه بارگذاری شده: {forbidden_emojis}")
    
    for text in test_texts:
        detected, found_emoji = contains_stop_emoji(text, forbidden_emojis)
        if detected:
            print(f"✅ '{text}' - ایموجی ممنوعه تشخیص داده شد: {found_emoji}")
        else:
            print(f"❌ '{text}' - ایموجی ممنوعه تشخیص داده نشد")

if __name__ == "__main__":
    print("🔍 بررسی وضعیت فعلی سیستم ایموجی‌های ممنوعه")
    print("=" * 60)
    
    check_forbidden_emojis()
    test_emoji_detection()