
import sqlite3
import asyncio
import threading
from contextlib import asynccontextmanager
import time
import logging

logger = logging.getLogger(__name__)

class SharedDatabaseManager:
    def __init__(self):
        self.db_path = 'shared_bot_data.db'
        self.connection_pool = {}
        self.lock = threading.Lock()
        
    async def get_connection(self, bot_id):
        """دریافت اتصال مخصوص هر بات"""
        with self.lock:
            if bot_id not in self.connection_pool:
                conn = sqlite3.connect(
                    self.db_path,
                    timeout=30.0,
                    check_same_thread=False,
                    isolation_level=None  # autocommit mode
                )
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA temp_store=memory")
                self.connection_pool[bot_id] = conn
                
            return self.connection_pool[bot_id]
    
    def init_shared_database(self):
        """راه‌اندازی دیتابیس مشترک"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        # جدول فحش‌های مشترک
        cursor.execute('''CREATE TABLE IF NOT EXISTS shared_fosh_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fosh TEXT,
            media_type TEXT,
            file_id TEXT,
            added_by_bot INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # جدول دشمنان مشترک
        cursor.execute('''CREATE TABLE IF NOT EXISTS shared_enemy_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            added_by_bot INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # جدول دوستان مشترک
        cursor.execute('''CREATE TABLE IF NOT EXISTS shared_friend_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            added_by_bot INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # جدول کلمات دوستانه مشترک
        cursor.execute('''CREATE TABLE IF NOT EXISTS shared_friend_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT,
            media_type TEXT,
            file_id TEXT,
            added_by_bot INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # جدول لاگ مشترک
        cursor.execute('''CREATE TABLE IF NOT EXISTS shared_action_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_id INTEGER,
            action_type TEXT NOT NULL,
            user_id INTEGER,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # جدول سینک بین باتان
        cursor.execute('''CREATE TABLE IF NOT EXISTS bot_sync (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_bot INTEGER,
            to_bot INTEGER,
            sync_type TEXT,
            data TEXT,
            processed BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        conn.commit()
        conn.close()
        logger.info("دیتابیس مشترک راه‌اندازی شد")

# توابع مشترک برای دسترسی به دیتا
async def add_shared_fosh(bot_id, fosh=None, media_type=None, file_id=None):
    db_manager = SharedDatabaseManager()
    conn = await db_manager.get_connection(bot_id)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO shared_fosh_list (fosh, media_type, file_id, added_by_bot) VALUES (?, ?, ?, ?)",
            (fosh, media_type, file_id, bot_id)
        )
        return True
    except Exception as e:
        logger.error(f"خطا در اضافه کردن فحش مشترک: {e}")
        return False

async def add_shared_enemy(bot_id, user_id, username=None, first_name=None):
    db_manager = SharedDatabaseManager()
    conn = await db_manager.get_connection(bot_id)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM shared_friend_list WHERE user_id = ?", (user_id,))
        cursor.execute(
            "INSERT OR REPLACE INTO shared_enemy_list (user_id, username, first_name, added_by_bot) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, bot_id)
        )
        return True
    except Exception as e:
        logger.error(f"خطا در اضافه کردن دشمن مشترک: {e}")
        return False

async def add_shared_friend(bot_id, user_id, username=None, first_name=None):
    db_manager = SharedDatabaseManager()
    conn = await db_manager.get_connection(bot_id)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM shared_enemy_list WHERE user_id = ?", (user_id,))
        cursor.execute(
            "INSERT OR REPLACE INTO shared_friend_list (user_id, username, first_name, added_by_bot) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, bot_id)
        )
        return True
    except Exception as e:
        logger.error(f"خطا در اضافه کردن دوست مشترک: {e}")
        return False

async def add_shared_word(bot_id, word=None, media_type=None, file_id=None):
    db_manager = SharedDatabaseManager()
    conn = await db_manager.get_connection(bot_id)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO shared_friend_words (word, media_type, file_id, added_by_bot) VALUES (?, ?, ?, ?)",
            (word, media_type, file_id, bot_id)
        )
        return True
    except Exception as e:
        logger.error(f"خطا در اضافه کردن کلمه مشترک: {e}")
        return False

async def get_shared_enemies():
    db_manager = SharedDatabaseManager()
    conn = await db_manager.get_connection(1)  # استفاده از اتصال بات 1
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id FROM shared_enemy_list")
    return [row[0] for row in cursor.fetchall()]

async def get_shared_friends():
    db_manager = SharedDatabaseManager()
    conn = await db_manager.get_connection(1)
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id FROM shared_friend_list")
    return [row[0] for row in cursor.fetchall()]

async def get_shared_fosh():
    db_manager = SharedDatabaseManager()
    conn = await db_manager.get_connection(1)
    cursor = conn.cursor()
    
    cursor.execute("SELECT fosh, media_type, file_id FROM shared_fosh_list")
    return cursor.fetchall()

async def get_shared_words():
    db_manager = SharedDatabaseManager()
    conn = await db_manager.get_connection(1)
    cursor = conn.cursor()
    
    cursor.execute("SELECT word, media_type, file_id FROM shared_friend_words")
    return cursor.fetchall()

# راه‌اندازی دیتابیس
db_manager = SharedDatabaseManager()
db_manager.init_shared_database()
