import requests
import json

# Test the delivery optimization endpoint
url = "http://127.0.0.1:5000/api/delivery/optimize"
data = {
    "commercial_code": "1", 
    "delivery_date": "2024-01-15", 
    "min_revenue": 1000
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
