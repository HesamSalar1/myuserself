# Dockerfile برای سیستم مدیریت ربات‌های تلگرام
# Dockerfile for Telegram Bots Management System

FROM python:3.11-slim

# تنظیم متغیرهای محیط
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BOT_MODE=production
ENV DEBIAN_FRONTEND=noninteractive

# تنظیم timezone
ENV TZ=Asia/Tehran
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# تنظیم دایرکتری کاری
WORKDIR /app

# نصب ابزارهای سیستم و وابستگی‌ها
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libssl-dev \
    libffi-dev \
    libpq-dev \
    curl \
    wget \
    git \
    supervisor \
    cron \
    logrotate \
    procps \
    && rm -rf /var/lib/apt/lists/*

# ایجاد کاربر غیر privileged
RUN groupadd -r telegrambot && useradd -r -g telegrambot telegrambot

# کپی فایل‌های requirements
COPY requirements.txt .
COPY deployment/requirements.txt deployment-requirements.txt

# نصب وابستگی‌های Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r deployment-requirements.txt

# کپی فایل‌های پروژه
COPY . .

# ایجاد دایرکتری‌های لازم
RUN mkdir -p /app/logs /app/data /app/sessions /app/backups && \
    chmod 755 /app/logs /app/data /app/sessions /app/backups

# کپی فایل‌های پیکربندی
COPY deployment/supervisor/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY deployment/scripts/entrypoint.sh /entrypoint.sh
COPY deployment/scripts/healthcheck.sh /healthcheck.sh

# تنظیم مجوزها
RUN chmod +x /entrypoint.sh /healthcheck.sh && \
    chown -R telegrambot:telegrambot /app

# ایجاد فایل لاگ برای supervisor
RUN touch /var/log/supervisord.log && \
    chown telegrambot:telegrambot /var/log/supervisord.log

# تنظیم cron برای بک‌آپ خودکار
RUN echo "0 2 * * * root /app/deployment/scripts/backup.sh" >> /etc/crontab

# تنظیم logrotate برای مدیریت لاگ‌ها
COPY deployment/logrotate/telegram-bots /etc/logrotate.d/telegram-bots

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /healthcheck.sh

# پورت‌های expose
EXPOSE 5000

# تنظیم volume points
VOLUME ["/app/data", "/app/logs", "/app/sessions", "/app/backups"]

# نقطه شروع
ENTRYPOINT ["/entrypoint.sh"]
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]