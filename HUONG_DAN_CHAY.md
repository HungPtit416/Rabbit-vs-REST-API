# HƯỚNG DẪN CHẠY - DEMO REST API VS RABBITMQ

## BƯỚC 1: CÀI ĐẶT

### 1.1. Cài đặt Python packages
```powershell
cd "c:\Users\ADMIN\Desktop\HDV - py"
pip install Flask requests pika psutil
```

### 1.2. Khởi động RabbitMQ với cấu hình tối ưu

**QUAN TRỌNG:** Để test với 5000 users, cần RabbitMQ với cấu hình cao hơn!

#### **Option 1: Chạy script tự động (Khuyến nghị)**
```powershell
cd "c:\Users\ADMIN\Desktop\HDV - py"
.\restart_rabbitmq.ps1
```
→ Script sẽ tự động:
- Xóa container cũ
- Tạo RabbitMQ mới với max memory 1GB, max processes 1M
- Tăng connection limits

#### **Option 2: Chạy thủ công**
```powershell
# Dừng và xóa container cũ:
docker stop rabbitmq
docker rm rabbitmq

# Tạo mới với cấu hình cao:
docker run -d --name rabbitmq `
  -p 5672:5672 `
  -p 15672:15672 `
  -e RABBITMQ_VM_MEMORY_HIGH_WATERMARK=1024MiB `
  -e RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS="+P 1048576" `
  rabbitmq:3-management

# Đợi 10 giây
Start-Sleep -Seconds 10

# Tăng connection limits:
docker exec rabbitmq rabbitmqctl set_vm_memory_high_watermark 0.8
```

#### **Option 3: Container cũ (chỉ test nhẹ 1000 users)**
```powershell
# Nếu container đã tồn tại:
docker start rabbitmq
```
⚠️ **Không khuyến nghị cho test 5000 users!**

### 1.3. Kiểm tra trạng thái
```powershell
# Kiểm tra RabbitMQ đã chạy:
docker ps | Select-String rabbitmq

# Kiểm tra môi trường:
python kiem_tra.py
```

---

## BƯỚC 2: CHẠY CÁC SERVICE

### MỞ 3 CỬA SỔ POWERSHELL/TERMINAL

#### **Terminal 1: Order Service**
```powershell
cd "c:\Users\ADMIN\Desktop\HDV - py"
python order_service/app.py
```
**Kết quả:** Service chạy tại http://localhost:5000

---

#### **Terminal 2: Email Service (REST API)**
```powershell
cd "c:\Users\ADMIN\Desktop\HDV - py"
python email_service/app.py
```
**Kết quả:** Service chạy tại http://localhost:5001

---

#### **Terminal 3: Email Consumer (RabbitMQ)**
```powershell
cd "c:\Users\ADMIN\Desktop\HDV - py"
python email_service/consumer.py
```
**Kết quả:** Consumer lắng nghe queue `email_queue`

---

## BƯỚC 3: TEST NHANH

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

## BƯỚC 4: TEST LOAD VỚI JMETER (1000 USERS)

### 4.0. Monitor Performance (Khuyến nghị)

**Mở Terminal thứ 4 để monitor real-time:**
```powershell
cd "c:\Users\ADMIN\Desktop\HDV - py"
python monitor_performance.py
```

**Script này sẽ theo dõi:**
- CPU usage (System + Python processes)
- Memory usage
- Warnings khi CPU/Memory cao

**Khi chạy JMeter test, bạn sẽ thấy:**
- **REST API test:** CPU spike 80-100%
- **RabbitMQ test:** CPU stable 20-40%

→ Đây là bằng chứng trực quan REST API bị quá tải!

---

### 4.1. Cài đặt JMeter

1. **Download:** https://jmeter.apache.org/download_jmeter.cgi
2. **Giải nén:** Vào thư mục (VD: `C:\apache-jmeter`)
3. **Chạy:** `C:\apache-jmeter\bin\jmeter.bat`

### 4.2. Tạo Test Plan

**LƯU Ý:** Tạo **2 Thread Groups** trong **CÙNG 1 Test Plan** để so sánh dễ dàng.

---

#### **⚙️ KHUYẾN NGHỊ CẤU HÌNH:**

| Mục đích | Threads | Ramp-up | Kết quả mong đợi |
|----------|---------|---------|------------------|
| **Test nhanh** | 1000 | 10s | REST: 0-10% error, RabbitMQ: 0-2% error |
| **So sánh rõ** | 2000-3000 | 30s | REST: 20-40% error, RabbitMQ: 0-5% error |
| **Thấy REST sập** | 5000 | 60s | REST: 50-80% error, RabbitMQ: 0-10% error |

**Tips:**
- **Ramp-up period càng cao** → Load spread đều hơn → Ít error hơn
- **5000 threads trong 10s** = 500 req/giây → Quá nhanh, cả 2 đều crash!
- **5000 threads trong 60s** = 83 req/giây → Vừa phải, thấy rõ sự khác biệt

---

#### **THREAD GROUP 1: REST API (Endpoint chậm)**

**1. Tạo Thread Group đầu tiên:**
```
- Right click Test Plan → Add → Threads → Thread Group
- Đổi tên: "Test 1: REST API (Slow)"
- Number of Threads: 1000 (hoặc 5000 để test crash)
- Ramp-up period: 10 (hoặc 60 cho 5000 users)
- Loop Count: 1
```

**2. Thêm HTTP Request:**
```
- Right click "Test 1: REST API (Slow)" → Add → Sampler → HTTP Request
- Đổi tên: "POST /order/rest"

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
- Right click "Test 1: REST API (Slow)" → Add → Config Element → HTTP Header Manager
- Add:
  Name: Content-Type
  Value: application/json
```

---

#### **THREAD GROUP 2: RabbitMQ (Endpoint nhanh)**

**4. Tạo Thread Group thứ hai (trong cùng Test Plan):**
```
- Right click Test Plan → Add → Threads → Thread Group
- Đổi tên: "Test 2: RabbitMQ (Fast)"
- Number of Threads: 1000 (hoặc 5000 để test crash)
- Ramp-up period: 10 (hoặc 60 cho 5000 users) 
- Loop Count: 1
```

**5. Thêm HTTP Request:**
```
- Right click "Test 2: RabbitMQ (Fast)" → Add → Sampler → HTTP Request
- Đổi tên: "POST /order/rabbitmq"

Cấu hình:
- Server Name: localhost
- Port: 5000
- Method: POST
- Path: /order/rabbitmq
- Body Data:
  {
    "order_id": "ORD${__Random(1,10000)}",
    "email": "user${__Random(1,1000)}@example.com"
  }
```

**6. Thêm HTTP Header:**
```
- Right click "Test 2: RabbitMQ (Fast)" → Add → Config Element → HTTP Header Manager
- Add:
  Name: Content-Type
  Value: application/json
```

---

#### **LISTENERS (cho cả 2 Thread Groups)**

**7. Thêm Listeners vào Test Plan (không phải vào Thread Group):**
```
- Right click Test Plan → Add → Listener → Summary Report
- Right click Test Plan → Add → Listener → View Results Tree
- Right click Test Plan → Add → Listener → Graph Results
```

→ Listeners ở level Test Plan sẽ thu thập kết quả từ **cả 2 Thread Groups**

### 4.3. Chạy Test

**Cấu trúc JMeter sau khi tạo xong:**
```
Test Plan
├── Thread Group 1: REST API (Slow)
│   ├── HTTP Request: POST /order/rest
│   └── HTTP Header Manager
├── Thread Group 2: RabbitMQ (Fast)
│   ├── HTTP Request: POST /order/rabbitmq
│   └── HTTP Header Manager
├── Summary Report (Listener)
├── View Results Tree (Listener)
└── Graph Results (Listener)
```

**Chạy test:**
1. **Save Test Plan:** File → Save (lưu thành `test_load.jmx`)
2. **Chọn test nào chạy:**
   - Muốn chạy cả 2: Bỏ check hết
   - Muốn chỉ chạy REST: Right click "Test 2" → Disable
   - Muốn chỉ chạy RabbitMQ: Right click "Test 1" → Disable
3. **Run Test:** Click nút **Start** (▶️) hoặc Ctrl+R
4. **Quan sát kết quả** trong Summary Report và Graph Results

**Tips:**
- Chạy từng Test riêng trước để so sánh rõ
- Summary Report sẽ hiển thị kết quả theo Label (Thread Group name)

### 4.4. Kết quả mong đợi

#### **✅ Test với 1000 users (Ramp-up: 10s):**

| Metric | REST API | RabbitMQ |
|--------|----------|----------|
| **Samples** | 1000 | 1000 |
| **Average (ms)** | ~2500 | ~50 |
| **Min (ms)** | ~2000 | ~20 |
| **Max (ms)** | ~5000+ | ~200 |
| **Error %** | 0-10% | 0-2% |
| **Throughput (req/s)** | ~80 | ~100 |

**Kết luận:** Cả 2 đều ổn, nhưng REST chậm hơn RabbitMQ 50 lần!

---

#### **⚡ Test với 5000 users (Ramp-up: 60s):** ← KHUYẾN NGHỊ

**Kết quả mong đợi SAU KHI TỐI ƯU:**

| Metric | REST API | RabbitMQ | Winner |
|--------|----------|----------|--------|
| **Average (ms)** | 3000-5000 | 50-300 | RabbitMQ |
| **Error %** | 40-60% | 0-10% | RabbitMQ |
| **Throughput** | 200-300 | 80-100 | Tương đương |

**Giải thích:**
- **REST API:** Timeout nhiều vì phải chờ Email Service (2.5s), khi load cao không kịp xử lý
- **RabbitMQ:** Nhanh vì chỉ push message (~50ms), không chờ xử lý, connection pool giúp ổn định

**Kết luận:**
- REST API **SẬP** với ~50% error rate
- RabbitMQ **VẪN ỔN** với <10% error rate
- **Chứng minh:** RabbitMQ scalable hơn REST API với high load!

---

#### **❌ Test với 5000 users (Ramp-up: 10s - QUÁ NHANH!):**

**Vấn đề:**
- 5000 users trong 10s = **500 req/giây**
- Order Service **không kịp nhận** requests
- **Cả REST và RabbitMQ đều crash!**

**Kết quả thực tế (TRƯỚC KHI TỐI ƯU):**
```
POST /order/rest:     75% Error, 1592ms avg
POST /order/rabbitmq: 95% Error, 923ms avg  ← Cả 2 đều sập!
```

**Nguyên nhân:**
```
5000 requests trong 10s
         ↓
Order Service BỊ NGHẼN (đang nhận quá nhanh)
         ↓
┌────────┴────────┐
↓                 ↓
REST path:        RabbitMQ path:
Timeout           Connection pool cạn kiệt
```

**Giải pháp:**
1. **Tăng Ramp-up lên 60s** → Spread load đều hơn
2. **RabbitMQ connection pool** (100 connections sẵn sàng)
3. **Giảm REST timeout** xuống 5s (dễ fail hơn)
4. **RabbitMQ config cao hơn** (max memory 1GB, max processes 1M)
✅ Request đơn giản                        ❌ Connection pool cạn kiệt
✅ Không cần connection pool               ❌ Mỗi publish cần channel riêng
✅ Flask xử lý đủ nhanh (vẫn 75% error)    ❌ RabbitMQ từ chối connections

```

**Nguyên nhân gốc:**
- **Flask mặc định = SINGLE-THREADED** (chỉ xử lý 1 request/lần)
- Order Service không kịp nhận 5000 requests → timeout
- RabbitMQ path phức tạp hơn (cần mở connection/channel) → fail nhiều hơn

**2. Tại sao REST API log "giữ nguyên" (không chạy tiếp)?**

```python
# Code cũ (SINGLE-THREADED):
app.run(host='0.0.0.0', port=5001)  # Xử lý tuần tự, chậm!

# Điều gì xảy ra:
Request 1 → Processing (2.5s) → Done
Request 2 → Processing (2.5s) → Done
...
Request 100 → Done
Request 101-5000 → TIMEOUT (chờ quá lâu, JMeter hủy)
```

**Log "giữ nguyên" vì:**
- Flask xử lý ~100-200 requests
- Các request còn lại timeout
- JMeter ngừng gửi → Log dừng

**3. Tại sao RabbitMQ Consumer vẫn chạy?**

 **Đúng như thiết kế!**
- Những messages không bị error (~5% = 250 messages) đã vào queue
- Consumer xử lý ổn định, từng message (2.5s/cái)
- **Đây là ưu điểm:** Không bị timeout, xử lý chắc chắn

---

#### FIX: Bật Multi-threading

**ĐÃ FIX trong code mới!**

```python
# order_service/app.py và email_service/app.py
app.run(host='0.0.0.0', port=5000, threaded=True)  # Xử lý đồng thời!

# + Connection pooling cho RabbitMQ
```

**Chạy lại test sau khi fix:**
1. **Stop tất cả services** (Ctrl+C)
2. **Restart lại:**
   ```powershell
   python order_service/app.py
   python email_service/app.py
   python email_service/consumer.py
   ```
3. **Chạy JMeter lại với 5000 users**

**Kết quả mong đợi sau khi fix:**
```
POST /order/rest:     10-20% Error (thay vì 75%)
POST /order/rabbitmq: 0-5% Error (thay vì 95%)
```

---

#### **📋 WORKFLOW CHẠY TEST (5000 USERS):**

**Bước 1: Chuẩn bị**
```powershell
# Terminal mới - Restart RabbitMQ với config tối ưu
cd "c:\Users\ADMIN\Desktop\HDV - py"
.\restart_rabbitmq.ps1
```

**Bước 2: Purge queue cũ**
```powershell
docker exec rabbitmq rabbitmqctl purge_queue email_queue
```

**Bước 3: Stop tất cả services (nếu đang chạy)**
```powershell
# Ctrl+C ở tất cả terminals
```

**Bước 4: Start services**
```powershell
# Terminal 1
python order_service/app.py
# Đợi thấy "Server sẵn sàng!" (khởi tạo 100 connections)

# Terminal 2
python email_service/app.py

# Terminal 3
python email_service/consumer.py

# Terminal 4 (optional - monitor)
python monitor_performance.py
```

**Bước 5: Chạy JMeter test**
```
1. Mở JMeter → Load test_load.jmx
2. Thread Groups → Set:
   - Number of Threads: 5000
   - Ramp-up period: 60 (QUAN TRỌNG!)
3. Disable Thread Group không cần test
4. Click Start (▶️)
```

**Bước 6: Quan sát**
- **JMeter Summary Report:** REST error ~50%, RabbitMQ error ~5%
- **Terminal 4:** CPU spike khi test REST, stable khi test RabbitMQ
- **RabbitMQ Management UI:** http://localhost:15672 → Xem queue messages

**Kết quả:** REST API sập, RabbitMQ vẫn ổn!

---

### 4.5. Cách nhận biết REST API bị sập

#### **Dấu hiệu trong JMeter:**

**1. Error Rate cao (>10%):**
```
Summary Report → Cột "Error %"
- REST API: 10-30% errors
- RabbitMQ: 0-2% errors
```

**2. Response Time tăng vọt:**
```
Summary Report → Cột "Average"
- REST API: Từ 2.5s → 5s → 10s → timeout
- Nhiều request >30s
```

**3. Timeout errors:**
```
View Results Tree → Click vào request màu đỏ
- Response message: "SocketTimeoutException"
- Response message: "Connection refused"
- Response message: "Read timed out"
```

**4. Throughput giảm mạnh:**
```
Summary Report → Cột "Throughput"
- Càng về sau càng giảm
- REST: Bắt đầu 500 req/s → xuống 100 req/s
```

---

#### **Dấu hiệu trong Terminal/Console:**

**Terminal 1 (Order Service):**
```
[REST] Đang gọi Email Service cho đơn hàng ORD001...
[REST] Đang gọi Email Service cho đơn hàng ORD002...
[REST] Đang gọi Email Service cho đơn hàng ORD003...
... (hàng trăm dòng đồng thời)
[ERROR] Connection refused
[ERROR] Timeout waiting for response
```

**Terminal 2 (Email Service REST API):**
```
[EMAIL REST] Nhận request...
[EMAIL REST] Nhận request...
[EMAIL REST] Nhận request...
... (quá nhiều request đồng thời)
[Errno 10061] No connection could be made
OSError: [WinError 10048] Only one usage of socket address is permitted
```

**Dấu hiệu sập:**
- Console đầy errors màu đỏ
- Service không response
- CPU 100%
- Memory tăng liên tục

---

#### **So sánh khi chạy test:**

**REST API (1000 users):**
```
Request 1-100:    OK, ~2.5s
Request 101-500:  Chậm dần, ~5s
Request 501-1000: Timeout, errors

Summary Report:
- Average: 4500ms
- Error %: 25%
- Many red lines in "View Results Tree"
```

**RabbitMQ (1000 users):**
```
Request 1-1000: Tất cả OK, ~50ms

Summary Report:
- Average: 50ms
- Error %: 0%
- All green in "View Results Tree"
```

---

#### **Cách test để thấy rõ sự sập:**

**Test 1: Tăng dần số users**
```
Thread Group Settings:
1. 100 users  → REST: OK
2. 500 users  → REST: Chậm
3. 1000 users → REST: Timeout/Error
4. 2000 users → REST: Sập hoàn toàn
```

**Test 2: Kiểm tra logs real-time**
```powershell
# Xem CPU usage:
while($true) {
  Get-Process python | Select Name, CPU, PM | Format-Table
  Start-Sleep -Seconds 2
}
```

**Test 3: Monitor với Task Manager**
- Mở Task Manager (Ctrl+Shift+Esc)
- Tab "Performance"
- Quan sát khi chạy JMeter test:
  - REST API: CPU spike 80-100%
  - RabbitMQ: CPU stable 20-30%

---

#### **Ngưỡng cảnh báo:**

| Metric | Cảnh báo | Nghiêm trọng | Sập |
|--------|----------|--------------|-----|
| Error Rate | >5% | >15% | >30% |
| Avg Response | >5s | >10s | >30s |
| Throughput | <300/s | <100/s | 0/s |
| CPU | >70% | >90% | 100% |

---

#### **Tips để test:**

1. **Chạy REST trước để thấy nó sập:**
   ```
   - Start với 1000 users
   - Quan sát Summary Report
   - Check View Results Tree (nhiều màu đỏ = errors)
   ```

2. **Sau đó chạy RabbitMQ để so sánh:**
   ```
   - Cùng 1000 users
   - Summary Report: All green
   - No errors
   ```

3. **Chụp màn hình kết quả:**
   - REST: Nhiều errors
   - RabbitMQ: Không có errors
   - → Chứng minh RabbitMQ tốt hơn!

---

## QUAN SÁT KẾT QUẢ

### Terminal 1 (Order Service)
```
[REST] Đang gọi Email Service cho đơn hàng ORD001...
[RabbitMQ] Đã push message vào queue cho đơn hàng ORD002
```

### Terminal 2 (Email Service REST)
```
[EMAIL REST] Nhận yêu cầu gửi email cho đơn hàng ORD001
[EMAIL REST] Đang xử lý... (delay 2.5s)
[EMAIL REST] Đã gửi email thành công!
```

### Terminal 3 (Email Consumer)
```
[EMAIL RABBITMQ] Nhận yêu cầu gửi email cho đơn hàng ORD002
[EMAIL RABBITMQ] Đang xử lý... (delay 2.5s)
[EMAIL RABBITMQ] Đã gửi email thành công!
```

---

## DỬNG RABBITMQ CONSUMER

### Hiện tượng: Consumer "chạy mãi" sau khi Ctrl+C

**Tại sao Consumer vẫn chạy?**

```
[Khi chạy JMeter test]
Order Service → Push 1000 messages → Queue (nhanh, <20s)
                                       ↓
                            Consumer xử lý từng message (2.5s/cái)
                            → Mất ~40 phút cho 1000 messages!

[Sau khi Ctrl+C Order Service]
Order Service: Ngừng
Email REST:    Ngừng
Consumer:      VẪN CHẠY (xử lý messages còn trong queue)
```

**Đây là ĐẶC ĐIỂM của Message Queue:**
- **Ưu điểm:** Không mất data, xử lý chắc chắn
- **"Nhược điểm":** Phải đợi xử lý hết (hoặc dừng thủ công)

---

### Cách dừng Consumer:

#### **Option 1: Ctrl+C (dừng consumer, giữ messages)**
```powershell
# Trong Terminal 3 (Consumer)
Ctrl+C
```
→ Consumer dừng, messages **vẫn còn trong queue**  
→ Lần sau chạy lại consumer sẽ xử lý tiếp

#### **Option 2: Purge Queue (xóa tất cả messages chưa xử lý)**
```powershell
# Xóa tất cả messages trong queue:
docker exec rabbitmq rabbitmqctl purge_queue email_queue
```
→ **Cảnh báo:** Messages bị xóa vĩnh viễn!

#### **Option 3: Web UI (xóa messages qua giao diện)**
1. Mở http://localhost:15672 (guest/guest)
2. Tab "Queues" → Click `email_queue`
3. Kéo xuống section **"Purge Messages"**
4. Click **"Purge Messages"** button
5. Confirm xóa

---

### 📋 Workflow khuyến nghị:

**Trước mỗi lần test:**
```powershell
# 1. Kiểm tra queue hiện tại
docker exec rabbitmq rabbitmqctl list_queues

# 2. Purge nếu có messages cũ
docker exec rabbitmq rabbitmqctl purge_queue email_queue

# 3. Chạy test
```

**Sau test:**
- **Nếu chỉ test response time:** Ctrl+C consumer, purge queue
- **Nếu muốn xem consumer xử lý:** Để chạy hết, check logs

---

### 🔍 Kiểm tra trạng thái Queue:

```powershell
# Xem số messages trong queue:
docker exec rabbitmq rabbitmqctl list_queues name messages_ready messages_unacknowledged

# Output mẫu:
# email_queue    850    0    ← Còn 850 messages chưa xử lý
```

**Hoặc xem qua Web UI:**
- http://localhost:15672 → Tab "Queues"
- **Ready:** Messages chưa xử lý
- **Unacked:** Messages đang xử lý

---

## MONITORING (OPTIONAL)

### RabbitMQ Management UI
**Truy cập:** http://localhost:15672
- Username: `guest`
- Password: `guest`

**Quan sát:**
- Tab "Queues" → queue `email_queue`
- Message rate, Consumer count, Pending messages

---

## XỬ LÝ LỖI

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

## TIPS NÂNG CAO

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

## SO SÁNH KẾT QUẢ

### Test 1 user:
| Phương thức | Response Time |
|-------------|---------------|
| REST | ~2.5s Chậm |
| RabbitMQ | ~0.05s Nhanh |

**RabbitMQ nhanh hơn 50 lần!**

### Test 1000 concurrent users:
| Metric | REST | RabbitMQ | Winner |
|--------|------|----------|--------|
| Success Rate | 80-95% | 98-100% | RabbitMQ |
| Avg Response | ~2.5s | ~0.05s | RabbitMQ |
| Throughput | ~400/s | ~20000/s | RabbitMQ |
| Error Rate | 5-20% | 0-2% | RabbitMQ |

**Kết luận:** RabbitMQ hoàn toàn vượt trội khi load cao!

---

## CẤU TRÚC PROJECT

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

## KẾT LUẪN

### REST API:
- Đơn giản
- Phù hợp tác vụ nhanh
- Không scale với load cao
- Dễ timeout và crash

### RabbitMQ:
- Nhanh
- Scalable
- Stable với load cao
- Phù hợp background job
- Phức tạp hơn

### Khuyến nghị Production:
- **Email, SMS, Video:** RabbitMQ
- **Validation, CRUD:** REST API
- **Long-running task:** RabbitMQ
- **Quick response:** REST API

---

**Xem thêm:** [KIEN_TRUC.md](KIEN_TRUC.md)

Chúc bạn test thành công!
