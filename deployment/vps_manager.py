#!/usr/bin/env python3
"""
مدیر VPS برای سیستم ربات‌های تلگرام
VPS Manager for Telegram Bots System
"""

import os
import sys
import subprocess
import psutil
import time
import json
import argparse
from datetime import datetime
from pathlib import Path

class VPSManager:
    def __init__(self):
        self.bot_user = "telegrambot"
        self.bot_dir = f"/home/{self.bot_user}/telegram-bots"
        self.log_dir = "/var/log/telegram-bots"
        self.services = [
            "telegram-bots.service", 
            "telegram-bots-monitor.service",
            "telegram-bots-report.service"
        ]
        
    def run_command(self, command, check=True):
        """اجرای دستور shell"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                check=check
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.CalledProcessError as e:
            return e.stdout, e.stderr, e.returncode
    
    def check_system_status(self):
        """بررسی وضعیت کلی سیستم"""
        print("📊 بررسی وضعیت سیستم...")
        print("=" * 50)
        
        # CPU و RAM
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        print(f"🖥️  CPU: {cpu_percent}%")
        print(f"💾 RAM: {memory.percent}% ({memory.used // 1024**2}MB / {memory.total // 1024**2}MB)")
        print(f"💿 Disk: {disk.percent}% ({disk.used // 1024**3}GB / {disk.total // 1024**3}GB)")
        
        # Network
        net_io = psutil.net_io_counters()
        print(f"🌐 Network: ↑{net_io.bytes_sent // 1024**2}MB ↓{net_io.bytes_recv // 1024**2}MB")
        
        print()
        
    def check_services_status(self):
        """بررسی وضعیت سرویس‌ها"""
        print("🔧 وضعیت سرویس‌ها:")
        print("=" * 50)
        
        for service in self.services:
            stdout, stderr, code = self.run_command(f"systemctl is-active {service}", check=False)
            status = stdout.strip()
            
            if status == "active":
                print(f"✅ {service}: فعال")
            elif status == "inactive":
                print(f"⏹️  {service}: غیرفعال")
            elif status == "failed":
                print(f"❌ {service}: خطا")
            else:
                print(f"❓ {service}: {status}")
        
        print()
        
    def check_processes(self):
        """بررسی پروسه‌های مربوط به ربات‌ها"""
        print("🤖 پروسه‌های ربات:")
        print("=" * 50)
        
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
            try:
                if proc.info['name'] == 'python3' or proc.info['name'] == 'python':
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if 'bot' in cmdline.lower() or 'unified' in cmdline.lower():
                        python_processes.append({
                            'pid': proc.info['pid'],
                            'cmdline': cmdline,
                            'cpu': proc.info['cpu_percent'],
                            'memory': proc.info['memory_info'].rss // 1024**2 if proc.info['memory_info'] else 0
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if python_processes:
            for proc in python_processes:
                print(f"🐍 PID {proc['pid']}: {proc['cmdline'][:60]}...")
                print(f"   CPU: {proc['cpu']}% | RAM: {proc['memory']}MB")
        else:
            print("❌ هیچ پروسه ربات فعالی یافت نشد")
        
        print()
        
    def check_ports(self):
        """بررسی پورت‌های شبکه"""
        print("🌐 پورت‌های فعال:")
        print("=" * 50)
        
        important_ports = [5000, 80, 443, 5432, 6379]
        
        for port in important_ports:
            try:
                connections = psutil.net_connections()
                port_found = False
                for conn in connections:
                    if conn.laddr and conn.laddr.port == port:
                        status = conn.status if hasattr(conn, 'status') else 'UNKNOWN'
                        print(f"🔓 Port {port}: {status}")
                        port_found = True
                        break
                
                if not port_found:
                    print(f"🔒 Port {port}: بسته")
                    
            except Exception as e:
                print(f"❓ Port {port}: خطا در بررسی")
        
        print()
        
    def check_logs(self, lines=20):
        """بررسی لاگ‌های اخیر"""
        print(f"📋 آخرین {lines} خط لاگ:")
        print("=" * 50)
        
        for service in self.services:
            print(f"\n📊 {service}:")
            stdout, stderr, code = self.run_command(
                f"journalctl -u {service} -n {lines} --no-pager", 
                check=False
            )
            if code == 0:
                print(stdout[-500:] if len(stdout) > 500 else stdout)
            else:
                print(f"❌ خطا در خواندن لاگ: {stderr}")
        
    def restart_services(self):
        """ری‌استارت همه سرویس‌ها"""
        print("🔄 ری‌استارت سرویس‌ها...")
        
        for service in self.services:
            print(f"🔄 ری‌استارت {service}...")
            stdout, stderr, code = self.run_command(f"systemctl restart {service}")
            if code == 0:
                print(f"✅ {service} ری‌استارت شد")
            else:
                print(f"❌ خطا در ری‌استارت {service}: {stderr}")
        
        print("⏳ انتظار برای راه‌اندازی...")
        time.sleep(5)
        self.check_services_status()
        
    def start_services(self):
        """شروع همه سرویس‌ها"""  
        print("🚀 شروع سرویس‌ها...")
        
        for service in self.services:
            print(f"🚀 شروع {service}...")
            stdout, stderr, code = self.run_command(f"systemctl start {service}")
            if code == 0:
                print(f"✅ {service} شروع شد")
            else:
                print(f"❌ خطا در شروع {service}: {stderr}")
        
        time.sleep(3)
        self.check_services_status()
        
    def stop_services(self):
        """توقف همه سرویس‌ها"""
        print("⏹️ توقف سرویس‌ها...")
        
        for service in self.services:
            print(f"⏹️ توقف {service}...")
            stdout, stderr, code = self.run_command(f"systemctl stop {service}")
            if code == 0:
                print(f"✅ {service} متوقف شد")
            else:
                print(f"❌ خطا در توقف {service}: {stderr}")
        
    def backup_data(self, backup_path=None):
        """بک‌آپ از داده‌ها"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"/tmp/telegram-bots-backup-{timestamp}.tar.gz"
        
        print(f"💾 ایجاد بک‌آپ در {backup_path}...")
        
        # لیست فایل‌ها و دایرکتری‌های مهم
        backup_items = [
            self.bot_dir,
            self.log_dir,
            "/etc/systemd/system/telegram-bots*.service"
        ]
        
        # ایجاد tar archive
        items_str = " ".join(backup_items)
        command = f"tar -czf {backup_path} {items_str}"
        
        stdout, stderr, code = self.run_command(command, check=False)
        
        if code == 0:
            # اندازه فایل بک‌آپ
            size = os.path.getsize(backup_path) // 1024**2
            print(f"✅ بک‌آپ با موفقیت ایجاد شد ({size}MB)")
            print(f"📁 مسیر: {backup_path}")
            return backup_path
        else:
            print(f"❌ خطا در ایجاد بک‌آپ: {stderr}")
            return None
            
    def update_system(self):
        """به‌روزرسانی سیستم"""
        print("📦 به‌روزرسانی سیستم...")
        
        # بک‌آپ قبل از به‌روزرسانی
        backup_path = self.backup_data()
        if not backup_path:
            print("❌ خطا در بک‌آپ - به‌روزرسانی متوقف شد")
            return False
        
        # توقف سرویس‌ها
        self.stop_services()
        
        try:
            # به‌روزرسانی پکیج‌های سیستم
            print("📦 به‌روزرسانی پکیج‌های سیستم...")
            self.run_command("apt update && apt upgrade -y")
            
            # به‌روزرسانی Python packages
            print("🐍 به‌روزرسانی Python packages...")
            pip_path = f"{self.bot_dir}/venv/bin/pip"
            self.run_command(f"{pip_path} install --upgrade pip")
            self.run_command(f"{pip_path} install --upgrade -r {self.bot_dir}/requirements.txt")
            
            print("✅ به‌روزرسانی کامل شد")
            
            # شروع مجدد سرویس‌ها
            self.start_services()
            
            return True
            
        except Exception as e:
            print(f"❌ خطا در به‌روزرسانی: {e}")
            print("🔄 بازگردانی از بک‌آپ...")
            
            # بازگردانی
            self.run_command(f"tar -xzf {backup_path} -C /")
            self.start_services()
            
            return False

    def generate_report(self):
        """تولید گزارش کامل سیستم"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "system": {},
            "services": {},
            "processes": [],
            "network": {},
            "disk": {}
        }
        
        # اطلاعات سیستم
        report["system"]["cpu_percent"] = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        report["system"]["memory"] = {
            "total": memory.total,
            "used": memory.used,
            "percent": memory.percent
        }
        
        # وضعیت سرویس‌ها
        for service in self.services:
            stdout, stderr, code = self.run_command(f"systemctl is-active {service}", check=False)
            report["services"][service] = stdout.strip()
        
        # پروسه‌ها
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
            try:
                if proc.info['name'] in ['python3', 'python']:
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if 'bot' in cmdline.lower():
                        report["processes"].append({
                            'pid': proc.info['pid'],
                            'cmdline': cmdline,
                            'cpu': proc.info['cpu_percent'],
                            'memory': proc.info['memory_info'].rss if proc.info['memory_info'] else 0
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # شبکه
        net_io = psutil.net_io_counters()
        report["network"] = {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }
        
        # دیسک
        disk = psutil.disk_usage('/')
        report["disk"] = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }
        
        # ذخیره گزارش
        report_path = f"/tmp/system-report-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 گزارش سیستم ذخیره شد: {report_path}")
        return report_path

def main():
    parser = argparse.ArgumentParser(description='مدیر VPS برای سیستم ربات‌های تلگرام')
    parser.add_argument('action', choices=[
        'status', 'start', 'stop', 'restart', 'logs', 'backup', 
        'update', 'report', 'full-check'
    ], help='عملیات مورد نظر')
    parser.add_argument('--lines', type=int, default=20, help='تعداد خطوط لاگ')
    parser.add_argument('--backup-path', help='مسیر بک‌آپ')
    
    args = parser.parse_args()
    
    # بررسی دسترسی root
    if os.geteuid() != 0:
        print("❌ این اسکریپت باید با دسترسی root اجرا شود")
        print("استفاده کنید از: sudo python3 vps_manager.py")
        sys.exit(1)
    
    manager = VPSManager()
    
    print(f"🚀 مدیر VPS سیستم ربات‌های تلگرام")
    print(f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    if args.action == 'status':
        manager.check_services_status()
        
    elif args.action == 'start':
        manager.start_services()
        
    elif args.action == 'stop':
        manager.stop_services()
        
    elif args.action == 'restart':
        manager.restart_services()
        
    elif args.action == 'logs':
        manager.check_logs(args.lines)
        
    elif args.action == 'backup':
        manager.backup_data(args.backup_path)
        
    elif args.action == 'update':
        manager.update_system()
        
    elif args.action == 'report':
        manager.generate_report()
        
    elif args.action == 'full-check':
        manager.check_system_status()
        manager.check_services_status()
        manager.check_processes()
        manager.check_ports()
        print("📊 بررسی کامل انجام شد.")

if __name__ == "__main__":
    main()