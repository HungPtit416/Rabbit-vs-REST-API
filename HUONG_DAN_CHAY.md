# 🚀 HƯỚNG DẪN CHẠY - DEMO REST API VS RABBITMQ

## 📦 BƯỚC 1: CÀI ĐẶT

### 1.1. Cài đặt Python packages
```powershell
cd "c:\Users\ADMIN\Desktop\HDV - py"
pip install Flask requests pika
```

### 1.2. Khởi động RabbitMQ
```powershell
# Nếu container đã tồn tại:
docker start rabbitmq

# Nếu chưa có, tạo mới:
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

### 1.3. Kiểm tra trạng thái
```powershell
# Kiểm tra RabbitMQ đã chạy:
docker ps | Select-String rabbitmq

# Kiểm tra môi trường:
python kiem_tra.py
```

---

## 🎬 BƯỚC 2: CHẠY CÁC SERVICE

### MỞ 3 CỬA SỔ POWERSHELL/TERMINAL

#### 📟 **Terminal 1: Order Service**
```powershell
cd "c:\Users\ADMIN\Desktop\HDV - py"
python order_service/app.py
```
**Kết quả:** Service chạy tại http://localhost:5000

---

#### 📟 **Terminal 2: Email Service (REST API)**
```powershell
cd "c:\Users\ADMIN\Desktop\HDV - py"
python email_service/app.py
```
**Kết quả:** Service chạy tại http://localhost:5001

---

#### 📟 **Terminal 3: Email Consumer (RabbitMQ)**
```powershell
cd "c:\Users\ADMIN\Desktop\HDV - py"
python email_service/consumer.py
```
**Kết quả:** Consumer lắng nghe queue `email_queue`

---

## 🧪 BƯỚC 3: TEST NHANH

### 3.1. Test với Python script

Mở Terminal thứ 4:
```powershell
cd "c:\Users\ADMIN\Desktop\HDV - py"
python test_demo.py
```

### 3.2. Test thủ công với curl

**Test REST API (chậm ~2.5s):**
```powershell
curl -X POST http://localhost:5000/order/rest `
  -H "Content-Type: application/json" `
  -d '{\"order_id\": \"ORD001\", \"email\": \"user@example.com\"}'
```

**Test RabbitMQ (nhanh ~0.05s):**
```powershell
curl -X POST http://localhost:5000/order/rabbitmq `
  -H "Content-Type: application/json" `
  -d '{\"order_id\": \"ORD002\", \"email\": \"user@example.com\"}'
```

---

## 📊 BƯỚC 4: TEST LOAD VỚI JMETER (1000 USERS)

### 4.1. Cài đặt JMeter

1. **Download:** https://jmeter.apache.org/download_jmeter.cgi
2. **Giải nén:** Vào thư mục (VD: `C:\apache-jmeter`)
3. **Chạy:** `C:\apache-jmeter\bin\jmeter.bat`

### 4.2. Tạo Test Plan

#### **Test 1: REST API (Endpoint chậm)**

**1. Tạo Thread Group:**
```
- Right click Test Plan → Add → Threads → Thread Group
- Number of Threads: 1000
- Ramp-up period: 10 (giây)
- Loop Count: 1
```

**2. Thêm HTTP Request:**
```
- Right click Thread Group → Add → Sampler → HTTP Request

Cấu hình:
- Server Name: localhost
- Port: 5000
- Method: POST
- Path: /order/rest
- Body Data:
  {
    "order_id": "ORD${__Random(1,10000)}",
    "email": "user${__Random(1,1000)}@example.com"
  }
```

**3. Thêm HTTP Header:**
```
- Right click Thread Group → Add → Config Element → HTTP Header Manager
- Add:
  Name: Content-Type
  Value: application/json
```

**4. Thêm Listeners:**
```
- Right click Thread Group → Add → Listener → Summary Report
- Right click Thread Group → Add → Listener → View Results Tree
- Right click Thread Group → Add → Listener → Graph Results
```

#### **Test 2: RabbitMQ (Endpoint nhanh)**

Làm tương tự Test 1 nhưng:
- **Path:** `/order/rabbitmq`

### 4.3. Chạy Test

1. **Save Test Plan:** File → Save (lưu thành `test_load.jmx`)
2. **Run Test:** Click nút **Start** (▶️) hoặc Ctrl+R
3. **Quan sát kết quả** trong Summary Report và Graph Results

### 4.4. Kết quả mong đợi

| Metric | REST API | RabbitMQ |
|--------|----------|----------|
| **Samples** | 1000 | 1000 |
| **Average (ms)** | ~2500 | ~50 |
| **Min (ms)** | ~2000 | ~20 |
| **Max (ms)** | ~5000+ | ~200 |
| **Error %** | 5-20% | 0-2% |
| **Throughput (req/s)** | ~400 | ~20000 |

**Kết luận:**
- REST API: Nhiều timeout, slow, không stable
- RabbitMQ: Fast, stable, scalable

---

## 🎯 QUAN SÁT KẾT QUẢ

### Terminal 1 (Order Service)
```
[REST] Đang gọi Email Service cho đơn hàng ORD001...
[RabbitMQ] Đã push message vào queue cho đơn hàng ORD002
```

### Terminal 2 (Email Service REST)
```
[EMAIL REST] Nhận yêu cầu gửi email cho đơn hàng ORD001
[EMAIL REST] Đang xử lý... (delay 2.5s)
[EMAIL REST] ✅ Đã gửi email thành công!
```

### Terminal 3 (Email Consumer)
```
[EMAIL RABBITMQ] Nhận yêu cầu gửi email cho đơn hàng ORD002
[EMAIL RABBITMQ] Đang xử lý... (delay 2.5s)
[EMAIL RABBITMQ] ✅ Đã gửi email thành công!
```

---

## 🔍 MONITORING (OPTIONAL)

### RabbitMQ Management UI
**Truy cập:** http://localhost:15672
- Username: `guest`
- Password: `guest`

**Quan sát:**
- Tab "Queues" → queue `email_queue`
- Message rate, Consumer count, Pending messages

---

## ❌ XỬ LÝ LỖI

### Lỗi: ModuleNotFoundError
```powershell
pip install Flask requests pika
```

### Lỗi: Connection refused (RabbitMQ)
```powershell
docker start rabbitmq
# Đợi 3-5 giây
```

### Lỗi: Port already in use
```powershell
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Lỗi: JMeter timeout
Trong JMeter:
- Add → Config Element → HTTP Request Defaults
- Set Connect Timeout: `10000`ms
- Set Response Timeout: `10000`ms

---

## 💡 TIPS NÂNG CAO

### Scale Consumer (xử lý nhanh hơn)
```powershell
# Chạy nhiều consumer đồng thời:
# Terminal 3
python email_service/consumer.py

# Terminal 4
python email_service/consumer.py

# Terminal 5
python email_service/consumer.py
```
→ RabbitMQ tự động load balance

### JMeter Variables
Trong Body Data, dùng:
- `${__Random(min,max)}` - Random number
- `${__time()}` - Current timestamp
- `${__UUID()}` - Random UUID

---

## 📊 SO SÁNH KẾT QUẢ

### Test 1 user:
| Phương thức | Response Time |
|-------------|---------------|
| REST | ~2.5s 🐢 |
| RabbitMQ | ~0.05s ⚡ |

**RabbitMQ nhanh hơn 50 lần!**

### Test 1000 concurrent users:
| Metric | REST | RabbitMQ | Winner |
|--------|------|----------|--------|
| Success Rate | 80-95% | 98-100% | RabbitMQ ✅ |
| Avg Response | ~2.5s | ~0.05s | RabbitMQ ✅ |
| Throughput | ~400/s | ~20000/s | RabbitMQ ✅ |
| Error Rate | 5-20% | 0-2% | RabbitMQ ✅ |

**Kết luận:** RabbitMQ hoàn toàn vượt trội khi load cao!

---

## 📁 CẤU TRÚC PROJECT

```
HDV - py/
├── order_service/
│   └── app.py              # 2 endpoints (REST + RabbitMQ)
├── email_service/
│   ├── email_processor.py  # Hàm xử lý chung
│   ├── app.py             # REST API
│   └── consumer.py        # RabbitMQ Consumer
├── test_demo.py           # Quick test
├── kiem_tra.py            # Check environment
├── requirements.txt       # Dependencies
├── KIEN_TRUC.md          # Kiến trúc
└── HUONG_DAN_CHAY.md     # File này
```

---

## 🎓 KẾT LUẬN

### REST API:
- ✅ Đơn giản
- ✅ Phù hợp tác vụ nhanh
- ❌ Không scale với load cao
- ❌ Dễ timeout và crash

### RabbitMQ:
- ✅ Nhanh
- ✅ Scalable
- ✅ Stable với load cao
- ✅ Phù hợp background job
- ⚠️ Phức tạp hơn

### Khuyến nghị Production:
- **Email, SMS, Video:** RabbitMQ
- **Validation, CRUD:** REST API
- **Long-running task:** RabbitMQ
- **Quick response:** REST API

---

**Xem thêm:** [KIEN_TRUC.md](KIEN_TRUC.md)

Chúc bạn test thành công! 🎉
