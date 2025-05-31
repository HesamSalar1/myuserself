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
api_id = 21555907
api_hash = "16f4e09d753bc4b182434d8e37f410cd"
admin_id = 7607882302

# تنظیم لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot3.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Client("my_bot3", api_id, api_hash)

# متغیر کنترل وضعیت پاسخگویی خودکار
auto_reply_enabled = True

print("Bot 3 initialized with API ID:", api_id)
print("Bot 3 starting...")

if __name__ == "__main__":
    app.run()