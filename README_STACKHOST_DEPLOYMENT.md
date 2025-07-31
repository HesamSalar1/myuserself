# راهنمای کامل استقرار سیستم 9 ربات تلگرام روی StackHost

## معرفی

این سیستم شامل 9 ربات تلگرام مستقل با قابلیت‌های پیشرفته است که برای استقرار روی پلتفرم StackHost بهینه شده است.

## ویژگی‌های کلیدی

### 🤖 سیستم ربات‌ها
- **9 ربات تلگرام مستقل** با API ID و Hash جداگانه
- **مدیریت یکپارچه** تمام ربات‌ها از یک نقطه کنترل
- **ربات مانیتورینگ** برای نظارت بر عملکرد
- **ربات گزارش‌دهی** برای اطلاع‌رسانی‌های مهم
- **سیستم auto-reply** با قابلیت سفارشی‌سازی
- **مدیریت دوست/دشمن** برای هر ربات
- **سیستم فحش** با پشتیبانی رسانه
- **تشخیص ایموجی ممنوعه** با اقدام خودکار

### 🏗️ معماری سیستم
- **Container-based deployment** با Docker
- **Microservices architecture** برای مقیاس‌پذیری
- **Load balancing** با Nginx
- **Database clustering** با PostgreSQL
- **Caching layer** با Redis
- **Automated backups** با پشتیبانی S3
- **Health monitoring** و alerting
- **SSL/TLS encryption** و امنیت پیشرفته

### 📊 مانیتورینگ و مدیریت
- **Real-time monitoring** تمام سرویس‌ها
- **Performance metrics** و آمارگیری
- **Automated alerts** برای مشکلات
- **Web dashboard** برای مدیریت
- **Log aggregation** و تحلیل
- **Resource management** و بهینه‌سازی

## پیش‌نیازها

### 1. حساب StackHost
- حساب کاربری فعال در StackHost
- دسترسی به پنل مدیریت
- اعتبار کافی برای منابع مورد نیاز

### 2. اطلاعات ربات‌های تلگرام
- **API ID و API Hash** برای هر 9 ربات از [my.telegram.org](https://my.telegram.org)
- **Bot Token** برای ربات‌های مانیتورینگ و گزارش‌دهی از [@BotFather](https://t.me/BotFather)
- **Admin Telegram ID** برای هر ربات

### 3. سرویس‌های اختیاری
- **S3 Bucket** برای بک‌آپ (AWS, DigitalOcean Spaces, etc.)
- **Email/SMTP** برای اطلاع‌رسانی‌ها
- **Webhook URLs** برای آلارم‌ها (Discord, Slack, etc.)

## راه‌اندازی سریع

### مرحله 1: دانلود و آماده‌سازی

```bash
# کلون پروژه
git clone <repository-url>
cd telegram-bots

# اجرای اسکریپت راه‌اندازی سریع
chmod +x deployment/quick-start.sh
./deployment/quick-start.sh
```

### مرحله 2: پیکربندی تنظیمات

```bash
# کپی فایل تنظیمات
cp .env.stackhost.example .env

# ویرایش تنظیمات (ضروری!)
nano .env
```

**تنظیمات حیاتی که باید تغییر دهید:**

```env
# امنیت
SECRET_KEY=your_super_secure_key_minimum_32_characters
DB_PASSWORD=your_database_password
REDIS_PASSWORD=your_redis_password

# مدیریت
ADMIN_TELEGRAM_ID=your_telegram_user_id
REPORT_CHAT_ID=your_report_chat_id

# ربات‌ها (برای هر 9 ربات)
BOT1_API_ID=your_bot1_api_id
BOT1_API_HASH=your_bot1_api_hash
BOT1_ADMIN_ID=your_bot1_admin_telegram_id
# ... ادامه برای BOT2 تا BOT9

# ربات‌های سیستم
MONITORING_BOT_TOKEN=your_monitoring_bot_token
REPORT_BOT_TOKEN=your_report_bot_token
```

### مرحله 3: استقرار روی StackHost

#### روش A: استفاده از StackHost CLI

```bash
# نصب StackHost CLI
npm install -g @stackhost/cli

# ورود به حساب
stackhost login

# استقرار
stackhost deploy --config stackhost.yaml
```

#### روش B: استفاده از پنل وب StackHost

1. وارد پنل StackHost شوید
2. "Create New Application" کلیک کنید
3. فایل `stackhost.yaml` را آپلود کنید
4. فایل `.env` را آپلود کنید
5. "Deploy" کلیک کنید

### مرحله 4: بررسی وضعیت

```bash
# بررسی وضعیت سرویس‌ها
stackhost status

# مشاهده لاگ‌ها
stackhost logs telegram-bots-main

# دسترسی به پنل مدیریت
# https://your-app-name.stackhost.app
```

## پیکربندی پیشرفته

### تنظیمات Auto-Scaling

در فایل `stackhost.yaml`:

```yaml
x-stackhost-config:
  auto_scaling:
    enabled: true
    min_replicas: 1
    max_replicas: 5
    target_cpu_utilization: 70
    target_memory_utilization: 80
```

### تنظیمات SSL/HTTPS

```env
SSL_ENABLED=true
FORCE_HTTPS=true
```

### بک‌آپ خودکار

```env
# S3 Configuration
S3_BACKUP_BUCKET=my-telegram-bots-backup
S3_ACCESS_KEY=your_s3_access_key
S3_SECRET_KEY=your_s3_secret_key

# Backup Schedule (Cron format)
BACKUP_SCHEDULE=0 2 * * *  # روزانه ساعت 2 صبح
BACKUP_RETENTION_DAYS=30
```

### آلارم‌ها و اطلاع‌رسانی

```env
# Webhook (Discord, Slack, etc.)
ALERT_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook

# Email Notifications
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
NOTIFICATION_EMAIL=admin@yourdomain.com
```

## مانیتورینگ و نظارت

### متریک‌های اصلی

1. **System Metrics**
   - CPU Usage
   - Memory Usage
   - Disk Usage
   - Network I/O

2. **Application Metrics**
   - Bot Status (9 bots)
   - Message Processing Rate
   - Error Count
   - Response Time

3. **Database Metrics**
   - Connection Count
   - Query Performance
   - Storage Usage

### Dashboard ها

- **Main Dashboard**: `https://your-app.stackhost.app`
- **Health Check**: `https://your-app.stackhost.app/health`
- **Metrics**: `https://your-app.stackhost.app/metrics`
- **API Documentation**: `https://your-app.stackhost.app/api/docs`

### آلارم‌های خودکار

- CPU > 80% برای 5 دقیقه
- Memory > 85% برای 5 دقیقه
- Disk > 90%
- هر ربات که بیش از 3 بار restart شود
- Database connection errors
- High error rate (>5% در 10 دقیقه)

## مدیریت و نگهداری

### دستورات مفید

```bash
# وضعیت سرویس‌ها
stackhost ps

# ری‌استارت سرویس خاص
stackhost restart telegram-bots-main

# ری‌استارت کل سیستم
stackhost restart

# مشاهده لاگ‌های زنده
stackhost logs -f telegram-bots-main

# اجرای دستور در container
stackhost exec telegram-bots-main bash

# بک‌آپ دستی
stackhost exec telegram-bots-main python deployment/scripts/backup.sh

# به‌روزرسانی
stackhost deploy --config stackhost.yaml
```

### تنظیمات Performance

#### برای ترافیک پایین (کمتر از 1000 پیام در ساعت):
```yaml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
```

#### برای ترافیک متوسط (1000-10000 پیام در ساعت):
```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '1.0'
```

#### برای ترافیک بالا (بیش از 10000 پیام در ساعت):
```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '2.0'
```

## عیب‌یابی مشکلات

### مشکلات رایج

#### 1. ربات‌ها connect نمی‌شوند

```bash
# بررسی لاگ‌ها
stackhost logs telegram-bots-main | grep "ERROR"

# بررسی تنظیمات API
stackhost exec telegram-bots-main env | grep BOT
```

**راه‌حل:**
- API ID/Hash را از my.telegram.org بررسی کنید
- session files را حذف کرده و دوباره login کنید

#### 2. خطای Database Connection

```bash
# بررسی وضعیت PostgreSQL
stackhost logs postgres

# تست اتصال
stackhost exec telegram-bots-main python -c "
import psycopg2
import os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
print('Database OK')
"
```

**راه‌حل:**
- پسورد DATABASE را بررسی کنید
- PostgreSQL service را restart کنید

#### 3. مشکل حافظه یا CPU

```bash
# بررسی استفاده منابع
stackhost metrics

# افزایش منابع در stackhost.yaml
```

#### 4. مشکل SSL/HTTPS

```bash
# بررسی گواهی SSL
stackhost exec nginx nginx -t

# بررسی لاگ‌های nginx
stackhost logs nginx
```

### ابزارهای Debugging

```bash
# وارد شدن به container
stackhost exec telegram-bots-main bash

# بررسی پروسه‌ها
stackhost exec telegram-bots-main ps aux

# بررسی شبکه
stackhost exec telegram-bots-main netstat -tlnp

# تست API endpoints
curl https://your-app.stackhost.app/health
curl https://your-app.stackhost.app/api/status
```

## امنیت و بهترین practices

### امنیت

1. **Environment Variables**: همیشه از متغیرهای محیط برای اطلاعات حساس استفاده کنید
2. **SSL/TLS**: HTTPS را فعال کنید
3. **Firewall**: فقط پورت‌های ضروری را باز کنید
4. **Regular Updates**: به‌روزرسانی‌های امنیتی را اعمال کنید
5. **Backup Security**: بک‌آپ‌ها را رمزگذاری کنید

### Performance

1. **Resource Monitoring**: منابع را مدام نظارت کنید
2. **Database Optimization**: Index ها و query ها را بهینه کنید
3. **Caching**: از Redis برای cache استفاده کنید
4. **Load Balancing**: در ترافیک بالا از Load Balancer استفاده کنید

### Reliability

1. **Health Checks**: Health check های مناسب تنظیم کنید
2. **Auto-restart**: سرویس‌ها را روی auto-restart تنظیم کنید
3. **Monitoring**: آلارم‌های مناسب تنظیم کنید
4. **Backup Strategy**: استراتژی بک‌آپ مناسب داشته باشید

## پشتیبانی و کمک

### منابع مفید

- [مستندات StackHost](https://docs.stackhost.com)
- [مستندات Telegram Bot API](https://core.telegram.org/bots/api)
- [مستندات Pyrogram](https://docs.pyrogram.org)

### گزارش مشکل

در صورت بروز مشکل:

1. **جمع‌آوری اطلاعات:**
```bash
# گزارش وضعیت کامل
stackhost exec telegram-bots-main python deployment/vps_manager.py full-check > system-report.txt

# دانلود لاگ‌ها
stackhost logs --all > all-logs.txt
```

2. **بررسی متریک‌ها:**
```bash
# متریک‌های سیستم
curl https://your-app.stackhost.app/metrics

# وضعیت سلامت
curl https://your-app.stackhost.app/health
```

3. **ارسال گزارش** همراه با فایل‌های جمع‌آوری شده

---

## خلاصه Commands

```bash
# راه‌اندازی اولیه
./deployment/quick-start.sh

# استقرار
stackhost deploy --config stackhost.yaml

# مدیریت
stackhost status
stackhost logs -f telegram-bots-main
stackhost restart telegram-bots-main

# نگهداری
stackhost exec telegram-bots-main python deployment/scripts/backup.sh
stackhost metrics

# عیب‌یابی
stackhost exec telegram-bots-main bash
curl https://your-app.stackhost.app/health
```

این راهنما همه چیزی که برای استقرار موفق سیستم 9 ربات تلگرام روی StackHost نیاز دارید را پوشش می‌دهد. برای سوالات بیشتر، با تیم پشتیبانی تماس بگیرید.