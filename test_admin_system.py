#!/usr/bin/env python3
"""
تست سیستم ادمین جدید
بررسی دسترسی‌های مختلف ادمین‌ها
"""

from unified_bot_launcher import UnifiedBotLauncher

def test_admin_permissions():
    """تست سیستم دسترسی ادمین‌ها"""
    print("🔍 شروع تست سیستم ادمین جدید...")
    
    # ایجاد لانچر
    launcher = UnifiedBotLauncher()
    
    # ادمین اصلی لانچر
    launcher_admin = 5533325167
    
    # ادمین‌های بات‌ها
    bot1_admin = 7143723023
    bot2_admin = 7419698159
    bot3_admin = 7607882302
    bot4_admin = 7850529246  # این ادمین برای بات‌های 4-9 است
    
    print(f"👑 ادمین اصلی لانچر: {launcher_admin}")
    print(f"🔧 ادمین‌های بات‌ها: {list(launcher.bot_admin_ids)}")
    print(f"📋 همه ادمین‌ها: {list(launcher.all_admin_ids)}")
    print()
    
    # تست ادمین اصلی لانچر
    print("📊 تست ادمین اصلی لانچر:")
    print(f"  ✓ آیا {launcher_admin} ادمین اصلی است؟ {launcher.is_launcher_admin(launcher_admin)}")
    print(f"  ✓ بات‌های قابل کنترل: {launcher.get_accessible_bots(launcher_admin)}")
    for bot_id in range(1, 10):
        can_control = launcher.can_control_bot(launcher_admin, bot_id)
        print(f"  ✓ کنترل بات {bot_id}: {'✅' if can_control else '❌'}")
    print()
    
    # تست ادمین بات 1
    print("📊 تست ادمین بات 1:")
    print(f"  ✓ آیا {bot1_admin} ادمین اصلی است؟ {launcher.is_launcher_admin(bot1_admin)}")
    print(f"  ✓ بات مربوطه: {launcher.get_bot_for_admin(bot1_admin)}")
    print(f"  ✓ بات‌های قابل کنترل: {launcher.get_accessible_bots(bot1_admin)}")
    for bot_id in range(1, 10):
        can_control = launcher.can_control_bot(bot1_admin, bot_id)
        print(f"  ✓ کنترل بات {bot_id}: {'✅' if can_control else '❌'}")
    print()
    
    # تست ادمین بات 2
    print("📊 تست ادمین بات 2:")
    print(f"  ✓ آیا {bot2_admin} ادمین اصلی است؟ {launcher.is_launcher_admin(bot2_admin)}")
    print(f"  ✓ بات مربوطه: {launcher.get_bot_for_admin(bot2_admin)}")
    print(f"  ✓ بات‌های قابل کنترل: {launcher.get_accessible_bots(bot2_admin)}")
    for bot_id in range(1, 10):
        can_control = launcher.can_control_bot(bot2_admin, bot_id)
        print(f"  ✓ کنترل بات {bot_id}: {'✅' if can_control else '❌'}")
    print()
    
    # تست ادمین بات‌های 4-9
    print("📊 تست ادمین بات‌های 4-9:")
    print(f"  ✓ آیا {bot4_admin} ادمین اصلی است؟ {launcher.is_launcher_admin(bot4_admin)}")
    print(f"  ✓ بات مربوطه: {launcher.get_bot_for_admin(bot4_admin)}")
    print(f"  ✓ بات‌های قابل کنترل: {launcher.get_accessible_bots(bot4_admin)}")
    for bot_id in range(1, 10):
        can_control = launcher.can_control_bot(bot4_admin, bot_id)
        print(f"  ✓ کنترل بات {bot_id}: {'✅' if can_control else '❌'}")
    print()
    
    # تست کاربر غیر ادمین
    random_user = 123456789
    print("📊 تست کاربر غیر ادمین:")
    print(f"  ✓ آیا {random_user} ادمین اصلی است؟ {launcher.is_launcher_admin(random_user)}")
    print(f"  ✓ بات مربوطه: {launcher.get_bot_for_admin(random_user)}")
    print(f"  ✓ بات‌های قابل کنترل: {launcher.get_accessible_bots(random_user)}")
    print(f"  ✓ آیا ادمین است؟ {random_user in launcher.all_admin_ids}")
    print()
    
    print("✅ تست سیستم ادمین کامل شد!")

if __name__ == "__main__":
    test_admin_permissions()