-- اسکریپت راه‌اندازی اولیه پایگاه داده
-- Initial Database Setup Script

-- تنظیم encoding
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

-- ایجاد database در صورت عدم وجود
SELECT 'CREATE DATABASE telegram_bots'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'telegram_bots')\gexec

-- اتصال به database
\c telegram_bots;

-- ایجاد schema اصلی
CREATE SCHEMA IF NOT EXISTS public;

-- تنظیم مجوزها
GRANT ALL ON SCHEMA public TO telegram_user;
GRANT ALL ON SCHEMA public TO public;

-- ایجاد extension های لازم
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- تابع به‌روزرسانی timestamp
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- جدول کاربران سیستم
CREATE TABLE IF NOT EXISTS system_users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول تنظیمات ربات‌ها
CREATE TABLE IF NOT EXISTS bot_configs (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER UNIQUE NOT NULL,
    api_id BIGINT NOT NULL,
    api_hash VARCHAR(255) NOT NULL,
    session_name VARCHAR(255) NOT NULL,
    admin_id BIGINT NOT NULL,
    auto_reply_enabled BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول فحش‌ها
CREATE TABLE IF NOT EXISTS fosh_list (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER NOT NULL,
    fosh TEXT NOT NULL,
    media_type VARCHAR(50),
    file_id VARCHAR(255),
    created_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bot_id) REFERENCES bot_configs(bot_id) ON DELETE CASCADE
);

-- جدول دشمنان
CREATE TABLE IF NOT EXISTS enemy_list (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER NOT NULL,
    user_id BIGINT NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    added_by BIGINT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bot_id, user_id),
    FOREIGN KEY (bot_id) REFERENCES bot_configs(bot_id) ON DELETE CASCADE
);

-- جدول دوستان
CREATE TABLE IF NOT EXISTS friend_list (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER NOT NULL,
    user_id BIGINT NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    added_by BIGINT,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bot_id, user_id),
    FOREIGN KEY (bot_id) REFERENCES bot_configs(bot_id) ON DELETE CASCADE
);

-- جدول ایموجی‌های ممنوعه
CREATE TABLE IF NOT EXISTS forbidden_emojis (
    id SERIAL PRIMARY KEY,
    emoji VARCHAR(10) UNIQUE NOT NULL,
    description TEXT,
    added_by BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول لاگ‌های سیستم
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    extra_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_system_logs_bot_id (bot_id),
    INDEX idx_system_logs_level (level),
    INDEX idx_system_logs_created_at (created_at)
);

-- جدول آمار کاربری
CREATE TABLE IF NOT EXISTS user_stats (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER NOT NULL,
    user_id BIGINT NOT NULL,
    messages_count INTEGER DEFAULT 0,
    commands_count INTEGER DEFAULT 0,
    last_activity TIMESTAMP,
    total_activity_time INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bot_id, user_id),
    FOREIGN KEY (bot_id) REFERENCES bot_configs(bot_id) ON DELETE CASCADE
);

-- جدول sessions
CREATE TABLE IF NOT EXISTS bot_sessions (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER UNIQUE NOT NULL,
    session_data BYTEA,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bot_id) REFERENCES bot_configs(bot_id) ON DELETE CASCADE
);

-- جدول پیام‌های برنامه‌ریزی شده
CREATE TABLE IF NOT EXISTS scheduled_messages (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER NOT NULL,
    chat_id BIGINT NOT NULL,
    message_text TEXT,
    media_type VARCHAR(50),
    file_id VARCHAR(255),
    scheduled_time TIMESTAMP NOT NULL,
    is_sent BOOLEAN DEFAULT FALSE,
    repeat_interval INTEGER, -- minutes
    created_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bot_id) REFERENCES bot_configs(bot_id) ON DELETE CASCADE
);

-- جدول مانیتورینگ
CREATE TABLE IF NOT EXISTS monitoring_data (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,2),
    metric_unit VARCHAR(20),
    bot_id INTEGER,
    additional_data JSONB,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_monitoring_metric_name (metric_name),
    INDEX idx_monitoring_bot_id (bot_id),
    INDEX idx_monitoring_recorded_at (recorded_at)
);

-- جدول بک‌آپ‌ها
CREATE TABLE IF NOT EXISTS backups (
    id SERIAL PRIMARY KEY,
    backup_name VARCHAR(255) NOT NULL,
    backup_type VARCHAR(50) NOT NULL, -- full, partial, database
    file_path TEXT,
    file_size BIGINT,
    backup_status VARCHAR(20) DEFAULT 'in_progress', -- in_progress, completed, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- ایجاد trigger ها برای update timestamp
CREATE TRIGGER update_system_users_modified 
    BEFORE UPDATE ON system_users 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_bot_configs_modified 
    BEFORE UPDATE ON bot_configs 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_user_stats_modified 
    BEFORE UPDATE ON user_stats 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_bot_sessions_modified 
    BEFORE UPDATE ON bot_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- ایجاد index های بهینه‌سازی
CREATE INDEX IF NOT EXISTS idx_fosh_list_bot_id ON fosh_list(bot_id);
CREATE INDEX IF NOT EXISTS idx_enemy_list_bot_user ON enemy_list(bot_id, user_id);
CREATE INDEX IF NOT EXISTS idx_friend_list_bot_user ON friend_list(bot_id, user_id);
CREATE INDEX IF NOT EXISTS idx_user_stats_bot_user ON user_stats(bot_id, user_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_time ON scheduled_messages(scheduled_time) WHERE NOT is_sent;
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(created_at);

-- داده‌های اولیه - پیش‌فرض ایموجی‌های ممنوعه
INSERT INTO forbidden_emojis (emoji, description) VALUES
('🍌', 'موز - ایموجی ممنوعه پیش‌فرض'),
('🍆', 'بادمجان - ایموجی ممنوعه پیش‌فرض'),
('🍑', 'گیلاس - ایموجی ممنوعه پیش‌فرض'),
('💦', 'قطرات آب - ایموجی ممنوعه پیش‌فرض')
ON CONFLICT (emoji) DO NOTHING;

-- تنظیم مجوزهای نهایی
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO telegram_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO telegram_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO telegram_user;

-- پیام تایید
SELECT 'Database initialization completed successfully!' as status;