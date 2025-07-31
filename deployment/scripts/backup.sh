#!/bin/bash

# اسکریپت بک‌آپ خودکار برای سیستم ربات‌های تلگرام
# Automated Backup Script for Telegram Bots System

set -e

# متغیرهای پیکربندی
BACKUP_DIR="/app/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="telegram-bots-backup-$TIMESTAMP"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# تابع لاگ
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [BACKUP] $1"
}

# ایجاد دایرکتری بک‌آپ
mkdir -p "$BACKUP_DIR"

log "🎯 شروع فرآیند بک‌آپ: $BACKUP_NAME"

# بک‌آپ دیتابیس PostgreSQL
backup_database() {
    log "🗄️ بک‌آپ پایگاه داده PostgreSQL..."
    
    if [ ! -z "$DATABASE_URL" ]; then
        pg_dump "$DATABASE_URL" > "$BACKUP_DIR/$BACKUP_NAME-database.sql"
        log "✅ بک‌آپ پایگاه داده کامل شد"
    else
        log "⚠️ DATABASE_URL تنظیم نشده - از بک‌آپ دیتابیس صرف‌نظر شد"
    fi
}

# بک‌آپ فایل‌های session
backup_sessions() {
    log "🔐 بک‌آپ فایل‌های session..."
    
    if [ -d "/app/sessions" ]; then
        tar -czf "$BACKUP_DIR/$BACKUP_NAME-sessions.tar.gz" -C /app sessions/
        log "✅ بک‌آپ فایل‌های session کامل شد"
    else
        log "⚠️ دایرکتری sessions یافت نشد"
    fi
}

# بک‌آپ پیکربندی‌ها
backup_config() {
    log "⚙️ بک‌آپ فایل‌های پیکربندی..."
    
    local config_files=(
        "/app/.env"
        "/app/deployment/config.py"
        "/app/unified_bot_launcher.py"
        "/app/monitoring_bot.py"
        "/app/report_bot.py"
    )
    
    mkdir -p "$BACKUP_DIR/config"
    
    for file in "${config_files[@]}"; do
        if [ -f "$file" ]; then
            cp "$file" "$BACKUP_DIR/config/"
            log "📄 کپی شد: $file"
        fi
    done
    
    tar -czf "$BACKUP_DIR/$BACKUP_NAME-config.tar.gz" -C "$BACKUP_DIR" config/
    rm -rf "$BACKUP_DIR/config"
    
    log "✅ بک‌آپ فایل‌های پیکربندی کامل شد"
}

# بک‌آپ لاگ‌های مهم
backup_logs() {
    log "📋 بک‌آپ لاگ‌های مهم..."
    
    if [ -d "/app/logs" ]; then
        # فقط لاگ‌های 7 روز اخیر
        find /app/logs -name "*.log" -mtime -7 -exec tar -czf "$BACKUP_DIR/$BACKUP_NAME-logs.tar.gz" {} +
        log "✅ بک‌آپ لاگ‌های مهم کامل شد"
    else
        log "⚠️ دایرکتری logs یافت نشد"
    fi
}

# بک‌آپ داده‌های کاربری
backup_user_data() {
    log "👤 بک‌آپ داده‌های کاربری..."
    
    if [ -d "/app/data" ]; then
        tar -czf "$BACKUP_DIR/$BACKUP_NAME-data.tar.gz" -C /app data/
        log "✅ بک‌آپ داده‌های کاربری کامل شد"
    else
        log "⚠️ دایرکتری data یافت نشد"
    fi
}

# آپلود به S3 (اختیاری)
upload_to_s3() {
    if [ ! -z "$S3_BACKUP_BUCKET" ] && [ ! -z "$S3_ACCESS_KEY" ] && [ ! -z "$S3_SECRET_KEY" ]; then
        log "☁️ آپلود بک‌آپ به S3..."
        
        # نصب AWS CLI در صورت عدم وجود
        if ! command -v aws &> /dev/null; then
            pip install awscli
        fi
        
        # تنظیم credentials
        export AWS_ACCESS_KEY_ID="$S3_ACCESS_KEY"
        export AWS_SECRET_ACCESS_KEY="$S3_SECRET_KEY"
        
        # آپلود فایل‌ها
        for file in "$BACKUP_DIR"/$BACKUP_NAME-*.{sql,tar.gz}; do
            if [ -f "$file" ]; then
                aws s3 cp "$file" "s3://$S3_BACKUP_BUCKET/$(basename "$file")"
                log "☁️ آپلود شد: $(basename "$file")"
            fi
        done
        
        log "✅ آپلود به S3 کامل شد"
    else
        log "⚠️ اطلاعات S3 تنظیم نشده - از آپلود صرف‌نظر شد"
    fi
}

# پاک کردن بک‌آپ‌های قدیمی
cleanup_old_backups() {
    log "🧹 پاک کردن بک‌آپ‌های قدیمی (بیش از $RETENTION_DAYS روز)..."
    
    find "$BACKUP_DIR" -name "telegram-bots-backup-*" -mtime +$RETENTION_DAYS -delete
    
    # پاک کردن از S3 نیز
    if [ ! -z "$S3_BACKUP_BUCKET" ]; then
        aws s3 ls "s3://$S3_BACKUP_BUCKET/" | while read -r line; do
            createDate=$(echo "$line" | awk '{print $1" "$2}')
            createDate=$(date -d"$createDate" +%s)
            olderThan=$(date -d"$RETENTION_DAYS days ago" +%s)
            
            if [[ $createDate -lt $olderThan ]]; then
                fileName=$(echo "$line" | awk '{print $4}')
                if [[ $fileName == *"telegram-bots-backup-"* ]]; then
                    aws s3 rm "s3://$S3_BACKUP_BUCKET/$fileName"
                    log "🗑️ حذف شد از S3: $fileName"
                fi
            fi
        done
    fi
    
    log "✅ پاک کردن بک‌آپ‌های قدیمی کامل شد"
}

# ایجاد فهرست بک‌آپ
create_backup_manifest() {
    log "📄 ایجاد فهرست بک‌آپ..."
    
    cat > "$BACKUP_DIR/$BACKUP_NAME-manifest.json" << EOF
{
    "backup_name": "$BACKUP_NAME",
    "timestamp": "$TIMESTAMP",
    "date": "$(date)",
    "version": "1.0",
    "files": [
EOF

    local first=true
    for file in "$BACKUP_DIR"/$BACKUP_NAME-*.{sql,tar.gz}; do
        if [ -f "$file" ]; then
            if [ "$first" = true ]; then
                first=false
            else
                echo "," >> "$BACKUP_DIR/$BACKUP_NAME-manifest.json"
            fi
            
            local filename=$(basename "$file")
            local filesize=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
            local checksum=$(sha256sum "$file" | cut -d' ' -f1)
            
            cat >> "$BACKUP_DIR/$BACKUP_NAME-manifest.json" << EOF
        {
            "filename": "$filename",
            "size": $filesize,
            "checksum": "$checksum"
        }
EOF
        fi
    done

    cat >> "$BACKUP_DIR/$BACKUP_NAME-manifest.json" << EOF
    ],
    "total_files": $(ls -1 "$BACKUP_DIR"/$BACKUP_NAME-*.{sql,tar.gz} 2>/dev/null | wc -l),
    "total_size": $(du -sb "$BACKUP_DIR"/$BACKUP_NAME-* 2>/dev/null | awk '{sum += $1} END {print sum}')
}
EOF

    log "✅ فهرست بک‌آپ ایجاد شد"
}

# ارسال اطلاع‌رسانی
send_notification() {
    local status=$1
    local message=$2
    
    if [ ! -z "$ALERT_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🔄 Backup $status: $message\"}" \
            "$ALERT_WEBHOOK_URL" || true
    fi
    
    if [ ! -z "$NOTIFICATION_EMAIL" ] && [ ! -z "$SMTP_SERVER" ]; then
        # ارسال ایمیل (نیاز به پیکربندی mailutils)
        echo "$message" | mail -s "Backup $status - Telegram Bots System" "$NOTIFICATION_EMAIL" || true
    fi
}

# اجرای فرآیند بک‌آپ
main() {
    local start_time=$(date +%s)
    
    log "🚀 شروع فرآیند بک‌آپ کامل"
    
    # اجرای مراحل بک‌آپ
    backup_database
    backup_sessions
    backup_config
    backup_logs
    backup_user_data
    
    # ایجاد فهرست
    create_backup_manifest
    
    # آپلود (اختیاری)
    upload_to_s3
    
    # پاک کردن قدیمی‌ها
    cleanup_old_backups
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local total_size=$(du -sh "$BACKUP_DIR"/$BACKUP_NAME-* 2>/dev/null | awk '{sum += $1} END {print sum}' || echo "0")
    
    log "✅ فرآیند بک‌آپ کامل شد"
    log "⏱️ مدت زمان: ${duration} ثانیه"
    log "📦 حجم کل: $total_size"
    
    # ارسال اطلاع‌رسانی موفقیت
    send_notification "SUCCESS" "Backup completed successfully in ${duration}s. Total size: $total_size"
    
    return 0
}

# مدیریت خطا
trap 'log "❌ خطا در فرآیند بک‌آپ"; send_notification "FAILED" "Backup process failed"; exit 1' ERR

# اجرای اصلی
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi