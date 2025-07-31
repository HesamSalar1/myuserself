# راهنمای کامل نصب و راه‌اندازی سیستم ربات‌های تلگرام روی VPS

## معرفی سیستم

این پروژه یک سیستم مدیریت چندگانه ربات‌های تلگرام است که قابلیت اجرای همزمان 9 ربات تلگرام را دارد. سیستم شامل:

- **9 ربات تلگرام مستقل** با قابلیت‌های پیشرفته
- **سیستم مدیریت یکپارچه** (Unified Bot Launcher)
- **ربات مانیتورینگ** برای نظارت بر عملکرد
- **ربات گزارش‌دهی** برای اطلاع‌رسانی
- **پنل وب مدیریت** برای کنترل از راه دور
- **سیستم لاگینگ پیشرفته**
- **مدیریت خطاها و راه‌اندازی مجدد خودکار**

## پیش‌نیازها

### سیستم عامل
- Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- Python 3.11+
- Node.js 20+ (برای پنل وب)
- حداقل 2GB RAM
- حداقل 10GB فضای ذخیره‌سازی

### دسترسی‌های لازم
- دسترسی root به VPS
- اتصال اینترنت پایدار
- API ID و API Hash از https://my.telegram.org
- Bot Token از @BotFather (برای ربات‌های گزارش‌دهی)

## روش‌های نصب

### روش 1: نصب خودکار (پیشنهادی)

```bash
# دانلود اسکریپت نصب
wget https://your-domain.com/deployment/install.sh
chmod +x install.sh

# اجرای نصب
sudo ./install.sh
```

### روش 2: نصب دستی

#### مرحله 1: آماده‌سازی سیستم

```bash
# به‌روزرسانی سیستم
sudo apt update && sudo apt upgrade -y

# نصب Python و ابزارهای لازم
sudo apt install -y python3 python3-pip python3-venv git curl wget unzip supervisor nginx

# نصب Node.js (برای پنل وب)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

#### مرحله 2: ایجاد کاربر سیستم

```bash
# ایجاد کاربر مخصوص ربات‌ها
sudo useradd -r -s /bin/bash -m -d /home/telegrambot telegrambot

# ایجاد دایرکتری‌های لازم
sudo mkdir -p /var/log/telegram-bots
sudo chown telegrambot:telegrambot /var/log/telegram-bots
```

#### مرحله 3: کپی فایل‌های پروژه

```bash
# کپی پروژه
sudo mkdir -p /home/telegrambot/telegram-bots
sudo cp -r . /home/telegrambot/telegram-bots/
sudo chown -R telegrambot:telegrambot /home/telegrambot/telegram-bots
```

#### مرحله 4: راه‌اندازی Python Environment

```bash
# تغییر به کاربر ربات
sudo su - telegrambot

# ایجاد محیط مجازی
python3 -m venv telegram-bots/venv

# فعال‌سازی محیط مجازی
source telegram-bots/venv/bin/activate

# نصب وابستگی‌ها
pip install --upgrade pip
pip install -r telegram-bots/requirements.txt
```

#### مرحله 5: پیکربندی

```bash
# کپی فایل پیکربندی
cd telegram-bots
cp .env.example .env

# ویرایش تنظیمات
nano .env
```

**نمونه فایل .env:**
```env
# تنظیمات پایه
BOT_MODE=production
DEBUG=false
LOG_LEVEL=INFO
TOTAL_BOTS=9

# تنظیمات وب پنل
WEB_PORT=5000
WEB_HOST=0.0.0.0
SECRET_KEY=your_super_secret_key_here

# تنظیمات امنیتی
ADMIN_TELEGRAM_ID=your_telegram_id
REPORT_CHAT_ID=report_chat_id

# تنظیمات اختصاصی ربات‌ها (در صورت نیاز)
BOT1_ADMIN_ID=7850529246
BOT2_ADMIN_ID=7419698159
# ... باقی ربات‌ها
```

#### مرحله 6: راه‌اندازی Systemd Services

```bash
# بازگشت به کاربر root
exit

# کپی فایل‌های service
sudo cp deployment/systemd/*.service /etc/systemd/system/

# فعال‌سازی سرویس‌ها
sudo systemctl daemon-reload
sudo systemctl enable telegram-bots.service
sudo systemctl enable telegram-bots-monitor.service
sudo systemctl enable telegram-bots-report.service
```

#### مرحله 7: پیکربندی Nginx

```bash
# کپی پیکربندی nginx
sudo cp deployment/nginx/telegram-bots /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/telegram-bots /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# تست و راه‌اندازی
sudo nginx -t
sudo systemctl reload nginx
```

### روش 3: استفاده از Docker

#### پیش‌نیازها
```bash
# نصب Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# نصب Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-Linux-x86_64" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### راه‌اندازی
```bash
# کپی فایل‌های Docker
cp deployment/docker/docker-compose.yml .
cp deployment/docker/.env.example .env

# ویرایش تنظیمات
nano .env

# شروع سیستم
docker-compose up -d
```

## راه‌اندازی و مدیریت

### شروع سیستم

```bash
# شروع همه سرویس‌ها
sudo systemctl start telegram-bots.service
sudo systemctl start telegram-bots-monitor.service
sudo systemctl start telegram-bots-report.service
sudo systemctl start nginx

# یا استفاده از اسکریپت
./start.sh
```

### بررسی وضعیت

```bash
# بررسی وضعیت سرویس‌ها
sudo systemctl status telegram-bots.service
sudo systemctl status telegram-bots-monitor.service
sudo systemctl status telegram-bots-report.service

# یا استفاده از اسکریپت
./status.sh

# یا استفاده از ابزار مدیریت VPS
sudo python3 deployment/vps_manager.py full-check
```

### مشاهده لاگ‌ها

```bash
# لاگ‌های systemd
sudo journalctl -fu telegram-bots.service
sudo journalctl -fu telegram-bots-monitor.service
sudo journalctl -fu telegram-bots-report.service

# لاگ‌های فایل
tail -f /var/log/telegram-bots/*.log

# یا استفاده از اسکریپت
./logs.sh
```

### ری‌استارت سیستم

```bash
# ری‌استارت همه سرویس‌ها
sudo systemctl restart telegram-bots.service
sudo systemctl restart telegram-bots-monitor.service
sudo systemctl restart telegram-bots-report.service

# یا استفاده از اسکریپت
./restart.sh
```

### توقف سیستم

```bash
# توقف همه سرویس‌ها
sudo systemctl stop telegram-bots.service
sudo systemctl stop telegram-bots-monitor.service
sudo systemctl stop telegram-bots-report.service

# یا استفاده از اسکریپت
./stop.sh
```

## ابزارهای مدیریت پیشرفته

### مدیر VPS

```bash
# بررسی کامل سیستم
sudo python3 deployment/vps_manager.py full-check

# تولید گزارش
sudo python3 deployment/vps_manager.py report

# بک‌آپ سیستم
sudo python3 deployment/vps_manager.py backup

# به‌روزرسانی سیستم
sudo python3 deployment/vps_manager.py update
```

### سیستم مانیتورینگ

```bash
# شروع مانیتورینگ دستی
python3 deployment/monitoring.py --interval 30

# تولید گزارش 24 ساعته
python3 deployment/monitoring.py --report --hours 24

# پاک کردن داده‌های قدیمی
python3 deployment/monitoring.py --cleanup 30
```

### مدیریت پیکربندی

```bash
# اعتبارسنجی پیکربندی
python3 deployment/config.py validate

# صادرات پیکربندی
python3 deployment/config.py export --output config.json

# ایجاد فایل .env جدید
python3 deployment/config.py create-env --output .env.new
```

## مسیرهای مهم

```
/home/telegrambot/telegram-bots/          # دایرکتری اصلی پروژه
├── bots/                                 # ربات‌های تلگرام
│   ├── bot1/                            # ربات شماره 1
│   ├── bot2/                            # ربات شماره 2
│   └── ...                              # باقی ربات‌ها
├── deployment/                          # فایل‌های deployment
├── logs/                                # لاگ‌های محلی
├── .env                                 # تنظیمات محیط
├── unified_bot_launcher.py              # مدیر اصلی ربات‌ها
├── monitoring_bot.py                    # ربات مانیتورینگ
└── report_bot.py                        # ربات گزارش‌دهی

/var/log/telegram-bots/                  # لاگ‌های سیستم
├── main.log                             # لاگ اصلی
├── monitor.log                          # لاگ مانیتورینگ
├── report.log                           # لاگ گزارش‌دهی
└── error.log                            # لاگ خطاها

/etc/systemd/system/                     # سرویس‌های systemd
├── telegram-bots.service               # سرویس اصلی
├── telegram-bots-monitor.service       # سرویس مانیتورینگ
└── telegram-bots-report.service        # سرویس گزارش‌دهی
```

## دسترسی‌ها و آدرس‌ها

- **پنل وب:** http://your-server-ip
- **API Endpoint:** http://your-server-ip/api
- **لاگ‌های مانیتورینگ:** http://your-server-ip/logs
- **وضعیت سیستم:** http://your-server-ip/status

## مانیتورینگ و آلارم‌ها

### متریک‌های نظارت شده
- CPU و RAM سیستم
- وضعیت هر 9 ربات
- ترافیک شبکه
- فضای دیسک
- تعداد ری‌استارت‌ها
- تعداد خطاها

### آلارم‌های خودکار
- CPU بالای 80%
- RAM بالای 85%
- دیسک بالای 90%
- ربات متوقف شده
- خطاهای متوالی
- ری‌استارت‌های زیاد

## بک‌آپ و بازیابی

### بک‌آپ خودکار

```bash
# بک‌آپ دستی
sudo python3 deployment/vps_manager.py backup

# بک‌آپ در مسیر مشخص
sudo python3 deployment/vps_manager.py backup --backup-path /backup/telegram-bots-$(date +%Y%m%d).tar.gz
```

### بازیابی

```bash
# توقف سرویس‌ها
./stop.sh

# بازیابی از بک‌آپ
sudo tar -xzf backup-file.tar.gz -C /

# شروع مجدد
./start.sh
```

### بک‌آپ پایگاه داده

```bash
# بک‌آپ SQLite databases
cp /home/telegrambot/telegram-bots/bots/*/bot*_data.db /backup/
cp /home/telegrambot/telegram-bots/monitoring.db /backup/
```

## امنیت

### Firewall

```bash
# فعال‌سازی UFW
sudo ufw enable

# اجازه دسترسی به پورت‌های ضروری
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 22    # SSH

# محدود کردن دسترسی SSH (اختیاری)
sudo ufw allow from YOUR_IP to any port 22
```

### SSL Certificate

```bash
# نصب Certbot
sudo apt install certbot python3-certbot-nginx

# دریافت گواهی SSL
sudo certbot --nginx -d your-domain.com

# تمدید خودکار
sudo crontab -e
# اضافه کردن خط زیر:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### محدودیت دسترسی

```bash
# محدود کردن دسترسی به دایرکتری‌های حساس
sudo chmod 700 /home/telegrambot/telegram-bots
sudo chmod 600 /home/telegrambot/telegram-bots/.env
```

## عیب‌یابی

### مشکلات رایج

#### 1. ربات‌ها شروع نمی‌شوند

```bash
# بررسی لاگ‌ها
sudo journalctl -u telegram-bots.service -f

# بررسی مجوزها
sudo chown -R telegrambot:telegrambot /home/telegrambot/telegram-bots

# بررسی Python environment
sudo -u telegrambot /home/telegrambot/telegram-bots/venv/bin/python -c "import pyrogram; print('OK')"
```

#### 2. خطای اتصال به اینترنت

```bash
# تست اتصال
ping -c 4 8.8.8.8

# بررسی DNS
nslookup api.telegram.org

# بررسی proxy (در صورت استفاده)
echo $http_proxy
echo $https_proxy
```

#### 3. پورت اشغال شده

```bash
# بررسی پورت‌های اشغال شده
sudo netstat -tlnp | grep :5000
sudo lsof -i :5000

# کشتن پروسه
sudo kill -9 PID
```

#### 4. کمبود فضای دیسک

```bash
# بررسی فضا
df -h

# پاک کردن لاگ‌های قدیمی
sudo find /var/log/telegram-bots -name "*.log" -mtime +30 -delete

# پاک کردن داده‌های قدیمی مانیتورینگ
python3 deployment/monitoring.py --cleanup 30
```

#### 5. خطاهای حافظه

```bash
# بررسی وضعیت حافظه
free -h

# بررسی swap
sudo swapon --show

# افزودن swap (در صورت نیاز)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## به‌روزرسانی

### به‌روزرسانی خودکار

```bash
sudo python3 deployment/vps_manager.py update
```

### به‌روزرسانی دستی

```bash
# توقف سرویس‌ها
./stop.sh

# بک‌آپ
sudo python3 deployment/vps_manager.py backup

# دانلود نسخه جدید
git pull origin main  # یا کپی فایل‌های جدید

# به‌روزرسانی وابستگی‌ها
sudo -u telegrambot /home/telegrambot/telegram-bots/venv/bin/pip install --upgrade -r requirements.txt

# شروع مجدد
./start.sh
```

## پشتیبانی و مستندات

### لاگ‌های مهم

```bash
# لاگ اصلی سیستم
tail -f /var/log/telegram-bots/main.log

# لاگ خطاها
tail -f /var/log/telegram-bots/error.log

# لاگ systemd
sudo journalctl -fu telegram-bots.service
```

### ابزارهای نظارت

```bash
# نظارت بر پروسه‌ها
htop

# نظارت بر شبکه
iftop

# نظارت بر دیسک
iotop
```

### تماس برای پشتیبانی

در صورت بروز مشکل:

1. فایل‌های لاگ را بررسی کنید
2. گزارش مانیتورینگ تولید کنید
3. اطلاعات سیستم را جمع‌آوری کنید
4. با تیم پشتیبانی تماس بگیرید

```bash
# تولید گزارش کامل برای پشتیبانی
sudo python3 deployment/vps_manager.py report > support-report.json
sudo python3 deployment/monitoring.py --report --hours 24 > monitoring-report.json
```

---

**نکته:** این راهنما برای سیستم‌عامل‌های مبتنی بر Debian/Ubuntu نوشته شده است. برای سیستم‌عامل‌های دیگر، ممکن است نیاز به تغییراتی باشد.