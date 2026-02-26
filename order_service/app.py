from flask import Flask, request, jsonify
import requests
import pika
import json
import time

app = Flask(__name__)

# Cấu hình
EMAIL_SERVICE_URL = "http://localhost:5001/send-email"
RABBITMQ_HOST = "localhost"
RABBITMQ_QUEUE = "email_queue"


@app.route('/order/rest', methods=['POST'])
def create_order_rest():
    """
    Endpoint 1: REST API (Đồng bộ)
    Gọi trực tiếp sang Email Service và đợi xử lý xong
    """
    start_time = time.time()
    
    data = request.get_json()
    order_id = data.get('order_id', 'ORD001')
    customer_email = data.get('email', 'customer@example.com')
    
    try:
        # Gọi trực tiếp sang Email Service
        print(f"[REST] Đang gọi Email Service cho đơn hàng {order_id}...")
        
        response = requests.post(
            EMAIL_SERVICE_URL,
            json={
                'order_id': order_id,
                'email': customer_email,
                'message': f'Đơn hàng {order_id} đã được tạo thành công!'
            },
            timeout=10
        )
        
        elapsed_time = time.time() - start_time
        
        return jsonify({
            'status': 'success',
            'method': 'REST (Đồng bộ)',
            'order_id': order_id,
            'email_sent': response.json(),
            'elapsed_time': f'{elapsed_time:.2f}s',
            'note': '⚠️ Phải đợi Email Service xử lý xong mới trả về'
        }), 200
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        return jsonify({
            'status': 'error',
            'method': 'REST (Đồng bộ)',
            'error': str(e),
            'elapsed_time': f'{elapsed_time:.2f}s'
        }), 500


@app.route('/order/rabbitmq', methods=['POST'])
def create_order_rabbitmq():
    """
    Endpoint 2: RabbitMQ (Bất đồng bộ)
    Chỉ push message vào queue và trả về ngay
    """
    start_time = time.time()
    
    data = request.get_json()
    order_id = data.get('order_id', 'ORD002')
    customer_email = data.get('email', 'customer@example.com')
    
    try:
        # Kết nối RabbitMQ
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST)
        )
        channel = connection.channel()
        
        # Tạo queue nếu chưa có
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        
        # Publish message
        message = {
            'order_id': order_id,
            'email': customer_email,
            'message': f'Đơn hàng {order_id} đã được tạo thành công!'
        }
        
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
            )
        )
        
        connection.close()
        
        elapsed_time = time.time() - start_time
        
        print(f"[RabbitMQ] Đã push message vào queue cho đơn hàng {order_id}")
        
        return jsonify({
            'status': 'success',
            'method': 'RabbitMQ (Bất đồng bộ)',
            'order_id': order_id,
            'message': 'Đơn hàng đã được tạo, email sẽ được gửi trong giây lát',
            'elapsed_time': f'{elapsed_time:.2f}s',
            'note': '✅ Trả về ngay lập tức, không cần đợi Email Service'
        }), 200
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        return jsonify({
            'status': 'error',
            'method': 'RabbitMQ (Bất đồng bộ)',
            'error': str(e),
            'elapsed_time': f'{elapsed_time:.2f}s'
        }), 500


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'service': 'Order Service',
        'endpoints': {
            'REST (Đồng bộ)': 'POST /order/rest',
            'RabbitMQ (Bất đồng bộ)': 'POST /order/rabbitmq'
        },
        'example_payload': {
            'order_id': 'ORD001',
            'email': 'customer@example.com'
        }
    })


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 ORDER SERVICE đang chạy trên http://localhost:5000")
    print("=" * 60)
    print("📌 Endpoints:")
    print("   - POST /order/rest      → REST API (đồng bộ, chậm)")
    print("   - POST /order/rabbitmq  → RabbitMQ (bất đồng bộ, nhanh)")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
