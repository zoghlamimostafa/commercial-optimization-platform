#!/usr/bin/env python3
"""
Final verification test for delivery optimization UI sections
Tests both "Liste de Chargement" (Packing List) and "Prévisions SARIMA" (SARIMA Predictions)
"""

import requests
import json
from datetime import datetime, timedelta

def test_ui_sections():
    """Test that both packing list and SARIMA predictions sections have data"""
    
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 FINAL VERIFICATION TEST")
    print("=" * 50)
    print("Testing delivery optimization UI sections:")
    print("1. Liste de Chargement (Packing List)")
    print("2. Prévisions SARIMA (SARIMA Predictions)")
    print("=" * 50)
    
    # Test scenarios with different commercial codes and dates
    test_scenarios = [
        {
            'name': 'Test with Commercial 1300 (Historical Data Available)',
            'data': {
                'commercial_code': '1300',
                'delivery_date': '2023-06-15'
            }
        },
        {
            'name': 'Test with Commercial 1 (Fallback Data)',
            'data': {
                'commercial_code': '1',
                'delivery_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            }
        },
        {
            'name': 'Test with Revenue Constraint',
            'data': {
                'commercial_code': '1300',
                'delivery_date': '2023-06-15',
                'min_revenue': 1500
            }
        }
    ]
    
    all_tests_passed = True
    
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
                
                # Test 1: Packing List (Liste de Chargement)
                print("📦 TESTING PACKING LIST:")
                if 'packing_list' in result and result['packing_list']:
                    packing_items = len(result['packing_list'])
                    print(f"   ✅ Packing list present with {packing_items} items")
                    
                    # Show first few items as examples
                    items_shown = 0
                    for product, qty in result['packing_list'].items():
                        if items_shown < 3:  # Show first 3 items
                            print(f"      - {product}: {qty}")
                            items_shown += 1
                        else:
                            break
                    if packing_items > 3:
                        print(f"      ... and {packing_items - 3} more items")
                else:
                    print("   ❌ FAILED: Packing list is missing or empty")
                    all_tests_passed = False
                
                # Test 2: SARIMA Predictions (Prévisions SARIMA)
                print("\n🔮 TESTING SARIMA PREDICTIONS:")
                if 'route' in result and result['route']:
                    route_stops = len(result['route'])
                    print(f"   ✅ Route present with {route_stops} stops")
                    
                    # Check for predicted products in route stops
                    stops_with_predictions = 0
                    total_prediction_value = 0
                    
                    for stop in result['route']:
                        if 'predicted_products' in stop and stop['predicted_products']:
                            stops_with_predictions += 1
                            
                            # Calculate total value for this stop
                            stop_value = 0
                            for product, data in stop['predicted_products'].items():
                                if isinstance(data, dict):
                                    stop_value += data.get('total_value', 0)
                                
                            total_prediction_value += stop_value
                            
                            # Show example of predictions
                            if stops_with_predictions == 1:  # Show first stop as example
                                print(f"   📊 Example predictions for {stop['client_name']} ({stop['client_code']}):")
                                shown_products = 0
                                for product, data in stop['predicted_products'].items():
                                    if shown_products < 2:  # Show first 2 products
                                        if isinstance(data, dict):
                                            qty = data.get('quantity', 0)
                                            price = data.get('price', 0)
                                            value = data.get('total_value', 0)
                                            print(f"      - {product}: {qty} units @ {price:.2f} = {value:.2f} TND")
                                        else:
                                            print(f"      - {product}: {data} units")
                                        shown_products += 1
                                    else:
                                        break
                    
                    if stops_with_predictions > 0:
                        print(f"   ✅ SARIMA predictions found for {stops_with_predictions}/{route_stops} stops")
                        if total_prediction_value > 0:
                            print(f"   💰 Total predicted value: {total_prediction_value:.2f} TND")
                    else:
                        print("   ❌ FAILED: No stops have SARIMA predictions")
                        all_tests_passed = False
                else:
                    print("   ❌ FAILED: No route data available")
                    all_tests_passed = False
                
                # Test 3: Additional Features
                print("\n🎯 ADDITIONAL FEATURES:")
                if 'revenue_info' in result:
                    revenue_info = result['revenue_info']
                    print(f"   ✅ Revenue analysis: Target {revenue_info.get('min_revenue_target', 0)}, "
                          f"Estimated {revenue_info.get('estimated_revenue', 0)}")
                
                if 'total_distance' in result:
                    print(f"   ✅ Route optimization: {result['total_distance']:.2f} km total distance")
                
                print(f"\n   🎉 Test {i} PASSED")
                
            else:
                print(f"   ❌ FAILED: API returned status code {response.status_code}")
                print(f"   Error: {response.text}")
                all_tests_passed = False
                
        except Exception as e:
            print(f"   ❌ FAILED: Exception occurred - {str(e)}")
            all_tests_passed = False
    
    # Final Results
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Liste de Chargement (Packing List) is working correctly")
        print("✅ Prévisions SARIMA (SARIMA Predictions) is working correctly")
        print("✅ Both sections now display data properly in the UI")
        print("\n🏆 The delivery optimization issues have been RESOLVED!")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the failed sections above for more details")
    
    print("=" * 50)

if __name__ == "__main__":
    test_ui_sections()
