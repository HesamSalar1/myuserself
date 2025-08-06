#!/usr/bin/env python3
"""
ماژول کنترل اکو برای بات‌های تلگرام
"""

# وضعیت اکو سراسری
_echo_active = False

def set_echo_active(active: bool):
    """تنظیم وضعیت اکو"""
    global _echo_active
    _echo_active = active

def is_echo_active() -> bool:
    """بررسی وضعیت اکو"""
    global _echo_active
    return _echo_active

def toggle_echo() -> bool:
    """تغییر وضعیت اکو"""
    global _echo_active
    _echo_active = not _echo_active
    return _echo_active