import requests
import json

# API URL
url = 'http://127.0.0.1:5000/api/delivery/optimize'

# Test data without product filter
data = {
    "commercial_code": "1300",  # From the test file
    "delivery_date": "2023-06-15"  # From the test file
}

# Make the request
response = requests.post(url, json=data)

# Print response
print(f"Status code: {response.status_code}")
print(f"Response headers: {response.headers}")
print("Response JSON:")
try:
    json_response = response.json()
    print(json.dumps(json_response, indent=2))
except Exception as e:
    print(f"Error parsing JSON: {e}")
    print(response.text)
