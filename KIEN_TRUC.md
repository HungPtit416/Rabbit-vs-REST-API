# KIẾN TRÚC - SO SÁNH REST API VS RABBITMQ

## Tổng quan

Demo so sánh 2 cách xử lý request khi có **load cao (1000 users đồng thời)**:
- **REST API** (đồng bộ) - Blocking, chậm, dễ timeout
- **RabbitMQ** (bất đồng bộ) - Non-blocking, nhanh, scalable

---

## LUỒNG 1: REST API (Đồng bộ)

```
Client → Order Service → Email Service (xử lý 2.5s) → Response
         (đợi 2.5s)                                    (chậm)
```

### Đặc điểm:
- Response time: **~2.5s**
- Blocking: Phải đợi xử lý xong
- Vấn đề: 1000 users đồng thời → timeout, lỗi
- Ưu điểm: Đơn giản, biết ngay kết quả

---

## LUỒNG 2: RabbitMQ (Bất đồng bộ)

```
Client → Order Service → RabbitMQ Queue → Response ngay
         (push queue)         ↓            (nhanh)
                         Email Consumer
                         (xử lý 2.5s sau)
```

### Đặc điểm:
- Response time: **~0.05s** (nhanh gấp 50 lần!)
- Non-blocking: Không đợi, trả về ngay
- Ưu điểm: Nhanh, stable với load cao
- Nhược điểm: Không biết ngay kết quả

---

## EMAIL SERVICE - Kiến trúc

```
┌─────────────────────────────────────────┐
│         EMAIL SERVICE                   │
├─────────────────────────────────────────┤
│  REST API       RabbitMQ Consumer      │
│  (app.py)       (consumer.py)           │
│      │               │                  │
│      └───────┬───────┘                  │
│              ▼                          │
│      process_email()                    │
│      (delay 2.5s)                       │
└─────────────────────────────────────────┘
```

**Điểm quan trọng:** REST và RabbitMQ đều gọi **cùng 1 hàm** `process_email()` → logic giống hệt nhau

---

## TEST VỚI JMETER (1000 USERS)

### Endpoint 1: REST API
```
POST http://localhost:5000/order/rest
Content-Type: application/json

{
  "order_id": "ORD001",
  "email": "user@example.com"
}
```

### Endpoint 2: RabbitMQ
```
POST http://localhost:5000/order/rabbitmq
Content-Type: application/json

{
  "order_id": "ORD002",
  "email": "user@example.com"
}
```

### Kết quả mong đợi với 1000 concurrent users:

| Metric | REST API | RabbitMQ |
|--------|----------|----------|
| **Avg Response Time** | ~2500ms | ~50ms |
| **Throughput** | ~400 req/s | ~20000 req/s |
| **Error Rate** | Cao (timeout) | Thấp |
| **Stability** | Không ổn định | Ổn định |

---

## Cấu trúc Project

```
HDV - py/
├── order_service/
│   └── app.py              # Order Service (2 endpoints)
│
├── email_service/
│   ├── email_processor.py  # Hàm xử lý chung (delay 2.5s)
│   ├── app.py             # REST API endpoint
│   └── consumer.py        # RabbitMQ Consumer
│
├── test_load.jmx          # JMeter test plan
├── test_demo.py           # Quick test script
├── requirements.txt       # Dependencies
├── KIEN_TRUC.md          # File này
└── HUONG_DAN_CHAY.md     # Hướng dẫn chi tiết
```

---

## Kết luận

### Load thấp (1-10 users):
- REST và RabbitMQ đều OK
- Không thấy sự khác biệt lớn

### Load cao (1000+ users):
- **REST API**: Blocking → queue up → timeout → crash
- **RabbitMQ**: Message queue → stable → không crash

### Chọn công nghệ:
| Use Case | Chọn |
|----------|------|
| Validation, tính toán nhanh | REST API |
| Gửi email, SMS | RabbitMQ |
| Xử lý video, ảnh | RabbitMQ |
| Tạo báo cáo | RabbitMQ |
| CRUD đơn giản | REST API |
| Background job | RabbitMQ |

---

## Chi tiết flow

### REST API Flow:
```
1. Client POST → Order Service
2. Order Service HTTP POST → Email Service
3. Email Service process (2.5s) → Response
4. Order Service ← Response
5. Client ← Response (total: 2.5s)
```

### RabbitMQ Flow:
```
1. Client POST → Order Service
2. Order Service publish → RabbitMQ Queue
3. Order Service → Response (total: 0.05s)
4. Client ← Response ✅

--- Background (không blocking client) ---
5. Consumer pull ← RabbitMQ Queue
6. Consumer process (2.5s)
7. Consumer ACK
```

---

**Xem thêm:** [HUONG_DAN_CHAY.md](HUONG_DAN_CHAY.md) - Hướng dẫn chi tiết chạy và test JMeter
