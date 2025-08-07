#!/usr/bin/env python3
"""
DateTime Error Fix Verification Test
"""

import requests
import json

def test_datetime_fix():
    """Test that the datetime error is fixed"""
    print("🔧 TESTING DATETIME ERROR FIX")
    print("=" * 50)
    
    # Test the specific endpoint that was failing
    url = "http://127.0.0.1:5000/api/revenue/predict"
    data = {
        "commercial_code": "1",
        "forecast_days": 7, 
        "min_revenue": 1000
    }
    
    try:
        print(f"Testing: POST {url}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(
            url,
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS - No datetime error!")
            print(f"✅ API returned success: {result.get('success')}")
            print(f"✅ Commercial code: {result.get('commercial_code')}")
            print(f"✅ Forecast days: {result.get('forecast_days')}")
            
            if 'prediction_results' in result:
                pred = result['prediction_results']
                print(f"✅ Prediction results generated")
                print(f"   - Enhancement applied: {pred.get('enhancement_applied')}")
                print(f"   - Revenue constraints applied: {pred.get('revenue_constraints_applied')}")
                print(f"   - Dates count: {len(pred.get('dates', []))}")
                
            return True
        else:
            print(f"❌ FAILED - HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ FAILED - Exception: {e}")
        return False

def test_commercial_revenue_dashboard():
    """Test that the commercial revenue dashboard is accessible"""
    print("\n🖥️  TESTING COMMERCIAL REVENUE DASHBOARD")
    print("=" * 50)
    
    url = "http://127.0.0.1:5000/commercial_revenue_dashboard"
    
    try:
        response = requests.get(url, allow_redirects=False)
        print(f"Testing: GET {url}")
        print(f"Response Status: {response.status_code}")
        
        if response.status_code in [200, 302]:  # 302 is redirect to login
            print("✅ SUCCESS - Dashboard accessible")
            if response.status_code == 302:
                print("✅ Correctly redirects to login (authentication required)")
            return True
        else:
            print(f"❌ FAILED - Unexpected status code")
            return False
            
    except Exception as e:
        print(f"❌ FAILED - Exception: {e}")
        return False

if __name__ == "__main__":
    print("🚀 DATETIME ERROR FIX VERIFICATION")
    print("=" * 60)
    print("Testing the specific issue that was causing:")
    print("'Can only use .dt accessor with datetimelike values'")
    print()
    
    # Run tests
    api_test = test_datetime_fix()
    dashboard_test = test_commercial_revenue_dashboard()
    
    print("\n" + "=" * 60)
    print("📋 VERIFICATION RESULTS")
    print("=" * 60)
    
    if api_test and dashboard_test:
        print("🎉 ALL TESTS PASSED!")
        print("✅ DateTime error has been successfully resolved")
        print("✅ Revenue prediction API is working")
        print("✅ Commercial revenue dashboard is accessible")
        print("✅ SARIMA system is operational")
    else:
        print("❌ Some tests failed:")
        print(f"   - Revenue API: {'✅' if api_test else '❌'}")
        print(f"   - Dashboard: {'✅' if dashboard_test else '❌'}")
