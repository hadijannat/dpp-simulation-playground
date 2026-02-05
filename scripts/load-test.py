import time
import requests

for _ in range(10):
    requests.get("http://localhost:8101/api/v1/health", timeout=5)
    time.sleep(0.2)
print("ok")
