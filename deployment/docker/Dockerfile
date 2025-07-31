# Dockerfile برای سیستم مدیریت ربات‌های تلگرام
FROM python:3.11-slim

# تنظیم متغیرهای محیط
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BOT_MODE=production

# تنظیم دایرکتری کاری
WORKDIR /app

# نصب ابزارهای سیستم
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libssl-dev \
    libffi-dev \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# کپی فایل‌های requirements
COPY requirements.txt .
COPY pyproject.toml .

# نصب وابستگی‌های Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# کپی فایل‌های پروژه
COPY . .

# ایجاد دایرکتری‌های لازم
RUN mkdir -p /app/logs /app/data /app/sessions

# پیکربندی supervisor
COPY deployment/docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# تنظیم مجوزها
RUN chmod +x deployment/docker/*.sh

# پورت‌های expose
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# نقطه شروع
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]