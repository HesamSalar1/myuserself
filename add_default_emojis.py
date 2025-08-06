
#!/usr/bin/env python3
"""
🧹 ابزار پاکسازی ایموجی‌های پیش‌فرض
❌ این فایل حذف شد - هیچ ایموجی پیش‌فرضی نخواهیم داشت
✅ سیستم کاملاً از طریق تلگرام قابل تنظیم است
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from unified_bot_launcher import UnifiedBotLauncher

def clear_default_emojis():
    """حذف همه ایموجی‌های پیش‌فرض از دیتابیس"""
    print("🧹 حذف همه ایموجی‌های پیش‌فرض...")
    
    launcher = UnifiedBotLauncher()
    
    # حذف همه ایموجی‌های موجود از دیتابیس
    try:
        import sqlite3
        import os
        
        possible_paths = [
            launcher.bot_configs[1]['db_path'],
            "bots/bot1/bot_database.db",
            "bots/bot1/bot1_data.db"
        ]
        
        cleared_count = 0
        for db_path in possible_paths:
            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # بررسی وجود جدول
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='forbidden_emojis'")
                    if cursor.fetchone():
                        # شمارش ایموجی‌های موجود
                        cursor.execute("SELECT COUNT(*) FROM forbidden_emojis")
                        current_count = cursor.fetchone()[0]
                        
                        # حذف همه
                        cursor.execute("DELETE FROM forbidden_emojis")
                        conn.commit()
                        
                        print(f"✅ {current_count} ایموجی از {db_path} حذف شد")
                        cleared_count += current_count
                    
                    conn.close()
                    break
                except Exception as e:
                    print(f"⚠️ خطا در پاکسازی {db_path}: {e}")
                    continue
        
        print(f"\n📊 مجموع {cleared_count} ایموجی پیش‌فرض حذف شد")
        print("✅ حالا سیستم کاملاً خالی است و فقط از طریق تلگرام قابل تنظیم!")
        
    except Exception as e:
        print(f"❌ خطا در پاکسازی: {e}")

if __name__ == "__main__":
    clear_default_emojis()
