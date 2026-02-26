# Email Service

Service xử lý gửi email với 2 cách nhận request:

## 📂 Cấu trúc

```
email_service/
├── email_processor.py   ⭐ Hàm xử lý chung
├── app.py              📨 REST API endpoint
└── consumer.py         📨 RabbitMQ Consumer
```

## 🎯 Kiến trúc

```
┌─────────────────────────────────────┐
│      REST API        RabbitMQ       │
│      (app.py)        (consumer.py)  │
│          │                │          │
│          └────────┬───────┘          │
│                   ▼                  │
│         process_email()              │
│       (email_processor.py)           │
│                   │                  │
│           ┌───────┴────────┐         │
│           │ Delay 2.5s     │         │
│           │ Log processing │         │
│           │ Return result  │         │
│           └────────────────┘         │
└─────────────────────────────────────┘
```

## 🔑 Điểm quan trọng

**Cả 2 luồng đều gọi chung 1 hàm `process_email()`:**

```python
# REST API
result = process_email(order_id, email, message, source="REST")

# RabbitMQ Consumer
result = process_email(order_id, email, message, source="RABBITMQ")
```

→ Đảm bảo logic xử lý **giống hệt nhau**, chỉ khác nguồn input!

## 📝 Chi tiết

### email_processor.py
- Hàm xử lý chung: `process_email()`
- Delay 2.5s để mô phỏng xử lý nặng
- Trả về kết quả chuẩn

### app.py (REST API)
- Endpoint: `POST /send-email`
- Nhận request từ HTTP
- Gọi `process_email()` với source="REST"

### consumer.py (RabbitMQ)
- Lắng nghe queue: `email_queue`
- Nhận message từ RabbitMQ
- Gọi `process_email()` với source="RABBITMQ"
