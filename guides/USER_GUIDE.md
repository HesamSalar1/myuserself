# 👥 راهنمای کامل مدیریت کاربران

## 🎯 نمای کلی

سیستم مدیریت کاربران شامل سه دسته اصلی: **ادمین‌ها**، **دوستان**، و **دشمنان** با امکان تنظیم رفتارهای مختلف برای هر گروه.

---

## 👑 مدیریت ادمین‌ها

### اضافه کردن ادمین:
```bash
/addadmin @username              # اضافه با نام کاربری
/addadmin 123456789              # اضافه با User ID
/addadmin @user1 @user2          # اضافه چندتایی
```

### حذف ادمین:
```bash
/deladmin @username              # حذف با نام کاربری
/deladmin 123456789              # حذف با User ID
/deladmin @user1 @user2          # حذف چندتایی
```

### مشاهده ادمین‌ها:
```bash
/listadmin                       # لیست همه ادمین‌ها
/listadmin detailed              # اطلاعات کامل
/admincount                      # تعداد ادمین‌ها
```

### سطوح ادمین:
```bash
/setadminlevel @username 1       # ادمین عادی
/setadminlevel @username 2       # ادمین ارشد
/setadminlevel @username 3       # سوپر ادمین
/admininfo @username             # بررسی سطح ادمین
```

---

## 🤝 مدیریت دوستان

### اضافه کردن دوست:
```bash
/addfriend @username             # اضافه با نام کاربری
/addfriend 123456789             # اضافه با User ID
/addfriend @user1 @user2 @user3  # اضافه چندتایی
```

### حذف دوست:
```bash
/delfriend @username             # حذف با نام کاربری
/delfriend 123456789             # حذف با User ID
/delfriend @user1 @user2         # حذف چندتایی
```

### مشاهده دوستان:
```bash
/listfriends                     # لیست همه دوستان
/listfriends 20                  # نمایش ۲۰ نفر اول
/listfriends online              # فقط آنلاین‌ها
/friendcount                     # تعداد دوستان
```

### دسته‌بندی دوستان:
```bash
/categorize @username VIP        # دسته‌بندی دوست
/addfriend @username group:gaming # اضافه به گروه
/friendgroups                    # لیست گروه‌های دوست
```

---

## ⚔️ مدیریت دشمنان

### اضافه کردن دشمن:
```bash
/addenemy @username              # اضافه با نام کاربری
/addenemy 123456789              # اضافه با User ID
/addenemy @spam1 @spam2          # اضافه چندتایی
```

### حذف دشمن:
```bash
/delenemy @username              # حذف با نام کاربری
/delenemy 123456789              # حذف با User ID
/delenemy @user1 @user2          # حذف چندتایی
```

### مشاهده دشمنان:
```bash
/listenemies                     # لیست همه دشمنان
/listenemies banned              # فقط بن‌شده‌ها
/listenemies recent              # اخیراً اضافه شده‌ها
/enemycount                      # تعداد دشمنان
```

### سطح تهدید:
```bash
/threatlevel @username 1         # تهدید کم
/threatlevel @username 2         # تهدید متوسط
/threatlevel @username 3         # تهدید بالا
/enemyinfo @username             # اطلاعات دشمن
```

---

## 🔍 کامندهای بررسی کاربر

### بررسی وضعیت کاربر:
```bash
/checkuser @username             # وضعیت کلی کاربر
/checkuser 123456789             # بررسی با ID
/usertype @username              # نوع کاربر (دوست/دشمن/عادی)
```

### اطلاعات تفصیلی:
```bash
/userinfo @username              # اطلاعات کامل
/userinfo 123456789              # اطلاعات با ID
/userstats @username             # آمار فعالیت کاربر
```

### تاریخچه فعالیت:
```bash
/userhistory @username           # تاریخچه فعالیت
/userhistory @username 7d        # ۷ روز اخیر
/userhistory @username detailed  # تاریخچه مفصل
```

---

## ⚙️ تنظیمات رفتار

### رفتار با دوستان:
```bash
/friendbehavior reply            # پاسخ‌دهی به دوستان
/friendbehavior priority         # اولویت به دوستان
/friendbehavior fast             # پاسخ سریع
/friendbehavior normal           # رفتار عادی
```

### رفتار با دشمنان:
```bash
/enemybehavior ignore            # نادیده گرفتن دشمنان
/enemybehavior slow              # پاسخ آهسته
/enemybehavior block             # مسدود کردن
/enemybehavior report            # گزارش خودکار
```

### رفتار با کاربران عادی:
```bash
/defaultbehavior normal          # رفتار عادی
/defaultbehavior cautious        # رفتار محتاط
/defaultbehavior friendly        # رفتار دوستانه
```

---

## 🔄 کامندهای مدیریت گروهی

### عملیات گروهی:
```bash
/bulkaction friends "action"     # عملیات روی همه دوستان
/bulkaction enemies "action"     # عملیات روی همه دشمنان
/massupdate group:gaming fast    # بروزرسانی گروهی
```

### انتقال بین دسته‌ها:
```bash
/promote @username               # ارتقا به دوست
/demote @username                # تنزل به عادی
/ban @username                   # تبدیل به دشمن
/unban @username                 # حذف از دشمنان
```

### سینک کاربران:
```bash
/syncusers                       # سینک همه کاربران
/syncusers friends               # سینک فقط دوستان
/syncusers enemies               # سینک فقط دشمنان
```

---

## 📊 آمار و گزارش‌گیری

### آمار کلی:
```bash
/userstats                       # آمار کل کاربران
/userstats detailed              # آمار تفصیلی
/userstats summary               # خلاصه آمار
```

### آمار فعالیت:
```bash
/activitystats                   # آمار فعالیت کاربران
/activitystats friends           # فعالیت دوستان
/activitystats enemies           # فعالیت دشمنان
```

### گزارش‌های زمانی:
```bash
/dailyusers                      # گزارش روزانه کاربران
/weeklyusers                     # گزارش هفتگی
/monthlyusers                    # گزارش ماهانه
```

### تحلیل رفتار:
```bash
/behavioranalysis                # تحلیل رفتار کاربران
/patternanalysis                 # تحلیل الگوهای رفتاری
/riskanalysis                    # تحلیل ریسک کاربران
```

---

## 🎯 سیستم امتیازدهی

### امتیاز کاربران:
```bash
/userscore @username             # امتیاز کاربر
/setscore @username 85           # تنظیم امتیاز
/topscore                        # بالاترین امتیازها
/lowscore                        # پایین‌ترین امتیازها
```

### سیستم کارما:
```bash
/karma @username                 # کارمای کاربر
/addkarma @username 10           # اضافه کردن کارما
/reducekarma @username 5         # کاهش کارما
/karmareset @username            # بازنشانی کارما
```

### سیستم اعتماد:
```bash
/trustlevel @username            # سطح اعتماد
/settrust @username high         # تنظیم سطح اعتماد
/trustlist                       # لیست قابل اعتماد
```

---

## 🔒 امنیت و محافظت

### تشخیص رفتار مشکوک:
```bash
/suspicious                      # کاربران مشکوک
/suspicious @username            # بررسی کاربر خاص
/autodetect on                   # تشخیص خودکار
```

### سیستم هشدار:
```bash
/warning @username "دلیل"        # ارسال هشدار
/warnings @username              # لیست هشدارهای کاربر
/clearwarnings @username         # پاک کردن هشدارها
```

### محافظت پیشرفته:
```bash
/protection high                 # سطح محافظت بالا
/whitelist @username             # اضافه به لیست سفید
/blacklist @username             # اضافه به لیست سیاه
```

---

## 📋 کامندهای پشتیبان‌گیری

### پشتیبان کاربران:
```bash
/backupusers                     # پشتیبان همه کاربران
/backupusers friends             # پشتیبان فقط دوستان
/restoreusers                    # بازگردانی پشتیبان
```

### صادرات/وارد کردن:
```bash
/exportusers                     # صادرات لیست کاربران
/exportusers friends.txt         # صادرات دوستان
/importusers file.txt            # وارد کردن از فایل
```

### آرشیو:
```bash
/archiveuser @username           # آرشیو کاربر
/unarchiveuser @username         # خروج از آرشیو
/listarchived                    # لیست آرشیو شده‌ها
```

---

## 💡 نکات و ترفندها

### ۱. **مدیریت سریع:**
```bash
# اضافه کردن گروهی
/addfriend @user1 @user2 @user3 @user4

# بهتر از:
/addfriend @user1
/addfriend @user2
/addfriend @user3
```

### ۲. **استفاده از ID بهتر از username:**
```bash
/addfriend 123456789             # قطعی و سریع
/addfriend @username             # ممکن است تغییر کند
```

### ۳. **دسته‌بندی هوشمند:**
```bash
/addfriend @gamer1 group:gaming
/addfriend @admin1 group:staff
/addfriend @vip1 group:premium
```

### ۴. **استفاده از bulk operations:**
```bash
/bulkaction group:gaming priority
/massupdate enemies ignore
```

---

## ⚠️ هشدارها

### 🔴 **خطرناک:**
```bash
/clearallusers                   # همه کاربران پاک می‌شود!
/bulkaction all delete           # همه پاک می‌شود!
```

### 🟡 **احتیاط:**
```bash
/addenemy @username              # مطمئن شوید کاربر واقعاً دشمن است
/bulkaction enemies block        # همه دشمنان مسدود می‌شوند
```

### 🟢 **امن:**
```bash
/listfriends                     # همیشه امن
/checkuser                       # فقط بررسی
/userstats                       # فقط آمار
```

---

## 🆘 رفع مشکلات متداول

### مشکل: کاربر اضافه نمی‌شود
```bash
/checkuser @username             # ابتدا بررسی کنید
/userinfo @username              # اطلاعات کاربر
# مطمئن شوید username یا ID درست باشد
```

### مشکل: رفتار درست اعمال نمی‌شود
```bash
/syncusers                       # سینک کاربران
/checkuser @username             # بررسی وضعیت
/friendbehavior check            # بررسی تنظیمات رفتار
```

### مشکل: لیست کاربران خالی است
```bash
/reloadusers                     # بازخوانی کاربران
/backupusers                     # چک کردن پشتیبان
/importusers backup.txt          # بازگردانی از پشتیبان
```

---

## 📚 مثال‌های عملی

### سناریو ۱: راه‌اندازی تیم مدیریت
```bash
/addadmin @mainmanager           # مدیر اصلی
/setadminlevel @mainmanager 3    # سطح بالا
/addadmin @helper1 @helper2      # کمک‌کارها
/setadminlevel @helper1 1        # سطح پایین
```

### سناریو ۲: مدیریت اعضای VIP
```bash
/addfriend @vip1 @vip2 @vip3     # اضافه VIP ها
/categorize @vip1 VIP            # دسته‌بندی
/friendbehavior priority         # اولویت بالا
/settrust @vip1 high             # اعتماد بالا
```

### سناریو ۳: مقابله با اسپمر
```bash
/checkuser @spammer              # بررسی کاربر
/addenemy @spammer               # اضافه به دشمنان
/threatlevel @spammer 3          # سطح تهدید بالا
/enemybehavior block             # مسدود کردن
```

برای بازگشت به راهنمای کلی: `/help`