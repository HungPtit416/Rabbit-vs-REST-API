import requests
import time

BASE_URL = "http://localhost:5000"

def test_rest_api():
    """Test REST API endpoint (đồng bộ)"""
    print("=" * 70)
    print("🧪 TEST 1: REST API (Đồng bộ)")
    print("=" * 70)
    
    start = time.time()
    try:
        response = requests.post(
            f'{BASE_URL}/order/rest',
            json={
                'order_id': 'ORD001',
                'email': 'customer@example.com'
            },
            timeout=10
        )
        elapsed = time.time() - start
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"⏱️  Thời gian: {elapsed:.2f}s")
        print(f"📦 Response:")
        print(response.json())
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
    
    print()


def test_rabbitmq():
    """Test RabbitMQ endpoint (bất đồng bộ)"""
    print("=" * 70)
    print("🧪 TEST 2: RabbitMQ (Bất đồng bộ)")
    print("=" * 70)
    
    start = time.time()
    try:
        response = requests.post(
            f'{BASE_URL}/order/rabbitmq',
            json={
                'order_id': 'ORD002',
                'email': 'customer@example.com'
            },
            timeout=10
        )
        elapsed = time.time() - start
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"⚡ Thời gian: {elapsed:.2f}s (Rất nhanh!)")
        print(f"📦 Response:")
        print(response.json())
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
    
    print()


def compare_performance():
    """So sánh hiệu suất giữa 2 phương thức"""
    print("\n" + "=" * 70)
    print("📊 SO SÁNH HIỆU SUẤT")
    print("=" * 70)
    
    # Test REST
    print("Đang test REST API...")
    start_rest = time.time()
    try:
        requests.post(f'{BASE_URL}/order/rest', 
                     json={'order_id': 'ORD_TEST1', 'email': 'test@test.com'},
                     timeout=10)
        rest_time = time.time() - start_rest
    except:
        rest_time = None
    
    # Test RabbitMQ
    print("Đang test RabbitMQ...")
    start_mq = time.time()
    try:
        requests.post(f'{BASE_URL}/order/rabbitmq',
                     json={'order_id': 'ORD_TEST2', 'email': 'test@test.com'},
                     timeout=10)
        mq_time = time.time() - start_mq
    except:
        mq_time = None
    
    # Hiển thị kết quả
    print("\n📈 KẾT QUẢ:")
    if rest_time:
        print(f"   REST API:  {rest_time:.3f}s {'🐢' if rest_time > 2 else ''}")
    else:
        print(f"   REST API:  ❌ Lỗi")
        
    if mq_time:
        print(f"   RabbitMQ:  {mq_time:.3f}s {'⚡' if mq_time < 0.5 else ''}")
    else:
        print(f"   RabbitMQ:  ❌ Lỗi")
    
    if rest_time and mq_time:
        speedup = rest_time / mq_time
        print(f"\n   🚀 RabbitMQ nhanh hơn: {speedup:.1f}x")
    
    print("=" * 70)


if __name__ == '__main__':
    print("\n🚀 BẮT ĐẦU TEST DEMO\n")
    
    # Test từng endpoint
    test_rest_api()
    time.sleep(1)
    test_rabbitmq()
    time.sleep(1)
    
    # So sánh hiệu suất
    compare_performance()
    
    print("\n✅ HOÀN THÀNH TEST!")
    print("\n💡 LƯU Ý:")
    print("   - Kiểm tra Terminal của Email Consumer để xem message được xử lý")
    print("   - REST API phải đợi ~2.5s, còn RabbitMQ trả về ngay")
    print("   - Đây là lý do tại sao dùng message queue cho các tác vụ chậm!")
