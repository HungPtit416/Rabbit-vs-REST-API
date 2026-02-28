# Demo So Sánh REST API vs RabbitMQ

So sánh hiệu suất giữa REST API (đồng bộ) và RabbitMQ (bất đồng bộ) với **load cao (1000 users đồng thời)**.

---

## TÀI LIỆU

| File | Mô tả |
|------|-------|
| **[HUONG_DAN_CHAY.md](HUONG_DAN_CHAY.md)** | Hướng dẫn chi tiết chạy + JMeter |
| **[KIEN_TRUC.md](KIEN_TRUC.md)** | Kiến trúc và flow |

---

## CHẠY NHANH

### 1. Cài đặt
```powershell
pip install Flask requests pika
docker start rabbitmq
```

### 2. Chạy 3 service (3 Terminal riêng)
```powershell
# Terminal 1
python order_service/app.py

# Terminal 2
python email_service/app.py

# Terminal 3
python email_service/consumer.py
```

### 3. Test
```powershell
# Test nhanh
python test_demo.py

# Hoặc test bằng curl
curl -X POST http://localhost:5000/order/rest -H "Content-Type: application/json" -d '{\"order_id\": \"ORD001\", \"email\": \"user@test.com\"}'

curl -X POST http://localhost:5000/order/rabbitmq -H "Content-Type: application/json" -d '{\"order_id\": \"ORD002\", \"email\": \"user@test.com\"}'
```

---

## Kết quả

| Phương thức | 1 user | 1000 users | Winner |
|-------------|--------|------------|--------|
| **REST API** | ~2.5s | Timeout | Chậm |
| **RabbitMQ** | ~0.05s | Stable | Nhanh |

**Kết luận:** RabbitMQ nhanh hơn **50 lần** và stable với load cao!

---

## Mục đích

Hiểu sự khác biệt giữa:
- **Đồng bộ** (REST) - Blocking, chậm
- **Bất đồng bộ** (RabbitMQ) - Non-blocking, nhanh, scalable

**Use case:**
- REST: Validation, CRUD nhanh
- RabbitMQ: Email, SMS, Video processing, Background job

---

**Chi tiết:** [HUONG_DAN_CHAY.md](HUONG_DAN_CHAY.md)

## Cài đặt

### Bước 1: Cài đặt Python dependencies

```powershell
pip install -r requirements.txt
```

### Bước 2: Cài đặt và chạy RabbitMQ

#### Cách 1: Dùng Docker (Khuyến nghị)

```powershell
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

Truy cập RabbitMQ Management: http://localhost:15672
- Username: `guest`
- Password: `guest`

#### Cách 2: Cài đặt RabbitMQ trực tiếp

1. Tải RabbitMQ: https://www.rabbitmq.com/download.html
2. Cài đặt Erlang: https://www.erlang.org/downloads
3. Cài đặt RabbitMQ và chạy service

## Chạy Demo

### Bước 1: Mở 3 cửa sổ Terminal/PowerShell

#### Terminal 1 - Chạy Order Service
```powershell
cd "c:\Users\ADMIN\Desktop\HDV - py"
python order_service/app.py
```

Kết quả: Order Service chạy trên http://localhost:5000

#### Terminal 2 - Chạy Email Service (REST API)
```powershell
cd "c:\Users\ADMIN\Desktop\HDV - py"
python email_service/app.py
```

Kết quả: Email Service chạy trên http://localhost:5001

#### Terminal 3 - Chạy Email Consumer (RabbitMQ)
```powershell
cd "c:\Users\ADMIN\Desktop\HDV - py"
python email_service/consumer.py
```

Kết quả: Consumer lắng nghe queue `email_queue`

## Test Demo

### Bước 2: Mở Terminal thứ 4 để test

#### Test 1: REST API (Đồng bộ - Chậm)

```powershell
curl -X POST http://localhost:5000/order/rest `
  -H "Content-Type: application/json" `
  -d '{\"order_id\": \"ORD001\", \"email\": \"customer@example.com\"}'
```

**Kết quả:**
- Phải đợi ~2.5 giây
- Order Service chờ Email Service xử lý xong mới trả về
- Response sẽ có `elapsed_time` khoảng 2.5-3s

#### Test 2: RabbitMQ (Bất đồng bộ - Nhanh)

```powershell
curl -X POST http://localhost:5000/order/rabbitmq `
  -H "Content-Type: application/json" `
  -d '{\"order_id\": \"ORD002\", \"email\": \"customer@example.com\"}'
```

**Kết quả:**
- Trả về ngay lập tức (~0.01-0.05 giây)
- Message được đẩy vào queue
- Email Consumer xử lý phía sau
- Response có `elapsed_time` rất thấp

### Hoặc dùng Python để test:

```python
import requests
import time

# Test REST API
print("Testing REST API...")
start = time.time()
response = requests.post('http://localhost:5000/order/rest', 
    json={'order_id': 'ORD001', 'email': 'customer@example.com'})
print(f"REST Response: {response.json()}")
print(f"Time taken: {time.time() - start:.2f}s\n")

# Test RabbitMQ
print("Testing RabbitMQ...")
start = time.time()
response = requests.post('http://localhost:5000/order/rabbitmq', 
    json={'order_id': 'ORD002', 'email': 'customer@example.com'})
print(f"RabbitMQ Response: {response.json()}")
print(f"Time taken: {time.time() - start:.2f}s")
```

## So sánh kết quả

| Phương thức | Thời gian phản hồi | Xử lý email | Load cao |
|-------------|-------------------|-------------|----------|
| **REST API** | ~2.5-3s (chậm) | Đồng bộ, phải đợi | Dễ bị nghẽ n |
| **RabbitMQ** | ~0.01-0.05s (nhanh) | Bất đồng bộ, không đợi | Ổn định |

## Kết luận

- **REST API**: Đơn giản nhưng chậm, client phải đợi toàn bộ quá trình
- **RabbitMQ**: Nhanh hơn, client không phải đợi, xử lý phía sau
- **Khi nào dùng RabbitMQ?**
  - Xử lý lâu (gửi email, xử lý video, báo cáo)
  - Cần scale và load balancing
  - Tách biệt các service

## Troubleshooting

### Lỗi: Connection refused to RabbitMQ
```
Kiểm tra RabbitMQ đã chạy chưa:
- Docker: docker ps | grep rabbitmq
- Windows Service: services.msc → tìm RabbitMQ
```

### Lỗi: Port đã được sử dụng
```
Đổi port trong file app.py:
- Order Service: app.run(port=5000)  → đổi thành 5010
- Email Service: app.run(port=5001)  → đổi thành 5011
```

### Consumer không nhận message
```
1. Kiểm tra RabbitMQ đã chạy
2. Kiểm tra queue 'email_queue' đã được tạo trong RabbitMQ Management
3. Restart consumer
```

## Cấu trúc Project

```
HDV - py/
├── order_service/
│   └── app.py              # Order Service với 2 endpoints
├── email_service/
│   ├── email_processor.py  # ⭐ Hàm xử lý chung cho cả REST và RabbitMQ
│   ├── app.py              # REST API endpoint (gọi email_processor)
│   └── consumer.py         # RabbitMQ Consumer (gọi email_processor)
├── test_demo.py            # Script test tự động
├── requirements.txt        # Python dependencies
├── README.md              # File này
├── QUICK_START.md         # Hướng dẫn nhanh
└── COMMANDS.ps1           # Tất cả lệnh cần dùng
```

### Kiến trúc Email Service

```
┌─────────────────────────────────────────────┐
│         EMAIL SERVICE                        │
├─────────────────────────────────────────────┤
│                                              │
│  REST API          RabbitMQ Consumer  │
│  (app.py)             (consumer.py)          │
│      │                      │                │
│      └──────────┬───────────┘                │
│                 │                            │
│                 ▼                            │
│      process_email()                      │
│      (email_processor.py)                    │
│                 │                            │
│                 ├─ Delay 2.5s               │
│                 ├─ Log processing           │
│                 └─ Return result            │
└─────────────────────────────────────────────┘
```

**Điểm quan trọng:** Cả REST API và RabbitMQ Consumer đều gọi chung **1 hàm `process_email()`** → đảm bảo logic xử lý giống hệt nhau!

## Support

Nếu có lỗi, kiểm tra:
1. RabbitMQ đã chạy chưa?
2. 3 service đã chạy đầy đủ chưa?
3. Port có bị conflict không?
