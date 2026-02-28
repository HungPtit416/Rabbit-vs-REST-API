from flask import Flask, request, jsonify
import requests
import pika
import json
import time
from pika.exceptions import AMQPConnectionError
import threading
from queue import Queue

app = Flask(__name__)

# Cấu hình
EMAIL_SERVICE_URL = "http://localhost:5001/send-email"
RABBITMQ_HOST = "localhost"
RABBITMQ_QUEUE = "email_queue"

# Connection Pool cho RabbitMQ (để xử lý high concurrency)
MAX_POOL_SIZE = 100  # 100 connections sẵn sàng
connection_pool = Queue(maxsize=MAX_POOL_SIZE)
pool_lock = threading.Lock()

def init_connection_pool():
    """Khởi tạo connection pool khi start app"""
    print(f"[INIT] Đang tạo {MAX_POOL_SIZE} RabbitMQ connections...")
    for i in range(MAX_POOL_SIZE):
        try:
            conn = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    heartbeat=600,
                    blocked_connection_timeout=300,
                )
            )
            channel = conn.channel()
            channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            connection_pool.put((conn, channel))
            if (i + 1) % 20 == 0:
                print(f"[INIT] Đã tạo {i + 1}/{MAX_POOL_SIZE} connections...")
        except Exception as e:
            print(f"[ERROR] Không thể tạo connection {i}: {e}")
            break
    print(f"[INIT] Connection pool sẵn sàng với {connection_pool.qsize()} connections")

def get_rabbitmq_connection():
    """Lấy connection từ pool"""
    try:
        conn, channel = connection_pool.get(timeout=2)
        # Kiểm tra connection còn sống không
        if conn.is_closed:
            # Tạo lại connection mới
            conn = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST, heartbeat=600)
            )
            channel = conn.channel()
            channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        return conn, channel
    except Exception as e:
        print(f"[ERROR] Không lấy được connection từ pool: {e}")
        return None, None

def return_connection(conn, channel):
    """Trả connection về pool"""
    try:
        if conn and not conn.is_closed:
            connection_pool.put((conn, channel), timeout=1)
    except:
        # Pool đầy, đóng connection
        if conn and not conn.is_closed:
            conn.close()


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
            timeout=5  # Giảm từ 10s xuống 5s để dễ timeout khi load cao
        )
        
        elapsed_time = time.time() - start_time
        
        return jsonify({
            'status': 'success',
            'method': 'REST (Đồng bộ)',
            'order_id': order_id,
            'email_sent': response.json(),
            'elapsed_time': f'{elapsed_time:.2f}s',
            'note': 'Phải đợi Email Service xử lý xong mới trả về'
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
        # Sử dụng connection pool thay vì tạo connection mới
        connection, channel = get_rabbitmq_connection()
        
        if connection is None or channel is None:
            raise Exception("Không thể kết nối tới RabbitMQ")
        
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
        
        # Trả connection về pool để reuse
        return_connection(connection, channel)
        
        elapsed_time = time.time() - start_time
        
        print(f"[RabbitMQ] Đã push message vào queue cho đơn hàng {order_id}")
        
        return jsonify({
            'status': 'success',
            'method': 'RabbitMQ (Bất đồng bộ)',
            'order_id': order_id,
            'message': 'Đơn hàng đã được tạo, email sẽ được gửi trong giây lát',
            'elapsed_time': f'{elapsed_time:.2f}s',
            'note': 'Trả về ngay lập tức, không cần đợi Email Service'
        }), 200
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        # Cố gắng trả connection về pool ngay cả khi có lỗi
        if 'connection' in locals() and connection:
            return_connection(connection, channel)
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
    print("ORDER SERVICE đang chạy trên http://localhost:5000")
    print("=" * 60)
    print("Endpoints:")
    print("   - POST /order/rest      → REST API (đồng bộ, chậm)")
    print("   - POST /order/rabbitmq  → RabbitMQ (bất đồng bộ, nhanh)")
    print("=" * 60)
    print("Multi-threading: ENABLED (xử lý đồng thời nhiều requests)")
    print("RabbitMQ Connection Pool: INITIALIZING...")
    print("=" * 60)
    
    # Khởi tạo connection pool trước khi start server
    init_connection_pool()
    
    print("=" * 60)
    print("Server sẵn sàng!")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True, use_reloader=False)
