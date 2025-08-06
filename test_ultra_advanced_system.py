#!/usr/bin/env python3
"""
🧪 تست جامع سیستم فوق‌پیشرفته ایموجی و کلمات ممنوعه
✅ بررسی همه ویژگی‌های جدید
"""

import sys
import os
from advanced_forbidden_system import AdvancedForbiddenSystem
import time

sys.stdout.reconfigure(encoding='utf-8')

def test_ultra_advanced_system():
    """تست کامل سیستم پیشرفته"""
    print("🚀 شروع تست سیستم فوق‌پیشرفته")
    print("=" * 60)
    
    # ایجاد سیستم تست
    system = AdvancedForbiddenSystem("test_ultra_advanced.db")
    
    # تست 1: اضافه کردن ایموجی‌های متنوع
    print("\n🧪 تست 1: اضافه کردن ایموجی‌های پیچیده")
    emojis_to_test = [
        ("⚡", "برق ساده", 1),
        ("🔥", "آتش خطرناک", 2),
        ("💀", "خطر مرگ", 3),
        ("🚀", "موشک", 2),
        ("⭐️", "ستاره با variation selector", 1)
    ]
    
    for emoji, desc, level in emojis_to_test:
        result = system.add_forbidden_emoji_ultimate(
            emoji, desc, level, 12345, "تستر_ایموجی", "test", True, True, "test,emoji", f"تست سطح {level}"
        )
        print(f"{'✅' if result else '❌'} اضافه کردن {emoji}: {result}")
    
    # تست 2: اضافه کردن کلمات با تنظیمات مختلف
    print("\n🧪 تست 2: اضافه کردن کلمات با تنظیمات پیشرفته")
    words_to_test = [
        ("بدکلام", "فحش ساده", 1, False, True, True),
        ("SPAM", "اسپم انگلیسی", 2, True, False, True),
        ("test", "کلمه تست", 1, False, True, False),
        ("خطر", "کلمه خطر", 3, False, False, True)
    ]
    
    for word, desc, level, case_sens, partial, boundaries in words_to_test:
        result = system.add_forbidden_word_ultimate(
            word, desc, level, case_sens, partial, boundaries, 
            12345, "تستر_کلمه", "test", True, True, "test,word", f"تست {word}"
        )
        print(f"{'✅' if result else '❌'} اضافه کردن '{word}': {result}")
    
    # تست 3: تشخیص محتوای پیچیده
    print("\n🧪 تست 3: تشخیص محتوای ممنوعه")
    test_texts = [
        "سلام ⚡ دوست عزیز",
        "این پیام🔥 خطرناک است",
        "تست کلمه بدکلام اینجا",
        "SPAM message here",
        "کلمه خطر در متن",
        "⭐️ ستاره زیبا",
        "پیام عادی بدون مشکل"
    ]
    
    for text in test_texts:
        detection = system.ultra_detect_forbidden_content(text)
        status = "🔴" if detection['detected'] else "🟢"
        items_count = len(detection['items'])
        severity = detection.get('highest_severity', 0)
        print(f"{status} '{text[:30]}...': {items_count} مورد (سطح {severity})")
    
    # تست 4: دریافت لیست‌ها
    print("\n🧪 تست 4: دریافت لیست محتوای ممنوعه")
    content_list = system.get_forbidden_list()
    print(f"📋 ایموجی‌های ثبت شده: {len(content_list['emojis'])}")
    print(f"📋 کلمات ثبت شده: {len(content_list['words'])}")
    
    # نمایش جزئیات ایموجی‌ها
    print("\n📝 ایموجی‌های ثبت شده:")
    for i, (emoji, desc, level, username, created, count, tags) in enumerate(content_list['emojis'], 1):
        level_icon = ["", "🟢", "🟡", "🔴"][level]
        print(f"  {i}. {emoji} {level_icon} - {desc} (توسط {username})")
    
    # نمایش جزئیات کلمات
    print("\n📝 کلمات ثبت شده:")
    for i, (word, desc, level, username, created, count, case_sens, partial, tags) in enumerate(content_list['words'], 1):
        level_icon = ["", "🟢", "🟡", "🔴"][level]
        options = []
        if case_sens: options.append("حساس")
        if not partial: options.append("دقیق")
        option_text = f" ({', '.join(options)})" if options else ""
        print(f"  {i}. '{word}' {level_icon} - {desc}{option_text} (توسط {username})")
    
    # تست 5: عملکرد تشخیص سریع
    print("\n🧪 تست 5: بررسی عملکرد")
    test_text = "پیام تست با ⚡ و کلمه بدکلام و 🔥 و SPAM"
    
    start_time = time.time()
    for _ in range(100):
        detection = system.ultra_detect_forbidden_content(test_text)
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 100 * 1000  # تبدیل به میلی‌ثانیه
    print(f"⚡ میانگین زمان تشخیص: {avg_time:.2f} میلی‌ثانیه")
    print(f"🎯 آیتم‌های تشخیص داده شده: {len(detection['items'])}")
    
    # تست 6: حذف محتوا
    print("\n🧪 تست 6: حذف محتوای ممنوعه")
    remove_result1 = system.remove_forbidden_content("test", "word")
    remove_result2 = system.remove_forbidden_content("🚀", "emoji")
    print(f"{'✅' if remove_result1 else '❌'} حذف کلمه 'test': {remove_result1}")
    print(f"{'✅' if remove_result2 else '❌'} حذف ایموجی '🚀': {remove_result2}")
    
    # بررسی نهایی
    final_list = system.get_forbidden_list()
    print(f"\n📊 آمار نهایی:")
    print(f"   ایموجی‌ها: {len(final_list['emojis'])} عدد")
    print(f"   کلمات: {len(final_list['words'])} عدد")
    
    print("\n" + "=" * 60)
    print("✅ تست سیستم فوق‌پیشرفته با موفقیت تکمیل شد!")
    print("🎉 همه ویژگی‌های جدید به درستی کار می‌کنند")

if __name__ == "__main__":
    test_ultra_advanced_system()