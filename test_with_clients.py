#!/usr/bin/env python3
import requests
import json

with open('test_with_clients.json', 'r') as f:
    data = json.load(f)

response = requests.post('http://127.0.0.1:5000/api/delivery/optimize', json=data)
print(f'Status Code: {response.status_code}')
if response.status_code == 200:
    result = response.json()
    print('SUCCESS!')
    print(f'Route length: {len(result.get("route", []))}')
    print(f'Total distance: {result.get("total_distance", 0)}')
    if 'revenue_info' in result:
        print('Revenue info available')
else:
    print(f'Error: {response.text}')
