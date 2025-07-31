#!/bin/bash

# اسکریپت ری‌استارت سیستم مدیریت ربات‌های تلگرام
# Telegram Bots Management System Restart Script

set -e

# تنظیمات
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/telegram-bots/restart.log"

# تابع لاگ
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE" 2>/dev/null || echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# بررسی دسترسی root
if [[ $EUID -ne 0 ]]; then
   echo "❌ این اسکریپت باید با دسترسی root اجرا شود"
   echo "استفاده کنید از: sudo $0"
   exit 1
fi

log "🔄 شروع ری‌استارت سیستم مدیریت ربات‌های تلگرام..."

# توقف تدریجی سرویس‌ها
graceful_stop() {
    log "⏹️ توقف تدریجی سرویس‌ها..."
    
    local services=("telegram-bots.service" "telegram-bots-monitor.service" "telegram-bots-report.service")
    
    # ابتدا سرویس‌های فرعی را متوقف کنیم
    for service in "${services[@]:1}"; do
        if systemctl is-active "$service" &>/dev/null; then
            log "⏹️ توقف $service"
            systemctl stop "$service"
        fi
    done
    
    # سپس سرویس اصلی
    if systemctl is-active "${services[0]}" &>/dev/null; then
        log "⏹️ توقف ${services[0]}"
        systemctl stop "${services[0]}"
    fi
    
    # انتظار برای توقف کامل
    log "⏳ انتظار برای توقف کامل..."
    sleep 10
}

# شروع تدریجی سرویس‌ها
graceful_start() {
    log "🚀 شروع تدریجی سرویس‌ها..."
    
    local services=("telegram-bots.service" "telegram-bots-monitor.service" "telegram-bots-report.service")
    
    # ابتدا سرویس اصلی را شروع کنیم
    log "🚀 شروع ${services[0]}"
    if systemctl start "${services[0]}"; then
        log "✅ ${services[0]} شروع شد"
    else
        log "❌ خطا در شروع ${services[0]}"
        return 1
    fi
    
    # انتظار برای آماده شدن سرویس اصلی
    log "⏳ انتظار برای آماده شدن سرویس اصلی..."
    sleep 15
    
    # سپس سرویس‌های فرعی
    for service in "${services[@]:1}"; do
        log "🚀 شروع $service"
        if systemctl start "$service"; then
            log "✅ $service شروع شد"
        else
            log "❌ خطا در شروع $service"
            systemctl status "$service" --no-pager >> "$LOG_FILE" 2>/dev/null || true
        fi
        sleep 5
    done
}

# ری‌استارت nginx
restart_nginx() {
    log "🌐 ری‌استارت Nginx"
    if systemctl restart nginx; then
        log "✅ Nginx ری‌استارت شد"
    else
        log "❌ خطا در ری‌استارت Nginx"
        systemctl status nginx --no-pager >> "$LOG_FILE" 2>/dev/null || true
    fi
}

# بررسی سلامت سیستم
health_check() {
    log "🏥 بررسی سلامت سیستم..."
    
    local services=("telegram-bots.service" "telegram-bots-monitor.service" "telegram-bots-report.service" "nginx.service")
    local unhealthy_services=()
    
    for service in "${services[@]}"; do
        if systemctl is-active "$service" &>/dev/null; then
            log "✅ $service: سالم"
        else
            log "❌ $service: ناسالم"
            unhealthy_services+=("$service")
        fi
    done
    
    # بررسی پورت‌های شبکه
    local ports=(5000 80)
    for port in "${ports[@]}"; do
        if netstat -tlnp | grep ":$port " &>/dev/null; then
            log "✅ پورت $port: فعال"
        else
            log "❌ پورت $port: غیرفعال"
            unhealthy_services+=("port-$port")
        fi
    done
    
    # تست HTTP endpoint
    if curl -f -s --max-time 10 "http://localhost/health" > /dev/null 2>&1; then
        log "✅ Health endpoint: پاسخگو"
    else
        log "❌ Health endpoint: عدم پاسخ"
        unhealthy_services+=("health-endpoint")
    fi
    
    if [ ${#unhealthy_services[@]} -eq 0 ]; then
        log "🎉 همه سرویس‌ها سالم هستند"
        return 0
    else
        log "⚠️ سرویس‌های ناسالم: ${unhealthy_services[*]}"
        return 1
    fi
}

# بک‌آپ سریع قبل از ری‌استارت
quick_backup() {
    log "💾 ایجاد بک‌آپ سریع قبل از ری‌استارت..."
    
    local backup_dir="/tmp/pre-restart-backup-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # بک‌آپ فایل‌های مهم
    local important_files=(
        "/home/telegrambot/telegram-bots/.env"
        "/home/telegrambot/telegram-bots/unified_bot_launcher.py"
        "/home/telegrambot/telegram-bots/monitoring_bot.py"
        "/home/telegrambot/telegram-bots/report_bot.py"
    )
    
    for file in "${important_files[@]}"; do
        if [ -f "$file" ]; then
            cp "$file" "$backup_dir/" 2>/dev/null || true
        fi
    done
    
    # بک‌آپ session files
    if [ -d "/home/telegrambot/telegram-bots/sessions" ]; then
        cp -r "/home/telegrambot/telegram-bots/sessions" "$backup_dir/" 2>/dev/null || true
    fi
    
    log "✅ بک‌آپ سریع در $backup_dir ایجاد شد"
}

# بررسی و تعمیر مجوزها
fix_permissions() {
    log "🔧 بررسی و تعمیر مجوزها..."
    
    local dirs=(
        "/home/telegrambot/telegram-bots"
        "/var/log/telegram-bots"
    )
    
    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            chown -R telegrambot:telegrambot "$dir" 2>/dev/null || true
            chmod -R 755 "$dir" 2>/dev/null || true
            log "🔧 مجوزهای $dir تعمیر شد"
        fi
    done
    
    # مجوز خاص برای .env
    if [ -f "/home/telegrambot/telegram-bots/.env" ]; then
        chmod 600 "/home/telegrambot/telegram-bots/.env"
        chown telegrambot:telegrambot "/home/telegrambot/telegram-bots/.env"
        log "🔧 مجوزهای .env تعمیر شد"
    fi
}

# پاک کردن فایل‌های قفل
cleanup_locks() {
    log "🧹 پاک کردن فایل‌های قفل و cache..."
    
    # فایل‌های قفل session
    find /home/telegrambot/telegram-bots -name "*.session-journal" -delete 2>/dev/null || true
    
    # فایل‌های cache Python
    find /home/telegrambot/telegram-bots -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find /home/telegrambot/telegram-bots -name "*.pyc" -delete 2>/dev/null || true
    
    # فایل‌های لاگ قدیمی
    find /var/log/telegram-bots -name "*.log.*" -mtime +7 -delete 2>/dev/null || true
    
    log "✅ پاک‌سازی کامل شد"
}

# اجرای مراحل
main() {
    local start_time=$(date +%s)
    
    log "🎯 شروع فرآیند ری‌استارت کامل"
    
    # مراحل آماده‌سازی
    quick_backup
    fix_permissions
    cleanup_locks
    
    # توقف سرویس‌ها
    graceful_stop
    
    # انتظار کوتاه
    log "⏳ انتظار برای تمیز شدن منابع سیستم..."
    sleep 5
    
    # شروع سرویس‌ها
    graceful_start
    
    # ری‌استارت nginx
    restart_nginx
    
    # انتظار برای آماده شدن کامل
    log "⏳ انتظار برای آماده شدن کامل سیستم..."
    sleep 20
    
    # بررسی سلامت
    if health_check; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        log "🎉 ری‌استارت با موفقیت کامل شد!"
        log "⏱️ مدت زمان: ${duration} ثانیه"
        
        # نمایش اطلاعات سیستم
        SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
        log "🌐 آدرس وب پنل: http://$SERVER_IP"
        log "📊 آدرس API: http://$SERVER_IP/api"
        log "🏥 Health Check: http://$SERVER_IP/health"
        
        echo ""
        echo "📋 دستورات مفید:"
        echo "• بررسی وضعیت: sudo systemctl status telegram-bots.service"
        echo "• مشاهده لاگ‌ها: sudo journalctl -fu telegram-bots.service"
        echo "• توقف سیستم: ./stop.sh"
        echo "• لاگ ری‌استارت: cat $LOG_FILE"
        echo ""
        
        exit 0
    else
        log "❌ مشکل در آماده‌سازی سیستم پس از ری‌استارت"
        echo ""
        echo "🔍 برای عیب‌یابی:"
        echo "• بررسی لاگ‌ها: sudo journalctl -xe"
        echo "• وضعیت سرویس‌ها: systemctl status telegram-bots.service"
        echo "• لاگ ری‌استارت: cat $LOG_FILE"
        echo "• تست health endpoint: curl http://localhost/health"
        echo ""
        
        exit 1
    fi
}

# مدیریت خطا
trap 'log "❌ خطا در فرآیند ری‌استارت"; exit 1' ERR

# اجرای اسکریپت
main "$@"