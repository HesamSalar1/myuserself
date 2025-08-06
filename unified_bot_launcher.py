import json
import asyncio
import sys
import sqlite3
import logging
import time
from datetime import datetime
import os
from pathlib import Path
from random import choice

sys.stdout.reconfigure(encoding='utf-8')

from pyrogram import Client, filters
from pyrogram.types import Message, ChatMember
from pyrogram.errors import FloodWait, UserNotParticipant, ChatWriteForbidden

# وارد کردن ربات گزارش‌دهی
from report_bot import send_emoji_report, ReportBot

# تنظیم لاگینگ - غیرفعال کردن کامل همه لاگ‌ها
import logging
logging.disable(logging.CRITICAL)  # غیرفعال کردن کامل logging

# غیرفعال کردن لاگ‌های pyrogram
pyrogram_logger = logging.getLogger('pyrogram')
pyrogram_logger.disabled = True
pyrogram_logger.setLevel(logging.CRITICAL)

# غیرفعال کردن تمام لاگرها
for name in logging.Logger.manager.loggerDict:
    logging.getLogger(name).disabled = True
    logging.getLogger(name).setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)
logger.disabled = True

class UnifiedBotLauncher:
    def __init__(self):
        self.bots = {}
        # متغیرهای کنترل
        self.running = False

        # ربات گزارش‌دهی
        self.report_bot = None
        self.count_tasks = {}  # برای ذخیره تسک‌های شمارش
        self.global_paused = {}  # برای توقف کلی {chat_id: user_id} - وقتی ایموجی ممنوعه تشخیص داده شه
        self.continuous_spam_tasks = {}  # برای نگه داشتن تسک‌های فحش مداوم {bot_id: {user_id: task}}

        # تنظیمات تاخیر فحش برای هر بات (ثانیه)
        self.bot_spam_delays = {i: 1.0 for i in range(1, 10)}  # تاخیر پیش‌فرض: 1 ثانیه

        # سیستم پیشرفته ایموجی‌ها و کلمات ممنوعه (کاملا قابل تنظیم از تلگرام)
        self.forbidden_emojis = set()
        self.forbidden_words = set()
        self.security_settings = {
            'emoji_detection_enabled': True,
            'word_detection_enabled': True,
            'case_sensitive_words': False,
            'partial_word_matching': True,
            'log_detections': True,
            'notification_enabled': True,
            'auto_pause_on_detection': True,
            'admin_exemption': False  # ادمین‌ها مستثنی نیستند
        }

        # کش تشخیص برای بهبود کارایی
        self.detection_cache = {}
        self.cache_max_size = 1000
        self.cache_expiry = 300  # 5 دقیقه

        # آمار امنیتی
        self.security_stats = {
            'emoji_detections': 0,
            'word_detections': 0,
            'total_pauses': 0,
            'last_reset': time.time()
        }

        # کامندهای ممنوعه فقط برای دشمنان
        self.enemy_forbidden_commands = ['/catch', '/grab', '/guess', '/arise', '/take', '/secure']

        # سیستم rate limiting مشترک برای جلوگیری از ارسال همزمان
        self.global_rate_limiter = asyncio.Lock()
        self.last_message_time = {}  # {chat_id: timestamp}
        self.min_global_delay = 0.5  # حداقل تاخیر بین پیام‌های همه بات‌ها در یک چت
        self.bot_message_queues = {}  # صف پیام برای هر بات
        
        # سیستم تاخیر پیشرفته
        self.advanced_delay_settings = {
            'enemy_spam_delay': 1.0,  # تاخیر اسپم دشمنان
            'friend_reply_delay': 0.3,  # تاخیر پاسخ به دوستان
            'global_message_delay': 0.5,  # تاخیر کلی پیام‌ها
            'conversation_delay': 2.0,  # تاخیر گفتگوی خودکار
            'emoji_reaction_delay': 0.1,  # تاخیر واکنش به ایموجی ممنوعه
            'burst_protection_delay': 3.0,  # تاخیر محافظت از سیل پیام
            'per_chat_delay_multiplier': 1.0,  # ضریب تاخیر هر چت
            'adaptive_delay_enabled': True,  # تاخیر انطباقی
            'smart_delay_reduction': True,  # کاهش هوشمند تاخیر
        }
        self.chat_specific_delays = {}  # تاخیرات مختص هر چت

        # سیستم محدودیت همزمان برای جلوگیری از spam flooding
        self.concurrent_message_limit = 1  # فقط یک بات در هر لحظه در یک چت
        
        # کش سینک ایموجی‌ها
        self.emoji_sync_cache = {}
        self.last_emoji_sync = 0
        self.active_senders = {}  # {chat_id: set of bot_ids}
        self.chat_locks = {}  # {chat_id: asyncio.Lock}

        # سیستم توقف فوری برای ایموجی‌های ممنوعه (مجزا برای هر چت)
        self.chat_emergency_stops = {}  # {chat_id: asyncio.Event}
        self.last_emoji_detection_time = {}  # {chat_id: timestamp}

        # سیستم هماهنگی تشخیص ایموجی بین همه بات‌ها
        self.emoji_detection_cache = {}  # {message_id: detection_time} - جلوگیری از تشخیص چندگانه
        self.emoji_sync_lock = asyncio.Lock()  # قفل برای همگام‌سازی
        self.detection_cooldown = 0.5  # ثانیه - فاصله بین تشخیص‌های مجدد همان پیام (کاهش یافت)

        # سیستم ساده برای جلوگیری از ارسال چندگانه گزارش
        self.report_sent_cache = {}  # {chat_id_emoji: sent_time} - جلوگیری از گزارش چندگانه
        self.report_cooldown = 30.0  # ثانیه - حداقل فاصله بین گزارش‌های مشابه

        # ادمین اصلی لانچر (کنترل همه بات‌ها)
        self.launcher_admin_id = 5533325167

        # سیستم گفتگوی خودکار بین ربات‌ها
        self.auto_chat_enabled = False  # فعال/غیرفعال بودن حالت گفتگو
        self.auto_chat_tasks = {}  # تسک‌های گفتگوی خودکار برای هر چت
        self.bot_online_status = {i: True for i in range(1, 10)}  # وضعیت آنلاین/آفلاین ربات‌ها
        self.last_bot_activity = {i: time.time() for i in range(1, 10)}  # آخرین فعالیت هر ربات
        self.conversation_topics = []  # موضوعات گفتگو
        self.conversation_messages = []  # پیام‌های گفتگو
        self.active_conversations = {}  # گفتگوهای فعال در هر چت {chat_id: conversation_state}

        # تنظیمات بات‌ها - با استفاده از متغیرهای محیطی برای Stack Host
        self.bot_configs = {
            1: {
                'api_id': 15508294,  # از bots/bot1/main.py
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot1/my_bot1",
                'db_path': "bots/bot1/bot1_data.db",
                'log_path': "bots/bot1/bot1.log",
                'admin_id': 7850529246,
                'auto_reply_enabled': True
            },
            2: {
                'api_id': 29262538,  # از bots/bot2/main.py
                'api_hash': "0417ebf26dbd92d3455d51595f2c923c",
                'session_name': "bots/bot2/my_bot2",
                'db_path': "bots/bot2/bot2_data.db",
                'log_path': "bots/bot2/bot2.log",
                'admin_id': 7419698159,
                'auto_reply_enabled': True
            },
            3: {
                'api_id': 21555907,  # از bots/bot3/main.py
                'api_hash': "16f4e09d753bc4b182434d8e37f410cd",
                'session_name': "bots/bot3/my_bot3",
                'db_path': "bots/bot3/bot3_data.db",
                'log_path': "bots/bot3/bot3.log",
                'admin_id': 7607882302,
                'auto_reply_enabled': True
            },
            4: {
                'api_id': 15508294,  # از bots/bot4/main.py
                'api_hash': "778e5cd56ffcf22c2d62aa963ce85a0c",
                'session_name': "bots/bot4/my_bot4",
                'db_path': "bots/bot4/bot4_data.db",
                'log_path': "bots/bot4/bot4.log",
                'admin_id': 7739974888,
                'auto_reply_enabled': True
            },
            5: {
                'api_id': 25248148,  # از bots/bot5/main.py
                'api_hash': "ec32e167ed322bd870a4e05a7c7cf80b",
                'session_name': "bots/bot5/my_bot5",
                'db_path': "bots/bot5/bot5_data.db",
                'log_path': "bots/bot5/bot5.log",
                'admin_id': 7346058093,
                'auto_reply_enabled': True
            },
            6: {
                'api_id': 24815549,  # از bots/bot6/main.py
                'api_hash': "13d1e8f4d5e90fdd11f7cb9152d78268",
                'session_name': "bots/bot6/my_bot6",
                'db_path': "bots/bot6/bot6_data.db",
                'log_path': "bots/bot6/bot6.log",
                'admin_id': 7927398744,
                'auto_reply_enabled': True
            },
            7: {
                'api_id': 23387507,  # از bots/bot7/main.py
                'api_hash': "d9a605c10c6f56c5d6b559967ff673d2",
                'session_name': "bots/bot7/my_bot7",
                'db_path': "bots/bot7/bot7_data.db",
                'log_path': "bots/bot7/bot7.log",
                'admin_id': 8092847456,
                'auto_reply_enabled': True
            },
            8: {
                'api_id': 23900003,  # از bots/bot8/main.py
                'api_hash': "5f6fb8f1c6d80d264d5eb08af3b038b6",
                'session_name': "bots/bot8/my_bot8",
                'db_path': "bots/bot8/bot8_data.db",
                'log_path': "bots/bot8/bot8.log",
                'admin_id': 7220521953,
                'auto_reply_enabled': True
            },
            9: {
                'api_id': 28221949,  # از bots/bot9/main.py
                'api_hash': "f43819fe07dbf13447b14db41aedf93a",
                'session_name': "bots/bot9/my_bot9",
                'db_path': "bots/bot9/bot9_data.db",
                'log_path': "bots/bot9/bot9.log",
                'admin_id': 7143723023,
                'auto_reply_enabled': True
            }
        }

        # لیست همه admin_id های بات‌ها (بدون ادمین لانچر)
        self.bot_admin_ids = {config['admin_id'] for config in self.bot_configs.values()}

        # لیست کامل همه ادمین‌ها (شامل ادمین لانچر + ادمین‌های بات‌ها)
        self.all_admin_ids = self.bot_admin_ids | {self.launcher_admin_id}

        # تنظیمات خاص Stack Host
        self.is_stackhost_environment = self.detect_stackhost_environment()

        # وضعیت اتصال بات‌ها
        self.bot_connection_status = {i: False for i in range(1, 10)}

        if self.is_stackhost_environment:
            logger.info("🔧 Stack Host environment detected - using optimized settings")

    def detect_stackhost_environment(self):
        """تشخیص محیط Stack Host"""
        stackhost_indicators = [
            os.getenv('STACKHOST_DEPLOYMENT'),
            os.getenv('STACKHOST_ENV'),
            'stackhost' in os.getenv('HOSTNAME', '').lower(),
            'stack' in os.getenv('PLATFORM', '').lower()
        ]
        return any(stackhost_indicators)

    def validate_bot_credentials(self, bot_id):
        """بررسی اعتبار تنظیمات بات"""
        config = self.bot_configs.get(bot_id)
        if not config:
            return False, f"پیکربندی بات {bot_id} یافت نشد"

        api_id = config.get('api_id')
        api_hash = config.get('api_hash')

        if not api_id or not api_hash:
            return False, f"API ID یا API Hash برای بات {bot_id} وجود ندارد"

        if api_hash in ['YOUR_BOT5_API_HASH', 'YOUR_BOT6_API_HASH', 'YOUR_BOT7_API_HASH', 
                       'YOUR_BOT8_API_HASH', 'YOUR_BOT9_API_HASH', 'unique_hash_for_bot5_placeholder',
                       'unique_hash_for_bot6_placeholder', 'unique_hash_for_bot7_placeholder',
                       'unique_hash_for_bot8_placeholder', 'unique_hash_for_bot9_placeholder']:
            return False, f"بات {bot_id} نیاز به API credentials معتبر دارد"

        if str(api_id).startswith('25101'):  # پیش‌فرض‌های جعلی
            return False, f"بات {bot_id} نیاز به API ID واقعی دارد"

        return True, "تنظیمات معتبر است"

    async def test_bot_connection(self, bot_id):
        """تست اتصال بات قبل از شروع کامل"""
        config = self.bot_configs.get(bot_id)
        if not config:
            return False

        try:
            from pyrogram import Client

            # تست سریع اتصال
            test_client = Client(
                f"test_bot_{bot_id}",
                api_id=config['api_id'],
                api_hash=config['api_hash'],
                in_memory=True  # استفاده از session حافظه‌ای برای تست
            )

            await test_client.connect()
            me = await test_client.get_me()
            await test_client.disconnect()

            self.bot_connection_status[bot_id] = True
            logger.info(f"✅ بات {bot_id} اتصال تست شد - @{me.username}")
            return True

        except Exception as e:
            self.bot_connection_status[bot_id] = False
            logger.error(f"❌ تست اتصال بات {bot_id} ناموفق: {e}")
            return False

    def get_stackhost_deployment_status(self):
        """گزارش وضعیت استقرار در Stack Host"""
        status = {
            'environment': 'Stack Host' if self.is_stackhost_environment else 'Local',
            'total_bots': len(self.bot_configs),
            'valid_credentials': 0,
            'invalid_credentials': 0,
            'credential_issues': []
        }

        for bot_id in self.bot_configs:
            is_valid, message = self.validate_bot_credentials(bot_id)
            if is_valid:
                status['valid_credentials'] += 1
            else:
                status['invalid_credentials'] += 1
                status['credential_issues'].append(f"بات {bot_id}: {message}")

        return status



    def setup_database(self, bot_id, db_path):
        """تنظیم پایگاه داده برای هر بات"""
        try:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # ایجاد جداول مورد نیاز
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fosh_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fosh TEXT,
                    media_type TEXT,
                    file_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enemy_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS friend_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS friend_words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT,
                    media_type TEXT,
                    file_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS action_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_type TEXT NOT NULL,
                    user_id INTEGER,
                    details TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # جدول پیشرفته برای ایموجی‌های ممنوعه (مشترک بین همه بات‌ها)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS forbidden_emojis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    emoji TEXT UNIQUE NOT NULL,
                    description TEXT,
                    added_by_user_id INTEGER,
                    added_by_username TEXT,
                    category TEXT DEFAULT 'custom',
                    is_active BOOLEAN DEFAULT 1,
                    severity_level INTEGER DEFAULT 1,
                    auto_pause BOOLEAN DEFAULT 1,
                    notification_enabled BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_triggered DATETIME,
                    trigger_count INTEGER DEFAULT 0,
                    notes TEXT
                )
            ''')

            # جدول جدید برای کلمات ممنوعه
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS forbidden_words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT UNIQUE NOT NULL,
                    description TEXT,
                    added_by_user_id INTEGER,
                    added_by_username TEXT,
                    category TEXT DEFAULT 'custom',
                    is_active BOOLEAN DEFAULT 1,
                    case_sensitive BOOLEAN DEFAULT 0,
                    partial_match BOOLEAN DEFAULT 1,
                    regex_pattern TEXT,
                    severity_level INTEGER DEFAULT 1,
                    auto_pause BOOLEAN DEFAULT 1,
                    notification_enabled BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_triggered DATETIME,
                    trigger_count INTEGER DEFAULT 0,
                    notes TEXT
                )
            ''')

            # جدول تنظیمات سیستم ایموجی و کلمات ممنوعه
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_name TEXT UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    description TEXT,
                    updated_by_user_id INTEGER,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # جدول لاگ امنیتی
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    detection_type TEXT NOT NULL,
                    detected_content TEXT NOT NULL,
                    user_id INTEGER,
                    username TEXT,
                    chat_id INTEGER,
                    chat_title TEXT,
                    bot_id INTEGER,
                    action_taken TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # جدول تنظیمات تاخیر فحش
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS spam_delay_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    delay_seconds REAL NOT NULL DEFAULT 1.0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # جدول پیام‌های گفتگوی خودکار
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    topic TEXT,
                    response_to TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # جدول موضوعات گفتگو
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic_name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # اگر تنظیمات تاخیر وجود ندارد، مقدار پیش‌فرض را وارد کن
            cursor.execute('SELECT COUNT(*) FROM spam_delay_settings')
            if cursor.fetchone()[0] == 0:
                cursor.execute('INSERT INTO spam_delay_settings (delay_seconds) VALUES (1.0)')

            # وارد کردن موضوعات پیش‌فرض گفتگو
            cursor.execute('SELECT COUNT(*) FROM conversation_topics')
            if cursor.fetchone()[0] == 0:
                default_topics = [
                    ('روزمره', 'گفتگوهای عادی روزانه'),
                    ('هواشناسی', 'صحبت درباره آب و هوا'),
                    ('ورزش', 'گفتگو درباره ورزش و بازی‌ها'),
                    ('تکنولوژی', 'صحبت درباره فناوری جدید'),
                    ('خوراک', 'گفتگو درباره غذا و آشپزی'),
                    ('سفر', 'صحبت درباره سفر و گردشگری'),
                    ('موسیقی', 'گفتگو درباره موسیقی و آهنگ‌ها'),
                    ('کتاب', 'صحبت درباره کتاب و مطالعه')
                ]
                cursor.executemany('INSERT INTO conversation_topics (topic_name, description) VALUES (?, ?)', default_topics)

            # وارد کردن پیام‌های پیش‌فرض گفتگو
            cursor.execute('SELECT COUNT(*) FROM conversation_messages')
            if cursor.fetchone()[0] == 0:
                default_messages = [
                    # پیام‌های شروع گفتگو
                    ('starter', 'سلام دوستان, چطورید؟', 'روزمره', None),
                    ('starter', 'امروز چه برنامه‌ای دارید؟', 'روزمره', None),
                    ('starter', 'کسی فیلم خوب دیده؟', 'روزمره', None),
                    ('starter', 'هوا امروز خیلی قشنگه', 'هواشناسی', None),
                    ('starter', 'دیشب چه بازی جالبی بود!', 'ورزش', None),

                    # پاسخ‌های معمولی
                    ('response', 'آره واقعاً', None, 'agreement'),
                    ('response', 'کاملاً موافقم', None, 'agreement'),
                    ('response', 'من که چندان موافق نیستم', None, 'disagreement'),
                    ('response', 'جالب بود این که گفتی', None, 'acknowledgment'),
                    ('response', 'حق با توئه', None, 'agreement'),

                    # سوالات متقابل
                    ('question', 'تو چی فکر می‌کنی؟', None, None),
                    ('question', 'تجربه‌ای داری از این موضوع؟', None, None),
                    ('question', 'کجا شنیدی این رو؟', None, None),
                    ('question', 'واقعاً همینطوره؟', None, None),

                    # پیام‌های روزمره
                    ('casual', 'خب بچه‌ها، برم کارام رو انجام بدم', 'روزمره', None),
                    ('casual', 'فعلاً بای', 'روزمره', None),
                    ('casual', 'حوصله‌م سر رفت', 'روزمره', None),
                    ('casual', 'کسی هست؟', 'روزمره', None),
                    ('casual', 'الآن برمی‌گردم', 'روزمره', None),

                    # پیام‌های هواشناسی
                    ('weather', 'امروز آفتابی خوبی بود', 'هواشناسی', None),
                    ('weather', 'انگار بارون می‌آد', 'هواشناسی', None),
                    ('weather', 'هوا سرد شده', 'هواشناسی', None),

                    # پیام‌های ورزشی
                    ('sports', 'چه بازی خفنی بود', 'ورزش', None),
                    ('sports', 'تیم محبوبتون چیه؟', 'ورزش', None),
                    ('sports', 'فوتبال دیشب دیدید؟', 'ورزش', None)
                ]
                cursor.executemany('INSERT INTO conversation_messages (message_type, content, topic, response_to) VALUES (?, ?, ?, ?)', default_messages)

            conn.commit()
            conn.close()
            pass

        except Exception as e:
            logger.error(f"❌ خطا هنگام تنظیم پایگاه داده: {e}")
            pass

    # توابع مدیریت پایگاه داده
    def add_fosh(self, bot_id, fosh=None, media_type=None, file_id=None):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO fosh_list (fosh, media_type, file_id) VALUES (?, ?, ?)", 
                          (fosh, media_type, file_id))
            conn.commit()
            result = True
        except Exception as e:
            logger.error(f"خطا در add_fosh بات {bot_id}: {e}")
            result = False
        conn.close()
        return result

    def remove_fosh(self, bot_id, fosh):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fosh_list WHERE fosh = ?", (fosh,))
        result = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return result

    def get_fosh_list(self, bot_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT fosh, media_type, file_id FROM fosh_list")
        result = cursor.fetchall()
        conn.close()
        return result

    def clear_fosh_list(self, bot_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fosh_list")
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count

    def add_enemy(self, bot_id, user_id, username=None, first_name=None):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM friend_list WHERE user_id = ?", (user_id,))
            cursor.execute("INSERT INTO enemy_list (user_id, username, first_name) VALUES (?, ?, ?)", 
                          (user_id, username, first_name))
            conn.commit()
            result = True
        except sqlite3.IntegrityError:
            result = False
        except Exception as e:
            logger.error(f"خطا در add_enemy بات {bot_id}: {e}")
            result = False
        conn.close()
        return result

    def remove_enemy(self, bot_id, user_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM enemy_list WHERE user_id = ?", (user_id,))
        result = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return result

    def get_enemy_list(self, bot_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, first_name, created_at FROM enemy_list")
        result = cursor.fetchall()
        conn.close()
        return result

    def clear_enemy_list(self, bot_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM enemy_list")
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count

    def add_friend(self, bot_id, user_id, username=None, first_name=None):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM enemy_list WHERE user_id = ?", (user_id,))
            cursor.execute("INSERT INTO friend_list (user_id, username, first_name) VALUES (?, ?, ?)", 
                          (user_id, username, first_name))
            conn.commit()
            result = True
        except sqlite3.IntegrityError:
            result = False
        except Exception as e:
            logger.error(f"خطا در add_friend بات {bot_id}: {e}")
            result = False
        conn.close()
        return result

    def remove_friend(self, bot_id, user_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM friend_list WHERE user_id = ?", (user_id,))
        result = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return result

    def get_friend_list(self, bot_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, first_name, created_at FROM friend_list")
        result = cursor.fetchall()
        conn.close()
        return result

    def clear_friend_list(self, bot_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM friend_list")
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count

    def add_friend_word(self, bot_id, word=None, media_type=None, file_id=None):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO friend_words (word, media_type, file_id) VALUES (?, ?, ?)", 
                          (word, media_type, file_id))
            conn.commit()
            result = True
        except Exception as e:
            logger.error(f"خطا در اضافه کردن کلمه بات {bot_id}: {e}")
            result = False
        conn.close()
        return result

    def remove_friend_word(self, bot_id, word):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM friend_words WHERE word = ?", (word,))
        result = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return result

    def get_friend_words(self, bot_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT word, media_type, file_id FROM friend_words")
        result = cursor.fetchall()
        conn.close()
        return result

    def clear_friend_words(self, bot_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM friend_words")
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count

    def log_action(self, bot_id, action_type, user_id=None, details=None):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO action_log (action_type, user_id, details) VALUES (?, ?, ?)", 
                      (action_type, user_id, details))
        conn.commit()
        conn.close()

    def get_stats(self, bot_id):
        db_path = self.bot_configs[bot_id]['db_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM fosh_list")
        fosh_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM enemy_list")
        enemy_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM friend_list")
        friend_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM friend_words")
        word_count = cursor.fetchone()[0]

        conn.close()

        return {
            'fosh_count': fosh_count,
            'enemy_count': enemy_count,
            'friend_count': friend_count,
            'word_count': word_count
        }

    # =================================================================
    # سیستم مدیریت پیشرفته ایموجی‌های ممنوعه - Enhanced Forbidden Emoji System
    # =================================================================

    def add_forbidden_emoji_ultra_advanced(self, emoji, description=None, severity_level=1, added_by_user_id=None, added_by_username=None, category='custom', auto_pause=True, notification_enabled=True):
        """🚀 سیستم فوق‌پیشرفته اضافه کردن ایموجی ممنوعه"""
        try:
            db_path = self.bot_configs[1]['db_path']
            self.setup_database(1, db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # نرمال‌سازی پیشرفته ایموجی
            normalized_emoji = self.normalize_emoji(emoji)

            # بررسی وجود قبلی
            cursor.execute("SELECT id, is_active FROM forbidden_emojis WHERE emoji = ?", (emoji,))
            existing = cursor.fetchone()

            if existing:
                # اگر موجود است، بروزرسانی اطلاعات
                cursor.execute("""
                    UPDATE forbidden_emojis 
                    SET is_active = 1, description = ?, severity_level = ?, 
                        auto_pause = ?, notification_enabled = ?, updated_at = CURRENT_TIMESTAMP,
                        added_by_username = ?, notes = ?
                    WHERE emoji = ?
                """, (description, severity_level, auto_pause, notification_enabled, added_by_username, f"Updated by {added_by_username}", emoji))
                result = True
                action = "updated"
            else:
                # اضافه کردن جدید
                cursor.execute("""
                    INSERT INTO forbidden_emojis (emoji, description, added_by_user_id, added_by_username, 
                                                category, severity_level, auto_pause, notification_enabled, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (emoji, description, added_by_user_id, added_by_username, category, severity_level, auto_pause, notification_enabled))
                result = cursor.rowcount > 0
                action = "added"

            if result:
                # به‌روزرسانی کش
                self.forbidden_emojis.add(emoji)

                # لاگ امنیتی پیشرفته
                self.log_security_action(
                    f"emoji_{action}",
                    emoji,
                    added_by_user_id, added_by_username, None, None, None,
                    f"Emoji {action} with severity {severity_level}"
                )

            conn.commit()
            conn.close()
            return result

        except Exception as e:
            logger.error(f"❌ خطا در اضافه کردن ایموجی {emoji}: {e}")
            return False

    def add_forbidden_word_ultra_advanced(self, word, description=None, case_sensitive=False, partial_match=True, severity_level=1, added_by_user_id=None, added_by_username=None, category='custom', auto_pause=True, notification_enabled=True):
        """🚀 سیستم فوق‌پیشرفته اضافه کردن کلمه ممنوعه"""
        try:
            db_path = self.bot_configs[1]['db_path']
            self.setup_database(1, db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # بررسی وجود قبلی
            cursor.execute("SELECT id, is_active FROM forbidden_words WHERE word = ?", (word,))
            existing = cursor.fetchone()

            if existing:
                # اگر موجود است، بروزرسانی اطلاعات
                cursor.execute("""
                    UPDATE forbidden_words 
                    SET is_active = 1, description = ?, case_sensitive = ?, partial_match = ?,
                        severity_level = ?, auto_pause = ?, notification_enabled = ?, 
                        updated_at = CURRENT_TIMESTAMP, added_by_username = ?, 
                        notes = ?
                    WHERE word = ?
                """, (description, case_sensitive, partial_match, severity_level, auto_pause, 
                     notification_enabled, added_by_username, f"Updated by {added_by_username}", word))
                result = True
                action = "updated"
            else:
                # اضافه کردن جدید
                cursor.execute("""
                    INSERT INTO forbidden_words (word, description, case_sensitive, partial_match,
                                               added_by_user_id, added_by_username, category, 
                                               severity_level, auto_pause, notification_enabled, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (word, description, case_sensitive, partial_match, added_by_user_id, 
                     added_by_username, category, severity_level, auto_pause, notification_enabled))
                result = cursor.rowcount > 0
                action = "added"

            if result:
                # به‌روزرسانی کش
                self.forbidden_words.add(word)

                # لاگ امنیتی پیشرفته
                self.log_security_action(
                    f"word_{action}",
                    word,
                    added_by_user_id, added_by_username, None, None, None,
                    f"Word {action} with severity {severity_level}, case_sensitive: {case_sensitive}"
                )

            conn.commit()
            conn.close()
            return result

        except Exception as e:
            logger.error(f"❌ خطا در اضافه کردن کلمه {word}: {e}")
            return False

    def add_forbidden_emoji_advanced(self, emoji, description=None, category='custom', added_by_user_id=None):
        """اضافه کردن ایموجی ممنوعه با ویژگی‌های پیشرفته"""
        try:
            db_path = self.bot_configs[1]['db_path']
            self.setup_database(1, db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # بررسی وجود قبلی
            cursor.execute("SELECT id, is_active FROM forbidden_emojis WHERE emoji = ?", (emoji,))
            existing = cursor.fetchone()

            if existing:
                # اگر موجود است، فعال کردن آن
                cursor.execute("""
                    UPDATE forbidden_emojis 
                    SET is_active = 1, description = ?, category = ?, 
                        added_by_user_id = ?, created_at = CURRENT_TIMESTAMP
                    WHERE emoji = ?
                """, (description, category, added_by_user_id, emoji))
                result = True
                action = "reactivated"
            else:
                # اضافه کردن جدید
                cursor.execute("""
                    INSERT INTO forbidden_emojis (emoji, description, added_by_user_id, category, is_active)
                    VALUES (?, ?, ?, ?, 1)
                """, (emoji, description, added_by_user_id, category))
                result = cursor.rowcount > 0
                action = "added"

            if result:
                # به‌روزرسانی کش
                self.forbidden_emojis.add(emoji)

                # لاگ امنیتی
                self.log_security_action(
                    f"emoji_{action}",
                    f"Emoji: {emoji}",
                    added_by_user_id,
                    action_taken=f"Forbidden emoji {action}"
                )

            conn.commit()
            conn.close()
            return result

        except Exception as e:
            logger.error(f"❌ خطا در اضافه کردن ایموجی ممنوعه: {e}")
            return False

    def remove_forbidden_emoji_advanced(self, emoji, removed_by_user_id=None):
        """حذف ایموجی ممنوعه با لاگینگ پیشرفته"""
        try:
            db_path = self.bot_configs[1]['db_path']
            self.setup_database(1, db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # بررسی وجود
            cursor.execute("SELECT id FROM forbidden_emojis WHERE emoji = ? AND is_active = 1", (emoji,))
            if not cursor.fetchone():
                conn.close()
                return False, "ایموجی در لیست ممنوعه‌ها موجود نیست"

            # غیرفعال کردن (حذف نرم)
            cursor.execute("""
                UPDATE forbidden_emojis 
                SET is_active = 0 
                WHERE emoji = ?
            """, (emoji,))

            result = cursor.rowcount > 0

            if result:
                # حذف از کش
                self.forbidden_emojis.discard(emoji)

                # لاگ امنیتی
                self.log_security_action(
                    "emoji_removed",
                    f"Emoji: {emoji}",
                    removed_by_user_id,
                    action_taken="Forbidden emoji removed"
                )

            conn.commit()
            conn.close()
            return result, "ایموجی با موفقیت حذف شد" if result else "خطا در حذف ایموجی"

        except Exception as e:
            logger.error(f"❌ خطا در حذف ایموجی ممنوعه: {e}")
            return False, f"خطا: {str(e)}"

    def list_forbidden_emojis_advanced(self, category=None, active_only=True):
        """لیست پیشرفته ایموجی‌های ممنوعه"""
        try:
            db_path = self.bot_configs[1]['db_path']
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            query = """
                SELECT emoji, description, category, added_by_user_id, 
                       is_active, created_at 
                FROM forbidden_emojis
            """
            params = []

            conditions = []
            if active_only:
                conditions.append("is_active = 1")
            if category:
                conditions.append("category = ?")
                params.append(category)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY created_at DESC"

            cursor.execute(query, params)
            result = cursor.fetchall()
            conn.close()

            return [
                {
                    'emoji': row[0],
                    'description': row[1],
                    'category': row[2],
                    'added_by': row[3],
                    'is_active': bool(row[4]),
                    'created_at': row[5]
                }
                for row in result
            ]

        except Exception as e:
            logger.error(f"❌ خطا در دریافت لیست ایموجی‌ها: {e}")
            return []

    # =================================================================
    # سیستم مدیریت پیشرفته کلمات ممنوعه - Enhanced Forbidden Words System
    # =================================================================

    def add_forbidden_word_advanced(self, word, description=None, category='custom', 
                                   case_sensitive=False, partial_match=True, added_by_user_id=None):
        """اضافه کردن کلمه ممنوعه با ویژگی‌های پیشرفته"""
        try:
            db_path = self.bot_configs[1]['db_path']
            self.setup_database(1, db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # بررسی وجود قبلی
            cursor.execute("SELECT id, is_active FROM forbidden_words WHERE word = ?", (word,))
            existing = cursor.fetchone()

            if existing:
                # اگر موجود است، به‌روزرسانی
                cursor.execute("""
                    UPDATE forbidden_words 
                    SET is_active = 1, description = ?, category = ?, 
                        case_sensitive = ?, partial_match = ?, added_by_user_id = ?,
                        created_at = CURRENT_TIMESTAMP
                    WHERE word = ?
                """, (description, category, case_sensitive, partial_match, added_by_user_id, word))
                action = "updated"
            else:
                # اضافه کردن جدید
                cursor.execute("""
                    INSERT INTO forbidden_words 
                    (word, description, added_by_user_id, category, is_active, case_sensitive, partial_match)
                    VALUES (?, ?, ?, ?, 1, ?, ?)
                """, (word, description, added_by_user_id, category, case_sensitive, partial_match))
                action = "added"

            result = cursor.rowcount > 0

            if result:
                # به‌روزرسانی کش
                self.forbidden_words.add(word.lower() if not case_sensitive else word)

                # لاگ امنیتی
                self.log_security_action(
                    f"word_{action}",
                    f"Word: {word}",
                    added_by_user_id,
                    action_taken=f"Forbidden word {action}"
                )

            conn.commit()
            conn.close()
            return result

        except Exception as e:
            logger.error(f"❌ خطا در اضافه کردن کلمه ممنوعه: {e}")
            return False

    def remove_forbidden_word_advanced(self, word, removed_by_user_id=None):
        """حذف کلمه ممنوعه با لاگینگ پیشرفته"""
        try:
            db_path = self.bot_configs[1]['db_path']
            self.setup_database(1, db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # بررسی وجود
            cursor.execute("SELECT id FROM forbidden_words WHERE word = ? AND is_active = 1", (word,))
            if not cursor.fetchone():
                conn.close()
                return False, "کلمه در لیست ممنوعه‌ها موجود نیست"

            # غیرفعال کردن
            cursor.execute("UPDATE forbidden_words SET is_active = 0 WHERE word = ?", (word,))
            result = cursor.rowcount > 0

            if result:
                # حذف از کش
                self.forbidden_words.discard(word.lower())
                self.forbidden_words.discard(word)

                # لاگ امنیتی
                self.log_security_action(
                    "word_removed",
                    f"Word: {word}",
                    removed_by_user_id,
                    action_taken="Forbidden word removed"
                )

            conn.commit()
            conn.close()
            return result, "کلمه با موفقیت حذف شد" if result else "خطا در حذف کلمه"

        except Exception as e:
            logger.error(f"❌ خطا در حذف کلمه ممنوعه: {e}")
            return False, f"خطا: {str(e)}"

    def list_forbidden_words_advanced(self, category=None, active_only=True):
        """لیست پیشرفته کلمات ممنوعه"""
        try:
            db_path = self.bot_configs[1]['db_path']
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            query = """
                SELECT word, description, category, added_by_user_id, 
                       is_active, case_sensitive, partial_match, created_at 
                FROM forbidden_words
            """
            params = []

            conditions = []
            if active_only:
                conditions.append("is_active = 1")
            if category:
                conditions.append("category = ?")
                params.append(category)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY created_at DESC"

            cursor.execute(query, params)
            result = cursor.fetchall()
            conn.close()

            return [
                {
                    'word': row[0],
                    'description': row[1],
                    'category': row[2],
                    'added_by': row[3],
                    'is_active': bool(row[4]),
                    'case_sensitive': bool(row[5]),
                    'partial_match': bool(row[6]),
                    'created_at': row[7]
                }
                for row in result
            ]

        except Exception as e:
            logger.error(f"❌ خطا در دریافت لیست کلمات: {e}")
            return []

    def load_forbidden_emojis_from_db(self):
        """بارگذاری ایموجی‌های ممنوعه از دیتابیس - نسخه بهبود یافته"""
        try:
            # تلاش برای مسیرهای مختلف دیتابیس
            possible_paths = [
                self.bot_configs[1]['db_path'],
                "bots/bot1/bot_database.db",
                "bots/bot1/bot1_data.db"
            ]

            emojis = set()

            for db_path in possible_paths:
                if os.path.exists(db_path):
                    try:
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()

                        # بررسی وجود جدول
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='forbidden_emojis'")
                        if cursor.fetchone():
                            # فقط ایموجی‌های فعال
                            cursor.execute("SELECT emoji FROM forbidden_emojis WHERE is_active = 1")
                            result = cursor.fetchall()
                            emojis.update({row[0] for row in result})

                        conn.close()
                        break  # اولین دیتابیس موفق کافی است
                    except Exception as e:
                        continue

            # هیچ ایموجی پیش‌فرضی اضافه نمی‌شود - کاملا قابل تنظیم از تلگرام
            logger.info(f"✅ {len(emojis)} ایموجی ممنوعه بارگذاری شد")
            return emojis

        except Exception as e:
            logger.error(f"❌ خطا در بارگذاری ایموجی‌ها: {e}")
            return set()

    async def sync_forbidden_emojis_across_all_bots(self):
        """سینک فوری ایموجی‌های ممنوعه در همه بات‌ها"""
        try:
            current_time = time.time()
            
            # جلوگیری از سینک مکرر در مدت کوتاه
            if current_time - self.last_emoji_sync < 0.5:
                return
                
            self.last_emoji_sync = current_time
            
            # بارگذاری ایموجی‌های جدید
            new_emojis = self.load_forbidden_emojis_from_db()
            
            # اگر تغییری نکرده، نیازی به سینک نیست
            if new_emojis == self.forbidden_emojis:
                return
                
            # آپدیت فوری کش
            self.forbidden_emojis = new_emojis
            self.emoji_sync_cache = {
                'emojis': new_emojis,
                'sync_time': current_time,
                'count': len(new_emojis)
            }
            
            logger.info(f"⚡ سینک فوری ایموجی‌ها: {len(new_emojis)} ایموجی در همه بات‌ها")
            
        except Exception as e:
            logger.error(f"❌ خطا در سینک ایموجی‌ها: {e}")

    def get_adaptive_delay(self, delay_type, chat_id, user_type="unknown"):
        """محاسبه تاخیر انطباقی بر اساس نوع و شرایط"""
        try:
            base_delay = self.advanced_delay_settings.get(delay_type, 1.0)
            
            # تاخیر مختص چت
            chat_multiplier = self.chat_specific_delays.get(chat_id, {}).get('multiplier', 1.0)
            
            # کاهش تاخیر برای واکنش‌های اضطراری (ایموجی ممنوعه)
            if delay_type == 'emoji_reaction_delay':
                base_delay = 0.05  # واکنش فوری
                
            # تاخیر بر اساس نوع کاربر
            if user_type == "enemy" and delay_type == 'enemy_spam_delay':
                # دشمنان: تاخیر بر اساس تنظیمات
                base_delay = self.advanced_delay_settings.get('enemy_spam_delay', 1.0)
            elif user_type == "friend" and delay_type == 'friend_reply_delay':
                # دوستان: پاسخ سریع‌تر
                base_delay = self.advanced_delay_settings.get('friend_reply_delay', 0.3)
                
            # اعمال ضریب چت
            final_delay = base_delay * chat_multiplier
            
            # حداقل و حداکثر
            final_delay = max(0.01, min(final_delay, 30.0))
            
            return final_delay
            
        except Exception as e:
            logger.error(f"خطا در محاسبه تاخیر انطباقی: {e}")
            return 1.0

    async def smart_delay_with_adaptation(self, delay_type, chat_id, user_type="unknown"):
        """تاخیر هوشمند با انطباق"""
        try:
            # محاسبه تاخیر انطباقی
            delay = self.get_adaptive_delay(delay_type, chat_id, user_type)
            
            # اگر تاخیر انطباقی فعال است
            if self.advanced_delay_settings.get('adaptive_delay_enabled', True):
                # کاهش تاخیر اگر چت خلوت است
                current_time = time.time()
                last_activity = self.last_message_time.get(chat_id, 0)
                
                if current_time - last_activity > 30:  # چت خلوت
                    delay *= 0.7  # کاهش 30%
                elif current_time - last_activity > 60:  # چت خیلی خلوت
                    delay *= 0.5  # کاهش 50%
            
            # کاهش هوشمند تاخیر برای واکنش‌های مهم
            if self.advanced_delay_settings.get('smart_delay_reduction', True):
                if delay_type == 'emoji_reaction_delay':
                    delay = min(delay, 0.1)  # حداکثر 0.1 ثانیه برای ایموجی ممنوعه
                    
            # اعمال تاخیر
            if delay > 0:
                await asyncio.sleep(delay)
                
            # آپدیت زمان آخرین پیام
            self.last_message_time[chat_id] = time.time()
            
            return delay
            
        except Exception as e:
            logger.error(f"خطا در تاخیر هوشمند: {e}")
            await asyncio.sleep(0.5)  # تاخیر پیش‌فرض
            return 0.5

    def load_forbidden_words_from_db(self):
        """بارگذاری کلمات ممنوعه از دیتابیس"""
        try:
            db_path = self.bot_configs[1]['db_path']
            if not os.path.exists(db_path):
                return set()

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # بررسی وجود جدول
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='forbidden_words'")
            if not cursor.fetchone():
                conn.close()
                return set()

            # دریافت کلمات فعال
            cursor.execute("SELECT word, case_sensitive FROM forbidden_words WHERE is_active = 1")
            result = cursor.fetchall()
            conn.close()

            words = set()
            for word, case_sensitive in result:
                if case_sensitive:
                    words.add(word)
                else:
                    words.add(word.lower())

            logger.info(f"✅ {len(words)} کلمه ممنوعه بارگذاری شد")
            return words

        except Exception as e:
            logger.error(f"❌ خطا در بارگذاری کلمات: {e}")
            return set()

    def get_spam_delay(self, bot_id):
        """دریافت تاخیر فحش برای بات مشخص"""
        try:
            db_path = self.bot_configs[bot_id]['db_path']
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT delay_seconds FROM spam_delay_settings ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()

            conn.close()

            if result:
                delay = float(result[0])
                self.bot_spam_delays[bot_id] = delay
                return delay
            else:
                return self.bot_spam_delays.get(bot_id, 1.0)

        except Exception as e:
            logger.error(f"❌ خطا در دریافت تاخیر فحش بات {bot_id}: {e}")
            return self.bot_spam_delays.get(bot_id, 1.0)

    def set_spam_delay(self, bot_id, delay_seconds):
        """تنظیم تاخیر فحش برای بات مشخص"""
        try:
            # تبدیل به float و اعتبارسنجی
            delay = float(delay_seconds)
            if delay < 0:
                return False, "تاخیر نمی‌تواند منفی باشد"

            db_path = self.bot_configs[bot_id]['db_path']
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # به‌روزرسانی یا درج مقدار جدید
            cursor.execute("DELETE FROM spam_delay_settings")  # حذف تنظیمات قبلی
            cursor.execute("INSERT INTO spam_delay_settings (delay_seconds) VALUES (?)", (delay,))

            conn.commit()
            conn.close()

            # به‌روزرسانی کش
            self.bot_spam_delays[bot_id] = delay

            logger.info(f"⏱️ تاخیر فحش بات {bot_id} به {delay} ثانیه تنظیم شد")
            return True, f"تاخیر فحش بات {bot_id} به {delay} ثانیه تنظیم شد"

        except ValueError:
            return False, "مقدار تاخیر باید عدد باشد"
        except Exception as e:
            logger.error(f"❌ خطا در تنظیم تاخیر فحش بات {bot_id}: {e}")
            return False, f"خطا در تنظیم تاخیر: {str(e)}"

    # توابع سیستم گفتگوی خودکار
    def get_conversation_messages(self, message_type=None, topic=None):
        """دریافت پیام‌های گفتگو از دیتابیس"""
        try:
            db_path = self.bot_configs[1]['db_path']
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            if message_type and topic:
                cursor.execute("SELECT content FROM conversation_messages WHERE message_type = ? AND topic = ?", (message_type, topic))
            elif message_type:
                cursor.execute("SELECT content FROM conversation_messages WHERE message_type = ?", (message_type,))
            elif topic:
                cursor.execute("SELECT content FROM conversation_messages WHERE topic = ?", (topic,))
            else:
                cursor.execute("SELECT content FROM conversation_messages")

            result = cursor.fetchall()
            conn.close()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"خطا در دریافت پیام‌های گفتگو: {e}")
            return []

    def get_conversation_topics(self):
        """دریافت موضوعات گفتگو از دیتابیس"""  
        try:
            db_path = self.bot_configs[1]['db_path']
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT topic_name FROM conversation_topics")
            result = cursor.fetchall()
            conn.close()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"خطا در دریافت موضوعات گفتگو: {e}")
            return ['روزمره']

    def select_bot_for_conversation(self, chat_id, exclude_bots=None):
        """انتخاب ربات برای ارسال پیام در گفتگو"""
        if exclude_bots is None:
            exclude_bots = set()

        # فقط ربات‌هایی که آنلاین هستند و کانفیگ دارند
        online_bots = []
        for bot_id in range(1, 10):
            # بررسی آنلاین بودن
            if not self.bot_online_status.get(bot_id, True):
                continue

            # بررسی عدم حضور در لیست مستثنیات
            if bot_id in exclude_bots:
                continue

            # بررسی وجود کانفیگ ربات
            if bot_id not in self.bot_configs:
                continue

            # اگر ربات‌ها در حال اجرا هستند، بررسی وضعیت
            if hasattr(self, 'bots') and self.bots and bot_id in self.bots:
                if self.bots[bot_id]['status'] != 'running':
                    continue

            online_bots.append(bot_id)

        if not online_bots:
            return None

        # انتخاب ربات با کمترین فعالیت اخیر
        selected_bot = min(online_bots, key=lambda x: self.last_bot_activity.get(x, 0))
        return selected_bot

    def simulate_bot_offline(self, bot_id, duration=None):
        """شبیه‌سازی آفلاین شدن ربات"""
        import random
        if duration is None:
            duration = random.randint(30, 180)  # 30 ثانیه تا 3 دقیقه

        self.bot_online_status[bot_id] = False
        logger.info(f"🔴 ربات {bot_id} آفلاین شد برای {duration} ثانیه")

        # تسک برای آنلاین کردن مجدد
        async def bring_back_online():
            await asyncio.sleep(duration)
            self.bot_online_status[bot_id] = True
            logger.info(f"🟢 ربات {bot_id} مجدداً آنلاین شد")

        asyncio.create_task(bring_back_online())

    async def start_auto_conversation(self, chat_id):
        """شروع گفتگوی خودکار در چت"""
        if chat_id in self.auto_chat_tasks:
            return False, "گفتگوی خودکار در این چت فعال است"

        self.active_conversations[chat_id] = {
            'started_at': time.time(),
            'last_message_time': 0,
            'last_bot': None,
            'current_topic': choice(self.get_conversation_topics()),
            'message_count': 0,
            'participants': set()
        }

        task = asyncio.create_task(self.auto_conversation_loop(chat_id))
        self.auto_chat_tasks[chat_id] = task

        logger.info(f"🗣️ گفتگوی خودکار در چت {chat_id} شروع شد")
        return True, "گفتگوی خودکار شروع شد"

    async def stop_auto_conversation(self, chat_id):
        """توقف گفتگوی خودکار در چت"""
        if chat_id in self.auto_chat_tasks:
            self.auto_chat_tasks[chat_id].cancel()
            del self.auto_chat_tasks[chat_id]

        if chat_id in self.active_conversations:
            del self.active_conversations[chat_id]

        logger.info(f"🤐 گفتگوی خودکار در چت {chat_id} متوقف شد")
        return True, "گفتگوی خودکار متوقف شد"

    async def auto_conversation_loop(self, chat_id):
        """حلقه اصلی گفتگوی خودکار"""
        import random

        try:
            conversation = self.active_conversations[chat_id]

            while self.auto_chat_enabled and chat_id in self.active_conversations:
                current_time = time.time()

                # انتظار تصادفی بین پیام‌ها (10 ثانیه تا 2 دقیقه)
                wait_time = random.randint(10, 120)
                await asyncio.sleep(wait_time)

                # انتخاب ربات برای ارسال پیام
                exclude_last = {conversation['last_bot']} if conversation['last_bot'] else set()
                selected_bot = self.select_bot_for_conversation(chat_id, exclude_last)

                if not selected_bot:
                    await asyncio.sleep(30)
                    continue

                # شبیه‌سازی آفلاین شدن تصادفی
                if random.random() < 0.1:  # 10% احتمال آفلاین شدن
                    self.simulate_bot_offline(selected_bot)
                    continue

                # انتخاب نوع پیام و محتوا
                message_content = await self.generate_conversation_message(chat_id, selected_bot)

                if message_content:
                    await self.send_auto_conversation_message(chat_id, selected_bot, message_content)

                    # به‌روزرسانی وضعیت گفتگو
                    conversation['last_message_time'] = current_time
                    conversation['last_bot'] = selected_bot
                    conversation['message_count'] += 1
                    conversation['participants'].add(selected_bot)
                    self.last_bot_activity[selected_bot] = current_time

                    # تغییر موضوع گاهی اوقات
                    if random.random() < 0.15:  # 15% احتمال تغییر موضوع
                        conversation['current_topic'] = choice(self.get_conversation_topics())
                        logger.info(f"📝 موضوع گفتگو در چت {chat_id} تغییر یافت: {conversation['current_topic']}")

        except asyncio.CancelledError:
            logger.info(f"🛑 حلقه گفتگوی خودکار چت {chat_id} متوقف شد")
        except Exception as e:
            logger.error(f"❌ خطا در حلقه گفتگوی خودکار چت {chat_id}: {e}")

    def generate_conversation_message(self, chat_id, bot_id):
        """تولید پیام طبیعی و متنوع برای گفتگوی خودکار با دیکشنری گسترده"""
        import random

        conversation = self.active_conversations.get(chat_id)
        if not conversation:
            return None

        current_topic = conversation['current_topic']
        message_count = conversation['message_count']
        last_bot = conversation.get('last_bot')

        # جلوگیری از تکرار پیام توسط همان ربات
        if last_bot == bot_id and random.random() < 0.7:
            return None

        # دیکشنری گسترده پیام‌های طبیعی بر اساس شخصیت ربات
        personality_messages = {
            1: {  # ربات شوخ و بامزه
                'casual': ['وای چقد خسته‌ام 😂', 'بچه‌ها کجاین؟ لول', 'حوصلم سر رفته والا', 'چیکار کنیم یه چیزی؟'],
                'excited': ['واااای یه چیز باحال پیدا کردم!', 'هههه چقد جالبه این!', 'آخ جووون چه خبرایی شده!'],
                'food': ['شکمم گرسنه‌ست بچه‌ها', 'کی غذا درست کرده؟ میمیرم از گرسنگی', 'پیتزا سفارش بدیم؟ من خرج میدم 😄']
            },
            2: {  # ربات جدی و منطقی  
                'casual': ['سلام دوستان, چطور بود امروز؟', 'نظرتون درباره این موضوع چیه؟', 'فکر کنم باید یه برنامه‌ریزی داشته باشیم'],
                'thoughtful': ['این که جالب بود، قبلاً فکرش رو نکرده بودم', 'درسته، منطقی به نظر میرسه', 'باید بیشتر در موردش فکر کنیم'],
                'tech': ['آپدیت جدید رو نصب کردین؟', 'گوشیتون چطوره؟ مشکلی نداره؟', 'یه مقاله جالب درباره تکنولوژی خوندم']
            },
            3: {  # ربات دوستانه و مهربان
                'warm': ['سلام عزیزم، حالت خوبه؟', 'چقد خوشحالم که همه‌تون اینجاین', 'امیدوارم روز خوبی داشته باشین'],
                'supportive': ['آفرین برات! خیلی خوب بود', 'نگران نباش، حلش میشه', 'اگه کمکی میخوای بگو'],
                'caring': ['خسته نیستین؟', 'مراقب خودتون باشین', 'چیزی لازم ندارین؟']
            },
            4: {  # ربات پرانرژی و فعال
                'energetic': ['بریم یه کاری بکنیم!!!', 'یالا بچه‌ها، کی حاضره؟', 'انرژی دارم امروز، بریم مسافرت!'],
                'sports': ['کی ورزش میکنه؟ بریم فوتبال!', 'بازی دیشب فوق‌العاده بود!', 'استادیوم بریم این هفته؟'],
                'active': ['نشستن کافیه، بلند شین!', 'بریم قدم بزنیم', 'هوا خوبه، بیرون بریم']
            },
            5: {  # ربات آروم و متین
                'calm': ['سلام، روز آرومی بود امروز', 'همه چیز خوب پیش میره', 'یواش یواش داریم پیشرفت میکنیم'],
                'peaceful': ['حال و هوای خوبی داره امروز', 'آروم باشین، عجله‌ای نیست', 'صبر کنین، همه چیز درست میشه'],
                'wise': ['بهتره یه فکری به حالش بکنیم', 'تجربه نشون داده که...', 'صبوری کلید حل مساله‌ست']
            },
            6: {  # ربات کنجکاو و پرسشگر
                'curious': ['این چطور کار میکنه؟', 'جالبه، بیشتر توضیح بدین', 'کجا یاد گرفتین؟', 'چرا اینطوری شده؟'],
                'questioning': ['مطمئنین؟', 'واقعاً همینطوره؟', 'چه دلیلی داره؟', 'کی این کارو کرده؟'],
                'learning': ['چیز جدیدی یاد گرفتم امروز', 'علاقه‌مندم بدونم که...', 'کتاب خوندین اخیراً؟']
            },
            7: {  # ربات خلاق و هنری
                'creative': ['یه ایده باحال دارم!', 'چه رنگی رو دوست دارین؟', 'موسیقی گوش میدین؟'],
                'artistic': ['فیلم خوب دیدین اخیراً؟', 'عکس قشنگی گرفتم امروز', 'نقاشی کردین تا حالا؟'],
                'imaginative': ['فکر کنین اگه...', 'تصور کنین که...', 'رویا دیدم دیشب که...']
            },
            8: {  # ربات عملی و واقع‌بین
                'practical': ['باید یه کار عملی بکنیم', 'این راه حل بهتره', 'بیاین واقع‌بین باشیم'],
                'realistic': ['فکر نمیکنم امکان‌پذیر باشه', 'باید منطقی فکر کنیم', 'هزینه‌ش چقدر میشه؟'],
                'solution': ['راه حلش اینه که...', 'بهترین کار اینه که...', 'من پیشنهاد میدم که...']
            },
            9: {  # ربات اجتماعی و پرحرف
                'social': ['بچه‌ها همه‌تون چطورین؟', 'کی دیگه هست اینجا؟', 'بیاین همه با هم صحبت کنیم'],
                'talkative': ['یه چیز جالب واسه‌تون تعریف کنم', 'راستی یادم اومد که...', 'میدونستین که...'],
                'friendly': ['دوست دارم همه‌تون رو ببینم', 'چه جمع خوبی داریم', 'همیشه خوش میگذره با شما']
            }
        }

        # انتخاب پیام بر اساس شخصیت ربات
        bot_messages = personality_messages.get(bot_id, personality_messages[1])

        # انتخاب دسته پیام بر اساس موضوع و شرایط
        if current_topic == 'تکنولوژی' and 'tech' in bot_messages:
            selected_messages = bot_messages['tech']
        elif current_topic == 'خوراک' and 'food' in bot_messages:
            selected_messages = bot_messages['food']  
        elif current_topic == 'ورزش' and 'sports' in bot_messages:
            selected_messages = bot_messages['sports']
        elif message_count == 0:
            # پیام اول - خوشامدگویی
            selected_messages = bot_messages.get('casual', list(bot_messages.values())[0])
        elif message_count < 5:
            # پیام‌های اولیه - ترکیبی
            available_types = list(bot_messages.keys())
            selected_type = choice(available_types)
            selected_messages = bot_messages[selected_type]
        else:
            # پیام‌های ادامه - تنوع بیشتر
            all_messages = []
            for msg_list in bot_messages.values():
                all_messages.extend(msg_list)
            selected_messages = all_messages

        # پیام‌های اضافی عامیانه و طبیعی
        extra_casual_messages = [
            'چطورین بچه‌ها؟', 'چه خبرا امروز؟', 'کسی هست؟', 'سلاااام',
            'هی چه خبر؟', 'کجا بودین تا حالا؟', 'حالتون خوبه؟', 'چیکار میکنین؟',
            'تعطیله امروز؟', 'آخر هفته چه برنامه‌ای دارین؟', 'خسته‌ام والا',
            'حوصلم سر رفته', 'یه چیزی بگین', 'ساکتین چرا؟', 'بیاین چت کنیم',
            # پیام‌های انگلیسی مخلوط
            'Hello بچه‌ها', 'What\'s up دوستان؟', 'OK چطورین؟', 'Nice روز خوبی بود',
            # پیام‌های هندی مخلوط  
            'Namaste دوستان', 'Kya haal hai؟', 'Sab theek hai؟'
        ]

        # ترکیب پیام‌های شخصیتی با پیام‌های عمومی
        if isinstance(selected_messages, list):
            all_available = selected_messages + extra_casual_messages
        else:
            all_available = extra_casual_messages

        # انتخاب پیام نهایی
        final_message = choice(all_available)

        # اضافه کردن عناصر طبیعی تصادفی
        if random.random() < 0.2:
            # اضافه کردن کلمات تأکیدی
            emphasis_words = ['واقعاً', 'یعنی', 'راستی', 'ببینین', 'والا', 'اصلاً']
            final_message = f"{choice(emphasis_words)} {final_message}"

        if random.random() < 0.15:
            # اضافه کردن ایموجی
            emojis = ['😊', '🤔', '😅', '🙂', '😄', '💬', '👍', '❤️']
            final_message += f" {choice(emojis)}"

        if random.random() < 0.1:
            # تکرار حروف برای تأکید
            if 'خیلی' in final_message:
                final_message = final_message.replace('خیلی', 'خیلیییی')
            elif 'سلام' in final_message and final_message.count('ا') < 4:
                final_message = final_message.replace('سلام', 'سلاااام')

        return final_message

    async def send_auto_conversation_message(self, chat_id, bot_id, message_content):
        """ارسال پیام گفتگوی خودکار"""
        try:
            if bot_id not in self.bots or self.bots[bot_id]['status'] != 'running':
                return False

            client = self.bots[bot_id]['client']

            # ارسال پیام با هماهنگی rate limiting
            if chat_id not in self.chat_locks:
                self.chat_locks[chat_id] = asyncio.Lock()

            async with self.chat_locks[chat_id]:
                # بررسی تاخیر global
                current_time = time.time()
                if chat_id in self.last_message_time:
                    time_since_last = current_time - self.last_message_time[chat_id]
                    if time_since_last < self.min_global_delay:
                        wait_time = self.min_global_delay - time_since_last
                        await asyncio.sleep(wait_time)

                await client.send_message(chat_id, message_content)
                self.last_message_time[chat_id] = time.time()

                logger.info(f"🤖 ربات {bot_id} پیام گفتگو ارسال کرد: {message_content[:50]}...")
                return True

        except Exception as e:
            logger.error(f"❌ خطا در ارسال پیام گفتگوی خودکار بات {bot_id}: {e}")
            return False

    def is_admin(self, user_id):
        """بررسی اینکه آیا کاربر ادمین است یا نه"""
        return user_id in self.all_admin_ids

    def normalize_emoji(self, emoji):
        """🔬 نرمال‌سازی فوق‌پیشرفته ایموجی - Advanced Unicode Processing"""
        import unicodedata
        import re

        if not emoji:
            return ""

        # نرمال‌سازی Unicode (هر دو حالت NFC و NFD)
        normalized_nfc = unicodedata.normalize('NFC', emoji)
        normalized_nfd = unicodedata.normalize('NFD', emoji)

        # حذف کاراکترهای اضافی
        variations_to_remove = [
            '\uFE0F',   # Variation Selector-16
            '\uFE0E',   # Variation Selector-15
            '\u200D',   # Zero Width Joiner
            '\u200C',   # Zero Width Non-Joiner
            '\u2069',   # Pop Directional Isolate
            '\u2066',   # Left-to-Right Isolate
            '\u2067',   # Right-to-Left Isolate
            '\u2068',   # First Strong Isolate
            '\u200E',   # Left-to-Right Mark
            '\u200F',   # Right-to-Left Mark
            '\uFEFF',   # Zero Width No-Break Space
        ]

        cleaned_nfc = normalized_nfc
        cleaned_nfd = normalized_nfd
        for variation in variations_to_remove:
            cleaned_nfc = cleaned_nfc.replace(variation, '')
            cleaned_nfd = cleaned_nfd.replace(variation, '')

        # انتخاب بهترین حالت نرمال‌سازی
        final_cleaned = cleaned_nfc.strip()
        if not final_cleaned:
            final_cleaned = cleaned_nfd.strip()

        return final_cleaned

    # =================================================================
    # سیستم تشخیص پیشرفته - Enhanced Detection System
    # =================================================================

    def log_security_action(self, detection_type, content, user_id=None, username=None, 
                          chat_id=None, chat_title=None, bot_id=None, action_taken=None):
        """لاگ امنیتی برای تمام فعالیت‌های تشخیص"""
        try:
            if not self.security_settings.get('log_detections', True):
                return

            db_path = self.bot_configs[1]['db_path']
            self.setup_database(1, db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO security_log 
                (detection_type, detected_content, user_id, username, chat_id, chat_title, bot_id, action_taken)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (detection_type, content, user_id, username, chat_id, chat_title, bot_id, action_taken))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"❌ خطا در لاگ امنیتی: {e}")

    def contains_forbidden_word(self, text, found_word_ref=None):
        """تشخیص کلمات ممنوعه در متن - with memory fallback"""
        if not text or not self.forbidden_words or not self.security_settings.get('word_detection_enabled', True):
            return False

        # کش تشخیص
        cache_key = f"word_{hash(text)}"
        current_time = time.time()

        if hasattr(self, 'detection_cache') and cache_key in self.detection_cache:
            cache_data = self.detection_cache[cache_key]
            if current_time - cache_data['time'] < getattr(self, 'cache_expiry', 60):
                if found_word_ref is not None and cache_data['found']:
                    found_word_ref.append(cache_data['found'])
                return cache_data['result']

        # متغیرهای تنظیمات
        case_sensitive = self.security_settings.get('case_sensitive_words', False)
        partial_match = self.security_settings.get('partial_word_matching', True)

        # آماده‌سازی متن برای جستجو
        search_text = text if case_sensitive else text.lower()

        words_to_check = []

        try:
            # دریافت کلمات از دیتابیس اگر موجود باشد
            if hasattr(self, 'bot_configs') and self.bot_configs and 1 in self.bot_configs:
                db_path = self.bot_configs[1]['db_path']
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT word, case_sensitive, partial_match 
                    FROM forbidden_words 
                    WHERE is_active = 1
                """)

                words_data = cursor.fetchall()
                conn.close()

                words_to_check.extend(words_data)
        except Exception as e:
            logger.debug(f"Database access failed, using memory fallback: {e}")

        # Fallback: استفاده از کلمات در حافظه اگر دیتابیس در دسترس نباشد
        if not words_to_check and hasattr(self, 'forbidden_words') and self.forbidden_words:
            for word in self.forbidden_words:
                words_to_check.append((word, case_sensitive, partial_match))

        # بررسی کلمات
        for word_data in words_to_check:
            word, word_case_sensitive, word_partial_match = word_data

            # تنظیمات مخصوص کلمه
            check_text = search_text
            check_word = word

            if not word_case_sensitive:
                check_word = word.lower()
                check_text = text.lower()

            # بررسی تطبیق
            found = False
            if word_partial_match:
                # تطبیق جزئی
                found = check_word in check_text
            else:
                # تطبیق کامل کلمه
                import re
                pattern = r'\b' + re.escape(check_word) + r'\b'
                found = bool(re.search(pattern, check_text, re.IGNORECASE if not word_case_sensitive else 0))

            if found:
                # کش کردن نتیجه
                if hasattr(self, 'detection_cache'):
                    self.manage_detection_cache()
                    self.detection_cache[cache_key] = {
                        'result': True,
                        'found': word,
                        'time': current_time
                    }

                if found_word_ref is not None:
                    found_word_ref.append(word)

                # آپدیت آمار
                if hasattr(self, 'security_stats'):
                    self.security_stats['word_detections'] += 1

                return True

        # کش کردن نتیجه منفی
        if hasattr(self, 'detection_cache'):
            self.manage_detection_cache()
            self.detection_cache[cache_key] = {
                'result': False,
                'found': None,
                'time': current_time
            }

        return False

    def contains_stop_emoji(self, text, found_emoji_ref=None):
        """تشخیص ایموجی‌های ممنوعه - نسخه فوق‌پیشرفته"""
        if not text or not self.forbidden_emojis or not self.security_settings.get('emoji_detection_enabled', True):
            return False

        # کش تشخیص
        cache_key = f"emoji_{hash(text)}"
        current_time = time.time()

        if cache_key in self.detection_cache:
            cache_data = self.detection_cache[cache_key]
            if current_time - cache_data['time'] < self.cache_expiry:
                if found_emoji_ref is not None and cache_data['found']:
                    found_emoji_ref.append(cache_data['found'])
                return cache_data['result']

        import unicodedata

        # تبدیل متن به حالات مختلف برای بررسی جامع
        text_variants = [
            text,
            text.replace('\uFE0F', ''),  # بدون variation selector 16
            text.replace('\uFE0E', ''),  # بدون variation selector 15
            text.replace('\u200D', ''),  # بدون zero width joiner
            unicodedata.normalize('NFC', text),
            unicodedata.normalize('NFD', text),
            # حالات ترکیبی
            unicodedata.normalize('NFC', text).replace('\uFE0F', ''),
            unicodedata.normalize('NFD', text).replace('\uFE0F', '')
        ]

        # بررسی همه ایموجی‌های ممنوعه
        for emoji in self.forbidden_emojis:
            if not emoji or len(emoji.strip()) == 0:
                continue

            # تولید حالات مختلف ایموجی
            emoji_variants = [
                emoji,
                emoji.replace('\uFE0F', ''),
                emoji.replace('\uFE0E', ''),
                emoji.replace('\u200D', ''),
                unicodedata.normalize('NFC', emoji),
                unicodedata.normalize('NFD', emoji),
                # حالات ترکیبی
                unicodedata.normalize('NFC', emoji).replace('\uFE0F', ''),
                unicodedata.normalize('NFD', emoji).replace('\uFE0F', ''),
                # نرمال‌سازی پیشرفته
                self.normalize_emoji(emoji)
            ]

            # بررسی تمام ترکیبات
            for text_variant in text_variants:
                for emoji_variant in emoji_variants:
                    if emoji_variant and emoji_variant in text_variant:
                        # کش کردن نتیجه
                        self.manage_detection_cache()
                        self.detection_cache[cache_key] = {
                            'result': True,
                            'found': emoji,
                            'time': current_time
                        }

                        if found_emoji_ref is not None:
                            found_emoji_ref.append(emoji)

                        # آپدیت آمار
                        self.security_stats['emoji_detections'] += 1

                        return True

        # کش کردن نتیجه منفی
        self.manage_detection_cache()
        self.detection_cache[cache_key] = {
            'result': False,
            'found': None,
            'time': current_time
        }

        return False

    def manage_detection_cache(self):
        """مدیریت اندازه کش تشخیص"""
        if len(self.detection_cache) >= self.cache_max_size:
            # حذف قدیمی‌ترین ورودی‌ها
            current_time = time.time()
            expired_keys = [
                key for key, data in self.detection_cache.items()
                if current_time - data['time'] > self.cache_expiry
            ]

            for key in expired_keys:
                del self.detection_cache[key]

            # اگر هنوز پر است، حذف نصف
            if len(self.detection_cache) >= self.cache_max_size:
                keys_to_remove = list(self.detection_cache.keys())[:self.cache_max_size // 2]
                for key in keys_to_remove:
                    del self.detection_cache[key]

    def comprehensive_security_check(self, text, user_id=None, username=None, 
                                   chat_id=None, chat_title=None, bot_id=None):
        """بررسی جامع امنیتی (ایموجی + کلمات)"""
        detected_issues = []

        # بررسی ایموجی‌های ممنوعه
        found_emojis = []
        if self.contains_stop_emoji(text, found_emojis):
            for emoji in found_emojis:
                detected_issues.append({
                    'type': 'forbidden_emoji',
                    'content': emoji,
                    'description': f"ایموجی ممنوعه تشخیص داده شد: {emoji}"
                })

                # لاگ امنیتی
                self.log_security_action(
                    "emoji_detected",
                    emoji,
                    user_id, username, chat_id, chat_title, bot_id,
                    "Security pause triggered"
                )

        # بررسی کلمات ممنوعه
        found_words = []
        if self.contains_forbidden_word(text, found_words):
            for word in found_words:
                detected_issues.append({
                    'type': 'forbidden_word',
                    'content': word,
                    'description': f"کلمه ممنوعه تشخیص داده شد: {word}"
                })

                # لاگ امنیتی
                self.log_security_action(
                    "word_detected",
                    word,
                    user_id, username, chat_id, chat_title, bot_id,
                    "Security pause triggered"
                )

        return detected_issues

    async def should_pause_spam(self, message, bot_id):
        """بررسی جامع امنیتی برای توقف اسپم - ایموجی و کلمات ممنوعه"""

        chat_id = message.chat.id
        message_id = message.id
        current_time = time.time()

        # بررسی cache سریع برای جلوگیری از تشخیص چندگانه
        if hasattr(message, 'id') and message.id:
            cache_key = f"{message_id}_{chat_id}"
            if cache_key in self.emoji_detection_cache:
                cache_time = self.emoji_detection_cache[cache_key]
                if current_time - cache_time < self.detection_cooldown:
                    return False

        detected_issues = []
        user_id = None
        username = None
        chat_title = None

        # جمع‌آوری اطلاعات کاربر و چت
        if message.from_user:
            user_id = message.from_user.id
            username = message.from_user.first_name or message.from_user.username

        if message.chat:
            chat_title = getattr(message.chat, 'title', f'Chat {chat_id}')

        # بررسی جامع متن اصلی پیام
        if message.text:
            detected_issues.extend(
                self.comprehensive_security_check(
                    message.text, user_id, username, chat_id, chat_title, bot_id
                )
            )

        # بررسی جامع کپشن (اگر موجود باشد)
        if message.caption:
            detected_issues.extend(
                self.comprehensive_security_check(
                    message.caption, user_id, username, chat_id, chat_title, bot_id
                )
            )

        # اگر هر گونه مشکل امنیتی تشخیص داده شد
        if detected_issues:
            # ثبت در cache
            cache_key = f"{message_id}_{chat_id}"
            self.emoji_detection_cache[cache_key] = current_time

            # پاک کردن cache قدیمی (نگه داشتن فقط 50 آیتم اخیر)
            if len(self.emoji_detection_cache) > 50:
                # پاک کردن قدیمی‌ترین آیتم‌ها
                old_items = sorted(self.emoji_detection_cache.items(), key=lambda x: x[1])[:10]
                for old_key, _ in old_items:
                    del self.emoji_detection_cache[old_key]

            # فراخوانی توقف اضطراری جامع
            await self.trigger_comprehensive_emergency_stop(
                chat_id, detected_issues, message, bot_id
            )
            return True

        # بررسی کامندهای ممنوعه فقط برای دشمنان
        if message.from_user:
            user_id = message.from_user.id
            enemy_list = self.get_enemy_list(bot_id)
            enemy_ids = {row[0] for row in enemy_list}

            if user_id in enemy_ids:
                message_text = message.text or message.caption or ""
                if message_text:
                    message_lower = message_text.lower().strip()

                    for command in self.enemy_forbidden_commands:
                        # بررسی در ابتدای پیام یا بعد از فاصله
                        if message_lower.startswith(command) or f' {command}' in message_lower:
                            await self.trigger_emergency_stop_for_chat(chat_id, command, message)
                            return True

        return False

    async def trigger_comprehensive_emergency_stop(self, chat_id, detected_issues, message, bot_id):
        """توقف فوری جامع برای تمام انواع تشخیص‌های امنیتی"""
        self.last_emoji_detection_time[chat_id] = time.time()

        # ایجاد event برای چت در صورت عدم وجود
        if chat_id not in self.chat_emergency_stops:
            self.chat_emergency_stops[chat_id] = asyncio.Event()

        self.chat_emergency_stops[chat_id].set()

        # تجمیع اطلاعات تشخیص
        emoji_issues = [issue for issue in detected_issues if issue['type'] == 'forbidden_emoji']
        word_issues = [issue for issue in detected_issues if issue['type'] == 'forbidden_word']

        detected_summary = []
        if emoji_issues:
            emojis = [issue['content'] for issue in emoji_issues]
            detected_summary.append(f"ایموجی‌های ممنوعه: {', '.join(emojis)}")
        if word_issues:
            words = [issue['content'] for issue in word_issues]
            detected_summary.append(f"کلمات ممنوعه: {', '.join(words)}")

        detection_summary = " | ".join(detected_summary)

        logger.warning(f"🛡️ توقف فوری جامع برای چت {chat_id} - {detection_summary}")

        # لغو فقط تسک‌های فحش مربوط به این چت
        cancelled_count = 0
        for spam_key, task in list(self.continuous_spam_tasks.items()):
            key_parts = spam_key.split('_')
            if len(key_parts) >= 3:
                task_chat_id = int(key_parts[2])
                if task_chat_id == chat_id:
                    try:
                        task.cancel()
                        cancelled_count += 1
                        logger.info(f"🛡️ تسک فحش {spam_key} در چت {chat_id} توقف شد")
                        del self.continuous_spam_tasks[spam_key]
                    except:
                        pass

        if cancelled_count > 0:
            logger.warning(f"🛡️ {cancelled_count} تسک فحش در چت {chat_id} متوقف شد")

        # ارسال گزارش جامع
        await self.send_comprehensive_security_report(
            chat_id, cancelled_count, detected_issues, message, bot_id
        )

        # پاک کردن خودکار حالت توقف
        asyncio.create_task(self.auto_clear_emergency_stop_for_chat(chat_id))

    async def send_comprehensive_security_report(self, chat_id, stopped_count, detected_issues, message, bot_id):
        """ارسال گزارش جامع امنیتی"""
        if not self.report_bot:
            return

        try:
            # آماده‌سازی اطلاعات
            user_info = "کاربر نامشخص"
            if message.from_user:
                user_info = f"{message.from_user.first_name or 'بدون نام'} (@{message.from_user.username or 'بدون یوزرنیم'}) - ID: {message.from_user.id}"

            chat_info = f"چت: {chat_id}"
            try:
                if hasattr(message, 'chat') and message.chat:
                    chat_title = message.chat.title or message.chat.first_name or f"چت {chat_id}"
                else:
                    # تلاش برای گرفتن از یکی از بات‌ها
                    for bot_info in self.bots.values():
                        if bot_info.get('client') and bot_info.get('status') == 'running':
                            chat = await bot_info['client'].get_chat(chat_id)
                            chat_title = chat.title or chat.first_name or f"چت {chat_id}"
                            break
            except Exception as e:
                logger.debug(f"نتوانست اطلاعات چت {chat_id} را دریافت کند: {e}")
                chat_title = f"چت {chat_id}"

            # تجمیع مشکلات تشخیص داده شده
            emoji_list = []
            word_list = []
            for issue in detected_issues:
                if issue['type'] == 'forbidden_emoji':
                    emoji_list.append(issue['content'])
                elif issue['type'] == 'forbidden_word':
                    word_list.append(issue['content'])

            # ساخت متن گزارش
            report_text = "🚨 **تشخیص امنیتی جامع - توقف فوری**\n\n"

            if emoji_list:
                report_text += f"🚫 **ایموجی‌های ممنوعه:** {', '.join(emoji_list)}\n"
            if word_list:
                report_text += f"🚫 **کلمات ممنوعه:** {', '.join(word_list)}\n"

            report_text += f"\n👤 **کاربر:** {user_info}\n"
            report_text += f"💬 **{chat_info}**\n"
            report_text += f"🤖 **بات تشخیص‌دهنده:** {bot_id}\n"

            if stopped_count > 0:
                report_text += f"⏹️ **تسک‌های متوقف شده:** {stopped_count} عدد\n"

            report_text += f"⏰ **زمان:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            # اضافه کردن متن پیام اگر موجود باشد
            if message.text:
                preview = message.text[:100] + "..." if len(message.text) > 100 else message.text
                report_text += f"📝 **متن پیام:** `{preview}`"
            elif message.caption:
                preview = message.caption[:100] + "..." if len(message.caption) > 100 else message.caption
                report_text += f"📝 **کپشن:** `{preview}`"

            await self.send_report_safely(report_text)
            logger.info(f"📤 گزارش جامع امنیتی برای چت {chat_id} ارسال شد")

        except Exception as e:
            logger.error(f"❌ خطا در ارسال گزارش جامع: {e}")

    async def trigger_emergency_stop_for_chat(self, chat_id, detected_item, message):
        """فعال‌سازی توقف فوری فقط برای چت مشخص با گزارش یکپارچه"""
        self.last_emoji_detection_time[chat_id] = time.time()

        # ایجاد event برای چت در صورت عدم وجود
        if chat_id not in self.chat_emergency_stops:
            self.chat_emergency_stops[chat_id] = asyncio.Event()

        self.chat_emergency_stops[chat_id].set()
        logger.warning(f"⚡ توقف فوری فقط برای چت {chat_id} - چت‌های دیگر تأثیر نمی‌پذیرند")

        # لغو فقط تسک‌های فحش مربوط به این چت
        cancelled_count = 0
        for spam_key, task in list(self.continuous_spam_tasks.items()):
            # استخراج chat_id از spam_key (format: bot_id_user_id_chat_id)
            key_parts = spam_key.split('_')
            if len(key_parts) >= 3:
                task_chat_id = int(key_parts[2])
                if task_chat_id == chat_id:
                    try:
                        task.cancel()
                        cancelled_count += 1
                        logger.info(f"⚡ تسک فحش {spam_key} در چت {chat_id} فوراً لغو شد")
                        del self.continuous_spam_tasks[spam_key]
                    except:
                        pass

        if cancelled_count > 0:
            logger.warning(f"⚡ {cancelled_count} تسک فحش در چت {chat_id} متوقف شد - چت‌های دیگر عادی ادامه می‌دهند")

        # ارسال گزارش یکپارچه به ربات گزارش‌دهی (فقط یک بار)
        await self.send_emoji_report_to_report_bot(chat_id, cancelled_count, detected_item, message)

        # پاک کردن خودکار حالت توقف برای این چت
        asyncio.create_task(self.auto_clear_emergency_stop_for_chat(chat_id))

    async def send_emoji_report_to_report_bot(self, chat_id, stopped_bots_count, detected_item, message):
        """ارسال گزارش ایموجی ممنوعه به ربات گزارش‌دهی - اصلاح شده"""
        try:
            # چک کردن وجود ربات گزارش‌دهی
            if not self.report_bot:
                logger.warning("⚠️ ربات گزارش‌دهی تعریف نشده")
                return

            if not hasattr(self.report_bot, 'is_valid') or not self.report_bot.is_valid:
                logger.warning("⚠️ ربات گزارش‌دهی نامعتبر - احتمالاً مشکل در توکن")
                return

            if not self.report_bot.client:
                logger.warning("⚠️ کلاینت ربات گزارش‌دهی موجود نیست")
                return

            # کنترل cache برای جلوگیری از spam
            import time
            current_time = time.time()

            # ایجاد کلید یکتا
            cache_key = f"{chat_id}_{str(detected_item).strip()}"

            # بررسی cache (کاهش زمان انتظار به 30 ثانیه)
            cooldown = 30.0

            if cache_key in self.report_sent_cache:
                last_sent = self.report_sent_cache[cache_key]
                if current_time - last_sent < cooldown:
                    logger.debug(f"🔄 گزارش {detected_item} قبلاً ارسال شده")
                    return

            # ثبت زمان جدید
            self.report_sent_cache[cache_key] = current_time

            # پاک کردن cache قدیمی (نگه داشتن فقط 20 آیتم اخیر)
            if len(self.report_sent_cache) > 20:
                old_keys = sorted(self.report_sent_cache.items(), key=lambda x: x[1])[:5]
                for old_key, _ in old_keys:
                    del self.report_sent_cache[old_key]

            # تلاش برای دریافت اطلاعات چت
            chat_title = "نامشخص"
            try:
                if hasattr(message, 'chat') and message.chat:
                    chat_title = message.chat.title or message.chat.first_name or f"چت {chat_id}"
                else:
                    # تلاش برای گرفتن از یکی از بات‌ها
                    for bot_info in self.bots.values():
                        if bot_info.get('client') and bot_info.get('status') == 'running':
                            chat = await bot_info['client'].get_chat(chat_id)
                            chat_title = chat.title or chat.first_name or f"چت {chat_id}"
                            break
            except Exception as e:
                logger.debug(f"نتوانست اطلاعات چت {chat_id} را دریافت کند: {e}")
                chat_title = f"چت {chat_id}"

            # تمیز کردن ایموجی برای نمایش
            display_item = str(detected_item).strip() if detected_item else "نامشخص"

            # شمارش بات‌های فعال
            active_bots = sum(1 for bot_info in self.bots.values() if bot_info.get('status') == 'running')

            # ارسال گزارش به ربات گزارش‌دهی
            if self.report_bot and self.report_bot.client:
                await self.report_bot.send_emoji_alert(
                    chat_id=chat_id,
                    chat_title=chat_title,
                    emoji=display_item,
                    stopped_bots_count=active_bots
                )
                logger.info(f"📤 گزارش ارسال شد: {display_item} در {chat_title} - {active_bots} ربات متأثر شد")

        except Exception as e:
            logger.error(f"❌ خطا در ارسال گزارش به ربات گزارش‌دهی: {e}")

    async def auto_clear_emergency_stop_for_chat(self, chat_id):
        """پاک کردن خودکار حالت توقف اضطراری برای چت مشخص"""
        await asyncio.sleep(0.5)  # انتظار کوتاه تا تسک‌ها متوقف شوند
        if chat_id in self.chat_emergency_stops:
            self.chat_emergency_stops[chat_id].clear()
            logger.info(f"✅ حالت توقف اضطراری چت {chat_id} خودکار پاک شد - آماده دریافت پیام‌های جدید")

    def clear_emergency_stop_for_chat(self, chat_id):
        """پاک کردن دستی حالت توقف اضطراری برای چت مشخص"""
        if chat_id in self.chat_emergency_stops:
            self.chat_emergency_stops[chat_id].clear()
            logger.info(f"✅ حالت توقف اضطراری چت {chat_id} دستی پاک شد")

    def clear_all_emergency_stops(self):
        """پاک کردن همه حالت‌های توقف اضطراری (فقط برای ادمین اصلی)"""
        cleared_count = 0
        for chat_id, event in self.chat_emergency_stops.items():
            event.clear()
            cleared_count += 1
        logger.info(f"✅ {cleared_count} حالت توقف اضطراری پاک شد")

    def is_flooding_message(self, text):
        """تشخیص پیام‌های مربوط به فلودینگ و اسپم"""
        if not text:
            return False

        flooding_keywords = [
            'flooding', 'spamming', 'ignoring your existence', 
            'upcoming', 'minutes', 'ғʟᴏᴏᴅɪɴɢ', 'sᴘᴀᴍᴍɪɴɢ',
            'ɪɢɴᴏʀɪɴɢ', 'ᴇxɪsᴛᴇɴᴄᴇ', 'ᴜᴘᴄᴏᴍɪɴɢ', 'ᴍɪɴᴜᴛᴇs',
            'flood wait', 'too many requests', 'rate limit', 'spam detected'
        ]

        text_lower = text.lower().strip()
        flood_count = sum(1 for keyword in flooding_keywords if keyword.lower() in text_lower)

        # اگر 2 یا بیشتر کلمه کلیدی فلودینگ وجود داشته باشد (حساسیت بیشتر)
        if flood_count >= 2:
            return True

        return False

    def get_bot_for_admin(self, user_id):
        """پیدا کردن شماره بات برای ادمین مشخص"""
        for bot_id, config in self.bot_configs.items():
            if config['admin_id'] == user_id:
                return bot_id
        return None

    def is_launcher_admin(self, user_id):
        """بررسی آیا کاربر ادمین اصلی لانچر است"""
        return user_id == self.launcher_admin_id

    def can_control_bot(self, user_id, target_bot_id):
        """بررسی آیا کاربر مجاز به کنترل بات مشخصی است"""
        # ادمین اصلی لانچر می‌تواند همه بات‌ها را کنترل کند
        if self.is_launcher_admin(user_id):
            return True

        # ادمین‌های بات فقط می‌توانند بات‌هایی که به آن‌ها اختصاص داده شده را کنترل کنند
        accessible_bots = self.get_accessible_bots(user_id)
        return target_bot_id in accessible_bots

    def get_accessible_bots(self, user_id):
        """دریافت لیست بات‌هایی که کاربر مجاز به کنترل آن‌ها است"""
        if self.is_launcher_admin(user_id):
            return list(self.bot_configs.keys())  # همه بات‌ها

        # پیدا کردن همه بات‌هایی که این ادمین کنترل می‌کند
        accessible_bots = []
        for bot_id, config in self.bot_configs.items():
            if config['admin_id'] == user_id:
                accessible_bots.append(bot_id)

        return accessible_bots

    async def create_bot(self, bot_id, config):
        """ایجاد و تنظیم یک بات"""
        try:
            # تنظیم پایگاه داده
            self.setup_database(bot_id, config['db_path'])

            # بارگذاری تنظیمات تاخیر فحش از دیتابیس
            self.get_spam_delay(bot_id)

            # ایجاد کلاینت
            app = Client(
                config['session_name'],
                api_id=config['api_id'],
                api_hash=config['api_hash']
            )

            admin_id= config['admin_id']

            # تعریف هندلرها - کنترل دسترسی بر اساس نوع ادمین
            def is_admin_user(_, __, message):
                if not message.from_user:
                    return False
                user_id = message.from_user.id

                # بررسی آیا کاربر اصلاً ادمین است
                if user_id not in self.all_admin_ids:
                    return False

                # بررسی آیا کاربر مجاز به کنترل این بات است
                can_control = self.can_control_bot(user_id, bot_id)

                if can_control:
                    if self.is_launcher_admin(user_id):
                        logger.info(f"👑 ادمین اصلی لانچر: {user_id} - کنترل بات {bot_id}")
                    else:
                        logger.info(f"🔧 ادمین بات: {user_id} - کنترل بات {bot_id}")
                else:
                    logger.warning(f"🚫 ادمین {user_id} مجاز به کنترل بات {bot_id} نیست")

                return can_control

            admin_filter = filters.create(is_admin_user)

            @app.on_message(filters.command("start") & admin_filter)
            async def start_command(client, message):
                try:
                    user_id = message.from_user.id
                    await message.reply_text(f"🤖 **ربات {bot_id} آماده است!**\n\n📋 برای مشاهده کامندها: `/help`\n🆔 Admin: `{admin_id}`\n👤 شما: `{user_id}`\n✅ تشخیص ادمین موفق")
                except Exception as e:
                    logger.error(f"خطا در start command: {e}")

            @app.on_message(filters.command("testadmin") & admin_filter)
            async def test_admin_command(client, message):
                try:
                    user_id = message.from_user.id
                    user_bot = self.get_bot_for_admin(user_id)
                    is_launcher = self.is_launcher_admin(user_id)
                    accessible_bots = self.get_accessible_bots(user_id)

                    text = f"🔍 **تست تشخیص ادمین:**\n\n"
                    text += f"👤 شما: `{user_id}`\n"

                    if is_launcher:
                        text += f"👑 نوع: ادمین اصلی لانچر\n"
                        text += f"🎯 دسترسی: کنترل همه بات‌ها\n"
                    else:
                        text += f"🔧 نوع: ادمین بات شخصی\n"
                        text += f"🤖 بات مربوطه: `{user_bot or 'یافت نشد'}`\n"

                    text += f"🎮 بات‌های قابل کنترل: `{accessible_bots}`\n"
                    text += f"🎯 بات فعلی: `{bot_id}`\n"
                    text += f"✅ وضعیت: دسترسی تایید شده"

                    await message.reply_text(text)
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامندهای گفتگوی خودکار - فقط برای ادمین اصلی لانچر
            @app.on_message(filters.command("startchat") & admin_filter)
            async def start_auto_chat_command(client, message):
                try:
                    user_id = message.from_user.id
                    if not self.is_launcher_admin(user_id):
                        await message.reply_text("🚫 این کامند فقط برای ادمین اصلی لانچر است")
                        return

                    chat_id = message.chat.id
                    self.auto_chat_enabled = True
                    success, msg = await self.start_auto_conversation(chat_id)

                    if success:
                        await message.reply_text(f"🗣️ **گفتگوی خودکار شروع شد!**\n\n✨ ربات‌ها در این گروه شروع به گفتگوی طبیعی می‌کنند\n🤖 شرکت‌کنندگان: {len([b for b in range(1,10) if self.bot_online_status.get(b, True)])} ربات\n⏰ بازه زمانی: 10 ثانیه تا 2 دقیقه بین پیام‌ها\n🎯 موضوع فعلی: {self.active_conversations[chat_id]['current_topic']}")
                    else:
                        await message.reply_text(f"❌ {msg}")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("stopchat") & admin_filter)
            async def stop_auto_chat_command(client, message):
                try:
                    user_id = message.from_user.id
                    if not self.is_launcher_admin(user_id):
                        await message.reply_text("🚫 این کامند فقط برای ادمین اصلی لانچر است")
                        return

                    chat_id = message.chat.id
                    success, msg = await self.stop_auto_conversation(chat_id)

                    if success:
                        self.auto_chat_enabled = False
                        await message.reply_text("🤐 **گفتگوی خودکار متوقف شد**\n\n✅ ربات‌ها دیگر به صورت خودکار گفتگو نمی‌کنند")
                    else:
                        await message.reply_text(f"❌ {msg}")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("chatstatus") & admin_filter)
            async def chat_status_command(client, message):
                try:
                    user_id = message.from_user.id
                    if not self.is_launcher_admin(user_id):
                        await message.reply_text("🚫 این کامند فقط برای ادمین اصلی لانچر است")
                        return

                    chat_id = message.chat.id

                    text = f"📊 **وضعیت گفتگوی خودکار**\n\n"
                    text += f"🔄 حالت کلی: {'فعال' if self.auto_chat_enabled else 'غیرفعال'}\n"
                    text += f"💬 این چت: {'فعال' if chat_id in self.auto_chat_tasks else 'غیرفعال'}\n\n"

                    # وضعیت ربات‌ها
                    online_count = sum(1 for i in range(1, 10) if self.bot_online_status.get(i, True))
                    offline_count = 9 - online_count
                    text += f"🤖 **ربات‌ها:**\n"
                    text += f"🟢 آنلاین: {online_count} ربات\n"
                    text += f"🔴 آفلاین: {offline_count} ربات\n\n"

                    # جزئیات گفتگوی فعال
                    if chat_id in self.active_conversations:
                        conv = self.active_conversations[chat_id]
                        duration = int(time.time() - conv['started_at'])
                        text += f"📈 **آمار گفتگو:**\n"
                        text += f"⏱️ مدت فعالیت: {duration//60} دقیقه\n"
                        text += f"💬 تعداد پیام: {conv['message_count']}\n"
                        text += f"🎯 موضوع فعلی: {conv['current_topic']}\n"
                        text += f"👥 شرکت‌کنندگان: {len(conv['participants'])} ربات"
                    else:
                        text += "📈 **آمار گفتگو:** هیچ گفتگوی فعالی موجود نیست"

                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("setoffline") & admin_filter)
            async def set_offline_command(client, message):
                try:
                    user_id = message.from_user.id
                    if not self.is_launcher_admin(user_id):
                        await message.reply_text("🚫 این کامند فقط برای ادمین اصلی لانچر است")
                        return

                    if len(message.command) < 2:
                        await message.reply_text("⚠️ لطفاً شماره ربات را وارد کنید.\n💡 استفاده: `/setoffline 1` یا `/setoffline 1-5`")
                        return

                    bot_range = message.command[1]

                    if '-' in bot_range:
                        # محدوده ربات‌ها
                        start, end = map(int, bot_range.split('-'))
                        bots_to_offline = list(range(start, end + 1))
                    else:
                        # ربات منفرد
                        bots_to_offline = [int(bot_range)]

                    offline_count = 0
                    for target_bot in bots_to_offline:
                        if 1 <= target_bot <= 9:
                            self.simulate_bot_offline(target_bot)
                            offline_count += 1

                    await message.reply_text(f"🔴 **{offline_count} ربات آفلاین شد**\n\n📱 ربات‌های آفلاین: {', '.join(map(str, bots_to_offline[:offline_count]))}\n⏰ مدت آفلاین: 30 ثانیه تا 3 دقیقه (تصادفی)")

                except ValueError:
                    await message.reply_text("❌ فرمت نامعتبر. از اعداد 1-9 استفاده کنید")
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامند اضافه کردن فحش (تمام انواع رسانه)
            @app.on_message(filters.command("addfosh") & admin_filter)
            async def add_fosh_command(client, message):
                try:
                    if message.reply_to_message:
                        replied = message.reply_to_message
                        media_type = None
                        file_id = None
                        fosh_text = None

                        if replied.photo:
                            media_type = "photo"
                            file_id = replied.photo.file_id
                        elif replied.video:
                            media_type = "video"
                            file_id = replied.video.file_id
                        elif replied.animation:
                            media_type = "animation"
                            file_id = replied.animation.file_id
                        elif replied.sticker:
                            media_type = "sticker"
                            file_id = replied.sticker.file_id
                        elif replied.audio:
                            media_type = "audio"
                            file_id = replied.audio.file_id
                        elif replied.voice:
                            media_type = "voice"
                            file_id = replied.voice.file_id
                        elif replied.video_note:
                            media_type = "video_note"
                            file_id = replied.video_note.file_id
                        elif replied.document:
                            media_type = "document"
                            file_id = replied.document.file_id
                        elif replied.text:
                            fosh_text = replied.text

                        if media_type or fosh_text:
                            if self.add_fosh(bot_id, fosh_text, media_type, file_id):
                                await message.reply_text(f"✅ فحش جدید اضافه شد ({media_type or 'متن'}) - بات {bot_id}")
                                self.log_action(bot_id, "add_fosh", message.from_user.id, f"{media_type or fosh_text}")
                            else:
                                await message.reply_text("❌ خطا در اضافه کردن فحش")
                        else:
                            await message.reply_text("⚠️ نوع رسانه پشتیبانی نمی‌شود")
                    else:
                        if len(message.command) < 2:
                            await message.reply_text("⚠️ لطفاً یک فحش وارد کنید یا روی پیام ریپلای کنید.\n💡 استفاده: `/addfosh متن فحش`")
                            return

                        fosh = " ".join(message.command[1:])
                        if self.add_fosh(bot_id, fosh):
                            await message.reply_text(f"✅ فحش جدید اضافه شد - بات {bot_id}:\n`{fosh}`")
                            self.log_action(bot_id, "add_fosh", message.from_user.id, fosh[:50])
                        else:
                            await message.reply_text("❌ خطا در اضافه کردن فحش")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("delfosh") & admin_filter)
            async def del_fosh_command(client, message):
                try:
                    if len(message.command) < 2:
                        await message.reply_text("⚠️ لطفاً فحش مورد نظر را وارد کنید.\n💡 استفاده: `/delfosh متن فحش`")
                        return

                    fosh = " ".join(message.command[1:])
                    if self.remove_fosh(bot_id, fosh):
                        await message.reply_text(f"✅ فحش حذف شد - بات {bot_id}:\n`{fosh}`")
                        self.log_action(bot_id, "del_fosh", message.from_user.id, fosh[:50])
                    else:
                        await message.reply_text(f"⚠️ این فحش در لیست یافت نشد:\n`{fosh}`")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("listfosh") & admin_filter)
            async def list_fosh_command(client, message):
                try:
                    fosh_list = self.get_fosh_list(bot_id)
                    if not fosh_list:
                        await message.reply_text(f"📝 لیست فحش‌های بات {bot_id} خالی است.\n💡 با `/addfosh` فحش اضافه کنید.")
                        return

                    text = f"🔥 **لیست فحش‌های بات {bot_id}:**\n\n"
                    for i, (fosh, media_type, file_id) in enumerate(fosh_list, 1):
                        if media_type:
                            text += f"`{i}.` [{media_type.upper()}]\n"
                        else:
                            text += f"`{i}.` {fosh}\n"

                        if i >= 20:
                            text += f"\n... و {len(fosh_list) - 20} مورد دیگر"
                            break

                    text += f"\n📊 **تعداد کل:** {len(fosh_list)} فحش"
                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("clearfosh") & admin_filter)
            async def clear_fosh_command(client, message):
                try:
                    count = self.clear_fosh_list(bot_id)
                    await message.reply_text(f"✅ تمام فحش‌های بات {bot_id} حذف شدند.\n📊 تعداد حذف شده: {count} مورد")
                    self.log_action(bot_id, "clear_fosh", message.from_user.id, f"حذف {count} فحش")
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامندهای دشمنان
            @app.on_message(filters.command("setenemy") & admin_filter & filters.reply)
            async def set_enemy_command(client, message):
                try:
                    replied = message.reply_to_message
                    user_id = replied.from_user.id
                    username = replied.from_user.username
                    first_name = replied.from_user.first_name

                    if self.add_enemy(bot_id, user_id, username, first_name):
                        await message.reply_text(f"👹 کاربر به لیست دشمنان بات {bot_id} اضافه شد:\n**نام:** {first_name}\n**آیدی:** `{user_id}`")
                        self.log_action(bot_id, "add_enemy", user_id, f"{first_name} (@{username})")
                    else:
                        await message.reply_text(f"⚠️ این کاربر قبلاً در لیست دشمنان است")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("delenemy") & admin_filter & filters.reply)
            async def del_enemy_command(client, message):
                try:
                    replied = message.reply_to_message
                    user_id = replied.from_user.id
                    first_name = replied.from_user.first_name

                    if self.remove_enemy(bot_id, user_id):
                        await message.reply_text(f"✅ کاربر از لیست دشمنان بات {bot_id} حذف شد:\n**نام:** {first_name}")
                        self.log_action(bot_id, "del_enemy", user_id, f"{first_name}")
                    else:
                        await message.reply_text(f"⚠️ این کاربر در لیست دشمنان یافت نشد")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("listenemy") & admin_filter)
            async def list_enemy_command(client, message):
                try:
                    enemy_list = self.get_enemy_list(bot_id)
                    if not enemy_list:
                        await message.reply_text(f"📝 لیست دشمنان بات {bot_id} خالی است.")
                        return

                    text = f"👹 **لیست دشمنان بات {bot_id}:**\n\n"
                    for i, (user_id, username, first_name, created_at) in enumerate(enemy_list, 1):
                        text += f"`{i}.` {first_name or 'نامشخص'} (`{user_id}`)\n"
                        if i >= 20:
                            text += f"... و {len(enemy_list) - 20} نفر دیگر\n"
                            break

                    text += f"\n📊 **تعداد کل:** {len(enemy_list)} دشمن"
                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("clearenemy") & admin_filter)
            async def clear_enemy_command(client, message):
                try:
                    count = self.clear_enemy_list(bot_id)
                    await message.reply_text(f"✅ تمام دشمنان بات {bot_id} حذف شدند.\n📊 تعداد حذف شده: {count} نفر")
                    self.log_action(bot_id, "clear_enemy", message.from_user.id, f"حذف {count} دشمن")
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامندهای دوستان
            @app.on_message(filters.command("setfriend") & admin_filter & filters.reply)
            async def set_friend_command(client, message):
                try:
                    replied = message.reply_to_message
                    user_id = replied.from_user.id
                    username = replied.from_user.username
                    first_name = replied.from_user.first_name

                    if self.add_friend(bot_id, user_id, username, first_name):
                        await message.reply_text(f"😊 کاربر به لیست دوستان بات {bot_id} اضافه شد:\n**نام:** {first_name}\n**آیدی:** `{user_id}`")
                        self.log_action(bot_id, "add_friend", user_id, f"{first_name} (@{username})")
                    else:
                        await message.reply_text(f"⚠️ این کاربر قبلاً در لیست دوستان است")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("delfriend") & admin_filter & filters.reply)
            async def del_friend_command(client, message):
                try:
                    replied = message.reply_to_message
                    user_id = replied.from_user.id
                    first_name = replied.from_user.first_name

                    if self.remove_friend(bot_id, user_id):
                        await message.reply_text(f"✅ کاربر از لیست دوستان بات {bot_id} حذف شد:\n**نام:** {first_name}")
                        self.log_action(bot_id, "del_friend", user_id, f"{first_name}")
                    else:
                        await message.reply_text(f"⚠️ این کاربر در لیست دوستان یافت نشد")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("listfriend") & admin_filter)
            async def list_friend_command(client, message):
                try:
                    friend_list = self.get_friend_list(bot_id)
                    if not friend_list:
                        await message.reply_text(f"📝 لیست دوستان بات {bot_id} خالی است.")
                        return

                    text = f"😊 **لیست دوستان بات {bot_id}:**\n\n"
                    for i, (user_id, username, first_name, created_at) in enumerate(friend_list, 1):
                        text += f"`{i}.` {first_name or 'نامشخص'} (`{user_id}`)\n"
                        if i >= 20:
                            text += f"... و {len(friend_list) - 20} نفر دیگر\n"
                            break

                    text += f"\n📊 **تعداد کل:** {len(friend_list)} دوست"
                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("clearfriend") & admin_filter)
            async def clear_friend_command(client, message):
                try:
                    count = self.clear_friend_list(bot_id)
                    await message.reply_text(f"✅ تمام دوستان بات {bot_id} حذف شدند.\n📊 تعداد حذف شده: {count} نفر")
                    self.log_action(bot_id, "clear_friend", message.from_user.id, f"حذف {count} دوست")
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامند اضافه کردن کلمه دوستانه (تمام انواع رسانه)
            @app.on_message(filters.command("addword") & admin_filter)
            async def add_word_command(client, message):
                try:
                    if message.reply_to_message:
                        replied = message.reply_to_message
                        media_type = None
                        file_id = None
                        word_text = None

                        if replied.photo:
                            media_type = "photo"
                            file_id = replied.photo.file_id
                        elif replied.video:
                            media_type = "video"
                            file_id = replied.video.file_id
                        elif replied.animation:
                            media_type = "animation"
                            file_id = replied.animation.file_id
                        elif replied.sticker:
                            media_type = "sticker"
                            file_id = replied.sticker.file_id
                        elif replied.audio:
                            media_type = "audio"
                            file_id = replied.audio.file_id
                        elif replied.voice:
                            media_type = "voice"
                            file_id = replied.voice.file_id
                        elif replied.video_note:
                            media_type = "video_note"
                            file_id = replied.video_note.file_id
                        elif replied.document:
                            media_type = "document"
                            file_id = replied.document.file_id
                        elif replied.text:
                            word_text = replied.text

                        if media_type or word_text:
                            if self.add_friend_word(bot_id, word_text, media_type, file_id):
                                await message.reply_text(f"✅ کلمه دوستانه اضافه شد ({media_type or 'متن'}) - بات {bot_id}")
                                self.log_action(bot_id, "add_word", message.from_user.id, f"{media_type or word_text}")
                            else:
                                await message.reply_text("❌ خطا در اضافه کردن کلمه")
                        else:
                            await message.reply_text("⚠️ نوع رسانه پشتیبانی نمی‌شود")
                    else:
                        if len(message.command) < 2:
                            await message.reply_text("⚠️ لطفاً یک کلمه وارد کنید یا روی پیام ریپلای کنید.\n💡 استفاده: `/addword سلام دوست عزیز`")
                            return

                        word = " ".join(message.command[1:])
                        if self.add_friend_word(bot_id, word):
                            await message.reply_text(f"✅ کلمه دوستانه اضافه شد - بات {bot_id}:\n`{word}`")
                            self.log_action(bot_id, "add_word", message.from_user.id, word[:50])
                        else:
                            await message.reply_text("❌ خطا در اضافه کردن کلمه")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("delword") & admin_filter)
            async def del_word_command(client, message):
                try:
                    if len(message.command) < 2:
                        await message.reply_text("⚠️ لطفاً کلمه مورد نظر را وارد کنید.\n💡 استفاده: `/delword کلمه`")
                        return

                    word = " ".join(message.command[1:])
                    if self.remove_friend_word(bot_id, word):
                        await message.reply_text(f"✅ کلمه دوستانه حذف شد - بات {bot_id}:\n`{word}`")
                        self.log_action(bot_id, "del_word", message.from_user.id, word[:50])
                    else:
                        await message.reply_text(f"⚠️ این کلمه در لیست یافت نشد:\n`{word}`")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("listword") & admin_filter)
            async def list_word_command(client, message):
                try:
                    word_list = self.get_friend_words(bot_id)
                    if not word_list:
                        await message.reply_text(f"📝 لیست کلمات دوستانه بات {bot_id} خالی است.\n💡 با `/addword` کلمه اضافه کنید.")
                        return

                    text = f"💬 **لیست کلمات دوستانه بات {bot_id}:**\n\n"
                    for i, (word, media_type, file_id) in enumerate(word_list, 1):
                        if media_type:
                            text += f"`{i}.` [{media_type.upper()}]\n"
                        else:
                            text += f"`{i}.` {word}\n"

                        if i >= 20:
                            text += f"\n... و {len(word_list) - 20} مورد دیگر"
                            break

                    text += f"\n📊 **تعداد کل:** {len(word_list)} کلمه"
                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("clearword") & admin_filter)
            async def clear_word_command(client, message):
                try:
                    count = self.clear_friend_words(bot_id)
                    await message.reply_text(f"✅ تمام کلمات دوستانه بات {bot_id} حذف شدند.\n📊 تعداد حذف شده: {count} مورد")
                    self.log_action(bot_id, "clear_word", message.from_user.id, f"حذف {count} کلمه")
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامند آمار
            @app.on_message(filters.command("stats") & admin_filter)
            async def stats_command(client, message):
                try:
                    stats = self.get_stats(bot_id)

                    text = f"📊 **آمار کامل ربات {bot_id}:**\n\n"
                    text += f"🔥 فحش‌ها: `{stats['fosh_count']}` عدد\n"
                    text += f"👹 دشمنان: `{stats['enemy_count']}` نفر\n"
                    text += f"😊 دوستان: `{stats['friend_count']}` نفر\n"
                    text += f"💬 کلمات دوستانه: `{stats['word_count']}` عدد\n\n"
                    text += f"🤖 **وضعیت پاسخگویی:** {'فعال ✅' if config['auto_reply_enabled'] else 'غیرفعال ❌'}\n"
                    text += f"⏰ **آخرین بروزرسانی:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                    await message.reply_text(text)
                    self.log_action(bot_id, "stats_view", message.from_user.id, "نمایش آمار")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامند فعال/غیرفعال پاسخگویی
            @app.on_message(filters.command(["autoreply", "toggle", "runself"]) & admin_filter)
            async def toggle_auto_reply(client, message):
                try:
                    self.bot_configs[bot_id]['auto_reply_enabled'] = True
                    await message.reply_text(f"🤖 **پاسخگویی خودکار بات {bot_id} فعال شد ✅**")
                    self.log_action(bot_id, "toggle_auto_reply", message.from_user.id, "فعال")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("offself") & admin_filter)
            async def off_auto_reply(client, message):
                try:
                    self.bot_configs[bot_id]['auto_reply_enabled'] = False
                    await message.reply_text(f"🤖 **پاسخگویی خودکار بات {bot_id} غیرفعال شد ❌**")
                    self.log_action(bot_id, "toggle_auto_reply", message.from_user.id, "غیرفعال")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامند ارسال همگانی
            @app.on_message(filters.command("broadcast") & admin_filter)
            async def broadcast_command(client, message):
                try:
                    if len(message.command) < 2 and not message.reply_to_message:
                        await message.reply_text("⚠️ لطفاً پیام مورد نظر را وارد کنید یا روی پیام ریپلای کنید.\n💡 استفاده: `/broadcast سلام به همه`")
                        return

                    if message.reply_to_message:
                        target_message = message.reply_to_message
                    else:
                        text = " ".join(message.command[1:])

                    await message.reply_text(f"📤 شروع ارسال همگانی از بات {bot_id}...")

                    success = 0
                    fail = 0

                    async for dialog in client.get_dialogs():
                        if dialog.chat.type in ["group", "supergroup"]:
                            try:
                                if message.reply_to_message:
                                    await target_message.copy(dialog.chat.id)
                                else:
                                    await client.send_message(dialog.chat.id, text)
                                success += 1
                                await asyncio.sleep(0.01)
                            except FloodWait as e:
                                await asyncio.sleep(e.value)
                                try:
                                    if message.reply_to_message:
                                        await target_message.copy(dialog.chat.id)
                                    else:
                                        await client.send_message(dialog.chat.id, text)
                                    success += 1
                                except:
                                    fail += 1
                            except:
                                fail += 1

                    result_text = f"✅ **ارسال همگانی بات {bot_id} تکمیل شد:**\n\n"
                    result_text += f"📤 **موفق:** {success} گروه\n"
                    result_text += f"❌ **ناموفق:** {fail} گروه\n"
                    result_text += f"📊 **کل:** {success + fail} گروه"

                    # ارسال نتیجه در پیام جدید
                    await client.send_message(message.chat.id, result_text)
                    self.log_action(bot_id, "broadcast", message.from_user.id, f"موفق:{success}, ناموفق:{fail}")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامند اکو برای بات 3 (فقط دشمنان می‌توانند استفاده کنند)
            if bot_id == 3:
                @app.on_message(filters.command("echo") & filters.group)
                async def echo_command(client, message):
                    try:
                        user_id = message.from_user.id if message.from_user else None
                        if not user_id:
                            return

                        # اگر ادمین است، هیچ کاری نکن
                        if user_id in self.all_admin_ids:
                            return

                        # بررسی اینکه کاربر دشمن باشد
                        enemy_list = self.get_enemy_list(bot_id)
                        enemy_ids = {row[0] for row in enemy_list}

                        if user_id not in enemy_ids:
                            return  # اگر دشمن نیست، هیچ کاری نکن

                        # فعال کردن حالت اکو
                        import sys
                        sys.path.append('./bots')
                        from echo_control import set_echo_active
                        set_echo_active(True)

                        # استخراج متن بعد از /echo
                        echo_text = None
                        if len(message.command) > 1:
                            # متن بعد از /echo
                            echo_text = " ".join(message.command[1:])

                        try:
                            if message.reply_to_message:
                                # اگر روی پیامی ریپلای شده، همان پیام را اکو کن
                                target_message = message.reply_to_message

                                if target_message.text:
                                    await client.send_message(
                                        message.chat.id,
                                        target_message.text,
                                        reply_to_message_id=target_message.reply_to_message_id if target_message.reply_to_message else None
                                    )
                                elif target_message.photo:
                                    await client.send_photo(
                                        message.chat.id,
                                        target_message.photo.file_id,
                                        caption=target_message.caption,
                                        reply_to_message_id=target_message.reply_to_message_id if target_message.reply_to_message else None
                                    )
                                elif target_message.video:
                                    await client.send_video(
                                        message.chat.id,
                                        target_message.video.file_id,
                                        caption=target_message.caption,
                                        reply_to_message_id=target_message.reply_to_message_id if target_message.reply_to_message else None
                                    )
                                elif target_message.animation:
                                    await client.send_animation(
                                        message.chat.id,
                                        target_message.animation.file_id,
                                        caption=target_message.caption,
                                        reply_to_message_id=target_message.reply_to_message_id if target_message.reply_to_message else None
                                    )
                                elif target_message.sticker:
                                    await client.send_sticker(
                                        message.chat.id,
                                        target_message.sticker.file_id,
                                        reply_to_message_id=target_message.reply_to_message_id if target_message.reply_to_message else None
                                    )
                                elif target_message.audio:
                                    await client.send_audio(
                                        message.chat.id,
                                        target_message.audio.file_id,
                                        caption=target_message.caption,
                                        reply_to_message_id=target_message.reply_to_message_id if target_message.reply_to_message else None
                                    )
                                elif target_message.voice:
                                    await client.send_voice(
                                        message.chat.id,
                                        target_message.voice.file_id,
                                        caption=target_message.caption,
                                        reply_to_message_id=target_message.reply_to_message_id if target_message.reply_to_message else None
                                    )
                                elif target_message.video_note:
                                    await client.send_video_note(
                                        message.chat.id,
                                        target_message.video_note.file_id,
                                        reply_to_message_id=target_message.reply_to_message_id if target_message.reply_to_message else None
                                    )
                                elif target_message.document:
                                    await client.send_document(
                                        message.chat.id,
                                        target_message.document.file_id,
                                        caption=target_message.caption,
                                        reply_to_message_id=target_message.reply_to_message_id if target_message.reply_to_message else None
                                    )
                            elif echo_text:
                                # اگر متن بعد از /echo وجود دارد، آن را اکو کن
                                await client.send_message(message.chat.id, echo_text)

                            # غیرفعال کردن حالت اکو بعد از اکو
                            await asyncio.sleep(0.1)  # کمی تاخیر برای اطمینان از ارسال
                            set_echo_active(False)

                        except Exception as echo_error:
                            logger.error(f"خطا در اکو کردن پیام: {echo_error}")
                            set_echo_active(False)

                    except Exception as e:
                        logger.error(f"خطا در کامند اکو: {e}")

            # کامند مدیریت توقف اسپم
            @app.on_message(filters.command("pausestatus") & admin_filter)
            async def pause_status_command(client, message):
                try:
                    if not self.global_paused:
                        await message.reply_text(f"✅ **وضعیت سیستم:** همه بات‌ها فعال در همه چت‌ها")
                        return

                    text = f"⏸️ **چت‌های متوقف شده (کلی):**\n\n"
                    for chat_id, user_id in self.global_paused.items():
                        try:
                            chat_info = await client.get_chat(chat_id)
                            chat_name = chat_info.title or f"چت {chat_id}"
                        except:
                            chat_name = f"چت {chat_id}"

                        text += f"🔸 {chat_name}\n   └ متوقف توسط: `{user_id}`\n"

                    text += f"\n📌 **نحوه ازسرگیری:** دشمن باید پیام بفرسته"
                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("resumespam") & admin_filter)
            async def resume_spam_command(client, message):
                try:
                    if len(message.command) < 2:
                        await message.reply_text("⚠️ استفاده: `/resumespam [chat_id]`\nمثال: `/resumespam -1001234567890`")
                        return

                    try:
                        chat_id = int(message.command[1])
                    except ValueError:
                        await message.reply_text("❌ شناسه چت نامعتبر")
                        return

                    if chat_id in self.global_paused:
                        user_id = self.global_paused[chat_id]
                        del self.global_paused[chat_id]
                        await message.reply_text(f"▶️ **همه بات‌ها در چت `{chat_id}` ازسرگیری شدند**\n👤 متوقف شده توسط: `{user_id}`")
                        self.log_action(bot_id, "manual_global_resume", message.from_user.id, f"ازسرگیری دستی کلی در چت {chat_id}")
                    else:
                        await message.reply_text(f"✅ چت `{chat_id}` قبلاً فعال بوده")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامند مدیریت ایموجی‌های ممنوعه
            @app.on_message(filters.command("addemoji") & admin_filter)
            async def add_emoji_command(client, message):
                """🆕 اضافه کردن ایموجی ممنوعه با ویژگی‌های پیشرفته"""
                try:
                    if len(message.command) < 2:
                        await message.reply_text(
                            "⚠️ **استفاده صحیح:**\n"
                            "`/addemoji [ایموجی] [توضیحات] [سطح خطر: 1-3]`\n\n"
                            "**مثال‌ها:**\n"
                            "• `/addemoji ⚡`\n"
                            "• `/addemoji 🔮 ایموجی خطرناک`\n"
                            "• `/addemoji 💎 الماس گران‌بها 3`"
                        )
                        return

                    emoji = message.command[1]
                    
                    # پردازش آرگومان‌ها
                    args = message.command[2:]
                    description = ""
                    severity_level = 1
                    
                    # جدا کردن سطح خطر از توضیحات
                    if args:
                        # بررسی آخرین آرگومان برای سطح خطر
                        try:
                            severity_level = int(args[-1])
                            if 1 <= severity_level <= 3:
                                description = " ".join(args[:-1]) if len(args) > 1 else ""
                            else:
                                severity_level = 1
                                description = " ".join(args)
                        except ValueError:
                            description = " ".join(args)
                    
                    if not description:
                        description = "بدون توضیحات"

                    user_id = message.from_user.id
                    username = message.from_user.username or message.from_user.first_name

                    print(f"🔍 اضافه کردن ایموجی: '{emoji}' | توضیحات: '{description}' | سطح: {severity_level}")

                    # سعی در اضافه کردن با سیستم پیشرفته
                    success = False
                    try:
                        success = self.add_forbidden_emoji_ultra_advanced(emoji, description, severity_level, user_id, username)
                    except:
                        # اگر سیستم پیشرفته کار نکرد، از سیستم عادی استفاده کنیم
                        success = self.add_forbidden_emoji_advanced(emoji, description, 'custom', user_id)
                    
                    if success:
                        severity_text = ["", "🟢 کم", "🟡 متوسط", "🔴 بالا"][severity_level]
                        await message.reply_text(
                            f"✅ **ایموجی ممنوعه اضافه شد**\n\n"
                            f"🎯 **ایموجی:** {emoji}\n"
                            f"📝 **توضیحات:** {description}\n"
                            f"⚡ **سطح خطر:** {severity_text}\n"
                            f"👤 **اضافه‌کننده:** {username}\n"
                            f"🕐 **زمان:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                            f"✅ **تشخیص در همه ۹ بات فعال شد!**\n"
                            f"🔄 **ویژگی‌های فعال:** توقف خودکار، اعلان فوری"
                        )

                        # بارگذاری فوری ایموجی‌ها در همه بات‌ها
                        await self.sync_forbidden_emojis_across_all_bots()
                        
                        # گزارش به ربات مانیتورینگ (بدون تاخیر)
                        if self.report_bot:
                            report_text = f"🆕 ایموجی ممنوعه: {emoji} | سطح: {severity_text} | توسط: {username}"
                            asyncio.create_task(self.send_report_safely(report_text))

                        self.log_action(bot_id, "add_emoji_advanced", user_id, f"اضافه کردن {emoji} با سطح {severity_level}")
                        logger.info(f"✅ ایموجی {emoji} با سطح {severity_level} اضافه شد توسط {user_id}")
                    else:
                        # بررسی دقیق‌تر برای نمایش علت
                        if emoji in self.forbidden_emojis:
                            await message.reply_text(
                                f"⚠️ **ایموجی از قبل موجود است**\n\n"
                                f"🎯 **ایموجی:** {emoji}\n"
                                f"✅ **وضعیت:** در لیست ممنوعه‌ها موجود است\n"
                                f"📋 **برای مشاهده:** `/listemoji`\n"
                                f"🔄 **برای حذف:** `/delemoji {emoji}`"
                            )
                        else:
                            await message.reply_text(
                                f"✅ **ایموجی با موفقیت پردازش شد**\n\n"
                                f"🎯 **ایموجی:** {emoji}\n"
                                f"📝 **توضیحات:** {description}\n"
                                f"⚡ **سطح خطر:** {severity_text}\n"
                                f"✅ **حالت:** فعال در همه ۹ بات\n"
                                f"💡 **نکته:** ایموجی حالا قابل تشخیص است"
                            )

                except Exception as e:
                    logger.error(f"❌ خطا در کامند addemoji: {e}")
                    await message.reply_text(
                        f"❌ **خطای سیستمی**\n\n"
                        f"🔹 **پیام خطا:** {str(e)}\n"
                        f"🔹 **راهکار:** دوباره تلاش کنید"
                    )

            @app.on_message(filters.command("delemoji") & admin_filter)
            async def del_emoji_command(client, message):
                try:
                    if len(message.command) < 2:
                        await message.reply_text("❌ **استفاده صحیح:** `/delemoji [ایموجی]`")
                        return

                    emoji = message.command[1]
                    user_id = message.from_user.id

                    success, msg = self.remove_forbidden_emoji_advanced(emoji, user_id)
                    if success:
                        await message.reply_text(
                            f"✅ **ایموجی ممنوعه حذف شد**\n\n"
                            f"🔹 **ایموجی:** {emoji}\n"
                            f"🔹 **مجموع ایموجی‌ها:** {len(self.forbidden_emojis)} عدد"
                        )

                        # بارگذاری مجدد ایموجی‌ها
                        self.forbidden_emojis = self.load_forbidden_emojis_from_db()
                        logger.info(f"✅ ایموجی {emoji} از سیستم امنیتی حذف شد توسط {user_id}")

                        # گزارش
                        if self.report_bot:
                            report_text = f"🗑️ ایموجی ممنوعه حذف شد: {emoji}\n"
                            report_text += f"👤 توسط: {message.from_user.first_name} ({message.from_user.id})"
                            await self.send_report_safely(report_text)
                    else:
                        await message.reply_text(f"❌ {msg}")

                except Exception as e:
                    logger.error(f"❌ خطا در کامند delemoji: {e}")
                    await message.reply_text(f"❌ خطای سیستمی: {str(e)}")

            @app.on_message(filters.command("listemoji") & admin_filter)
            async def list_emoji_command(client, message):
                """لیست پیشرفته ایموجی‌های ممنوعه"""
                try:
                    emoji_list = self.list_forbidden_emojis_advanced()

                    if not emoji_list:
                        await message.reply_text(
                            "📝 **لیست ایموجی‌های ممنوعه خالی است**\n\n"
                            "💡 با `/addemoji [ایموجی]` ایموجی اضافه کنید.\n"
                            "📚 کامندهای مفید:\n"
                            "• `/addword [کلمه]` - اضافه کردن کلمه ممنوعه\n"
                            "• `/listword` - لیست کلمات ممنوعه\n"
                            "• `/securitystats` - آمار امنیتی"
                        )
                        return

                    text = "🚫 **لیست ایموجی‌های ممنوعه (همه بات‌ها):**\n\n"

                    for i, emoji_data in enumerate(emoji_list[:15], 1):
                        text += f"`{i}.` {emoji_data['emoji']}"
                        if emoji_data['description'] and emoji_data['description'] != 'اضافه شده توسط ادمین':
                            text += f" - {emoji_data['description'][:25]}"
                        text += f" ({emoji_data['category']})\n"

                    if len(emoji_list) > 15:
                        text += f"\n... و {len(emoji_list) - 15} ایموجی دیگر"

                    text += f"\n\n📊 **آمار:**\n"
                    text += f"• تعداد کل: {len(emoji_list)} ایموجی\n"
                    text += f"• وضعیت تشخیص: {'✅ فعال' if self.security_settings['emoji_detection_enabled'] else '❌ غیرفعال'}\n"
                    text += f"• آخرین بروزرسانی: {datetime.now().strftime('%H:%M:%S')}\n\n"
                    text += f"💡 **راهنما:** `/testemoji [ایموجی]` برای تست تشخیص"

                    await message.reply_text(text)

                except Exception as e:
                    logger.error(f"❌ خطا در کامند listemoji: {e}")
                    await message.reply_text(f"❌ خطای سیستمی: {str(e)}")

            @app.on_message(filters.command("testemoji") & admin_filter)
            async def test_emoji_command(client, message):
                try:
                    parts = message.text.split(None, 1)
                    if len(parts) < 2:
                        await message.reply_text("❌ **استفاده صحیح:** `/testemoji [ایموجی]`\nمثال: `/testemoji ⚡️`")
                        return

                    test_emoji = parts[1]

                    # تست تشخیص
                    found_emoji_ref = []
                    is_detected = self.contains_stop_emoji(test_emoji, found_emoji_ref)

                    # نمایش جزئیات
                    import unicodedata
                    unicode_codes = [f"U+{ord(char):04X}" for char in test_emoji]
                    normalized = self.normalize_emoji(test_emoji)
                    normalized_codes = [f"U+{ord(char):04X}" for char in normalized] if normalized else []

                    text = f"🔍 **تست تشخیص ایموجی:**\n\n"
                    text += f"ایموجی: {test_emoji}\n"
                    text += f"کد اصلی: `{' '.join(unicode_codes)}`\n"
                    text += f"نرمال شده: {normalized}\n"
                    text += f"کد نرمال: `{' '.join(normalized_codes)}`\n"
                    text += f"در لیست ممنوعه: {'✅ بله' if test_emoji in self.forbidden_emojis else '❌ خیر'}\n"
                    text += f"تشخیص داده شد: {'✅ بله' if is_detected else '❌ خیر'}\n"
                    if found_emoji_ref:
                        text += f"ایموجی یافت شده: {found_emoji_ref[0]}\n"
                    text += f"\n📊 تعداد کل ایموجی‌های ممنوعه: {len(self.forbidden_emojis)}\n"
                    text += f"🚀 سرعت تشخیص: {self.detection_cooldown} ms"

                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("syncemojis") & admin_filter)
            async def sync_emojis_command(client, message):
                try:
                    # بارگذاری مجدد ایموجی‌ها از دیتابیس برای همه بات‌ها
                    old_count = len(self.forbidden_emojis)
                    fresh_emojis = self.load_forbidden_emojis_from_db()
                    self.forbidden_emojis = fresh_emojis
                    new_count = len(self.forbidden_emojis)

                    status_text = f"🔄 **همگام‌سازی ایموجی‌های ممنوعه:**\n\n"
                    status_text += f"📊 تعداد قبل: {old_count} ایموجی\n"
                    status_text += f"📊 تعداد بعد: {new_count} ایموجی\n"
                    status_text += f"🔄 تغییر: {new_count - old_count:+d} ایموجی\n\n"
                    status_text += f"✅ همه ۹ بات هماهنگ شدند\n"
                    status_text += f"🕐 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                    await message.reply_text(status_text)
                    self.log_action(bot_id, "sync_emojis", message.from_user.id, f"همگام‌سازی: {old_count} -> {new_count}")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("debugemoji") & admin_filter)
            async def debug_emoji_command(client, message):
                try:
                    if len(message.command) < 2:
                        await message.reply_text("❌ **استفاده صحیح:** `/debugemoji [متن]`\nمثال: `/debugemoji A CHARACTER HAS SPAWNED ⚡`")
                        return

                    test_text = " ".join(message.command[1:])

                    # تست تشخیص با زمان‌سنجی
                    import time
                    start_time = time.time()
                    found_emoji_ref = []
                    is_detected = self.contains_stop_emoji(test_text, found_emoji_ref)
                    end_time = time.time()
                    detection_time = (end_time - start_time) * 1000  # میلی‌ثانیه

                    # نمایش جزئیات کامل
                    debug_text = f"🔍 **دیباگ تشخیص ایموجی (نسخه بهبود یافته):**\n\n"
                    debug_text += f"📝 متن تست: `{test_text}`\n"
                    debug_text += f"🎯 تشخیص داده شد: {'✅ بله' if is_detected else '❌ خیر'}\n"
                    debug_text += f"⏱️ زمان تشخیص: {detection_time:.2f}ms\n"

                    if found_emoji_ref:
                        debug_text += f"⚡ ایموجی یافت شده: `{found_emoji_ref[0]}`\n"
                        # نمایش کدهای Unicode
                        unicode_codes = [f"U+{ord(c):04X}" for c in found_emoji_ref[0]]
                        debug_text += f"🔢 کدهای Unicode: `{' '.join(unicode_codes)}`\n"

                    debug_text += f"📊 تعداد ایموجی‌های ممنوعه: {len(self.forbidden_emojis)}\n"
                    debug_text += f"🔄 وضعیت cache: {len(self.detection_cache)} آیتم\n\n"

                    # نمایش تمام ایموجی‌های ممنوعه فعلی
                    if self.forbidden_emojis:
                        debug_text += "📋 **ایموجی‌های ممنوعه فعلی:**\n"
                        for i, emoji in enumerate(list(self.forbidden_emojis)[:10], 1):
                            unicode_codes = [f"U+{ord(c):04X}" for c in emoji]
                            debug_text += f"{i}. `{emoji}` ({' '.join(unicode_codes)})\n"
                        if len(self.forbidden_emojis) > 10:
                            debug_text += f"... و {len(self.forbidden_emojis) - 10} مورد دیگر\n"

                    await message.reply_text(debug_text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("quicktest") & admin_filter)
            async def quick_test_command(client, message):
                try:
                    test_cases = [
                        "⚡ برق",
                        "⚡️ برق با variation",
                        "🔮 کریستال",
                        "💎 الماس",
                        "A CHARACTER HAS SPAWNED ⚡",
                        "متن عادی",
                    ]

                    result_text = "🧪 **تست سریع تشخیص:**\n\n"
                    detected_count = 0
                    total_time = 0

                    for i, test_text in enumerate(test_cases, 1):
                        import time
                        start_time = time.time()
                        found_emoji_ref = []
                        is_detected = self.contains_stop_emoji(test_text, found_emoji_ref)
                        end_time = time.time()
                        detection_time = (end_time - start_time) * 1000
                        total_time += detection_time

                        if is_detected:
                            detected_count += 1
                            status = "✅"
                            found_text = f" ({found_emoji_ref[0]})" if found_emoji_ref else ""
                        else:
                            status = "❌"
                            found_text = ""

                        result_text += f"`{i}.` {test_text[:20]}... → {status}{found_text}\n"

                    avg_time = total_time / len(test_cases)
                    result_text += f"\n📊 **نتایج:**\n"
                    result_text += f"🎯 تشخیص: {detected_count}/{len(test_cases)}\n"
                    result_text += f"⏱️ میانگین: {avg_time:.2f}ms\n"
                    result_text += f"🚀 سرعت: {1000/avg_time:.0f}/ثانیه"

                    await message.reply_text(result_text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # =================================================================
            # کامندهای پیشرفته مدیریت تاخیر - Advanced Delay Management Commands
            # =================================================================

            @app.on_message(filters.command("setdelay") & admin_filter)
            async def set_delay_command(client, message):
                """تنظیم تاخیر پیشرفته"""
                try:
                    # بهبود پارس کردن کامند برای رفع مشکل فاصله
                    command_parts = message.command[1:] if len(message.command) > 1 else []
                    
                    # اگر فقط یک قسمت داریم، سعی کن جدا کنیم
                    if len(command_parts) == 1 and command_parts[0]:
                        # جستجوی الگوهای متصل مثل enemy_spam2.5
                        import re
                        match = re.match(r'([a-zA-Z_]+)([0-9.]+)$', command_parts[0])
                        if match:
                            command_parts = [match.group(1), match.group(2)]
                    
                    if len(command_parts) < 2:
                        delay_types = list(self.advanced_delay_settings.keys())
                        await message.reply_text(
                            f"⚠️ **استفاده درست:** `/setdelay [نوع] [مقدار]`\n\n"
                            f"**انواع تاخیر:**\n"
                            f"• `enemy_spam` - تاخیر اسپم دشمنان ({self.advanced_delay_settings['enemy_spam_delay']}s)\n"
                            f"• `friend_reply` - پاسخ به دوستان ({self.advanced_delay_settings['friend_reply_delay']}s)\n"
                            f"• `global_msg` - پیام‌های کلی ({self.advanced_delay_settings['global_message_delay']}s)\n"
                            f"• `conversation` - گفتگوی خودکار ({self.advanced_delay_settings['conversation_delay']}s)\n"
                            f"• `emoji_react` - واکنش ایموجی ({self.advanced_delay_settings['emoji_reaction_delay']}s)\n"
                            f"• `burst_protect` - محافظت سیل ({self.advanced_delay_settings['burst_protection_delay']}s)\n\n"
                            f"**✅ مثال درست:** `/setdelay enemy_spam 2.5`\n"
                            f"**❌ اشتباه:** `/setdelayenemy_spam 2.5` یا `/setdelay enemy_spam2.5`\n"
                            f"**نکته:** حتماً بین همه قسمت‌ها فاصله بگذارید"
                        )
                        return

                    delay_type = command_parts[0].strip()
                    try:
                        delay_value = float(command_parts[1].strip())
                    except (ValueError, IndexError):
                        await message.reply_text(
                            f"❌ **خطا در مقدار تاخیر**\n\n"
                            f"مقدار باید عدد باشد (مثال: 2.5 یا 1.0)\n"
                            f"**مثال درست:** `/setdelay {delay_type} 2.5`\n"
                            f"**فرمت شما:** `/setdelay {' '.join(command_parts)}`\n\n"
                            f"لطفاً فاصله بین نوع تاخیر و مقدار رعایت کنید"
                        )
                        return

                    # مپ کردن اسامی کوتاه
                    delay_map = {
                        'enemy_spam': 'enemy_spam_delay',
                        'friend_reply': 'friend_reply_delay', 
                        'global_msg': 'global_message_delay',
                        'conversation': 'conversation_delay',
                        'emoji_react': 'emoji_reaction_delay',
                        'burst_protect': 'burst_protection_delay'
                    }

                    if delay_type not in delay_map:
                        await message.reply_text("❌ نوع تاخیر نامعتبر است")
                        return

                    actual_key = delay_map[delay_type]
                    old_value = self.advanced_delay_settings[actual_key]
                    self.advanced_delay_settings[actual_key] = max(0.01, min(delay_value, 30.0))

                    await message.reply_text(
                        f"✅ **تاخیر تنظیم شد**\n\n"
                        f"🎯 **نوع:** {delay_type}\n"
                        f"⏱️ **مقدار قبلی:** {old_value}s\n"
                        f"⏱️ **مقدار جدید:** {self.advanced_delay_settings[actual_key]}s\n"
                        f"🤖 **اعمال در:** همه ۹ بات\n"
                        f"🕐 **زمان:** {time.strftime('%H:%M:%S')}"
                    )

                    self.log_action(bot_id, "set_delay", message.from_user.id, 
                                  f"{delay_type}: {old_value} -> {self.advanced_delay_settings[actual_key]}")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("chatdelay") & admin_filter)
            async def chat_delay_command(client, message):
                """تنظیم تاخیر مختص چت"""
                try:
                    if len(message.command) < 3:
                        await message.reply_text(
                            f"⚠️ **استفاده:** `/chatdelay [chat_id] [ضریب]`\n\n"
                            f"**ضریب تاخیر:**\n"
                            f"• `0.5` - سریع (نصف تاخیر)\n"
                            f"• `1.0` - عادی (بدون تغییر)\n"
                            f"• `2.0` - آهسته (دو برابر تاخیر)\n"
                            f"• `0.1` - فوری (حداقل تاخیر)\n\n"
                            f"**مثال:** `/chatdelay -1001234567890 0.5`"
                        )
                        return

                    try:
                        chat_id = int(message.command[1])
                        multiplier = float(message.command[2])
                    except ValueError:
                        await message.reply_text("❌ chat_id باید عدد صحیح و ضریب باید عدد اعشاری باشد")
                        return

                    multiplier = max(0.1, min(multiplier, 10.0))  # محدود کردن

                    if chat_id not in self.chat_specific_delays:
                        self.chat_specific_delays[chat_id] = {}
                    
                    old_multiplier = self.chat_specific_delays[chat_id].get('multiplier', 1.0)
                    self.chat_specific_delays[chat_id]['multiplier'] = multiplier
                    self.chat_specific_delays[chat_id]['updated_at'] = time.time()

                    try:
                        chat_info = await client.get_chat(chat_id)
                        chat_name = chat_info.title or f"چت {chat_id}"
                    except:
                        chat_name = f"چت {chat_id}"

                    await message.reply_text(
                        f"✅ **تاخیر چت تنظیم شد**\n\n"
                        f"💬 **چت:** {chat_name}\n"
                        f"🆔 **شناسه:** `{chat_id}`\n"
                        f"⏱️ **ضریب قبلی:** {old_multiplier}x\n"
                        f"⏱️ **ضریب جدید:** {multiplier}x\n"
                        f"📊 **معنی:** تاخیرها {multiplier} برابر اعمال می‌شوند\n"
                        f"🕐 **زمان:** {time.strftime('%H:%M:%S')}"
                    )

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("delayinfo") & admin_filter)
            async def delay_info_command(client, message):
                """نمایش اطلاعات کامل تاخیرها"""
                try:
                    info_text = f"⚡ **تنظیمات تاخیر پیشرفته**\n\n"
                    
                    # تاخیرهای کلی
                    info_text += f"🌐 **تاخیرهای کلی:**\n"
                    for key, value in self.advanced_delay_settings.items():
                        if isinstance(value, (int, float)):
                            persian_name = {
                                'enemy_spam_delay': 'اسپم دشمنان',
                                'friend_reply_delay': 'پاسخ دوستان', 
                                'global_message_delay': 'پیام کلی',
                                'conversation_delay': 'گفتگوی خودکار',
                                'emoji_reaction_delay': 'واکنش ایموجی',
                                'burst_protection_delay': 'محافظت سیل',
                                'per_chat_delay_multiplier': 'ضریب چت'
                            }.get(key, key)
                            info_text += f"• {persian_name}: `{value}s`\n"
                    
                    # تاخیرهای مختص چت
                    if self.chat_specific_delays:
                        info_text += f"\n💬 **تاخیرهای مختص چت:**\n"
                        for chat_id, settings in list(self.chat_specific_delays.items())[:5]:
                            try:
                                chat_info = await client.get_chat(chat_id)
                                chat_name = chat_info.title or f"چت {chat_id}"
                                chat_name = chat_name[:20] + "..." if len(chat_name) > 20 else chat_name
                            except:
                                chat_name = f"چت {chat_id}"
                            
                            multiplier = settings.get('multiplier', 1.0)
                            info_text += f"• {chat_name}: `{multiplier}x`\n"
                        
                        if len(self.chat_specific_delays) > 5:
                            info_text += f"... و {len(self.chat_specific_delays) - 5} چت دیگر\n"
                    
                    # وضعیت سیستم
                    info_text += f"\n🔧 **وضعیت سیستم:**\n"
                    info_text += f"• تاخیر انطباقی: {'✅' if self.advanced_delay_settings.get('adaptive_delay_enabled') else '❌'}\n"
                    info_text += f"• کاهش هوشمند: {'✅' if self.advanced_delay_settings.get('smart_delay_reduction') else '❌'}\n"
                    info_text += f"• حداقل تاخیر کلی: `{self.min_global_delay}s`\n"
                    
                    # آمار
                    active_chats = len([t for t in self.last_message_time.values() if time.time() - t < 300])
                    info_text += f"\n📊 **آمار:**\n"
                    info_text += f"• چت‌های فعال: {active_chats}\n"
                    info_text += f"• چت‌های با تاخیر خاص: {len(self.chat_specific_delays)}\n"
                    info_text += f"• آخرین بروزرسانی: {time.strftime('%H:%M:%S')}\n\n"
                    info_text += f"💡 **کامندها:** `/setdelay`, `/chatdelay`, `/resetdelay`"

                    await message.reply_text(info_text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("resetdelay") & admin_filter)
            async def reset_delay_command(client, message):
                """بازنشانی تاخیرها به حالت پیش‌فرض"""
                try:
                    # ذخیره تنظیمات قبلی
                    old_settings = self.advanced_delay_settings.copy()
                    old_chat_delays = self.chat_specific_delays.copy()
                    
                    # بازنشانی به پیش‌فرض
                    self.advanced_delay_settings = {
                        'enemy_spam_delay': 1.0,
                        'friend_reply_delay': 0.3,
                        'global_message_delay': 0.5,
                        'conversation_delay': 2.0,
                        'emoji_reaction_delay': 0.1,
                        'burst_protection_delay': 3.0,
                        'per_chat_delay_multiplier': 1.0,
                        'adaptive_delay_enabled': True,
                        'smart_delay_reduction': True,
                    }
                    self.chat_specific_delays = {}
                    self.min_global_delay = 0.5

                    await message.reply_text(
                        f"🔄 **تاخیرها بازنشانی شدند**\n\n"
                        f"✅ تاخیرهای کلی: حالت پیش‌فرض\n"
                        f"✅ تاخیرهای چت: پاک شدند ({len(old_chat_delays)} چت)\n"
                        f"✅ تنظیمات پیشرفته: فعال\n"
                        f"🤖 **اعمال در:** همه ۹ بات\n"
                        f"🕐 **زمان:** {time.strftime('%H:%M:%S')}\n\n"
                        f"💡 با `/delayinfo` وضعیت جدید را ببینید"
                    )

                    self.log_action(bot_id, "reset_delays", message.from_user.id, 
                                  f"Reset all delays to default")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # =================================================================
            # کامندهای راهنما - Help Commands System
            # =================================================================

            @app.on_message(filters.command("help") & admin_filter)
            async def help_general_command(client, message):
                """راهنمای کلی سیستم"""
                try:
                    # خواندن از فایل راهنمای کلی
                    try:
                        with open('guides/GENERAL_GUIDE.md', 'r', encoding='utf-8') as f:
                            guide_content = f.read()
                        
                        # استخراج بخش‌های کلیدی از markdown
                        lines = guide_content.split('\n')
                        help_sections = []
                        current_section = []
                        in_code_block = False
                        
                        for line in lines:
                            if line.strip().startswith('```'):
                                in_code_block = not in_code_block
                                if in_code_block:
                                    current_section.append('```')
                                else:
                                    current_section.append('```')
                                    if current_section:
                                        help_sections.append('\n'.join(current_section))
                                        current_section = []
                            elif in_code_block:
                                current_section.append(line)
                            elif line.startswith('## '):
                                if current_section:
                                    help_sections.append('\n'.join(current_section))
                                current_section = [f"**{line[3:]}**"]
                            elif line.startswith('### '):
                                current_section.append(f"• **{line[4:]}**")
                            elif line.strip() and not line.startswith('#'):
                                current_section.append(line)
                        
                        if current_section:
                            help_sections.append('\n'.join(current_section))
                        
                        # ساخت متن راهنما با محدودیت طول تلگرام
                        help_text = "📚 **راهنمای کامل سیستم**\n\n"
                        help_text += "**دسترسی سریع به راهنماها:**\n"
                        help_text += "`/helpemoji` - 🚫 مدیریت ایموجی‌ها\n"
                        help_text += "`/helpword` - 📝 مدیریت کلمات\n"
                        help_text += "`/helpdelay` - ⏱️ سیستم تاخیر\n"
                        help_text += "`/helpuser` - 👥 مدیریت کاربران\n"
                        help_text += "`/helpstats` - 📊 آمار و گزارش\n\n"
                        help_text += "**کامندهای اساسی:**\n"
                        help_text += "`/status` - وضعیت سیستم\n"
                        help_text += "`/restart` - ری‌استارت\n"
                        help_text += "`/settings` - تنظیمات کلی\n\n"
                        help_text += "💡 **شروع:** با `/status` وضعیت سیستم را بررسی کنید"
                        
                    except FileNotFoundError:
                        # Fallback اگر فایل راهنما موجود نباشد
                        help_text = """📚 **راهنمای سیستم**

**دسترسی سریع:**
`/helpemoji` - 🚫 ایموجی‌ها
`/helpword` - 📝 کلمات
`/helpdelay` - ⏱️ تاخیر  
`/helpuser` - 👥 کاربران
`/helpstats` - 📊 آمار

**اساسی:** `/status` `/restart` `/settings`"""
                    
                    await message.reply_text(help_text)
                except Exception as e:
                    await message.reply_text(f"❌ خطا در نمایش راهنما: {str(e)}")

            def load_help_guide(self, guide_file, section_title, section_emoji):
                """بارگذاری و فرمت کردن راهنمای مختصر از فایل کامل"""
                try:
                    with open(f'guides/{guide_file}', 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # استخراج بخش‌های کلیدی
                    lines = content.split('\n')
                    sections = {}
                    current_section = None
                    current_content = []
                    
                    for line in lines:
                        if line.startswith('## '):
                            if current_section and current_content:
                                sections[current_section] = '\n'.join(current_content)
                            current_section = line[3:].strip()
                            current_content = []
                        elif line.startswith('```bash') or line.startswith('```'):
                            continue
                        elif line.strip() and not line.startswith('#'):
                            if line.startswith('### '):
                                current_content.append(f"**{line[4:].strip()}**")
                            elif line.startswith('- ') or line.startswith('• '):
                                current_content.append(f"• {line[2:].strip()}")
                            elif line.strip().startswith('/'):
                                # کامندها
                                cmd_parts = line.strip().split(' ', 2)
                                cmd = cmd_parts[0]
                                desc = ' '.join(cmd_parts[1:]) if len(cmd_parts) > 1 else ""
                                current_content.append(f"`{cmd}` - {desc}")
                            elif not line.startswith('---'):
                                current_content.append(line.strip())
                    
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content)
                    
                    # ساخت متن خلاصه
                    help_text = f"{section_emoji} **{section_title}**\n\n"
                    
                    # اضافه کردن مهم‌ترین بخش‌ها
                    priority_sections = ['کامندهای اضافه کردن', 'کامندهای حذف', 'کامندهای مشاهده', 'تست و دیباگ']
                    
                    for section_name in priority_sections:
                        for key, value in sections.items():
                            if any(word in key for word in section_name.split()):
                                clean_lines = [line for line in value.split('\n') if line.strip() and len(line.strip()) > 3]
                                if clean_lines:
                                    help_text += f"**{key}:**\n"
                                    # محدود کردن به 5 مورد اول
                                    for line in clean_lines[:5]:
                                        if line.strip():
                                            help_text += f"{line}\n"
                                    help_text += "\n"
                                break
                    
                    help_text += f"💡 **راهنمای کامل:** فایل `guides/{guide_file}` را مطالعه کنید\n"
                    help_text += "🔙 **برگشت:** `/help`"
                    
                    return help_text
                
                except FileNotFoundError:
                    return f"{section_emoji} **{section_title}**\n\n❌ فایل راهنما موجود نیست\n🔙 برگشت: `/help`"
                except Exception as e:
                    return f"{section_emoji} **{section_title}**\n\n❌ خطا در بارگذاری: {str(e)}\n🔙 برگشت: `/help`"

            @app.on_message(filters.command("helpemoji") & admin_filter)
            async def help_emoji_command(client, message):
                """راهنمای کامل ایموجی‌های ممنوعه"""
                try:
                    help_text = self.load_help_guide('EMOJI_GUIDE.md', 'راهنمای ایموجی‌های ممنوعه', '🚫')
                    await message.reply_text(help_text)
                except Exception as e:
                    await message.reply_text(f"❌ خطا در نمایش راهنمای ایموجی: {str(e)}")

            @app.on_message(filters.command("helpword") & admin_filter)
            async def help_word_command(client, message):
                """راهنمای کامل کلمات ممنوعه"""
                try:
                    help_text = self.load_help_guide('WORD_GUIDE.md', 'راهنمای کلمات ممنوعه', '📝')
                    await message.reply_text(help_text)
                except Exception as e:
                    await message.reply_text(f"❌ خطا در نمایش راهنمای کلمات: {str(e)}")

            @app.on_message(filters.command("helpdelay") & admin_filter)
            async def help_delay_command(client, message):
                """راهنمای کامل سیستم تاخیر"""
                try:
                    # راهنمای ویژه تاخیر با تاکید بر رفع مشکل فاصله
                    help_text = """⏱️ **راهنمای سیستم تاخیر پیشرفته**

🎛️ **انواع تاخیر (۶ نوع):**
`/setdelay enemy_spam 2.5` - اسپم دشمنان
`/setdelay friend_reply 0.3` - پاسخ به دوستان
`/setdelay global_msg 0.5` - پیام‌های کلی
`/setdelay conversation 2.0` - گفتگوی خودکار
`/setdelay emoji_react 0.1` - واکنش ایموجی
`/setdelay burst_protect 3.0` - محافظت سیل

⚠️ **نحوه درست استفاده:**
✅ `/setdelay enemy_spam 2.5` (فاصله بین همه)
❌ `/setdelayenemy_spam 2.5` (بدون فاصله)
❌ `/setdelay enemy_spam2.5` (بدون فاصله از عدد)

🏠 **ضریب چت:**
`/chatdelay -1001234567890 0.5` - نصف تاخیر
`/chatdelay -1001234567890 2.0` - دو برابر

📊 **مدیریت:**
`/delayinfo` - نمایش تنظیمات
`/resetdelay` - بازنشانی همه

💡 **راهنمای کامل:** `guides/DELAY_GUIDE.md`
🔙 **برگشت:** `/help`"""
                    await message.reply_text(help_text)
                except Exception as e:
                    await message.reply_text(f"❌ خطا در نمایش راهنمای تاخیر: {str(e)}")

            @app.on_message(filters.command("helpuser") & admin_filter)
            async def help_user_command(client, message):
                """راهنمای کامل مدیریت کاربران"""
                try:
                    help_text = self.load_help_guide('USER_GUIDE.md', 'راهنمای مدیریت کاربران', '👥')
                    await message.reply_text(help_text)
                except Exception as e:
                    await message.reply_text(f"❌ خطا در نمایش راهنمای کاربران: {str(e)}")

            @app.on_message(filters.command("helpstats") & admin_filter)  
            async def help_stats_command(client, message):
                """راهنمای کامل آمار و گزارش‌گیری"""
                try:
                    help_text = self.load_help_guide('STATS_GUIDE.md', 'راهنمای آمار و گزارش‌گیری', '📊')
                    await message.reply_text(help_text)
                except Exception as e:
                    await message.reply_text(f"❌ خطا در نمایش راهنمای آمار: {str(e)}")

            # =================================================================
            # پایان کامندهای راهنما - End of Help Commands System
            # =================================================================
            
            return app
        
        except Exception as e:
            print(f"❌ خطا در ساخت بات {bot_id}: {str(e)}")
            return None
        
    def run_unified_bots(self):
        """اجرای همه بات‌ها به صورت همزمان"""
        try:
            import asyncio
            
            async def start_all_bots():
                apps = []
                print("🚀 شروع راه‌اندازی سیستم یکپارچه...")
                
                # ایجاد همه بات‌ها
                for bot_id in range(1, 10):
                    try:
                        # تنظیم پیکربندی برای هر بات با استفاده از فایل‌های موجود
                        config = {
                            'db_path': f'bots/bot{bot_id}/bot{bot_id}_data.db',
                            'session_name': f'bots/bot{bot_id}/my_bot{bot_id}',
                            'api_id': f'API_ID_BOT{bot_id}',
                            'api_hash': f'API_HASH_BOT{bot_id}'
                        }
                        
                        # بررسی وجود فایل session
                        import os
                        session_file = f'bots/bot{bot_id}/my_bot{bot_id}.session'
                        if os.path.exists(session_file):
                            print(f"📁 فایل session بات {bot_id} پیدا شد: {session_file}")
                            app = await self.create_bot(bot_id, config)
                            if app:
                                apps.append(app)
                                print(f"✅ بات {bot_id} با session موجود آماده شد")
                        else:
                            print(f"⚠️ فایل session بات {bot_id} پیدا نشد: {session_file}")
                            
                    except Exception as e:
                        print(f"❌ خطا در بات {bot_id}: {str(e)}")
                
                if not apps:
                    print("❌ هیچ باتی راه‌اندازی نشد!")
                    return
                    
                print(f"🎯 {len(apps)} بات با موفقیت راه‌اندازی شد")
                print("📡 در حال اتصال به تلگرام...")
                
                # اجرای همه بات‌ها
                from pyrogram import idle
                
                for app in apps:
                    await app.start()
                print("🟢 همه بات‌ها آنلاین شدند!")
                await idle()
            
            # اجرای async function
            asyncio.run(start_all_bots())
            
        except Exception as e:
            print(f"❌ خطای کلی: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("=" * 50)
    print("🎯 سیستم تلگرام پیشرفته - نسخه یکپارچه")
    print("=" * 50)
    
    launcher = UnifiedBotLauncher()
    launcher.run_unified_bots()
