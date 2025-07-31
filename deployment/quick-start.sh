#!/bin/bash

# اسکریپت راه‌اندازی سریع برای StackHost
# Quick Setup Script for StackHost

set -e

echo "🚀 راه‌اندازی سریع سیستم مدیریت 9 ربات تلگرام"
echo "🚀 Quick Setup for 9 Telegram Bots Management System"
echo "================================================="

# بررسی Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker نصب نیست!"
    echo "❌ Docker is not installed!"
    echo "لطفاً ابتدا Docker را نصب کنید"
    echo "Please install Docker first"
    exit 1
fi

# بررسی docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose نصب نیست!"
    echo "❌ Docker Compose is not installed!"
    exit 1
fi

# کپی فایل .env
if [ ! -f ".env" ]; then
    echo "📝 ایجاد فایل .env از نمونه"
    echo "📝 Creating .env file from template"
    cp .env.stackhost.example .env
    
    echo ""
    echo "⚠️ فایل .env ایجاد شد - لطفاً تنظیمات را ویرایش کنید:"
    echo "⚠️ .env file created - Please edit the settings:"
    echo ""
    echo "📋 تنظیمات ضروری:"
    echo "📋 Required settings:"
    echo "  • SECRET_KEY: کلید امنیتی قوی"
    echo "  • DB_PASSWORD: رمز عبور پایگاه داده"
    echo "  • REDIS_PASSWORD: رمز عبور Redis"
    echo "  • ADMIN_TELEGRAM_ID: شناسه تلگرام مدیر"
    echo "  • BOT*_API_ID & BOT*_API_HASH: اطلاعات API ربات‌ها"
    echo ""
    echo "🔧 برای ویرایش: nano .env"
    echo ""
    
    read -p "آیا می‌خواهید الان فایل .env را ویرایش کنید؟ (y/n): " edit_now
    if [[ $edit_now =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    else
        echo "⚠️ حتماً قبل از ادامه فایل .env را ویرایش کنید"
        echo "⚠️ Make sure to edit .env file before continuing"
        exit 0
    fi
fi

# ایجاد دایرکتری‌های لازم
echo "📁 ایجاد دایرکتری‌های لازم"
echo "📁 Creating necessary directories"
mkdir -p data logs sessions backups

# تنظیم مجوزها
chmod 755 data logs sessions backups
chmod +x deployment/scripts/*.sh

# بیلد image
echo "🔨 بیلد Docker images"
echo "🔨 Building Docker images"
docker-compose -f stackhost.yaml build

# شروع سرویس‌ها
echo "🚀 شروع سرویس‌ها"
echo "🚀 Starting services"
docker-compose -f stackhost.yaml up -d

# انتظار برای راه‌اندازی
echo "⏳ انتظار برای راه‌اندازی کامل سرویس‌ها..."
echo "⏳ Waiting for services to fully start..."
sleep 30

# بررسی وضعیت
echo "📊 بررسی وضعیت سرویس‌ها"
echo "📊 Checking services status"
docker-compose -f stackhost.yaml ps

echo ""
echo "✅ راه‌اندازی کامل شد!"
echo "✅ Setup completed!"
echo ""
echo "🌐 آدرس‌های دسترسی:"
echo "🌐 Access URLs:"
echo "  • وب پنل / Web Panel: http://localhost"
echo "  • API: http://localhost/api"
echo "  • Health Check: http://localhost/health"
echo ""
echo "📋 دستورات مفید:"
echo "📋 Useful commands:"
echo "  • مشاهده لاگ‌ها / View logs: docker-compose -f stackhost.yaml logs -f"
echo "  • توقف / Stop: docker-compose -f stackhost.yaml down"
echo "  • ری‌استارت / Restart: docker-compose -f stackhost.yaml restart"
echo "  • وضعیت / Status: docker-compose -f stackhost.yaml ps"
echo ""
echo "📚 مستندات کامل: deployment/README_VPS_DEPLOYMENT.md"
echo "📚 Full documentation: deployment/README_VPS_DEPLOYMENT.md"