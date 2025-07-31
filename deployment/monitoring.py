#!/usr/bin/env python3
"""
سیستم مانیتورینگ پیشرفته برای ربات‌های تلگرام
Advanced Monitoring System for Telegram Bots
"""

import os
import sys
import time
import json
import asyncio
import logging
import psutil
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class BotStatus:
    """وضعیت یک ربات"""
    bot_id: int
    is_running: bool
    pid: Optional[int]
    cpu_percent: float
    memory_mb: float
    uptime_seconds: int
    last_activity: Optional[datetime]
    error_count: int
    restart_count: int
    status: str  # running, stopped, error, restarting

@dataclass
class SystemMetrics:
    """متریک‌های سیستم"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_sent_mb: float
    network_recv_mb: float
    load_average: List[float]
    active_bots: int
    total_bots: int

class BotMonitor:
    """کلاس مانیتورینگ ربات‌ها"""
    
    def __init__(self, config_path: str = "/home/telegrambot/telegram-bots"):
        self.config_path = config_path
        self.db_path = os.path.join(config_path, "monitoring.db")
        self.log_path = os.path.join(config_path, "monitoring.log")
        
        # تنظیم لاگینگ
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_path, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # راه‌اندازی دیتابیس
        self.init_database()
        
        # متغیرهای مانیتورینگ
        self.bot_processes: Dict[int, psutil.Process] = {}
        self.bot_stats: Dict[int, BotStatus] = {}
        self.last_network_io = None
        self.monitoring = False
        
        # تنظیمات آلارم
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'bot_restart_count': 5,
            'bot_error_count': 10
        }
        
    def init_database(self):
        """راه‌اندازی دیتابیس مانیتورینگ"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول متریک‌های سیستم
        cursor.execute('''CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            cpu_percent REAL,
            memory_percent REAL,
            disk_percent REAL,
            network_sent_mb REAL,
            network_recv_mb REAL,
            load_avg_1m REAL,
            load_avg_5m REAL,
            load_avg_15m REAL,
            active_bots INTEGER,
            total_bots INTEGER
        )''')
        
        # جدول وضعیت ربات‌ها
        cursor.execute('''CREATE TABLE IF NOT EXISTS bot_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            bot_id INTEGER,
            is_running BOOLEAN,
            pid INTEGER,
            cpu_percent REAL,
            memory_mb REAL,
            uptime_seconds INTEGER,
            last_activity DATETIME,
            error_count INTEGER,
            restart_count INTEGER,
            status TEXT
        )''')
        
        # جدول رویدادها و آلارم‌ها
        cursor.execute('''CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT,
            bot_id INTEGER,
            severity TEXT,
            message TEXT,
            details TEXT
        )''')
        
        # جدول آمار کلی
        cursor.execute('''CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE,
            bot_id INTEGER,
            uptime_minutes INTEGER,
            restart_count INTEGER,
            error_count INTEGER,
            messages_processed INTEGER,
            avg_cpu_percent REAL,
            avg_memory_mb REAL
        )''')
        
        conn.commit()
        conn.close()
        
    def find_bot_processes(self):
        """یافتن پروسه‌های ربات‌ها"""
        bot_processes = {}
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                if proc.info['name'] in ['python', 'python3']:
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    
                    # تشخیص ربات از روی command line
                    if 'bot' in cmdline.lower() and ('main.py' in cmdline or 'unified' in cmdline):
                        # استخراج شماره ربات
                        bot_id = None
                        
                        if 'unified_bot_launcher.py' in cmdline:
                            # این پروسه مدیر کل است
                            bot_id = 0
                        else:
                            # تلاش برای استخراج شماره ربات از مسیر
                            for part in cmdline.split():
                                if 'bot' in part and any(char.isdigit() for char in part):
                                    import re
                                    match = re.search(r'bot(\d+)', part)
                                    if match:
                                        bot_id = int(match.group(1))
                                        break
                        
                        if bot_id is not None:
                            bot_processes[bot_id] = psutil.Process(proc.info['pid'])
                            
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
        return bot_processes
    
    def get_bot_status(self, bot_id: int, process: Optional[psutil.Process] = None) -> BotStatus:
        """دریافت وضعیت یک ربات"""
        
        if process and process.is_running():
            try:
                # محاسبه uptime
                create_time = process.create_time()
                uptime_seconds = int(time.time() - create_time)
                
                # دریافت آمار CPU و حافظه
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                
                # خواندن آمار از دیتابیس
                error_count, restart_count = self.get_bot_stats_from_db(bot_id)
                
                return BotStatus(
                    bot_id=bot_id,
                    is_running=True,
                    pid=process.pid,
                    cpu_percent=cpu_percent,
                    memory_mb=memory_mb,
                    uptime_seconds=uptime_seconds,
                    last_activity=datetime.now(),
                    error_count=error_count,
                    restart_count=restart_count,
                    status="running"
                )
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # ربات در حال اجرا نیست
        error_count, restart_count = self.get_bot_stats_from_db(bot_id)
        
        return BotStatus(
            bot_id=bot_id,
            is_running=False,
            pid=None,
            cpu_percent=0.0,
            memory_mb=0.0,
            uptime_seconds=0,
            last_activity=None,
            error_count=error_count,
            restart_count=restart_count,
            status="stopped"
        )
    
    def get_bot_stats_from_db(self, bot_id: int) -> tuple:
        """دریافت آمار ربات از دیتابیس"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # آمار از جدول رویدادها
        cursor.execute('''
            SELECT COUNT(*) FROM events 
            WHERE bot_id = ? AND event_type = 'error' 
            AND timestamp > datetime('now', '-1 day')
        ''', (bot_id,))
        error_count = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM events 
            WHERE bot_id = ? AND event_type = 'restart' 
            AND timestamp > datetime('now', '-1 day')
        ''', (bot_id,))
        restart_count = cursor.fetchone()[0]
        
        conn.close()
        return error_count, restart_count
    
    def get_system_metrics(self) -> SystemMetrics:
        """دریافت متریک‌های سیستم"""
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # حافظه
        memory = psutil.virtual_memory()
        
        # دیسک
        disk = psutil.disk_usage('/')
        
        # شبکه
        net_io = psutil.net_io_counters()
        network_sent_mb = net_io.bytes_sent / 1024 / 1024
        network_recv_mb = net_io.bytes_recv / 1024 / 1024
        
        # Load Average (فقط در Linux)
        try:
            load_avg = os.getloadavg()
        except AttributeError:
            load_avg = [0.0, 0.0, 0.0]
        
        # تعداد ربات‌های فعال
        active_bots = len([status for status in self.bot_stats.values() if status.is_running])
        
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=disk.percent,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            load_average=list(load_avg),
            active_bots=active_bots,
            total_bots=9
        )
    
    def save_metrics_to_db(self, metrics: SystemMetrics):
        """ذخیره متریک‌ها در دیتابیس"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # ذخیره متریک‌های سیستم
        cursor.execute('''INSERT INTO system_metrics 
            (cpu_percent, memory_percent, disk_percent, network_sent_mb, network_recv_mb,
             load_avg_1m, load_avg_5m, load_avg_15m, active_bots, total_bots)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (metrics.cpu_percent, metrics.memory_percent, metrics.disk_percent,
             metrics.network_sent_mb, metrics.network_recv_mb,
             metrics.load_average[0], metrics.load_average[1], metrics.load_average[2],
             metrics.active_bots, metrics.total_bots))
        
        # ذخیره وضعیت ربات‌ها
        for bot_status in self.bot_stats.values():
            cursor.execute('''INSERT INTO bot_status 
                (bot_id, is_running, pid, cpu_percent, memory_mb, uptime_seconds,
                 last_activity, error_count, restart_count, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (bot_status.bot_id, bot_status.is_running, bot_status.pid,
                 bot_status.cpu_percent, bot_status.memory_mb, bot_status.uptime_seconds,
                 bot_status.last_activity, bot_status.error_count, 
                 bot_status.restart_count, bot_status.status))
        
        conn.commit()
        conn.close()
    
    def check_alerts(self, metrics: SystemMetrics):
        """بررسی آلارم‌ها"""
        alerts = []
        
        # آلارم CPU
        if metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
            alerts.append({
                'type': 'cpu_high',
                'severity': 'warning',
                'message': f'CPU usage is high: {metrics.cpu_percent:.1f}%'
            })
        
        # آلارم حافظه
        if metrics.memory_percent > self.alert_thresholds['memory_percent']:
            alerts.append({
                'type': 'memory_high',
                'severity': 'warning', 
                'message': f'Memory usage is high: {metrics.memory_percent:.1f}%'
            })
        
        # آلارم دیسک
        if metrics.disk_percent > self.alert_thresholds['disk_percent']:
            alerts.append({
                'type': 'disk_high',
                'severity': 'critical',
                'message': f'Disk usage is high: {metrics.disk_percent:.1f}%'
            })
        
        # آلارم ربات‌های متوقف شده
        stopped_bots = [bot for bot in self.bot_stats.values() if not bot.is_running]
        if stopped_bots:
            alerts.append({
                'type': 'bots_stopped',
                'severity': 'critical',
                'message': f'{len(stopped_bots)} bots are stopped: {[bot.bot_id for bot in stopped_bots]}'
            })
        
        # آلارم ری‌استارت زیاد
        high_restart_bots = [bot for bot in self.bot_stats.values() 
                           if bot.restart_count > self.alert_thresholds['bot_restart_count']]
        if high_restart_bots:
            for bot in high_restart_bots:
                alerts.append({
                    'type': 'high_restarts',
                    'severity': 'warning',
                    'bot_id': bot.bot_id,
                    'message': f'Bot {bot.bot_id} has high restart count: {bot.restart_count}'
                })
        
        # ذخیره آلارم‌ها
        if alerts:
            self.save_alerts(alerts)
            self.logger.warning(f"Generated {len(alerts)} alerts")
        
        return alerts
    
    def save_alerts(self, alerts: List[Dict]):
        """ذخیره آلارم‌ها در دیتابیس"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for alert in alerts:
            cursor.execute('''INSERT INTO events 
                (event_type, bot_id, severity, message, details)
                VALUES (?, ?, ?, ?, ?)''',
                (alert['type'], alert.get('bot_id'), alert['severity'], 
                 alert['message'], json.dumps(alert)))
        
        conn.commit()
        conn.close()
    
    def generate_report(self, hours: int = 24) -> Dict[str, Any]:
        """تولید گزارش"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        
        # آمار کلی سیستم
        cursor.execute('''SELECT 
            AVG(cpu_percent), AVG(memory_percent), AVG(disk_percent),
            AVG(active_bots), COUNT(*)
            FROM system_metrics 
            WHERE timestamp > ?''', (since,))
        
        system_stats = cursor.fetchone()
        
        # آمار ربات‌ها
        cursor.execute('''SELECT bot_id, 
            AVG(cpu_percent), AVG(memory_mb), 
            SUM(CASE WHEN is_running THEN 1 ELSE 0 END) as uptime_count,
            COUNT(*) as total_count
            FROM bot_status 
            WHERE timestamp > ?
            GROUP BY bot_id
            ORDER BY bot_id''', (since,))
        
        bot_stats = cursor.fetchall()
        
        # رویدادها و آلارم‌ها
        cursor.execute('''SELECT event_type, severity, COUNT(*) 
            FROM events 
            WHERE timestamp > ?
            GROUP BY event_type, severity
            ORDER BY COUNT(*) DESC''', (since,))
        
        events_stats = cursor.fetchall()
        
        conn.close()
        
        # تولید گزارش
        report = {
            'period': f'{hours} hours',
            'generated_at': datetime.now().isoformat(),
            'system': {
                'avg_cpu_percent': round(system_stats[0] or 0, 2),
                'avg_memory_percent': round(system_stats[1] or 0, 2),
                'avg_disk_percent': round(system_stats[2] or 0, 2),
                'avg_active_bots': round(system_stats[3] or 0, 1),
                'data_points': system_stats[4] or 0
            },
            'bots': {},
            'events': {
                'by_type': {}
            }
        }
        
        # آمار ربات‌ها
        for bot_id, avg_cpu, avg_memory, uptime_count, total_count in bot_stats:
            uptime_percent = (uptime_count / total_count * 100) if total_count > 0 else 0
            
            report['bots'][bot_id] = {
                'avg_cpu_percent': round(avg_cpu or 0, 2),
                'avg_memory_mb': round(avg_memory or 0, 2),
                'uptime_percent': round(uptime_percent, 2),
                'data_points': total_count
            }
        
        # آمار رویدادها
        for event_type, severity, count in events_stats:
            if event_type not in report['events']['by_type']:
                report['events']['by_type'][event_type] = {}
            report['events']['by_type'][event_type][severity] = count
        
        return report
    
    async def monitor_loop(self, interval: int = 30):
        """حلقه اصلی مانیتورینگ"""
        self.monitoring = True
        self.logger.info(f"Starting monitoring loop with {interval}s interval")
        
        while self.monitoring:
            try:
                # یافتن پروسه‌های ربات
                self.bot_processes = self.find_bot_processes()
                
                # به‌روزرسانی وضعیت ربات‌ها
                for bot_id in range(1, 10):  # 9 ربات
                    process = self.bot_processes.get(bot_id)
                    self.bot_stats[bot_id] = self.get_bot_status(bot_id, process)
                
                # دریافت متریک‌های سیستم
                metrics = self.get_system_metrics()
                
                # ذخیره در دیتابیس
                self.save_metrics_to_db(metrics)
                
                # بررسی آلارم‌ها
                alerts = self.check_alerts(metrics)
                
                # لاگ وضعیت
                active_bots = [bot_id for bot_id, status in self.bot_stats.items() if status.is_running]
                self.logger.info(f"System: CPU {metrics.cpu_percent:.1f}%, "
                               f"RAM {metrics.memory_percent:.1f}%, "
                               f"Active bots: {len(active_bots)}/9")
                
                if alerts:
                    self.logger.warning(f"Generated {len(alerts)} alerts")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)
    
    def stop_monitoring(self):
        """توقف مانیتورینگ"""
        self.monitoring = False
        self.logger.info("Monitoring stopped")
    
    def cleanup_old_data(self, days: int = 30):
        """پاک کردن داده‌های قدیمی"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # پاک کردن داده‌های قدیمی
        cursor.execute('DELETE FROM system_metrics WHERE timestamp < ?', (cutoff_date,))
        cursor.execute('DELETE FROM bot_status WHERE timestamp < ?', (cutoff_date,))
        cursor.execute('DELETE FROM events WHERE timestamp < ?', (cutoff_date,))
        
        deleted_metrics = cursor.rowcount
        conn.commit()
        conn.close()
        
        self.logger.info(f"Cleaned up data older than {days} days ({deleted_metrics} records)")

async def main():
    """تابع اصلی"""
    import argparse
    
    parser = argparse.ArgumentParser(description='سیستم مانیتورینگ ربات‌های تلگرام')
    parser.add_argument('--interval', type=int, default=30, help='فاصله زمانی مانیتورینگ (ثانیه)')
    parser.add_argument('--config-path', default='/home/telegrambot/telegram-bots', 
                       help='مسیر پیکربندی')
    parser.add_argument('--report', action='store_true', help='تولید گزارش')
    parser.add_argument('--hours', type=int, default=24, help='ساعات گزارش')
    parser.add_argument('--cleanup', type=int, help='پاک کردن داده‌های قدیمی (روز)')
    
    args = parser.parse_args()
    
    monitor = BotMonitor(args.config_path)
    
    if args.report:
        # تولید گزارش
        report = monitor.generate_report(args.hours)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        
    elif args.cleanup:
        # پاک کردن داده‌های قدیمی
        monitor.cleanup_old_data(args.cleanup)
        
    else:
        # شروع مانیتورینگ
        try:
            await monitor.monitor_loop(args.interval)
        except KeyboardInterrupt:
            monitor.stop_monitoring()
            print("\nMonitoring stopped.")

if __name__ == "__main__":
    asyncio.run(main())