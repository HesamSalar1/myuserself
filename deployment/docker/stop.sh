#!/bin/bash

# اسکریپت توقف Docker containers

echo "⏹️ توقف سیستم مدیریت ربات‌های تلگرام..."

# توقف containers
docker-compose down

echo ""
echo "✅ سیستم متوقف شد!"
echo ""
echo "📋 دستورات مفید:"
echo "• شروع مجدد: ./start.sh"
echo "• حذف کامل: docker-compose down -v"
echo "• مشاهده volumes: docker volume ls"