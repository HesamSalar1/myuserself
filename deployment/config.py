#!/usr/bin/env python3
"""
مدیریت پیکربندی برای سیستم ربات‌های تلگرام
Configuration Management for Telegram Bots System
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

class BotConfig:
    """کلاس مدیریت پیکربندی ربات‌ها"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.getenv('CONFIG_PATH', '/home/telegrambot/telegram-bots')
        self.env_path = os.path.join(self.config_path, '.env')
        
        # بارگذاری متغیرهای محیط
        if os.path.exists(self.env_path):
            load_dotenv(self.env_path)
            
        self.load_config()
    
    def load_config(self):
        """بارگذاری تنظیمات"""
        
        # تنظیمات پایه سیستم
        self.system_config = {
            'bot_mode': os.getenv('BOT_MODE', 'production'),
            'debug': os.getenv('DEBUG', 'false').lower() == 'true',
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'total_bots': int(os.getenv('TOTAL_BOTS', '9')),
            'restart_delay': int(os.getenv('RESTART_DELAY', '10')),
            'max_restart_attempts': int(os.getenv('MAX_RESTART_ATTEMPTS', '5'))
        }
        
        # تنظیمات وب پنل
        self.web_config = {
            'port': int(os.getenv('WEB_PORT', '5000')),
            'host': os.getenv('WEB_HOST', '0.0.0.0'),
            'secret_key': os.getenv('SECRET_KEY', 'your_super_secret_key_here'),
            'session_timeout': int(os.getenv('SESSION_TIMEOUT', '3600'))
        }
        
        # تنظیمات دیتابیس
        self.database_config = {
            'url': os.getenv('DATABASE_URL', ''),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'name': os.getenv('DB_NAME', 'telegram_bots'),
            'user': os.getenv('DB_USER', 'telegram_user'),
            'password': os.getenv('DB_PASSWORD', ''),
            'use_sqlite': os.getenv('USE_SQLITE', 'true').lower() == 'true'
        }
        
        # تنظیمات لاگ
        self.logging_config = {
            'dir': os.getenv('LOG_DIR', '/var/log/telegram-bots'),
            'max_size': os.getenv('LOG_MAX_SIZE', '100MB'),
            'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '10')),
            'format': os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        }
        
        # تنظیمات امنیتی
        self.security_config = {
            'admin_telegram_id': os.getenv('ADMIN_TELEGRAM_ID', ''),
            'report_chat_id': os.getenv('REPORT_CHAT_ID', ''),
            'allowed_ips': os.getenv('ALLOWED_IPS', '').split(',') if os.getenv('ALLOWED_IPS') else [],
            'rate_limit': int(os.getenv('RATE_LIMIT', '60')),
            'max_requests_per_minute': int(os.getenv('MAX_REQUESTS_PER_MINUTE', '100'))
        }
        
        # تنظیمات پیش‌فرض ربات‌ها - اینها از unified_bot_launcher.py آمده‌اند
        self.default_bot_configs = {
            1: {
                'api_id': 23700094,
                'api_hash': "7cd6b0ba9c5b1a5f21b8b76f1e2b8e40",
                'session_name': "bots/bot1/my_bot1",
                'db_path': "bots/bot1/bot1_data.db",
                'log_path': "bots/bot1/bot1.log",
                'admin_id': 7850529246,
                'auto_reply_enabled': True
            },
            2: {
                'api_id': 29262538,
                'api_hash': "0417ebf26dbd92d3455d51595f2c923c",
                'session_name': "bots/bot2/my_bot2",
                'db_path': "bots/bot2/bot2_data.db",
                'log_path': "bots/bot2/bot2.log",
                'admin_id': 7419698159,
                'auto_reply_enabled': True
            },
            3: {
                'api_id': 21555907,
                'api_hash': "16f4e09d753bc4b182434d8e37f410cd",
                'session_name': "bots/bot3/my_bot3",
                'db_path': "bots/bot3/bot3_data.db",
                'log_path': "bots/bot3/bot3.log",
                'admin_id': 7607882302,
                'auto_reply_enabled': True
            },
            4: {
                'api_id': 15508294,
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot4/my_bot4",
                'db_path': "bots/bot4/bot4_data.db",
                'log_path': "bots/bot4/bot4.log",
                'admin_id': 7739974888,
                'auto_reply_enabled': True
            },
            5: {
                'api_id': 15508294,
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot5/my_bot5",
                'db_path': "bots/bot5/bot5_data.db",
                'log_path': "bots/bot5/bot5.log",
                'admin_id': 7346058093,
                'auto_reply_enabled': True
            },
            6: {
                'api_id': 15508294,
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot6/my_bot6",
                'db_path': "bots/bot6/bot6_data.db",
                'log_path': "bots/bot6/bot6.log",
                'admin_id': 7927398744,
                'auto_reply_enabled': True
            },
            7: {
                'api_id': 15508294,
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot7/my_bot7",
                'db_path': "bots/bot7/bot7_data.db",
                'log_path': "bots/bot7/bot7.log",
                'admin_id': 6992382710,
                'auto_reply_enabled': True
            },
            8: {
                'api_id': 15508294,
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot8/my_bot8", 
                'db_path': "bots/bot8/bot8_data.db",
                'log_path': "bots/bot8/bot8.log",
                'admin_id': 7036853670,
                'auto_reply_enabled': True
            },
            9: {
                'api_id': 15508294,
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot9/my_bot9",
                'db_path': "bots/bot9/bot9_data.db", 
                'log_path': "bots/bot9/bot9.log",
                'admin_id': 7583940804,
                'auto_reply_enabled': True
            }
        }
    
    def get_bot_config(self, bot_id: int) -> Dict[str, Any]:
        """دریافت پیکربندی یک ربات خاص"""
        if bot_id not in self.default_bot_configs:
            raise ValueError(f"Bot {bot_id} not found in configuration")
        
        config = self.default_bot_configs[bot_id].copy()
        
        # اعمال override از environment variables
        env_prefix = f"BOT{bot_id}_"
        
        if os.getenv(f"{env_prefix}API_ID"):
            config['api_id'] = int(os.getenv(f"{env_prefix}API_ID"))
        
        if os.getenv(f"{env_prefix}API_HASH"):
            config['api_hash'] = os.getenv(f"{env_prefix}API_HASH")
            
        if os.getenv(f"{env_prefix}ADMIN_ID"):
            config['admin_id'] = int(os.getenv(f"{env_prefix}ADMIN_ID"))
            
        if os.getenv(f"{env_prefix}AUTO_REPLY"):
            config['auto_reply_enabled'] = os.getenv(f"{env_prefix}AUTO_REPLY").lower() == 'true'
        
        return config
    
    def get_all_bot_configs(self) -> Dict[int, Dict[str, Any]]:
        """دریافت پیکربندی همه ربات‌ها"""
        configs = {}
        for bot_id in range(1, self.system_config['total_bots'] + 1):
            configs[bot_id] = self.get_bot_config(bot_id)
        return configs
    
    def validate_config(self) -> Dict[str, list]:
        """اعتبارسنجی پیکربندی"""
        errors = {
            'system': [],
            'web': [], 
            'database': [],
            'bots': []
        }
        
        # بررسی تنظیمات سیستم
        if self.system_config['total_bots'] < 1 or self.system_config['total_bots'] > 20:
            errors['system'].append("تعداد ربات‌ها باید بین 1 تا 20 باشد")
            
        if self.system_config['restart_delay'] < 5:
            errors['system'].append("تاخیر ری‌استارت باید حداقل 5 ثانیه باشد")
        
        # بررسی تنظیمات وب
        if self.web_config['port'] < 1024 or self.web_config['port'] > 65535:
            errors['web'].append("پورت وب باید بین 1024 تا 65535 باشد")
            
        if len(self.web_config['secret_key']) < 32:
            errors['web'].append("کلید امنیتی باید حداقل 32 کاراکتر باشد")
        
        # بررسی تنظیمات دیتابیس
        if not self.database_config['use_sqlite'] and not self.database_config['url']:
            if not all([self.database_config['host'], self.database_config['name'], 
                       self.database_config['user'], self.database_config['password']]):
                errors['database'].append("اطلاعات اتصال دیتابیس ناقص است")
        
        # بررسی تنظیمات ربات‌ها
        for bot_id in range(1, self.system_config['total_bots'] + 1):
            try:
                config = self.get_bot_config(bot_id)
                if not config['api_id'] or not config['api_hash']:
                    errors['bots'].append(f"API ID یا API Hash برای ربات {bot_id} وجود ندارد")
                if not config['admin_id']:
                    errors['bots'].append(f"Admin ID برای ربات {bot_id} تنظیم نشده")
            except Exception as e:
                errors['bots'].append(f"خطا در پیکربندی ربات {bot_id}: {str(e)}")
        
        return errors
    
    def create_env_file(self, output_path: str = None):
        """ایجاد فایل .env نمونه"""
        if not output_path:
            output_path = os.path.join(self.config_path, '.env')
        
        env_content = f"""# تنظیمات پایه سیستم
BOT_MODE=production
DEBUG=false
LOG_LEVEL=INFO
TOTAL_BOTS=9
RESTART_DELAY=10
MAX_RESTART_ATTEMPTS=5

# تنظیمات وب پنل
WEB_PORT=5000
WEB_HOST=0.0.0.0
SECRET_KEY={os.urandom(32).hex()}
SESSION_TIMEOUT=3600

# تنظیمات دیتابیس
USE_SQLITE=true
DATABASE_URL=
DB_HOST=localhost
DB_PORT=5432
DB_NAME=telegram_bots
DB_USER=telegram_user
DB_PASSWORD=

# تنظیمات لاگ
LOG_DIR=/var/log/telegram-bots
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=10

# تنظیمات امنیتی
ADMIN_TELEGRAM_ID=
REPORT_CHAT_ID=
ALLOWED_IPS=
RATE_LIMIT=60
MAX_REQUESTS_PER_MINUTE=100

# تنظیمات اختصاصی ربات‌ها (اختیاری - برای override کردن تنظیمات پیش‌فرض)
# BOT1_API_ID=
# BOT1_API_HASH=
# BOT1_ADMIN_ID=
# BOT1_AUTO_REPLY=true

# BOT2_API_ID=
# BOT2_API_HASH=
# BOT2_ADMIN_ID=
# BOT2_AUTO_REPLY=true

# ... برای بقیه ربات‌ها
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        return output_path
    
    def export_config_json(self, output_path: str = None) -> str:
        """صادرات پیکربندی به فرمت JSON"""
        if not output_path:
            output_path = os.path.join(self.config_path, 'config.json')
        
        full_config = {
            'system': self.system_config,
            'web': self.web_config,
            'database': self.database_config,
            'logging': self.logging_config,
            'security': self.security_config,
            'bots': self.get_all_bot_configs()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(full_config, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def get_database_url(self) -> str:
        """ساخت URL اتصال دیتابیس"""
        if self.database_config['use_sqlite']:
            return f"sqlite:///telegram_bots.db"
        
        if self.database_config['url']:
            return self.database_config['url']
        
        return (f"postgresql://{self.database_config['user']}:"
                f"{self.database_config['password']}@"
                f"{self.database_config['host']}:"
                f"{self.database_config['port']}/"
                f"{self.database_config['name']}")
    
    def get_paths(self) -> Dict[str, str]:
        """دریافت مسیرهای مهم"""
        return {
            'config_dir': self.config_path,
            'log_dir': self.logging_config['dir'],
            'bot_dir': os.path.join(self.config_path, 'bots'),
            'backup_dir': os.path.join(self.config_path, 'backups'),
            'sessions_dir': os.path.join(self.config_path, 'sessions')
        }

# تابع helper برای استفاده آسان
def get_config() -> BotConfig:
    """دریافت نمونه پیکربندی"""
    return BotConfig()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='مدیریت پیکربندی سیستم ربات‌ها')
    parser.add_argument('action', choices=['validate', 'export', 'create-env'], 
                       help='عملیات مورد نظر')
    parser.add_argument('--output', help='مسیر خروجی')
    
    args = parser.parse_args()
    
    config = BotConfig()
    
    if args.action == 'validate':
        errors = config.validate_config()
        has_errors = any(errors.values())
        
        if has_errors:
            print("❌ خطاهای پیکربندی:")
            for category, error_list in errors.items():
                if error_list:
                    print(f"\n{category.upper()}:")
                    for error in error_list:
                        print(f"  • {error}")
        else:
            print("✅ پیکربندی معتبر است")
    
    elif args.action == 'export':
        output_path = config.export_config_json(args.output)
        print(f"📄 پیکربندی در {output_path} ذخیره شد")
    
    elif args.action == 'create-env':
        output_path = config.create_env_file(args.output)
        print(f"📝 فایل .env در {output_path} ایجاد شد")