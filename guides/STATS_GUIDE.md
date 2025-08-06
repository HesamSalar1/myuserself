# 📊 راهنمای کامل آمار و گزارش‌گیری

## 🎯 نمای کلی

سیستم جامع آمارگیری و گزارش‌دهی با قابلیت نمایش آمار کلی، امنیتی، عملکرد، و تحلیل‌های پیشرفته.

---

## 📈 آمار کلی سیستم

### وضعیت کلی:
```bash
/status                          # وضعیت کامل سیستم
/status brief                    # خلاصه وضعیت
/status detailed                 # جزئیات کامل
/quickstatus                     # نمای سریع
```

### آمار بات‌ها:
```bash
/botstats                        # آمار همه بات‌ها
/botstats online                 # فقط بات‌های آنلاین
/botstats performance            # عملکرد بات‌ها
/botcount                        # تعداد کل بات‌ها
```

### آمار چت‌ها:
```bash
/chatstats                       # آمار همه چت‌ها
/chatstats active                # چت‌های فعال
/chatstats today                 # فعالیت امروز
/chatcount                       # تعداد چت‌ها
```

### آمار کاربران:
```bash
/userstats                       # آمار کل کاربران
/userstats friends               # آمار دوستان
/userstats enemies               # آمار دشمنان
/usercount                       # تعداد کاربران
```

---

## 🔒 آمار امنیتی

### آمار تشخیص:
```bash
/securitystats                   # آمار کلی امنیتی
/detectstats                     # آمار تشخیص‌ها
/detectstats emoji               # فقط ایموجی‌ها
/detectstats words               # فقط کلمات
```

### سطح تهدید:
```bash
/threatlevel                     # سطح تهدید کلی
/threatlevel current             # وضعیت فعلی
/threatlevel trend               # روند تهدیدات
/threatlevel alerts              # هشدارهای فعال
```

### آمار مسدودی:
```bash
/blockstats                      # آمار مسدودی‌ها
/blockstats today                # مسدودی‌های امروز
/blockstats reasons              # دلایل مسدودی
```

### تحلیل حملات:
```bash
/attackanalysis                  # تحلیل حملات
/attackpatterns                  # الگوهای حمله
/attacksource                    # منابع حملات
```

---

## ⚡ آمار عملکرد

### سرعت پاسخ:
```bash
/speedtest                       # تست سرعت
/speedtest detailed              # تست مفصل
/responsetime                    # زمان پاسخ میانگین
/latency                         # تأخیر شبکه
```

### عملکرد سیستم:
```bash
/performance                     # عملکرد کلی
/performance cpu                 # مصرف CPU
/performance memory              # مصرف RAM
/performance network             # ترافیک شبکه
```

### آمار پردازش:
```bash
/processstats                    # آمار پردازش
/processstats messages           # پردازش پیام‌ها
/processstats emojis             # پردازش ایموجی‌ها
/throughput                      # میزان عبور
```

### بهینه‌سازی:
```bash
/optimization                    # آمار بهینه‌سازی
/bottlenecks                     # گلوگاه‌های سیستم
/efficiency                      # کارایی سیستم
```

---

## 📅 گزارش‌های زمانی

### گزارش‌های روزانه:
```bash
/dailyreport                     # گزارش کامل روزانه
/dailyreport security            # امنیت روزانه
/dailyreport performance         # عملکرد روزانه
/today                           # خلاصه امروز
```

### گزارش‌های هفتگی:
```bash
/weeklyreport                    # گزارش هفتگی
/weeklyreport trends             # روندهای هفتگی
/weeklyreport comparison         # مقایسه با هفته قبل
```

### گزارش‌های ماهانه:
```bash
/monthlyreport                   # گزارش ماهانه
/monthlyreport summary           # خلاصه ماه
/monthlyreport growth            # رشد ماهانه
```

### گزارش‌های دلخواه:
```bash
/customreport 7d                 # گزارش ۷ روزه
/customreport 30d                # گزارش ۳۰ روزه
/customreport 2024-01-01:2024-01-31 # بازه خاص
```

---

## 🔍 تحلیل‌های پیشرفته

### تحلیل روند:
```bash
/trendanalysis                   # تحلیل روندها
/trendanalysis security          # روند امنیتی
/trendanalysis usage             # روند استفاده
```

### تحلیل الگو:
```bash
/patternanalysis                 # تحلیل الگوها
/patterns spam                   # الگوهای اسپم
/patterns behavior               # الگوهای رفتاری
```

### تحلیل پیش‌بینی:
```bash
/predictanalysis                 # تحلیل پیش‌بینی
/forecast load                   # پیش‌بینی بار
/forecast threats                # پیش‌بینی تهدیدات
```

### تحلیل مقایسه‌ای:
```bash
/compare today yesterday         # مقایسه امروز با دیروز
/compare thisweek lastweek       # مقایسه هفته‌ها
/compare performance             # مقایسه عملکرد
```

---

## 🖥️ مانیتورینگ سیستم

### سلامت سیستم:
```bash
/systemhealth                    # سلامت کلی
/health cpu                      # سلامت پردازنده
/health memory                   # سلامت حافظه
/health network                  # سلامت شبکه
```

### مصرف منابع:
```bash
/memoryusage                     # مصرف حافظه
/cpuusage                        # مصرف CPU
/diskusage                       # مصرف دیسک
/networkusage                    # مصرف شبکه
```

### زمان فعالیت:
```bash
/uptime                          # مدت فعالیت
/uptime bots                     # زمان فعالیت بات‌ها
/downtime                        # زمان‌های خاموشی
/availability                    # درصد دسترسی
```

### لاگ‌ها:
```bash
/logs                            # لاگ‌های سیستم
/logs error                      # لاگ‌های خطا
/logs security                   # لاگ‌های امنیتی
/logs performance                # لاگ‌های عملکرد
```

---

## 📊 آمار تعاملات

### آمار پیام‌ها:
```bash
/messagestats                    # آمار کل پیام‌ها
/messagestats hourly             # آمار ساعتی
/messagestats type               # بر اساس نوع پیام
```

### آمار واکنش‌ها:
```bash
/reactionstats                   # آمار واکنش‌ها
/reactionstats emoji             # واکنش‌های ایموجی
/reactionstats speed             # سرعت واکنش
```

### آمار تشخیص:
```bash
/detectionrate                   # نرخ تشخیص
/falsepositive                   # False Positive ها
/falsenegative                   # False Negative ها
/accuracy                        # دقت تشخیص
```

---

## 🎯 آمار اهداف و KPI

### شاخص‌های کلیدی:
```bash
/kpi                             # همه KPI ها
/kpi security                    # KPI امنیتی
/kpi performance                 # KPI عملکرد
/kpi user                        # KPI کاربری
```

### آمار اهداف:
```bash
/goals                           # وضعیت اهداف
/goals monthly                   # اهداف ماهانه
/goals achievement               # دستاوردها
```

### معیارهای موفقیت:
```bash
/metrics                         # همه معیارها
/metrics response                # معیار پاسخ‌دهی
/metrics detection               # معیار تشخیص
/benchmarks                      # معیارهای مرجع
```

---

## 📋 گزارش‌های تخصصی

### گزارش امنیت:
```bash
/securityreport                  # گزارش کامل امنیتی
/securityreport incidents        # حوادث امنیتی
/securityreport threats          # تهدیدات شناسایی شده
```

### گزارش عملکرد:
```bash
/performancereport               # گزارش کامل عملکرد
/performancereport bottlenecks   # گلوگاه‌های عملکرد
/performancereport optimization  # بهینه‌سازی‌ها
```

### گزارش کاربری:
```bash
/userreport                      # گزارش فعالیت کاربران
/userreport engagement           # میزان تعامل
/userreport satisfaction         # رضایت کاربران
```

---

## 🔧 تنظیمات گزارش‌دهی

### فرمت گزارش:
```bash
/reportformat text               # فرمت متنی
/reportformat json               # فرمت JSON
/reportformat csv                # فرمت CSV
/reportformat html               # فرمت HTML
```

### ارسال خودکار:
```bash
/autoreport daily                # ارسال روزانه
/autoreport weekly               # ارسال هفتگی
/autoreport custom               # زمان‌بندی دلخواه
```

### تنظیم هشدارها:
```bash
/alerts setup                    # راه‌اندازی هشدارها
/alerts threshold 80             # آستانه هشدار
/alerts email user@domain.com    # ارسال ایمیل
```

---

## 💡 نکات و ترفندها

### ۱. **استفاده بهینه از آمار:**
```bash
/status                          # نگاه کلی
/performance                     # عملکرد
/securitystats                   # امنیت
/dailyreport                     # خلاصه روز
```

### ۲. **مانیتورینگ مداوم:**
```bash
/autoreport daily                # گزارش خودکار
/alerts setup                    # هشدارهای خودکار
/monitor start                   # مانیتورینگ زنده
```

### ۳. **تحلیل مسائل:**
```bash
/bottlenecks                     # پیدا کردن مشکلات
/logs error                      # بررسی خطاها
/trendanalysis                   # روند مشکلات
```

### ۴. **بهبود عملکرد:**
```bash
/optimization                    # پیشنهادات بهبود
/benchmark                       # مقایسه با استاندارد
/efficiency                      # میزان کارایی
```

---

## ⚠️ هشدارها

### 🔴 **خطرناک:**
```bash
/clearlogs                       # همه لاگ‌ها پاک می‌شود
/resetstats                      # همه آمار پاک می‌شود
```

### 🟡 **احتیاط:**
```bash
/heavyreport                     # ممکن است سیستم را کند کند
/autoreport hourly               # ممکن است اسپم ایجاد کند
```

### 🟢 **امن:**
```bash
/status                          # همیشه امن
/dailyreport                     # امن و مفید
/performance                     # فقط نمایش
```

---

## 🆘 رفع مشکلات متداول

### مشکل: آمار نمایش داده نمی‌شود
```bash
/refresh stats                   # تازه‌سازی آمار
/sync stats                      # همگام‌سازی
/reload stats                    # بازخوانی
```

### مشکل: گزارش‌ها کامل نیست
```bash
/checkreports                    # بررسی گزارش‌ها
/repairreports                   # تعمیر گزارش‌ها
/fullreport                      # گزارش کامل
```

### مشکل: عملکرد کند
```bash
/optimize reports                # بهینه‌سازی گزارش‌ها
/cache clear                     # پاک کردن کش
/lightweight mode                # حالت سبک
```

---

## 📚 مثال‌های عملی

### سناریو ۱: بررسی روزانه
```bash
/status                          # شروع با وضعیت کلی
/dailyreport                     # گزارش روز
/securitystats                   # چک امنیت
/performance                     # بررسی عملکرد
```

### سناریو ۲: بررسی مشکل
```bash
/logs error                      # چک خطاها
/bottlenecks                     # پیدا کردن مشکل
/performance cpu                 # بررسی CPU
/systemhealth                    # سلامت کلی
```

### سناریو ۳: آماده‌سازی گزارش
```bash
/weeklyreport                    # گزارش هفته
/trendanalysis                   # تحلیل روند
/kpi                             # شاخص‌های کلیدی
/exportreport                    # صادرات گزارش
```

برای بازگشت به راهنمای کلی: `/help`