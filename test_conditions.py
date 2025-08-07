#!/usr/bin/env python3
"""
Test the delivery optimization conditions for revenue and frequent visits
"""

import requests
import json
from datetime import datetime, timedelta

def test_delivery_optimization_conditions():
    """Test the revenue and frequent visits conditions"""
    
    # Test data with both conditions
    test_data = {
        'commercial_code': '1',
        'delivery_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'min_revenue': 1000,
        'min_frequent_visits': 3
    }

    print('Testing delivery optimization API with revenue and visits conditions...')
    print(f'Test data: {json.dumps(test_data, indent=2)}')

    try:
        response = requests.post('http://localhost:5000/api/delivery/optimize', 
                               json=test_data, 
                               timeout=30)
        print(f'Response status: {response.status_code}')
        
        if response.status_code == 200:
            result = response.json()
            print('SUCCESS - API returned results')
            
            # Check revenue info
            if 'revenue_info' in result:
                revenue_info = result['revenue_info']
                print('Revenue info found:')
                print(f'  - Min target: {revenue_info.get("min_revenue_target", "N/A")}')
                print(f'  - Estimated revenue: {revenue_info.get("estimated_revenue", "N/A")}')
                print(f'  - Meets target: {revenue_info.get("meets_target", "N/A")}')
                print(f'  - Revenue gap: {revenue_info.get("revenue_gap", "N/A")}')
                if 'error' in revenue_info:
                    print(f'  - ERROR: {revenue_info["error"]}')
            else:
                print('WARNING - No revenue_info in response')
                
            # Check visits info
            if 'visits_info' in result:
                visits_info = result['visits_info']
                print('Visits info found:')
                print(f'  - Min target: {visits_info.get("min_visits_target", "N/A")}')
                print(f'  - Average visits: {visits_info.get("average_visits", "N/A")}')
                print(f'  - Meets target: {visits_info.get("meets_target", "N/A")}')
                print(f'  - Visits gap: {visits_info.get("visits_gap", "N/A")}')
                print(f'  - Frequent clients count: {visits_info.get("total_frequent_clients", "N/A")}')
                if 'error' in visits_info:
                    print(f'  - ERROR: {visits_info["error"]}')
            else:
                print('WARNING - No visits_info in response')
                
            # Check route data
            if 'route' in result:
                route = result['route']
                print(f'Route found with {len(route)} stops')
                for i, stop in enumerate(route[:3]):  # Check first 3 stops
                    print(f'  Stop {i+1}: {stop.get("client_code", "Unknown")} - Products: {len(stop.get("predicted_products", {}))}')
            else:
                print('WARNING - No route in response')
                
        else:
            print(f'ERROR - Status {response.status_code}: {response.text}')
            
    except requests.exceptions.ConnectionError:
        print('ERROR - Cannot connect to server. Is the Flask app running?')
    except Exception as e:
        print(f'ERROR calling API: {e}')

if __name__ == "__main__":
    test_delivery_optimization_conditions()
