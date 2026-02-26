"""
Email Processor - Hàm xử lý chung cho cả REST API và RabbitMQ Consumer
"""
import time


def process_email(order_id, email, message, source="UNKNOWN"):
    """
    Hàm xử lý email chung cho cả REST và RabbitMQ
    
    Args:
        order_id: Mã đơn hàng
        email: Email người nhận
        message: Nội dung email
        source: Nguồn gọi ("REST" hoặc "RABBITMQ")
    
    Returns:
        dict: Kết quả xử lý
    """
    print(f"[EMAIL {source}] Nhận yêu cầu gửi email cho đơn hàng {order_id}")
    print(f"[EMAIL {source}] To: {email}")
    print(f"[EMAIL {source}] Đang xử lý... (delay 2.5s)")
    
    # Mô phỏng xử lý nặng: gửi email, kết nối SMTP, etc.
    time.sleep(2.5)
    
    print(f"[EMAIL {source}] ✅ Đã gửi email thành công!")
    print("-" * 60)
    
    return {
        'status': 'success',
        'order_id': order_id,
        'email': email,
        'message': 'Email đã được gửi thành công',
        'processing_time': '2.5s',
        'source': source
    }
