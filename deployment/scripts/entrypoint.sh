#!/bin/bash

# نقطه ورود اصلی برای container
# Main entrypoint script for container

set -e

echo "🚀 شروع سیستم مدیریت ربات‌های تلگرام..."
echo "🚀 Starting Telegram Bots Management System..."

# تابع لاگ
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ENTRYPOINT] $1"
}

log "Initializing container..."

# بررسی متغیرهای محیط ضروری
check_required_env() {
    local required_vars=(
        "BOT_MODE"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log "❌ متغیر محیط $var تنظیم نشده است"
            log "❌ Required environment variable $var is not set"
            exit 1
        fi
    done
    
    log "✅ متغیرهای محیط اساسی تایید شدند"
    log "✅ Basic environment variables verified"
}

# ایجاد دایرکتری‌های لازم
create_directories() {
    local dirs=(
        "/app/data"
        "/app/logs"
        "/app/sessions" 
        "/app/backups"
        "/app/bots/bot1"
        "/app/bots/bot2"
        "/app/bots/bot3"
        "/app/bots/bot4"
        "/app/bots/bot5"
        "/app/bots/bot6"
        "/app/bots/bot7"
        "/app/bots/bot8"
        "/app/bots/bot9"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log "📁 ایجاد دایرکتری: $dir"
        fi
    done
    
    # تنظیم مجوزها
    chown -R telegrambot:telegrambot /app/data /app/logs /app/sessions /app/backups
    chmod -R 755 /app/data /app/logs /app/sessions /app/backups
    
    log "✅ دایرکتری‌ها آماده شدند"
    log "✅ Directories prepared"
}

# بررسی و ایجاد فایل .env
setup_env_file() {
    if [ ! -f "/app/.env" ]; then
        if [ -f "/app/.env.example" ]; then
            log "📝 کپی .env.example به .env"
            cp /app/.env.example /app/.env
        else
            log "⚠️ فایل .env یافت نشد، ایجاد فایل پایه"
            cat > /app/.env << EOF
BOT_MODE=production
DEBUG=false
LOG_LEVEL=INFO
TOTAL_BOTS=9
WEB_PORT=5000
WEB_HOST=0.0.0.0
EOF
        fi
    fi
    
    # تنظیم مجوزهای امن برای .env
    chmod 600 /app/.env
    chown telegrambot:telegrambot /app/.env
    
    log "✅ فایل .env آماده است"
    log "✅ .env file is ready"
}

# راه‌اندازی دیتابیس
setup_database() {
    log "🗄️ راه‌اندازی دیتابیس..."
    log "🗄️ Setting up database..."
    
    # انتظار برای آماده شدن PostgreSQL
    if [ ! -z "$DATABASE_URL" ]; then
        log "⏳ انتظار برای آماده شدن PostgreSQL..."
        
        max_attempts=30
        attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if python3 -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.close()
    print('PostgreSQL is ready')
    exit(0)
except:
    exit(1)
" 2>/dev/null; then
                log "✅ PostgreSQL آماده است"
                break
            fi
            
            log "⏳ تلاش $attempt از $max_attempts - انتظار برای PostgreSQL"
            sleep 2
            attempt=$((attempt + 1))
        done
        
        if [ $attempt -gt $max_attempts ]; then
            log "❌ PostgreSQL در زمان مقرر آماده نشد"
            log "❌ PostgreSQL did not become ready in time"
        fi
    fi
    
    # راه‌اندازی جداول (در صورت وجود اسکریپت)
    if [ -f "/app/deployment/sql/init_tables.py" ]; then
        log "🏗️ راه‌اندازی جداول دیتابیس"
        python3 /app/deployment/sql/init_tables.py
    fi
}

# راه‌اندازی Redis
setup_redis() {
    if [ ! -z "$REDIS_URL" ]; then
        log "🔴 بررسی اتصال Redis..."
        log "🔴 Checking Redis connection..."
        
        max_attempts=15
        attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if python3 -c "
import redis
import os
try:
    r = redis.from_url(os.environ['REDIS_URL'])
    r.ping()
    print('Redis is ready')
    exit(0)
except:
    exit(1)
" 2>/dev/null; then
                log "✅ Redis آماده است"
                break
            fi
            
            log "⏳ تلاش $attempt از $max_attempts - انتظار برای Redis"
            sleep 2
            attempt=$((attempt + 1))
        done
    fi
}

# پیکربندی supervisor
setup_supervisor() {
    log "⚙️ پیکربندی Supervisor..."
    
    # اطمینان از وجود فایل پیکربندی
    if [ ! -f "/etc/supervisor/conf.d/supervisord.conf" ]; then
        log "❌ فایل پیکربندی Supervisor یافت نشد"
        exit 1
    fi
    
    # ایجاد دایرکتری لاگ supervisor
    mkdir -p /var/log/supervisor
    
    log "✅ Supervisor آماده است"
}

# تنظیم cron
setup_cron() {
    log "⏰ راه‌اندازی Cron..."
    
    # شروع cron daemon
    service cron start
    
    log "✅ Cron راه‌اندازی شد"
}

# تنظیم logrotate
setup_logrotate() {
    log "📋 پیکربندی Log Rotation..."
    
    # اجرای logrotate برای اولین بار
    if [ -f "/etc/logrotate.d/telegram-bots" ]; then
        logrotate -f /etc/logrotate.d/telegram-bots
    fi
    
    log "✅ Log Rotation پیکربندی شد"
}

# تست سیستم
test_system() {
    log "🧪 تست سیستم..."
    
    # تست Python modules
    python3 -c "
import pyrogram
import asyncio
import sqlite3
import json
import logging
print('✅ همه ماژول‌های اصلی موجود هستند')
print('✅ All core modules are available')
"
    
    # تست دایرکتری‌ها
    for dir in "/app/data" "/app/logs" "/app/sessions"; do
        if [ ! -w "$dir" ]; then
            log "❌ دایرکتری $dir قابل نوشتن نیست"
            exit 1
        fi
    done
    
    log "✅ تست‌های سیستم موفق بودند"
    log "✅ System tests passed"
}

# نمایش اطلاعات سیستم
show_system_info() {
    log "📊 اطلاعات سیستم:"
    log "📊 System Information:"
    echo "===========================================" 
    echo "🐍 Python Version: $(python3 --version)"
    echo "🌍 Environment: ${BOT_MODE:-unknown}"
    echo "📁 Working Directory: $(pwd)"
    echo "👤 User: $(whoami)"
    echo "🕐 Time Zone: ${TZ:-UTC}"
    echo "💾 Disk Space: $(df -h /app | tail -1 | awk '{print $4}') free"
    echo "🧠 Memory: $(free -h | grep Mem | awk '{print $7}') available"
    echo "===========================================" 
}

# اجرای تمام مراحل setup
main() {
    log "🎯 شروع راه‌اندازی container"
    log "🎯 Starting container setup"
    
    check_required_env
    create_directories
    setup_env_file
    setup_database
    setup_redis
    setup_supervisor
    setup_cron
    setup_logrotate
    test_system
    show_system_info
    
    log "✅ راه‌اندازی کامل شد"
    log "✅ Setup completed successfully"
    
    # تغییر به کاربر telegrambot برای اجرای برنامه
    if [ "$1" = "supervisord" ]; then
        log "🚀 شروع Supervisor..."
        log "🚀 Starting Supervisor..."
        exec "$@"
    else
        log "🔧 اجرای دستور: $@"
        log "🔧 Executing command: $@"
        exec su-exec telegrambot "$@"
    fi
}

# اجرای main function
main "$@"