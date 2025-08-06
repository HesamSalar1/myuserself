# 🚫 راهنمای کامل مدیریت ایموجی‌های ممنوعه

## 🎯 نمای کلی

سیستم ایموجی پیشرفته با قابلیت تشخیص فوق‌سریع (کمتر از 0.05 ثانیه) و مدیریت پیشرفته ایموجی‌های ممنوعه.

---

## 📋 کامندهای اضافه کردن

### اضافه کردن ایموجی منفرد:
```bash
/addemoji ⚡         # اضافه کردن ایموجی تکی
/addemoji 🎮         # ایموجی گیم
/addemoji 💎         # ایموجی الماس
```

### اضافه کردن چندتایی:
```bash
/addemoji ⚡ 🎮 💎   # چند ایموجی با فاصله
/addemoji "⚡ 🎮 💎" # با کوتیشن (اختیاری)
```

### اضافه کردن با توضیح:
```bash
/addemoji ⚡ "ایموجی انرژی گیم"
/addemoji 🎮 "ایموجی ربات گیم"
```

---

## 🗑️ کامندهای حذف

### حذف ایموجی منفرد:
```bash
/delemoji ⚡         # حذف ایموجی تکی
/delemoji 🎮         # حذف ایموجی گیم
```

### حذف چندتایی:
```bash
/delemoji ⚡ 🎮      # چند ایموجی با فاصله
```

### حذف همه:
```bash
/clearemojis        # حذف همه ایموجی‌ها (احتیاط!)
/clearemojis confirm # تایید حذف همه
```

---

## 📜 کامندهای مشاهده

### لیست کامل:
```bash
/listemojis         # لیست همه ایموجی‌های ممنوعه
/listemojis 10      # نمایش 10 تای اول
/listemojis all     # نمایش کامل (بدون محدودیت)
```

### جستجوی هوشمند:
```bash
/findemoji ⚡       # جستجوی ایموجی خاص
/findemoji game     # جستجو در توضیحات
/findemoji energy   # جستجوی کلیدی
```

### آمار ایموجی:
```bash
/emojicount         # تعداد کل ایموجی‌ها
/emojistats         # آمار کامل
```

---

## 🧪 کامندهای تست و دیباگ

### تست تشخیص:
```bash
/testemoji ⚡       # تست تشخیص ایموجی
/testemoji "⚡ متن تست" # تست با متن
```

### تست سرعت:
```bash
/speedtest          # تست سرعت تشخیص
/speedtest 100      # تست با 100 نمونه
/speedtest detailed # تست مفصل
```

### دیباگ پیشرفته:
```bash
/debugemoji ⚡      # دیباگ ایموجی خاص
/debugemoji all     # دیباگ همه سیستم
/debugmode on       # فعال کردن حالت دیباگ
/debugmode off      # غیرفعال کردن دیباگ
```

---

## 🔄 کامندهای مدیریت

### سینک و بروزرسانی:
```bash
/sync               # سینک فوری همه بات‌ها
/reload             # بازخوانی از دیتابیس
/refresh            # تازه‌سازی کش
```

### پشتیبان‌گیری:
```bash
/backup             # پشتیبان‌گیری ایموجی‌ها
/restore            # بازگردانی پشتیبان
/export             # صادرات به فایل
```

### بازنشانی:
```bash
/reset              # بازنشانی تنظیمات
/reset emojis       # بازنشانی فقط ایموجی‌ها
/reset confirm      # تایید بازنشانی
```

---

## 📊 کامندهای آمار و گزارش

### آمار کلی:
```bash
/emojistats         # آمار کامل ایموجی‌ها
/detectstats        # آمار تشخیص
/performance        # آمار عملکرد
```

### گزارش‌های تشخیص:
```bash
/detectionlog       # لاگ تشخیص‌ها
/detectionlog 24h   # لاگ ۲۴ ساعت اخیر
/detectionlog today # لاگ امروز
```

### تحلیل ترافیک:
```bash
/traffic            # آمار ترافیک
/peaktime           # زمان اوج فعالیت
/responsetime       # زمان پاسخ میانگین
```

---

## ⚙️ تنظیمات پیشرفته

### تنظیمات تشخیص:
```bash
/sensitivity high   # حساسیت بالا
/sensitivity medium # حساسیت متوسط
/sensitivity low    # حساسیت پایین
```

### تنظیمات واکنش:
```bash
/reaction instant   # واکنش فوری
/reaction delayed   # واکنش با تاخیر
/reaction smart     # واکنش هوشمند
```

### تنظیمات کش:
```bash
/cache clear        # پاک کردن کش
/cache optimize     # بهینه‌سازی کش
/cache status       # وضعیت کش
```

---

## 💡 نکات و ترفندها

### ۱. **اضافه کردن سریع:**
```bash
# بهتر:
/addemoji ⚡ 🎮 💎 🔥 ⭐

# به جای:
/addemoji ⚡
/addemoji 🎮
/addemoji 💎
```

### ۲. **تست قبل از اضافه:**
```bash
/testemoji ⚡       # اول تست کنید
/addemoji ⚡        # سپس اضافه کنید
```

### ۳. **استفاده از توضیحات:**
```bash
/addemoji ⚡ "انرژی - ربات گیم اکسیون"
/addemoji 🎮 "کنسول - ربات گیم پلی"
```

### ۴. **مدیریت تعداد زیاد:**
```bash
/listemojis 20      # محدود کردن نمایش
/findemoji game     # جستجوی هدفمند
/clearemojis old    # پاک کردن قدیمی‌ها
```

---

## ⚠️ هشدارها و احتیاط

### 🔴 **خطرناک:**
```bash
/clearemojis        # همه را پاک می‌کند!
/reset emojis       # بازنشانی کامل!
```

### 🟡 **احتیاط:**
```bash
/addemoji 😀 😃 😄  # تعداد زیاد ایموجی عمومی
/sensitivity high   # ممکن است False Positive داشته باشد
```

### 🟢 **امن:**
```bash
/testemoji          # همیشه امن
/listemojis         # فقط نمایش
/emojistats         # فقط آمار
```

---

## 🆘 عیب‌یابی

### مشکل: ایموجی تشخیص نمی‌شود
```bash
/sync               # سینک کنید
/reload             # دوباره لود کنید
/testemoji [ایموجی] # تست کنید
```

### مشکل: تشخیص کند است
```bash
/cache clear        # کش را پاک کنید
/performance        # عملکرد را چک کنید
/speedtest          # سرعت را تست کنید
```

### مشکل: False Positive
```bash
/sensitivity medium # حساسیت را کم کنید
/debugemoji [ایموجی] # دیباگ کنید
```

---

## 📚 مثال‌های کاربردی

### سناریو ۱: راه‌اندازی اولیه
```bash
/listemojis         # چک کنید چی دارید
/addemoji ⚡ 🎮 💎   # ایموجی‌های گیم اضافه کنید
/testemoji ⚡       # تست کنید
/speedtest          # سرعت را چک کنید
```

### سناریو ۲: بهبود عملکرد
```bash
/performance        # عملکرد فعلی
/cache optimize     # بهینه‌سازی کش
/sync               # سینک همه بات‌ها
/speedtest detailed # تست مجدد
```

### سناریو ۳: عیب‌یابی
```bash
/debugmode on       # فعال کردن دیباگ
/testemoji [مشکل]   # تست مورد مشکل
/detectionlog       # چک کردن لاگ
/debugmode off      # غیرفعال کردن دیباگ
```

برای بازگشت به راهنمای کلی: `/help`