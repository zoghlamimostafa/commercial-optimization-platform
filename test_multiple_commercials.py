#!/usr/bin/env python3
"""
Final validation test for the SARIMA revenue prediction system
"""

import requests
import json

def test_multiple_commercials():
    """Test the system with different commercial codes"""
    
    base_url = "http://127.0.0.1:5000"
    
    # Test different commercial codes
    commercial_codes = ["1", "2", "3"]
    
    print("🔍 Testing SARIMA revenue prediction with multiple commercial codes...")
    print("=" * 70)
    
    for commercial_code in commercial_codes:
        print(f"\n📊 Testing Commercial Code: {commercial_code}")
        print("-" * 40)
        
        test_data = {
            "commercial_code": commercial_code,
            "delivery_date": "2024-05-15",
            "min_revenue": 1500,
            "min_frequent_visits": 5
        }
        
        try:
            response = requests.post(
                f"{base_url}/api/delivery/optimize",
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SUCCESS")
                
                # Check revenue information
                if 'revenue_info' in result:
                    revenue_info = result['revenue_info']
                    print(f"   💰 Revenue Analysis:")
                    print(f"      Min target: {revenue_info.get('min_revenue_target', 0)}")
                    print(f"      Estimated: {revenue_info.get('estimated_revenue', 0)}")
                    print(f"      Meets target: {'✅' if revenue_info.get('meets_target', False) else '❌'}")
                    print(f"      Total estimated: {revenue_info.get('total_estimated_revenue', 0)}")
                else:
                    print("   ⚠️  No revenue info available")
                    
                message = result.get('message', '')
                if message:
                    print(f"   📝 Message: {message}")
                    
            elif response.status_code == 404:
                print(f"❌ NO DATA - No historical data found for commercial {commercial_code}")
            else:
                try:
                    error_data = response.json()
                    print(f"❌ ERROR: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"❌ ERROR: {response.text}")
                    
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
    
    print("\n" + "=" * 70)
    print("✅ Multiple commercial codes testing completed!")

if __name__ == "__main__":
    test_multiple_commercials()
