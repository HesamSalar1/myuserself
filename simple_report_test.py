#!/usr/bin/env python3
"""
تست ساده ربات گزارش‌دهی
"""

import asyncio
import os
import sys
import logging
from pyrogram import Client

# فعال کردن لاگینگ
logging.basicConfig(level=logging.INFO)

async def test_simple_bot():
    """تست ساده ربات تلگرام"""
    token = os.getenv('REPORT_BOT_TOKEN', '').strip()
    
    if not token:
        print("❌ توکن یافت نشد")
        return False
    
    print(f"✅ توکن: {token[:20]}...")
    
    try:
        # تست با API credentials مختلف
        api_credentials = [
            (15508294, "778e5cd56ffcf22c2d62aa963ce85a0c"),
            (29262538, "0417ebf26dbd92d3455d51595f2c923c"),
            (21555907, "16f4e09d753bc4b182434d8e37f410cd"),
        ]
        
        for api_id, api_hash in api_credentials:
            try:
                print(f"🔄 تست با API ID: {api_id}")
                client = Client(
                    "simple_test",
                    api_id=api_id,
                    api_hash=api_hash,
                    bot_token=token,
                    workdir="."
                )
                break
            except Exception as e:
                print(f"❌ API {api_id} ناموفق: {e}")
                continue
        else:
            print("❌ هیچ API معتبری یافت نشد")
            return False
        
        print("📡 در حال اتصال...")
        await client.start()
        print("✅ اتصال موفق")
        
        me = await client.get_me()
        print(f"🤖 ربات: @{me.username} (ID: {me.id})")
        
        await client.stop()
        print("🛑 ربات متوقف شد")
        
        return True
        
    except Exception as e:
        print(f"❌ خطا: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_simple_bot())
    print("✅ تست موفق" if result else "❌ تست ناموفق")