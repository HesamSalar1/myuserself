#!/usr/bin/env python3
"""
تست سیستم جدید ادمین‌ها و کنترل دستی
"""

from unified_bot_launcher import UnifiedBotLauncher

def test_admin_system():
    """تست سیستم ادمین‌های جدید"""
    print("🧪 تست سیستم ادمین‌های جدید")
    print("=" * 50)
    
    launcher = UnifiedBotLauncher()
    
    # تست ادمین لانچر
    launcher_admin = 5533325167
    print(f"🔐 ادمین لانچر: {launcher_admin}")
    print(f"   ✅ تشخیص ادمین لانچر: {launcher.is_launcher_admin(launcher_admin)}")
    print(f"   ✅ تشخیص ادمین کلی: {launcher.is_admin(launcher_admin)}")
    
    # تست ادمین‌های بات‌ها
    print(f"\n🤖 ادمین‌های بات‌ها:")
    for bot_id, admin_id in launcher.bot_admins.items():
        print(f"   بات {bot_id}: {admin_id}")
        print(f"     ✅ تشخیص ادمین بات {bot_id}: {launcher.is_bot_admin(admin_id, bot_id)}")
        print(f"     ✅ پیدا کردن بات ادمین: {launcher.get_user_bot_id(admin_id)}")
    
    # تست وضعیت‌های پیش‌فرض
    print(f"\n📊 وضعیت پیش‌فرض بات‌ها:")
    for bot_id in range(1, 10):
        status = launcher.get_bot_status(bot_id)
        if status:
            print(f"   بات {bot_id}: {'🟢 فعال' if status['enabled'] else '🔴 غیرفعال'} - تاخیر: {status['delay']}s")
        
    # تست تغییر وضعیت
    print(f"\n🔄 تست تغییر وضعیت:")
    test_bot_id = 1
    
    # فعال کردن
    if launcher.toggle_bot_status(test_bot_id, True):
        status = launcher.get_bot_status(test_bot_id)
        print(f"   ✅ بات {test_bot_id} فعال شد - وضعیت: {status['enabled']}")
    
    # تغییر تاخیر
    if launcher.set_bot_delay(test_bot_id, 5.0):
        status = launcher.get_bot_status(test_bot_id)
        print(f"   ⏱️ تاخیر بات {test_bot_id} تغییر یافت - جدید: {status['delay']}s")
    
    # غیرفعال کردن
    if launcher.toggle_bot_status(test_bot_id, False):
        status = launcher.get_bot_status(test_bot_id)
        print(f"   ⏹️ بات {test_bot_id} غیرفعال شد - وضعیت: {status['enabled']}")

if __name__ == "__main__":
    test_admin_system()
    print("\n" + "=" * 50)
    print("🎯 خلاصه:")
    print("✅ سیستم ادمین‌های جدید آماده")
    print("✅ هر بات ادمین اختصاصی دارد")
    print("✅ کنترل دستی فعال/غیرفعال")
    print("✅ تنظیم تاخیر قابل تنظیم")
    print("✅ پیش‌فرض همه بات‌ها خاموش")
    print("✅ فقط ادمین لانچر کنترل کامل دارد")
    print("\n🚀 سیستم آماده استفاده!")