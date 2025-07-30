#!/usr/bin/env python3
"""
سیستم پیشرفته گفتگوی خودکار با دیکشنری گسترده
ایجاد گفتگوهای طبیعی، عامیانه و متنوع
"""

import random
import sqlite3
import time
from typing import List, Dict, Tuple

class EnhancedConversationSystem:
    """سیستم پیشرفته گفتگوی طبیعی"""
    
    def __init__(self):
        # دیکشنری گسترده عبارات فارسی عامیانه
        self.casual_phrases = {
            'greetings': [
                'سلاااام', 'هی سلام', 'سلام عزیزم', 'چطوری داداش؟', 'سلام بر شما',
                'سلام چطورید؟', 'هالو', 'سلام و علیکم', 'درود', 'چه خبرا؟',
                'صبح بخیر', 'ظهر بخیر', 'عصر بخیر', 'شب بخیر', 'روز بخیر'
            ],
            
            'responses_positive': [
                'واااای چقد جالب!', 'آره دقیقاً همینه', 'حق با توه', 'آفرین برات!',
                'عالی بود', 'خیلی خوب', 'بد نبود', 'تو راه راست میری', 'درسته',
                'موافقم باهات', 'قبول دارم', 'یعنی واقعاً؟', 'چه حال داد!',
                'perfect', 'awesome', 'great job', 'well done', 'fantastic'
            ],
            
            'responses_negative': [
                'نه بابا', 'اصلاً موافق نیستم', 'نمیدونم والا', 'شک دارم',
                'اَه! چه سگی', 'اوووف', 'ول کن', 'بیخیال', 'اصلاً نه',
                'not really', 'nah', 'come on', 'seriously?', 'no way'
            ],
            
            'questions_casual': [
                'چی شده؟', 'کجا بودی تا حالا؟', 'چه خبرا؟', 'چی کار میکنی؟',
                'کی میای؟', 'کجا میری؟', 'چند وقت طول کشید؟', 'چطور شد؟',
                'کی گفته؟', 'مطمئنی؟', 'جدی میگی؟', 'واقعاً؟',
                'what do you think?', 'really?', 'are you sure?', 'when?', 'where?'
            ],
            
            'emotions_strong': [
                'وای خیلی ناراحت شدم', 'چه خبر خوبی!', 'آفرین! فوق‌العاده بود',
                'اووووف چقد بده', 'ای وای!', 'خدا قوت!', 'متأسفم واست',
                'خیلی خوشحالم', 'غمگین شدم', 'عصبانیم', 'استرس دارم',
                'oh my god!', 'so sorry', 'congratulations!', 'I\'m so happy', 'damn!'
            ],
            
            'daily_topics': [
                'امروز چکار کردی؟', 'کاری ندارم', 'خسته شدم', 'حوصلم سر رفت',
                'بریم بیرون', 'یه کاری بکنیم', 'کلافه‌ام', 'سرحالم امروز',
                'درس دارم', 'کار دارم', 'تعطیله امروز', 'آخر هفته چیکار کنیم؟'
            ],
            
            # موضوعات تخصصی
            'tech_talk': [
                'گوشیم خراب شده', 'اینترنت قطع شده', 'یه اپ جدید پیدا کردم',
                'آپدیت جدید اومده', 'لپ تاپم هنگ کرده', 'وای فای نمیاد',
                'شارژم تموم شده', 'یه بازی باحال پیدا کردم', 'سایت داون شده',
                'phone is lagging', 'wifi is down', 'new update is out', 'app crashed'
            ],
            
            'food_talk': [
                'شکمم گرسنه است', 'چی بخوریم؟', 'پیتزا سفارش بدیم؟', 'خیلی سیر شدم',
                'این غذا خوشمزه است', 'تلخه', 'شوره', 'بی‌مزه است', 'فلفله',
                'آب میخوام', 'نوشابه داری؟', 'شکلات کجاست؟', 'میوه بخوریم',
                'I\'m starving', 'let\'s order food', 'tasty!', 'too spicy', 'yummy'
            ],
            
            'sports_talk': [
                'بریم ورزش کنیم', 'تیم ما برد', 'بازی دیشب دیدی؟', 'خیلی خسته شدم',
                'استادیوم بریم', 'والیبال بازی کنیم', 'فوتبال دوست دارم', 'دویدن بریم',
                'good match', 'let\'s play', 'team won', 'great goal', 'nice shot'
            ],
            
            # عبارات ترکیبی فارسی-انگلیسی
            'mixed_language': [
                'واقعاً؟ OMG نمیدونستم!', 'LOL خیلی بامزه بود', 'OK چشم حتماً',
                'Sorry دیر کردم', 'Thanks واقعاً ممنون', 'Bye برو خوش بگذره',
                'Hello سلام چطوری؟', 'Nice خیلی خوب بود', 'Cool باحال بود'
            ],
            
            # عبارات هندی مخلوط
            'hindi_mixed': [
                'Namaste دوست من', 'Kya haal hai؟', 'Bohot accha!', 'Theek hai',
                'Bilkul sahi میگی', 'Kya lagta hai تو نظرت چیه؟', 'Arrey yaar!',
                'Kuch karte hain یه کاری بکنیم', 'Bahut tasty خوشمزه بود'
            ],
            
            # عبارات محاوره‌ای قوی
            'slang_expressions': [
                'دهنت سرویس!', 'مرسی داش', 'چاکرم', 'قربون شما', 'جون دل',
                'عزیز دل', 'گل گفتی', 'حرف حساب زدی', 'دمت گرم', 'نوکرتم',
                'چشم قشنگت', 'فدات بشم', 'خیلی باحالی', 'تو خفنی', 'زیاد داری'
            ]
        }
        
        # الگوهای گفتگوی پیچیده
        self.conversation_patterns = {
            'story_telling': [
                'راستی یه چیز جالب واسه‌تون تعریف کنم...',
                'دیروز یه اتفاق عجیب افتاد...',
                'یادتونه اون روز که...',
                'یکی از دوستام گفت که...',
                'تو اینستا دیدم که...'
            ],
            
            'asking_opinions': [
                'نظرتون درباره این چیه؟',
                'شما اگه جای من بودید چیکار میکردید؟',
                'این کارو درست کردم؟',
                'فکر میکنید باید این کارو بکنم؟',
                'موافقید با این تصمیم؟'
            ],
            
            'making_plans': [
                'فردا برنامه دارید؟',
                'آخر هفته کجا بریم؟',
                'شب میایید بیرون؟',
                'سینما بریم این هفته؟',
                'یه جا قشنگ میشناسید برای رفتن؟'
            ],
            
            'sharing_experiences': [
                'امروز یه چیز جالب یاد گرفتم',
                'دیدم یه فیلم خیلی باحال',
                'یه کتاب داشتم میخوندم',
                'تو یوتیوب یه ویدیو دیدم',
                'یه خبر جالب شنیدم'
            ]
        }
        
        # شخصیت‌های مختلف برای ربات‌ها
        self.bot_personalities = {
            1: {'type': 'funny', 'traits': ['شوخ', 'سربه‌سر', 'بامزه']},
            2: {'type': 'serious', 'traits': ['جدی', 'منطقی', 'عاقل']},
            3: {'type': 'friendly', 'traits': ['دوستانه', 'مهربان', 'صمیمی']},
            4: {'type': 'energetic', 'traits': ['پرانرژی', 'فعال', 'هیجان‌زده']},
            5: {'type': 'calm', 'traits': ['آروم', 'صبور', 'متین']},
            6: {'type': 'curious', 'traits': ['کنجکاو', 'پرسشگر', 'علاقه‌مند']},
            7: {'type': 'creative', 'traits': ['خلاق', 'هنری', 'تخیلی']},
            8: {'type': 'practical', 'traits': ['عملی', 'واقع‌بین', 'کاربردی']},
            9: {'type': 'social', 'traits': ['اجتماعی', 'پرحرف', 'دوست‌داشتنی']}
        }
    
    def generate_natural_message(self, bot_id: int, topic: str, conversation_context: Dict) -> str:
        """تولید پیام طبیعی بر اساس شخصیت ربات و زمینه گفتگو"""
        
        personality = self.bot_personalities.get(bot_id, {'type': 'neutral', 'traits': ['معمولی']})
        
        # انتخاب نوع پیام بر اساس زمینه
        message_type = self._determine_message_type(conversation_context, personality)
        
        # تولید پیام اصلی
        base_message = self._generate_base_message(message_type, topic, personality)
        
        # اضافه کردن عناصر شخصیتی
        enhanced_message = self._add_personality_elements(base_message, personality, bot_id)
        
        # اضافه کردن عناصر طبیعی (املا، تکرار کلمات، ...)
        natural_message = self._add_natural_elements(enhanced_message)
        
        return natural_message
    
    def _determine_message_type(self, context: Dict, personality: Dict) -> str:
        """تعیین نوع پیام بر اساس زمینه و شخصیت"""
        
        last_messages = context.get('last_messages', [])
        time_since_last = context.get('time_since_last', 0)
        
        # اگر مدت زیادی سکوت بوده، سوال یا موضوع جدید
        if time_since_last > 300:  # 5 دقیقه
            return random.choice(['new_topic', 'question', 'greeting'])
        
        # اگر آخرین پیام سوال بوده، پاسخ بده
        if last_messages and '؟' in last_messages[-1]:
            return 'response'
        
        # بر اساس شخصیت
        if personality['type'] == 'curious':
            return random.choice(['question', 'response', 'sharing'])
        elif personality['type'] == 'funny':
            return random.choice(['joke', 'funny_response', 'casual'])
        elif personality['type'] == 'social':
            return random.choice(['sharing', 'planning', 'friendly_chat'])
        
        # پیش‌فرض
        return random.choice(['response', 'casual', 'sharing'])
    
    def _generate_base_message(self, message_type: str, topic: str, personality: Dict) -> str:
        """تولید پیام پایه"""
        
        if message_type == 'greeting':
            return random.choice(self.casual_phrases['greetings'])
        
        elif message_type == 'response':
            if random.random() < 0.6:
                return random.choice(self.casual_phrases['responses_positive'])
            else:
                return random.choice(self.casual_phrases['responses_negative'])
        
        elif message_type == 'question':
            return random.choice(self.casual_phrases['questions_casual'])
        
        elif message_type == 'new_topic':
            return random.choice(self.conversation_patterns['story_telling'])
        
        elif message_type == 'sharing':
            return random.choice(self.conversation_patterns['sharing_experiences'])
        
        elif message_type == 'planning':
            return random.choice(self.conversation_patterns['making_plans'])
        
        elif message_type == 'casual':
            return random.choice(self.casual_phrases['daily_topics'])
        
        # موضوع‌های تخصصی
        elif topic == 'تکنولوژی':
            return random.choice(self.casual_phrases['tech_talk'])
        elif topic == 'خوراک':
            return random.choice(self.casual_phrases['food_talk'])
        elif topic == 'ورزش':
            return random.choice(self.casual_phrases['sports_talk'])
        
        # پیش‌فرض
        return random.choice(self.casual_phrases['responses_positive'])
    
    def _add_personality_elements(self, message: str, personality: Dict, bot_id: int) -> str:
        """اضافه کردن عناصر شخصیتی به پیام"""
        
        personality_type = personality['type']
        
        if personality_type == 'funny':
            # اضافه کردن عناصر طنز
            if random.random() < 0.3:
                message += ' 😂'
            if random.random() < 0.2:
                message = 'هههه ' + message
        
        elif personality_type == 'energetic':
            # اضافه کردن انرژی
            if random.random() < 0.4:
                message = message.replace('!', '!!!')
            if random.random() < 0.3:
                message += ' یالا بریم!'
        
        elif personality_type == 'calm':
            # آرام‌تر کردن پیام
            message = message.replace('!!!', '.')
            if random.random() < 0.2:
                message = 'آروم ' + message
        
        elif personality_type == 'social':
            # اجتماعی‌تر کردن
            if random.random() < 0.3:
                message += ' بچه‌ها چه فکر میکنین؟'
        
        return message
    
    def _add_natural_elements(self, message: str) -> str:
        """اضافه کردن عناصر طبیعی (تایپوها، تکرار، ...)"""
        
        # احتمال استفاده از زبان مخلوط
        if random.random() < 0.15:
            mixed_phrases = self.casual_phrases['mixed_language'] + self.casual_phrases['hindi_mixed']
            return random.choice(mixed_phrases)
        
        # احتمال استفاده از عبارات محاوره‌ای
        if random.random() < 0.1:
            slang = random.choice(self.casual_phrases['slang_expressions'])
            return f"{slang} {message}"
        
        # احتمال تکرار حروف برای تأکید
        if random.random() < 0.2:
            if 'خیلی' in message:
                message = message.replace('خیلی', 'خیلیییی')
            if 'واقعاً' in message:
                message = message.replace('واقعاً', 'واقعااااً')
        
        # احتمال اضافه کردن پیشوند یا پسوند عامیانه
        if random.random() < 0.15:
            prefixes = ['وای', 'آخ', 'اوه', 'اَه']
            message = f"{random.choice(prefixes)} {message}"
        
        return message
    
    def get_conversation_starters(self, topic: str = None) -> List[str]:
        """دریافت پیام‌های شروع‌کننده برای موضوع خاص"""
        
        starters = []
        
        # شروع عمومی
        starters.extend([
            'سلام بچه‌ها چه خبرا؟',
            'هی چطورید امروز؟',
            'سلام من اومدم!',
            'چه خبر از زندگی؟',
            'بچه‌ها کجاین؟'
        ])
        
        # شروع موضوعی
        if topic == 'تکنولوژی':
            starters.extend([
                'دیدید چه آپدیت جدیدی اومده؟',
                'گوشیتون چطوره؟',
                'یه اپ باحال پیدا کردم'
            ])
        elif topic == 'خوراک':
            starters.extend([
                'کی غذا درست کرده؟ گرسنه‌ام',
                'بچه‌ها امروز چی خوردین؟',
                'کجا غذای خوب هست؟'
            ])
        elif topic == 'ورزش':
            starters.extend([
                'بازی دیشب دیدین؟',
                'کی ورزش میکنه؟',
                'تیم مورد علاقه‌تون کیه؟'
            ])
        
        return starters
    
    def should_bot_respond(self, bot_id: int, last_speaker: int, time_since_last: float) -> bool:
        """تعیین اینکه آیا ربات باید پاسخ دهد یا نه"""
        
        # ربات نباید پشت سر خودش صحبت کند
        if last_speaker == bot_id:
            return False
        
        # احتمال پاسخ بر اساس شخصیت
        personality = self.bot_personalities.get(bot_id, {'type': 'neutral'})
        
        base_probability = 0.3  # احتمال پایه 30%
        
        if personality['type'] == 'social':
            base_probability = 0.5
        elif personality['type'] == 'calm':
            base_probability = 0.2
        elif personality['type'] == 'energetic':
            base_probability = 0.4
        
        # احتمال بیشتر اگر زمان زیادی گذشته
        if time_since_last > 120:  # 2 دقیقه
            base_probability += 0.2
        
        return random.random() < base_probability

# تست سیستم
if __name__ == "__main__":
    conv_system = EnhancedConversationSystem()
    
    print("🧪 تست سیستم گفتگوی پیشرفته")
    print("=" * 50)
    
    # تست تولید پیام برای ربات‌های مختلف
    for bot_id in range(1, 6):
        context = {
            'last_messages': ['سلام چطورید؟'],
            'time_since_last': 30
        }
        
        message = conv_system.generate_natural_message(bot_id, 'روزمره', context)
        personality = conv_system.bot_personalities[bot_id]['type']
        print(f"🤖 ربات {bot_id} ({personality}): {message}")
    
    print("\n" + "=" * 50)
    print("✅ سیستم پیشرفته آماده است!")