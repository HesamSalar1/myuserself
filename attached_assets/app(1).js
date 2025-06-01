
// اسکریپت‌های جاوااسکریپت برای پنل مدیریت

document.addEventListener('DOMContentLoaded', function() {
    // ایجاد تایمر برای حذف خودکار پیام‌های هشدار
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // اضافه کردن تأیید برای عملیات‌های حذف
    const deleteLinks = document.querySelectorAll('a[href*="delete"]');
    deleteLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            if (!confirm('آیا مطمئن هستید که می‌خواهید این مورد را حذف کنید?')) {
                e.preventDefault();
            }
        });
    });

    // شمارنده کاراکتر برای textarea ها
    const textareas = document.querySelectorAll('textarea[maxlength]');
    textareas.forEach(function(textarea) {
        const maxLength = textarea.getAttribute('maxlength');
        const counter = document.createElement('small');
        counter.className = 'text-muted float-left';
        counter.textContent = `0/${maxLength}`;
        textarea.parentNode.appendChild(counter);

        textarea.addEventListener('input', function() {
            const currentLength = this.value.length;
            counter.textContent = `${currentLength}/${maxLength}`;
            
            if (currentLength > maxLength * 0.9) {
                counter.className = 'text-warning float-left';
            } else if (currentLength === parseInt(maxLength)) {
                counter.className = 'text-danger float-left';
            } else {
                counter.className = 'text-muted float-left';
            }
        });
    });

    // بروزرسانی خودکار زمان
    function updateTime() {
        const timeElements = document.querySelectorAll('[data-time-update]');
        timeElements.forEach(function(element) {
            const now = new Date();
            element.textContent = now.toLocaleString('fa-IR');
        });
    }

    // بروزرسانی هر دقیقه
    setInterval(updateTime, 60000);

    // اضافه کردن loader برای فرم‌ها
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> در حال پردازش...';
            }
        });
    });

    // اضافه کردن tooltips برای عناصر
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // جستجوی آنی در جدول‌ها
    const searchInputs = document.querySelectorAll('.table-search');
    searchInputs.forEach(function(input) {
        input.addEventListener('keyup', function() {
            const filter = this.value.toLowerCase();
            const table = this.closest('.card').querySelector('table tbody');
            const rows = table.querySelectorAll('tr');

            rows.forEach(function(row) {
                const text = row.textContent.toLowerCase();
                if (text.includes(filter)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    });
});

// تابع برای حذف گروهی
function clearAll(tableName) {
    let confirmMessage = '';
    
    switch(tableName) {
        case 'fosh_list':
            confirmMessage = 'آیا مطمئن هستید که می‌خواهید همه فحش‌ها را حذف کنید؟';
            break;
        case 'enemy_list':
            confirmMessage = 'آیا مطمئن هستید که می‌خواهید همه دشمنان را حذف کنید؟';
            break;
        case 'friend_list':
            confirmMessage = 'آیا مطمئن هستید که می‌خواهید همه دوستان را حذف کنید؟';
            break;
        case 'friend_words':
            confirmMessage = 'آیا مطمئن هستید که می‌خواهید همه کلمات دوستانه را حذف کنید؟';
            break;
        default:
            confirmMessage = 'آیا مطمئن هستید؟';
    }
    
    if (confirm(confirmMessage + ' این عمل غیرقابل بازگشت است!')) {
        // نمایش loader
        const loadingAlert = document.createElement('div');
        loadingAlert.className = 'alert alert-info';
        loadingAlert.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> در حال حذف...';
        document.querySelector('main').insertBefore(loadingAlert, document.querySelector('main').firstChild);

        fetch('/api/clear_all', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({table: tableName})
        })
        .then(response => response.json())
        .then(data => {
            loadingAlert.remove();
            
            if (data.success) {
                // نمایش پیام موفقیت
                const successAlert = document.createElement('div');
                successAlert.className = 'alert alert-success alert-dismissible fade show';
                successAlert.innerHTML = `
                    ${data.message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                document.querySelector('main').insertBefore(successAlert, document.querySelector('main').firstChild);
                
                // بروزرسانی صفحه بعد از 1 ثانیه
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                // نمایش پیام خطا
                const errorAlert = document.createElement('div');
                errorAlert.className = 'alert alert-danger alert-dismissible fade show';
                errorAlert.innerHTML = `
                    خطا: ${data.message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                document.querySelector('main').insertBefore(errorAlert, document.querySelector('main').firstChild);
            }
        })
        .catch(error => {
            loadingAlert.remove();
            alert('خطا در اتصال به سرور: ' + error.message);
        });
    }
}

// تابع برای بروزرسانی آمار در زمان واقعی
function refreshStats() {
    fetch('/api/stats')
    .then(response => response.json())
    .then(data => {
        // بروزرسانی آمار در داشبورد
        const statElements = document.querySelectorAll('[data-stat]');
        statElements.forEach(element => {
            const statType = element.getAttribute('data-stat');
            if (data[statType] !== undefined) {
                element.textContent = data[statType];
            }
        });
    })
    .catch(error => {
        console.log('خطا در بروزرسانی آمار:', error);
    });
}

// بروزرسانی آمار هر 30 ثانیه
setInterval(refreshStats, 30000);

// تابع برای export کردن داده‌ها
function exportData(format) {
    const url = `/api/export?format=${format}`;
    window.open(url, '_blank');
}

// تابع برای backup دیتابیس
function backupDatabase() {
    if (confirm('آیا می‌خواهید از دیتابیس بکاپ تهیه کنید؟')) {
        fetch('/api/backup', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('بکاپ با موفقیت انجام شد: ' + data.filename);
            } else {
                alert('خطا در ایجاد بکاپ: ' + data.message);
            }
        });
    }
}
