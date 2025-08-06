#!/usr/bin/env python3
"""
Stack Host Diagnostic Tool
تشخیص و رفع مشکلات اتصال ربات‌های تلگرام در محیط Stack Host
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Tuple
from pyrogram import Client
from pyrogram.errors import *

# تنظیمات لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('stackhost_diagnostic.log')
    ]
)
logger = logging.getLogger(__name__)

class StackHostDiagnostic:
    def __init__(self):
        self.bot_configs = self._load_bot_configs()
        self.environment_info = self._gather_environment_info()
        
    def _load_bot_configs(self) -> Dict:
        """بارگذاری تنظیمات ربات‌ها"""
        return {
            1: {
                'api_id': int(os.getenv('BOT1_API_ID', '23700094')),
                'api_hash': os.getenv('BOT1_API_HASH', "7cd6b0ba9c5b1a5f21b8b76f1e2b8e40"),
                'admin_id': int(os.getenv('BOT1_ADMIN_ID', '7850529246')),
            },
            2: {
                'api_id': int(os.getenv('BOT2_API_ID', '29262538')),
                'api_hash': os.getenv('BOT2_API_HASH', "0417ebf26dbd92d3455d51595f2c923c"),
                'admin_id': int(os.getenv('BOT2_ADMIN_ID', '7419698159')),
            },
            3: {
                'api_id': int(os.getenv('BOT3_API_ID', '21555907')),
                'api_hash': os.getenv('BOT3_API_HASH', "16f4e09d753bc4b182434d8e37f410cd"),
                'admin_id': int(os.getenv('BOT3_ADMIN_ID', '7607882302')),
            },
            4: {
                'api_id': int(os.getenv('BOT4_API_ID', '15508294')),
                'api_hash': os.getenv('BOT4_API_HASH', "778e5cd56ffcf22c2d62aa963ce85a0c"),
                'admin_id': int(os.getenv('BOT4_ADMIN_ID', '7739974888')),
            },
            5: {
                'api_id': int(os.getenv('BOT5_API_ID', '25101001')),
                'api_hash': os.getenv('BOT5_API_HASH', "unique_hash_for_bot5_placeholder"),
                'admin_id': int(os.getenv('BOT5_ADMIN_ID', '7346058093')),
            },
            6: {
                'api_id': int(os.getenv('BOT6_API_ID', '25101002')),
                'api_hash': os.getenv('BOT6_API_HASH', "unique_hash_for_bot6_placeholder"),
                'admin_id': int(os.getenv('BOT6_ADMIN_ID', '7927398744')),
            },
            7: {
                'api_id': int(os.getenv('BOT7_API_ID', '25101003')),
                'api_hash': os.getenv('BOT7_API_HASH', "unique_hash_for_bot7_placeholder"),
                'admin_id': int(os.getenv('BOT7_ADMIN_ID', '8092847456')),
            },
            8: {
                'api_id': int(os.getenv('BOT8_API_ID', '25101004')),
                'api_hash': os.getenv('BOT8_API_HASH', "unique_hash_for_bot8_placeholder"),
                'admin_id': int(os.getenv('BOT8_ADMIN_ID', '7220521953')),
            },
            9: {
                'api_id': int(os.getenv('BOT9_API_ID', '25101005')),
                'api_hash': os.getenv('BOT9_API_HASH', "unique_hash_for_bot9_placeholder"),
                'admin_id': int(os.getenv('BOT9_ADMIN_ID', '7143723023')),
            }
        }
    
    def _gather_environment_info(self) -> Dict:
        """جمع‌آوری اطلاعات محیط"""
        return {
            'hostname': os.getenv('HOSTNAME', 'unknown'),
            'platform': os.getenv('PLATFORM', 'unknown'),
            'total_bots': int(os.getenv('TOTAL_BOTS', '9')),
            'bot_mode': os.getenv('BOT_MODE', 'development'),
            'python_version': sys.version,
            'working_directory': os.getcwd(),
            'stackhost_detected': any([
                os.getenv('STACKHOST_DEPLOYMENT'),
                os.getenv('STACKHOST_ENV'),
                'stackhost' in os.getenv('HOSTNAME', '').lower(),
                'stack' in os.getenv('PLATFORM', '').lower()
            ])
        }
    
    def validate_credentials(self, bot_id: int) -> Tuple[bool, str]:
        """بررسی اعتبار credentials ربات"""
        config = self.bot_configs.get(bot_id)
        if not config:
            return False, f"تنظیمات بات {bot_id} یافت نشد"
        
        api_id = config.get('api_id')
        api_hash = config.get('api_hash')
        
        if not api_id or not api_hash:
            return False, "API ID یا API Hash موجود نیست"
        
        # بررسی placeholder values
        placeholder_hashes = [
            'YOUR_BOT5_API_HASH', 'YOUR_BOT6_API_HASH', 'YOUR_BOT7_API_HASH',
            'YOUR_BOT8_API_HASH', 'YOUR_BOT9_API_HASH',
            'unique_hash_for_bot5_placeholder', 'unique_hash_for_bot6_placeholder',
            'unique_hash_for_bot7_placeholder', 'unique_hash_for_bot8_placeholder',
            'unique_hash_for_bot9_placeholder'
        ]
        
        if api_hash in placeholder_hashes:
            return False, "API Hash پیش‌فرض است - نیاز به تنظیم credentials واقعی"
        
        if str(api_id).startswith('25101'):
            return False, "API ID پیش‌فرض است - نیاز به تنظیم API ID واقعی"
        
        return True, "تنظیمات معتبر است"
    
    async def test_bot_connection(self, bot_id: int) -> Tuple[bool, str]:
        """تست اتصال ربات"""
        config = self.bot_configs.get(bot_id)
        if not config:
            return False, f"تنظیمات بات {bot_id} یافت نشد"
        
        # ابتدا اعتبار credentials را بررسی کن
        is_valid, validation_message = self.validate_credentials(bot_id)
        if not is_valid:
            return False, f"Credentials نامعتبر: {validation_message}"
        
        try:
            # تست اتصال با session موقت
            test_client = Client(
                f"diagnostic_test_bot_{bot_id}",
                api_id=config['api_id'],
                api_hash=config['api_hash'],
                in_memory=True
            )
            
            logger.info(f"🔍 تست اتصال بات {bot_id}...")
            await test_client.connect()
            
            # دریافت اطلاعات کاربر
            me = await test_client.get_me()
            await test_client.disconnect()
            
            return True, f"اتصال موفق - @{me.username} ({me.first_name})"
            
        except ApiIdInvalid:
            return False, "API ID نامعتبر است"
        except ApiIdPublishedFlood:
            return False, "API ID در حال flood است - لطفاً کمی صبر کنید"
        except AccessTokenInvalid:
            return False, "Access Token نامعتبر است"
        except AuthKeyUnregistered:
            return False, "Auth Key ثبت نشده - نیاز به ورود مجدد"
        except SessionPasswordNeeded:
            return False, "نیاز به رمز عبور دو مرحله‌ای"
        except FloodWait as e:
            return False, f"Flood wait - {e.value} ثانیه صبر کنید"
        except NetworkError:
            return False, "خطای شبکه - اتصال اینترنت را بررسی کنید"
        except Exception as e:
            return False, f"خطای غیرمنتظره: {type(e).__name__}: {str(e)}"
    
    def print_environment_report(self):
        """چاپ گزارش محیط"""
        print("\n" + "="*60)
        print("           🔧 Stack Host Diagnostic Report")
        print("="*60)
        
        print(f"🌐 Environment: {'Stack Host' if self.environment_info['stackhost_detected'] else 'Local'}")
        print(f"🏠 Hostname: {self.environment_info['hostname']}")
        print(f"💻 Platform: {self.environment_info['platform']}")
        print(f"🤖 Total Bots: {self.environment_info['total_bots']}")
        print(f"⚙️  Mode: {self.environment_info['bot_mode']}")
        print(f"🐍 Python: {self.environment_info['python_version'].split()[0]}")
        print(f"📁 Directory: {self.environment_info['working_directory']}")
        
    def print_credentials_report(self):
        """چاپ گزارش credentials"""
        print("\n" + "="*60)
        print("           📊 Credentials Validation Report")
        print("="*60)
        
        valid_count = 0
        invalid_count = 0
        
        for bot_id in range(1, 10):
            is_valid, message = self.validate_credentials(bot_id)
            status = "✅ معتبر" if is_valid else "❌ نامعتبر"
            print(f"🤖 Bot {bot_id}: {status} - {message}")
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
        
        print(f"\n📈 خلاصه: {valid_count} معتبر، {invalid_count} نامعتبر")
        
        if invalid_count > 0:
            print("\n⚠️  توجه: ربات‌های نامعتبر نیاز به تنظیم API credentials دارند")
            print("📝 برای دریافت API credentials به https://my.telegram.org/apps مراجعه کنید")
    
    async def run_connection_tests(self):
        """اجرای تست‌های اتصال"""
        print("\n" + "="*60)
        print("           🔌 Connection Test Report")
        print("="*60)
        
        successful_connections = 0
        failed_connections = 0
        
        for bot_id in range(1, 10):
            try:
                success, message = await self.test_bot_connection(bot_id)
                status = "✅ موفق" if success else "❌ ناموفق"
                print(f"🤖 Bot {bot_id}: {status} - {message}")
                
                if success:
                    successful_connections += 1
                else:
                    failed_connections += 1
                    
            except Exception as e:
                print(f"🤖 Bot {bot_id}: ❌ خطا - {str(e)}")
                failed_connections += 1
        
        print(f"\n📈 خلاصه: {successful_connections} موفق، {failed_connections} ناموفق")
        
        return successful_connections, failed_connections
    
    def generate_stackhost_config_suggestions(self):
        """تولید پیشنهادات تنظیمات Stack Host"""
        print("\n" + "="*60)
        print("           💡 Stack Host Configuration Suggestions")
        print("="*60)
        
        invalid_bots = []
        for bot_id in range(1, 10):
            is_valid, _ = self.validate_credentials(bot_id)
            if not is_valid:
                invalid_bots.append(bot_id)
        
        if invalid_bots:
            print("🔧 تنظیمات لازم برای متغیرهای محیطی Stack Host:")
            print()
            for bot_id in invalid_bots:
                print(f"# Bot {bot_id} Configuration")
                print(f"BOT{bot_id}_API_ID=YOUR_ACTUAL_API_ID_{bot_id}")
                print(f"BOT{bot_id}_API_HASH=YOUR_ACTUAL_API_HASH_{bot_id}")
                print(f"BOT{bot_id}_ADMIN_ID={self.bot_configs[bot_id]['admin_id']}")
                print()
        
        print("📋 برای استفاده از تنظیمات فوق:")
        print("1. به پنل Stack Host بروید")
        print("2. متغیرهای محیطی را اضافه کنید")
        print("3. API credentials را از https://my.telegram.org/apps دریافت کنید")
        print("4. ربات‌ها را restart کنید")

async def main():
    """تابع اصلی تشخیص"""
    print("🚀 شروع تشخیص Stack Host...")
    
    diagnostic = StackHostDiagnostic()
    
    # گزارش محیط
    diagnostic.print_environment_report()
    
    # گزارش credentials
    diagnostic.print_credentials_report()
    
    # تست اتصالات
    successful, failed = await diagnostic.run_connection_tests()
    
    # پیشنهادات
    if failed > 0:
        diagnostic.generate_stackhost_config_suggestions()
    
    # خلاصه نهایی
    print("\n" + "="*60)
    print("                    📋 Final Summary")
    print("="*60)
    
    if successful == 9:
        print("🎉 همه ربات‌ها آماده اتصال هستند!")
    elif successful > 0:
        print(f"⚠️  {successful} ربات آماده، {failed} ربات نیاز به تنظیم دارند")
    else:
        print("❌ هیچ ربات آماده اتصال نیست - API credentials را بررسی کنید")
    
    print("\n📝 Log file: stackhost_diagnostic.log")
    
    return successful, failed

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 تشخیص متوقف شد")
    except Exception as e:
        logger.error(f"خطای کلی در تشخیص: {e}")
        print(f"\n❌ خطا: {e}")