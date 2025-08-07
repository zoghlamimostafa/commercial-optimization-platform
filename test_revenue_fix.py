#!/usr/bin/env python3
"""
Test script to verify the revenue calculation fix is working properly.
"""

import requests
import json

def test_revenue_calculation():
    """Test the delivery optimization with revenue calculation"""    # Test data
    test_data = {
        "commercial_code": "1",
        "delivery_date": "2025-05-28",
        "min_revenue": 1000,
        "product_codes": ["P001", "P002", "P003"]
    }
    
    print("Testing revenue calculation fix...")
    print(f"Request data: {json.dumps(test_data, indent=2)}")
    
    try:        # Make request to the delivery optimization endpoint
        response = requests.post(
            "http://127.0.0.1:5000/api/delivery/optimize",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\nResponse status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nResponse received successfully!")
            
            # Check if we have revenue info
            if 'revenue_info' in result:
                revenue_info = result['revenue_info']
                print(f"\nRevenue Info:")
                print(f"  - Target Revenue: {revenue_info.get('target_revenue', 'N/A')} TND")
                print(f"  - Estimated Revenue: {revenue_info.get('estimated_revenue', 'N/A')} TND")
                print(f"  - Meets Target: {revenue_info.get('meets_target', 'N/A')}")
                print(f"  - Revenue Gap: {revenue_info.get('revenue_gap', 'N/A')} TND")
                
                # Check if estimated revenue is properly calculated
                estimated = revenue_info.get('estimated_revenue')
                if estimated and estimated != 'N/A' and isinstance(estimated, (int, float)):
                    print(f"\n✅ SUCCESS: Estimated revenue is calculated: {estimated} TND")
                else:
                    print(f"\n❌ ISSUE: Estimated revenue is still N/A or invalid: {estimated}")
            else:
                print("\n❌ ISSUE: No revenue_info in response")
            
            # Check individual route stops
            if 'route' in result and result['route']:
                print(f"\nRoute stops ({len(result['route'])} stops):")
                total_manual = 0.0
                for i, stop in enumerate(result['route']):
                    client_name = stop.get('client_name', 'Unknown')
                    est_rev = stop.get('estimated_revenue', 0)
                    print(f"  {i+1}. {client_name}: {est_rev} TND")
                    if isinstance(est_rev, (int, float)):
                        total_manual += est_rev
                
                print(f"\nManual calculation total: {total_manual:.2f} TND")
                
                # Compare with reported estimated revenue
                reported = revenue_info.get('estimated_revenue') if 'revenue_info' in result else None
                if reported and isinstance(reported, (int, float)):
                    if abs(total_manual - reported) < 0.01:
                        print(f"✅ Revenue calculation matches: {reported} TND")
                    else:
                        print(f"❌ Revenue mismatch: Manual={total_manual:.2f}, Reported={reported}")
                else:
                    print(f"❌ Reported revenue is invalid: {reported}")
            else:
                print(f"\n❌ ISSUE: No route data in response")
                
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to Flask server. Make sure it's running on http://127.0.0.1:5000")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_revenue_calculation()
