
import sqlite3
import logging

logger = logging.getLogger(__name__)

def init_shared_db():
    """ایجاد دیتابیس مشترک برای تمام باتها"""
    conn = sqlite3.connect('shared_data.db')
    cursor = conn.cursor()

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

    # جدول فحش‌های مشترک
    cursor.execute('''CREATE TABLE IF NOT EXISTS shared_fosh_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fosh TEXT,
        media_type TEXT,
        file_id TEXT,
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

    conn.commit()
    conn.close()

# توابع مدیریت دشمنان مشترک
def add_shared_enemy(user_id, username=None, first_name=None, bot_number=0):
    conn = sqlite3.connect('shared_data.db')
    cursor = conn.cursor()
    try:
        # حذف از دوستان مشترک اگر وجود دارد
        cursor.execute("DELETE FROM shared_friend_list WHERE user_id = ?", (user_id,))
        cursor.execute("INSERT INTO shared_enemy_list (user_id, username, first_name, added_by_bot) VALUES (?, ?, ?, ?)", 
                      (user_id, username, first_name, bot_number))
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    conn.close()
    return result

def remove_shared_enemy(user_id):
    conn = sqlite3.connect('shared_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shared_enemy_list WHERE user_id = ?", (user_id,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_shared_enemy_list():
    conn = sqlite3.connect('shared_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, first_name, added_by_bot, created_at FROM shared_enemy_list")
    result = cursor.fetchall()
    conn.close()
    return result

# توابع مدیریت دوستان مشترک
def add_shared_friend(user_id, username=None, first_name=None, bot_number=0):
    conn = sqlite3.connect('shared_data.db')
    cursor = conn.cursor()
    try:
        # حذف از دشمنان مشترک اگر وجود دارد
        cursor.execute("DELETE FROM shared_enemy_list WHERE user_id = ?", (user_id,))
        cursor.execute("INSERT INTO shared_friend_list (user_id, username, first_name, added_by_bot) VALUES (?, ?, ?, ?)", 
                      (user_id, username, first_name, bot_number))
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    conn.close()
    return result

def remove_shared_friend(user_id):
    conn = sqlite3.connect('shared_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shared_friend_list WHERE user_id = ?", (user_id,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_shared_friend_list():
    conn = sqlite3.connect('shared_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, first_name, added_by_bot, created_at FROM shared_friend_list")
    result = cursor.fetchall()
    conn.close()
    return result

# توابع مدیریت فحش‌های مشترک
def add_shared_fosh(fosh=None, media_type=None, file_id=None, bot_number=0):
    conn = sqlite3.connect('shared_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO shared_fosh_list (fosh, media_type, file_id, added_by_bot) VALUES (?, ?, ?, ?)", 
                      (fosh, media_type, file_id, bot_number))
        conn.commit()
        result = True
    except Exception as e:
        logger.error(f"خطا در اضافه کردن فحش مشترک: {e}")
        result = False
    conn.close()
    return result

def remove_shared_fosh(fosh):
    conn = sqlite3.connect('shared_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shared_fosh_list WHERE fosh = ?", (fosh,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_shared_fosh_list():
    conn = sqlite3.connect('shared_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT fosh, media_type, file_id, added_by_bot FROM shared_fosh_list")
    result = cursor.fetchall()
    conn.close()
    return result

# توابع مدیریت کلمات دوستانه مشترک
def add_shared_friend_word(word=None, media_type=None, file_id=None, bot_number=0):
    conn = sqlite3.connect('shared_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO shared_friend_words (word, media_type, file_id, added_by_bot) VALUES (?, ?, ?, ?)", 
                      (word, media_type, file_id, bot_number))
        conn.commit()
        result = True
    except Exception as e:
        logger.error(f"خطا در اضافه کردن کلمه مشترک: {e}")
        result = False
    conn.close()
    return result

def remove_shared_friend_word(word):
    conn = sqlite3.connect('shared_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shared_friend_words WHERE word = ?", (word,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_shared_friend_words():
    conn = sqlite3.connect('shared_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT word, media_type, file_id, added_by_bot FROM shared_friend_words")
    result = cursor.fetchall()
    conn.close()
    return result

# ایجاد دیتابیس مشترک
init_shared_db()
