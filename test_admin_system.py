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
    
    # ادمین‌های بات‌ها (ایدی‌های جدید)
    bot1_admin = 7419698159  # ادمین بات 1
    bot2_admin = 7607882302  # ادمین بات 2
    bot3_admin = 7850529246  # ادمین بات 3
    bot4_admin = 7739974888  # ادمین بات 4
    bot5_admin = 7346058093  # ادمین بات 5
    bot6_admin = 7927398744  # ادمین بات 6
    bot7_admin = 8092847456  # ادمین بات 7
    bot8_admin = 7220521953  # ادمین بات 8
    bot9_admin = 7143723023  # ادمین بات 9
    
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
    
    # تست همه ادمین‌های بات‌ها
    admin_tests = [
        ("بات 3", bot3_admin, 3),
        ("بات 4", bot4_admin, 4),
        ("بات 5", bot5_admin, 5),
        ("بات 6", bot6_admin, 6),
        ("بات 7", bot7_admin, 7),
        ("بات 8", bot8_admin, 8),
        ("بات 9", bot9_admin, 9),
    ]
    
    for bot_name, admin_id, expected_bot in admin_tests:
        print(f"📊 تست ادمین {bot_name} ({admin_id}):")
        print(f"  ✓ آیا {admin_id} ادمین اصلی است؟ {launcher.is_launcher_admin(admin_id)}")
        print(f"  ✓ بات مربوطه: {launcher.get_bot_for_admin(admin_id)}")
        print(f"  ✓ بات‌های قابل کنترل: {launcher.get_accessible_bots(admin_id)}")
        
        # بررسی دسترسی به بات خودش
        can_control_own = launcher.can_control_bot(admin_id, expected_bot)
        print(f"  ✓ کنترل {bot_name}: {'✅' if can_control_own else '❌'}")
        
        # بررسی عدم دسترسی به بات‌های دیگر
        other_bots = [i for i in range(1, 10) if i != expected_bot]
        accessible_others = sum(1 for bot_id in other_bots if launcher.can_control_bot(admin_id, bot_id))
        print(f"  ✓ دسترسی غیرمجاز به بات‌های دیگر: {'❌ مشکل!' if accessible_others > 0 else '✅ هیچ'}")
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