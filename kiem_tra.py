"""
Script kiểm tra môi trường trước khi chạy demo
"""
import sys
import subprocess

print("=" * 70)
print("KIỂM TRA MÔI TRƯỜNG")
print("=" * 70)

errors = []
warnings = []

# 1. Kiểm tra Python version
print("\n1. Kiểm tra Python...")
python_version = sys.version_info
if python_version.major >= 3 and python_version.minor >= 7:
    print(f"   Python {python_version.major}.{python_version.minor}.{python_version.micro}")
else:
    errors.append("Python phải >= 3.7")
    print(f"   Python {python_version.major}.{python_version.minor} (cần >= 3.7)")

# 2. Kiểm tra các thư viện
print("\n2. Kiểm tra thư viện Python...")
required_packages = ['flask', 'requests', 'pika']
missing_packages = []

for package in required_packages:
    try:
        __import__(package)
        print(f"   {package}")
    except ImportError:
        missing_packages.append(package)
        print(f"   {package} (chưa cài)")

if missing_packages:
    errors.append(f"Thiếu packages: {', '.join(missing_packages)}")
    print(f"\n   Cài đặt: pip install {' '.join(missing_packages)}")

# 3. Kiểm tra Docker
print("\n3. Kiểm tra Docker...")
try:
    result = subprocess.run(['docker', '--version'], 
                          capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"   Docker đã cài đặt")
    else:
        warnings.append("Docker có vấn đề")
        print(f"   Docker có vấn đề")
except FileNotFoundError:
    warnings.append("Docker chưa cài đặt")
    print(f"   Docker chưa cài đặt")
    print(f"   Tải tại: https://www.docker.com/products/docker-desktop")
except Exception as e:
    warnings.append(f"Không kiểm tra được Docker: {e}")
    print(f"   Không kiểm tra được Docker")

# 4. Kiểm tra RabbitMQ
print("\n4. Kiểm tra RabbitMQ container...")
try:
    result = subprocess.run(['docker', 'ps'], 
                          capture_output=True, text=True, timeout=5)
    if 'rabbitmq' in result.stdout:
        print(f"   RabbitMQ đang chạy")
    else:
        warnings.append("RabbitMQ chưa chạy")
        print(f"   RabbitMQ chưa chạy")
        print(f"   Start: docker start rabbitmq")
except Exception as e:
    warnings.append("Không kiểm tra được RabbitMQ")
    print(f"   Không kiểm tra được RabbitMQ")

# 5. Kiểm tra các file cần thiết
print("\n5. Kiểm tra các file cần thiết...")
import os
required_files = [
    'order_service/app.py',
    'email_service/app.py',
    'email_service/consumer.py',
    'email_service/email_processor.py',
]

for file_path in required_files:
    if os.path.exists(file_path):
        print(f"   {file_path}")
    else:
        errors.append(f"Thiếu file: {file_path}")
        print(f"   {file_path}")

# Kết quả
print("\n" + "=" * 70)
if errors:
    print("CÓ LỖI - CHƯA THỂ CHẠY DEMO")
    print("=" * 70)
    for i, error in enumerate(errors, 1):
        print(f"{i}. {error}")
    sys.exit(1)
elif warnings:
    print("CÓ CẢNH BÁO - CÓ THỂ GẶP VẤN ĐỀ")
    print("=" * 70)
    for i, warning in enumerate(warnings, 1):
        print(f"{i}. {warning}")
    print("\nKhuyến nghị: Sửa các cảnh báo trước khi chạy demo")
else:
    print("TẤT CẢ ĐỀU OK - SẴN SÀNG CHẠY DEMO!")
    print("=" * 70)
    print("\nBƯỚC TIẾP THEO:")
    print("\nMở 3 cửa sổ Terminal và chạy:")
    print("   1. python order_service/app.py")
    print("   2. python email_service/app.py")
    print("   3. python email_service/consumer.py")
    print("\nSau đó test:")
    print("   python test_demo.py")

print("\n" + "=" * 70)
