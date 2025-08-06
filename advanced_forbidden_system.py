#!/usr/bin/env python3
"""
🚀 سیستم فوق‌پیشرفته مدیریت ایموجی و کلمات ممنوعه
✨ ویژگی‌های جدید:
- هیچ ایموجی یا کلمه پیش‌فرضی ندارد
- کاملاً از طریق تلگرام قابل تنظیم
- سیستم تشخیص Unicode پیشرفته
- مدیریت سطوح خطر (1-3)
- تنظیمات جزئی برای هر ایموجی/کلمه
- گزارش‌دهی و آمار پیشرفته
"""

import sys
import sqlite3
import unicodedata
import re
import time
import os
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

class AdvancedForbiddenSystem:
    def __init__(self, db_path):
        self.db_path = db_path
        self.cache = {}
        self.cache_expiry = 300  # 5 دقیقه
        self.setup_advanced_database()
    
    def setup_advanced_database(self):
        """راه‌اندازی دیتابیس پیشرفته"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول ایموجی‌های ممنوعه با ویژگی‌های کامل
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS forbidden_emojis_advanced (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emoji TEXT UNIQUE NOT NULL,
                normalized_emoji TEXT,
                description TEXT,
                added_by_user_id INTEGER,
                added_by_username TEXT,
                category TEXT DEFAULT 'custom',
                severity_level INTEGER DEFAULT 1,
                auto_pause BOOLEAN DEFAULT 1,
                notification_enabled BOOLEAN DEFAULT 1,
                regex_pattern TEXT,
                unicode_variants TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_triggered DATETIME,
                trigger_count INTEGER DEFAULT 0,
                notes TEXT,
                tags TEXT
            )
        ''')
        
        # جدول کلمات ممنوعه با ویژگی‌های کامل
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS forbidden_words_advanced (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE NOT NULL,
                normalized_word TEXT,
                description TEXT,
                added_by_user_id INTEGER,
                added_by_username TEXT,
                category TEXT DEFAULT 'custom',
                severity_level INTEGER DEFAULT 1,
                case_sensitive BOOLEAN DEFAULT 0,
                partial_match BOOLEAN DEFAULT 1,
                regex_pattern TEXT,
                word_boundaries BOOLEAN DEFAULT 1,
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
        ''')
        
        # جدول تنظیمات پیشرفته سیستم
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS advanced_security_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_name TEXT UNIQUE NOT NULL,
                setting_value TEXT,
                data_type TEXT DEFAULT 'string',
                description TEXT,
                updated_by INTEGER,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول لاگ امنیتی پیشرفته
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                content_type TEXT NOT NULL,
                content_value TEXT,
                user_id INTEGER,
                username TEXT,
                chat_id INTEGER,
                chat_title TEXT,
                bot_id INTEGER,
                severity_level INTEGER,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def ultra_normalize_emoji(self, emoji):
        """🔬 نرمال‌سازی فوق‌پیشرفته ایموجی"""
        if not emoji:
            return ""
        
        # تولید همه حالات ممکن یونیکد
        variants = []
        
        # نرمال‌سازی‌های استاندارد
        variants.extend([
            emoji,
            unicodedata.normalize('NFC', emoji),
            unicodedata.normalize('NFD', emoji),
            unicodedata.normalize('NFKC', emoji),
            unicodedata.normalize('NFKD', emoji)
        ])
        
        # حذف variation selectors
        for variant in list(variants):
            cleaned = variant.replace('\uFE0F', '').replace('\uFE0E', '')
            if cleaned not in variants:
                variants.append(cleaned)
        
        # حذف zero-width joiner
        for variant in list(variants):
            no_zwj = variant.replace('\u200D', '')
            if no_zwj not in variants:
                variants.append(no_zwj)
        
        # ترکیب حذف‌ها
        for variant in list(variants):
            ultra_clean = (variant
                          .replace('\uFE0F', '')
                          .replace('\uFE0E', '')
                          .replace('\u200D', '')
                          .replace('\u200C', ''))  # zero-width non-joiner
            if ultra_clean not in variants:
                variants.append(ultra_clean)
        
        # حذف موارد تکراری و خالی
        unique_variants = list(set(v for v in variants if v.strip()))
        
        return unique_variants
    
    def add_forbidden_emoji_ultimate(self, emoji, description="", severity_level=1, 
                                   user_id=None, username="", category="custom",
                                   auto_pause=True, notification_enabled=True,
                                   tags="", notes=""):
        """💎 اضافه کردن ایموجی ممنوعه با حداکثر ویژگی‌ها"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # نرمال‌سازی فوق‌پیشرفته
            variants = self.ultra_normalize_emoji(emoji)
            normalized_emoji = variants[0] if variants else emoji
            unicode_variants = "|".join(variants)
            
            # بررسی وجود
            cursor.execute("SELECT id FROM forbidden_emojis_advanced WHERE emoji = ?", (emoji,))
            existing = cursor.fetchone()
            
            if existing:
                # بروزرسانی
                cursor.execute("""
                    UPDATE forbidden_emojis_advanced 
                    SET description = ?, severity_level = ?, auto_pause = ?, 
                        notification_enabled = ?, tags = ?, notes = ?,
                        updated_at = CURRENT_TIMESTAMP, is_active = 1,
                        unicode_variants = ?, normalized_emoji = ?
                    WHERE emoji = ?
                """, (description, severity_level, auto_pause, notification_enabled,
                     tags, notes, unicode_variants, normalized_emoji, emoji))
                action = "updated"
            else:
                # اضافه کردن جدید
                cursor.execute("""
                    INSERT INTO forbidden_emojis_advanced 
                    (emoji, normalized_emoji, description, added_by_user_id, added_by_username,
                     category, severity_level, auto_pause, notification_enabled, 
                     unicode_variants, tags, notes, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (emoji, normalized_emoji, description, user_id, username,
                     category, severity_level, auto_pause, notification_enabled,
                     unicode_variants, tags, notes))
                action = "added"
            
            # لاگ امنیتی
            self.log_security_action("emoji_" + action, "emoji", emoji, user_id, username, 
                                   None, None, None, severity_level, 
                                   f"Emoji {action} with {len(variants)} variants")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ خطا در اضافه کردن ایموجی: {e}")
            return False
    
    def add_forbidden_word_ultimate(self, word, description="", severity_level=1,
                                  case_sensitive=False, partial_match=True,
                                  word_boundaries=True, user_id=None, username="",
                                  category="custom", auto_pause=True, 
                                  notification_enabled=True, tags="", notes=""):
        """💎 اضافه کردن کلمه ممنوعه با حداکثر ویژگی‌ها"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # نرمال‌سازی کلمه
            normalized_word = word.strip().lower() if not case_sensitive else word.strip()
            
            # تولید regex pattern
            escaped_word = re.escape(word)
            if word_boundaries and not partial_match:
                regex_pattern = r'\b' + escaped_word + r'\b'
            elif partial_match:
                regex_pattern = escaped_word
            else:
                regex_pattern = r'\b' + escaped_word + r'\b'
            
            # بررسی وجود
            cursor.execute("SELECT id FROM forbidden_words_advanced WHERE word = ?", (word,))
            existing = cursor.fetchone()
            
            if existing:
                # بروزرسانی
                cursor.execute("""
                    UPDATE forbidden_words_advanced 
                    SET description = ?, severity_level = ?, case_sensitive = ?,
                        partial_match = ?, word_boundaries = ?, auto_pause = ?,
                        notification_enabled = ?, tags = ?, notes = ?,
                        regex_pattern = ?, normalized_word = ?,
                        updated_at = CURRENT_TIMESTAMP, is_active = 1
                    WHERE word = ?
                """, (description, severity_level, case_sensitive, partial_match,
                     word_boundaries, auto_pause, notification_enabled, tags, notes,
                     regex_pattern, normalized_word, word))
                action = "updated"
            else:
                # اضافه کردن جدید
                cursor.execute("""
                    INSERT INTO forbidden_words_advanced 
                    (word, normalized_word, description, added_by_user_id, added_by_username,
                     category, severity_level, case_sensitive, partial_match, word_boundaries,
                     auto_pause, notification_enabled, regex_pattern, tags, notes, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (word, normalized_word, description, user_id, username, category,
                     severity_level, case_sensitive, partial_match, word_boundaries,
                     auto_pause, notification_enabled, regex_pattern, tags, notes))
                action = "added"
            
            # لاگ امنیتی
            self.log_security_action("word_" + action, "word", word, user_id, username,
                                   None, None, None, severity_level,
                                   f"Word {action} with pattern: {regex_pattern}")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ خطا در اضافه کردن کلمه: {e}")
            return False
    
    def ultra_detect_forbidden_content(self, text, content_type="both"):
        """🔍 تشخیص فوق‌پیشرفته محتوای ممنوعه"""
        if not text:
            return {"detected": False, "items": [], "details": []}
        
        detected_items = []
        detection_details = []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # تشخیص ایموجی‌های ممنوعه
            if content_type in ["emoji", "both"]:
                cursor.execute("""
                    SELECT emoji, unicode_variants, severity_level, description, auto_pause
                    FROM forbidden_emojis_advanced 
                    WHERE is_active = 1
                """)
                emojis = cursor.fetchall()
                
                for emoji, variants_str, severity, desc, auto_pause in emojis:
                    variants = variants_str.split("|") if variants_str else [emoji]
                    
                    for variant in variants:
                        if variant and variant in text:
                            detected_items.append({
                                "type": "emoji",
                                "content": emoji,
                                "matched_variant": variant,
                                "severity": severity,
                                "description": desc,
                                "auto_pause": bool(auto_pause)
                            })
                            
                            detection_details.append({
                                "original": emoji,
                                "matched": variant,
                                "position": text.find(variant),
                                "severity": severity
                            })
                            
                            # اپدیت آمار
                            cursor.execute("""
                                UPDATE forbidden_emojis_advanced 
                                SET trigger_count = trigger_count + 1, 
                                    last_triggered = CURRENT_TIMESTAMP
                                WHERE emoji = ?
                            """, (emoji,))
                            break
            
            # تشخیص کلمات ممنوعه
            if content_type in ["word", "both"]:
                cursor.execute("""
                    SELECT word, regex_pattern, severity_level, description, 
                           case_sensitive, auto_pause
                    FROM forbidden_words_advanced 
                    WHERE is_active = 1
                """)
                words = cursor.fetchall()
                
                for word, pattern, severity, desc, case_sensitive, auto_pause in words:
                    flags = 0 if case_sensitive else re.IGNORECASE
                    
                    try:
                        if re.search(pattern, text, flags):
                            detected_items.append({
                                "type": "word",
                                "content": word,
                                "pattern": pattern,
                                "severity": severity,
                                "description": desc,
                                "auto_pause": bool(auto_pause)
                            })
                            
                            match = re.search(pattern, text, flags)
                            if match:
                                detection_details.append({
                                    "original": word,
                                    "matched": match.group(),
                                    "position": match.start(),
                                    "severity": severity
                                })
                            
                            # اپدیت آمار
                            cursor.execute("""
                                UPDATE forbidden_words_advanced 
                                SET trigger_count = trigger_count + 1,
                                    last_triggered = CURRENT_TIMESTAMP
                                WHERE word = ?
                            """, (word,))
                    except re.error:
                        # اگر regex نامعتبر باشد، تطبیق ساده
                        search_text = text if case_sensitive else text.lower()
                        search_word = word if case_sensitive else word.lower()
                        if search_word in search_text:
                            detected_items.append({
                                "type": "word",
                                "content": word,
                                "severity": severity,
                                "description": desc,
                                "auto_pause": bool(auto_pause)
                            })
            
            conn.commit()
            conn.close()
            
            return {
                "detected": len(detected_items) > 0,
                "items": detected_items,
                "details": detection_details,
                "highest_severity": max([item["severity"] for item in detected_items]) if detected_items else 0
            }
            
        except Exception as e:
            conn.close()
            print(f"❌ خطا در تشخیص: {e}")
            return {"detected": False, "items": [], "details": []}
    
    def get_forbidden_list(self, content_type="both", limit=50):
        """📋 دریافت لیست محتوای ممنوعه"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        result = {"emojis": [], "words": []}
        
        try:
            if content_type in ["emoji", "both"]:
                cursor.execute("""
                    SELECT emoji, description, severity_level, added_by_username,
                           created_at, trigger_count, tags
                    FROM forbidden_emojis_advanced 
                    WHERE is_active = 1 
                    ORDER BY severity_level DESC, created_at DESC 
                    LIMIT ?
                """, (limit,))
                result["emojis"] = cursor.fetchall()
            
            if content_type in ["word", "both"]:
                cursor.execute("""
                    SELECT word, description, severity_level, added_by_username,
                           created_at, trigger_count, case_sensitive, partial_match, tags
                    FROM forbidden_words_advanced 
                    WHERE is_active = 1 
                    ORDER BY severity_level DESC, created_at DESC 
                    LIMIT ?
                """, (limit,))
                result["words"] = cursor.fetchall()
            
            conn.close()
            return result
            
        except Exception as e:
            conn.close()
            print(f"❌ خطا در دریافت لیست: {e}")
            return {"emojis": [], "words": []}
    
    def remove_forbidden_content(self, content, content_type):
        """🗑️ حذف محتوای ممنوعه"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if content_type == "emoji":
                cursor.execute("DELETE FROM forbidden_emojis_advanced WHERE emoji = ?", (content,))
            elif content_type == "word":
                cursor.execute("DELETE FROM forbidden_words_advanced WHERE word = ?", (content,))
            
            removed = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return removed
            
        except Exception as e:
            print(f"❌ خطا در حذف: {e}")
            return False
    
    def log_security_action(self, action_type, content_type, content_value, 
                          user_id, username, chat_id, chat_title, bot_id, 
                          severity_level, details):
        """📝 ثبت لاگ امنیتی پیشرفته"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO security_audit_log 
                (action_type, content_type, content_value, user_id, username,
                 chat_id, chat_title, bot_id, severity_level, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (action_type, content_type, content_value, user_id, username,
                 chat_id, chat_title, bot_id, severity_level, details))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ خطا در ثبت لاگ: {e}")

if __name__ == "__main__":
    # تست سیستم پیشرفته
    system = AdvancedForbiddenSystem("test_advanced.db")
    
    print("🚀 تست سیستم فوق‌پیشرفته ایموجی و کلمات ممنوعه")
    print("=" * 60)
    
    # تست اضافه کردن ایموجی
    result1 = system.add_forbidden_emoji_ultimate("⚡", "ایموجی برق خطرناک", 3, 123, "تستر")
    print(f"✅ اضافه کردن ایموجی: {result1}")
    
    # تست اضافه کردن کلمه
    result2 = system.add_forbidden_word_ultimate("تست", "کلمه تستی", 2, False, True, True, 123, "تستر")
    print(f"✅ اضافه کردن کلمه: {result2}")
    
    # تست تشخیص
    detection = system.ultra_detect_forbidden_content("سلام ⚡ این تست است")
    print(f"🔍 تشخیص: {detection['detected']}")
    print(f"📊 موارد یافت شده: {len(detection['items'])}")
    
    # نمایش لیست
    content_list = system.get_forbidden_list()
    print(f"📋 ایموجی‌ها: {len(content_list['emojis'])}")
    print(f"📋 کلمات: {len(content_list['words'])}")
    
    print("\n✅ سیستم آماده برای استفاده است!")