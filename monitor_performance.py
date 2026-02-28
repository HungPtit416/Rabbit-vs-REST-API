"""
Script monitor performance khi chạy load test
Chạy script này TRƯỚC KHI chạy JMeter để theo dõi real-time
"""
import psutil
import time
import os
from datetime import datetime

def get_python_processes():
    """Lấy thông tin các process Python"""
    python_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            if 'python' in proc.info['name'].lower():
                python_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return python_processes

def format_bytes(bytes):
    """Format bytes thành MB"""
    return f"{bytes / (1024 * 1024):.1f} MB"

def monitor_performance(interval=2):
    """Monitor CPU, Memory real-time"""
    print("=" * 80)
    print("🔍 PERFORMANCE MONITOR - Tracking Python processes")
    print("=" * 80)
    print("Nhấn Ctrl+C để dừng\n")
    print("💡 Chạy JMeter test để thấy performance thay đổi...\n")
    
    try:
        sample_count = 0
        while True:
            sample_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Clear screen (optional)
            if sample_count % 10 == 1:
                os.system('cls' if os.name == 'nt' else 'clear')
                print("=" * 80)
                print(f"🔍 PERFORMANCE MONITOR - Sample #{sample_count}")
                print("=" * 80)
            
            # Get system info
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            print(f"\n[{timestamp}] System Overview:")
            print(f"  💻 Total CPU: {cpu_percent:.1f}%")
            print(f"  🧠 Total Memory: {memory.percent:.1f}% ({format_bytes(memory.used)} / {format_bytes(memory.total)})")
            
            # Get Python processes
            python_procs = get_python_processes()
            
            if python_procs:
                print(f"\n  🐍 Python Processes ({len(python_procs)}):")
                for proc in python_procs:
                    try:
                        cpu = proc.cpu_percent(interval=0.1)
                        mem = proc.memory_info().rss
                        print(f"     PID {proc.pid}: CPU {cpu:.1f}%, Memory {format_bytes(mem)}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            
            # Warning indicators
            warnings = []
            if cpu_percent > 70:
                warnings.append(f"⚠️  HIGH CPU: {cpu_percent:.1f}%")
            if cpu_percent > 90:
                warnings.append(f"🚨 CRITICAL CPU: {cpu_percent:.1f}%")
            if memory.percent > 80:
                warnings.append(f"⚠️  HIGH MEMORY: {memory.percent:.1f}%")
            
            if warnings:
                print("\n  Warnings:")
                for warning in warnings:
                    print(f"     {warning}")
            
            print("-" * 80)
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n👋 Stopped monitoring.")

if __name__ == '__main__':
    print("\n🚀 Starting Performance Monitor...")
    print("=" * 80)
    print("📊 This will track:")
    print("   - System CPU usage")
    print("   - Memory usage")
    print("   - Python processes performance")
    print("\n💡 Guide:")
    print("   1. Let this run")
    print("   2. Open another terminal and run JMeter test")
    print("   3. Watch the numbers here:")
    print("      - REST API: CPU will spike to 80-100%")
    print("      - RabbitMQ: CPU stays stable 20-40%")
    print("=" * 80)
    input("\nPress ENTER to start monitoring...")
    
    try:
        monitor_performance(interval=2)
    except Exception as e:
        print(f"\n❌ Error: {e}")
