from flask import Flask, request, jsonify
import sys
import os

# Thêm đường dẫn để import được email_processor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from email_processor import process_email

app = Flask(__name__)


@app.route('/send-email', methods=['POST'])
def send_email():
    """
    REST API endpoint để gửi email
    Cả REST và RabbitMQ đều gọi chung hàm process_email()
    """
    data = request.get_json()
    order_id = data.get('order_id', 'UNKNOWN')
    email = data.get('email', 'unknown@example.com')
    message = data.get('message', '')
    
    # Gọi hàm xử lý chung (giống như RabbitMQ Consumer)
    result = process_email(order_id, email, message, source="REST")
    
    return jsonify(result), 200


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'service': 'Email Service',
        'endpoints': {
            'send_email': 'POST /send-email'
        }
    })


if __name__ == '__main__':
    print("=" * 60)
    print("EMAIL SERVICE (REST API) đang chạy trên http://localhost:5001")
    print("=" * 60)
    print("Multi-threading: ENABLED (xử lý đồng thời nhiều requests)")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)
