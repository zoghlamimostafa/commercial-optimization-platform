import requests
import json
from datetime import datetime, timedelta

def test_complete_delivery_optimization():
    """Comprehensive test for delivery optimization with both revenue and frequent visits features"""
    base_url = "http://localhost:5000"
    
    print("🧪 COMPREHENSIVE DELIVERY OPTIMIZATION TEST")
    print("=" * 60)
    
    # Test scenarios
    test_scenarios = [
        {
            'name': 'Basic Delivery Optimization',
            'data': {
                'commercial_code': '1',
                'delivery_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            }
        },
        {
            'name': 'With Minimum Revenue Constraint',
            'data': {
                'commercial_code': '1',
                'delivery_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'min_revenue': 1500
            }
        },
        {
            'name': 'With Frequent Visits Constraint',
            'data': {
                'commercial_code': '1',
                'delivery_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'min_frequent_visits': 3
            }
        },
        {
            'name': 'With Both Revenue and Visits Constraints',
            'data': {
                'commercial_code': '1',
                'delivery_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'min_revenue': 1200,
                'min_frequent_visits': 2
            }
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📋 Test {i}: {scenario['name']}")
        print("-" * 40)
        
        try:
            response = requests.post(
                f"{base_url}/api/delivery/optimize",
                json=scenario['data'],
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ SUCCESS - API returned valid response")
                
                # Check basic delivery plan structure
                required_fields = ['commercial_code', 'delivery_date', 'route', 'packing_list', 'total_distance']
                for field in required_fields:
                    if field in result:
                        print(f"   ✓ {field}: {get_field_summary(result[field])}")
                    else:
                        print(f"   ❌ Missing field: {field}")
                
                # Check revenue information if requested
                if 'min_revenue' in scenario['data']:
                    if 'revenue_info' in result:
                        revenue_info = result['revenue_info']
                        print("   💰 Revenue Analysis:")
                        print(f"      Target: {revenue_info.get('min_revenue_target', 'N/A')}")
                        print(f"      Estimated: {revenue_info.get('estimated_revenue', 'N/A')}")
                        print(f"      Meets target: {revenue_info.get('meets_target', 'N/A')}")
                        if 'recommendations' in revenue_info:
                            print(f"      Recommendations: {len(revenue_info['recommendations'])} provided")
                    else:
                        print("   ⚠️  Revenue info requested but not found in response")
                
                # Check visits information if requested
                if 'min_frequent_visits' in scenario['data']:
                    if 'visits_info' in result:
                        visits_info = result['visits_info']
                        print("   📊 Visits Analysis:")
                        print(f"      Target: {visits_info.get('min_visits_target', 'N/A')}")
                        print(f"      Average: {visits_info.get('average_visits', 'N/A')}")
                        print(f"      Meets target: {visits_info.get('meets_target', 'N/A')}")
                        print(f"      Frequent clients: {visits_info.get('total_frequent_clients', 0)}")
                    else:
                        print("   ⚠️  Visits info requested but not found in response")
                
                # Check SARIMA predictions with price integration
                if 'route' in result and len(result['route']) > 0:
                    print("   🔮 SARIMA Predictions:")
                    sarima_count = 0
                    total_value = 0
                    
                    for stop in result['route']:
                        if 'predicted_products' in stop and stop['predicted_products']:
                            sarima_count += 1
                            
                            # Check if predictions include price information
                            products = stop['predicted_products']
                            if isinstance(products, dict):
                                for product, info in products.items():
                                    if isinstance(info, dict) and 'price' in info and 'total_value' in info:
                                        total_value += info.get('total_value', 0)
                                        break
                    
                    print(f"      Clients with predictions: {sarima_count}/{len(result['route'])}")
                    if total_value > 0:
                        print(f"      Total predicted value: {total_value:.2f} TND")
                        print("      ✅ Price integration working")
                    else:
                        print("      ⚠️  Price integration may not be working")
                
            else:
                print(f"❌ FAILED - Status code: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.Timeout:
            print("❌ FAILED - Request timed out")
        except requests.exceptions.ConnectionError:
            print("❌ FAILED - Connection error (is Flask server running?)")
        except Exception as e:
            print(f"❌ FAILED - Unexpected error: {e}")
    
    print(f"\n🏁 Test completed!")
    print("=" * 60)

def get_field_summary(field_value):
    """Get a brief summary of a field value for display"""
    if isinstance(field_value, list):
        return f"List with {len(field_value)} items"
    elif isinstance(field_value, dict):
        return f"Dict with {len(field_value)} keys"
    elif isinstance(field_value, (int, float)):
        return str(field_value)
    elif isinstance(field_value, str):
        return field_value[:50] + "..." if len(field_value) > 50 else field_value
    else:
        return str(type(field_value).__name__)

if __name__ == "__main__":
    test_complete_delivery_optimization()
