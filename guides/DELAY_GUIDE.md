# ⏱️ راهنمای کامل سیستم تاخیر پیشرفته

## 🎯 نمای کلی

سیستم تاخیر پیشرفته با ۶ نوع تاخیر مختلف، تاخیر انطباقی، و ضریب‌های مختص هر چت برای کنترل کامل سرعت واکنش بات‌ها.

---

## 🎛️ انواع تاخیر

### ۱. تاخیر اسپم دشمنان (enemy_spam)
```bash
/setdelay enemy_spam 2.5     # تاخیر برای پیام‌های اسپم دشمنان
/setdelay enemy_spam 1.0     # حالت پیش‌فرض
/setdelay enemy_spam 5.0     # تاخیر زیاد برای کنترل بیشتر
```

### ۲. تاخیر پاسخ به دوستان (friend_reply)
```bash
/setdelay friend_reply 0.3   # پاسخ سریع به دوستان
/setdelay friend_reply 0.1   # پاسخ فوری
/setdelay friend_reply 0.5   # پاسخ آهسته‌تر
```

### ۳. تاخیر پیام‌های کلی (global_msg)
```bash
/setdelay global_msg 0.5     # تاخیر کلی همه پیام‌ها
/setdelay global_msg 0.2     # سریع
/setdelay global_msg 1.0     # آهسته
```

### ۴. تاخیر گفتگوی خودکار (conversation)
```bash
/setdelay conversation 2.0   # گفتگوی طبیعی
/setdelay conversation 1.5   # سریع‌تر
/setdelay conversation 3.0   # آهسته‌تر و طبیعی‌تر
```

### ۵. تاخیر واکنش ایموجی (emoji_react)
```bash
/setdelay emoji_react 0.1    # واکنش سریع به ایموجی ممنوعه
/setdelay emoji_react 0.05   # فوری (توصیه شده)
/setdelay emoji_react 0.2    # آهسته‌تر
```

### ۶. تاخیر محافظت از سیل (burst_protect)
```bash
/setdelay burst_protect 3.0  # محافظت از سیل پیام
/setdelay burst_protect 2.0  # سریع‌تر
/setdelay burst_protect 5.0  # محافظت قوی‌تر
```

---

## 🎯 نحوه استفاده صحیح کامندها

### ❌ **اشتباه - باعث خطا می‌شود:**
```bash
/setdelayenemy_spam2.5       # بدون فاصله
/setdelay enemy_spam2.5      # فاصله فقط قبل از نوع
/setdelayenemy_spam 2.5      # فاصله فقط قبل از مقدار
```

### ✅ **درست - کار می‌کند:**
```bash
/setdelay enemy_spam 2.5     # فاصله بین همه قسمت‌ها
/setdelay friend_reply 0.3   # فاصله کامل
/setdelay global_msg 0.5     # فرمت صحیح
```

### 📝 **نکات مهم فرمت:**
- همیشه بین `/setdelay` و نوع تاخیر فاصله بگذارید
- همیشه بین نوع تاخیر و مقدار فاصله بگذارید
- مقدار باید عدد باشد (اعشاری یا صحیح)
- مقدار بین 0.01 تا 30.0 ثانیه مجاز است

---

## 🏠 ضریب‌های مختص چت

### تنظیم ضریب چت:
```bash
/chatdelay -1001234567890 0.5    # نصف تاخیر برای این چت
/chatdelay -1001234567890 1.0    # تاخیر عادی
/chatdelay -1001234567890 2.0    # دو برابر تاخیر
/chatdelay -1001234567890 0.1    # فوری (حداقل تاخیر)
```

### مثال‌های کاربردی:
```bash
# چت VIP - واکنش سریع
/chatdelay -1001111111111 0.3

# چت عمومی - واکنش عادی  
/chatdelay -1002222222222 1.0

# چت مشکل‌دار - واکنش آهسته
/chatdelay -1003333333333 2.5
```

### نحوه پیدا کردن Chat ID:
```bash
/chatstats                       # لیست تمام چت‌ها با ID
/thisChat                        # ID چت فعلی
```

---

## 📊 مدیریت و مشاهده

### نمایش تنظیمات فعلی:
```bash
/delayinfo                       # همه تنظیمات تاخیر
/delayinfo detailed              # جزئیات کامل
/delayinfo chat                  # فقط ضریب‌های چت
```

### بازنشانی تنظیمات:
```bash
/resetdelay                      # بازنشانی همه تاخیرها
/resetdelay confirm              # تایید بازنشانی
/resetdelay chat                 # فقط ضریب‌های چت
```

### آمار تاخیر:
```bash
/delaystats                      # آمار استفاده تاخیرها
/delaytest                       # تست سرعت واکنش
/delayperformance                # تحلیل عملکرد
```

---

## 🧠 سیستم تاخیر انطباقی

### ویژگی‌های هوشمند:
- **چت خلوت:** تاخیر ۳۰-۵۰% کمتر در چت‌های کم‌فعال
- **چت پرترافیک:** تاخیر عادی در چت‌های پرفعال
- **واکنش اضطراری:** حداکثر ۰.۱ ثانیه برای ایموجی‌های ممنوعه

### تنظیمات انطباقی:
```bash
/adaptive on                     # فعال کردن تاخیر انطباقی
/adaptive off                    # غیرفعال کردن
/adaptive smart                  # حالت هوشمند (پیشنهادی)
```

### کنترل کاهش هوشمند:
```bash
/smartreduction on               # فعال کردن کاهش هوشمند
/smartreduction off              # غیرفعال کردن
/smartreduction auto             # حالت خودکار
```

---

## 📈 بهینه‌سازی عملکرد

### تنظیمات پیشنهادی برای چت‌های مختلف:

#### 🎮 **چت‌های گیم (پرسرعت):**
```bash
/setdelay enemy_spam 1.0
/setdelay friend_reply 0.2
/setdelay emoji_react 0.05
/setdelay global_msg 0.3
```

#### 💬 **چت‌های عمومی (متعادل):**
```bash
/setdelay enemy_spam 2.0
/setdelay friend_reply 0.4
/setdelay emoji_react 0.1
/setdelay global_msg 0.6
```

#### 🏢 **چت‌های رسمی (آهسته):**
```bash
/setdelay enemy_spam 3.0
/setdelay friend_reply 0.8
/setdelay emoji_react 0.2
/setdelay global_msg 1.0
```

### پروفایل‌های آماده:
```bash
/loadprofile gaming              # پروفایل گیمینگ
/loadprofile balanced            # پروفایل متعادل
/loadprofile conservative        # پروفایل محافظه‌کارانه
/saveprofile myprofile           # ذخیره پروفایل شخصی
```

---

## 🔧 تنظیمات پیشرفته

### حد تاخیرها:
```bash
/setlimits min 0.01              # حداقل تاخیر
/setlimits max 30.0              # حداکثر تاخیر
/setlimits emergency 0.05        # تاخیر اضطراری
```

### تنظیمات ایموجی اضطراری:
```bash
/emergency emoji_react 0.03      # تاخیر فوری برای ایموجی
/emergency burst_protect 1.0     # حفاظت سریع از سیل
```

### پیکربندی چندچته:
```bash
/bulkdelay "chat1,chat2" 0.5     # تنظیم برای چند چت
/bulkprofile gaming "chat1,chat2" # اعمال پروفایل برای چند چت
```

---

## 📊 مانیتورینگ و آمار

### آمار لحظه‌ای:
```bash
/realtime                        # آمار زنده تاخیرها
/monitor start                   # شروع مانیتورینگ
/monitor stop                    # توقف مانیتورینگ
```

### گزارش‌های تحلیلی:
```bash
/delayreport daily               # گزارش روزانه
/delayreport weekly              # گزارش هفتگی
/delayreport custom 7d           # گزارش ۷ روز اخیر
```

### تحلیل عملکرد:
```bash
/analyze performance             # تحلیل عملکرد کلی
/analyze bottleneck              # تشخیص گلوگاه‌ها
/analyze optimization            # پیشنهاد بهینه‌سازی
```

---

## 🧪 تست و عیب‌یابی

### تست‌های سرعت:
```bash
/speedtest delay                 # تست سرعت تاخیرها
/speedtest realworld             # تست در شرایط واقعی
/benchmark                       # معیارسنجی کامل
```

### دیباگ مسائل:
```bash
/debugdelay on                   # فعال کردن دیباگ
/debugdelay specific enemy_spam  # دیباگ تاخیر خاص
/debugdelay chat -1001234567890  # دیباگ چت خاص
```

### شبیه‌سازی:
```bash
/simulate load                   # شبیه‌سازی بار بالا
/simulate burst                  # شبیه‌سازی سیل پیام
/simulate mixed                  # شبیه‌سازی ترافیک مختلط
```

---

## 💡 نکات و ترفندها

### ۱. **شروع بهینه:**
```bash
/delayinfo                       # ببینید چی دارید
/loadprofile balanced            # شروع با پروفایل متعادل
/delaytest                       # تست کنید
```

### ۲. **بهبود تدریجی:**
```bash
/analyze optimization            # پیشنهادات دریافت کنید
# تنظیمات را تدریجی تغییر دهید
/delaytest                       # مجدداً تست کنید
```

### ۳. **مدیریت بحران:**
```bash
/emergency                       # حالت اضطراری
/loadprofile conservative        # پروفایل محافظه‌کارانه
```

### ۴. **بکاپ تنظیمات:**
```bash
/saveprofile backup_$(date +%Y%m%d)
/export delays                   # صادرات تنظیمات
```

---

## ⚠️ هشدارها

### 🔴 **خطرناک:**
```bash
/setdelay emoji_react 5.0        # خیلی آهسته برای امنیت
/resetdelay                      # تمام تنظیمات پاک می‌شود
```

### 🟡 **احتیاط:**
```bash
/setdelay enemy_spam 0.1         # ممکن است خیلی سریع باشد
/chatdelay -1001234567890 0.05   # ممکن است اسپم محسوب شود
```

### 🟢 **امن:**
```bash
/delayinfo                       # همیشه امن
/delaytest                       # فقط تست
/loadprofile balanced            # پروفایل امن
```

---

## 🆘 رفع مشکلات متداول

### مشکل: "❌ مقدار تاخیر باید عدد باشد"
```bash
# اشتباه:
/setdelay enemy_spam2.5          # فاصله نداره
/setdelayenemy_spam 2.5          # اینم فاصله نداره

# درست:
/setdelay enemy_spam 2.5         # فاصله کامل
```

### مشکل: تاخیر اعمال نمی‌شود
```bash
/sync                            # سینک همه بات‌ها
/reload                          # بازخوانی تنظیمات
/delayinfo                       # چک کردن تنظیمات
```

### مشکل: عملکرد کند
```bash
/analyze bottleneck              # پیدا کردن مشکل
/optimize                        # بهینه‌سازی خودکار
/cache clear                     # پاک کردن کش
```

---

## 📚 مثال‌های عملی

### سناریو ۱: راه‌اندازی چت گیم
```bash
/delayinfo                       # وضعیت فعلی
/loadprofile gaming              # بار کردن پروفایل گیم
/chatdelay -1001234567890 0.3    # ضریب چت گیم
/delaytest                       # تست عملکرد
```

### سناریو ۲: کنترل اسپم
```bash
/setdelay enemy_spam 3.0         # تاخیر بیشتر برای اسپم
/setdelay burst_protect 5.0      # محافظت قوی از سیل
/adaptive on                     # تاخیر انطباقی
```

### سناریو ۳: عیب‌یابی مشکل
```bash
/debugdelay on                   # فعال کردن دیباگ
/monitor start                   # شروع مانیتورینگ
# مشاهده مشکل
/analyze bottleneck              # تشخیص علت
```

برای بازگشت به راهنمای کلی: `/help`