import pika
import json
import sys
import os

# Thêm đường dẫn để import được email_processor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from email_processor import process_email

RABBITMQ_HOST = "localhost"
RABBITMQ_QUEUE = "email_queue"


def callback(ch, method, properties, body):
    """
    Callback function khi nhận message từ RabbitMQ
    Gọi chung hàm process_email() (giống như REST)
    """
    try:
        # Parse message
        data = json.loads(body)
        order_id = data.get('order_id')
        email = data.get('email')
        message = data.get('message')
        
        # Gọi hàm xử lý chung (giống như REST API)
        result = process_email(order_id, email, message, source="RABBITMQ")
        
        # Acknowledge message (xác nhận đã xử lý xong)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f"[ERROR] Lỗi xử lý message: {e}")
        # Nack message nếu có lỗi (để retry)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def main():
    """
    Consumer RabbitMQ - lắng nghe queue và xử lý message
    """
    print("=" * 60)
    print("EMAIL CONSUMER đang khởi động...")
    print("=" * 60)
    
    try:
        # Kết nối RabbitMQ
        print("Đang kết nối tới RabbitMQ...")
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST)
        )
        channel = connection.channel()
        
        # Tạo queue nếu chưa có
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        
        # Set prefetch count (chỉ nhận 1 message tại 1 thời điểm)
        channel.basic_qos(prefetch_count=1)
        
        # Subscribe vào queue
        channel.basic_consume(
            queue=RABBITMQ_QUEUE,
            on_message_callback=callback
        )
        
        print(f"Đang lắng nghe queue: {RABBITMQ_QUEUE}")
        print("Chờ message... (Ctrl+C để thoát)")
        print("=" * 60)
        
        # Bắt đầu consume
        channel.start_consuming()
        
    except KeyboardInterrupt:
        print("\nDừng consumer...")
    except pika.exceptions.AMQPConnectionError as e:
        print(f"Lỗi kết nối RabbitMQ: {e}")
        print("\nGiải pháp:")
        print("   1. Kiểm tra RabbitMQ đã chạy: docker ps | Select-String rabbitmq")
        print("   2. Start RabbitMQ: docker start rabbitmq")
        print("   3. Hoặc chạy container mới: docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management")
    except Exception as e:
        print(f"Lỗi: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
