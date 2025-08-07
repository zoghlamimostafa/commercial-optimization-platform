"""
Test the delivery optimization API with authentication
"""

import requests
import json
from datetime import datetime, timedelta

def login_first():
    """Login to get session cookies"""
    
    print("🔐 Logging in first...")
    
    # Try to login with admin credentials
    login_data = {
        "login": "admin",
        "password": "admin123"  # Adjust this to match your admin password
    }
    
    session = requests.Session()
    
    try:
        # Make login request
        login_response = session.post(
            'http://127.0.0.1:5000/login',
            data=login_data,  # Use data instead of json for form data
            timeout=30
        )
        
        print(f"Login response status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            # Check if we were redirected to dashboard (successful login)
            if "tableau_de_bord" in login_response.url or "dashboard" in login_response.text:
                print("✅ Login successful!")
                return session
            else:
                print("❌ Login failed - check credentials")
                return None
        else:
            print(f"❌ Login failed with status {login_response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_authenticated_api():
    """Test the delivery optimization API with authentication"""
    
    print("🧪 TESTING AUTHENTICATED DELIVERY OPTIMIZATION API")
    print("=" * 60)
    
    # First, login to get session
    session = login_first()
    
    if not session:
        print("❌ Cannot test API without successful login")
        return
    
    # Test data
    test_data = {
        "commercial_code": "1",
        "delivery_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "product_codes": ["PROD_001", "PROD_002", "PROD_003"],
        "min_revenue": 2000,
        "min_frequent_visits": 3
    }
    
    print(f"\n📤 Sending authenticated request:")
    print(json.dumps(test_data, indent=2))
    
    try:
        # Make the API call with session cookies
        response = session.post(
            'http://127.0.0.1:5000/api/delivery/optimize',
            json=test_data,
            timeout=60,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\n📥 Response:")
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                
                print(f"\n✅ SUCCESS! API returned valid JSON")
                print(f"📊 RESULTS SUMMARY:")
                
                # Check packing list
                packing_list = result.get('packing_list', {})
                if packing_list:
                    total_items = sum(packing_list.values()) if isinstance(list(packing_list.values())[0], (int, float)) else len(packing_list)
                    print(f"  📦 Packing List: {len(packing_list)} products, {total_items} total items")
                    print(f"      Products: {list(packing_list.keys())}")
                else:
                    print(f"  ❌ Packing List: EMPTY")
                
                # Check revenue info
                revenue_info = result.get('revenue_info', {})
                if revenue_info:
                    estimated = revenue_info.get('estimated_revenue', 0)
                    target = revenue_info.get('min_revenue_target', 0)
                    meets_target = revenue_info.get('meets_target', False)
                    gap = revenue_info.get('revenue_gap', 0)
                    
                    print(f"  💰 Revenue Info:")
                    print(f"      Estimated: {estimated:.2f} TND")
                    print(f"      Target: {target:.2f} TND")
                    print(f"      Meets Target: {meets_target}")
                    print(f"      Gap: {gap:.2f} TND")
                    
                    # Check if our fix worked
                    if estimated > 0:
                        print(f"      ✅ Revenue calculation fix: WORKING")
                    else:
                        print(f"      ❌ Revenue calculation fix: FAILED")
                else:
                    print(f"  ❌ Revenue Info: MISSING")
                
                # Check visits info
                visits_info = result.get('visits_info', {})
                if visits_info:
                    avg_visits = visits_info.get('average_visits', 0)
                    meets_visits_target = visits_info.get('meets_target', False)
                    
                    print(f"  👥 Visits Info:")
                    print(f"      Average Visits: {avg_visits:.1f}")
                    print(f"      Meets Target: {meets_visits_target}")
                else:
                    print(f"  ❌ Visits Info: MISSING")
                
                # Check route
                route = result.get('route', [])
                if route:
                    print(f"  🚚 Route: {len(route)} stops")
                    for i, stop in enumerate(route[:3]):  # Show first 3 stops
                        client = stop.get('client_code', 'unknown')
                        products = len(stop.get('predicted_products', {}))
                        print(f"      Stop {i+1}: Client {client}, {products} products")
                else:
                    print(f"  ❌ Route: EMPTY")
                
                # Overall assessment
                issues_fixed = []
                issues_remaining = []
                
                if packing_list:
                    issues_fixed.append("✅ Packing list is no longer empty")
                else:
                    issues_remaining.append("❌ Empty packing list")
                
                if revenue_info and revenue_info.get('estimated_revenue', 0) > 0:
                    issues_fixed.append("✅ Revenue calculation is working")
                else:
                    issues_remaining.append("❌ Zero revenue")
                
                if route:
                    issues_fixed.append("✅ Route generation is working")
                else:
                    issues_remaining.append("❌ Empty route")
                
                print(f"\n🔧 FIX STATUS:")
                if issues_fixed:
                    for fix in issues_fixed:
                        print(f"  {fix}")
                
                if issues_remaining:
                    print(f"\n⚠️ REMAINING ISSUES:")
                    for issue in issues_remaining:
                        print(f"  {issue}")
                else:
                    print(f"\n🎉 ALL MAJOR ISSUES HAVE BEEN RESOLVED!")
                
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON response: {e}")
                print(f"Response text: {response.text[:500]}...")
                
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed - make sure Flask app is running on http://127.0.0.1:5000")
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out - the API might be taking too long")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_authenticated_api()
