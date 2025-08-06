#!/usr/bin/env python3
"""
⚡ تست نهایی سرعت سیستم - زیر 20 میلی‌ثانیه
"""

import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

def simple_speed_test():
    """تست سرعت بدون دیتابیس"""
    
    # شبیه‌سازی کش سریع
    emoji_cache = {
        "⚡": {"severity": 1, "auto_pause": True},
        "🔥": {"severity": 3, "auto_pause": True},
        "💀": {"severity": 3, "auto_pause": True}
    }
    
    word_cache = {
        "خطر": {"severity": 3, "auto_pause": True},
        "spam": {"severity": 2, "auto_pause": True}
    }
    
    def ultra_fast_detect(text):
        """تشخیص فوق‌سریع"""
        detected = []
        
        # تشخیص ایموجی
        for emoji, data in emoji_cache.items():
            if emoji in text:
                detected.append({
                    "type": "emoji", 
                    "content": emoji, 
                    "severity": data["severity"]
                })
        
        # تشخیص کلمه
        text_lower = text.lower()
        for word, data in word_cache.items():
            if word in text_lower:
                detected.append({
                    "type": "word", 
                    "content": word, 
                    "severity": data["severity"]
                })
        
        return {
            "detected": len(detected) > 0,
            "items": detected,
            "highest_severity": max([item["severity"] for item in detected]) if detected else 0
        }
    
    # تست‌های مختلف
    test_cases = [
        "سلام ⚡ دوست عزیز",
        "این پیام 🔥 خطرناک است", 
        "spam message with 💀",
        "پیام عادی بدون مشکل",
        "کلمه خطر در متن"
    ]
    
    print("🚀 تست سرعت سیستم تشخیص")
    print("=" * 50)
    
    # تست سرعت برای هر مورد
    for test_text in test_cases:
        start = time.time()
        
        # تکرار 10000 بار برای دقت بالا
        for _ in range(10000):
            result = ultra_fast_detect(test_text)
        
        end = time.time()
        avg_microseconds = (end - start) / 10000 * 1000000
        avg_milliseconds = avg_microseconds / 1000
        
        status = "🔴" if result["detected"] else "🟢"
        severity = result.get("highest_severity", 0)
        items_count = len(result["items"])
        
        print(f"{status} '{test_text[:30]}...'")
        print(f"   ⚡ زمان: {avg_milliseconds:.1f} میلی‌ثانیه ({avg_microseconds:.0f} میکروثانیه)")
        print(f"   🎯 موارد: {items_count} | سطح: {severity}")
        print()
    
    # تست ترکیبی
    complex_text = "پیام پیچیده با ⚡ و 🔥 و کلمه خطر و spam content 💀"
    
    start = time.time()
    for _ in range(10000):
        result = ultra_fast_detect(complex_text)
    end = time.time()
    
    avg_ms = (end - start) / 10000 * 1000
    
    print("🧪 تست متن پیچیده:")
    print(f"   📝 متن: '{complex_text}'")
    print(f"   ⚡ سرعت: {avg_ms:.1f} میلی‌ثانیه")
    print(f"   🎯 موارد تشخیص شده: {len(result['items'])}")
    print(f"   📊 بالاترین سطح خطر: {result['highest_severity']}")
    
    # نمایش جزئیات
    print("\n📋 جزئیات تشخیص:")
    for item in result["items"]:
        type_icon = "🎭" if item["type"] == "emoji" else "📝"
        severity_icon = ["", "🟢", "🟡", "🔴"][item["severity"]]
        print(f"   {type_icon} {item['content']} {severity_icon} (سطح {item['severity']})")

if __name__ == "__main__":
    simple_speed_test()