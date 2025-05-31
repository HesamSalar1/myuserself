import json
import asyncio
import sys
import sqlite3
import logging
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

from pyrogram import Client, filters

from pyrogram.types import Message, ChatMember
from pyrogram.errors import FloodWait, UserNotParticipant, ChatWriteForbidden
from random import choice

# تنظیمات اصلی
api_id = 15508294
api_hash = "778e5cd56ffcf22c2d62aa963ce85a0c"
admin_id = 7850529246

# تنظیم لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Client("my_bot", api_id, api_hash)

# متغیر کنترل وضعیت پاسخگویی خودکار
auto_reply_enabled = True

# دیکشنری برای نگهداری تسک‌های شمارش
count_tasks = {}

print("Bot 1 initialized with API ID:", api_id)
print("Bot 1 starting...")

if __name__ == "__main__":
    app.run()