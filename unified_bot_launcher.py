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
                'api_id': int(os.getenv('BOT1_API_ID', '23700094')),
                'api_hash': os.getenv('BOT1_API_HASH', "7cd6b0ba9c5b1a5f21b8b76f1e2b8e40"),
                'session_name': "bots/bot1/my_bot1",
                'db_path': "bots/bot1/bot1_data.db",
                'log_path': "bots/bot1/bot1.log",
                'admin_id': int(os.getenv('BOT1_ADMIN_ID', '7850529246')),
                'auto_reply_enabled': True
            },
            2: {
                'api_id': int(os.getenv('BOT2_API_ID', '29262538')),
                'api_hash': os.getenv('BOT2_API_HASH', "0417ebf26dbd92d3455d51595f2c923c"),
                'session_name': "bots/bot2/my_bot2",
                'db_path': "bots/bot2/bot2_data.db",
                'log_path': "bots/bot2/bot2.log",
                'admin_id': int(os.getenv('BOT2_ADMIN_ID', '7419698159')),
                'auto_reply_enabled': True
            },
            3: {
                'api_id': int(os.getenv('BOT3_API_ID', '21555907')),
                'api_hash': os.getenv('BOT3_API_HASH', "16f4e09d753bc4b182434d8e37f410cd"),
                'session_name': "bots/bot3/my_bot3",
                'db_path': "bots/bot3/bot3_data.db",
                'log_path': "bots/bot3/bot3.log",
                'admin_id': int(os.getenv('BOT3_ADMIN_ID', '7607882302')),
                'auto_reply_enabled': True
            },
            4: {
                'api_id': int(os.getenv('BOT4_API_ID', '15508294')),
                'api_hash': os.getenv('BOT4_API_HASH', "778e5cd56ffcf22c2d62aa963ce85a0c"),
                'session_name': "bots/bot4/my_bot4",
                'db_path': "bots/bot4/bot4_data.db",
                'log_path': "bots/bot4/bot4.log",
                'admin_id': int(os.getenv('BOT4_ADMIN_ID', '7739974888')),
                'auto_reply_enabled': True
            },
            5: {
                'api_id': int(os.getenv('BOT5_API_ID', '25101001')),  # API جدید پیش‌فرض برای بات 5
                'api_hash': os.getenv('BOT5_API_HASH', "unique_hash_for_bot5_placeholder"),
                'session_name': "bots/bot5/my_bot5",
                'db_path': "bots/bot5/bot5_data.db",
                'log_path': "bots/bot5/bot5.log",
                'admin_id': int(os.getenv('BOT5_ADMIN_ID', '7346058093')),
                'auto_reply_enabled': True
            },
            6: {
                'api_id': int(os.getenv('BOT6_API_ID', '25101002')),  # API جدید پیش‌فرض برای بات 6
                'api_hash': os.getenv('BOT6_API_HASH', "unique_hash_for_bot6_placeholder"),
                'session_name': "bots/bot6/my_bot6",
                'db_path': "bots/bot6/bot6_data.db",
                'log_path': "bots/bot6/bot6.log",
                'admin_id': int(os.getenv('BOT6_ADMIN_ID', '7927398744')),
                'auto_reply_enabled': True
            },
            7: {
                'api_id': int(os.getenv('BOT7_API_ID', '25101003')),  # API جدید پیش‌فرض برای بات 7
                'api_hash': os.getenv('BOT7_API_HASH', "unique_hash_for_bot7_placeholder"),
                'session_name': "bots/bot7/my_bot7",
                'db_path': "bots/bot7/bot7_data.db",
                'log_path': "bots/bot7/bot7.log",
                'admin_id': int(os.getenv('BOT7_ADMIN_ID', '8092847456')),
                'auto_reply_enabled': True
            },
            8: {
                'api_id': int(os.getenv('BOT8_API_ID', '25101004')),  # API جدید پیش‌فرض برای بات 8
                'api_hash': os.getenv('BOT8_API_HASH', "unique_hash_for_bot8_placeholder"),
                'session_name': "bots/bot8/my_bot8",
                'db_path': "bots/bot8/bot8_data.db",
                'log_path': "bots/bot8/bot8.log",
                'admin_id': int(os.getenv('BOT8_ADMIN_ID', '7220521953')),
                'auto_reply_enabled': True
            },
            9: {
                'api_id': int(os.getenv('BOT9_API_ID', '25101005')),  # API جدید پیش‌فرض برای بات 9
                'api_hash': os.getenv('BOT9_API_HASH', "unique_hash_for_bot9_placeholder"),
                'session_name': "bots/bot9/my_bot9",
                'db_path': "bots/bot9/bot9_data.db",
                'log_path': "bots/bot9/bot9.log",
                'admin_id': int(os.getenv('BOT9_ADMIN_ID', '7143723023')),  # ادمین اصلی بات 9
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

⚙️ **تنظیم تاخیر:**
• `/setdelay enemy_spam 2.5` - تاخیر اسپم دشمن
• `/setdelay friend_reply 0.3` - تاخیر پاسخ دوست
• `/setdelay emoji_react 0.05` - تاخیر واکنش ایموجی

🎯 **تاخیر چت:**
• `/chatdelay -1001234567890 0.5` - ضریب چت خاص
• `/chatdelay -1001234567890 2.0` - آهسته کردن چت

📊 **اطلاعات:**
• `/delayinfo` - نمایش همه تنظیمات
• `/delaytest` - تست سرعت سیستم

🔄 **بازنشانی:**
• `/resetdelay` - برگشت به پیش‌فرض

🎛️ **انواع تاخیر (۶ نوع):**
• `enemy_spam` - اسپم دشمنان (1.0s)
• `friend_reply` - پاسخ دوستان (0.3s)
• `global_msg` - پیام کلی (0.5s)
• `conversation` - گفتگو (2.0s)
• `emoji_react` - واکنش ایموجی (0.1s)
• `burst_protect` - محافظت سیل (3.0s)

🎯 **ضریب‌های چت:**
• `0.1` - فوری (۱۰% تاخیر)
• `0.5` - سریع (۵۰% تاخیر)
• `1.0` - عادی (۱۰۰% تاخیر)
• `2.0` - آهسته (۲۰۰% تاخیر)

🧠 **ویژگی‌های هوشمند:**
• تاخیر انطباقی (چت خلوت/پرفعالیت)
• کاهش تاخیر برای موارد اضطراری
• محدودیت‌های ایمن (0.01s - 30s)

🔙 برگشت: `/help`
                    """
                    await message.reply_text(help_text)
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("helpuser") & admin_filter)
            async def help_user_command(client, message):
                """راهنمای مدیریت کاربران"""
                try:
                    help_text = """
👥 **راهنمای مدیریت کاربران**

📋 **کامندهای اصلی:**

👨‍💼 **مدیریت ادمین:**
• `/addadmin @username` - اضافه ادمین
• `/deladmin @username` - حذف ادمین
• `/listadmin` - لیست ادمین‌ها

👨‍👩‍👧‍👦 **مدیریت دوستان:**
• `/addfriend @username` - اضافه دوست
• `/delfriend @username` - حذف دوست
• `/listfriends` - لیست دوستان

😈 **مدیریت دشمنان:**
• `/addenemy @username` - اضافه دشمن
• `/delenemy @username` - حذف دشمن
• `/listenemies` - لیست دشمنان

🔍 **بررسی کاربر:**
• `/checkuser @username` - وضعیت کاربر
• `/userinfo 123456789` - اطلاعات با ID

⚙️ **تنظیمات رفتار:**
• رفتار با دوستان: پاسخ سریع، احترام
• رفتار با دشمنان: اسپم، کامندهای ویژه
• رفتار با غریبه‌ها: حالت عادی

🎯 **کامندهای ویژه دشمنان:**
• `/catch` - فقط برای دشمنان
• `/grab` - فقط برای دشمنان
• `/guess` - فقط برای دشمنان
• `/arise` - فقط برای دشمنان
• `/take` - فقط برای دشمنان
• `/secure` - فقط برای دشمنان

💡 **نکات:**
• تشخیص خودکار نوع کاربر
• اعمال تاخیر مناسب
• محدودیت دسترسی
• لاگ تمام تغییرات

🔙 برگشت: `/help`
                    """
                    await message.reply_text(help_text)
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("helpstats") & admin_filter)
            async def help_stats_command(client, message):
                """راهنمای آمار و گزارش‌گیری"""
                try:
                    help_text = """
📊 **راهنمای آمار و گزارش‌گیری**

📋 **کامندهای اصلی:**

📈 **آمار کلی:**
• `/status` - وضعیت کلی سیستم
• `/botstats` - آمار همه بات‌ها
• `/chatstats` - آمار چت فعلی

🛡️ **آمار امنیتی:**
• `/securitystats` - آمار تشخیص‌ها
• `/detectstats` - آمار ایموجی/کلمات
• `/threatlevel` - سطح تهدید

⚡ **آمار عملکرد:**
• `/speedtest` - تست سرعت تشخیص
• `/performance` - آمار عملکرد
• `/responsetime` - زمان پاسخ‌گویی

📊 **گزارش‌های تفصیلی:**
• `/dailyreport` - گزارش روزانه
• `/weeklyreport` - گزارش هفتگی
• `/monthlyreport` - گزارش ماهانه

📋 **لاگ‌ها:**
• `/recentlogs` - لاگ‌های اخیر
• `/errorlogs` - لاگ خطاها
• `/actionlogs` - لاگ اعمال

🔧 **مانیتورینگ:**
• `/systemhealth` - سلامت سیستم
• `/memoryusage` - مصرف حافظه
• `/uptime` - مدت زمان فعالیت

📡 **ربات گزارش:**
• گزارش خودکار تغییرات
• اعلان‌های امنیتی
• هشدار خطاها

💾 **صادرات داده:**
• `/exportstats` - صادرات آمار
• `/backup` - پشتیبان‌گیری
• `/export logs` - صادرات لاگ‌ها

💡 **ویژگی‌ها:**
• آمار زنده (Real-time)
• نمودارهای تصویری
• تحلیل روند
• پیش‌بینی بار

🔙 برگشت: `/help`
                    """
                    await message.reply_text(help_text)
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("testhelp") & admin_filter)
            async def test_help_command(client, message):
                """تست سریع کامندهای راهنما"""
                try:
                    test_text = """
🧪 **تست کامندهای راهنما**

📚 **کامندهای اصلی:**
• `/help` - راهنمای کلی ✅
• `/helpemoji` - راهنمای ایموجی ✅
• `/helpword` - راهنمای کلمات ✅
• `/helpdelay` - راهنمای تاخیر ✅
• `/helpuser` - راهنمای کاربران ✅
• `/helpstats` - راهنمای آمار ✅

🎯 **کامندهای آزمایشی:**
• `/status` - وضعیت سیستم
• `/delayinfo` - اطلاعات تاخیر
• `/listemoji` - لیست ایموجی‌ها
• `/securitystats` - آمار امنیتی

✅ **همه کامندها فعال و آماده هستند!**

💡 **شروع کنید با:** `/help`
                    """
                    await message.reply_text(test_text)
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # =================================================================
            # کامندهای پیشرفته مدیریت کلمات ممنوعه - Enhanced Forbidden Words Commands
            # =================================================================

            @app.on_message(filters.command("addword") & admin_filter)
            async def add_word_advanced_command(client, message):
                """اضافه کردن کلمه ممنوعه با ویژگی‌های پیشرفته"""
                try:
                    if len(message.command) < 2:
                        await message.reply_text(
                            "⚠️ استفاده: `/addword [کلمه] [توضیحات]`\n"
                            "گزینه‌های پیشرفته: `/addwordadv`\n\n"
                            "مثال‌ها:\n"
                            "• `/addword test کلمه تست`\n"
                            "• `/addword character برای گیم‌ها`\n"
                            "• `/addword spawned کلمه بازی`"
                        )
                        return

                    parts = message.text.split(maxsplit=2)
                    word = parts[1] if len(parts) > 1 else ""
                    description = parts[2] if len(parts) > 2 else "اضافه شده توسط ادمین"

                    result = self.add_forbidden_word_advanced(
                        word, 
                        description, 
                        'custom',
                        case_sensitive=False,  # پیش‌فرض: حساس به کوچک/بزرگ نیست
                        partial_match=True,    # پیش‌فرض: تطبیق جزئی
                        added_by_user_id=message.from_user.id
                    )

                    if result:
                        await message.reply_text(
                            f"✅ **کلمه ممنوعه اضافه شد - همه بات‌ها:**\n\n"
                            f"🚫 کلمه: `{word}`\n"
                            f"📝 توضیحات: {description}\n"
                            f"🔍 تطبیق: جزئی (در هر جای متن)\n"
                            f"🔤 حساسیت: عدم تمایز کوچک/بزرگ\n"
                            f"👤 اضافه‌کننده: {message.from_user.first_name}\n"
                            f"🕐 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                            f"⚡ تشخیص در تمام ۹ بات فعال شد!"
                        )

                        # گزارش
                        if self.report_bot:
                            report_text = f"🚨 کلمه ممنوعه جدید: {word}\n"
                            report_text += f"📝 توضیحات: {description}\n"
                            report_text += f"👤 توسط: {message.from_user.first_name} ({message.from_user.id})"
                            await self.send_report_safely(report_text)
                    else:
                        await message.reply_text(f"⚠️ کلمه قبلاً موجود است یا خطایی رخ داد: `{word}`")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("addwordadv") & admin_filter)
            async def add_word_advanced_options_command(client, message):
                """اضافه کردن کلمه ممنوعه با گزینه‌های کامل"""
                try:
                    if len(message.command) < 4:
                        await message.reply_text(
                            "⚠️ استفاده: `/addwordadv [کلمه] [exact|partial] [sensitive|insensitive] [توضیحات]`\n\n"
                            "مثال‌ها:\n"
                            "• `/addwordadv CHARACTER exact sensitive کلمه کامل`\n"
                            "• `/addwordadv test partial insensitive کلمه جزئی`\n\n"
                            "**گزینه‌ها:**\n"
                            "• `exact`: فقط کلمه کامل\n"
                            "• `partial`: در هر جای متن\n"
                            "• `sensitive`: حساس به کوچک/بزرگ\n"
                            "• `insensitive`: عدم حساسیت به کوچک/بزرگ"
                        )
                        return

                    parts = message.text.split(maxsplit=4)
                    word = parts[1]
                    match_type = parts[2].lower()
                    case_type = parts[3].lower()
                    description = parts[4] if len(parts) > 4 else f"کلمه {match_type} {case_type}"

                    partial_match = match_type == "partial"
                    case_sensitive = case_type == "sensitive"

                    result = self.add_forbidden_word_advanced(
                        word, 
                        description, 
                        'advanced',
                        case_sensitive=case_sensitive,
                        partial_match=partial_match,
                        added_by_user_id=message.from_user.id
                    )

                    if result:
                        match_desc = "جزئی (در هر جای متن)" if partial_match else "دقیق (کلمه کامل)"
                        case_desc = "حساس به کوچک/بزرگ" if case_sensitive else "عدم تمایز کوچک/بزرگ"

                        await message.reply_text(
                            f"✅ **کلمه ممنوعه پیشرفته اضافه شد:**\n\n"
                            f"🚫 کلمه: `{word}`\n"
                            f"📝 توضیحات: {description}\n"
                            f"🔍 نوع تطبیق: {match_desc}\n"
                            f"🔤 حساسیت: {case_desc}\n"
                            f"👤 اضافه‌کننده: {message.from_user.first_name}\n"
                            f"🕐 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                    else:
                        await message.reply_text(f"⚠️ خطا در اضافه کردن کلمه: `{word}`")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("delword") & admin_filter)
            async def del_word_advanced_command(client, message):
                """حذف کلمه ممنوعه با تأیید"""
                try:
                    parts = message.text.split(None, 1)
                    if len(parts) < 2:
                        await message.reply_text("❌ **استفاده صحیح:** `/delword [کلمه]`\nمثال: `/delword character`")
                        return

                    word = parts[1]
                    result, msg = self.remove_forbidden_word_advanced(word, message.from_user.id)

                    if result:
                        await message.reply_text(
                            f"✅ **کلمه ممنوعه حذف شد - همه بات‌ها:**\n\n"
                            f"🗑️ کلمه: `{word}`\n"
                            f"👤 حذف‌کننده: {message.from_user.first_name}\n"
                            f"🕐 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                            f"⚡ تشخیص از تمام ۹ بات حذف شد!"
                        )

                        # گزارش
                        if self.report_bot:
                            report_text = f"🗑️ کلمه ممنوعه حذف شد: {word}\n"
                            report_text += f"👤 توسط: {message.from_user.first_name} ({message.from_user.id})"
                            await self.send_report_safely(report_text)
                    else:
                        await message.reply_text(f"⚠️ {msg}")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("listword") & admin_filter)
            async def list_word_advanced_command(client, message):
                """لیست پیشرفته کلمات ممنوعه"""
                try:
                    word_list = self.list_forbidden_words_advanced()

                    if not word_list:
                        await message.reply_text(
                            "📝 **لیست کلمات ممنوعه خالی است**\n\n"
                            "💡 با `/addword [کلمه]` کلمه اضافه کنید.\n"
                            "⚙️ پیشرفته: `/addwordadv [کلمه] [exact|partial] [sensitive|insensitive]`\n"
                            "📚 کامندهای مفید:\n"
                            "• `/addemoji [ایموجی]` - اضافه کردن ایموجی ممنوعه\n"
                            "• `/securitystats` - آمار امنیتی"
                        )
                        return

                    text = "🚫 **لیست کلمات ممنوعه (همه بات‌ها):**\n\n"

                    for i, word_data in enumerate(word_list[:12], 1):
                        match_type = "دقیق" if not word_data['partial_match'] else "جزئی"
                        case_type = "حساس" if word_data['case_sensitive'] else "عادی"

                        text += f"`{i}.` **{word_data['word']}** ({match_type}, {case_type})"
                        if word_data['description'] and word_data['description'] != 'اضافه شده توسط ادمین':
                            text += f"\n    └ {word_data['description'][:35]}"
                        text += f"\n    └ دسته: {word_data['category']}\n\n"

                    if len(word_list) > 12:
                        text += f"... و {len(word_list) - 12} کلمه دیگر\n\n"

                    text += f"📊 **آمار:**\n"
                    text += f"• تعداد کل: {len(word_list)} کلمه\n"
                    text += f"• وضعیت تشخیص: {'✅ فعال' if self.security_settings['word_detection_enabled'] else '❌ غیرفعال'}\n"
                    text += f"• آخرین بروزرسانی: {datetime.now().strftime('%H:%M:%S')}\n\n"
                    text += f"💡 **راهنما:** `/testword [متن]` برای تست تشخیص"

                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("testword") & admin_filter)
            async def test_word_command(client, message):
                """تست تشخیص کلمات ممنوعه"""
                try:
                    parts = message.text.split(None, 1)
                    if len(parts) < 2:
                        await message.reply_text("❌ **استفاده صحیح:** `/testword [متن]`\nمثال: `/testword A CHARACTER HAS SPAWNED`")
                        return

                    test_text = parts[1]

                    # تست تشخیص با زمان‌سنجی
                    import time
                    start_time = time.time()
                    found_words = []
                    is_detected = self.contains_forbidden_word(test_text, found_words)
                    end_time = time.time()
                    detection_time = (end_time - start_time) * 1000  # میلی‌ثانیه

                    # نمایش جزئیات کامل
                    debug_text = f"🔍 **تست تشخیص کلمات ممنوعه:**\n\n"
                    debug_text += f"📝 متن تست: `{test_text}`\n"
                    debug_text += f"🎯 تشخیص داده شد: {'✅ بله' if is_detected else '❌ خیر'}\n"
                    debug_text += f"⏱️ زمان تشخیص: {detection_time:.2f}ms\n"

                    if found_words:
                        debug_text += f"⚡ کلمه یافت شده: `{found_words[0]}`\n"

                    debug_text += f"📊 تعداد کلمات ممنوعه: {len(self.forbidden_words)}\n"
                    debug_text += f"🔄 وضعیت cache: {len(self.detection_cache)} آیتم\n\n"

                    # نمایش تمام کلمات ممنوعه فعلی
                    if self.forbidden_words:
                        debug_text += "📋 **کلمات ممنوعه فعلی:**\n"
                        for i, word in enumerate(list(self.forbidden_words)[:8], 1):
                            debug_text += f"{i}. `{word}`\n"
                        if len(self.forbidden_words) > 8:
                            debug_text += f"... و {len(self.forbidden_words) - 8} مورد دیگر\n"

                    await message.reply_text(debug_text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("clearword") & admin_filter)
            async def clear_word_command(client, message):
                """حذف همه کلمات ممنوعه با تأیید"""
                try:
                    # دریافت تعداد کلمات قبل از حذف
                    count = len(self.forbidden_words)

                    if count == 0:
                        await message.reply_text("📝 لیست کلمات ممنوعه خالی است.")
                        return

                    # حذف از دیتابیس
                    db_path = self.bot_configs[1]['db_path']
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM forbidden_words")
                    conn.commit()
                    conn.close()

                    # حذف از حافظه
                    self.forbidden_words.clear()

                    await message.reply_text(
                        f"✅ **همه کلمات ممنوعه حذف شدند:**\n\n"
                        f"🗑️ تعداد حذف شده: {count} کلمه\n"
                        f"👤 حذف‌کننده: {message.from_user.first_name}\n"
                        f"🕐 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        f"⚡ تشخیص از تمام ۹ بات حذف شد!"
                    )

                    # گزارش
                    if self.report_bot:
                        report_text = f"🗑️ همه کلمات ممنوعه حذف شدند ({count} کلمه)\n"
                        report_text += f"👤 توسط: {message.from_user.first_name} ({message.from_user.id})"
                        await self.send_report_safely(report_text)

                    self.log_action(bot_id, "clear_words", message.from_user.id, f"حذف {count} کلمه")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("securitystats") & admin_filter)
            async def security_stats_command(client, message):
                """نمایش آمار کامل امنیتی"""
                try:
                    emoji_count = len(self.forbidden_emojis)
                    word_count = len(self.forbidden_words)

                    text = f"🛡️ **آمار کامل امنیتی (همه بات‌ها):**\n\n"

                    # آمار کلی
                    text += f"📊 **آمار کلی:**\n"
                    text += f"• ایموجی‌های ممنوعه: {emoji_count} عدد\n"
                    text += f"• کلمات ممنوعه: {word_count} عدد\n"
                    text += f"• مجموع: {emoji_count + word_count} مورد\n\n"

                    # وضعیت تشخیص
                    text += f"⚙️ **وضعیت تشخیص:**\n"
                    text += f"• ایموجی‌ها: {'✅ فعال' if self.security_settings['emoji_detection_enabled'] else '❌ غیرفعال'}\n"
                    text += f"• کلمات: {'✅ فعال' if self.security_settings['word_detection_enabled'] else '❌ غیرفعال'}\n"
                    text += f"• لاگ امنیتی: {'✅ فعال' if self.security_settings['log_detections'] else '❌ غیرفعال'}\n\n"

                    # آمار تشخیص
                    text += f"📈 **آمار تشخیص (این جلسه):**\n"
                    text += f"• تشخیص ایموجی: {self.security_stats['emoji_detections']} بار\n"
                    text += f"• تشخیص کلمه: {self.security_stats['word_detections']} بار\n"
                    text += f"• مجموع: {self.security_stats['emoji_detections'] + self.security_stats['word_detections']} بار\n\n"

                    # وضعیت کش
                    text += f"💾 **وضعیت کش:**\n"
                    text += f"• آیتم‌های کش: {len(self.detection_cache)} عدد\n"
                    text += f"• حد اکثر: {self.cache_max_size} عدد\n"
                    text += f"• مدت انقضا: {self.cache_expiry} ثانیه\n\n"

                    # آخرین بروزرسانی
                    text += f"🕐 **آخرین بروزرسانی:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

                    # کامندهای مفید
                    text += f"💡 **کامندهای مفید:**\n"
                    text += f"• `/listemoji` - لیست ایموجی‌ها\n"
                    text += f"• `/listword` - لیست کلمات\n"
                    text += f"• `/testemoji [ایموجی]` - تست ایموجی\n"
                    text += f"• `/testword [متن]` - تست کلمه"

                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("spamstatus") & admin_filter)
            async def spam_status_command(client, message):
                try:
                    if not self.continuous_spam_tasks:
                        await message.reply_text("✅ **هیچ فحش نامحدودی در حال اجرا نیست**")
                        return

                    text = f"🔥 **فحش‌های نامحدود فعال:**\n\n"

                    for i, (spam_key, task) in enumerate(self.continuous_spam_tasks.items(), 1):
                        bot_id, user_id, chat_id = spam_key.split('_')

                        try:
                            chat_info = await client.get_chat(int(chat_id))
                            chat_name = chat_info.title or f"چت {chat_id}"
                        except:
                            chat_name = f"چت {chat_id}"

                        text += f"`{i}.` بات {bot_id} → دشمن `{user_id}`\n"
                        text += f"    └ در: {chat_name}\n"
                        text += f"    └ وضعیت: {'✅ فعال' if not task.done() else '❌ متوقف'}\n\n"

                        if i >= 10:  # محدود به 10 مورد
                            text += f"... و {len(self.continuous_spam_tasks) - 10} مورد دیگر\n"
                            break

                    text += f"\n📊 **تعداد کل:** {len(self.continuous_spam_tasks)} فحش نامحدود فعال"
                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("stopspam") & admin_filter)
            async def stop_spam_command(client, message):
                try:
                    if len(message.command) < 2:
                        await message.reply_text("⚠️ استفاده: `/stopspam [bot_id]` یا `/stopspam all`\nمثال: `/stopspam 1` یا `/stopspam all`")
                        return

                    target = message.command[1].lower()
                    stopped_count = 0

                    if target == "all":
                        # متوقف کردن همه فحش‌های نامحدود
                        for spam_key, task in list(self.continuous_spam_tasks.items()):
                            try:
                                task.cancel()
                                stopped_count += 1
                            except:
                                pass
                        self.continuous_spam_tasks.clear()

                        await message.reply_text(f"🛑 **همه فحش‌های نامحدود متوقف شدند**\n📊 تعداد متوقف شده: {stopped_count}")

                    else:
                        try:
                            target_bot_id = int(target)

                            # متوقف کردن فحش‌های مربوط به بات مشخص
                            keys_to_remove = []
                            for spam_key, task in self.continuous_spam_tasks.items():
                                bot_id, user_id, chat_id = spam_key.split('_')
                                if int(bot_id) == target_bot_id:
                                    try:
                                        task.cancel()
                                        keys_to_remove.append(spam_key)
                                        stopped_count += 1
                                    except:
                                        pass

                            for key in keys_to_remove:
                                del self.continuous_spam_tasks[key]

                            if stopped_count > 0:
                                await message.reply_text(f"🛑 **فحش‌های نامحدود بات {target_bot_id} متوقف شدند**\n📊 تعداد متوقف شده: {stopped_count}")
                            else:
                                await message.reply_text(f"ℹ️ هیچ فحش نامحدودی برای بات {target_bot_id} یافت نشد")

                        except ValueError:
                            await message.reply_text("❌ شماره بات نامعتبر")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # کامندهای تنظیم تاخیر فحش
            @app.on_message(filters.command("setdelay") & admin_filter)
            async def set_delay_command(client, message):
                try:
                    if len(message.command) < 2:
                        await message.reply_text("⚠️ استفاده: /setdelay [ثانیه]\nمثال: /setdelay 2.5")
                        return

                    delay_str = message.command[1]
                    success, msg = self.set_spam_delay(bot_id, delay_str)

                    if success:
                        await message.reply_text(f"✅ {msg}")
                        self.log_action(bot_id, "set_delay", message.from_user.id, f"تاخیر: {delay_str} ثانیه")
                    else:
                        await message.reply_text(f"❌ {msg}")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("getdelay") & admin_filter)
            async def get_delay_command(client, message):
                try:
                    current_delay = self.get_spam_delay(bot_id)
                    await message.reply_text(f"⏱️ **تاخیر فعلی فحش بات {bot_id}:**\n\n🕒 {current_delay} ثانیه\n🌐 تاخیر عمومی: {self.min_global_delay} ثانیه\n\n💡 برای تغییر از `/setdelay [ثانیه]` استفاده کنید")
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("setglobaldelay") & admin_filter)
            async def set_global_delay_command(client, message):
                try:
                    user_id = message.from_user.id
                    if not self.is_launcher_admin(user_id):
                        await message.reply_text("🚫 این کامند فقط برای ادمین اصلی لانچر است")
                        return

                    if len(message.command) < 2:
                        await message.reply_text("⚠️ استفاده: /setglobaldelay [ثانیه]\nمثال: /setglobaldelay 1.0")
                        return

                    try:
                        delay_seconds = float(message.command[1])
                        if delay_seconds < 0:
                            await message.reply_text("❌ تاخیر نمی‌تواند منفی باشد")
                            return

                        self.min_global_delay = delay_seconds
                        await message.reply_text(f"✅ تاخیر عمومی تنظیم شد: {delay_seconds} ثانیه\n\n📝 این تاخیر بین پیام‌های همه بات‌ها در هر چت اعمال می‌شود\n💡 حالا می‌توانید هر عددی از 0 به بالا تنظیم کنید")

                    except ValueError:
                        await message.reply_text("❌ لطفاً عدد معتبر وارد کنید")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("ratelimit") & admin_filter)
            async def rate_limit_status_command(client, message):
                try:
                    active_chats = len(self.last_message_time)
                    active_locks = len(self.chat_locks)
                    emergency_active = self.emergency_stop_event.is_set()

                    text = f"📊 **وضعیت Rate Limiting:**\n\n"
                    text += f"🌐 تاخیر عمومی: {self.min_global_delay} ثانیه\n"
                    text += f"💬 چت‌های فعال: {active_chats}\n"
                    text += f"🔒 Lock های فعال: {active_locks}\n"
                    text += f"🔥 تسک‌های فحش فعال: {len(self.continuous_spam_tasks)}\n"
                    text += f"🚨 توقف اضطراری: {'فعال' if emergency_active else 'غیرفعال'}\n\n"
                    text += f"📝 سیستم rate limiting جلوگیری از ارسال همزمان پیام‌ها توسط بات‌های مختلف را می‌کند"

                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("clearstop") & admin_filter)
            async def clear_emergency_stop_command(client, message):
                try:
                    user_id = message.from_user.id
                    if not self.is_launcher_admin(user_id):
                        await message.reply_text("🚫 این کامند فقط برای ادمین اصلی لانچر است")
                        return

                    if self.emergency_stop_event.is_set():
                        self.clear_emergency_stop()
                        await message.reply_text("✅ حالت توقف اضطراری پاک شد\n\n💡 بات‌ها می‌توانند مجدداً شروع به کار کنند")
                    else:
                        await message.reply_text("ℹ️ هیچ توقف اضطراری فعالی وجود ندارد")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            @app.on_message(filters.command("stopstatus") & admin_filter)
            async def stop_status_command(client, message):
                try:
                    emergency_active = self.emergency_stop_event.is_set()
                    last_detection = self.last_emoji_detection_time

                    text = f"🛑 **وضعیت سیستم توقف:**\n\n"
                    text += f"🚨 توقف اضطراری: {'🔴 فعال' if emergency_active else '🟢 غیرفعال'}\n"
                    text += f"🔥 تسک‌های فحش فعال: {len(self.continuous_spam_tasks)}\n"

                    if last_detection > 0:
                        import datetime
                        detection_time = datetime.datetime.fromtimestamp(last_detection)
                        text += f"⏰ آخرین تشخیص: {detection_time.strftime('%H:%M:%S')}\n"

                    text += f"\n📝 ایموجی‌های ممنوعه فعال: {len(self.forbidden_emojis)}"

                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # راهنما
            @app.on_message(filters.command("help") & admin_filter)
            async def help_command(client, message):
                try:
                    user_id = message.from_user.id
                    is_launcher = self.is_launcher_admin(user_id)
                    accessible_bots = self.get_accessible_bots(user_id)

                    help_text = f"""🤖 **راهنمای جامع سیستم ۹ بات هوشمند - بات {bot_id}**

👤 **دسترسی شما:**
{'👑 ادمین اصلی لانچر - کنترل همه بات‌ها' if is_launcher else f'🔧 ادمین بات شخصی - کنترل بات‌های: {accessible_bots}'}

🔥 **سیستم فحش نامحدود:**
• فحش خودکار و مداوم به دشمنان تا دریافت ایموجی توقف
• توقف هوشمند با ایموجی‌های ممنوعه (قابل تنظیم ۱۰۰٪ از تلگرام)
• مانیتورینگ real-time تعداد فحش‌های ارسالی"""

                    # اضافه کردن توضیح اکو برای بات 3
                    if bot_id == 3:
                        help_text += f"""

🔊 **قابلیت اکو (ویژه بات {bot_id}):**
• `/echo` - اکو کردن پیام (فقط برای دشمنان)
  └ با ریپلای: پیام ریپلای شده را اکو می‌کند
  └ بدون ریپلای: خود پیام کامند را اکو می‌کند
  └ تمام انواع رسانه پشتیبانی می‌شود"""

                    text = help_text + f"""

🔥 **مدیریت فحش‌ها:**
• `/addfosh [متن/رسانه]` - اضافه کردن فحش جدید
• `/delfosh [متن]` - حذف فحش مشخص
• `/listfosh` - نمایش تمام فحش‌های بات {bot_id}
• `/clearfosh` - حذف همه فحش‌ها
• `/startfosh` - شروع فحش نامحدود (ریپلای روی دشمن)
• `/stopfosh` - توقف فوری فحش نامحدود

👹 **مدیریت دشمنان:**
• `/setenemy` - اضافه کردن دشمن (ریپلای)
• `/delenemy` - حذف دشمن (ریپلای)
• `/listenemy` - نمایش لیست دشمنان
• `/clearenemy` - حذف همه دشمنان

😊 **مدیریت دوستان:**
• `/setfriend` - اضافه کردن دوست (ریپلای)
• `/delfriend` - حذف دوست (ریپلای)
• `/listfriend` - نمایش لیست دوستان
• `/clearfriend` - حذف همه دوستان

💬 **کلمات دوستانه:**
• `/addword [متن/رسانه]` - اضافه کردن کلمه دوستانه
• `/delword [متن]` - حذف کلمه دوستانه
• `/listword` - نمایش لیست کلمات
• `/clearword` - حذف همه کلمات

🔧 **تنظیمات:**
• `/autoreply` - فعال/غیرفعال پاسخگویی خودکار
• `/stats` - نمایش آمار کامل بات {bot_id}
• `/broadcast [پیام]` - ارسال همگانی
• `/pause` - توقف موقت همه بات‌ها
• `/resume` - ادامه کار همه بات‌ها

🛑 **ایموجی‌های توقف:**
⭐ هیچ ایموجی پیش‌فرضی - کاملاً قابل تنظیم از تلگرام ⭐

هنگام دیدن این ایموجی‌ها، تمام بات‌ها متوقف می‌شوند.

📊 **وضعیت سیستم:**
• ۹ بات همزمان فعال
• فحش نامحدود تا دریافت ایموجی توقف
• مدیریت خودکار flood wait
• آمارگیری لحظه‌ای

💡 **نکات مهم:**
• فحش نامحدود خودکار با تشخیص دشمن شروع می‌شود
• سیستم توقف هوشمند برای جلوگیری از مشکل
• همه کامندها فقط برای ادمین‌ها
• پشتیبانی کامل از انواع رسانه

💡 **نکات مهم:**
• فحش نامحدود خودکار با تشخیص دشمن شروع می‌شود
• سیستم توقف هوشمند برای جلوگیری از مشکل
• همه کامندها فقط برای ادمین‌ها
• پشتیبانی کامل از انواع رسانه

🔗 **دستورات اضافی:**
• `/help` - راهنمای اصلی
• `/help2` - راهنمای پیشرفته و ویژگی‌های خاص
• `/stats` - آمار کامل سیستم"""

                    # اضافه کردن کامندهای ویژه ادمین اصلی لانچر
                    if is_launcher:
                        text += f"""

👑 **کامندهای ویژه ادمین اصلی لانچر:**
• `/launcherstatus` - نمایش وضعیت کامل همه بات‌ها
• `/restartbot [شماره]` - راه‌اندازی مجدد بات مشخص
• `/manageall autoreply [on|off]` - کنترل پاسخگویی همه بات‌ها
• `/testadmin` - بررسی دسترسی و نوع ادمین

🎯 **دسترسی شما:** کنترل کامل همه ۹ بات
⚠️ **توجه:** این کامندها فقط برای شما قابل استفاده هستند"""

                    text += """

💡 **نکات مهم:**
• هر ادمین فقط بات خودش را کنترل می‌کند
• ادمین اصلی لانچر همه بات‌ها را کنترل می‌کند
• فحش نامحدود خودکار با تشخیص دشمن شروع می‌شود
• سیستم توقف هوشمند برای جلوگیری از مشکل"""

                    await message.reply_text(text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # راهنمای پیشرفته (بخش دوم)
            @app.on_message(filters.command("help2") & admin_filter)
            async def help2_command(client, message):
                try:
                    user_id = message.from_user.id
                    is_launcher = self.is_launcher_admin(user_id)
                    accessible_bots = self.get_accessible_bots(user_id)

                    help2_text = f"""🔧 **راهنمای پیشرفته - بات {bot_id}**

👤 **دسترسی شما:**
{'👑 ادمین اصلی لانچر - کنترل همه بات‌ها' if is_launcher else f'🔧 ادمین بات شخصی - کنترل بات‌های: {accessible_bots}'}

🔥 **مدیریت سیستم فحش‌ها:**
• `/addfosh [متن/رسانه]` - اضافه کردن فحش جدید (متن یا ریپلای رسانه)
  └ پشتیبانی: متن، عکس، ویدیو، گیف، استیکر، صوت
• `/delfosh [متن]` - حذف فحش مشخص از دیتابیس
• `/listfosh` - نمایش کامل فحش‌ها با صفحه‌بندی خودکار
• `/clearfosh` - حذف کلی تمام فحش‌ها (غیرقابل بازگشت)

📢 **سیستم ارسال همگانی:**
• `/broadcast [پیام]` - ارسال همگانی متن به تمام گروه‌ها
• پشتیبانی از ارسال رسانه با ریپلای در broadcast

🤖 **تنظیمات سیستم:**
• `/autoreply` - فعال کردن پاسخگویی خودکار
• `/offself` - غیرفعال کردن پاسخگویی
• `/start` - راه‌اندازی مجدد ربات

⏸️ **کنترل هوشمند اسپم:**
• `/pausestatus` - نمایش وضعیت توقف اسپم در چت‌ها
• `/resumespam [chat_id]` - ازسرگیری دستی اسپم در چت مشخص

🛑 **توقف خودکار اسپم:**
• ایموجی‌های توقف: کاملاً قابل تنظیم از طریق کامندهای تلگرام
• کامندهای ممنوعه (فقط دشمن): /catch /grab /guess /arise /take /secure

🚫 **مدیریت ایموجی‌های ممنوعه:**
• `/addemoji [ایموجی]` - اضافه کردن ایموجی جدید به لیست ممنوعه
• `/delemoji [ایموجی]` - حذف ایموجی از لیست ممنوعه
• `/listemoji` - نمایش تمام ایموجی‌های ممنوعه

🔥 **مدیریت فحش نامحدود:**
• `/spamstatus` - نمایش وضعیت فحش‌های نامحدود فعال
• `/stopspam [bot_id|all]` - متوقف کردن فحش‌های نامحدود
  └ مثال: `/stopspam 1` یا `/stopspam all`

⏱️ **تنظیمات تاخیر فحش:**
• `/setdelay [ثانیه]` - تنظیم تاخیر بین فحش‌ها
  └ مثال: `/setdelay 2.5` (2.5 ثانیه تاخیر)
  └ مثال: `/setdelay 0.1` (0.1 ثانیه تاخیر)
• `/getdelay` - نمایش تاخیر فعلی فحش

⚡ **ویژگی‌های جدید:**
• فحش نامحدود به دشمنان تا ایموجی ممنوعه فرستاده شود
• سیستم کامندهای ممنوعه مخصوص دشمنان
• مدیریت قابل تنظیم ایموجی‌های ممنوعه
• کامندهای توقف: `/catch` `/grab` `/guess` `/take` `/arise`
└ اسپم تا پیام بعدی دشمن متوقف می‌شود"""

                    # اضافه کردن کامندهای ویژه ادمین اصلی لانچر برای help2
                    if is_launcher:
                        help2_text += f"""

👑 **کامندهای ویژه ادمین اصلی لانچر:**
• `/launcherstatus` - نمایش وضعیت کامل همه بات‌ها
• `/restartbot [شماره]` - راه‌اندازی مجدد بات مشخص
• `/manageall autoreply [on|off]` - کنترل پاسخگویی همه بات‌ها
• `/testadmin` - بررسی دسترسی و نوع ادمین

🗣️ **گفتگوی خودکار ربات‌ها (ویژگی جدید):**
• `/startchat` - شروع گفتگوی خودکار بین ۹ ربات
• `/stopchat` - توقف گفتگوی خودکار
• `/chatstatus` - وضعیت گفتگوی خودکار و آمار
• `/setoffline [شماره]` - آفلاین کردن ربات‌ها
  └ مثال: `/setoffline 1` یا `/setoffline 1-5`

🎯 **دسترسی شما:** کنترل کامل همه ۹ بات
⚠️ **توجه:** این کامندها فقط برای شما قابل استفاده هستند"""

                    help2_text += """

💡 **نکات پیشرفته:**
• هر ادمین فقط بات خودش را کنترل می‌کند
• ادمین اصلی لانچر همه بات‌ها را کنترل می‌کند
• فحش نامحدود خودکار با تشخیص دشمن شروع می‌شود
• سیستم توقف هوشمند برای جلوگیری از مشکل

🔗 **دستورات راهنما:**
• `/help` - راهنمای اصلی
• `/help2` - این راهنمای پیشرفته
• `/stats` - آمار کامل سیستم"""

                    await message.reply_text(help2_text)

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {str(e)}")

            # دستورات مدیریتی ویژه ادمین اصلی لانچر
            @app.on_message(filters.command("launcherstatus") & admin_filter)
            async def launcher_status_command(client, message):
                try:
                    user_id = message.from_user.id
                    if not self.is_launcher_admin(user_id):
                        await message.reply_text("🚫 این کامند فقط برای ادمین اصلی لانچر است")
                        return

                    status = self.get_status()
                    status_text = f"""
👑 **وضعیت لانچر واحد - ادمین اصلی:**

🤖 تعداد کل بات‌ها: {status['total_bots']}
✅ بات‌های فعال: {status['running_bots']}
❌ بات‌های خطا: {status['error_bots']}

📋 **جزئیات بات‌ها:**
"""

                    for bot_info in status['bots']:
                        emoji = "✅" if bot_info['status'] == 'running' else "❌"
                        bot_admin = self.bot_configs.get(bot_info['id'], {}).get('admin_id', 'Unknown')
                        status_text += f"{emoji} بات {bot_info['id']}: {bot_info['status']} (Admin: {bot_admin})\n"

                    await message.reply_text(status_text.strip())

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {e}")

            @app.on_message(filters.command("restartbot") & admin_filter)
            async def restart_bot_command(client, message):
                try:
                    user_id = message.from_user.id

                    if len(message.command) < 2:
                        await message.reply_text("⚠️ استفاده: /restartbot [شماره_بات]\nمثال: /restartbot 2")
                        return

                    target_bot_id = int(message.command[1])
                    if target_bot_id not in self.bot_configs:
                        await message.reply_text(f"❌ بات {target_bot_id} یافت نشد")
                        return

                    # بررسی دسترسی
                    if not self.can_control_bot(user_id, target_bot_id):
                        await message.reply_text(f"🚫 شما مجاز به راه‌اندازی مجدد بات {target_bot_id} نیستید")
                        return

                    await message.reply_text(f"🔄 راه‌اندازی مجدد بات {target_bot_id}...")

                    success = await self.restart_bot(target_bot_id)
                    if success:
                        await message.reply_text(f"✅ بات {target_bot_id} مجدداً راه‌اندازی شد")
                    else:
                        await message.reply_text(f"❌ خطا در راه‌اندازی مجدد بات {target_bot_id}")

                except ValueError:
                    await message.reply_text("❌ شماره بات نامعتبر")
                except Exception as e:
                    await message.reply_text(f"❌ خطا: {e}")

            # کامند جدید برای مدیریت کردن همه بات‌ها (فقط ادمین اصلی)
            @app.on_message(filters.command("manageall") & admin_filter)
            async def manage_all_bots_command(client, message):
                try:
                    user_id = message.from_user.id
                    if not self.is_launcher_admin(user_id):
                        await message.reply_text("🚫 این کامند فقط برای ادمین اصلی لانچر است")
                        return

                    if len(message.command) < 3:
                        await message.reply_text("⚠️ استفاده: /manageall [کامند] [پارامتر]\nمثال: /manageall autoreply on")
                        return

                    command = message.command[1].lower()
                    parameter = message.command[2].lower()

                    if command == "autoreply":
                        enabled = parameter == "on"
                        for bot_id in self.bot_configs.keys():
                            self.bot_configs[bot_id]['auto_reply_enabled'] = enabled

                        status = "فعال" if enabled else "غیرفعال" 
                        await message.reply_text(f"✅ پاسخگویی خودکار همه بات‌ها {status} شد")

                    elif command == "webpanel":
                        if parameter == "restart":
                            await self.stop_web_panel()
                            await asyncio.sleep(2)
                            web_success = await self.start_web_panel()
                            if web_success:
                                await message.reply_text("✅ پنل وب مجدداً راه‌اندازی شد")
                            else:
                                await message.reply_text("❌ خطا در راه‌اندازی مجدد پنل وب")
                        elif parameter == "status":
                            if self.web_process and self.web_process.poll() is None:
                                await message.reply_text("✅ پنل وب فعال - http://localhost:5000")
                            else:
                                await message.reply_text("❌ پنل وب غیرفعال")
                        else:
                            await message.reply_text("❌ پارامتر نامعتبر. کامندهای موجود: autoreply, webpanel")

                    else:
                        await message.reply_text("❌ کامند نامعتبر. کامندهای موجود: autoreply, webpanel")

                except Exception as e:
                    await message.reply_text(f"❌ خطا: {e}")

            # **بررسی ایموجی ممنوعه برای ادمین‌ها (اولویت بالا - بدون استثنا)**
            @app.on_message(
                ~filters.me & 
                ~filters.channel & 
                admin_filter &
                ~filters.service &
                filters.group
            )
            async def admin_emoji_security_handler(client, message):
                """تشخیص ایموجی ممنوعه برای ادمین‌ها - هیچ استثنایی نیست"""
                chat_id = message.chat.id

                # **بررسی ایموجی/کامند ممنوعه حتی برای ادمین‌ها - هیچ استثنایی نیست**
                if await self.should_pause_spam(message, bot_id):
                    # دریافت اطلاعات ادمین
                    user_id = message.from_user.id if message.from_user else 0
                    sender_name = message.from_user.first_name if message.from_user else "نامشخص"
                    sender_username = message.from_user.username if message.from_user else "نامشخص"
                    sender_detail = f"{sender_name} (@{sender_username})" if sender_username else f"{sender_name}"

                    logger.warning(f"🚨 SECURITY ALERT - بات {bot_id} - ایموجی ممنوعه توسط ADMIN تشخیص داده شد در چت {chat_id}")
                    logger.warning(f"   └ توسط: ADMIN - {sender_detail} (ID: {user_id})")
                    logger.warning(f"   └ ⚠️ حتی ادمین‌ها هم می‌توانند سیستم را متوقف کنند - هیچ استثنایی نیست")

                    # نمایش محتوای پیام با بررسی امنیت
                    message_content = message.text or message.caption or "[بدون متن]"
                    if len(message_content) > 100:
                        message_content = message_content[:100] + "..."
                    logger.warning(f"   └ محتوای پیام ADMIN: {message_content}")

                    # **توقف کلی همه بات‌ها در این چت - حتی اگر ادمین باشد**
                    self.global_paused[chat_id] = user_id
                    logger.warning(f"🛑 همه بات‌ها در چت {chat_id} توسط ADMIN متوقف شدند - امنیت مطلق")

                    # لاگ عملیات در دیتابیس با اولویت بالا
                    chat_title = message.chat.title if message.chat.title else f"چت {chat_id}"
                    self.log_action(bot_id, "admin_security_pause", user_id, f"توقف امنیتی توسط ADMIN {sender_detail} در {chat_title}")

                    # **هیچ استثنایی برای ادمین‌ها - سیستم متوقف می‌شود**
                    return

            # **بررسی ایموجی ممنوعه برای ادمین‌ها در چت‌های خصوصی نیز**
            @app.on_message(
                ~filters.me & 
                admin_filter &
                ~filters.service &
                filters.private
            )
            async def admin_private_emoji_security_handler(client, message):
                """تشخیص ایموجی ممنوعه برای ادمین‌ها در چت‌های خصوصی - هیچ استثنایی نیست"""
                chat_id = message.chat.id

                # **بررسی ایموجی/کامند ممنوعه حتی برای ادمین‌ها در خصوصی**
                if await self.should_pause_spam(message, bot_id):
                    # دریافت اطلاعات ادمین
                    user_id = message.from_user.id if message.from_user else 0
                    sender_name = message.from_user.first_name if message.from_user else "نامشخص"
                    sender_username = message.from_user.username if message.from_user else "نامشخص"
                    sender_detail = f"{sender_name} (@{sender_username})" if sender_username else f"{sender_name}"

                    logger.warning(f"🚨 SECURITY ALERT PRIVATE - بات {bot_id} - ایموجی ممنوعه توسط ADMIN در چت خصوصی تشخیص داده شد")
                    logger.warning(f"   └ توسط: ADMIN - {sender_detail} (ID: {user_id})")
                    logger.warning(f"   └ ⚠️ حتی در چت‌های خصوصی ادمین‌ها استثنا ندارند")

                    # نمایش محتوای پیام
                    message_content = message.text or message.caption or "[بدون متن]"
                    if len(message_content) > 100:
                        message_content = message_content[:100] + "..."
                    logger.warning(f"   └ محتوای پیام ADMIN (خصوصی): {message_content}")

                    # لاگ عملیات امنیتی
                    self.log_action(bot_id, "admin_private_security_pause", user_id, f"توقف امنیتی ADMIN در چت خصوصی: {sender_detail}")

                    # **هیچ استثنایی - حتی در خصوصی**
                    return

            # پاسخگویی خودکار
            @app.on_message(
                ~filters.me & 
                ~filters.channel & 
                ~admin_filter &
                ~filters.service &
                filters.group
            )
            async def auto_reply_handler(client, message):
                """هندلر پاسخگویی خودکار"""
                # بررسی وضعیت اکو - اگر اکو فعال است، پاسخگویی خودکار نکن
                try:
                    import sys
                    sys.path.append('./bots')
                    from echo_control import is_echo_active
                    if is_echo_active():
                        return
                except:
                    pass

                if not config['auto_reply_enabled']:
                    return

                chat_id = message.chat.id

                # بررسی ایموجی/کامند ممنوعه برای همه کاربران
                if await self.should_pause_spam(message, bot_id):
                    # دریافت اطلاعات فرستنده
                    user_id = message.from_user.id if message.from_user else 0
                    sender_name = message.from_user.first_name if message.from_user else "نامشخص"
                    sender_username = message.from_user.username if message.from_user else "نامشخص"

                    # تشخیص نوع فرستنده
                    if message.from_user:
                        if message.from_user.is_bot:
                            sender_type = "ربات تلگرام"
                            sender_detail = f"@{sender_username}" if sender_username else f"ربات {user_id}"
                        else:
                            sender_type = "کاربر"
                            sender_detail = f"{sender_name} (@{sender_username})" if sender_username else f"{sender_name}"
                    else:
                        sender_type = "فرستنده نامشخص"
                        sender_detail = "بدون اطلاعات"

                    logger.info(f"🛑 بات {bot_id} - ایموجی/کامند ممنوعه تشخیص داده شد در چت {chat_id}")
                    logger.info(f"   └ توسط: {sender_type} - {sender_detail} (ID: {user_id})")

                    # نمایش محتوای پیام با بررسی امنیت
                    message_content = message.text or message.caption or "[بدون متن]"
                    if len(message_content) > 100:
                        message_content = message_content[:100] + "..."
                    logger.info(f"   └ محتوای پیام: {message_content}")

                    # **توقف کلی همه بات‌ها در این چت تا پیام بعدی دشمن**
                    self.global_paused[chat_id] = user_id
                    logger.info(f"⏸️ همه بات‌ها در چت {chat_id} متوقف شدند تا پیام بعدی دشمن")

                    # لاگ عملیات در دیتابیس
                    chat_title = message.chat.title if message.chat.title else f"چت {chat_id}"
                    self.log_action(bot_id, "global_pause_forbidden", user_id, f"توقف کلی توسط {sender_type} ({sender_detail}) در {chat_title}")

                    # ❌ هیچ واکنشی نشون نده و همه بات‌ها رو متوقف کن
                    return

                # بررسی اینکه آیا این چت متوقف شده یا نه
                if chat_id in self.global_paused:
                    # اگر پیام از دشمن باشد، سیستم رو فعال کن
                    if message.from_user:
                        user_id = message.from_user.id
                        enemy_list = self.get_enemy_list(bot_id)
                        enemy_ids = {row[0] for row in enemy_list}

                        if user_id in enemy_ids:
                            # دشمن پیام فرستاده - ازسرگیری فعالیت
                            paused_by = self.global_paused[chat_id]
                            del self.global_paused[chat_id]
                            logger.info(f"▶️ سیستم در چت {chat_id} ازسرگیری شد - دشمن {user_id} پیام فرستاد")
                            logger.info(f"   └ قبلاً توسط کاربر {paused_by} متوقف شده بود")
                            self.log_action(bot_id, "global_resume_by_enemy", user_id, f"ازسرگیری توسط دشمن {user_id}")
                            # ادامه به منطق پاسخگویی
                        else:
                            # کاربر عادی پیام فرستاده - همچنان متوقف
                            logger.debug(f"⏸️ چت {chat_id} همچنان متوقف - کاربر عادی {user_id} پیام فرستاد")
                            return
                    else:
                        # پیام بدون فرستنده - همچنان متوقف
                        return

                # ادامه منطق فقط برای پیام‌هایی که from_user دارند
                if not message.from_user:
                    return

                user_id = message.from_user.id

                # بررسی دشمن بودن
                enemy_list = self.get_enemy_list(bot_id)
                enemy_ids = {row[0] for row in enemy_list}

                if user_id in enemy_ids:
                    # شروع فحش نامحدود به دشمن - همیشه شروع می‌شود حتی بعد از توقف با ایموجی
                    fosh_list = self.get_fosh_list(bot_id)
                    if fosh_list:
                        # ایجاد کلید یونیک برای این دشمن در این بات
                        spam_key = f"{bot_id}_{user_id}_{chat_id}"

                        # اگر قبلاً تسک فعال برای این دشمن وجود دارد، آن را متوقف کن
                        if spam_key in self.continuous_spam_tasks:
                            try:
                                self.continuous_spam_tasks[spam_key].cancel()
                                logger.info(f"🔄 تسک قبلی فحش برای دشمن {user_id} در بات {bot_id} متوقف شد")
                            except:
                                pass

                        # پاک کردن حالت توقف اضطراری برای این چت اگر فعال است
                        if chat_id in self.chat_emergency_stops and self.chat_emergency_stops[chat_id].is_set():
                            logger.info(f"⚡ پاک کردن توقف اضطراری چت {chat_id} برای شروع مجدد فحش به دشمن {user_id}")
                            self.chat_emergency_stops[chat_id].clear()

                        # شروع تسک جدید فحش نامحدود
                        spam_task = asyncio.create_task(
                            self.continuous_spam_attack(client, message, user_id, fosh_list, bot_id, chat_id)
                        )
                        self.continuous_spam_tasks[spam_key] = spam_task
                        logger.info(f"🔥 شروع مجدد فحش نامحدود به دشمن {user_id} توسط بات {bot_id}")
                    return

                # در حالت گفتگوی خودکار، احتمال پاسخ به پیام‌های عادی
                if self.auto_chat_enabled and chat_id in self.active_conversations:
                    import random
                    # 20% احتمال پاسخ به پیام‌های عادی کاربران
                    if random.random() < 0.2 and not user_id in enemy_ids:
                        # انتخاب پاسخ مناسب از دیتابیس گفتگو
                        response_messages = self.get_conversation_messages('response')
                        if response_messages:
                            selected_response = choice(response_messages)

                            # با تاخیر کوتاه پاسخ بده تا طبیعی به نظر برسد
                            await asyncio.sleep(random.uniform(2, 8))
                            await self.send_auto_conversation_message(chat_id, bot_id, selected_response)

                            # به‌روزرسانی آمار گفتگو
                            conv = self.active_conversations[chat_id]
                            conv['message_count'] += 1
                            conv['last_bot'] = bot_id
                            conv['last_message_time'] = time.time()
                            self.last_bot_activity[bot_id] = time.time()

                            logger.info(f"💬 ربات {bot_id} به پیام کاربر {user_id} پاسخ داد: {selected_response[:30]}...")
                            return

                # بررسی دوست بودن
                friend_list = self.get_friend_list(bot_id)
                friend_ids = {row[0] for row in friend_list}

                if user_id in friend_ids:
                    word_list = self.get_friend_words(bot_id)
                    if word_list:
                        selected = choice(word_list)
                        await self.send_coordinated_reply(message, selected, bot_id)

            # ذخیره بات
            self.bots[bot_id] = {
                'client': app,
                'config': config,
                'status': 'initialized'
            }

            return app

        except Exception as e:
            logger.error(f"❌ خطا در ایجاد بات {bot_id}: {e}")
            return None

    async def send_coordinated_reply(self, message, selected_content, bot_id):
        """ارسال پاسخ با کنترل rate limiting مشترک"""
        chat_id = message.chat.id

        # ایجاد lock برای چت در صورت عدم وجود
        if chat_id not in self.chat_locks:
            self.chat_locks[chat_id] = asyncio.Lock()

        async with self.chat_locks[chat_id]:
            try:
                # بررسی آخرین زمان ارسال پیام در این چت
                current_time = time.time()

                if chat_id in self.last_message_time:
                    time_since_last = current_time - self.last_message_time[chat_id]
                    if time_since_last < self.min_global_delay:
                        # انتظار تا رسیدن به حداقل تاخیر
                        wait_time = self.min_global_delay - time_since_last
                        await asyncio.sleep(wait_time)

                # ارسال پاسخ
                await self.send_reply(message, selected_content)

                # ثبت زمان ارسال
                self.last_message_time[chat_id] = time.time()

                logger.debug(f"📤 بات {bot_id} پاسخ دوستانه در چت {chat_id} ارسال کرد")

            except Exception as e:
                logger.error(f"❌ خطا در ارسال پاسخ هماهنگ بات {bot_id}: {e}")
                raise

    async def send_reply(self, message, selected_content):
        """ارسال پاسخ"""
        try:
            content_text, media_type, file_id = selected_content

            if media_type and file_id:
                reply_methods = {
                    "photo": message.reply_photo,
                    "video": message.reply_video,
                    "animation": message.reply_animation,
                    "sticker": message.reply_sticker,
                    "audio": message.reply_audio,
                    "voice": message.reply_voice,
                    "video_note": message.reply_video_note,
                    "document": message.reply_document
                }

                method = reply_methods.get(media_type)
                if method:
                    await method(file_id)
            elif content_text:
                await message.reply_text(content_text)
        except Exception as e:
            logger.error(f"خطا در ارسال پاسخ: {e}")

    async def start_all_bots(self):
        """شروع همه بات‌ها"""
        self.running = True

        # بارگذاری ایموجی‌های ممنوعه قبل از شروع
        self.forbidden_emojis = self.load_forbidden_emojis_from_db()

        # شروع ربات گزارش‌دهی
        await self.start_report_bot()

        # ایجاد همه بات‌ها
        tasks = []
        for bot_id, config in self.bot_configs.items():
            bot = await self.create_bot(bot_id, config)
            if bot:
                tasks.append(self.start_single_bot(bot_id))

        # شروع همه بات‌ها به صورت موازی
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # بررسی کدام بات‌ها متصل شدند
        connected_bots = []
        for bot_id in self.bot_configs.keys():
            if bot_id in self.bots and self.bots[bot_id]['status'] == 'running':
                connected_bots.append(bot_id)

        # تنها پیام نهایی نمایش داده می‌شود
        if connected_bots:
            print(f"🎉 بات‌های متصل شده: {', '.join(map(str, sorted(connected_bots)))} - آماده کار هستند")
        else:
            print("❌ هیچ باتی متصل نشد")

        # نگه داشتن سیستم زنده
        try:
            while self.running:
                await asyncio.sleep(10)
                # بررسی بدون لاگ
                if self.report_bot and self.report_bot.client and not self.report_bot.client.is_connected:
                    try:
                        await self.report_bot.client.start()
                    except:
                        pass
        except KeyboardInterrupt:
            logger.info("🔴 متوقف شدن با Ctrl+C")
        finally:
            await self.stop_all_bots()

    async def start_single_bot(self, bot_id):
        """شروع یک بات"""
        try:
            if bot_id not in self.bots:
                return

            bot_info = self.bots[bot_id]
            client = bot_info['client']

            await client.start()
            bot_info['status'] = 'running'
            bot_info['start_time'] = datetime.now()

            # بارگذاری ایموجی‌های ممنوعه از دیتابیس برای همه بات‌ها
            try:
                loaded_emojis = self.load_forbidden_emojis_from_db()
                self.forbidden_emojis.update(loaded_emojis)
            except Exception as e:
                logger.error(f"خطا در بارگذاری ایموجی‌ها برای بات {bot_id}: {e}")

            # مانیتورینگ بدون لاگ
            while self.running and bot_info['status'] == 'running':
                try:
                    if not client.is_connected:
                        await client.start()
                    await asyncio.sleep(10)
                except:
                    await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"❌ خطا در شروع بات {bot_id}: {e}")
            if bot_id in self.bots:
                self.bots[bot_id]['status'] = 'error'

                # تلاش برای راه‌اندازی مجدد خودکار
                await asyncio.sleep(30)
                if self.running:
                    await self.restart_bot(bot_id)

    async def stop_single_bot(self, bot_id):
        """متوقف کردن یک بات"""
        try:
            if bot_id in self.bots:
                bot_info = self.bots[bot_id]
                if bot_info['status'] == 'running':
                    await bot_info['client'].stop()
                    bot_info['status'] = 'stopped'
        except Exception as e:
            logger.error(f"❌ خطا در توقف بات {bot_id}: {e}")

    async def start_report_bot(self):
        """شروع ربات گزارش‌دهی"""
        try:
            self.report_bot = ReportBot()
            if not hasattr(self.report_bot, 'is_valid') or not self.report_bot.is_valid:
                self.report_bot = None
                return
            if not await self.report_bot.start_bot():
                self.report_bot = None
        except Exception as e:
            logger.error(f"❌ خطا در شروع ربات گزارش‌دهی: {e}")
            self.report_bot = None

    async def stop_all_bots(self):
        """متوقف کردن همه بات‌ها"""
        self.running = False

        if self.report_bot:
            await self.report_bot.stop_bot()

        if self.continuous_spam_tasks:
            for spam_key, task in list(self.continuous_spam_tasks.items()):
                try:
                    task.cancel()
                except:
                    pass
            self.continuous_spam_tasks.clear()

        tasks = []
        for bot_id in list(self.bots.keys()):
            tasks.append(self.stop_single_bot(bot_id))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def restart_bot(self, bot_id):
        """راه‌اندازی مجدد یک بات"""
        try:
            logger.info(f"🔄 راه‌اندازی مجدد بات {bot_id}...")

            # متوقف کردن بات فعلی
            await self.stop_single_bot(bot_id)
            await asyncio.sleep(2)

            # ایجاد مجدد بات
            if bot_id in self.bot_configs:
                config = self.bot_configs[bot_id]
                bot = await self.create_bot(bot_id, config)
                if bot:
                    # شروع مجدد بات
                    asyncio.create_task(self.start_single_bot(bot_id))
                    logger.info(f"✅ بات {bot_id} مجدداً راه‌اندازی شد")
                    return True

            return False

        except Exception as e:
            logger.error(f"❌ خطا در راه‌اندازی مجدد بات {bot_id}: {e}")
            return False

    def get_status(self):
        """دریافت وضعیت همه بات‌ها"""
        status = {
            'total_bots': len(self.bot_configs),
            'running_bots': len([b for b in self.bots.values() if b['status'] == 'running']),
            'error_bots': len([b for b in self.bots.values() if b['status'] == 'error']),
            'bots': []
        }

        for bot_id, bot_info in self.bots.items():
            status['bots'].append({
                'id': bot_id,
                'status': bot_info['status'],
                'config': bot_info['config']['session_name']
            })

        return status

    async def continuous_spam_attack(self, client, message, user_id, fosh_list, bot_id, chat_id):
        """فحش نامحدود به دشمن تا ایموجی ممنوعه فرستاده شود"""
        try:
            spam_key = f"{bot_id}_{user_id}_{chat_id}"
            fosh_count = 0

            logger.info(f"🔥 شروع فحش نامحدود بات {bot_id} به دشمن {user_id} در چت {chat_id}")

            while True:
                # بررسی فوری توقف اضطراری برای این چت در ابتدای هر loop
                if chat_id in self.chat_emergency_stops and self.chat_emergency_stops[chat_id].is_set():
                    logger.info(f"🚨 فحش نامحدود بات {bot_id} فوراً متوقف شد - توقف اضطراری چت {chat_id}")
                    break

                # بررسی اینکه آیا چت متوقف شده یا نه
                if chat_id in self.global_paused:
                    logger.info(f"⏸️ فحش نامحدود بات {bot_id} متوقف شد - چت {chat_id} در حالت توقف")
                    break

                # بررسی اینکه آیا تسک کنسل شده یا نه
                if spam_key not in self.continuous_spam_tasks:
                    logger.info(f"⏹️ فحش نامحدود بات {bot_id} متوقف شد - تسک حذف شده")
                    break

                try:
                    # انتخاب فحش تصادفی
                    selected = choice(fosh_list)
                    await self.send_coordinated_message(client, message, selected, bot_id)
                    fosh_count += 1

                    # لاگ هر 10 فحش
                    if fosh_count % 10 == 0:
                        logger.info(f"🔥 بات {bot_id} - ارسال {fosh_count} فحش به دشمن {user_id}")

                    # دریافت تاخیر قابل تنظیم برای این بات
                    spam_delay = self.get_spam_delay(bot_id)

                    # بررسی فوری توقف اضطراری برای این چت قبل از انتظار
                    if chat_id in self.chat_emergency_stops and self.chat_emergency_stops[chat_id].is_set():
                        logger.info(f"🚨 فحش نامحدود بات {bot_id} فوراً متوقف شد - توقف اضطراری چت {chat_id} (حین انتظار)")
                        break

                    # تقسیم تاخیر به قطعات کوچک‌تر برای چک کردن سریع‌تر توقف
                    sleep_intervals = max(20, int(spam_delay * 50))  # حداقل 20 قطعه، 50 بررسی در ثانیه
                    interval_time = spam_delay / sleep_intervals if sleep_intervals > 0 else 0.02

                    should_break = False
                    for _ in range(sleep_intervals):
                        await asyncio.sleep(interval_time)

                        # بررسی اولویت بالا: توقف اضطراری برای این چت
                        if chat_id in self.chat_emergency_stops and self.chat_emergency_stops[chat_id].is_set():
                            logger.info(f"🚨 فحش نامحدود بات {bot_id} فوراً متوقف شد - توقف اضطراری چت {chat_id} (حین انتظار)")
                            should_break = True
                            break

                        # چک کردن توقف در هر قطعه
                        if chat_id in self.global_paused:
                            logger.info(f"⏸️ فحش نامحدود بات {bot_id} متوقف شد - چت {chat_id} در حالت توقف (حین انتظار)")
                            should_break = True
                            break

                        if spam_key not in self.continuous_spam_tasks:
                            logger.info(f"⏹️ فحش نامحدود بات {bot_id} متوقف شد - تسک حذف شده (حین انتظار)")
                            should_break = True
                            break

                    # اگر در loop داخلی break شد، از loop اصلی هم break کن
                    if should_break:
                        break

                except FloodWait as e:
                    # اگر تلگرام محدودیت زمانی اعمال کرد
                    wait_time = float(e.value) if hasattr(e, 'value') else 30.0
                    logger.warning(f"⏳ فلود ویت {wait_time} ثانیه برای بات {bot_id}")
                    await asyncio.sleep(wait_time)
                    continue

                except Exception as send_error:
                    logger.error(f"❌ خطا در ارسال فحش بات {bot_id}: {send_error}")
                    await asyncio.sleep(5)  # تاخیر بعد از خطا
                    continue

            # پاک کردن تسک از لیست
            if spam_key in self.continuous_spam_tasks:
                del self.continuous_spam_tasks[spam_key]

            # لاگ نهایی
            self.log_action(bot_id, "continuous_spam", user_id, f"{fosh_count} فحش نامحدود در {message.chat.title}")
            logger.info(f"✅ بات {bot_id} - فحش نامحدود تمام شد. کل ارسالی: {fosh_count} فحش به دشمن {user_id}")

        except asyncio.CancelledError:
            # تسک کنسل شده
            if spam_key in self.continuous_spam_tasks:
                del self.continuous_spam_tasks[spam_key]
            logger.info(f"🚫 فحش نامحدود بات {bot_id} به دشمن {user_id} کنسل شد")

        except Exception as e:
            # پاک کردن تسک در صورت خطا
            if spam_key in self.continuous_spam_tasks:
                del self.continuous_spam_tasks[spam_key]
            logger.error(f"❌ خطا در فحش نامحدود بات {bot_id}: {e}")

    async def staged_attack(self, client, message, user_id, fosh_list, bot_id):
        """حمله مرحله‌ای - 5 مرحله با فاصله زمانی (متد قدیمی - حفظ شده برای سازگاری)"""
        try:
            chat_id = message.chat.id

            # بررسی اینکه آیا چت متوقف شده یا نه
            if chat_id in self.global_paused:
                logger.info(f"⏸️ حمله مرحله‌ای بات {bot_id} متوقف شد - چت {chat_id} در حالت توقف")
                return

            # مرحله 1: فوری
            selected = choice(fosh_list)
            await self.send_fosh_reply(client, message, selected)
            logger.info(f"🔥 بات {bot_id} - مرحله 1: فحش به دشمن {user_id}")

            # مرحله 2: بعد از 1 ثانیه
            await asyncio.sleep(1)
            if chat_id not in self.global_paused:
                selected = choice(fosh_list)
                await self.send_fosh_reply(client, message, selected)
                logger.info(f"🔥 بات {bot_id} - مرحله 2: فحش به دشمن {user_id}")

            # مرحله 3: بعد از 1 ثانیه دیگر  
            await asyncio.sleep(1)
            if chat_id not in self.global_paused:
                selected = choice(fosh_list)
                await self.send_fosh_reply(client, message, selected)
                logger.info(f"🔥 بات {bot_id} - مرحله 3: فحش به دشمن {user_id}")

            # مرحله 4: بعد از 1 ثانیه دیگر
            await asyncio.sleep(1)
            if chat_id not in self.global_paused:
                selected = choice(fosh_list)
                await self.send_fosh_reply(client, message, selected)
                logger.info(f"🔥 بات {bot_id} - مرحله 4: فحش به دشمن {user_id}")

            # مرحله 5: بعد از 1 ثانیه دیگر
            await asyncio.sleep(1)
            if chat_id not in self.global_paused:
                selected = choice(fosh_list)
                await self.send_fosh_reply(client, message, selected)
                logger.info(f"🔥 بات {bot_id} - مرحله 5: فحش به دشمن {user_id}")

            # لاگ کامل حمله
            self.log_action(bot_id, "staged_attack", user_id, f"حمله مرحله‌ای 5 فحش در {message.chat.title}")
            logger.info(f"✅ بات {bot_id} - حمله مرحله‌ای کامل شد به دشمن {user_id}")

        except Exception as e:
            logger.error(f"خطا در حمله مرحله‌ای بات {bot_id}: {e}")

    async def send_coordinated_message(self, client, message, selected_content, bot_id):
        """ارسال پیام با کنترل rate limiting مشترک"""
        chat_id = message.chat.id

        # ایجاد lock برای چت در صورت عدم وجود
        if chat_id not in self.chat_locks:
            self.chat_locks[chat_id] = asyncio.Lock()

        async with self.chat_locks[chat_id]:
            try:
                # بررسی آخرین زمان ارسال پیام در این چت
                current_time = time.time()

                if chat_id in self.last_message_time:
                    time_since_last = current_time - self.last_message_time[chat_id]
                    if time_since_last < self.min_global_delay:
                        # انتظار تا رسیدن به حداقل تاخیر
                        wait_time = self.min_global_delay - time_since_last
                        await asyncio.sleep(wait_time)

                # ارسال پیام
                await self.send_fosh_reply(client, message, selected_content)

                # ثبت زمان ارسال
                self.last_message_time[chat_id] = time.time()

                logger.debug(f"📤 بات {bot_id} پیام در چت {chat_id} ارسال کرد")

            except Exception as e:
                logger.error(f"❌ خطا در ارسال پیام هماهنگ بات {bot_id}: {e}")
                raise

    async def send_fosh_reply(self, client, message, selected_content):
        """ارسال فحش"""
        try:
            content_text, media_type, file_id = selected_content

            if media_type and file_id:
                reply_methods = {
                    "photo": client.send_photo,
                    "video": client.send_video,
                    "animation": client.send_animation,
                    "sticker": client.send_sticker,
                    "audio": client.send_audio,
                    "voice": client.send_voice,
                    "video_note": client.send_video_note,
                    "document": client.send_document
                }

                method = reply_methods.get(media_type)
                if method:
                    await method(message.chat.id, file_id, reply_to_message_id=message.id)
            elif content_text:
                await client.send_message(message.chat.id, content_text, reply_to_message_id= message.id)
        except Exception as e:
            logger.error(f"خطا در ارسال فحش: {e}")

# متغیر کلی لانچر
launcher = UnifiedBotLauncher()

async def main():
    """تابع اصلی"""
    try:
        print("="*60)
        print("🤖 لانچر واحد بات‌های تلگرام")
        print("="*60)
        print("🎯 شروع همه ۹ بات در یک فرآیند...")
        print("📍 برای متوقف کردن: Ctrl+C")
        print("="*60)

        # شروع همه بات‌ها
        await launcher.start_all_bots()

    except KeyboardInterrupt:
        logger.info("🔴 متوقف شدن با Ctrl+C")
    except Exception as e:
        logger.error(f"❌ خطای غیرمنتظره: {e}")
    finally:
        await launcher.stop_all_bots()

if __name__ == "__main__":
    asyncio.run(main())