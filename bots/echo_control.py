
"""
ماژول کنترل مشترک برای حالت اکو
این فایل بین تمام بات‌ها مشترک است
"""

# متغیر کنترل اکو
echo_active = False

def set_echo_active(status):
    """تنظیم وضعیت اکو"""
    global echo_active
    echo_active = status

def is_echo_active():
    """بررسی وضعیت اکو"""
    global echo_active
    return echo_active
