#!/bin/bash

# اسکریپت شروع Docker containers

set -e

echo "🐳 شروع سیستم مدیریت ربات‌های تلگرام با Docker..."

# بررسی وجود فایل docker-compose
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ فایل docker-compose.yml یافت نشد!"
    exit 1
fi

# بررسی وجود فایل .env
if [ ! -f ".env" ]; then
    echo "⚠️ فایل .env یافت نشد - از .env.example استفاده می‌شود"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ فایل .env از .env.example کپی شد"
        echo "🔧 لطفاً فایل .env را ویرایش کنید و مجدداً اجرا کنید"
        exit 1
    fi
fi

# بیلد images
echo "🔨 بیلد Docker images..."
docker-compose build

# شروع services
echo "🚀 شروع services..."
docker-compose up -d

# بررسی وضعیت
echo "📊 بررسی وضعیت services..."
sleep 10
docker-compose ps

echo ""
echo "✅ سیستم با موفقیت راه‌اندازی شد!"
echo ""
echo "📋 دستورات مفید:"
echo "• مشاهده لاگ‌ها: docker-compose logs -f"
echo "• توقف سیستم: docker-compose down"
echo "• ری‌استارت: docker-compose restart"
echo "• وضعیت services: docker-compose ps"
echo ""
echo "🌐 آدرس وب پنل: http://localhost:5000"
echo ""
echo "📚 برای اطلاعات بیشتر: ./README_DOCKER.md"