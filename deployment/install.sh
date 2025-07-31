#!/bin/bash

# نصب سیستم مدیریت 9 ربات تلگرام روی VPS
# Installation Script for 9 Telegram Bots Management System on VPS

set -e

echo "🚀 شروع نصب سیستم مدیریت ربات‌های تلگرام..."
echo "🚀 Starting Telegram Bots Management System Installation..."

# متغیرهای پیکربندی
BOT_USER="telegrambot"
BOT_HOME="/home/$BOT_USER"
BOT_DIR="$BOT_HOME/telegram-bots"
SERVICE_DIR="/etc/systemd/system"
LOG_DIR="/var/log/telegram-bots"

# بررسی دسترسی root
if [[ $EUID -ne 0 ]]; then
   echo "❌ این اسکریپت باید با دسترسی root اجرا شود"
   echo "❌ This script must be run as root"
   echo "استفاده کنید از: sudo $0"
   echo "Use: sudo $0"
   exit 1
fi

echo "📦 به‌روزرسانی سیستم..."
echo "📦 Updating system packages..."
apt update && apt upgrade -y

echo "🐍 نصب Python و ابزارهای لازم..."
echo "🐍 Installing Python and required tools..."
apt install -y python3 python3-pip python3-venv git curl wget unzip supervisor nginx

echo "👤 ایجاد کاربر سیستم برای ربات‌ها..."
echo "👤 Creating system user for bots..."
if ! id "$BOT_USER" &>/dev/null; then
    useradd -r -s /bin/bash -m -d "$BOT_HOME" "$BOT_USER"
    echo "✅ کاربر $BOT_USER ایجاد شد"
    echo "✅ User $BOT_USER created"
fi

echo "📁 ایجاد دایرکتری‌های لازم..."
echo "📁 Creating necessary directories..."
mkdir -p "$BOT_DIR"
mkdir -p "$LOG_DIR"
chown -R $BOT_USER:$BOT_USER "$BOT_HOME"
chown -R $BOT_USER:$BOG_USER "$LOG_DIR"

echo "📋 کپی فایل‌های پروژه..."
echo "📋 Copying project files..."
# فرض بر این است که فایل‌های پروژه در همان دایرکتری اجرای اسکریپت هستند
cp -r ../bots "$BOT_DIR/"
cp -r ../*.py "$BOT_DIR/"
cp ../requirements.txt "$BOT_DIR/"
cp ../pyproject.toml "$BOT_DIR/" 2>/dev/null || true

echo "🐍 ایجاد محیط مجازی Python..."
echo "🐍 Creating Python virtual environment..."
sudo -u $BOT_USER python3 -m venv "$BOT_DIR/venv"

echo "📦 نصب وابستگی‌های Python..."
echo "📦 Installing Python dependencies..."
sudo -u $BOT_USER "$BOT_DIR/venv/bin/pip" install --upgrade pip
sudo -u $BOT_USER "$BOT_DIR/venv/bin/pip" install -r "$BOT_DIR/requirements.txt"

echo "⚙️ پیکربندی Nginx..."
echo "⚙️ Configuring Nginx..."
cat > /etc/nginx/sites-available/telegram-bots << 'EOF'
server {
    listen 80;
    server_name localhost;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/telegram-bots /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "📝 ایجاد فایل‌های systemd service..."
echo "📝 Creating systemd service files..."

# سرویس اصلی مدیریت ربات‌ها
cat > $SERVICE_DIR/telegram-bots.service << EOF
[Unit]
Description=Telegram Bots Management System
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$BOT_USER
Group=$BOT_USER
WorkingDirectory=$BOT_DIR
Environment=PATH=$BOT_DIR/venv/bin
ExecStart=$BOT_DIR/venv/bin/python unified_bot_launcher.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=telegram-bots

# محدودیت‌های امنیتی
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$BOT_DIR $LOG_DIR /tmp

[Install]
WantedBy=multi-user.target
EOF

# سرویس مانیتورینگ
cat > $SERVICE_DIR/telegram-bots-monitor.service << EOF
[Unit]
Description=Telegram Bots Monitoring System
After=network.target telegram-bots.service
Requires=telegram-bots.service

[Service]
Type=simple
User=$BOT_USER
Group=$BOT_USER
WorkingDirectory=$BOT_DIR
Environment=PATH=$BOT_DIR/venv/bin
ExecStart=$BOT_DIR/venv/bin/python monitoring_bot.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=telegram-bots-monitor

[Install]
WantedBy=multi-user.target
EOF

# سرویس ربات گزارش‌دهی
cat > $SERVICE_DIR/telegram-bots-report.service << EOF
[Unit]
Description=Telegram Bots Report System
After=network.target telegram-bots.service
Requires=telegram-bots.service

[Service]
Type=simple
User=$BOT_USER
Group=$BOT_USER
WorkingDirectory=$BOT_DIR
Environment=PATH=$BOT_DIR/venv/bin
ExecStart=$BOT_DIR/venv/bin/python report_bot.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=telegram-bots-report

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 فعال‌سازی سرویس‌ها..."
echo "🔄 Enabling services..."
systemctl daemon-reload
systemctl enable telegram-bots.service
systemctl enable telegram-bots-monitor.service
systemctl enable telegram-bots-report.service
systemctl enable nginx

echo "📊 ایجاد اسکریپت‌های مدیریت..."
echo "📊 Creating management scripts..."

# اسکریپت شروع
cat > "$BOT_DIR/start.sh" << 'EOF'
#!/bin/bash
echo "🚀 شروع سیستم مدیریت ربات‌های تلگرام..."
sudo systemctl start telegram-bots.service
sudo systemctl start telegram-bots-monitor.service
sudo systemctl start telegram-bots-report.service
sudo systemctl start nginx
echo "✅ همه سرویس‌ها شروع شدند"
EOF

# اسکریپت توقف
cat > "$BOT_DIR/stop.sh" << 'EOF'
#!/bin/bash
echo "⏹️ توقف سیستم مدیریت ربات‌های تلگرام..."
sudo systemctl stop telegram-bots.service
sudo systemctl stop telegram-bots-monitor.service
sudo systemctl stop telegram-bots-report.service
echo "✅ همه سرویس‌ها متوقف شدند"
EOF

# اسکریپت وضعیت
cat > "$BOT_DIR/status.sh" << 'EOF'
#!/bin/bash
echo "📊 وضعیت سیستم مدیریت ربات‌های تلگرام:"
echo "================================================"
echo "🤖 سرویس اصلی:"
sudo systemctl status telegram-bots.service --no-pager -l
echo ""
echo "📊 سرویس مانیتورینگ:"
sudo systemctl status telegram-bots-monitor.service --no-pager -l
echo ""
echo "📋 سرویس گزارش‌دهی:"
sudo systemctl status telegram-bots-report.service --no-pager -l
echo ""
echo "🌐 وضعیت Nginx:"
sudo systemctl status nginx --no-pager -l
EOF

# اسکریپت ری‌استارت
cat > "$BOT_DIR/restart.sh" << 'EOF'
#!/bin/bash
echo "🔄 ری‌استارت سیستم مدیریت ربات‌های تلگرام..."
sudo systemctl restart telegram-bots.service
sudo systemctl restart telegram-bots-monitor.service  
sudo systemctl restart telegram-bots-report.service
sudo systemctl reload nginx
echo "✅ همه سرویس‌ها ری‌استارت شدند"
EOF

# اسکریپت لاگ‌ها
cat > "$BOT_DIR/logs.sh" << 'EOF'
#!/bin/bash
echo "📋 لاگ‌های سیستم:"
echo "=================="
echo "برای خروج از حالت مشاهده لاگ، Ctrl+C بزنید"
echo ""
echo "📊 انتخاب کنید:"
echo "1. لاگ سرویس اصلی"
echo "2. لاگ سرویس مانیتورینگ"
echo "3. لاگ سرویس گزارش‌دهی"
echo "4. همه لاگ‌ها"

read -p "انتخاب شما (1-4): " choice

case $choice in
    1)
        sudo journalctl -fu telegram-bots.service
        ;;
    2)
        sudo journalctl -fu telegram-bots-monitor.service
        ;;
    3)
        sudo journalctl -fu telegram-bots-report.service
        ;;
    4)
        sudo journalctl -fu telegram-bots.service -fu telegram-bots-monitor.service -fu telegram-bots-report.service
        ;;
    *)
        echo "انتخاب نامعتبر"
        ;;
esac
EOF

chmod +x "$BOT_DIR"/*.sh
chown $BOT_USER:$BOT_USER "$BOT_DIR"/*.sh

echo "🔧 ایجاد فایل پیکربندی محیط..."
echo "🔧 Creating environment configuration file..."
cat > "$BOT_DIR/.env.example" << 'EOF'
# تنظیمات پایه
BOT_MODE=production
DEBUG=false
LOG_LEVEL=INFO

# تنظیمات دیتابیس (اختیاری - برای PostgreSQL)
# DATABASE_URL=postgresql://user:password@localhost:5432/telegram_bots
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=telegram_bots
# DB_USER=telegram_user
# DB_PASSWORD=your_secure_password

# تنظیمات وب پنل
WEB_PORT=5000
WEB_HOST=0.0.0.0

# تنظیمات امنیتی
SECRET_KEY=your_super_secret_key_here
SESSION_TIMEOUT=3600

# تنظیمات لاگ
LOG_DIR=/var/log/telegram-bots
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=10

# تنظیمات تعداد ربات‌ها
TOTAL_BOTS=9
RESTART_DELAY=10
MAX_RESTART_ATTEMPTS=5

# آدرس‌های کلیدی
ADMIN_TELEGRAM_ID=your_admin_telegram_id
REPORT_CHAT_ID=your_report_chat_id
EOF

echo "📚 ایجاد مستندات..."
echo "📚 Creating documentation..."
cat > "$BOT_DIR/README_VPS.md" << 'EOF'
# راهنمای نصب و راه‌اندازی سیستم ربات‌های تلگرام روی VPS

## مراحل نصب

### 1. نصب اولیه
```bash
sudo ./install.sh
```

### 2. پیکربندی
1. فایل `.env` را از `.env.example` کپی کنید:
```bash
cp .env.example .env
```

2. تنظیمات را ویرایش کنید:
```bash
nano .env
```

### 3. راه‌اندازی
```bash
./start.sh
```

## دستورات مدیریتی

### شروع سیستم
```bash
./start.sh
```

### توقف سیستم
```bash
./stop.sh
```

### ری‌استارت سیستم
```bash
./restart.sh
```

### بررسی وضعیت
```bash
./status.sh
```

### مشاهده لاگ‌ها
```bash
./logs.sh
```

## مدیریت سرویس‌ها

### سرویس اصلی
```bash
sudo systemctl start telegram-bots.service
sudo systemctl stop telegram-bots.service
sudo systemctl restart telegram-bots.service
sudo systemctl status telegram-bots.service
```

### سرویس مانیتورینگ
```bash
sudo systemctl start telegram-bots-monitor.service
sudo systemctl stop telegram-bots-monitor.service
sudo systemctl restart telegram-bots-monitor.service
```

### سرویس گزارش‌دهی
```bash
sudo systemctl start telegram-bots-report.service
sudo systemctl stop telegram-bots-report.service
sudo systemctl restart telegram-bots-report.service
```

## آدرس‌های دسترسی

- وب پنل: http://your-server-ip
- لاگ‌ها: `/var/log/telegram-bots/`
- فایل‌های پیکربندی: `/home/telegrambot/telegram-bots/`

## مشکلات رایج

### 1. سرویس شروع نمی‌شود
```bash
sudo journalctl -u telegram-bots.service -f
```

### 2. مجوزهای فایل
```bash
sudo chown -R telegrambot:telegrambot /home/telegrambot/telegram-bots/
```

### 3. پورت‌های اشغال شده
```bash
sudo netstat -tlnp | grep :5000
sudo lsof -i :5000
```

## بک‌آپ و بازیابی

### بک‌آپ
```bash
sudo tar -czf telegram-bots-backup-$(date +%Y%m%d).tar.gz /home/telegrambot/telegram-bots/
```

### بازیابی
```bash
sudo tar -xzf telegram-bots-backup-YYYYMMDD.tar.gz -C /
```

## به‌روزرسانی

### 1. توقف سرویس‌ها
```bash
./stop.sh
```

### 2. بک‌آپ
```bash
sudo tar -czf backup-before-update.tar.gz /home/telegrambot/telegram-bots/
```

### 3. کپی فایل‌های جدید
```bash
# کپی فایل‌های به‌روزرسانی شده
```

### 4. شروع مجدد
```bash
./start.sh
```

## امنیت

### 1. Firewall
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 2. SSL (اختیاری)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## مانیتورینگ

### وضعیت سیستم
```bash
htop
df -h
free -h
```

### وضعیت شبکه
```bash
netstat -tlnp
ss -tlnp
```

### وضعیت دیسک
```bash
du -sh /home/telegrambot/telegram-bots/
du -sh /var/log/telegram-bots/
```
EOF

echo "✅ نصب کامل شد!"
echo "✅ Installation completed!"
echo ""
echo "📋 مراحل بعدی:"
echo "📋 Next steps:"
echo "1. فایل .env را پیکربندی کنید"
echo "1. Configure .env file"
echo "2. سیستم را شروع کنید: $BOT_DIR/start.sh"
echo "2. Start the system: $BOT_DIR/start.sh"
echo "3. وضعیت را بررسی کنید: $BOT_DIR/status.sh"
echo "3. Check status: $BOT_DIR/status.sh"
echo ""
echo "🌐 آدرس وب پنل: http://$(hostname -I | awk '{print $1}')"
echo "🌐 Web panel address: http://$(hostname -I | awk '{print $1}')"
echo ""
echo "📚 برای اطلاعات بیشتر: $BOT_DIR/README_VPS.md"
echo "📚 For more information: $BOT_DIR/README_VPS.md"