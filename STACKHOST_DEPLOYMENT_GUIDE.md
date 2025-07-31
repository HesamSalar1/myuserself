# StackHost Deployment Guide - مرحله به مرحله

## فایل‌های آماده برای Deployment:

1. **stackhost.yaml** - نسخه اصلی
2. **app.yaml** - نسخه ساده
3. **stackhost.yml** - پسوند مختلف
4. **.stackhost.yaml** - فایل مخفی

## مراحل Deployment:

### گام 1: انتخاب فایل
اگر `stackhost.yaml` کار نکرد، فایل‌های زیر را امتحان کنید:
- `app.yaml` 
- `stackhost.yml`
- `.stackhost.yaml`

### گام 2: بررسی محتوای فایل
تمام فایل‌ها شامل:
- ✅ name
- ✅ language: python  
- ✅ port: 5000
- ✅ install command
- ✅ **build command** (اصلی‌ترین بخش)
- ✅ run command
- ✅ environments

### گام 3: Deploy کردن
1. فایل مناسب را انتخاب کنید
2. در StackHost upload کنید
3. Deploy button را بزنید

## اگر همچنان مشکل دارید:

### احتمال 1: مشکل Platform
StackHost ممکن است بخش build را به شکل دیگری تفسیر کند

### احتمال 2: نیاز به Dockerfile  
اگر هیچ کدام کار نکرد، ممکن است Dockerfile نیاز باشد

### احتمال 3: مستندات StackHost
مراجعه به مستندات رسمی StackHost برای syntax دقیق

## فایل‌های پشتیبان:
- `Dockerfile` - آماده است
- `requirements.txt` - آماده است  
- `unified_bot_launcher.py` - آماده است

سیستم کاملاً آماده deployment است!