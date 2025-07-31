#!/bin/bash

# اسکریپت شروع سیستم مدیریت ربات‌های تلگرام
# Telegram Bots Management System Start Script

set -e

# تنظیمات
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BOT_USER="telegrambot"
LOG_FILE="/var/log/telegram-bots/startup.log"

# تابع لاگ
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# بررسی دسترسی root
if [[ $EUID -ne 0 ]]; then
   echo "❌ این اسکریپت باید با دسترسی root اجرا شود"
   echo "استفاده کنید از: sudo $0"
   exit 1
fi

log "🚀 شروع سیستم مدیریت ربات‌های تلگرام..."

# بررسی وجود فایل‌های ضروری
if [ ! -f "/home/$BOT_USER/telegram-bots/.env" ]; then
    log "❌ فایل .env یافت نشد!"
    log "لطفاً ابتدا فایل .env را از .env.example کپی کنید و آن را پیکربندی کنید"
    exit 1
fi

# بررسی وضعیت سرویس‌ها
check_service() {
    local service=$1
    if systemctl is-enabled "$service" &>/dev/null; then
        log "✅ سرویس $service فعال است"
        return 0
    else
        log "❌ سرویس $service فعال نیست"
        return 1
    fi
}

# فعال‌سازی سرویس‌ها در صورت نیاز
enable_services() {
    local services=("telegram-bots.service" "telegram-bots-monitor.service" "telegram-bots-report.service")
    
    for service in "${services[@]}"; do
        if ! check_service "$service"; then
            log "🔧 فعال‌سازی $service"
            systemctl enable "$service"
        fi
    done
}

# شروع سرویس‌ها
start_services() {
    local services=("telegram-bots.service" "telegram-bots-monitor.service" "telegram-bots-report.service")
    
    for service in "${services[@]}"; do
        log "🚀 شروع $service"
        if systemctl start "$service"; then
            log "✅ $service شروع شد"
        else
            log "❌ خطا در شروع $service"
            systemctl status "$service" --no-pager >> "$LOG_FILE"
        fi
    done
}

# شروع nginx
start_nginx() {
    log "🌐 شروع Nginx"
    if systemctl start nginx; then
        log "✅ Nginx شروع شد"
    else
        log "❌ خطا در شروع Nginx"
        systemctl status nginx --no-pager >> "$LOG_FILE"
    fi
}

# بررسی وضعیت نهایی
check_final_status() {
    log "📊 بررسی وضعیت نهایی"
    
    local services=("telegram-bots.service" "telegram-bots-monitor.service" "telegram-bots-report.service" "nginx.service")
    local failed_services=()
    
    for service in "${services[@]}"; do
        if systemctl is-active "$service" &>/dev/null; then
            log "✅ $service: فعال"
        else
            log "❌ $service: غیرفعال"
            failed_services+=("$service")
        fi
    done
    
    if [ ${#failed_services[@]} -eq 0 ]; then
        log "🎉 همه سرویس‌ها با موفقیت شروع شدند!"
        
        # نمایش آدرس‌های دسترسی
        SERVER_IP=$(hostname -I | awk '{print $1}')
        log "🌐 آدرس وب پنل: http://$SERVER_IP"
        log "📊 آدرس API: http://$SERVER_IP/api"
        log "📋 آدرس لاگ‌ها: http://$SERVER_IP/logs"
        
        return 0
    else
        log "⚠️ برخی سرویس‌ها شروع نشدند: ${failed_services[*]}"
        return 1
    fi
}

# اجرای مراحل
main() {
    enable_services
    start_services
    start_nginx
    
    # تاخیر برای راه‌اندازی
    log "⏳ انتظار برای راه‌اندازی کامل سرویس‌ها..."
    sleep 10
    
    if check_final_status; then
        log "✅ سیستم آماده است!"
        
        # نمایش راهنمای سریع
        echo ""
        echo "📋 دستورات مفید:"
        echo "• بررسی وضعیت: sudo systemctl status telegram-bots.service"
        echo "• مشاهده لاگ‌ها: sudo journalctl -fu telegram-bots.service"
        echo "• توقف سیستم: ./stop.sh"
        echo "• ری‌استارت: ./restart.sh"
        echo ""
        
        exit 0
    else
        log "❌ برخی مشکلات در راه‌اندازی وجود دارد"
        echo ""
        echo "🔍 برای عیب‌یابی:"
        echo "• بررسی لاگ‌ها: sudo journalctl -xe"
        echo "• بررسی وضعیت: systemctl status telegram-bots.service"
        echo "• لاگ راه‌اندازی: cat $LOG_FILE"
        echo ""
        
        exit 1
    fi
}

# اجرای اسکریپت
main "$@"