#!/bin/bash

# اسکریپت Health Check برای container
# Health Check script for container

set -e

# متغیرهای پیکربندی
MAIN_SERVICE_URL="http://localhost:5000/health"
TIMEOUT=10
MAX_RETRIES=3

# تابع لاگ
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [HEALTHCHECK] $1"
}

# بررسی وب سرویس اصلی
check_web_service() {
    log "🌐 بررسی وب سرویس..."
    
    for i in $(seq 1 $MAX_RETRIES); do
        if curl -f -s --max-time $TIMEOUT "$MAIN_SERVICE_URL" > /dev/null 2>&1; then
            log "✅ وب سرویس سالم است"
            return 0
        fi
        
        log "⚠️ تلاش $i از $MAX_RETRIES برای وب سرویس"
        sleep 2
    done
    
    log "❌ وب سرویس پاسخ نمی‌دهد"
    return 1
}

# بررسی پروسه‌های Python
check_python_processes() {
    log "🐍 بررسی پروسه‌های Python..."
    
    # بررسی وجود پروسه‌های مهم
    local required_processes=(
        "unified_bot_launcher.py"
    )
    
    for process in "${required_processes[@]}"; do
        if ! pgrep -f "$process" > /dev/null; then
            log "❌ پروسه $process یافت نشد"
            return 1
        fi
    done
    
    log "✅ پروسه‌های Python سالم هستند"
    return 0
}

# بررسی فایل‌های ضروری
check_critical_files() {
    log "📁 بررسی فایل‌های ضروری..."
    
    local critical_files=(
        "/app/unified_bot_launcher.py"
        "/app/.env"
    )
    
    for file in "${critical_files[@]}"; do
        if [ ! -f "$file" ]; then
            log "❌ فایل ضروری یافت نشد: $file"
            return 1
        fi
    done
    
    log "✅ همه فایل‌های ضروری موجود هستند"
    return 0
}

# بررسی دایرکتری‌ها
check_directories() {
    log "📂 بررسی دایرکتری‌ها..."
    
    local required_dirs=(
        "/app/data"
        "/app/logs"
        "/app/sessions"
        "/app/bots"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            log "❌ دایرکتری یافت نشد: $dir"
            return 1
        fi
        
        if [ ! -w "$dir" ]; then
            log "❌ دایرکتری قابل نوشتن نیست: $dir"
            return 1
        fi
    done
    
    log "✅ همه دایرکتری‌ها سالم هستند"
    return 0
}

# بررسی اتصال دیتابیس
check_database() {
    if [ ! -z "$DATABASE_URL" ]; then
        log "🗄️ بررسی اتصال دیتابیس..."
        
        if python3 -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    conn.close()
    exit(0)
except Exception as e:
    print(f'Database error: {e}')
    exit(1)
" 2>/dev/null; then
            log "✅ اتصال دیتابیس سالم است"
            return 0
        else
            log "❌ مشکل در اتصال دیتابیس"
            return 1
        fi
    fi
    
    return 0  # اگر DATABASE_URL تنظیم نشده، مشکلی نیست
}

# بررسی اتصال Redis
check_redis() {
    if [ ! -z "$REDIS_URL" ]; then
        log "🔴 بررسی اتصال Redis..."
        
        if python3 -c "
import redis
import os
try:
    r = redis.from_url(os.environ['REDIS_URL'])
    r.ping()
    exit(0)
except Exception as e:
    print(f'Redis error: {e}')
    exit(1)
" 2>/dev/null; then
            log "✅ اتصال Redis سالم است"
            return 0
        else
            log "❌ مشکل در اتصال Redis"
            return 1
        fi
    fi
    
    return 0  # اگر REDIS_URL تنظیم نشده، مشکلی نیست
}

# بررسی مصرف منابع
check_resources() {
    log "📊 بررسی مصرف منابع..."
    
    # بررسی حافظه
    local memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ "$memory_usage" -gt 90 ]; then
        log "⚠️ مصرف حافظه بالا: ${memory_usage}%"
        return 1
    fi
    
    # بررسی فضای دیسک
    local disk_usage=$(df /app | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        log "⚠️ فضای دیسک کم: ${disk_usage}%"
        return 1
    fi
    
    log "✅ مصرف منابع در حد طبیعی"
    return 0
}

# بررسی لاگ‌ها برای خطاهای اخیر
check_recent_errors() {
    log "📋 بررسی خطاهای اخیر..."
    
    # بررسی لاگ‌های 5 دقیقه اخیر
    local error_count=0
    
    if [ -d "/app/logs" ]; then
        error_count=$(find /app/logs -name "*.log" -mmin -5 -exec grep -l "ERROR\|CRITICAL" {} \; 2>/dev/null | wc -l)
    fi
    
    if [ "$error_count" -gt 5 ]; then
        log "⚠️ تعداد زیادی خطا در 5 دقیقه اخیر: $error_count"
        return 1
    fi
    
    log "✅ تعداد خطاهای اخیر طبیعی است"
    return 0
}

# اجرای همه بررسی‌ها
main() {
    log "🏥 شروع Health Check"
    
    local checks=(
        "check_critical_files"
        "check_directories" 
        "check_python_processes"
        "check_web_service"
        "check_database"
        "check_redis"
        "check_resources"
        "check_recent_errors"
    )
    
    local failed_checks=()
    
    for check in "${checks[@]}"; do
        if ! $check; then
            failed_checks+=("$check")
        fi
    done
    
    if [ ${#failed_checks[@]} -eq 0 ]; then
        log "✅ همه بررسی‌ها موفق - سیستم سالم است"
        exit 0
    else
        log "❌ بررسی‌های ناموفق: ${failed_checks[*]}"
        log "❌ Failed checks: ${failed_checks[*]}"
        exit 1
    fi
}

# اجرای اصلی
main "$@"