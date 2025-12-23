import requests
import random
import threading
import time

# Nginx 域名或 IP
NGINX_URL = "http://localhost:8080/track"

# 模拟用户ID
user_ids = [f"user_{i}" for i in range(1, 21)]

# 模拟事件类型
events = ["login", "signup", "purchase", "logout"]

# 模拟设备
devices = ["iOS", "Android", "Windows", "Mac"]

# 模拟浏览器
browsers = ["Chrome", "Firefox", "Safari", "Edge"]

def send_request():
    """发送一次请求"""
    params = {
        "uid": random.choice(user_ids),
        "event": random.choice(events),
        "device": random.choice(devices),
        "browser": random.choice(browsers)
    }
    try:
        response = requests.get(NGINX_URL, params=params, timeout=2)
        print(f"Sent: {params}, Status: {response.status_code}")
    except Exception as e:
        print(f"Request failed: {e}")

def simulate_requests(concurrency=5, total_requests=50):
    """模拟并发请求"""
    threads = []
    for i in range(total_requests):
        t = threading.Thread(target=send_request)
        t.start()
        threads.append(t)
        time.sleep(0.05)  # 每 50ms 启动一个请求，控制速度

        # 控制并发线程数量
        if len(threads) >= concurrency:
            for th in threads:
                th.join()
            threads = []

    # 等待剩余线程完成
    for th in threads:
        th.join()

if __name__ == "__main__":
    simulate_requests(concurrency=10, total_requests=10000)
