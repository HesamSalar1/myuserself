# 📝 راهنمای کامل مدیریت کلمات ممنوعه

## 🎯 نمای کلی

سیستم مدیریت کلمات و عبارات ممنوعه با قابلیت تشخیص هوشمند، دسته‌بندی، و تنظیمات حساسیت پیشرفته.

---

## 📋 کامندهای اضافه کردن

### اضافه کردن کلمه منفرد:
```bash
/addword spam                    # اضافه کردن کلمه تکی
/addword "bad word"              # کلمه با فاصله (نیاز به کوتیشن)
/addword advertisement           # کلمه تبلیغاتی
```

### اضافه کردن چندتایی:
```bash
/addword spam scam fake          # چند کلمه با فاصله
/addword "spam scam fake"        # با کوتیشن (اختیاری)
```

### اضافه کردن با دسته‌بندی:
```bash
/addword spam category:advertising
/addword scam category:fraud
/addword "bad phrase" category:offensive
```

### اضافه کردن عبارات پیچیده:
```bash
/addword "click here for"        # عبارت کامل
/addword "free money"            # عبارت تبلیغاتی
/addword "urgent message"        # عبارت اسپم
```

---

## 🗑️ کامندهای حذف

### حذف کلمه منفرد:
```bash
/delword spam                    # حذف کلمه تکی
/delword "bad word"              # حذف عبارت
```

### حذف چندتایی:
```bash
/delword spam scam fake          # حذف چند کلمه
```

### حذف بر اساس دسته:
```bash
/delword category:advertising    # حذف همه کلمات تبلیغاتی
/delword category:offensive      # حذف کلمات توهین‌آمیز
```

### حذف همه:
```bash
/clearwords                      # حذف همه کلمات (احتیاط!)
/clearwords confirm              # تایید حذف
/clearwords category:spam        # حذف یک دسته خاص
```

---

## 📜 کامندهای مشاهده

### لیست کامل:
```bash
/listwords                       # لیست همه کلمات ممنوعه
/listwords 20                    # نمایش ۲۰ تای اول
/listwords category:spam         # فقط کلمات اسپم
```

### جستجوی هوشمند:
```bash
/findword spam                   # جستجوی کلمه خاص
/findword "free"                 # جستجوی عبارت
/findword category:advertising   # جستجو در دسته
```

### آمار کلمات:
```bash
/wordcount                       # تعداد کل کلمات
/wordstats                       # آمار تفصیلی
/wordstats category              # آمار بر اساس دسته
```

---

## 🧪 کامندهای تست و دیباگ

### تست تشخیص:
```bash
/testword "spam message"         # تست تشخیص متن
/testword spam                   # تست کلمه خاص
/testword "this is a test spam message" # تست متن پیچیده
```

### تست حساسیت:
```bash
/sensitivity high                # حساسیت بالا
/testword "SPAM"                 # تست با حروف بزرگ
/sensitivity low                 # حساسیت پایین
/testword "spam"                 # تست مجدد
```

### دیباگ پیشرفته:
```bash
/debugword on                    # فعال کردن دیباگ
/debugword "test message"        # دیباگ متن خاص
/debugword category:spam         # دیباگ دسته خاص
```

---

## ⚙️ تنظیمات حساسیت

### سطوح حساسیت:
```bash
/sensitivity high                # تشخیص دقیق‌ترین شکل‌ها
/sensitivity medium              # تعادل دقت و پوشش
/sensitivity low                 # فقط تطبیق دقیق
```

### تنظیمات تطبیق:
```bash
/matching exact                  # تطبیق دقیق
/matching partial                # تطبیق جزئی
/matching fuzzy                  # تطبیق فازی (با اشتباهات تایپی)
```

### تنظیمات حروف:
```bash
/casesensitive on                # حساس به حروف بزرگ/کوچک
/casesensitive off               # بدون توجه به حروف
```

### تنظیمات کاراکتر:
```bash
/ignorespecial on                # نادیده گرفتن کاراکترهای خاص
/ignorespecial off               # در نظر گرفتن همه کاراکترها
/ignorenumbers on                # نادیده گرفتن اعداد
```

---

## 📊 دسته‌بندی کلمات

### دسته‌های پیش‌فرض:
- `spam` - کلمات اسپم
- `advertising` - کلمات تبلیغاتی
- `offensive` - کلمات توهین‌آمیز
- `fraud` - کلمات کلاهبرداری
- `adult` - محتوای بزرگسالان
- `violence` - محتوای خشونت‌آمیز

### مدیریت دسته‌ها:
```bash
/listcategories                  # لیست همه دسته‌ها
/createcategory newcat           # ایجاد دسته جدید
/deletecategory oldcat           # حذف دسته
/renamecategory oldcat newcat    # تغییر نام دسته
```

### کار با دسته‌ها:
```bash
/addword spam category:custom    # اضافه به دسته خاص
/moveword spam from:spam to:advertising # انتقال بین دسته‌ها
/copyword spam to:fraud          # کپی به دسته دیگر
```

---

## 🔄 کامندهای مدیریت

### سینک و بروزرسانی:
```bash
/syncwords                       # سینک کلمات در همه بات‌ها
/reloadwords                     # بازخوانی از دیتابیس
/refreshwords                    # تازه‌سازی کش کلمات
```

### پشتیبان‌گیری:
```bash
/backupwords                     # پشتیبان کلمات
/restorewords                    # بازگردانی پشتیبان
/exportwords                     # صادرات به فایل
/importwords file.txt            # وارد کردن از فایل
```

### بازنشانی:
```bash
/resetwords                      # بازنشانی همه کلمات
/resetwords category:spam        # بازنشانی یک دسته
/resetwords confirm              # تایید بازنشانی
```

---

## 📈 آمار و گزارش

### آمار کلی:
```bash
/wordstats                       # آمار کامل کلمات
/detectionstats words            # آمار تشخیص کلمات
/categorystats                   # آمار هر دسته
```

### گزارش‌های تشخیص:
```bash
/wordlog                         # لاگ تشخیص کلمات
/wordlog 24h                     # لاگ ۲۴ ساعت اخیر
/wordlog category:spam           # لاگ دسته خاص
```

### تحلیل محتوا:
```bash
/contentanalysis                 # تحلیل محتوای تشخیص شده
/topwords                        # پرتکرارترین کلمات تشخیص شده
/trendwords                      # روند کلمات ممنوعه
```

---

## 🎯 بهینه‌سازی عملکرد

### تنظیمات بهینه برای انواع چت:

#### 🎮 **چت‌های گیم (سریع):**
```bash
/sensitivity medium              # تعادل سرعت و دقت
/matching partial                # تطبیق سریع
/casesensitive off               # کاهش پردازش
```

#### 💬 **چت‌های عمومی (متعادل):**
```bash
/sensitivity medium              # تعادل مناسب
/matching fuzzy                  # تشخیص اشتباهات تایپی
/casesensitive off               # راحت‌تر برای کاربر
```

#### 🏢 **چت‌های رسمی (دقیق):**
```bash
/sensitivity high                # دقت بالا
/matching exact                  # تطبیق دقیق
/casesensitive on                # دقت در حروف
```

### پروفایل‌های آماده:
```bash
/loadwordprofile gaming          # پروفایل گیمینگ
/loadwordprofile business        # پروفایل کسب‌وکار
/loadwordprofile educational     # پروفایل آموزشی
/savewordprofile myprofile       # ذخیره پروفایل شخصی
```

---

## 🔧 تنظیمات پیشرفته

### فیلترهای هوشمند:
```bash
/smartfilter on                  # فعال کردن فیلتر هوشمند
/smartfilter aggressive          # حالت تهاجمی
/smartfilter conservative        # حالت محافظه‌کارانه
```

### تنظیمات کانتکست:
```bash
/context on                      # در نظر گرفتن متن قبل/بعد
/context 5                       # ۵ کلمه قبل و بعد
/context off                     # فقط کلمه مورد نظر
```

### تشخیص الگو:
```bash
/pattern on                      # تشخیص الگوهای تکراری
/pattern spammy                  # الگوهای اسپمی
/pattern advertising             # الگوهای تبلیغاتی
```

---

## 💡 نکات و ترفندها

### ۱. **استفاده از regex:**
```bash
/addword "\\b(spam|scam)\\b" type:regex    # استفاده از عبارات منظم
/addword "free\\s+money" type:regex        # الگوی پیچیده‌تر
```

### ۲. **کلمات مرکب:**
```bash
/addword "click here"            # عبارت کامل
/addword "free*money"            # با wildcard
/addword "urgent!" suffix:true   # پایانه خاص
```

### ۳. **مدیریت استثنائات:**
```bash
/addexception "free software"    # استثنا برای کلمه free
/addexception "spam protection"  # استثنا برای spam
```

### ۴. **تست قبل از اضافه:**
```bash
/testword "potential spam"       # اول تست کنید
/addword "potential spam"        # سپس اضافه کنید
```

---

## ⚠️ هشدارها

### 🔴 **خطرناک:**
```bash
/clearwords                      # همه کلمات پاک می‌شود
/sensitivity high + /matching fuzzy # خیلی False Positive
```

### 🟡 **احتیاط:**
```bash
/addword "free"                  # ممکن است خیلی عمومی باشد
/sensitivity high                # ممکن است مزاحم باشد
```

### 🟢 **امن:**
```bash
/testword                        # همیشه امن
/listwords                       # فقط نمایش
/wordstats                       # فقط آمار
```

---

## 🆘 رفع مشکلات متداول

### مشکل: کلمات تشخیص نمی‌شوند
```bash
/syncwords                       # سینک همه بات‌ها
/reloadwords                     # بازخوانی کلمات
/testword "کلمه مشکل‌دار"        # تست مستقیم
```

### مشکل: خیلی False Positive
```bash
/sensitivity medium              # کاهش حساسیت
/addexception "کلمه مجاز"        # اضافه استثنا
/matching exact                  # تطبیق دقیق‌تر
```

### مشکل: عملکرد کند
```bash
/refreshwords                    # تازه‌سازی کش
/optimize words                  # بهینه‌سازی
/pattern off                     # غیرفعال کردن الگو
```

---

## 📚 مثال‌های عملی

### سناریو ۱: مبارزه با اسپم
```bash
/addword spam scam fake fraud    # اضافه کلمات اسپم
/addword "free money" "click here" # اضافه عبارات
/sensitivity medium              # تنظیم حساسیت
/testword "this is spam"         # تست
```

### سناریو ۲: محافظت از تبلیغات
```bash
/createcategory ads              # ایجاد دسته تبلیغات
/addword "buy now" category:ads  # اضافه به دسته
/addword "discount" category:ads # کلمات تبلیغاتی
/sensitivity high                # حساسیت بالا برای تبلیغات
```

### سناریو ۳: عیب‌یابی
```bash
/debugword on                    # فعال کردن دیباگ
/testword "متن مشکل‌دار"         # تست مشکل
/wordlog                         # بررسی لاگ
/debugword off                   # غیرفعال کردن دیباگ
```

برای بازگشت به راهنمای کلی: `/help`