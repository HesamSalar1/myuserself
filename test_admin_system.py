#!/usr/bin/env python3
"""
تست سیستم ادمین جدید
بررسی دسترسی‌های مختلف ادمین‌ها
"""

from unified_bot_launcher import UnifiedBotLauncher

def test_admin_permissions():
    """تست سیستم دسترسی ادمین‌ها"""
    print("🔍 تست سیستم دسترسی ادمین‌ها...")
    
    # ایجاد لانچر
    launcher = UnifiedBotLauncher()
    
    print(f"\n👑 ادمین اصلی لانچر: {launcher.launcher_admin_id}")
    
    print("\n📋 تنظیمات ادمین‌های بات‌ها:")
    for bot_id in range(1, 10):
        if bot_id in launcher.bot_configs:
            admin_id = launcher.bot_configs[bot_id]['admin_id']
            print(f"  بات {bot_id}: {admin_id}")
    
    print("\n🔐 آیدی‌های مورد انتظار (درخواست کاربر):")
    expected_admins = {
        1: 7850529246,
        2: 7419698159,
        3: 7607882302,
        4: 7739974888,
        5: 7346058093,
        6: 7927398744,
        7: 8092847456,
        8: 7220521953,
        9: 7143723023
    }
    
    print("  تطبیق تنظیمات:")
    all_correct = True
    for bot_id, expected_admin in expected_admins.items():
        current_admin = launcher.bot_configs[bot_id]['admin_id']
        if current_admin == expected_admin:
            print(f"    ✅ بات {bot_id}: {current_admin} (صحیح)")
        else:
            print(f"    ❌ بات {bot_id}: {current_admin} ← باید {expected_admin} باشد")
            all_correct = False
    
    if all_correct:
        print("\n✅ همه تنظیمات ادمین صحیح است!")
    else:
        print("\n❌ برخی تنظیمات ادمین نیاز به اصلاح دارند")
    
    # تست دسترسی‌ها
    print("\n🧪 تست دسترسی‌های ادمین:")
    
    # تست ادمین اصلی لانچر
    launcher_admin = launcher.launcher_admin_id
    print(f"  👑 ادمین لانچر {launcher_admin}:")
    for bot_id in range(1, 10):
        can_control = launcher.can_control_bot(launcher_admin, bot_id)
        print(f"    بات {bot_id}: {'✅ دسترسی دارد' if can_control else '❌ دسترسی ندارد'}")
    
    # تست ادمین‌های بات‌ها
    print(f"\n  🔧 ادمین‌های بات‌ها:")
    for bot_id in range(1, 5):  # تست چند بات برای نمونه
        admin_id = launcher.bot_configs[bot_id]['admin_id']
        print(f"    ادمین بات {bot_id} ({admin_id}):")
        for target_bot in range(1, 10):
            can_control = launcher.can_control_bot(admin_id, target_bot)
            status = "✅ دسترسی دارد" if can_control else "❌ دسترسی ندارد"
            if target_bot == bot_id:
                expected = "✅"
            else:
                expected = "❌"
            if (can_control and expected == "✅") or (not can_control and expected == "❌"):
                print(f"      بات {target_bot}: {status} ✓")
            else:
                print(f"      بات {target_bot}: {status} ✗ (خطا!)")

if __name__ == "__main__":
    test_admin_permissions()