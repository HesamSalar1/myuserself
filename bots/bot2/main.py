import json
import asyncio
import sys
import sqlite3
import logging
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.types import Message, ChatMember
from pyrogram.errors import FloodWait, UserNotParticipant, ChatWriteForbidden
from random import choice

# تنظیمات اصلی
api_id = 29262538
api_hash = "0417ebf26dbd92d3455d51595f2c923c"
admin_id = 7419698159

# تنظیم لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot2.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Client("my_bot2", api_id, api_hash)

# متغیر کنترل وضعیت پاسخگویی خودکار
auto_reply_enabled = True

print("Bot 2 initialized with API ID:", api_id)
print("Bot 2 starting...")

if __name__ == "__main__":
    app.run()