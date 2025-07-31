#!/bin/bash

# اسکریپت توقف سیستم مدیریت ربات‌های تلگرام
# Telegram Bots Management System Stop Script

set -e

# تنظیمات
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/var/log/telegram-bots/shutdown.log"

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

log "⏹️ شروع توقف سیستم مدیریت ربات‌های تلگرام..."

# توقف سرویس‌ها
stop_services() {
    local services=("telegram-bots.service" "telegram-bots-monitor.service" "telegram-bots-report.service")
    
    for service in "${services[@]}"; do
        log "⏹️ توقف $service"
        if systemctl is-active "$service" &>/dev/null; then
            if systemctl stop "$service"; then
                log "✅ $service متوقف شد"
            else
                log "❌ خطا در توقف $service"
                systemctl status "$service" --no-pager >> "$LOG_FILE" 2>/dev/null || true
            fi
        else
            log "ℹ️ $service قبلاً متوقف بود"
        fi
    done
}

# توقف nginx
stop_nginx() {
    log "🌐 توقف Nginx"
    if systemctl is-active nginx &>/dev/null; then
        if systemctl stop nginx; then
            log "✅ Nginx متوقف شد"
        else
            log "❌ خطا در توقف Nginx"
        fi
    else
        log "ℹ️ Nginx قبلاً متوقف بود"
    fi
}

# کشتن پروسه‌های باقی‌مانده
kill_remaining_processes() {
    log "🔪 کشتن پروسه‌های باقی‌مانده..."
    
    # یافتن پروسه‌های Python مربوط به ربات‌ها
    local bot_pids=$(pgrep -f "python.*bot" 2>/dev/null || true)
    
    if [ ! -z "$bot_pids" ]; then
        log "🔍 پروسه‌های یافت شده: $bot_pids"
        
        # ابتدا SIGTERM ارسال کنیم
        for pid in $bot_pids; do
            if kill -TERM "$pid" 2>/dev/null; then
                log "📤 SIGTERM ارسال شد به PID $pid"
            fi
        done
        
        # انتظار 10 ثانیه
        sleep 10
        
        # اگر هنوز زنده هستند، SIGKILL ارسال کنیم
        for pid in $bot_pids; do
            if kill -0 "$pid" 2>/dev/null; then
                if kill -KILL "$pid" 2>/dev/null; then
                    log "💀 SIGKILL ارسال شد به PID $pid"
                fi
            fi
        done
    else
        log "ℹ️ هیچ پروسه باقی‌مانده‌ای یافت نشد"
    fi
}

# بررسی وضعیت نهایی
check_final_status() {
    log "📊 بررسی وضعیت نهایی"
    
    local services=("telegram-bots.service" "telegram-bots-monitor.service" "telegram-bots-report.service" "nginx.service")
    local still_running=()
    
    for service in "${services[@]}"; do
        if systemctl is-active "$service" &>/dev/null; then
            log "⚠️ $service: هنوز فعال"
            still_running+=("$service")
        else
            log "✅ $service: متوقف"
        fi
    done
    
    # بررسی پروسه‌های Python
    local remaining_processes=$(pgrep -f "python.*bot" 2>/dev/null | wc -l)
    if [ "$remaining_processes" -gt 0 ]; then
        log "⚠️ $remaining_processes پروسه Python هنوز در حال اجرا"
        still_running+=("python-processes")
    fi
    
    if [ ${#still_running[@]} -eq 0 ]; then
        log "✅ همه سرویس‌ها و پروسه‌ها متوقف شدند"
        return 0
    else
        log "⚠️ برخی سرویس‌ها هنوز در حال اجرا: ${still_running[*]}"
        return 1
    fi
}

# آزادسازی پورت‌ها
free_ports() {
    log "🔓 بررسی و آزادسازی پورت‌های اشغال شده..."
    
    local ports=(5000 80 443)
    
    for port in "${ports[@]}"; do
        local pid=$(lsof -t -i:$port 2>/dev/null || true)
        if [ ! -z "$pid" ]; then
            log "🔍 پورت $port توسط PID $pid اشغال شده"
            if kill -TERM "$pid" 2>/dev/null; then
                log "📤 SIGTERM ارسال شد به PID $pid (پورت $port)"
                sleep 2
                
                # اگر هنوز زنده است، SIGKILL ارسال کنیم
                if kill -0 "$pid" 2>/dev/null; then
                    kill -KILL "$pid" 2>/dev/null && log "💀 SIGKILL ارسال شد به PID $pid"
                fi
            fi
        else
            log "✅ پورت $port آزاد است"
        fi
    done
}

# اجرای مراحل
main() {
    stop_services
    stop_nginx
    
    # تاخیر برای توقف تدریجی
    log "⏳ انتظار برای توقف تدریجی سرویس‌ها..."
    sleep 5
    
    kill_remaining_processes
    free_ports
    
    if check_final_status; then
        log "🎉 سیستم با موفقیت متوقف شد!"
        
        # نمایش راهنمای سریع
        echo ""
        echo "📋 دستورات مفید:"
        echo "• شروع مجدد: ./start.sh"
        echo "• بررسی وضعیت: sudo systemctl status telegram-bots.service"
        echo "• مشاهده لاگ‌ها: cat $LOG_FILE"
        echo ""
        
        exit 0
    else
        log "⚠️ برخی مشکلات در توقف سیستم وجود دارد"
        echo ""
        echo "🔍 برای عیب‌یابی:"
        echo "• بررسی سرویس‌ها: systemctl status telegram-bots.service"
        echo "• بررسی پروسه‌ها: ps aux | grep python"
        echo "• بررسی پورت‌ها: netstat -tlnp | grep -E ':5000|:80|:443'"
        echo "• لاگ توقف: cat $LOG_FILE"
        echo ""
        
        exit 1
    fi
}

# اجرای اسکریپت
main "$@"