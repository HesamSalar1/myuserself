# راهنمای استقرار روی StackHost

## مراحل استقرار

### 1. آماده‌سازی فایل‌ها

```bash
# کپی فایل تنظیمات
cp .env.stackhost.example .env

# ویرایش تنظیمات
nano .env
```

### 2. تنظیمات ضروری

در فایل `.env` موارد زیر را حتماً تغییر دهید:

- `SECRET_KEY`: کلید امنیتی قوی
- `DB_PASSWORD`: رمز عبور پایگاه داده
- `REDIS_PASSWORD`: رمز عبور Redis
- `ADMIN_TELEGRAM_ID`: شناسه تلگرام مدیر اصلی
- همه `BOT*_API_ID` و `BOT*_API_HASH`: اطلاعات API از my.telegram.org

### 3. استقرار

```bash
# استفاده از StackHost CLI
stackhost deploy --config stackhost.yaml

# یا آپلود فایل‌ها به پنل StackHost
```

### 4. بررسی وضعیت

پس از استقرار:

- بررسی logs: `stackhost logs telegram-bots-main`
- بررسی وضعیت: `stackhost status`
- دسترسی به پنل: `https://your-domain.stackhost.com`

## تنظیمات پیشرفته

### SSL/HTTPS

```env
SSL_ENABLED=true
FORCE_HTTPS=true
```

### بک‌آپ خودکار

```env
S3_BACKUP_BUCKET=my-backups
S3_ACCESS_KEY=xxx
S3_SECRET_KEY=xxx
```

### آلارم‌ها

```env
ALERT_WEBHOOK_URL=https://discord.com/api/webhooks/xxx
NOTIFICATION_EMAIL=admin@domain.com
```

## مشکلات رایج

### 1. خطای اتصال دیتابیس

```bash
# بررسی logs
stackhost logs postgres

# ری‌استارت سرویس
stackhost restart postgres
```

### 2. مشکل حافظه

```yaml
# در stackhost.yaml
deploy:
  resources:
    limits:
      memory: 2G  # افزایش حافظه
```

### 3. خطای مجوزها

```bash
# بررسی volumes
stackhost exec telegram-bots-main ls -la /app/data
```

## مانیتورینگ

- **Metrics**: `/metrics` endpoint
- **Health**: `/health` endpoint  
- **Logs**: StackHost dashboard
- **Alerts**: Telegram/Email notifications

## پشتیبانی

در صورت مشکل:

1. بررسی logs سرویس‌ها
2. تست health check endpoints
3. بررسی تنظیمات .env
4. تماس با پشتیبانی StackHost