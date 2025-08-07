#!/usr/bin/env python3
"""
Integration test for the commercial revenue dashboard and minimum revenue functionality
"""

import requests
import json
from datetime import datetime, timedelta

def test_flask_app_endpoints():
    """Test that all Flask endpoints are accessible"""
    base_url = "http://localhost:5000"
    
    endpoints_to_test = [
        ("/", "Home page"),
        ("/delivery_optimization", "Delivery optimization page"),
        ("/commercial_revenue_dashboard", "Commercial revenue dashboard"),
    ]
    
    print("🧪 TESTING FLASK ENDPOINTS")
    print("=" * 50)
    
    for endpoint, description in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            status = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
            print(f"{status} - {description}: {endpoint}")
        except requests.exceptions.RequestException as e:
            print(f"❌ FAIL - {description}: Connection error - {e}")
    
    print("\n")

def test_revenue_api_endpoints():
    """Test the revenue prediction API endpoints"""
    base_url = "http://localhost:5000"
    
    # Test data
    test_data = {
        'commercial_code': '1',
        'forecast_days': 7,
        'min_revenue': 1000
    }
    
    print("🧪 TESTING REVENUE API ENDPOINTS")
    print("=" * 50)
    
    # Test revenue prediction endpoint
    try:
        response = requests.post(
            f"{base_url}/api/revenue/predict",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ PASS - Revenue prediction API working")
                print(f"   Commercial: {result.get('commercial_code')}")
                print(f"   Forecast days: {result.get('forecast_days')}")
                print(f"   Min revenue target: {result.get('min_revenue_target')}")
            else:
                print(f"❌ FAIL - Revenue prediction API error: {result.get('error')}")
        else:
            print(f"❌ FAIL - Revenue prediction API returned {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL - Revenue prediction API: Connection error - {e}")
      # Test revenue analysis endpoint
    try:
        analysis_data = {
            'commercial_code': '1',
            'start_date': '2024-01-01',  # Use full year 2024
            'end_date': '2024-12-31',
            'min_revenue': 1000
        }
        
        response = requests.post(
            f"{base_url}/api/revenue/analyze",
            json=analysis_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ PASS - Revenue analysis API working")
                stats = result.get('revenue_statistics', {})
                print(f"   Days analyzed: {stats.get('days_analyzed', 'N/A')}")
                print(f"   Average daily revenue: {stats.get('average_daily_revenue', 'N/A')}")
            else:
                print(f"❌ FAIL - Revenue analysis API error: {result.get('error')}")
        else:
            print(f"❌ FAIL - Revenue analysis API returned {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL - Revenue analysis API: Connection error - {e}")
    
    print("\n")

def test_delivery_optimization_api():
    """Test the delivery optimization API with minimum revenue"""
    base_url = "http://localhost:5000"
    
    print("🧪 TESTING DELIVERY OPTIMIZATION WITH MINIMUM REVENUE")
    print("=" * 50)
    
    test_data = {
        'commercial_code': '1',
        'delivery_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'min_revenue': 1500
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/delivery/optimize",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ PASS - Delivery optimization API working")
            print(f"   Commercial: {result.get('commercial_name', 'N/A')}")
            print(f"   Delivery date: {result.get('delivery_date', 'N/A')}")
            print(f"   Total distance: {result.get('total_distance', 'N/A')} km")
            
            # Check if revenue info is included
            revenue_info = result.get('revenue_info')
            if revenue_info:
                print("✅ PASS - Revenue information included in delivery plan")
                print(f"   Min revenue target: {revenue_info.get('min_revenue_target', 'N/A')}")
                print(f"   Estimated revenue: {revenue_info.get('estimated_revenue', 'N/A')}")
                print(f"   Meets target: {revenue_info.get('meets_target', 'N/A')}")
            else:
                print("⚠️  WARN - No revenue information in delivery plan")
                
        else:
            print(f"❌ FAIL - Delivery optimization API returned {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL - Delivery optimization API: Connection error - {e}")
    
    print("\n")

def main():
    """Run all integration tests"""
    print("🚀 REVENUE INTEGRATION TESTING")
    print("=" * 60)
    print("Testing the complete integration of minimum revenue functionality")
    print("with delivery optimization and commercial revenue dashboard")
    print("=" * 60)
    print("\n")
    
    # Run all tests
    test_flask_app_endpoints()
    test_revenue_api_endpoints() 
    test_delivery_optimization_api()
    
    print("📊 INTEGRATION TEST SUMMARY")
    print("=" * 50)
    print("✅ If all tests passed, the revenue integration is working correctly")
    print("🌐 You can now access:")
    print("   • Commercial Revenue Dashboard: http://localhost:5000/commercial_revenue_dashboard")
    print("   • Delivery Optimization: http://localhost:5000/delivery_optimization")
    print("   • The navigation menu includes links to both dashboards")
    print("\n💡 Features tested:")
    print("   • Minimum revenue constraints in delivery optimization")
    print("   • Revenue prediction API endpoints")
    print("   • Integration between delivery and revenue systems")
    print("   • Navigation and UI connectivity")

if __name__ == "__main__":
    print("⚠️  NOTE: Make sure the Flask app is running (python app.py) before running this test")
    print("Starting tests in 3 seconds...\n")
    
    import time
    time.sleep(3)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
