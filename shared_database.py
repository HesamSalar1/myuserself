
import sqlite3
import json
from datetime import datetime

DB_FILE = 'shared_data.db'

def init_shared_db():
    """راه‌اندازی دیتابیس مشترک"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # جدول دشمنان مشترک
    cursor.execute('''CREATE TABLE IF NOT EXISTS shared_enemies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        first_name TEXT,
        added_by_bot INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول دوستان مشترک
    cursor.execute('''CREATE TABLE IF NOT EXISTS shared_friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        first_name TEXT,
        added_by_bot INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول فحش‌های مشترک
    cursor.execute('''CREATE TABLE IF NOT EXISTS shared_fosh (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fosh TEXT,
        media_type TEXT,
        file_id TEXT,
        added_by_bot INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول کلمات دوستانه مشترک
    cursor.execute('''CREATE TABLE IF NOT EXISTS shared_words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT,
        media_type TEXT,
        file_id TEXT,
        added_by_bot INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

def add_shared_enemy(user_id, username=None, first_name=None, bot_number=None):
    """اضافه کردن دشمن مشترک"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # حذف از دوستان اگر وجود دارد
        cursor.execute("DELETE FROM shared_friends WHERE user_id = ?", (user_id,))
        cursor.execute("INSERT INTO shared_enemies (user_id, username, first_name, added_by_bot) VALUES (?, ?, ?, ?)", 
                      (user_id, username, first_name, bot_number))
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    conn.close()
    return result

def add_shared_friend(user_id, username=None, first_name=None, bot_number=None):
    """اضافه کردن دوست مشترک"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # حذف از دشمنان اگر وجود دارد
        cursor.execute("DELETE FROM shared_enemies WHERE user_id = ?", (user_id,))
        cursor.execute("INSERT INTO shared_friends (user_id, username, first_name, added_by_bot) VALUES (?, ?, ?, ?)", 
                      (user_id, username, first_name, bot_number))
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    conn.close()
    return result

def add_shared_fosh(fosh=None, media_type=None, file_id=None, bot_number=None):
    """اضافه کردن فحش مشترک"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO shared_fosh (fosh, media_type, file_id, added_by_bot) VALUES (?, ?, ?, ?)", 
                      (fosh, media_type, file_id, bot_number))
        conn.commit()
        result = True
    except Exception as e:
        result = False
    conn.close()
    return result

def add_shared_word(word=None, media_type=None, file_id=None, bot_number=None):
    """اضافه کردن کلمه دوستانه مشترک"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO shared_words (word, media_type, file_id, added_by_bot) VALUES (?, ?, ?, ?)", 
                      (word, media_type, file_id, bot_number))
        conn.commit()
        result = True
    except Exception as e:
        result = False
    conn.close()
    return result

def get_shared_enemies():
    """دریافت لیست دشمنان مشترک"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, first_name, added_by_bot, created_at FROM shared_enemies")
    result = cursor.fetchall()
    conn.close()
    return result

def get_shared_friends():
    """دریافت لیست دوستان مشترک"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, first_name, added_by_bot, created_at FROM shared_friends")
    result = cursor.fetchall()
    conn.close()
    return result

def get_shared_fosh():
    """دریافت لیست فحش‌های مشترک"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT fosh, media_type, file_id, added_by_bot, created_at FROM shared_fosh")
    result = cursor.fetchall()
    conn.close()
    return result

def get_shared_words():
    """دریافت لیست کلمات دوستانه مشترک"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT word, media_type, file_id, added_by_bot, created_at FROM shared_words")
    result = cursor.fetchall()
    conn.close()
    return result

def remove_shared_enemy(user_id):
    """حذف دشمن مشترک"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shared_enemies WHERE user_id = ?", (user_id,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def remove_shared_friend(user_id):
    """حذف دوست مشترک"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shared_friends WHERE user_id = ?", (user_id,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def remove_shared_fosh(fosh_text):
    """حذف فحش مشترک"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shared_fosh WHERE fosh = ?", (fosh_text,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def remove_shared_word(word_text):
    """حذف کلمه دوستانه مشترک"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shared_words WHERE word = ?", (word_text,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_shared_stats():
    """آمار داده‌های مشترک"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM shared_enemies")
    enemies = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM shared_friends")
    friends = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM shared_fosh")
    fosh = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM shared_words")
    words = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'enemies': enemies,
        'friends': friends,
        'fosh': fosh,
        'words': words
    }

# راه‌اندازی دیتابیس
init_shared_db()
